"""Keep the numbers exposed on the bilingual project pages tied to their inputs."""
import csv
import hashlib
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'assets/evidence'


def record(filename):
    return json.loads((DATA / filename).read_bytes())


class ProjectEvidence(unittest.TestCase):
    def test_bathymetry_samples_and_errors(self):
        run = record('bathymetry-example.json')
        source = DATA / 'bathymetry-input.csv'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), run['input_sha256'])
        with source.open() as f:
            samples = list(csv.DictReader(f))
        train, test = run['train_rows'], run['test_rows']
        self.assertEqual(sorted(train + test), list(range(len(samples))))
        groups = lambda rows: {samples[i]['group_id'] for i in rows}
        self.assertFalse(groups(train) & groups(test))
        self.assertEqual(groups(test), set(run['test_groups']))
        truth = [float(samples[i]['depth_m']) for i in test]
        self.assertEqual(len(truth),len(run['test_depth_m']))
        for actual, archived in zip(truth, run['test_depth_m']):
            self.assertAlmostEqual(actual, archived)
        for model, predictions in run['predictions'].items():
            self.assertEqual(len(predictions),len(truth))
            errors = [a - b for a, b in zip(predictions, truth)]
            self.assertAlmostEqual(math.sqrt(sum(e * e for e in errors) / len(errors)),run['metrics'][model]['rmse_m'])
            self.assertAlmostEqual(sum(map(abs, errors)) / len(errors),run['metrics'][model]['mae_m'])

    def test_original_observations(self):
        folder = ROOT / 'assets/public-data'
        meta = json.loads((folder/'reef-metadata.json').read_text())
        source = folder/'reef-points.csv'
        downloads = json.loads((folder/'downloads.json').read_text())
        expected = next(x['sha256'] for x in downloads if x['file'] == source.name)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), expected)
        with source.open() as f:
            rows = [r for r in csv.DictReader(f) if r['GT Num']]
        self.assertEqual(len(rows),meta['rows'])
        values = [float(r['Height (m MSL)']) for r in rows]
        self.assertEqual([min(values),max(values)],meta['msl_height_range_m'])

    def test_fire_and_thesis_archives(self):
        self.assertEqual((DATA/'flame-results.json').read_bytes(),(ROOT/'firewatch/app/static/research-report.json').read_bytes())
        for out,src in [('pavia-table-4-1.csv','4.1_Pavia_comparison.csv'),('chikusei-table-4-2.csv','4.2_Chikusei_comparison.csv')]:
            self.assertEqual((DATA/out).read_bytes(),(ROOT/'hsi-sr-lab/evidence'/src).read_bytes())
        report = record('flame-results.json')
        for method in report['methods'].values():
            for metrics in method['test_iou_sensitivity'].values():
                self.assertEqual(metrics['tp']+metrics['fn'],1)

    def test_atlas_references(self):
        data = record('city-places.json')
        places = {p['id']:p for p in data['places']}
        self.assertEqual(len(places),len(data['places']))
        self.assertEqual(set(places),{key for r in data['routes'] for key in r['stops']})
        district_bounds = {
            '黄浦区': (31.19, 31.25, 121.45, 121.52),
            '静安区': (31.21, 31.34, 121.42, 121.50),
            '虹口区': (31.23, 31.32, 121.45, 121.52),
            '徐汇区': (31.08, 31.23, 121.37, 121.49),
            '长宁区': (31.17, 31.25, 121.32, 121.46),
        }
        graph_script = (ROOT / 'assets/atlas/walking-data.js').read_text()
        nodes, edges = json.loads(graph_script.split('const walkingData = ', 1)[1].strip().rstrip(';'))
        adjacent = [set() for _ in nodes]
        for origin, destination, *_ in edges:
            adjacent[origin].add(destination)
            adjacent[destination].add(origin)
        for place in places.values():
            self.assertIn(place['source'],data['sources'].values())
            self.assertRegex(place['osm'],r'^https://www\.openstreetmap\.org/(node|way)/\d+$')
            lat,lon = place['position']
            south, north, west, east = district_bounds[place['address'][:3]]
            self.assertTrue(south < lat < north and west < lon < east, place['id'])
            self.assertTrue(0 <= place['walkNode'] < len(nodes), place['id'])
        station_nodes = {place['walkNode'] for place in places.values()}
        origin = next(iter(station_nodes))
        visited, pending = {origin}, [origin]
        while pending and not station_nodes <= visited:
            neighbors = adjacent[pending.pop()] - visited
            visited.update(neighbors)
            pending.extend(neighbors)
        self.assertTrue(station_nodes <= visited)
