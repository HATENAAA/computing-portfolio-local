"""Traceable evaluation of existing HWC reconstructions; does not train MCArb."""
import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path
from importlib.metadata import version
import numpy as np
from safe_metrics import assess

METRICS = ["MPSNR", "MSSIM", "CrossCorrelation", "RMSE", "SAM_deg", "ERGAS"]

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_cube(path):
    x = np.load(path, allow_pickle=False)
    if x.ndim != 3 or min(x.shape) < 1 or not np.isfinite(x).all():
        raise ValueError("Expected a finite nonempty HWC cube: " + str(path))
    return x

def overlaps(a, b):
    r, c, h, w = a; rr, cc, hh, ww = b
    return max(r, rr) < min(r+h, rr+hh) and max(c, cc) < min(c+w, cc+ww)

def validate(manifest_path):
    path = Path(manifest_path)
    spec = json.loads(path.read_text())
    if spec.get("mode") not in ("synthetic", "real"):
        raise ValueError("Declare mode as synthetic or real")
    if not isinstance(spec.get("experiment_id"), str) or not spec["experiment_id"].strip():
        raise ValueError("experiment_id is required")
    dr = spec.get("data_range")
    if not isinstance(dr, (int, float)) or isinstance(dr, bool) or not np.isfinite(dr) or dr <= 0:
        raise ValueError("Declare a positive finite data_range")
    samples = spec.get("samples", [])
    if {s.get("split") for s in samples} != {"train", "val", "test"}:
        raise ValueError("Record train, val and test samples")
    ids, fingerprints, checked = set(), {}, []
    for sample in samples:
        sid = sample.get("id")
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError("Missing or duplicate sample id")
        ids.add(sid)
        if not isinstance(sample.get("scene"), str) or not sample["scene"]:
            raise ValueError("Each sample requires a scene")
        window = sample.get("window")
        if (not isinstance(window, list) or len(window) != 4 or
            not all(type(v) is int for v in window) or min(window[:2]) < 0 or min(window[2:]) < 1):
            raise ValueError("window must be [row, column, height, width] in original-scene coordinates")
        p = (path.parent / sample["truth"]).resolve()
        x = read_cube(p)
        if tuple(window[2:]) != x.shape[:2]:
            raise ValueError("Window dimensions must match the truth cube")
        if x.min() < 0 or x.max() > dr:
            raise ValueError("Truth exceeds declared [0,data_range]; check units without per-image rescaling")
        fingerprint = hashlib.sha256(str(x.shape).encode()+np.ascontiguousarray(x,dtype="<f8").tobytes()).hexdigest()
        if fingerprint in fingerprints and fingerprints[fingerprint] != sample["split"]:
            raise ValueError("Identical ground-truth data appears across splits")
        fingerprints[fingerprint] = sample["split"]
        for other in checked:
            if other["scene"] == sample["scene"] and other["split"] != sample["split"] and overlaps(window, other["window"]):
                raise ValueError("Spatial overlap across splits: " + other["id"] + " / " + sid)
        checked.append({**sample, "path":p, "truth_sha256":digest(p)})
    test_ids = {s["id"] for s in checked if s["split"] == "test"}
    run_ids = set()
    runs = spec.get("runs", [])
    if not runs:
        raise ValueError("At least one reconstruction run is required")
    for run in runs:
        rid = run.get("id")
        if not isinstance(rid, str) or not rid or rid in run_ids:
            raise ValueError("Missing or duplicate run id")
        run_ids.add(rid)
        scale = run.get("scale")
        if not isinstance(scale,(int,float)) or isinstance(scale,bool) or not np.isfinite(scale) or scale <= 0:
            raise ValueError("Each run requires a finite positive scale")
        preds = run.get("predictions", [])
        pred_ids = [p.get("sample_id") for p in preds]
        if len(pred_ids) != len(set(pred_ids)) or set(pred_ids) != test_ids:
            raise ValueError("Every run must predict exactly the same complete test set")
        if spec["mode"] == "real":
            if not run.get("checkpoint") or not (path.parent/run["checkpoint"]).is_file():
                raise ValueError("Real neural-network runs require an existing checkpoint")
            if not run.get("config") or not (path.parent/run["config"]).is_file() or type(run.get("seed")) is not int:
                raise ValueError("Real runs require an existing configuration and integer seed")
        for pred in preds:
            pred_path = (path.parent / pred["path"]).resolve()
            truth = next(s for s in checked if s["id"] == pred["sample_id"])
            if read_cube(pred_path).shape != read_cube(truth["path"]).shape:
                raise ValueError("Prediction shape does not match HWC truth")
    return path, spec, checked

def evaluate(manifest, output):
    path, spec, samples = validate(manifest)
    output = Path(output)
    if output.exists():
        raise ValueError("Use a new output directory to preserve previous evidence")
    tests = {s["id"]: s for s in samples if s["split"] == "test"}
    report = {
        "experiment_id":spec["experiment_id"], "mode":spec["mode"],
        "scope":"Existing reconstruction evaluation only; no training or checkpoint inference executed",
        "layout":"HWC", "data_range":spec["data_range"],
        "manifest_sha256":digest(path),
        "metric_implementation_sha256":digest(Path(__file__).with_name("safe_metrics.py")),
        "environment":{"python":platform.python_version(),"numpy":np.__version__,"scikit-image":version("scikit-image")},
        "splits":[{k:v for k,v in s.items() if k!="path"} for s in samples], "runs":[]}
    for run in spec["runs"]:
        rows=[]
        for pred in run["predictions"]:
            s=tests[pred["sample_id"]];p=path.parent/pred["path"]
            metrics,_=assess(read_cube(s["path"]),read_cube(p),spec["data_range"],run["scale"])
            rows.append({"sample_id":s["id"],"truth_sha256":s["truth_sha256"],"prediction_sha256":digest(p),"metrics":metrics})
        summary={}
        for metric in METRICS:
            defined=[r["metrics"][metric] for r in rows if r["metrics"][metric] is not None]
            summary[metric]={"mean":float(np.mean(defined)) if defined else None,"defined":len(defined),"undefined":len(rows)-len(defined)}
        hashes={k+"_sha256":digest(path.parent/run[k]) for k in ("checkpoint","config") if run.get(k)}
        report["runs"].append({"id":run["id"],"scale":run["scale"],"seed":run.get("seed"),**hashes,"samples":rows,"summary":summary})
    from paired_compare import compare
    report['comparisons'] = [compare(report, pair['baseline'], pair['candidate'])
                             for pair in spec.get('comparisons', [])]
    output.mkdir(parents=True)
    (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    with (output/'summary.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['mode','run','scale','metric','mean','defined_samples','undefined_samples'])
        for run in report['runs']:
            for metric,value in run['summary'].items():w.writerow([spec['mode'],run['id'],run['scale'],metric,value['mean'],value['defined'],value['undefined']])
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    evaluate(a.manifest,a.out);print(a.out/'report.json')
if __name__=='__main__':main()
