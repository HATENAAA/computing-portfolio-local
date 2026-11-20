"""Welch H1 estimate for synchronized uniformly-sampled real input/output pairs."""
import numpy as np
from scipy import signal

def estimate(t,x,y,nperseg=512,overlap=.5,coherence_floor=.8,excitation_floor=1e-5):
 t,x,y=[np.asarray(v,dtype=float) for v in (t,x,y)]
 if any(v.ndim!=1 for v in (t,x,y)) or len(t)!=len(x) or len(x)!=len(y) or len(t)<128 or not all(np.isfinite(v).all() for v in (t,x,y)):raise ValueError('同步输入输出必须为等长有限序列，至少128点')
 dt=np.diff(t)
 if np.any(dt<=0) or not np.allclose(dt,np.median(dt),rtol=1e-4,atol=1e-12):raise ValueError('需严格递增的等间隔时间戳')
 if type(nperseg) is not int or not 32<=nperseg<=len(t) or not 0<=overlap<.95:raise ValueError('无效窗长或重叠率')
 fs=1/np.median(dt);noverlap=int(nperseg*overlap);segments=1+(len(t)-nperseg)//(nperseg-noverlap)
 kw=dict(fs=fs,window='hann',nperseg=nperseg,noverlap=noverlap,detrend='constant')
 f,px=signal.welch(x,**kw);_,py=signal.welch(y,**kw);_,pxy=signal.csd(x,y,**kw)
 h=np.divide(pxy,px,out=np.zeros_like(pxy),where=px>0)
 c=np.divide(abs(pxy)**2,px*py,out=np.zeros_like(px),where=px*py>0);c=np.clip(c,0,1)
 # A single Welch segment can give trivial unit coherence; never call it reliable.
 stationary=True;block=len(x)//4
 powers=[np.mean((x[i*block:(i+1)*block]-np.mean(x[i*block:(i+1)*block]))**2) for i in range(4)]
 shapes=[]
 for i in range(4):
  _,v=signal.welch(x[i*block:(i+1)*block],fs=fs,nperseg=min(128,block),window='hann');v=np.convolve(v,np.ones(9)/9,mode='same');shapes.append(v/max(v.sum(),1e-30))
 spectral_drift=max(float(np.sum(abs(v-shapes[0]))) for v in shapes)
 if max(powers)>max(min(powers)*4,1e-24) or spectral_drift>1:stationary=False
 valid=(px>max(float(px.max())*excitation_floor,1e-24))&(c>=coherence_floor)&(segments>=4)&stationary
 phase=np.angle(h,deg=True);gain=20*np.log10(np.maximum(abs(h),1e-30))
 return dict(version=1,method='Welch H1=Pxy/Pxx; Pxy=conj(X)*Y',sampling_hz=float(fs),nperseg=nperseg,overlap=overlap,segments=segments,frequency_resolution_hz=float(fs/nperseg),stationarity_screen_passed=stationary,spectral_drift_l1=spectral_drift,frequency_hz=f.tolist(),coherence=c.tolist(),input_psd=px.tolist(),reliable=valid.tolist(),gain_db=[float(v) if ok else None for v,ok in zip(gain,valid)],phase_deg=[float(v) if ok else None for v,ok in zip(phase,valid)],thresholds=dict(coherence=coherence_floor,input_psd_relative=excitation_floor),warnings=([ '少于4段：相干性不可作为可靠性证据'] if segments<4 else [])+(['输入分块功率或谱形变化较大：非平稳风险，屏蔽全段估计'] if not stationary else []),scope='同步采样假设；相干性不是因果证明。相位为[-180,180]度，不补偿未知采集延迟。四块功率仅筛查部分非平稳性。')

def study(seed=7):
 rng=np.random.default_rng(seed);fs=1024.;t=np.arange(16384)/fs;x=rng.normal(size=len(t));sos=signal.butter(3,100,fs=fs,output='sos');clean=signal.sosfilt(sos,x);rows=[]
 for noise in [0,.1,.5]:
  y=clean+rng.normal(0,noise,len(t))
  for window in [256,512,1024]:
   for overlap in [0,.5,.75]:
    e=estimate(t,x,y,window,overlap);f=np.array(e['frequency_hz']);_,truth=signal.sosfreqz(sos,worN=f,fs=fs);ok=np.array(e['reliable'])&(f>10)&(f<180);indices=np.flatnonzero(ok)
    gains=np.array([e['gain_db'][i] for i in indices]);phase=np.array([e['phase_deg'][i] for i in indices]);diff=(phase-np.angle(truth[indices],deg=True)+180)%360-180
    rows.append(dict(noise_std=noise,window=window,overlap=overlap,reliable_bins=int(ok.sum()),gain_mae_db=float(np.mean(abs(gains-20*np.log10(abs(truth[indices]))))) if len(indices) else None,phase_mae_deg=float(np.mean(abs(diff))) if len(indices) else None))
 return dict(source='synthetic-known-system',seed=seed,filter_sos=sos.tolist(),rows=rows,scope='仿真系统核对，不是采集设备实测')
if __name__=='__main__':
 import argparse,json
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.write_text(json.dumps(study(),ensure_ascii=False,indent=2,allow_nan=False))
