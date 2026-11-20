"""Local hyperspectral reconstruction experiments and paired HWC evaluation."""
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,io,json,math,os,sys,uuid
from tempfile import TemporaryDirectory
import numpy as np
from PIL import Image
from scipy.ndimage import zoom
from safe_metrics import assess
from scene_experiment import METHODS, SCALES, catalog, digest_file, run_scene
ROOT=Path(__file__).resolve().parent

def bounded_number(value,name,low,high,integer=False):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high or integer and int(value)!=value:raise ValueError(name+' 超出范围')
 return int(value) if integer else float(value)
def load_array(raw):
 if len(raw)>16*1024*1024:raise ValueError('单个npy文件最大16MB')
 f=io.BytesIO(raw);version=np.lib.format.read_magic(f)
 if version==(1,0):shape,fortran,dtype=np.lib.format.read_array_header_1_0(f)
 elif version in [(2,0),(3,0)]:shape,fortran,dtype=np.lib.format.read_array_header_2_0(f)
 else:raise ValueError('不支持的npy版本')
 if len(shape)!=3 or min(shape)<1 or max(shape[:2])>512 or shape[2]>256 or math.prod(shape)>2_000_000:raise ValueError('需要非空HWC数组：高宽≤512、波段≤256、元素总数≤200万')
 if dtype.kind not in 'fiu' or dtype.hasobject:raise ValueError('只接收实数数值数组，不允许对象、复数或pickle')
 value=np.load(io.BytesIO(raw),allow_pickle=False)
 if not np.isfinite(value).all() or np.max(np.abs(value.astype(np.float64)))>1e12:raise ValueError('数组须为有限数值，绝对值不超过1e12')
 return value.astype(np.float64)
def png(array):
 image=Image.fromarray(np.asarray(array,dtype=np.uint8));out=io.BytesIO();image.save(out,format='PNG');return 'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()
def preview(cube,band,data_range):return png(np.clip(cube[:,:,band]/data_range*255,0,255))
def demo(scale=4,noise=.02):
 rng=np.random.default_rng(20261103);h=w=48;b=16;y,x=np.mgrid[:h,:w]/48;wave=np.linspace(0,1,b);truth=np.clip(.15+.45*x[:,:,None]+.2*np.sin(5*y[:,:,None]+wave[None,None,:]*4)+.1*np.cos(x[:,:,None]*17+wave[None,None,:]*8),.01,.99)
 low=zoom(truth,(1/scale,1/scale,1),order=1,prefilter=False);baseline=zoom(low,(h/low.shape[0],w/low.shape[1],1),order=3,mode='reflect')
 prediction=np.clip(truth+rng.normal(0,noise,truth.shape),0,1)
 return truth,prediction,baseline

def display_channels(cube, bands, reference):
 values=np.asarray(cube[:,:,bands],dtype=np.float32)
 return png(np.clip((values-reference[0])/np.maximum(reference[1]-reference[0],1)*255,0,255))

def scene_display(truth,pred,low,scene,band):
 rgb=scene['rgb_bands']
 composite_levels=np.percentile(truth[:,:,rgb],[2,98],axis=(0,1))
 single_levels=np.percentile(truth[:,:,band],[2,98],axis=(0,1))
 return {
  'truth':display_channels(truth,band,single_levels),
  'prediction':display_channels(pred,band,single_levels),
  'low':display_channels(low,band,single_levels),
  'composite_truth':display_channels(truth,rgb,composite_levels),
  'composite_prediction':display_channels(pred,rgb,composite_levels),
  'composite_low':display_channels(low,rgb,composite_levels),
 }

