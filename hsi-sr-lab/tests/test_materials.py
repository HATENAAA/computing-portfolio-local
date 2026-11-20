import unittest,tempfile,json
from pathlib import Path
import numpy as np
from reconstruct import reconstruct
from evidence_audit import audit
class MaterialTests(unittest.TestCase):
 def test_inference_input_output_and_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);np.save(p/'x.npy',np.ones((8,8,3)));r=reconstruct(p/'x.npy',2,p/'out');self.assertEqual(r['output_shape'],[16,16,3]);self.assertIsNone(r['gpu_peak_memory_bytes'])
   with self.assertRaises(ValueError):reconstruct(p/'x.npy',2,p/'out')
 def test_missing_not_complete(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'m.json';p.write_text(json.dumps(dict(runs=[dict(id='old',origin='historical')])));self.assertFalse(audit(p)['runs'][0]['complete'])
 def test_argument_dictionary_allowlist(self):
  from read_args import read
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'args.npy';np.save(p,{'seed':3407,'dataset_name':'Pavia'});self.assertEqual(read(p)['seed'],3407)
