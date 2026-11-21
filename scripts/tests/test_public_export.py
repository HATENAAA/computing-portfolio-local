"""Check that the standalone portfolio contains the linked project materials."""
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from urllib.parse import unquote, urlsplit

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from export_public import ROOT, export


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src', 'poster'} and value:
                url = urlsplit(value)
                if not url.scheme and not url.netloc and url.path:
                    self.paths.add(unquote(url.path))


class PublicExportTests(unittest.TestCase):
    def test_shared_pages_and_project_materials_resolve_statically(self):
        with TemporaryDirectory() as folder:
            site = Path(folder).resolve()
            export(site)
            self.assertEqual((site/'index.html').read_bytes(), (ROOT/'index.html').read_bytes())
            self.assertFalse((site/'assets/local-apps.js').exists())
            for case in (site/'projects/review').glob('*.html'):
                self.assertEqual(case.read_bytes(), (ROOT/case.relative_to(site)).read_bytes())
            for page in site.rglob('*.html'):
                links = LocalLinks()
                links.feed(page.read_text(encoding='utf-8'))
                for path in links.paths:
                    with self.subTest(page=page.relative_to(site), path=path):
                        target = (page.parent/path).resolve()
                        if target.is_dir():
                            target /= 'index.html'
                        self.assertTrue(target.is_file())
                        self.assertTrue(target.is_relative_to(site))
