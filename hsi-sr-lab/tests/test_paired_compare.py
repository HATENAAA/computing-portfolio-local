import copy
import unittest
from paired_compare import compare

def example():
    samples = [dict(id=str(i), scene='scene'+str(i//2), split='test') for i in range(6)]
    def run(name, shift):
        return dict(id=name, scale=4, summary={'MPSNR': {}, 'SAM_deg': {}}, samples=[
            dict(sample_id=str(i), truth_sha256='truth'+str(i), metrics={'MPSNR': 20+i+shift, 'SAM_deg': 4-shift})
            for i in range(6)])
    return dict(mode='synthetic', splits=samples, runs=[run('base', 0), run('new', 1)])

class PairedTests(unittest.TestCase):
    def test_known_improvement_and_determinism(self):
        r=example(); a=compare(r,'base','new')
        self.assertEqual(a,compare(r,'base','new'))
        for v in a['metrics'].values():
            self.assertEqual(v['mean_improvement'],1)
            self.assertEqual(v['confidence_interval_95'],[1,1])
            self.assertEqual(v['independent_scenes'],3)
    def test_cluster_equal_weights_and_single_scene(self):
        r=example()
        for s in r['splits']: s['scene']='one'
        a=compare(r,'base','new')['metrics']['MPSNR']
        self.assertIsNone(a['confidence_interval_95'])
        self.assertEqual(a['independent_scenes'],1)
    def test_pair_integrity(self):
        for change in ['hash','scale','missing']:
            r=example()
            if change=='hash':r['runs'][1]['samples'][0]['truth_sha256']='different'
            elif change=='scale':r['runs'][1]['scale']=8
            else:r['runs'][1]['samples'].pop()
            with self.assertRaises(ValueError):compare(r,'base','new')
    def test_undefined_values_use_paired_exclusion(self):
        r=example();r['runs'][0]['samples'][0]['metrics']['MPSNR']=None
        a=compare(r,'base','new')['metrics']['MPSNR']
        self.assertEqual(a['excluded_sample_ids'],['0'])
        self.assertEqual(a['paired_samples'],5)
    def test_unequal_patch_counts_do_not_overweight_scene(self):
        r=example()
        for s in r['splits']:s['scene']='A' if s['id']=='0' else 'B'
        r['runs'][1]['samples'][0]['metrics']['MPSNR']+=4
        self.assertEqual(compare(r,'base','new')['metrics']['MPSNR']['mean_improvement'],3)

if __name__=='__main__':unittest.main()
