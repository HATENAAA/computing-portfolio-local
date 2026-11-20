"""Evaluate a manifest/image ZIP using the same protocol as the web workspace."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.evaluation import evaluate_archive
from app.model import ONNXDetector
from app.image_io import decode

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('dataset',type=Path);p.add_argument('--model-config',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.dataset.stat().st_size>20*1024*1024:p.error('Dataset ZIP exceeds 20 MB')
    report=evaluate_archive(a.dataset.read_bytes(),ONNXDetector(a.model_config),decode)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'ap50':report['test']['ap50'],'threshold':report['selected_threshold'],'test_f1':report['test']['operating']['f1'],'report':str(a.output)},ensure_ascii=False))
if __name__=='__main__':main()
