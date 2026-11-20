"""Interactive signal generation and CSV analysis using the existing FFT checker."""
import base64,csv,hashlib,io,json,math,os,sys,uuid
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from scipy import signal
from signal_check import spectrum,analyze
from spectral_validation import power_check,fit_tones
from transfer import estimate
ROOT=Path(__file__).resolve().parent

def number(value,name,low,high,integer=False):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high or integer and int(value)!=value:raise ValueError(name+' 超出范围')
 return int(value) if integer else float(value)

def generate(config):
 fs=number(config.get('sampling_hz',1024),'采样率',32,48000);n=number(config.get('samples',4096),'样本数',128,32768,True);frequency=number(config.get('frequency',50),'频率',.01,100000);second=number(config.get('second_frequency',200),'第二频率',.01,100000);noise=number(config.get('noise_std',0),'噪声',0,2);kind=config.get('waveform','multitone')
 t=np.arange(n)/fs;phase=2*np.pi*frequency*t
 if kind=='sine':x=np.sin(phase)
 elif kind=='multitone':x=np.sin(phase)+.5*np.sin(2*np.pi*second*t)
 elif kind=='square':x=signal.square(phase)
 elif kind=='triangle':x=signal.sawtooth(phase,width=.5)
 elif kind=='sawtooth':x=signal.sawtooth(phase)
 elif kind=='chirp':x=signal.chirp(t,f0=frequency,f1=second,t1=n/fs)
 elif kind=='noise':x=np.zeros(n)
 else:raise ValueError('未知波形')
 rng=np.random.default_rng(number(config.get('seed',20261103),'随机种子',0,2**32-1,True));x=x+rng.normal(0,noise if kind!='noise' else max(noise,.1),n)
 return t,x,fs,frequency,second,kind

def filter_design(config,fs):
 kind=config.get('filter','butterworth');band=config.get('band','lowpass');order=number(config.get('order',4),'阶数',1,10,True);cut=number(config.get('cutoff_hz',100),'截止频率',.01,fs/2-.001)
 if band not in ['lowpass','highpass','bandpass']:raise ValueError('未知滤波类型')
 cutoffs=[cut,number(config.get('high_hz',300),'上截止频率',.01,fs/2-.001)] if band=='bandpass' else cut
 if band=='bandpass' and cutoffs[1]<=cutoffs[0]:raise ValueError('上截止频率须大于下截止频率')
 if kind=='butterworth':sos=signal.butter(order,cutoffs,btype=band,fs=fs,output='sos')
 elif kind=='chebyshev':sos=signal.cheby1(order,number(config.get('ripple_db',1),'通带纹波',.1,3),cutoffs,btype=band,fs=fs,output='sos')
 else:raise ValueError('未知滤波器')
 return sos,dict(family=kind,band=band,order=order,cutoff_hz=cutoffs,sos=sos.tolist(),mode='causal sosfilt; transient removal is explicit')

