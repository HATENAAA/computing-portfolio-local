import tempfile,unittest
from pathlib import Path
import numpy as np
from signal_check import spectrum,analyze
from reference_suite import generate
class SignalTests(unittest.TestCase):
 def test_known_sine_frequency_and_amplitude(self):
  t=np.arange(4096)/1024;f,a,fs=spectrum(t,2*np.sin(2*np.pi*50*t));k=np.argmax(a)
  self.assertEqual(f[k],50);self.assertAlmostEqual(a[k],2,places=5);self.assertEqual(fs,1024)
 def test_invalid_time_nan_and_short_records_rejected(self):
  for t,x in [(np.arange(20),np.ones(20)),(np.zeros(40),np.ones(40)),(np.arange(40),np.full(40,np.nan)),(np.r_[np.arange(39),40],np.ones(40))]:
   with self.assertRaises(ValueError):spectrum(t,x)
 def test_filter_measurement_matches_theoretical_response_and_aliasing(self):
  with tempfile.TemporaryDirectory() as temp:
   r=generate(temp)
   for row in r['filters']:
    self.assertLess(row['maximum_gain_error_db'],.01)
    self.assertGreater(row['tones'][0]['gain_db'],-2)
    self.assertLess(row['tones'][1]['gain_db'],-20)
   self.assertEqual(r['aliasing']['observed_peak_hz'],274)
 def test_no_unmeasurable_or_above_nyquist_gain_claim(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'zero.csv';np.savetxt(p,np.column_stack([np.arange(40)/100,np.zeros(40),np.zeros(40)]),delimiter=',',header='time_s,input,filtered',comments='')
   self.assertIsNone(analyze(p,[10])['tones'][0]['gain_db'])
   with self.assertRaises(ValueError):analyze(p,[60])
if __name__=='__main__':unittest.main()
