"""Local grouped-regression workbench using the project's existing pipeline."""
from pathlib import Path
import csv, io, json, uuid, hashlib, sys
import numpy as np
import joblib
from pipeline import load_samples, train, BANDS
from predict import predict_samples

ROOT = Path(__file__).resolve().parent

def run_id(value):
    if not isinstance(value, str) or len(value)!=32 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('实验编号无效')
    return value

def demo_csv():
    rng=np.random.default_rng(42)
    stream=io.StringIO();writer=csv.writer(stream)
    writer.writerow([*BANDS,'depth_m','group_id','photon_date','image_date'])
    for group in range(8):
        for _ in range(15):
            bands=rng.uniform(.05,.65,4)
            depth=1+7*bands[0]+3*bands[1]+rng.normal(0,.12)
            writer.writerow([*bands,float(depth),'example-'+str(group),'2025-05-01','2025-05-01'])
    return stream.getvalue()

def validate_csv(text):
    if not isinstance(text,str) or not text.strip() or len(text.encode())>1024*1024:
        raise ValueError('请提供1MB以内的CSV文本')
    if len(text.splitlines())>1501:raise ValueError('交互评价最多1500行样本')
    return text

class Workbench:
    name='卫星测深回归分析'
    def __init__(self, root=None):
        self.root=Path(root or ROOT/'runs/interactive');self.root.mkdir(parents=True,exist_ok=True)
    def post(self,path,value):
        if path=='/api/train':
            text=demo_csv() if value.get('demo') else validate_csv(value.get('csv'))
            units='reflectance' if value.get('demo') else value.get('units','reflectance')
            identifier=uuid.uuid4().hex;folder=self.root/identifier;folder.mkdir()
            try:
                source=folder/'samples.csv';source.write_text(text)
                x,y,groups=load_samples(source,units)
                models,report=train(x,y,groups)
                report.update(id=identifier,source='synthetic-example' if value.get('demo') else 'uploaded-csv',
                              units=units,samples=len(y),group_count=len(set(groups)),
                              input_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
                (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
                with (folder/'predictions.csv').open('w',newline='') as stream:
                    writer=csv.writer(stream);writer.writerow(['source_row','synthetic_reference_depth_m' if value.get('demo') else 'reference_depth_m','linear_m','svr_m'])
                    writer.writerows(zip(report['test_rows'],report['test_depth_m'],report['predictions']['linear'],report['predictions']['svr']))
                for name,model in models.items():joblib.dump(dict(model=model,input_units='reflectance',bands=BANDS),folder/(name+'.joblib'))
                return report
            except Exception:
                import shutil;shutil.rmtree(folder);raise
        if path=='/api/predict':
            folder=self.root/run_id(value.get('id'));model=value.get('model','svr')
            if model not in ['linear','svr']:raise ValueError('请选择线性回归或SVR')
            text=validate_csv(value.get('csv'));source=folder/'new-samples.csv';source.write_text(text)
            report=predict_samples(folder/(model+'.joblib'),source,value.get('units','reflectance'),folder/'inference.csv')
            return dict(id=folder.name,**report)
        raise ValueError('接口不存在')
    def get(self,path,query):
        if path=='/api/example':return dict(csv=demo_csv())
        if path=='/api/download':
            folder=self.root/run_id(query.get('id',[''])[0]);name=query.get('file',[''])[0]
            if name not in ['report.json','predictions.csv','samples.csv','linear.joblib','svr.joblib','inference.csv','inference.metadata.json']:
                raise ValueError('文件不存在')
            mime='application/json' if name.endswith('.json') else 'text/csv; charset=utf-8' if name.endswith('.csv') else 'application/octet-stream'
            return 200,(folder/name).read_bytes(),mime,name
        raise ValueError('接口不存在')

if __name__=='__main__':
    sys.path.insert(0,str(ROOT.parent/'scripts'))
    from lab_http import serve
    serve(Workbench(),ROOT/'web',8784)
