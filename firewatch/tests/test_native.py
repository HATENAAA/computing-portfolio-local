import unittest,tempfile,json,csv
from pathlib import Path
import cv2,numpy as np
from app.native_detector import analyze
from app.temporal import RollingEventGate
from app.review import compare,CompareInput
from scripts.analyze_video import video_report

def flame(seed=1):
 rng=np.random.default_rng(seed);image=np.zeros((128,160,3),np.uint8);noise=rng.integers(0,80,(70,60),dtype=np.uint8);image[25:95,45:105,0]=20;image[25:95,45:105,1]=100+noise;image[25:95,45:105,2]=240;return image
class NativeTests(unittest.TestCase):
 def test_kernel_outputs_regions_and_stable_hash(self):
  r,a=analyze(flame());self.assertEqual(r['algorithm'],'cpp-region-motion-v1');self.assertEqual(len(r['native_sha256']),64);self.assertTrue(r['boxes']);self.assertEqual(a['mask'].shape,(128,160))
 def test_static_orange_and_frozen_fire_image_do_not_gain_motion(self):
  for img in [np.full((128,160,3),(20,120,240),np.uint8),flame()]:
   r,_=analyze(img,previous=img.copy());self.assertFalse(r['detected']);self.assertEqual(r['motion_ratio'],0)
 def test_internal_fluctuations_form_candidate(self):
  r,_=analyze(flame(2),previous=flame(1));self.assertTrue(r['detected']);self.assertGreater(r['motion_ratio'],.02)
 def test_uniform_exposure_shift_not_mistaken_for_flicker(self):
  a=np.full((100,100,3),(10,80,170),np.uint8);b=np.full((100,100,3),(50,120,210),np.uint8);r,_=analyze(b,previous=a);self.assertFalse(r['detected'])
 def test_rolling_gate_tolerates_one_missed_sample_but_not_single_flash(self):
  gate=RollingEventGate(3,2)
  for n,value in enumerate([False,True,False,True,True,False,True]):gate.update(n/5,value)
  self.assertEqual(len(gate.finish()),1)
  gate=RollingEventGate(3,2)
  for n,value in enumerate([False,True,False,False,False,False]):gate.update(n/5,value)
  self.assertEqual(gate.finish(),[])
 def test_video_to_native_report_and_exact_threshold_replay(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);video=root/'synthetic.avi';writer=cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*'MJPG'),10,(160,128));self.assertTrue(writer.isOpened())
   for n in range(20):writer.write(flame(n))
   writer.release();report=video_report(video,root/'report',native=True)
   self.assertTrue(report['events']);self.assertEqual(report['rule_engine'],'cpp-region-motion-v1')
   replay=compare(root/'report',CompareInput(thresholds=[.02]),dict(annotated=False,version=0,truth=[]))
   self.assertEqual(replay['trials'][0]['events'],report['events'])
 def test_bad_frame_shape_rejected(self):
  with self.assertRaises(ValueError):analyze(np.zeros((3,3),np.uint8))

 def test_native_image_http_retains_actual_implementation_hash(self):
  from test_app import client
  raw=cv2.imencode('.png',flame())[1].tobytes();response=client.post('/api/native/analyze',files={'file':('synthetic.png',raw,'image/png')});self.assertEqual(response.status_code,200,response.text);r=response.json();self.assertEqual(r['native_sha256'],r['provenance']['detector_sha256'])
 def test_cpp_video_job_to_report_over_http(self):
  from test_app import client
  from app.main import VIDEO
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'sample.avi';writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(160,128))
   for n in range(20):writer.write(flame(n))
   writer.release();response=client.post('/api/videos',files={'file':('synthetic.avi',path.read_bytes(),'video/x-msvideo')},data={'decision_engine':'cpp'});self.assertEqual(response.status_code,202,response.text);job=response.json()['id'];VIDEO.futures[job].result(timeout=15);report=client.get('/api/videos/'+job+'/files/video-report.json').json();self.assertEqual(report['rule_engine'],'cpp-region-motion-v1');self.assertTrue(report['events'])
