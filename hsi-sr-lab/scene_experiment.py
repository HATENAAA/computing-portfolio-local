"""Controlled, spatial-only resampling experiments on curated Pavia crops."""
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

from safe_metrics import assess

SCENE_DATA = Path(__file__).resolve().with_name('scene_data')
SCALES = (2, 4, 8)
METHODS = {
    'nearest': ('最近邻', Image.Resampling.NEAREST),
    'bilinear': ('双线性', Image.Resampling.BILINEAR),
    'bicubic': ('双三次', Image.Resampling.BICUBIC),
}


def digest_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def catalog(root=SCENE_DATA):
    try:
        scenes = json.loads((root / 'catalog.json').read_text())
    except FileNotFoundError:
        return []
    return [scene for scene in scenes if (root / (scene['id'] + '.npy')).is_file()]


def low_resolution(cube, scale):
    h, w, bands = cube.shape
    return cube.reshape(h // scale, scale, w // scale, scale, bands).mean(axis=(1, 3), dtype=np.float32)


def upsample(cube, scale, algorithm):
    h, w, bands = cube.shape
    result = np.empty((h * scale, w * scale, bands), dtype=np.float32)
    for band in range(bands):
        plane = Image.fromarray(cube[:, :, band])
        result[:, :, band] = np.asarray(plane.resize((w * scale, h * scale), algorithm))
    return result


def run_scene(scene, scale, method, root=SCENE_DATA):
    raw = (root / (scene['id'] + '.npy')).read_bytes()
    if hashlib.sha256(raw).hexdigest() != scene['sample_sha256']:
        raise ValueError('场景样本校验失败，请重新安装本地数据。')
    truth = np.load(io.BytesIO(raw), allow_pickle=False)
    if list(truth.shape) != scene['shape'] or truth.dtype != np.uint16:
        raise ValueError('场景样本格式与来源记录不一致。')
    low = low_resolution(truth, scale)
    results = []
    for key, (name, algorithm) in METHODS.items():
        candidate = upsample(low, scale, algorithm)
        metrics, sam = assess(truth, candidate, scene['data_range'], scale)
        if key == method:
            prediction, angles, summary = candidate, sam, metrics
        else:
            results.append({'name': name, 'method_id': key, 'metrics': metrics})
    return truth, low, prediction, angles, summary, results
