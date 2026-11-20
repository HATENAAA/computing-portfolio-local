"""Paired, scene-clustered comparison of reconstruction evaluation reports."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np

LOWER_IS_BETTER = {'RMSE', 'SAM_deg', 'ERGAS'}
METRIC_NAMES = {'MPSNR', 'MSSIM', 'CrossCorrelation', 'RMSE', 'SAM_deg', 'ERGAS'}

def compare(report, baseline, candidate, *, seed=7319, resamples=2000):
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError('seed must be a uint32 integer')
    if type(resamples) is not int or not 100 <= resamples <= 10000:
        raise ValueError('resamples must be 100..10000')
    if baseline == candidate:
        raise ValueError('Choose distinct runs')
    runs = {r['id']: r for r in report['runs']}
    a, b = runs[baseline], runs[candidate]
    if a['scale'] != b['scale']:
        raise ValueError('Paired runs must use the same reconstruction scale')
    scenes = {s['id']: s['scene'] for s in report['splits'] if s['split'] == 'test'}
    aa = {s['sample_id']: s for s in a['samples']}
    bb = {s['sample_id']: s for s in b['samples']}
    if not aa or set(aa) != set(bb) or set(aa) != set(scenes):
        raise ValueError('Both runs must cover the identical complete test set')
    for sid in aa:
        if aa[sid]['truth_sha256'] != bb[sid]['truth_sha256']:
            raise ValueError('Paired ground truths differ')
    metrics = {}
    for metric in a['summary']:
        if metric not in METRIC_NAMES:continue
        groups, excluded = {}, []
        for sid in sorted(aa):
            av, bv = aa[sid]['metrics'].get(metric), bb[sid]['metrics'].get(metric)
            if av is None or bv is None:
                excluded.append(sid)
                continue
            if (isinstance(av, bool) or isinstance(bv, bool) or
                not isinstance(av, (int, float)) or not isinstance(bv, (int, float)) or
                not math.isfinite(av) or not math.isfinite(bv)):
                raise ValueError('Metric values must be finite numbers or null')
            improvement = (av - bv) if metric in LOWER_IS_BETTER else (bv - av)
            groups.setdefault(scenes[sid], []).append(improvement)
        # Give scenes equal weight. Patches from one scene are not independent replicates.
        means = np.array([np.mean(groups[k]) for k in sorted(groups)], dtype=float)
        ci = None
        if len(means) >= 2:
            rng = np.random.default_rng(seed)
            boot = np.mean(means[rng.integers(0, len(means), (resamples, len(means)))], axis=1)
            ci = [float(v) for v in np.quantile(boot, [.025, .975])]
        metrics[metric] = dict(
            mean_improvement=float(means.mean()) if len(means) else None,
            confidence_interval_95=ci, independent_scenes=len(means),
            paired_samples=sum(map(len, groups.values())), excluded_sample_ids=excluded,
            scene_improvements={k: float(np.mean(v)) for k, v in groups.items()},
            note='One scene: uncertainty across independent scenes cannot be estimated.' if len(means) == 1 else
                 'Descriptive percentile interval; few scenes limit inference. No multiple-comparison correction.')
    return dict(baseline=baseline, candidate=candidate, scale=a['scale'], mode=report['mode'],
                metrics=metrics, seed=seed, resamples=resamples,
                definition='Positive improvement always favours candidate; equal scene weights, paired within scene.',
                scope='Existing reconstruction outputs only; does not train models or establish statistical significance.')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path); p.add_argument('baseline'); p.add_argument('candidate')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); raw = a.report.read_bytes()
    result = compare(json.loads(raw), a.baseline, a.candidate)
    result['source_report_sha256'] = hashlib.sha256(raw).hexdigest()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(a.out)

if __name__ == '__main__': main()
