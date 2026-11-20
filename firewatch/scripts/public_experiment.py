from pathlib import Path
import sys,json,hashlib,time,xml.etree.ElementTree as ET
import numpy as np,cv2,onnxruntime as ort
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.detector import analyze,Config
from app.benchmark import evaluate
from app.evaluation import metrics
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(root,model):
 root=Path(root);out=root.parent/'public-probe';out.mkdir(exist_ok=True);options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
 session=ort.InferenceSession(str(model),options,providers=['CPUExecutionProvider']);videos=[];boxes=[]
 for name,split,scene in [('Car1','validation','vehicle-fire'),('non_fire_patrolbot_onboard','validation','patrol-negative'),('house6','test','house-fire'),('cleaner','test','cleaner-negative')]:
  path=root/(name+'.mp4');xml=root/(name+'.xml');tree=ET.parse(xml).getroot();labels={int(f.findtext('frameNumber')):[list(map(int,b.text.split())) for b in f.find('annotations')] for f in tree.find('frames')}
  cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS);total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));duration=min(total/fps,120);timeline=[];truth=[];start=None
  for i in range(min(total,int(duration*fps))):
   positive=bool(labels.get(i,[]))
   if positive and start is None:start=i/fps
   if not positive and start is not None:truth.append(dict(start=start,end=i/fps));start=None
  if start is not None:truth.append(dict(start=start,end=duration))
  for t in np.arange(0,duration,1.):
   frame_id=min(total-1,round(t*fps));cap.set(cv2.CAP_PROP_POS_FRAMES,frame_id);ok,img=cap.read()
   if not ok:raise ValueError('Decode failed')
   rule,_=analyze(img,Config());rgb=Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB)).resize((224,224),Image.Resampling.BILINEAR);x=(np.asarray(rgb,dtype=np.float32)/255-.5)/.5
   began=time.perf_counter();logits=session.run(None,{'pixel_values':x.transpose(2,0,1)[None]})[0][0];elapsed=time.perf_counter()-began;prob=np.exp(logits-logits.max());prob/=prob.sum()
   score=max(m['edge_color_ratio'] for m in rule['methods']) if rule['boxes'] and rule['area_ratio']>=Config().min_area_ratio else 0
   timeline.append(dict(time=float(t),rule=score,model=float(prob[0]),model_seconds=elapsed))
   if split=='test':boxes.append(dict(id=f'{name}:{frame_id}',truth=[dict(zip(['x','y','width','height'],b)) for b in labels.get(frame_id,[])],predictions=[dict(b,confidence=score) for b in rule['boxes']]))
  cap.release();videos.append(dict(id=name,source_group=name,split=split,scene=scene,duration=duration,source_sha256=sha(path),annotation_author='FURG authors',annotation_file_sha256=sha(xml),truth=truth,timeline=timeline));print(name,len(timeline),flush=True)
 spec=dict(mode='real',videos=videos,model_sha256=sha(Path(model)));report=evaluate(spec)
 report.update(source='https://github.com/steffensbola/furg-fire-dataset',license='CC0 1.0',model=dict(source='https://huggingface.co/prithivMLmods/Fire-Detection-Engine-ONNX',revision='02bd7f981aac3e27a75f83e0a3b97dfadaffc228',sha256=spec['model_sha256'],task='image-classification',class_names=['fire','normal','smoke'],license='apache-2.0',training_overlap='unknown'))
 report['rule_box_iou_sensitivity']={str(i):{('ap_at_iou' if k=='ap50' else k):v for k,v in metrics(boxes,report['methods']['rule']['selected']['threshold'],i).items()} for i in [.25,.5,.75]};report['limitations']=['4 videos only, source-disjoint validation/test, model training overlap unknown','1fps, first at most120s; no confidence intervals','Classifier has no boxes; box IoU only applies to rule baseline','No established sunset/reflection/light/orange-object negative coverage','Event delay excludes decode/inference latency']
 for name,obj in [('manifest',spec),('report',report)]: (out/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False))
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
