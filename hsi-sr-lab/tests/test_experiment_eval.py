import json
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
from experiment_eval import evaluate,validate

class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        rng=np.random.default_rng(7);self.samples=[]
        for i,split in enumerate(['train','val','test','test']):
            x=rng.uniform(.1,.9,(8,8,4));np.save(self.root/f'{i}.npy',x)
            if split=='test':np.save(self.root/f'p{i}.npy',x+.01)
            self.samples.append(dict(id=str(i),split=split,scene='scene',window=[i*16,0,8,8],truth=f'{i}.npy'))
        self.spec=dict(mode='synthetic',experiment_id='test',data_range=1,samples=self.samples,runs=[dict(id='synthetic-noise',scale=4,predictions=[dict(sample_id=str(i),path=f'p{i}.npy') for i in [2,3]])])
        self.path=self.root/'manifest.json';self.save()
    def tearDown(self):self.temp.cleanup()
    def save(self):self.path.write_text(json.dumps(self.spec))
    def test_end_to_end_records_metrics_splits_hashes_and_scope(self):
        r=evaluate(self.path,self.root/'out');self.assertEqual(r['mode'],'synthetic');self.assertEqual(len(r['splits']),4)
        self.assertAlmostEqual(r['runs'][0]['summary']['RMSE']['mean'],.01)
        self.assertEqual(r['runs'][0]['summary']['RMSE']['defined'],2)
        self.assertEqual(len(r['manifest_sha256']),64);self.assertTrue((self.root/'out/summary.csv').exists())
        with self.assertRaises(ValueError):evaluate(self.path,self.root/'out')
    def test_manifest_comparison_is_exported_and_rejects_cross_scale_pair(self):
        import copy
        other=copy.deepcopy(self.spec['runs'][0]);other['id']='second-run'
        self.spec['runs'].append(other)
        self.spec['comparisons']=[dict(baseline='synthetic-noise',candidate='second-run')]
        self.save();r=evaluate(self.path,self.root/'paired')
        self.assertEqual(r['comparisons'][0]['metrics']['RMSE']['mean_improvement'],0)
        self.assertIsNone(r['comparisons'][0]['metrics']['RMSE']['confidence_interval_95'])
        other['scale']=8;self.save()
        with self.assertRaisesRegex(ValueError,'same reconstruction scale'):evaluate(self.path,self.root/'bad')
        self.assertFalse((self.root/'bad').exists())
    def test_overlapping_windows_across_splits_rejected(self):
        self.spec['samples'][2]['window']=[4,0,8,8];self.save()
        with self.assertRaisesRegex(ValueError,'Spatial overlap'):validate(self.path)
    def test_duplicate_data_under_different_filename_rejected(self):
        shutil.copyfile(self.root/'0.npy',self.root/'2.npy')
        with self.assertRaisesRegex(ValueError,'Identical ground-truth'):validate(self.path)
    def test_unequal_or_duplicated_test_coverage_rejected(self):
        self.spec['runs'][0]['predictions'].pop();self.save()
        with self.assertRaisesRegex(ValueError,'complete test set'):validate(self.path)
    def test_real_runs_require_actual_provenance_files(self):
        self.spec['mode']='real';self.save()
        with self.assertRaisesRegex(ValueError,'checkpoint'):validate(self.path)
        (self.root/'weights.bin').write_bytes(b'test fixture, not trained weights');(self.root/'config.json').write_text('{}')
        self.spec['runs'][0].update(checkpoint='weights.bin',config='config.json',seed=1);self.save()
        r=evaluate(self.path,self.root/'out');self.assertEqual(len(r['runs'][0]['checkpoint_sha256']),64)
    def test_inconsistent_units_and_prediction_shape_rejected(self):
        self.spec['data_range']=.5;self.save()
        with self.assertRaisesRegex(ValueError,'Truth exceeds'):validate(self.path)
        self.spec['data_range']=1;self.save();np.save(self.root/'p2.npy',np.ones((3,3,4)))
        with self.assertRaisesRegex(ValueError,'shape'):validate(self.path)

if __name__=='__main__':unittest.main()
