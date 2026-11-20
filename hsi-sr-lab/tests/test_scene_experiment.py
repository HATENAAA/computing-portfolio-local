import io
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from scene_experiment import catalog, low_resolution, upsample
from workbench import Workbench


class SceneExperimentTests(unittest.TestCase):
    def test_downsampling_and_reconstruction_only_change_spatial_axes(self):
        cube = np.broadcast_to(np.array([7, 19, 142], dtype=np.uint16), (16, 16, 3))
        reduced = low_resolution(cube, 4)
        np.testing.assert_array_equal(reduced, cube[:4, :4, :])
        for method in (Image.Resampling.NEAREST, Image.Resampling.BILINEAR, Image.Resampling.BICUBIC):
            np.testing.assert_array_equal(upsample(reduced, 4, method), cube)

    def test_scene_metrics_downloads_and_cache_use_one_report_per_configuration(self):
        with tempfile.TemporaryDirectory() as root:
            bench = Workbench(root)
            scenes = catalog()
            self.assertEqual({scene['name'] for scene in scenes}, {'Pavia Centre', 'Pavia University'})
            payload = {'scene': 'centre-city', 'scale': 4, 'method': 'bicubic'}
            view = bench.post('/api/experiment', payload)
            report = view['report']
            self.assertEqual(report['source'], 'observed-scene')
            self.assertEqual(report['input_shape'], [28, 28, 102])
            self.assertEqual(report['shape'], [112, 112, 102])
            self.assertEqual({row['method_id'] for row in report['comparison']}, {'bilinear', 'nearest'})
            saved = bench.get('/api/cube', {'id':[report['id']], 'kind':['prediction']})
            self.assertEqual(np.load(io.BytesIO(saved[1]), allow_pickle=False).shape, (112,112,102))
            other = bench.post('/api/experiment', {**payload, 'method':'bilinear'})['report']
            paired = bench.post('/api/compare', {'baseline':report['id'], 'candidate':other['id']})
            self.assertEqual(paired['mode'], 'observed-scene')
            self.assertEqual(report['id'], bench.post('/api/experiment', payload)['report']['id'])
            self.assertEqual(len(list(Path(root).glob('*/report.json'))),2)
            with self.assertRaises(ValueError):
                bench.post('/api/experiment', {**payload,'scene':'../../any'})
