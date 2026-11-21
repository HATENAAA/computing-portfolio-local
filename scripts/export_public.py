"""Export the existing catalogue and evidence as a standalone Pages site."""

import argparse
import json
from pathlib import Path
from shutil import copyfile

import render_catalog
import render_review

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    'bathymetry-example.json', 'chikusei-table-4-2.csv', 'city-places.json',
    'fire-image-candidates.jpg', 'flame-evaluation-setup.json', 'flame-results.json',
    'pavia-table-4-1.csv',
    'inventory-rollback-test.txt', 'inventory-test.txt', 'vr-recovery-tests.txt',
    'signal-h1.jpg', 'signal-sweep.json',
    'vr-flow-course.jpg', 'vr-flow-active.jpg', 'vr-flow-paused.jpg', 'vr-flow-summary.jpg',
    'furg-house6.mp4', 'bathymetry-input.csv', 'manufacturing-flow.json', 'hsi-auxiliary-table.csv',
)
FILES = (
    'assets/portfolio.js', 'assets/portfolio.css', 'assets/project-identities.css', 'assets/catalog.css',
    'assets/tokens.css', 'assets/review.css', 'assets/review.js', 'assets/medical-demo.js',
    'assets/public-data/furg-source.json', 'assets/public-data/furg-LICENSE.txt',
    'assets/public-data/reef-metadata.json',
    'case-studies/medical/images/patient-runtime.jpg', 'case-studies/medical/images/doctor-runtime.jpg',
    'hsi-sr-lab/thesis-final/images/pavia/ERCSR_x4.png',
    'hsi-sr-lab/thesis-final/images/pavia/MCArb_ERCSR_x4.png',
    'hsi-sr-lab/thesis-final/images/pavia/ERCSR_x4_error.png',
    'hsi-sr-lab/thesis-final/images/pavia/MCArb_ERCSR_x4_error.png',
    'hsi-sr-lab/thesis-final/source/LICENSE',
    'projects/credits.html', 'signal-lab/original/Virtual_Oscilloscope.vi',
)


# These are the linked public materials from the project pages.
PROJECT_PAGES = (
    'hsi', 'vrfitai', 'manufacturing', 'firewatch', 'signal', 'city', 'bathymetry',
    'medical', 'guide', 'guide-en', 'offline', 'ai-setup',
)
PROJECT_MATERIALS = (
    'preview/hsi-final.png', 'preview/signal-h1.jpg', 'preview/manufacturing-preview.jpg',
    'assets/public-data/furg-Car1.mp4', 'assets/public-data/mitdb-100-10s.csv',
    'assets/public-data/reef-points.csv',
    'hsi-sr-lab/thesis-final/README.md', 'hsi-sr-lab/thesis-final/manifest.json',
    'hsi-sr-lab/thesis-final/source/test_eval.py',
    'hsi-sr-lab/thesis-final/source/testeval2.py',
    'hsi-sr-lab/thesis-final/source/visualize.py',
)


def export(destination):
    destination = destination.resolve()
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError('Export to a new or empty folder.')
    render_catalog.render(destination)
    render_review.render(destination)
    records = json.loads((ROOT / 'assets/projects.json').read_text(encoding='utf-8'))
    previews = [f'preview/{project["image"]}' for project in records]
    thesis_images = [path.relative_to(ROOT).as_posix()
                     for path in sorted((ROOT / 'hsi-sr-lab' / 'thesis-final' / 'images').glob('*/*.png'))]
    detail_pages = [f'projects/{page}.html' for page in PROJECT_PAGES]
    ablations = [path.relative_to(ROOT).as_posix()
                 for path in sorted((ROOT / 'hsi-sr-lab' / 'evidence').glob('4.[3-6]_*.csv'))]
    atlas = [f.relative_to(ROOT).as_posix() for directory in ("assets/atlas","assets/studio") for f in (ROOT / directory).rglob("*") if f.is_file()]
    for name in dict.fromkeys((*FILES, *detail_pages, *PROJECT_MATERIALS, *atlas,
                               *(f'assets/evidence/{name}' for name in EVIDENCE), *previews, *thesis_images, *ablations)):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(ROOT / name, target)
    copyfile(ROOT / 'README.md', destination / 'README.md')
    (destination / '.nojekyll').touch()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    export(parser.parse_args().destination)
