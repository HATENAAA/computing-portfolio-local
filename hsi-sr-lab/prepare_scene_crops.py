"""Prepare crops from the checksum-verified HPC4RS Pavia .mat files."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat

RECORD = 'https://doi.org/10.5281/zenodo.10638886'
ORIGINAL = 'https://www.ehu.eus/ccwintco/index.php/Hyperspectral_Remote_Sensing_Scenes'
LICENSE = 'https://creativecommons.org/licenses/by-nc-sa/3.0/'
SOURCES = (
    ('Pavia Centre', 'PaviaCentre.mat', 'pavia', 'dc21f27749d702b26b68e16658322376', (1096, 715, 102),
     (('centre-city', '市中心街区', 0, 32), ('centre-river', '河岸与道路', 150, 414))),
    ('Pavia University', 'PaviaUniversity.mat', 'paviaU', '165a3c7488995f54a19add47c7eed4cd', (610, 340, 103),
     (('university', '大学校区', 104, 68),)),
)

def prepare(inputs, out):
    out.mkdir(parents=True, exist_ok=True)
    records = []
    side = 112
    for dataset, filename, variable, expected_md5, expected_shape, crops in SOURCES:
        path = inputs / filename
        md5, sha = hashlib.md5(), hashlib.sha256()
        with path.open('rb') as stream:
            while data := stream.read(1024 * 1024):
                md5.update(data)
                sha.update(data)
        if md5.hexdigest() != expected_md5:
            raise ValueError(f'Checksum mismatch: {filename}')
        scene = loadmat(path, variable_names=[variable])[variable]
        if scene.shape != expected_shape or scene.dtype != np.uint16 or int(scene.max()) != 8000:
            raise ValueError(f'Unexpected array: {filename}')
        for scene_id, region, row, column in crops:
            cube = np.ascontiguousarray(scene[row:row + side, column:column + side, :])
            if np.any(np.all(cube == 0, axis=-1)):
                raise ValueError(f'No-data pixels in {scene_id}')
            sample = out / f'{scene_id}.npy'
            np.save(sample, cube, allow_pickle=False)
            records.append(dict(
                id=scene_id, name=dataset, region=region, sensor='ROSIS', gsd_m=1.3,
                scene_shape=list(expected_shape), crop=[row, column, side, side], shape=list(cube.shape),
                data_range=8000, unit='DN', rgb_bands=[55, 41, 12], archive=RECORD, original=ORIGINAL,
                archive_file=filename, archive_md5=expected_md5, archive_sha256=sha.hexdigest(),
                credit='Paolo Gamba, University of Pavia; HPC4RS, CiTIUS / Universidade de Santiago de Compostela',
                license='CC BY-NC-SA 3.0', license_url=LICENSE, sample_sha256=hashlib.sha256(sample.read_bytes()).hexdigest(),
            ))
    (out / 'catalog.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path)
    parser.add_argument('out', type=Path)
    a = parser.parse_args()
    prepare(a.inputs, a.out)
