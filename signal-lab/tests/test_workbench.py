import base64,csv,hashlib,io,tempfile,unittest
from pathlib import Path
import numpy as np
from workbench import Workbench
class InteractiveSignal(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.app=Workbench(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def analyze(self,config=None,**kw):return self.app.post('/api/analyze',{'config':config or {},**kw})
 def test_coherent_tone_gain_matches_analytic_filter_response(self):
  r=self.analyze();self.assertAlmostEqual(r['peak_hz'],50,places=7);self.assertEqual(r['samples'],3072)
  for t in r['tones']:self.assertAlmostEqual(t['gain_difference_db'],0,delta=.01)
 def test_alias_frequency_folds_but_does_not_claim_original_tone(self):
  r=self.analyze({'waveform':'sine','frequency':750,'second_frequency':750});self.assertEqual(r['aliases'][0]['folded_hz'],274);self.assertTrue(r['aliases'][0]['above_nyquist']);self.assertEqual(len(r['tones']),1);self.assertAlmostEqual(r['peak_hz'],274,places=7)
 def test_uploaded_filtered_samples_preserved_and_no_filter_inferred(self):
  t=np.arange(1024)/1024;x=np.sin(2*np.pi*50*t);y=.25*x;f=io.StringIO();w=csv.writer(f);w.writerow(['time_s','input','filtered']);w.writerows(zip(t,x,y));raw=f.getvalue().encode();r=self.analyze({'discard':0},csv_base64=base64.b64encode(raw).decode());self.assertEqual(r['source'],'uploaded-csv');self.assertIsNone(r['filter']);self.assertIsNone(r['tones'][1]['gain_db']);self.assertNotIn('theoretical_gain_db',r['tones'][0]);self.assertAlmostEqual(r['tones'][0]['gain_db'],20*np.log10(.25),places=8);self.assertEqual(r['source_sha256'],hashlib.sha256(raw).hexdigest())
 def test_csv_and_report_exports_retain_input_fingerprint(self):
  r=self.analyze();status,data,_,_=self.app.get('/api/csv',{'id':[r['id']]});self.assertEqual(status,200);self.assertEqual(r['input_sha256'],hashlib.sha256(data).hexdigest());self.assertEqual(self.app.get('/api/report',{'id':[r['id']]}),r)
 def test_invalid_parameters_do_not_publish_results(self):
  for c in [{'cutoff_hz':512},{'discard':4090},{'band':'bandpass','high_hz':50},{'samples':True},{'noise_std':float('nan')}]:
   with self.subTest(c=c),self.assertRaises(ValueError):self.analyze(c)
  self.assertEqual(list(Path(self.tmp.name).glob('*/report.json')),[])
 def test_nonuniform_csv_rejected(self):
  raw='time_s,input\n'+'\n'.join(f'{i*i/1024},0' for i in range(128))
  with self.assertRaises(ValueError):self.analyze({'discard':0},csv_base64=base64.b64encode(raw.encode()).decode())
 def test_all_waveform_and_filter_families_generate_finite_reports(self):
  for wave in ['sine','square','triangle','sawtooth','multitone','chirp','noise']:
   r=self.analyze({'waveform':wave,'filter':'chebyshev','band':'highpass','discard':1024});self.assertTrue(np.isfinite(r['rms_filtered']));self.assertEqual(r['filter']['family'],'chebyshev')
 def test_invalid_run_id_rejected(self):
  with self.assertRaises(ValueError):self.app.get('/api/csv',{'id':['../../private']})
if __name__=='__main__':unittest.main()
