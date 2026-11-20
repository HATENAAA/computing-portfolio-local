"""Runnable bicubic input-to-reconstruction baseline; does not claim MCArb inference."""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import zoom

def reconstruct(input_path,scale,out):
 x=np.load(input_path,allow_pickle=False)
 if x.ndim!=3 or not np.isfinite(x).all() or type(scale) is not int or not 2<=scale<=8:raise ValueError('Expected finite HWC and integer scale 2–8')
 start=time.perf_counter();y=zoom(x.astype(np.float32),(scale,scale,1),order=3,mode='reflect',prefilter=True);elapsed=time.perf_counter()-start
 out=Path(out)
 if out.exists():raise ValueError('Use new output directory')
 out.mkdir(parents=True);np.save(out/'prediction.npy',y)
 report=dict(method='bicubic-cpu-baseline',input_shape=list(x.shape),output_shape=list(y.shape),scale=scale,inference_seconds=elapsed,device='CPU',gpu_peak_memory_bytes=None,input_sha256=hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),prediction_sha256=hashlib.sha256((out/'prediction.npy').read_bytes()).hexdigest(),scope='新增插值基线；不加载神经网络权重，不代表MCArb结果，GPU显存不适用')
 (out/'inference.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--scale',type=int,required=True);p.add_argument('--out',required=True);a=p.parse_args();reconstruct(a.input,a.scale,a.out)
