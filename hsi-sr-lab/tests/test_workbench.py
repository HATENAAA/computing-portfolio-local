import base64,hashlib,io,json,tempfile,unittest
from pathlib import Path
import numpy as np
from workbench import Workbench,load_array

def encoded(x):
 f=io.BytesIO();np.save(f,x);return base64.b64encode(f.getvalue()).decode(),f.getvalue()
class InteractiveEvaluation(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.app=Workbench(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def upload(self,x,y,**kw):
  a,_=encoded(x);b,_=encoded(y);return self.app.post('/api/analyze',dict(truth=a,prediction=b,**kw))
 def test_exact_reconstruction_and_export_preserve_undefined_flags(self):
  x=np.arange(8*8*3).reshape(8,8,3)/200;v=self.upload(x,x);r=v['report'];self.assertEqual(r['metrics']['RMSE'],0);self.assertIsNone(r['metrics']['MPSNR']);self.assertTrue(r['metrics']['psnr_has_infinite_band']);self.assertEqual(r,self.app.get('/api/report',{'id':[r['id']]}));json.dumps(v,allow_nan=False)
 def test_roi_and_selected_pixel_are_independent_of_global_metrics(self):
  x=np.ones((8,9,3))*.5;y=x.copy();y[0,0]=.8;v=self.upload(x,y);r=v['report'];view=self.app.get('/api/view',{'id':[r['id']],'row':['0'],'column':['7'],'band':['2'],'roi':['[1,1,3,4]']});self.assertEqual(view['selection']['column'],7);self.assertEqual(view['roi_metrics']['RMSE'],0);self.assertGreater(view['report']['metrics']['RMSE'],0);self.assertEqual(view['spectrum']['truth'],[.5]*3)
 def test_out_of_range_prediction_is_not_clipped_for_metrics(self):
  x=np.ones((4,4,2))*.5;v=self.upload(x,x+1);self.assertEqual(v['report']['prediction_out_of_range_values'],32);self.assertEqual(v['report']['metrics']['RMSE'],1)
 def test_uploaded_and_saved_file_fingerprints(self):
  x=np.ones((4,4,2))*.5;v=self.upload(x,x*.9);r=v['report'];_,raw=encoded(x);self.assertEqual(r['input_hashes']['uploaded_truth_sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(r['prediction_sha256'],hashlib.sha256((Path(self.tmp.name)/r['id']/'prediction.npy').read_bytes()).hexdigest());self.assertEqual(len(r['implementation_sha256']),64)
 def test_synthetic_demo_is_labelled_and_has_interpolation_baseline(self):
  r=self.app.post('/api/analyze',{'demo':True,'noise_std':0})['report'];self.assertEqual(r['source'],'synthetic-diagnostic');self.assertTrue(r['metrics']['psnr_has_infinite_band']);self.assertEqual(len(r['comparison']),1);self.assertIn('no model training',r['scope'])
 def test_shape_range_and_wavelength_constraints(self):
  x=np.ones((4,4,2))*.5
  for y,kw in [(x[:3],{}),(x,{'data_range':.1}),(x,{'wavelengths':[500,400]}),(x,{'wavelengths':[500]})]:
   with self.subTest(kw=kw),self.assertRaises(ValueError):self.upload(x,y,**kw)
  self.assertEqual(list(Path(self.tmp.name).glob('*/report.json')),[])
 def test_rejects_object_nonfinite_and_oversized_headers_before_allocation(self):
  for x in [np.array([[[{}]]],dtype=object),np.full((2,2,2),np.nan),np.full((2,2,2),1e100)]:
   _,raw=encoded(x)
   with self.assertRaises(ValueError):load_array(raw)
  f=io.BytesIO();np.lib.format.write_array_header_1_0(f,{'descr':'<f8','fortran_order':False,'shape':(999999,999999,16)})
  with self.assertRaises(ValueError):load_array(f.getvalue())
 def test_invalid_roi_and_path_id(self):
  r=self.app.post('/api/analyze',{'demo':True})['report']
  with self.assertRaises(ValueError):self.app.view(r['id'],0,0,0,[0,0,999,1])
  with self.assertRaises(ValueError):self.app.read('../secret')
if __name__=='__main__':unittest.main()
