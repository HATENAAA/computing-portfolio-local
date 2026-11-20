"""Source-disjoint temporal replay; validation-only parameter selection."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from .temporal import EventGate,event_metrics

def evaluate(spec):
 videos=spec['videos'];groups={};ids=set();hashes={}
 if spec.get('mode') not in ['synthetic','real']:raise ValueError('Declare synthetic or real')
 for v in videos:
  if v['id'] in ids or v['split'] not in ['validation','test'] or not math.isfinite(v['duration']) or v['duration']<=0:raise ValueError('Invalid video or split')
  ids.add(v['id']);g=v['source_group']
  if not g or (g in groups and groups[g]!=v['split']):raise ValueError('Source leakage across splits')
  groups[g]=v['split'];last=-1
  for row in v['timeline']:
   if not math.isfinite(row['time']) or not last<row['time']<v['duration']:raise ValueError('Invalid timestamp')
   last=row['time']
   for key in ['rule','model']:
    if not isinstance(row[key],(float,int)) or isinstance(row[key],bool) or not math.isfinite(row[key]) or not 0<=row[key]<=1:raise ValueError('Invalid scores')
  if len(v['timeline'])<2:raise ValueError('At least two samples per video')
  event_metrics([],v['truth'])
  if any(t['end']>v['duration'] for t in v['truth']):raise ValueError('Truth outside video')
  if spec['mode']=='real' and not all(v.get(k) for k in ['source_sha256','annotation_author','annotation_file_sha256']):raise ValueError('Real data needs source and annotation provenance')
  h=v.get('source_sha256') or hashlib.sha256(json.dumps(v['timeline'],sort_keys=True).encode()).hexdigest()
  if h in hashes and hashes[h]!=v['split']:raise ValueError('Duplicate video across splits')
  hashes[h]=v['split']
 if {v['split'] for v in videos}!={'validation','test'}:raise ValueError('Both splits required')
 def run(rows,method,threshold,on,tiou):
  outputs=[]
  for v in rows:
   gate=EventGate(on,2)
   for frame in v['timeline']:gate.update(frame['time'],bool(frame[method]>=threshold))
   dt=float(np.median(np.diff([f['time'] for f in v['timeline']])))
   events=[dict(e,end=min(v['duration'],e['end']+dt)) for e in gate.finish()]
   m=event_metrics(events,v['truth'],tiou);outputs.append(dict(id=v['id'],scene=v.get('scene','unspecified'),duration=v['duration'],truth_events=len(v['truth']),events=events,**m))
  tp=sum(v['tp'] for v in outputs);fp=sum(v['fp'] for v in outputs);fn=sum(v['fn'] for v in outputs);duration=sum(v['duration'] for v in outputs);delay=[d for v in outputs for d in v['confirmation_delay_seconds']]
  return dict(tp=tp,fp=fp,fn=fn,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0,false_alarms_per_hour=fp/(duration/3600),event_miss_rate=fn/(tp+fn) if tp+fn else None,alarm_delay_median_s=float(np.median(delay)) if delay else None,alarm_delay_p95_s=float(np.percentile(delay,95)) if delay else None,videos=outputs)
 result=dict(mode=spec['mode'],methods={},scope='确认延迟只统计匹配事件，未含解码/推理耗时；FP/小时以完整已标注时长为分母。来源独立性依赖声明与源指纹。')
 for method in ['rule','model']:
  validation=[v for v in videos if v['split']=='validation'];test=[v for v in videos if v['split']=='test']
  sweep=[dict(threshold=t,on_frames=n,metrics=run(validation,method,t,n,.5)) for t in [.2,.5,.8] for n in [1,3,5]]
  best=max(sweep,key=lambda x:(x['metrics']['f1'],-x['metrics']['fp'],-x['on_frames'],x['threshold']))
  frozen={k:best[k] for k in ['threshold','on_frames']}
  result['methods'][method]=dict(selected=frozen,validation_usable=best['metrics']['f1']>0,validation_sweep=sweep,test_iou_sensitivity={str(i):run(test,method,**{'threshold':frozen['threshold'],'on':frozen['on_frames'],'tiou':i}) for i in [.25,.5,.75]},confirmation_ablation=[dict(on_frames=n,metrics=run(test,method,frozen['threshold'],n,.5)) for n in [1,3,5]])
 return result
