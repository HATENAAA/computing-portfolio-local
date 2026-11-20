"""Optional local ONNX detector. Explicit output contract; no automatic model download."""
from pathlib import Path
import os,json,hashlib,time,threading
import cv2,numpy as np

def letterbox(image,size):
 h,w=image.shape[:2];ratio=min(size/w,size/h);nw=max(1,round(w*ratio));nh=max(1,round(h*ratio));left=(size-nw)//2;top=(size-nh)//2
 canvas=np.full((size,size,3),114,np.uint8);canvas[top:top+nh,left:left+nw]=cv2.resize(image,(nw,nh))
 return canvas,dict(scale_x=nw/w,scale_y=nh/h,left=left,top=top,width=w,height=h)

def decode_output(output,contract,transform,confidence=.25,iou=.45):
 a=np.asarray(output)
 if a.ndim!=3 or a.shape[0]!=1 or not np.isfinite(a).all():raise ValueError('模型输出须为单批次、有限数值的三维张量')
 count=len(contract['class_names']);layout=contract['output_layout']
 if layout=='xyxy6':
  if a.shape[2]!=6:raise ValueError('xyxy6 输出形状须为 [1,N,6]')
  rows=a[0];classes=rows[:,5]
  if not np.all(classes==np.floor(classes)):raise ValueError('类别索引必须为整数')
  boxes=rows[:,:4];scores=rows[:,4];classes=classes.astype(int)
  if np.any(classes<0) or np.any(classes>=count):raise ValueError('输出类别超出类别表范围')
 elif layout=='yolov8-raw':
  if a.shape[1]!=4+count:raise ValueError('yolov8-raw 输出形状须为 [1,4+C,N]')
  rows=a[0].T
  if np.any(rows[:,4:]<0) or np.any(rows[:,4:]>1):raise ValueError('类别分数须在0至1内')
  classes=rows[:,4:].argmax(axis=1);scores=rows[np.arange(len(rows)),4+classes];boxes=rows[:,:4].copy();boxes[:,:2]-=boxes[:,2:]/2;boxes[:,2:]+=boxes[:,:2]
 else:raise ValueError('不支持的输出布局')
 if len(boxes)>30000 or np.any(scores<0) or np.any(scores>1):raise ValueError('输出数量过大，或置信度不在0至1内')
 candidates=[]
 for box,score,cls in zip(boxes,scores,classes):
  if score<confidence or int(cls) not in contract['target_classes']:continue
  x1,y1,x2,y2=map(float,box);x1=max(0,min(transform['width'],(x1-transform['left'])/transform['scale_x']));x2=max(0,min(transform['width'],(x2-transform['left'])/transform['scale_x']));y1=max(0,min(transform['height'],(y1-transform['top'])/transform['scale_y']));y2=max(0,min(transform['height'],(y2-transform['top'])/transform['scale_y']))
  if x2<=x1 or y2<=y1:continue
  candidates.append(dict(x=x1,y=y1,width=x2-x1,height=y2-y1,confidence=float(score),class_id=int(cls),label=contract['class_names'][int(cls)]))
 kept=[]
 for cls in sorted(set(r['class_id'] for r in candidates)):
  group=[r for r in candidates if r['class_id']==cls]
  indices=cv2.dnn.NMSBoxes([[r['x'],r['y'],r['width'],r['height']] for r in group],[r['confidence'] for r in group],confidence,iou)
  kept.extend(group[int(i)] for i in np.asarray(indices).reshape(-1))
 return sorted(kept,key=lambda r:-r['confidence'])[:300]

class ONNXDetector:
 def __init__(self,config):
  path=Path(config).resolve();v=json.loads(path.read_text())
  if not isinstance(v,dict):raise ValueError('模型配置须为JSON对象')
  required={'model','sha256','input_size','class_names','target_classes','output_layout'}
  if not required<=v.keys():raise ValueError('模型配置缺少必填字段')
  import re
  if not isinstance(v['model'],str) or not isinstance(v['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',v['sha256']):raise ValueError('模型路径或SHA256格式无效')
  if type(v['input_size']) is not int or not 128<=v['input_size']<=1280 or v['input_size']%32:raise ValueError('输入边长须为128至1280间的32倍数')
  if not isinstance(v['class_names'],list) or not 1<=len(v['class_names'])<=100 or any(not isinstance(s,str) or not 1<=len(s)<=60 for s in v['class_names']):raise ValueError('类别表无效')
  if not isinstance(v['target_classes'],list) or not v['target_classes'] or any(type(i) is not int or not 0<=i<len(v['class_names']) for i in v['target_classes']):raise ValueError('目标类别索引无效')
  if v['output_layout'] not in ('xyxy6','yolov8-raw'):raise ValueError('需显式指定支持的输出布局')
  model=(path.parent/v['model']).resolve()
  if model.suffix.lower()!='.onnx' or not model.is_file() or model.stat().st_size>200*1024*1024:raise ValueError('需要本机200MB以内的ONNX文件')
  digest=hashlib.sha256(model.read_bytes()).hexdigest()
  if digest!=v['sha256']:raise ValueError('模型SHA256与配置不一致')
  self.contract=v;self.sha256=digest;self.net=cv2.dnn.readNetFromONNX(str(model));self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV);self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU);self.lock=threading.Lock()
 def analyze(self,image,confidence=.25,iou=.45):
  start=time.perf_counter();canvas,transform=letterbox(image,self.contract['input_size'])
  blob=cv2.dnn.blobFromImage(canvas,1/255,swapRB=True,crop=False)
  with self.lock:self.net.setInput(blob);output=self.net.forward().copy()
  boxes=decode_output(output,self.contract,transform,confidence,iou);overlay=image.copy()
  for r in boxes:
   x,y,w,h=map(round,(r['x'],r['y'],r['width'],r['height']));cv2.rectangle(overlay,(x,y),(x+w,y+h),(40,190,250),2);cv2.putText(overlay,f"{r['label']} {r['confidence']:.2f}",(x,max(18,y-6)),cv2.FONT_HERSHEY_SIMPLEX,.6,(40,190,250),2)
  return dict(engine='onnx-opencv-cpu',model_sha256=self.sha256,adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),runtime=dict(opencv=cv2.__version__,numpy=np.__version__),input_size=self.contract['input_size'],output_layout=self.contract['output_layout'],class_names=self.contract['class_names'],target_classes=self.contract['target_classes'],boxes=boxes,detected=bool(boxes),elapsed_ms=round((time.perf_counter()-start)*1000,2),confidence_threshold=confidence,nms_iou=iou,scope='Model prediction; requires manual review and independent validation.'),overlay

_cached=None;_lock=threading.Lock()
def configured_model():
 global _cached
 with _lock:
  if _cached is not None:return _cached
  path=os.environ.get('FIREWATCH_MODEL_CONFIG',str(Path(__file__).resolve().parent.parent/'models/config.json'))
  if not path or not Path(path).is_file():raise ValueError('尚未配置火焰ONNX模型。请按 models/README.md 提供权重、类别表和SHA256。')
  _cached=ONNXDetector(path);return _cached
