"""Regression coverage for the project pages blocked by the hub allowlist."""
import importlib.util
from pathlib import Path
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

spec = importlib.util.spec_from_file_location('portfolio_hub', Path(__file__).resolve().parents[1] / 'hub_server.py')
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)

class HubNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), hub.Hub)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, method='GET', host=None, extra_headers=None):
        conn = HTTPConnection('127.0.0.1', self.port, timeout=3)
        headers = {'Host': host} if host else {}
        headers.update(extra_headers or {})
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        result = response.status, {k.lower(): v for k, v in response.getheaders()}, response.read()
        conn.close()
        return result

    def test_all_five_project_pages_and_navigation_pages_are_served(self):
        for name in ['hsi', 'vrfitai', 'manufacturing', 'firewatch', 'signal', 'city', 'bathymetry', 'medical', 'offline', 'guide', 'credits', 'ai-setup']:
            with self.subTest(page=name):
                status, headers, body = self.request('/projects/' + name + '.html')
                self.assertEqual(status, 200)
                self.assertIn('text/html', headers['content-type'])
                self.assertIn('返回'.encode(), body)

    def test_assets_and_final_thesis_materials_are_served(self):
        for path in ['/assets/portfolio.css', '/assets/portfolio.js', '/preview/hsi-final.png',
                     '/hsi-sr-lab/thesis-final/source/test_eval.py',
                     '/hsi-sr-lab/thesis-final/images/pavia/MCArb_SSPSR_x4.png',
                     '/assets/projects.json','/assets/tokens.css','/assets/public-data/mitdb-100-10s.csv']:
            with self.subTest(path=path):
                status, _, body = self.request(path)
                self.assertEqual(status, 200)
                self.assertTrue(body)

    def test_head_has_the_same_status_and_no_body(self):
        status, headers, body = self.request('/projects/hsi.html', 'HEAD')
        self.assertEqual(status, 200)
        self.assertGreater(int(headers['content-length']), 0)
        self.assertEqual(body, b'')

    def test_private_files_listing_and_traversal_remain_unavailable(self):
        for path in ['/scripts/env.sh', '/vrfitai/.env', '/projects/', '/docs/',
                     '/hsi-sr-lab/thesis-final/source/', '/projects/%2e%2e/scripts/manage.py',
                     '/%2e%2e/README.md']:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)

    def test_unexpected_host_is_rejected(self):
        self.assertEqual(self.request('/projects/hsi.html', host='example.com')[0], 403)

    def test_old_conditional_request_gets_fresh_html(self):
        status, headers, body = self.request('/', extra_headers={'If-Modified-Since':'Tue, 01 Jan 2030 00:00:00 GMT'})
        self.assertEqual(status, 200)
        self.assertIn('no-store', headers['cache-control'])
        self.assertIn('按项目领域'.encode(), body)
        self.assertEqual(body, self.request('/local.html')[2])
        self.assertEqual(body.count(b'<article class="project"'), 8)
        self.assertEqual(body.count(b'class="launch-tile"'), 8)
        for project in (b'hsi', b'vrfitai', b'manufacturing', b'firewatch', b'signal', b'city', b'bathymetry', b'medical'):
            self.assertIn(b'data-id="' + project + b'"', body)
        self.assertIn(b'data-static-only', body)
        self.assertIn(b'data-local-hub', body)
        self.assertNotIn(b'evidence-count', body)
        self.assertIn('按项目领域'.encode(), self.request('/local.html')[2])

    def test_cv_files_are_no_longer_published(self):
        self.assertEqual(self.request('/CV/Jiawei_Wang_CV_CityU_CS.docx')[0], 404)

if __name__ == '__main__':
    unittest.main()
