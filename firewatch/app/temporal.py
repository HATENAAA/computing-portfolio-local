"""Offline candidate events with explicit confirmation/release hysteresis."""
from dataclasses import dataclass
import math
@dataclass
class EventGate:
    on_frames: int = 3
    off_frames: int = 2
    def __post_init__(self):
        if type(self.on_frames) is not int or type(self.off_frames) is not int or min(self.on_frames,self.off_frames)<1:
            raise ValueError('positive integer frame thresholds required')
        self.events=[];self.run=0;self.misses=0;self.active=None;self.first=None;self.last=None;self.last_positive=None
    def update(self, timestamp, candidate):
        if not math.isfinite(timestamp) or timestamp<0 or (self.last is not None and timestamp<=self.last):
            raise ValueError('timestamps must be finite and strictly increasing')
        if type(candidate) is not bool:raise ValueError('candidate must be boolean')
        self.last=timestamp
        if candidate:
            if self.run==0:self.first=timestamp
            self.run+=1;self.misses=0;self.last_positive=timestamp
            if self.active is None and self.run>=self.on_frames:
                self.active=dict(start=self.first,confirmed_at=timestamp)
        else:
            self.run=0;self.misses+=1
            if self.active is not None and self.misses>=self.off_frames:self._close()
    def _close(self):
        self.events.append(dict(self.active,end=self.last_positive));self.active=None
    def finish(self):
        if self.active is not None:self._close()
        return list(self.events)

def event_metrics(predictions, truth, iou_threshold=.5):
    if not 0<iou_threshold<=1:raise ValueError('invalid IoU threshold')
    for row in [*predictions,*truth]:
        if not all(math.isfinite(row[k]) for k in ('start','end')) or row['start']<0 or row['end']<=row['start']:
            raise ValueError('positive-duration intervals required')
    # Maximum-cardinality one-to-one matching over eligible temporal IoU edges.
    edges=[];ious=[]
    for p in predictions:
        eligible=[];scores=[]
        for j,t in enumerate(truth):
            overlap=max(0,min(p['end'],t['end'])-max(p['start'],t['start']))
            union=p['end']-p['start']+t['end']-t['start']-overlap
            scores.append(overlap/union)
            if overlap/union>=iou_threshold:eligible.append(j)
        edges.append(eligible)
        ious.append(scores)
    assigned={}
    def match(i,seen):
        for j in edges[i]:
            if j in seen:continue
            seen.add(j)
            if j not in assigned or match(assigned[j],seen):assigned[j]=i;return True
        return False
    for i in range(len(predictions)):match(i,set())
    tp=len(assigned);fp=len(predictions)-tp;fn=len(truth)-tp
    latencies=[max(0,predictions[i].get('confirmed_at',predictions[i]['start'])-truth[j]['start']) for j,i in assigned.items()]
    used=set(assigned.values())
    errors=[]
    for i in range(len(predictions)):
        if i in used:continue
        best=max(ious[i],default=0)
        category='duplicate' if edges[i] else ('temporal_localisation' if best>0 else 'background')
        errors.append(dict(prediction_index=i,category=category,best_temporal_iou=best))
    return dict(tp=tp,fp=fp,fn=fn,precision=tp/(tp+fp) if tp+fp else None,
        recall=tp/(tp+fn) if tp+fn else None,
        confirmation_delay_seconds=latencies,iou_threshold=iou_threshold,
        matched_pairs=[dict(prediction_index=i,truth_index=j,temporal_iou=ious[i][j]) for j,i in sorted(assigned.items())],
        false_positives=errors,missed_truth_indices=[j for j in range(len(truth)) if j not in assigned],
        error_counts={kind:sum(e['category']==kind for e in errors) for kind in ('duplicate','temporal_localisation','background')},
        matching='maximum cardinality, one to one')

class RollingEventGate:
    """Confirm N positive samples within 2N-1 samples; tolerate brief flame flicker."""
    def __init__(self,on_frames=3,off_frames=2):
        from collections import deque
        self.gate=EventGate(1,off_frames);self.required=on_frames
        if type(on_frames) is not int or not 1<=on_frames<=30:raise ValueError('Invalid vote count')
        self.window=deque(maxlen=2*on_frames-1);self.last_candidate=False
    def update(self,timestamp,candidate):
        # Validate before mutating the vote window, so a rejected frame cannot affect later events.
        if (not math.isfinite(timestamp) or timestamp<0 or
            self.gate.last is not None and timestamp<=self.gate.last):
            raise ValueError('timestamps must be finite and strictly increasing')
        if type(candidate) is not bool:raise ValueError('candidate must be boolean')
        self.window.append((timestamp,candidate));self.last_candidate=sum(int(v) for _,v in self.window)>=self.required
        was_active=self.gate.active is not None;self.gate.update(timestamp,self.last_candidate)
        if not was_active and self.gate.active is not None:self.gate.active['start']=next(t for t,v in self.window if v)
    def finish(self):return self.gate.finish()