class Workbench:
 name='Signal Lab'
 def __init__(self,root=None):
  self.root=Path(root or os.environ.get('SIGNAL_RUNS',ROOT/'runs/interactive'));self.root.mkdir(parents=True,exist_ok=True)
 def post(self,path,value):
  if path!='/api/analyze':raise ValueError('接口不存在')
  config=value.get('config',{});source='synthetic';raw=None;y=None;kind='csv'
  if not isinstance(config,dict):raise ValueError('参数格式无效')
  if value.get('csv_base64'):
   raw=base64.b64decode(value['csv_base64'],validate=True)
   if len(raw)>8*1024*1024:raise ValueError('CSV最大8MB')
   rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
   if not 128<=len(rows)<=32768 or not {'time_s','input'}<=rows[0].keys():raise ValueError('CSV需有time_s,input列，128至32768行；filtered列选填')
   t=np.array([float(r['time_s']) for r in rows]);x=np.array([float(r['input']) for r in rows]);spectrum(t,x)
   fs=float(1/np.median(np.diff(t)))
   if not math.isfinite(fs) or not 0<fs<=1e9:raise ValueError('CSV采样率须为正且不超过1GHz')
   if 'filtered' in rows[0]:y=np.array([float(r['filtered']) for r in rows]);spectrum(t,y)
   frequency=number(config.get('frequency',50),'分析频率',.01,100000);second=number(config.get('second_frequency',200),'第二频率',.01,100000);source='uploaded-csv'
  else:t,x,fs,frequency,second,kind=generate(config)
  if not np.isfinite(x).all() or np.max(np.abs(x))>1e12:raise ValueError('信号须为有限数值，幅度不超过1e12')
  sos=None;design=None
  if y is None:sos,design=filter_design(config,fs);y=signal.sosfilt(sos,x)
  if not np.isfinite(y).all() or np.max(np.abs(y))>1e12:raise ValueError('输出包含非有限值或幅度异常')
  discard=number(config.get('discard',1024),'丢弃瞬态点数',0,len(t)-32,True)
  requested=[frequency,second] if kind in ['multitone','chirp','csv'] else [frequency]
  aliases=[abs((f+fs/2)%fs-fs/2) for f in requested];tones=sorted(set(f for f in aliases if 1e-10<f<fs/2))
  run=uuid.uuid4().hex;folder=self.root/run;folder.mkdir()
  try:
   csv_path=folder/'waveform.csv';np.savetxt(csv_path,np.column_stack([t,x,y]),delimiter=',',header='time_s,input,filtered',comments='')
   report=analyze(csv_path,tones,discard);f,a,_=spectrum(t[discard:],x[discard:]);_,b,_=spectrum(t[discard:],y[discard:])
   amplitude_floor=max(float(a.max())*1e-6,1e-12)
   for row in report['tones']:
    if row['input_amplitude']<amplitude_floor:row.update(gain_db=None,measurement_note='Input amplitude below 1e-6 of the retained spectrum peak (absolute floor 1e-12); gain not measurable.')
   hz=np.linspace(0,fs/2,513);response=None
   if sos is not None:
    _,h=signal.sosfreqz(sos,worN=hz,fs=fs);response=(20*np.log10(np.maximum(np.abs(h),1e-12))).tolist()
    for row in report['tones']:
     _,h=signal.sosfreqz(sos,worN=[row['bin_hz']],fs=fs);theory=float(20*np.log10(max(abs(h[0]),1e-12)));row['theoretical_gain_db']=theory;row['gain_difference_db']=row['gain_db']-theory if row['gain_db'] is not None else None
   # Full FFT and measurements are preserved; plots use a bounded contiguous time window and frequency bins.
   top=np.argsort(a)[-8:][::-1];plot_f=np.unique(np.r_[np.linspace(0,len(f)-1,min(len(f),1800)).astype(int),top]);window=min(len(t),2048)
   report.update(id=run,created=datetime.now(timezone.utc).isoformat(),source=source,waveform=kind,filter=design,source_sha256=hashlib.sha256(raw).hexdigest() if raw else None,configuration=config,implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()+Path(__file__).with_name('signal_check.py').read_bytes()+Path(__file__).with_name('spectral_validation.py').read_bytes()+Path(__file__).with_name('transfer.py').read_bytes()).hexdigest(),aliases=[{'requested_hz':v,'folded_hz':a,'above_nyquist':v>=fs/2} for v,a in zip(requested,aliases)],rms_input=float(np.sqrt(np.mean(x[discard:]**2))),rms_filtered=float(np.sqrt(np.mean(y[discard:]**2))),peak_hz=float(f[np.argmax(a)]),plot=dict(time=t[:window].tolist(),input=x[:window].tolist(),filtered=y[:window].tolist(),frequency=f[plot_f].tolist(),input_spectrum=a[plot_f].tolist(),filtered_spectrum=b[plot_f].tolist(),response_frequency=hz.tolist(),response_db=response),definitions={'time_plot':'First up to 2048 contiguous samples; metrics use every retained sample.','spectrum_plot':'Bounded bins with largest input peaks preserved; original full FFT used for metrics.','gain':'Nearest FFT-bin ratio, not an unbiased off-bin amplitude estimate.','measurement':'Numerical analysis, not actual LabVIEW or hardware execution.'})
   report['power_validation']={'input':power_check(t[discard:],x[discard:]),'filtered':power_check(t[discard:],y[discard:])}
   report['transfer']=estimate(t[discard:],x[discard:],y[discard:],number(config.get('segment_length',min(512,len(t[discard:])//4)),'Welch窗长',32,len(t[discard:]),True),number(config.get('overlap',.5),'重叠率',0,.9)) if len(t[discard:])>=128 else None
   if sos is not None and report['transfer'] is not None:
    frequencies=report['transfer']['frequency_hz']
    _,reference=signal.sosfreqz(sos,worN=frequencies,fs=fs)
    report['transfer']['reference_gain_db']=(20*np.log10(np.maximum(np.abs(reference),1e-12))).tolist()
   report['stationary_tone_fit']=None
   if tones and kind not in ['chirp','noise']:
    try:report['stationary_tone_fit']=fit_tones(t[discard:],x[discard:],y[discard:],tones)
    except ValueError as e:report['tone_fit_note']=str(e)
   if source=='synthetic':report['source_sha256']=report['input_sha256']
   (folder/'report.tmp').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False));(folder/'report.tmp').replace(folder/'report.json');return report
  except Exception:
   import shutil;shutil.rmtree(folder);raise
 def get(self,path,query):
  if path=='/api/history':
   rows=[]
   for p in sorted(self.root.glob('*/report.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:20]:
    r=json.loads(p.read_text());rows.append({k:r[k] for k in ['id','created','source','sampling_hz','samples']})
   return rows
  run=query.get('id',[''])[0]
  if len(run)!=32 or any(c not in '0123456789abcdef' for c in run):raise ValueError('结果编号无效')
  folder=self.root/run
  if path=='/api/report':return json.loads((folder/'report.json').read_text())
  if path=='/api/export':return 200,(folder/'report.json').read_bytes(),'application/json','signal-report.json'
  if path=='/api/csv':return 200,(folder/'waveform.csv').read_bytes(),'text/csv; charset=utf-8','waveform.csv'
  raise ValueError('接口不存在')
if __name__=='__main__':
 sys.path.insert(0,str(ROOT.parent/'scripts'));from lab_http import serve
 serve(Workbench(),ROOT/'web',8783)
