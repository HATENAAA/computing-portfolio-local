import tempfile
from pathlib import Path
import unittest
from workbench import Workbench

class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.app=Workbench(self.root)
    def tearDown(self):
        self.temp.cleanup()
    def test_demo_reports_disjoint_groups_and_downloadable_artifacts(self):
        report=self.app.post('/api/train',{'demo':True})
        self.assertEqual(report['source'],'synthetic-example')
        self.assertEqual(report['samples'],120)
        self.assertFalse(set(report['train_groups']) & set(report['test_groups']))
        for name in ['report.json','predictions.csv','samples.csv','linear.joblib','svr.joblib']:
            response=self.app.get('/api/download',{'id':[report['id']],'file':[name]})
            self.assertEqual(response[0],200)
            self.assertTrue(response[1])
    def test_trained_pipeline_predicts_new_csv(self):
        report=self.app.post('/api/train',{'demo':True})
        output=self.app.post('/api/predict',{'id':report['id'],'model':'svr','units':'reflectance',
            'csv':'B2,B3,B4,B8,sample_id\n0.2,0.3,0.1,0.2,example\n'})
        self.assertEqual(output['count'],1)
        csv=self.app.get('/api/download',{'id':[report['id']],'file':['inference.csv']})[1]
        self.assertIn(b'predicted_depth_m',csv)
        self.assertIn(b'example',csv)
    def test_invalid_upload_cleans_up_and_download_cannot_escape_run(self):
        with self.assertRaises((ValueError,KeyError)):
            self.app.post('/api/train',{'csv':'B2,B3\n1,2','units':'reflectance'})
        self.assertEqual(list(self.root.iterdir()),[])
        with self.assertRaises(ValueError):
            self.app.get('/api/download',{'id':['../outside'],'file':['report.json']})
        report=self.app.post('/api/train',{'demo':True})
        with self.assertRaises(ValueError):
            self.app.get('/api/download',{'id':[report['id']],'file':['../source.py']})

if __name__=='__main__':unittest.main()
