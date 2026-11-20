"""Versioned human annotation and reproducible threshold replay, separate from predictions."""
import json,sqlite3,csv,hashlib,math
from datetime import datetime,timezone
from pathlib import Path
from pydantic import BaseModel,ConfigDict,Field
from typing import Literal
from fastapi import HTTPException
from .temporal import EventGate,RollingEventGate,event_metrics
class Interval(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 start:float=Field(ge=0);end:float=Field(gt=0)
class ReviewInput(BaseModel):
 model_config=ConfigDict(extra='forbid')
 version:int=Field(ge=0,strict=True)
 decision:Literal['unreviewed','candidate','false_alarm','inconclusive']='unreviewed'
 notes:str=Field(default='',max_length=2000)
 annotated:bool=False
 truth:list[Interval]=Field(default_factory=list,max_length=100)
class CompareInput(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 thresholds:list[float]=Field(min_length=1,max_length=12)
 on_frames:int=Field(default=3,ge=1,le=30,strict=True)
 off_frames:int=Field(default=2,ge=1,le=30,strict=True)
class ReviewStore:
 def __init__(self,root):
  self.db=Path(root)/'reviews.sqlite3'
  with self.connect() as c:c.executescript('CREATE TABLE IF NOT EXISTS reviews(job TEXT PRIMARY KEY,version INTEGER NOT NULL,payload TEXT NOT NULL); CREATE TABLE IF NOT EXISTS revisions(job TEXT,version INTEGER,payload TEXT NOT NULL,created TEXT NOT NULL,PRIMARY KEY(job,version));')
 def connect(self):return sqlite3.connect(self.db,timeout=10)
 def get(self,job):
  with self.connect() as c:row=c.execute('SELECT payload FROM reviews WHERE job=?',(job,)).fetchone()
  return json.loads(row[0]) if row else dict(version=0,decision='unreviewed',notes='',annotated=False,truth=[])
 def history(self,job):
  with self.connect() as c:rows=c.execute('SELECT payload,created FROM revisions WHERE job=? ORDER BY version DESC',(job,)).fetchall()
  return [dict(json.loads(p),saved_at=t) for p,t in rows]
 def save(self,job,value,report):
  truth=sorted([r.model_dump() for r in value.truth],key=lambda r:r['start'])
  if (not value.annotated and truth) or any(r['end']<=r['start'] or r['end']>report['duration_analyzed_s']+1e-6 for r in truth) or any(b['start']<a['end'] for a,b in zip(truth,truth[1:])):raise HTTPException(400,'标注须在已分析时段内，结束晚于开始，且不能重叠；有区间时需确认已标注。')
  payload=dict(value.model_dump(),truth=truth,version=value.version+1,source_sha256=report['source_sha256'])
  with self.connect() as c:
   c.execute('BEGIN IMMEDIATE');old=c.execute('SELECT version FROM reviews WHERE job=?',(job,)).fetchone()
   if (old[0] if old else 0)!=value.version:raise HTTPException(409,'复核已被其他页面更新，请重新载入后核对。')
   text=json.dumps(payload,ensure_ascii=False,allow_nan=False)
   c.execute('INSERT INTO reviews VALUES(?,?,?) ON CONFLICT(job) DO UPDATE SET version=excluded.version,payload=excluded.payload',(job,payload['version'],text))
   c.execute('INSERT INTO revisions VALUES(?,?,?,?)',(job,payload['version'],text,datetime.now(timezone.utc).isoformat()))
  return payload

def evaluate(report,review):
 return event_metrics(report['events'],review['truth']) if review['annotated'] else None

def compare(folder,value,review):
 if any(not math.isfinite(t) or not 0<=t<=1 for t in value.thresholds):raise HTTPException(400,'阈值须在0至1之间')
 folder=Path(folder);report=json.loads((folder/'video-report.json').read_text());raw=(folder/'timeline.csv').read_bytes()
 with (folder/'timeline.csv').open() as stream:rows=list(csv.DictReader(stream))
 if not rows or 'best_edge_ratio' not in rows[0]:raise HTTPException(409,'旧结果缺少逐帧得分，请用新版重新分析视频。')
 if report.get('decision_engine')=='model' and any(t<report['model']['confidence_threshold'] for t in value.thresholds):raise HTTPException(400,'模型重放阈值不能低于原分析阈值；低分框未保留，请降低上传阈值后重新分析。')
 trials=[]
 for threshold in value.thresholds:
  native=report.get('rule_engine')=='cpp-region-motion-v1'
  gate=(RollingEventGate if native else EventGate)(value.on_frames,value.off_frames);positive=0
  for row in rows:
   candidate=(int(row.get('model_boxes',0))>0 and float(row['model_confidence'])>=threshold) if report.get('decision_engine')=='model' else (float(row['best_edge_ratio'])>=threshold and float(row['area_ratio'])>=report['config']['min_area_ratio'] and row['reason'] not in ('no_color_region','area_below_threshold'))
   if native:candidate=row['native_spatial']=='True' and float(row['native_motion_ratio'])>=threshold and float(row['scene_motion_ratio'])<report['scene_motion_limit']
   gate.update(float(row['time_s']),candidate);positive+=gate.last_candidate if native else candidate
  events=gate.finish()
  for e in events:e['end']=min(report['duration_analyzed_s'],e['end']+1/report['sample_hz'])
  trials.append(dict(threshold=threshold,candidate_frames=positive,events=events,evaluation=event_metrics(events,review['truth']) if review['annotated'] else None))
 return dict(decision_engine=report.get('decision_engine','rules'),model=report.get('model'),trials=trials,annotation=review,annotation_sha256=hashlib.sha256(json.dumps(review,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),replay_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),temporal_sha256=hashlib.sha256((Path(__file__).parent/'temporal.py').read_bytes()).hexdigest(),source_sha256=report['source_sha256'],timeline_sha256=hashlib.sha256(raw).hexdigest(),review_version=review['version'],fixed_config=report['config'],on_frames=value.on_frames,off_frames=value.off_frames,scope='Exploratory replay of the same sampled frames, not independent validation; brightness and region filters remain fixed.')