class Workbench:
 name='Spectral Lab'
 def __init__(self,root=None):self.root=Path(root or os.environ.get('HSI_RUNS',ROOT/'runs/interactive'));self.root.mkdir(parents=True,exist_ok=True)
 def experiment(self,value):
  scene_id=value.get('scene')
  if not isinstance(scene_id,str):raise ValueError('请选择航测样本')
  scene=next((item for item in catalog() if item['id']==scene_id),None)
  if scene is None:raise ValueError('本地找不到所选航测样本')
  scale=value.get('scale',4)
  if type(scale) is not int or scale not in SCALES:raise ValueError('请选择 ×2、×4 或 ×8 倍率')
  method=value.get('method','bicubic')
  if not isinstance(method,str) or method not in METHODS:raise ValueError('请选择重建方法')
  implementation=hashlib.sha256(b''.join(Path(__file__).with_name(name).read_bytes()
     for name in ('workbench.py','scene_experiment.py','safe_metrics.py'))).hexdigest()
  run=hashlib.sha256(f"{scene['sample_sha256']}:{scale}:{method}:{implementation}".encode()).hexdigest()[:32]
  folder=self.root/run
  if not (folder/'report.json').exists():
   truth,low,pred,angles,metrics,comparison=run_scene(scene,scale,method)
   dr=scene['data_range']
   with TemporaryDirectory(dir=self.root) as stage:
    pending=Path(stage)/'result';pending.mkdir()
    for name,array in [('truth',truth),('low-resolution',low),('prediction',pred),('sam',angles)]:
     np.save(pending/(name+'.npy'),array,allow_pickle=False)
    report=dict(id=run,created=datetime.now(timezone.utc).isoformat(),source='observed-scene',
      method=METHODS[method][0],method_id=method,shape=list(truth.shape),input_shape=list(low.shape),
      layout='HWC',data_range=dr,scale=scale,wavelengths=None,metrics=metrics,comparison=comparison,
      prediction_out_of_range_values=int(((pred<0)|(pred>dr)).sum()),
      truth_sha256=digest_file(pending/'truth.npy'),prediction_sha256=digest_file(pending/'prediction.npy'),
      low_resolution_sha256=digest_file(pending/'low-resolution.npy'),implementation_sha256=implementation,
      input_hashes={'scene_sample_sha256':scene['sample_sha256']},environment={'numpy':np.__version__},
      experiment=scene,scope='Observed airborne reference crop; simulated block-average degradation and CPU interpolation.',
      definitions={'degradation':'Non-overlapping spatial block mean per band; no spectral resampling.',
        'reconstruction':'Selected Pillow float32 interpolation, applied independently to each spectral band.',
        'display':'Shared 2nd–98th percentile stretch from reference per displayed band; visualization only.',
        'SAM':'Degrees; zero-norm spectra are undefined.', 'data_range':'8000 DN, the ceiling observed in both archived cubes.'})
    (pending/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
    try:pending.rename(folder)
    except OSError:
     if not (folder/'report.json').is_file():raise
  h,w,_=scene['shape']
  return self.view(run,scene['rgb_bands'][0],h//2,w//2,None)

 def post(self,path,value):
  if path=='/api/experiment':return self.experiment(value)
  if path=='/api/compare':
   from paired_compare import compare
   a=self.read(value.get('baseline',''));b=self.read(value.get('candidate',''))
   if a['id']==b['id'] or a['truth_sha256']!=b['truth_sha256'] or a['scale']!=b['scale'] or a['data_range']!=b['data_range']:
    raise ValueError('请选择真值、倍率和量程一致的两条不同记录')
   runs=[dict(id=r['id'],scale=r['scale'],summary=r['metrics'],samples=[dict(sample_id='image',truth_sha256=r['truth_sha256'],metrics=r['metrics'])]) for r in [a,b]]
   spec=dict(mode='synthetic' if any(r['source']=='synthetic-diagnostic' for r in [a,b]) else 'observed-scene' if all(r['source']=='observed-scene' for r in [a,b]) else 'uploaded-reconstructions',splits=[dict(id='image',scene='uploaded-scene',split='test')],runs=runs)
   result=compare(spec,a['id'],b['id']);result['source_reports_sha256']={r['id']:hashlib.sha256((self.root/r['id']/'report.json').read_bytes()).hexdigest() for r in [a,b]}
   result['compared_values']={'baseline':a['metrics'],'candidate':b['metrics']}
   result['scope']='同一幅影像的成对描述性比较；不估计独立场景置信区间。多场景实验请使用experiment_eval.py。'
   return result
  if path!='/api/analyze':raise ValueError('接口不存在')
  dr=bounded_number(value.get('data_range',1),'数据量程',1e-9,1e9);scale=bounded_number(value.get('scale',4),'倍率',1,16,True);source='uploaded-reconstruction';baseline=None;input_hashes={}
  if value.get('demo',False):
   noise=bounded_number(value.get('noise_std',.02),'诊断噪声',0,.25);truth,pred,baseline=demo(scale,noise);source='synthetic-diagnostic';dr=1;method=f'合成噪声诊断 σ={noise:g}'
  else:
   if not value.get('truth') or not value.get('prediction'):raise ValueError('请提供真值和重建结果的npy文件')
   raw_x=base64.b64decode(value['truth'],validate=True);raw_y=base64.b64decode(value['prediction'],validate=True);truth=load_array(raw_x);pred=load_array(raw_y);input_hashes={'uploaded_truth_sha256':hashlib.sha256(raw_x).hexdigest(),'uploaded_prediction_sha256':hashlib.sha256(raw_y).hexdigest()};method=str(value.get('method','用户提供的重建结果'))[:120]
  if truth.shape!=pred.shape:raise ValueError('真值与重建数组形状必须一致，且为HWC排列')
  if truth.min()<0 or truth.max()>dr:raise ValueError('真值超出所填量程，请核对单位；不会按每张图自动缩放')
  wavelengths=value.get('wavelengths',None)
  if wavelengths is not None:
   if not isinstance(wavelengths,list) or len(wavelengths)!=truth.shape[2] or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in wavelengths) or any(b<=a for a,b in zip(wavelengths,wavelengths[1:])):raise ValueError('波长须与波段数一致、为正且严格递增')
  metrics,angles=assess(truth,pred,dr,scale);run=uuid.uuid4().hex;folder=self.root/run;folder.mkdir()
  try:
   np.save(folder/'truth.npy',truth);np.save(folder/'prediction.npy',pred);np.save(folder/'sam.npy',angles)
   comparison=[]
   if baseline is not None:
    np.save(folder/'baseline.npy',baseline);other,_=assess(truth,baseline,dr,scale);comparison.append({'name':'三次插值基线','metrics':other,'scope':'Interpolation of a synthetically downsampled cube, not neural inference.'})
   report=dict(id=run,created=datetime.now(timezone.utc).isoformat(),source=source,method=method,shape=list(truth.shape),layout='HWC',data_range=dr,scale=scale,wavelengths=wavelengths,metrics=metrics,comparison=comparison,prediction_out_of_range_values=int(((pred<0)|(pred>dr)).sum()),truth_sha256=hashlib.sha256((folder/'truth.npy').read_bytes()).hexdigest(),prediction_sha256=hashlib.sha256((folder/'prediction.npy').read_bytes()).hexdigest(),implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()+Path(__file__).with_name('safe_metrics.py').read_bytes()).hexdigest(),input_hashes=input_hashes,environment={'numpy':np.__version__},scope='Reconstruction evaluation only; no model training or checkpoint inference executed.',definitions={'display':'Fixed declared data range for truth and prediction; image clipping is display-only.','SAM':'Degrees; zero-norm pixels undefined, shown grey.','MPSNR':'Null with an explicit infinite-band flag for exact bands; not replaced with an arbitrary finite value.','ERGAS':'Requires scale and nonzero band means; zero-mean bands make it undefined.'})
   (folder/'report.tmp').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False));(folder/'report.tmp').replace(folder/'report.json');return self.view(run,0,truth.shape[0]//2,truth.shape[1]//2,None)
  except Exception:
   import shutil;shutil.rmtree(folder);raise
 def read(self,run):
  if not isinstance(run,str) or len(run)!=32 or any(c not in '0123456789abcdef' for c in run):raise ValueError('结果编号无效')
  return json.loads((self.root/run/'report.json').read_text())
 def view(self,run,band,row,col,roi):
  report=self.read(run);folder=self.root/run;x=np.load(folder/'truth.npy',mmap_mode='r',allow_pickle=False);y=np.load(folder/'prediction.npy',mmap_mode='r',allow_pickle=False);h,w,b=x.shape
  band=bounded_number(band,'波段',0,b-1,True);row=bounded_number(row,'行',0,h-1,True);col=bounded_number(col,'列',0,w-1,True);dr=report['data_range']
  if roi is None:roi=[0,0,h,w]
  if not isinstance(roi,list) or len(roi)!=4 or any(type(v) is not int for v in roi):raise ValueError('ROI须为行、列、高、宽四个整数')
  r,c,rh,cw=roi
  if min(r,c)<0 or min(rh,cw)<1 or r+rh>h or c+cw>w:raise ValueError('ROI超出数组边界')
  all_pixels=roi==[0,0,h,w]
  metrics=report['metrics'] if all_pixels else assess(x[r:r+rh,c:c+cw,:],y[r:r+rh,c:c+cw,:],dr,report['scale'])[0]
  err=np.abs(np.asarray(x[:,:,band],dtype=np.float64)-np.asarray(y[:,:,band],dtype=np.float64))
  error_limit=dr*.10 if 'experiment' in report else dr
  strength=np.clip(err/error_limit,0,1)
  rgb=np.stack([22+strength*233,20+strength*121,40+(1-strength)*30],axis=-1)
  sam=np.load(folder/'sam.npy',mmap_mode='r',allow_pickle=False) if (folder/'sam.npy').exists() else assess(x,y,dr,report['scale'])[1]
  valid=np.isfinite(sam);ratio=np.clip(np.nan_to_num(sam,nan=0)/30,0,1)
  sam_rgb=np.stack([22+ratio*233,20+ratio*121,40+(1-ratio)*30],axis=-1)
  sam_rgb[~valid]=[128,128,128]
  if 'experiment' in report:
   low=np.load(folder/'low-resolution.npy',mmap_mode='r',allow_pickle=False)
   images=scene_display(x,y,low,report['experiment'],band)
  else:
   images={'truth':preview(x,band,dr),'prediction':preview(y,band,dr)}
  images.update(absolute_error=png(rgb),spectral_angle=png(sam_rgb))
  return dict(report=report,selection={'band':band,'row':row,'column':col,'roi':roi},roi_metrics=metrics,
     images=images,error_limit=error_limit,
     spectrum={'axis':report['wavelengths'] or list(range(b)),
               'axis_label':'波长（输入单位）' if report['wavelengths'] else '波段索引',
               'truth':np.asarray(x[row,col,:]).tolist(),'prediction':np.asarray(y[row,col,:]).tolist()})
 def get(self,path,query):
  if path=='/api/scenes':return {'scenes':catalog(),'scales':list(SCALES),'methods':[{'id':code,'name':value[0]} for code,value in METHODS.items()]}
  if path=='/api/thesis-table':
   return 200,(ROOT/'evidence/4.1_Pavia_comparison.csv').read_bytes(),'text/csv','pavia-table-4-1.csv'
  if path=='/api/thesis-image':
   model=query.get('model',[''])[0];view=query.get('view',[''])[0]
   if model not in ('ERCSR','MCArb_ERCSR') or view not in ('error','reconstruction'):raise ValueError('请选择归档图像')
   suffix='_error' if view=='error' else ''
   return 200,(ROOT/'thesis-final/images/pavia'/f'{model}_x4{suffix}.png').read_bytes(),'image/png'

  if path=='/api/history':
   rows=[]
   for p in sorted(self.root.glob('*/report.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:20]:
    r=json.loads(p.read_text())
    row={k:r[k] for k in ['id','created','source','shape','method','scale','data_range','truth_sha256']}
    if 'experiment' in r:row['scene_name']=r['experiment']['name']+' · '+r['experiment']['region']
    rows.append(row)
   return rows
  run=query.get('id',[''])[0];report=self.read(run)
  if path=='/api/cube':
   kind=query.get('kind',[''])[0]
   if kind not in ('prediction','low-resolution') or (kind=='low-resolution' and 'experiment' not in report):
    raise ValueError('本记录没有所选输出')
   return 200,(self.root/run/(kind+'.npy')).read_bytes(),'application/octet-stream',kind+'.npy'
  if path=='/api/report':return report
  if path=='/api/export':return 200,json.dumps(report,ensure_ascii=False,indent=2).encode(),'application/json','spectral-report.json'
  if path=='/api/view':
   roi=json.loads(query['roi'][0]) if query.get('roi') else None
   return self.view(run,int(query.get('band',[0])[0]),int(query.get('row',[0])[0]),int(query.get('column',[0])[0]),roi)
  raise ValueError('接口不存在')
if __name__=='__main__':
 sys.path.insert(0,str(ROOT.parent/'scripts'));from lab_http import serve
 serve(Workbench(),ROOT/'web',8782)
