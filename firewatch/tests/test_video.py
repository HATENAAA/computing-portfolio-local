import unittest,tempfile
from pathlib import Path
import cv2,numpy as np
from app.temporal import EventGate,event_metrics
from scripts.analyze_video import video_report
from app.detector import Config
import csv
class TemporalTests(unittest.TestCase):
 def test_isolated_flash_ignored(self):
  g=EventGate()
  for t,p in enumerate([False,True,False,False]):g.update(t,p)
  self.assertEqual(g.finish(),[])
 def test_confirmation_release_and_gap(self):
  g=EventGate()
  for t,p in enumerate([True,True,True,False,True,False,False]):g.update(t,p)
  self.assertEqual(g.finish(),[dict(start=0,confirmed_at=2,end=4)])
 def test_active_event_flushed_at_end(self):
  g=EventGate(2,2);g.update(0,True);g.update(1,True)
  self.assertEqual(g.finish()[0]['confirmed_at'],1)
 def test_timestamps_and_thresholds_rejected(self):
  with self.assertRaises(ValueError):EventGate(0,2)
  g=EventGate();g.update(1,False)
  with self.assertRaises(ValueError):g.update(1,False)
  with self.assertRaises(ValueError):g.update(float('nan'),False)
 def test_one_to_one_matching_does_not_double_count(self):
  p=[dict(start=1,end=4),dict(start=1,end=4)]
  m=event_metrics(p,[dict(start=1,end=4)])
  self.assertEqual((m['tp'],m['fp'],m['fn']),(1,1,0))
 def test_empty_metrics_and_invalid_intervals(self):
  self.assertIsNone(event_metrics([],[])['recall'])
  with self.assertRaises(ValueError):event_metrics([dict(start=1,end=1)],[])
 def test_missed_event_and_latency(self):
  m=event_metrics([dict(start=1,end=4,confirmed_at=2)],[dict(start=1,end=4),dict(start=8,end=9)])
  self.assertEqual(m['fn'],1);self.assertEqual(m['confirmation_delay_seconds'],[1])
 def test_video_codec_to_report_timeline_and_review(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'diagnostic.avi'
   writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(128,96))
   self.assertTrue(writer.isOpened())
   for i in range(40):
    image=np.zeros((96,128,3),np.uint8)
    if 4<=i<16 or 24<=i<26 or i>=30:image[20:80,20:100]=[0,190,255]
    writer.write(image)
   writer.release()
   out=Path(folder)/'analysis'
   r=video_report(path,out,truth=[dict(start=.4,end=1.6)])
   self.assertEqual(len(r['events']),2);self.assertEqual(r['event_evaluation']['fp'],1)
   self.assertEqual(r['event_evaluation']['tp'],1)
   self.assertTrue((out/'timeline.csv').exists());self.assertTrue(list(out.glob('review-*.jpg')))
 def test_invalid_video_rejected(self):
  with tempfile.TemporaryDirectory() as f:
   with self.assertRaises(ValueError):video_report(Path(f)/'missing.mp4',Path(f)/'out')
 def test_negative_result_keeps_review_evidence_and_explains_edge_rejection(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'sample.avi'
   writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(128,96))
   self.assertTrue(writer.isOpened())
   image=np.zeros((96,128,3),np.uint8)
   image[55:90,45:85]=[0,190,255]
   for x in range(4,128,8):image[4:45,x:x+3]=255
   for _ in range(40):writer.write(image)
   writer.release()
   out=Path(folder)/'default'
   report=video_report(path,out,source_name='<flame>.avi')
   self.assertEqual(report['events'],[])
   self.assertGreater(report['diagnostics']['max_area_ratio'],report['config']['min_area_ratio'])
   self.assertEqual(report['diagnostics']['reason_counts']['edge_below_threshold'],report['sampled_frames'])
   self.assertTrue(1<=len(report['review_frames'])<=12)
   for frame in report['review_frames']:self.assertTrue((out/frame['file']).is_file())
   page=(out/'review.html').read_text()
   self.assertIn('未形成候选事件',page);self.assertIn('&lt;flame&gt;.avi',page)
   self.assertIn('未提供人工事件标注',page);self.assertNotIn('<flame>.avi',page)
   with (out/'timeline.csv').open() as stream:rows=list(csv.DictReader(stream))
   self.assertIn('sobel_edge_ratio',rows[0]);self.assertIn('reason',rows[0])
   exploratory=video_report(path,Path(folder)/'exploratory',config=Config(edge_ratio=0))
   self.assertEqual(len(exploratory['events']),1)
   self.assertEqual(exploratory['config']['edge_ratio'],0)
 def test_isolated_candidate_frames_report_continuity_failure(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'flash.avi'
   writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(128,96))
   self.assertTrue(writer.isOpened())
   for _ in range(20):writer.write(np.zeros((96,128,3),np.uint8))
   writer.release()
   from app.detector import analyze as real_analyze
   result,assets=real_analyze(np.zeros((96,128,3),np.uint8))
   results=[]
   for i in range(10):results.append((dict(result,detected=i==2),assets))
   with patch('scripts.analyze_video.analyze',side_effect=results):
    report=video_report(path,Path(folder)/'out')
   self.assertEqual(report['diagnostics']['candidate_frames'],1)
   self.assertEqual(report['diagnostics']['longest_candidate_run'],1)
   self.assertIn('未达到连续确认条件',(Path(folder)/'out/review.html').read_text())
