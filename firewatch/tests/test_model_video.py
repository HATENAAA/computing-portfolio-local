import csv,json,tempfile,unittest,hashlib,time
from pathlib import Path
from unittest.mock import patch
import cv2,numpy as np
from fastapi import HTTPException
from app.model import ONNXDetector
from app.review import compare,CompareInput
from app.video_jobs import VideoJobs
from scripts.analyze_video import video_report

def model_fixture(folder):
    file=Path(__file__).parent/'fixtures/synthetic_detector.onnx'
    config=dict(model=str(file.resolve()),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),input_size=128,class_names=['synthetic_fixture'],target_classes=[0],output_layout='xyxy6')
    path=Path(folder)/'model.json';path.write_text(json.dumps(config));return path

def video_fixture(path):
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(128,96))
    if not writer.isOpened():raise RuntimeError('MJPG codec unavailable')
    for _ in range(20):writer.write(np.zeros((96,128,3),np.uint8))
    writer.release()

class ModelVideoTests(unittest.TestCase):
    def test_actual_onnx_video_preserves_rule_disagreement_model_provenance_and_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);video=root/'input.avi';video_fixture(video);model=ONNXDetector(model_fixture(root))
            report=video_report(video,root/'analysis',model=model,source_name='<test>.avi',sample_hz=5)
            self.assertEqual(report['decision_engine'],'model');self.assertEqual(report['model']['model_sha256'],model.sha256)
            self.assertEqual(len(report['events']),1);self.assertEqual(report['diagnostics']['disagreement_frames'],report['sampled_frames'])
            with (root/'analysis/timeline.csv').open() as f:rows=list(csv.DictReader(f))
            self.assertTrue(all(row['rule_candidate']=='False' for row in rows));self.assertIn('model_confidence',rows[0])
            page=(root/'analysis/review.html').read_text();self.assertIn('模型预测',page);self.assertIn('&lt;test&gt;.avi',page);self.assertNotIn('<test>.avi',page)
            review=dict(annotated=True,truth=[dict(start=0,end=report['duration_analyzed_s'])],version=1)
            result=compare(root/'analysis',CompareInput(thresholds=[.25,.95]),review)
            self.assertEqual(result['trials'][0]['evaluation']['tp'],1);self.assertEqual(result['trials'][1]['evaluation']['fn'],1)
            with self.assertRaises(HTTPException):compare(root/'analysis',CompareInput(thresholds=[.1]),review)
    def test_unconfigured_model_is_explicitly_rejected_without_creating_a_job(self):
        from test_app import client
        from app.main import VIDEO
        import app.model as module
        before=len(VIDEO.list())
        with patch.dict('os.environ',{'FIREWATCH_MODEL_CONFIG':'/missing/model-config.json'}),patch.object(module,'_cached',None):
            response=client.post('/api/videos',files={'file':('test.avi',b'dummy','video/x-msvideo')},data={'decision_engine':'model'})
            self.assertEqual(response.status_code,409);self.assertIn('不会回退',response.json()['detail'])
        self.assertEqual(len(VIDEO.list()),before)
    def test_upload_model_queue_to_report_and_terminal_cleanup(self):
        from test_app import client
        from app.main import VIDEO,REVIEWS
        import app.model as module
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);video=root/'input.avi';video_fixture(video);config=model_fixture(root)
            with patch.dict('os.environ',{'FIREWATCH_MODEL_CONFIG':str(config)}),patch.object(module,'_cached',None):
                response=client.post('/api/videos',files={'file':('test.avi',video.read_bytes(),'video/x-msvideo')},data={'decision_engine':'model','retain_source':'true','sample_hz':'2'})
                self.assertEqual(response.status_code,202,response.text);job=response.json()['id']
                VIDEO.futures[job].result(timeout=10)
                report=client.get(f'/api/videos/{job}/files/video-report.json').json();self.assertEqual(report['decision_engine'],'model');self.assertEqual(report['sample_hz'],2)
                listed=next(r for r in client.get('/api/videos').json() if r['id']==job);self.assertTrue(listed['source_retained']);self.assertGreater(listed['storage_bytes'],0)
                self.assertEqual(client.put(f'/api/videos/{job}/review',json={'version':0,'notes':'cleanup test'}).status_code,200)
                self.assertEqual(client.delete(f'/api/videos/{job}').status_code,200)
                self.assertFalse((VIDEO.root/job).exists());self.assertIsNone(VIDEO.get(job));self.assertEqual(REVIEWS.history(job),[])
                self.assertEqual(client.get(f'/api/videos/{job}/source').status_code,404)
    def test_active_job_cannot_be_deleted(self):
        with tempfile.TemporaryDirectory() as temp:
            jobs=VideoJobs(temp);self.addCleanup(jobs.close);job=jobs.create('uploading.avi')
            with self.assertRaises(ValueError):jobs.delete(job)
            jobs.cancel(job);self.assertTrue(jobs.delete(job));self.assertFalse(jobs.delete(job))
