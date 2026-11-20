import unittest
import numpy as np
from spectral_validation import power_check,fit_tones

class SpectralValidationTests(unittest.TestCase):
    def test_off_bin_two_tone_gain_and_phase(self):
        t=np.arange(4096)/1024;f,g=50.37,173.21
        x=2*np.sin(2*np.pi*f*t)+.4*np.cos(2*np.pi*g*t)+3
        y=.5*np.sin(2*np.pi*f*t-.7)+.2*np.cos(2*np.pi*g*t+.2)-1
        r=fit_tones(t,x,y,[f,g])
        self.assertAlmostEqual(r['tones'][0]['input_amplitude'],2,places=10)
        self.assertAlmostEqual(r['tones'][0]['gain_db'],20*np.log10(.25),places=10)
        self.assertAlmostEqual(r['tones'][0]['phase_difference_deg'],-.7*180/np.pi,places=10)
        self.assertLess(r['residual_rms_input'],1e-10)
    def test_parseval_even_odd_noise_and_dc(self):
        for n in [1023,1024]:
            t=np.arange(n)/1024;x=np.random.default_rng(19).normal(size=n)+7
            self.assertLess(power_check(t,x)['relative_error'],1e-12)
        self.assertIsNone(power_check(t,np.ones(n))['relative_error'])
    def test_unidentifiable_nearby_tones_rejected(self):
        t=np.arange(1024)/1024;x=np.sin(2*np.pi*50*t)
        with self.assertRaises(ValueError):fit_tones(t,x,x,[50,50+1e-12])
        with self.assertRaises(ValueError):fit_tones(t,x,x,[512])
    def test_zero_amplitude_does_not_invent_gain(self):
        t=np.arange(1024)/1024
        self.assertIsNone(fit_tones(t,t*0,t*0,[50])['tones'][0]['gain_db'])

if __name__=='__main__':unittest.main()
