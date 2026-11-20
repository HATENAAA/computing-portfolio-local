import unittest,tempfile,json,csv,hashlib
from pathlib import Path
from unittest.mock import patch
import numpy as np,cv2
from fastapi import HTTPException
from app.review import ReviewStore,ReviewInput,CompareInput,compare,evaluate
from app.model import letterbox,decode_output,ONNXDetector
class ReviewTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.store=ReviewStore(self.root)
  self.report=dict(source_sha256='a'*64,duration_analyzed_s=3,events=[],sample_hz=1,config={'min_area_ratio':.002,'edge_ratio':.6})
  (self.root/'video-report.json').write_text(json.dumps(self.report))
  (self.root/'timeline.csv').write_text('time_s,best_edge_ratio,area_ratio,reason\n0,.5,.2,edge_below_threshold\n1,.5,.2,edge_below_threshold\n2,.5,.2,edge_below_threshold\n')
 def test_no_annotation_and_explicit_negative_are_distinct(self):
  self.assertIsNone(evaluate(self.report,self.store.get('job')))
  r=self.store.save('job',ReviewInput(version=0,annotated=True),self.report)
  self.assertEqual(evaluate(self.report,r)['fp'],0);self.assertIsNone(evaluate(self.report,r)['recall'])
 def test_annotation_bounds_overlap_and_conflicts_preserve_history(self):
  for truth in [[{'start':2,'end':1}],[{'start':0,'end':4}],[{'start':0,'end':2},{'start':1,'end':3}]]:
   with self.assertRaises(HTTPException):self.store.save('job',ReviewInput(version=0,annotated=True,truth=truth),self.report)
  self.store.save('job',ReviewInput(version=0,notes='first'),self.report)
  with self.assertRaises(HTTPException) as err:self.store.save('job',ReviewInput(version=0,notes='stale'),self.report)
  self.assertEqual(err.exception.status_code,409);self.assertEqual(len(self.store.history('job')),1);self.assertEqual(self.store.get('job')['notes'],'first')
 def test_same_video_threshold_replay_and_metrics_are_traceable(self):
  review=self.store.save('job',ReviewInput(version=0,annotated=True,truth=[{'start':0,'end':3}]),self.report)
  result=compare(self.root,CompareInput(thresholds=[.45,.6]),review)
  self.assertEqual(result['trials'][0]['evaluation']['tp'],1);self.assertEqual(result['trials'][1]['evaluation']['fn'],1);self.assertEqual(result['review_version'],1)
  self.assertEqual(result['timeline_sha256'],hashlib.sha256((self.root/'timeline.csv').read_bytes()).hexdigest())
 def test_invalid_threshold_and_old_timeline_rejected(self):
  with self.assertRaises(HTTPException):compare(self.root,CompareInput(thresholds=[1.2]),self.store.get('job'))
  (self.root/'timeline.csv').write_text('time_s,candidate\n0,False\n')
  with self.assertRaises(HTTPException):compare(self.root,CompareInput(thresholds=[.4]),self.store.get('job'))
