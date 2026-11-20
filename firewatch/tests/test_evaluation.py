import unittest,io,json,zipfile,hashlib,tempfile,os
from pathlib import Path
import cv2,numpy as np
from app.evaluation import iou,metrics,read_dataset,evaluate_archive
from app.main import decode

def box(x=1,y=1,w=10,h=10,score=None):
    b=dict(x=x,y=y,width=w,height=h,class_id=0)
    if score is not None:b['confidence']=score
    return b

def dataset(groups=('scene-a','scene-b'),same=False):
    manifest=dict(version=1,target_class=0,images=[]);out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for n,split in enumerate(('validation','test')):
            image=np.full((32,32,3),30 if same else 30+n*20,np.uint8)
            raw=cv2.imencode('.png',image)[1].tobytes();name=split+'.png';z.writestr(name,raw)
            manifest['images'].append(dict(id=split,file=name,group=groups[n],split=split,boxes=[[1,1,10,10]]))
        z.writestr('manifest.json',json.dumps(manifest))
    return out.getvalue()

class FakeModel:
    contract=dict(target_classes=[0],class_names=['fire'])
    def analyze(self,image,**kwargs):
        score=.9 if image[0,0,0]==30 else .8
        return dict(boxes=[box(score=score)],elapsed_ms=1,model_sha256='a'*64,adapter_sha256='b'*64,runtime={},input_size=640,output_layout='xyxy6'),image

class EvaluationTests(unittest.TestCase):
    def test_iou_and_all_point_ap(self):
        self.assertEqual(iou(box(),box()),1)
        s=[dict(id='a',truth=[box(),box(x=20)],predictions=[box(score=.9),box(x=40,score=.8),box(x=20,score=.7)])]
        m=metrics(s);self.assertEqual((m['tp'],m['fp'],m['fn']),(2,1,0));self.assertAlmostEqual(m['ap50'],5/6)
    def test_duplicate_and_localization_are_counted(self):
        m=metrics([dict(id='a',truth=[box()],predictions=[box(score=.9),box(score=.8),box(x=7,score=.7)])])
        self.assertEqual(m['tp'],1);self.assertEqual([x['type'] for x in m['errors']],['duplicate','localization'])
    def test_empty_predictions_are_all_misses(self):
        m=metrics([dict(id='a',truth=[box()],predictions=[])])
        self.assertEqual((m['ap50'],m['recall'],m['fn']),(0,0,1))
    def test_threshold_is_selected_only_on_validation(self):
        r=evaluate_archive(dataset(),FakeModel(),decode)
        self.assertEqual(r['selected_threshold'],.9)
        self.assertEqual(r['validation']['operating']['f1'],1)
        self.assertEqual(r['test']['operating']['tp'],0)
        self.assertEqual(r['test']['ap50'],1)
        self.assertEqual(len(r['dataset_sha256']),64)
    def test_source_group_leakage_rejected(self):
        with self.assertRaisesRegex(ValueError,'来源分组'):read_dataset(dataset(('same','same')),decode)
    def test_decoded_duplicate_leakage_rejected(self):
        with self.assertRaisesRegex(ValueError,'相同解码图像'):read_dataset(dataset(same=True),decode)
    def test_traversal_and_duplicate_zip_names_rejected(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('../secret','bad')
        with self.assertRaises(ValueError):read_dataset(b.getvalue(),decode)
    def test_model_class_mismatch_rejected(self):
        m=FakeModel();m.contract=dict(target_classes=[1],class_names=['fire','smoke'])
        with self.assertRaisesRegex(ValueError,'目标类别'):evaluate_archive(dataset(),m,decode)
    def test_out_of_bounds_annotation_rejected(self):
        raw=dataset();out=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(raw)) as z,zipfile.ZipFile(out,'w') as w:
            for name in z.namelist():
                b=z.read(name)
                if name=='manifest.json':m=json.loads(b);m['images'][0]['boxes']=[[0,0,100,100]];b=json.dumps(m).encode()
                w.writestr(name,b)
        with self.assertRaisesRegex(ValueError,'边界'):read_dataset(out.getvalue(),decode)

    def test_real_onnx_adapter_and_http_download(self):
        from test_app import client
        from test_model_video import model_fixture
        from unittest.mock import patch
        import app.model as module
        with tempfile.TemporaryDirectory() as folder:
            config=model_fixture(folder)
            with patch.dict(os.environ,{'FIREWATCH_MODEL_CONFIG':str(config)}),patch.object(module,'_cached',None):
                raw=dataset();response=client.post('/api/evaluations',files={'file':('test.zip',raw,'application/zip')})
                self.assertEqual(response.status_code,200,response.text)
                report=response.json();self.assertEqual(report['protocol'],'single-target-ap50-all-points-v1')
                self.assertEqual(report['model']['input_size'],128)
                saved=client.get('/api/evaluations/'+report['id']);self.assertEqual(saved.status_code,200)
                self.assertEqual(saved.json()['dataset_sha256'],hashlib.sha256(raw).hexdigest())
                self.assertEqual(client.get('/api/evaluations/../missing').status_code,404)
