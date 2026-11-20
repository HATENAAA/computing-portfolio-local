"""Audit material existence and bind file hashes; never invent historical training evidence."""
import json,hashlib,argparse
from pathlib import Path

def audit(manifest):
 p=Path(manifest);spec=json.loads(p.read_text());rows=[]
 for run in spec['runs']:
  entries={}
  for key in ['config','log','checkpoint','predictions_manifest']:
   name=run.get(key);f=p.parent/name if name else None
   entries[key]=dict(path=name,status='present' if f and f.is_file() else 'missing',sha256=hashlib.sha256(f.read_bytes()).hexdigest() if f and f.is_file() else None)
  rows.append(dict(id=run['id'],origin=run['origin'],seed=run.get('seed'),materials=entries,complete=all(v['status']=='present' for v in entries.values())))
 return dict(version=1,runs=rows,scope='文件齐备与哈希核对，不证明历史作者、训练真实性或预测来自指定权重。new-baseline 不等于历史 MCArb 复现。')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--out',required=True);a=p.parse_args();Path(a.out).write_text(json.dumps(audit(a.manifest),ensure_ascii=False,indent=2))