class ModelTests(unittest.TestCase):
 def fixture_config(self,root):
  fixture=Path(__file__).parent/'fixtures/synthetic_detector.onnx'
  v=dict(model=str(fixture.resolve()),sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),input_size=128,class_names=['synthetic_fixture'],target_classes=[0],output_layout='xyxy6')
  path=Path(root)/'config.json';path.write_text(json.dumps(v));return path
 def test_real_onnx_forward_and_coordinate_restore(self):
  with tempfile.TemporaryDirectory() as root:
   model=ONNXDetector(self.fixture_config(root));image=np.zeros((64,128,3),np.uint8);result,overlay=model.analyze(image)
   self.assertEqual(len(result['boxes']),1);box=result['boxes'][0];self.assertEqual((box['x'],box['y'],box['width'],box['height']),(32,0,64,64));self.assertEqual(overlay.shape,image.shape)
   self.assertEqual(len(model.analyze(image,confidence=.95)[0]['boxes']),0)
 def test_letterbox_round_trip_and_class_aware_nms(self):
  _,t=letterbox(np.zeros((100,200,3),np.uint8),128)
  out=np.array([[[32,48,96,80,.9,0],[33,49,95,79,.8,0],[32,48,96,80,.85,1]]],np.float32)
  config=dict(output_layout='xyxy6',class_names=['a','b'],target_classes=[0,1]);boxes=decode_output(out,config,t)
  self.assertEqual(len(boxes),2);self.assertAlmostEqual(boxes[0]['x'],50);self.assertAlmostEqual(boxes[0]['y'],25)
 def test_raw_yolov8_contract_and_bad_outputs(self):
  _,t=letterbox(np.zeros((128,128,3),np.uint8),128);v=dict(output_layout='yolov8-raw',class_names=['fire'],target_classes=[0])
  out=np.array([[[64],[64],[40],[40],[.9]]],np.float32)
  self.assertEqual(decode_output(out,v,t)[0]['width'],40)
  for bad in [np.array([[[float('nan')]]]),np.zeros((1,6,2)),np.ones((1,5,1))*2]:
   with self.assertRaises(ValueError):decode_output(bad,v,t)
 def test_hash_mismatch_prevents_loading(self):
  with tempfile.TemporaryDirectory() as root:
   path=self.fixture_config(root);v=json.loads(path.read_text());v['sha256']='0'*64;path.write_text(json.dumps(v))
   with self.assertRaises(ValueError):ONNXDetector(path)
class ReviewApiTests(unittest.TestCase):
 def test_review_compare_export_source_range_and_model_inference(self):
  from test_app import client
  from app.main import VIDEO
  job=VIDEO.create('review-test.mp4');folder=VIDEO.root/job;analysis=folder/'analysis';analysis.mkdir()
  report=dict(source='review-test.mp4',source_sha256='a'*64,duration_analyzed_s=3,events=[],sample_hz=1,config={'min_area_ratio':.002,'edge_ratio':.6},review_frames=[],sampled_frames=3)
  (analysis/'video-report.json').write_text(json.dumps(report));(analysis/'timeline.csv').write_text('time_s,best_edge_ratio,area_ratio,reason\n0,.5,.2,edge_below_threshold\n1,.5,.2,edge_below_threshold\n2,.5,.2,edge_below_threshold\n');(folder/'source.video').write_bytes(b'0123456789');VIDEO.update(job,status='completed')
  base='/api/videos/'+job
  self.assertEqual(client.get('/review/'+job).status_code,200)
  r=client.put(base+'/review',json={'version':0,'annotated':True,'truth':[{'start':0,'end':3}],'decision':'candidate','notes':'test'})
  self.assertEqual(r.status_code,200,r.text);self.assertEqual(client.put(base+'/review',json={'version':0}).status_code,409)
  self.assertEqual(client.post(base+'/compare',json={'thresholds':[.45]}).json()['trials'][0]['evaluation']['tp'],1)
  self.assertEqual(client.get(base+'/review-export').json()['review']['version'],1)
  self.assertEqual(client.get(base+'/source',headers={'Range':'bytes=0-3'}).status_code,206)
  with tempfile.TemporaryDirectory() as root:
   path=ModelTests().fixture_config(root)
   import app.model as model
   with patch.dict('os.environ',{'FIREWATCH_MODEL_CONFIG':str(path)}),patch.object(model,'_cached',None):
    raw=cv2.imencode('.png',np.zeros((64,128,3),np.uint8))[1].tobytes();r=client.post('/api/model/analyze',files={'file':('test.png',raw,'image/png')})
    self.assertEqual(r.status_code,200,r.text);self.assertEqual(len(r.json()['model']['boxes']),1);self.assertFalse(r.json()['baseline']['detected'])
