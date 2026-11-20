"""Embed the reviewed venue records so file:// and GitHub Pages work offline."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def render():
    records = json.loads((ROOT / 'assets/evidence/city-places.json').read_text())
    contents = 'const atlasData = ' + json.dumps(records, ensure_ascii=False, separators=(',', ':')) + ';\n'
    atlas = ROOT / 'assets/atlas'
    (atlas / 'places.js').write_text(contents)
    revision = hashlib.sha256(contents.encode()).hexdigest()[:12]
    page = atlas / 'index.html'
    page.write_text(re.sub(r'places\.js(?:\?v=[a-f0-9]+)?(?=")', f'places.js?v={revision}', page.read_text()))

if __name__ == '__main__':
    render()
