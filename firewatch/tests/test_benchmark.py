import unittest
from app.benchmark import evaluate
class BenchTests(unittest.TestCase):
 def fixture(self):
  return dict(mode='synthetic',videos=[dict(id=split,source_group=split,split=split,duration=12,scene='synthetic',truth=[dict(start=2,end=8)],timeline=[dict(time=i+.01*k,rule=.9 if 2<=i<=7 or i==10 else .1,model=.8 if 2<=i<=7 else .05) for i in range(12)]) for k,split in enumerate(['validation','test'])])
 def test_frozen_iou_and_confirmation(self):
  r=evaluate(self.fixture());self.assertEqual(set(r['methods']['rule']['test_iou_sensitivity']),{'0.25','0.5','0.75'});a=r['methods']['rule']['confirmation_ablation'];self.assertGreater(a[0]['metrics']['fp'],a[1]['metrics']['fp']);self.assertLess(a[0]['metrics']['alarm_delay_median_s'],a[1]['metrics']['alarm_delay_median_s'])
 def test_source_leak(self):
  s=self.fixture();s['videos'][1]['source_group']='validation'
  with self.assertRaises(ValueError):evaluate(s)
 def test_nan_rejected(self):
  s=self.fixture();s['videos'][0]['timeline'][0]['model']=float('nan')
  with self.assertRaises(ValueError):evaluate(s)
