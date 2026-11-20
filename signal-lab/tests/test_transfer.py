import unittest,numpy as np
from scipy import signal
from transfer import estimate,study
class TransferTests(unittest.TestCase):
 def test_known_filter_and_circular_phase(self):
  r=study();rows=[v for v in r['rows'] if v['noise_std']==0 and v['window']==1024];self.assertTrue(all(v['gain_mae_db']<.2 and v['phase_mae_deg']<2 for v in rows))
 def test_low_excitation_and_single_segment(self):
  t=np.arange(1024)/1024;self.assertFalse(any(estimate(t,t*0,t*0,256)['reliable']));r=estimate(t,np.sin(t),np.sin(t),1024);self.assertFalse(any(r['reliable']))
 def test_noise_and_nonstationarity(self):
  rng=np.random.default_rng(8);t=np.arange(8192)/1024;x=rng.normal(size=len(t));r=estimate(t,x,rng.normal(size=len(t)),512);self.assertLess(sum(r['reliable']),5)
  chirp=signal.chirp(t,10,t[-1],400);self.assertFalse(estimate(t,chirp,chirp,512)['stationarity_screen_passed'])
 def test_bad_sampling(self):
  with self.assertRaises(ValueError):estimate([0]*128,[1]*128,[1]*128,32)
