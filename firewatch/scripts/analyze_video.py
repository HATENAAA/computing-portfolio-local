"""Offline video review; rule candidates are not confirmed fires."""
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
from app.detector import analyze,Config
from app.temporal import EventGate,RollingEventGate,event_metrics
from scripts.video_review import render_review

def video_report(path, output, *, sample_hz=5, on_frames=3, off_frames=2, truth=None, max_seconds=300, progress=None, cancelled=None, config=None, source_name=None, model=None, confidence=.25, nms_iou=.45,native=False):
    if not math.isfinite(sample_hz) or not 1<=sample_hz<=30:raise ValueError('sample_hz must be 1..30')
    if not math.isfinite(max_seconds) or not 0<max_seconds<=300:raise ValueError('max_seconds must be 0..300')
    if not 0<=confidence<=1 or not 0<=nms_iou<=1 or not math.isfinite(confidence+nms_iou):raise ValueError('invalid model thresholds')
    path=Path(path);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()):raise ValueError('output directory must be empty to avoid stale review files')
    gate=(RollingEventGate if native else EventGate)(on_frames,off_frames);previous=None;cap=cv2.VideoCapture(str(path))
    if not cap.isOpened():raise ValueError('video could not be opened')
    rows=[];frames=0;next_time=0;limited=False
    cfg=config or Config()
    snapshots=[];best=None;positive_run=0;longest_run=0;model_metadata=None
    try:
        fps=cap.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps<=0 or fps>240:raise ValueError('valid constant-rate FPS metadata required')
        total=cap.get(cv2.CAP_PROP_FRAME_COUNT)
        estimate=min(total/fps,max_seconds) if math.isfinite(total) and total>0 else max_seconds
        snapshot_step=max(1,math.ceil(estimate*sample_hz/11))
        while True:
            if cancelled and cancelled():raise InterruptedError('Video analysis cancelled')
            ok,image=cap.read()
            if not ok:break
            timestamp=frames/fps;frames+=1
            if progress and frames%10==0:
                total=cap.get(cv2.CAP_PROP_FRAME_COUNT)
                fraction=min(.99,frames/max(1,min(total,max_seconds*fps))) if total>0 else None
                progress(fraction)
            if timestamp>=max_seconds:limited=True;break
            if image.size>12_000_000*3:raise ValueError('video frame pixel limit exceeded')
            if timestamp+1e-9<next_time:continue
            next_time=timestamp+1/sample_hz
            result,assets=analyze(image,cfg);candidate=result['detected'];native_result=None
            if native:
                from app.native_detector import analyze as cpp_analyze
                native_result,assets=cpp_analyze(image,cfg,previous);previous=image.copy();candidate=native_result['detected'] and native_result['has_previous']
            rule_candidate=candidate;model_result=None
            if model is not None:
                model_result,model_overlay=model.analyze(image,confidence,nms_iou)
                candidate=model_result['detected'];assets['overlay']=model_overlay
                if model_metadata is None:model_metadata={k:v for k,v in model_result.items() if k not in ('boxes','detected','elapsed_ms')}
            raw_candidate=candidate
            gate.update(timestamp,candidate)
            if native:candidate=gate.last_candidate
            score=max(m['edge_color_ratio'] for m in result['methods'])
            reason=('candidate' if candidate else 'no_color_region' if not result['boxes'] else
                    'area_below_threshold' if result['area_ratio']<cfg.min_area_ratio else 'edge_below_threshold')
            row=dict(time_s=timestamp,candidate=candidate,area_ratio=result['area_ratio'],best_edge_ratio=score,reason=reason)
            row.update({m['method'].lower()+'_edge_ratio':m['edge_color_ratio'] for m in result['methods']})
            row['rule_candidate']=rule_candidate
            if native:
                row['area_ratio']=native_result['area_ratio']
                row.update(native_raw_candidate=raw_candidate,native_spatial=any(b['spatial_candidate'] for b in native_result['boxes']),native_motion_ratio=native_result['motion_ratio'],scene_motion_ratio=native_result['scene_motion_ratio'])
                row['reason']='candidate' if candidate else native_result['reason']
                if row['reason']=='candidate' and not candidate:row['reason']='awaiting_temporal_confirmation'
            if model_result is not None:
                row['model_confidence']=max((b['confidence'] for b in model_result['boxes']),default=0.)
                row['model_boxes']=len(model_result['boxes'])
                row['model_elapsed_ms']=model_result['elapsed_ms']
                row['reason']='candidate' if candidate else 'model_below_threshold'
            row['ranking_score']=native_result['motion_ratio'] if native else row.get('model_confidence',score)
            rows.append(row)
            positive_run=positive_run+1 if candidate else 0;longest_run=max(longest_run,positive_run)
            selected=(len(rows)-1)%snapshot_step==0 and len(snapshots)<11
            if selected or best is None or row['ranking_score']>best[0]['ranking_score']:
                thumb=assets['overlay'];h,w=thumb.shape[:2]
                thumb=cv2.resize(thumb,(min(w,640),max(1,round(h*min(w,640)/w))))
                snapshot=dict(row,file=f'review-{len(rows):05d}.jpg')
                if selected:
                    if not cv2.imwrite(str(output/snapshot['file']),thumb):raise ValueError('review image could not be written')
                    snapshots.append(snapshot)
                if best is None or row['ranking_score']>best[0]['ranking_score']:best=(snapshot,thumb.copy())
    finally:cap.release()
    if not rows:raise ValueError('no decodable frames')
    events=gate.finish()
    # Interval end extends by one sampling period; raw gate time is the last positive sample.
    for e in events:e['end']=min(rows[-1]['time_s']+1/fps,e['end']+1/sample_hz)
    sha=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):sha.update(chunk)
    if best[0]['file'] not in {s['file'] for s in snapshots}:
        if not cv2.imwrite(str(output/best[0]['file']),best[1]):raise ValueError('review image could not be written')
        snapshots.append(best[0])
    snapshots.sort(key=lambda s:s['time_s'])
    from dataclasses import asdict
    reasons={key:sum(r['reason']==key for r in rows) for key in ('no_color_region','area_below_threshold','edge_below_threshold','model_below_threshold','motion_below_threshold','scene_motion','awaiting_temporal_confirmation','candidate')}
    diagnostics=dict(candidate_frames=reasons['candidate'],longest_candidate_run=longest_run,
        min_area_ratio=min(r['area_ratio'] for r in rows),max_area_ratio=max(r['area_ratio'] for r in rows),
        max_edge_ratio=max(r['best_edge_ratio'] for r in rows),reason_counts=reasons)
    if model is not None:diagnostics.update(max_model_confidence=max(r['model_confidence'] for r in rows),disagreement_frames=sum(r['candidate']!=r['rule_candidate'] for r in rows))
    report=dict(version=3 if model is not None else 2,decision_engine='model' if model is not None else 'rules',model=model_metadata,source=source_name or path.name,source_sha256=sha.hexdigest(),fps=fps,sample_hz=sample_hz,
        on_frames=on_frames,off_frames=off_frames,sampled_frames=len(rows),events=events,
        config=asdict(cfg),diagnostics=diagnostics,review_frames=snapshots,
        duration_analyzed_s=rows[-1]['time_s']+1/fps,truncated=limited,
        scope='offline candidate review, constant-frame-rate input; model and rule scores are distinct; no real-time or fire accuracy claim',
        detector_sha256=hashlib.sha256((Path(__file__).parents[1]/'app/detector.py').read_bytes()).hexdigest(),
        temporal_sha256=hashlib.sha256((Path(__file__).parents[1]/'app/temporal.py').read_bytes()).hexdigest())
    if native:
        from app.native_detector import library
        report.update(version=4,rule_engine='cpp-region-motion-v1',native_sha256=library()[1],native_adapter_sha256=hashlib.sha256((Path(__file__).parents[1]/'app/native_detector.py').read_bytes()).hexdigest(),confirmation_window=2*on_frames-1,motion_threshold=.02,scene_motion_limit=.65)
    report['analysis_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if truth is not None:report['event_evaluation']=event_metrics(events,truth)
    with (output/'timeline.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (output/'video-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    if native:
        from scripts.native_review import render_review as renderer
    else:renderer=render_review
    (output/'review.html').write_text(renderer(report,rows),encoding='utf-8')
    if progress:progress(1.0)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--sample-hz',type=float,default=5);p.add_argument('--truth',type=Path)
    p.add_argument('--engine',choices=['cpp','legacy'],default='cpp');p.add_argument('--model-config',type=Path);p.add_argument('--confidence',type=float,default=.25)
    p.add_argument('--edge-ratio',type=float,default=.6);p.add_argument('--brightness',type=int,default=150)
    a=p.parse_args();truth=json.loads(a.truth.read_text()) if a.truth else None
    from app.model import ONNXDetector
    model=ONNXDetector(a.model_config) if a.model_config else None
    print(json.dumps(video_report(a.video,a.out,sample_hz=a.sample_hz,truth=truth,model=model,confidence=a.confidence,config=Config(edge_ratio=a.edge_ratio,brightness=a.brightness),native=a.engine=='cpp' and model is None),ensure_ascii=False,indent=2))
