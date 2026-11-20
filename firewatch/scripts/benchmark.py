import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.benchmark import evaluate
p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();spec=json.loads(a.manifest.read_text());r=evaluate(spec);r['manifest_sha256']=__import__('hashlib').sha256(a.manifest.read_bytes()).hexdigest();a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False))
