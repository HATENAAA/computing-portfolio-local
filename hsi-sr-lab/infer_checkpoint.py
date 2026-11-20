"""CPU inference for the archived fixed-x4 ERCSR baseline, distinct from MCArb."""
from pathlib import Path
import argparse,json,time,hashlib,resource
import numpy as np

def infer(input_path,checkpoint,output):
 import torch
 from model.ERCSR import ERCSR
 torch.set_num_threads(2);x=np.load(input_path,allow_pickle=False)
 if x.ndim!=3 or not np.isfinite(x).all():raise ValueError('Expected finite HWC input')
 net=ERCSR(n_scale=4,n_colors=x.shape[2]);weights=torch.load(checkpoint,map_location='cpu',weights_only=True);net.load_state_dict(weights,strict=True);net.eval();tensor=torch.from_numpy(x.astype(np.float32).transpose(2,0,1)[None])
 with torch.inference_mode():
  start=time.perf_counter();y=net(tensor);seconds=time.perf_counter()-start
 p=Path(output)
 if p.exists():raise ValueError('Preserve existing evidence; use new output')
 p.mkdir(parents=True);np.save(p/'prediction.npy',y[0].numpy().transpose(1,2,0))
 sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
 r=dict(method='archived-fixed-x4-ERCSR-baseline',checkpoint_sha256=sha(checkpoint),input_sha256=sha(input_path),prediction_sha256=sha(p/'prediction.npy'),input_shape=list(x.shape),output_shape=list(y[0].shape[1:])+[int(y.shape[1])],inference_seconds=seconds,device='CPU',cpu_peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,gpu_peak_memory_bytes=None,scope='本次CPU前向；原历史固定倍率ERCSR基线，不是MCArb元上采样模型。耗时包含首轮初始化效应，进程峰值不是模型独占内存。')
 (p/'inference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));return r
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('checkpoint');a.add_argument('--out',required=True);v=a.parse_args();infer(v.input,v.checkpoint,v.out)
