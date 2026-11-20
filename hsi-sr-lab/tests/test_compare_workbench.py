import tempfile,unittest
from workbench import Workbench

class CompareWorkbenchTests(unittest.TestCase):
 def test_same_truth_pair_and_scope(self):
  with tempfile.TemporaryDirectory() as t:
   w=Workbench(t)
   a=w.post('/api/analyze',dict(demo=True,noise_std=.01))['report']
   b=w.post('/api/analyze',dict(demo=True,noise_std=.05))['report']
   r=w.post('/api/compare',dict(baseline=b['id'],candidate=a['id']))
   self.assertGreater(r['metrics']['MPSNR']['mean_improvement'],0)
   self.assertIsNone(r['metrics']['MPSNR']['confidence_interval_95'])
   self.assertEqual(r['mode'],'synthetic')
   self.assertEqual(len(r['source_reports_sha256']),2)
   with self.assertRaises(ValueError):w.post('/api/compare',dict(baseline=a['id'],candidate=a['id']))
 def test_scale_mismatch_and_invalid_ids(self):
  with tempfile.TemporaryDirectory() as t:
   w=Workbench(t)
   a=w.post('/api/analyze',dict(demo=True,scale=4))['report']
   b=w.post('/api/analyze',dict(demo=True,scale=8))['report']
   with self.assertRaises(ValueError):w.post('/api/compare',dict(baseline=a['id'],candidate=b['id']))
   with self.assertRaises(ValueError):w.post('/api/compare',dict(baseline=23,candidate=None))

if __name__=='__main__':unittest.main()
