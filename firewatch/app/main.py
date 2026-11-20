from pathlib import Path
import zipfile
import io, json, os, shutil, sqlite3, uuid, warnings, hashlib, platform
from datetime import datetime, timezone
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from .detector import analyze, Config

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('FIREWATCH_DATA', ROOT.parent / 'data')).resolve()
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / 'history.sqlite3'
with sqlite3.connect(DB) as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created TEXT, filename TEXT, result TEXT)')
app = FastAPI(title='视觉火焰检测与事件分析', version='1.0.0')
app.mount('/static', StaticFiles(directory=ROOT/'static'), name='static')
@app.middleware('http')
async def refresh_interface(request, call_next):
    response = await call_next(request)
    content_type = response.headers.get('content-type', '')
    if content_type.startswith('text/html'):
        response.headers['Cache-Control'] = 'no-store'
    elif request.url.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-cache'
    return response

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 12_000_000

from .image_io import decode

def fetch(run_id):
    with sqlite3.connect(DB) as conn:
        row = conn.execute('SELECT result FROM runs WHERE id=?', (run_id,)).fetchone()
    if row is None: raise HTTPException(404, '记录不存在')
    return json.loads(row[0])

def persist(raw, filename, cfg, native=False):
    img = decode(raw)
    if native:
        from .native_detector import analyze as cpp_analyze
        result,assets=cpp_analyze(img,cfg)
    else:result, assets = analyze(img, cfg)
    run_id = uuid.uuid4().hex
    folder = DATA/run_id
    folder.mkdir()
    try:
        output_hashes = {}
        for name, image in assets.items():
            ok, encoded = cv2.imencode('.png', image)
            if not ok: raise RuntimeError('图片编码失败')
            payload = encoded.tobytes()
            (folder/f'{name}.png').write_bytes(payload)
            output_hashes[name + '.png'] = hashlib.sha256(payload).hexdigest()
        source_hash = hashlib.sha256(raw).hexdigest()
        code_hash = hashlib.sha256(((ROOT.parent/'native/fire_core.cpp') if native else (ROOT/'detector.py')).read_bytes()).hexdigest()
        signature = {'source_sha256': source_hash, 'detector_sha256': code_hash,
                     'algorithm': result['algorithm'], 'config': result['config'],
                     'opencv': cv2.__version__, 'numpy': np.__version__}
        fingerprint = hashlib.sha256(json.dumps(signature, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        result['provenance'] = dict(signature, fingerprint=fingerprint, source_bytes=len(raw),
                                    python=platform.python_version(), output_sha256=output_hashes)
        result.update(id=run_id, filename=filename.replace('\\','/').split('/')[-1][:180],
                      created=datetime.now(timezone.utc).isoformat(),
                      assets={name: f'/api/runs/{run_id}/images/{name}' for name in assets})
        (folder/'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        with sqlite3.connect(DB) as conn:
            conn.execute('INSERT INTO runs VALUES (?,?,?,?)', (run_id,result['created'],result['filename'],json.dumps(result,ensure_ascii=False)))
        return result
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise

@app.get('/')
def home(): return FileResponse(ROOT/'static/index.html')
@app.get('/api/health')
def health(): return {'status':'ok','algorithm':'color-edge-v2'}
@app.post('/api/analyze')
async def detect(file: UploadFile = File(...), brightness: int = Form(150, ge=0, le=255),
                 edge_ratio: float = Form(0.6, ge=0, le=1), min_area_ratio: float = Form(0.002, ge=0, le=1),
                 min_component: int = Form(40, ge=1, le=100000)):
    try:
        raw = await file.read(MAX_BYTES+1)
        if len(raw) > MAX_BYTES: raise HTTPException(413, '文件不能超过 10 MB')
        try: return await run_in_threadpool(persist, raw, file.filename or 'image', Config(brightness,edge_ratio,min_area_ratio,min_component))
        except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    finally: await file.close()
@app.get('/api/runs')
def history(limit: int = Query(20, ge=1, le=100)):
    with sqlite3.connect(DB) as conn:
        rows=conn.execute('SELECT result FROM runs ORDER BY created DESC LIMIT ?', (limit,)).fetchall()
    return [json.loads(r[0]) for r in rows]
@app.get('/api/runs/{run_id}')
def get_run(run_id: str): return fetch(run_id)
@app.get('/api/runs/{run_id}/report')
def report(run_id: str):
    return Response(json.dumps(fetch(run_id),ensure_ascii=False,indent=2),media_type='application/json',
                    headers={'Content-Disposition':f'attachment; filename="firewatch-{run_id}.json"'})
@app.get('/api/runs/{run_id}/images/{name}')
def image(run_id: str, name: str):
    result=fetch(run_id)
    if name not in result['assets']: raise HTTPException(404,'图片不存在')
    return FileResponse(DATA/run_id/f'{name}.png')

# Local single-user video workbench. Queue and artefacts survive normal page reloads.
from .video_jobs import VideoJobs
VIDEO=VideoJobs(DATA/'videos')
MAX_VIDEO_BYTES=50*1024*1024
@app.get('/video')
def video_page():return FileResponse(ROOT/'static/video.html')
@app.post('/api/videos',status_code=202)
async def upload_video(file:UploadFile=File(...),edge_ratio:float=Form(.6,ge=0,le=1),brightness:int=Form(150,ge=0,le=255),retain_source:bool=Form(False),decision_engine:str=Form("rules"),confidence:float=Form(.25,ge=0,le=1),sample_hz:int=Form(5,ge=1,le=30),on_frames:int=Form(3,ge=1,le=30),off_frames:int=Form(2,ge=1,le=30)):
    filename=(file.filename or 'video').replace('\\','/').split('/')[-1][:180]
    if Path(filename).suffix.lower() not in ('.mp4','.avi','.mov','.webm'):
        await file.close();raise HTTPException(400,'支持 MP4、AVI、MOV、WebM 常帧率视频')
    if decision_engine not in ('rules','cpp','model'):
        await file.close();raise HTTPException(400,'分析引擎须为 rules 或 model')
    model_sha=None
    if decision_engine=='model':
        try:model_sha=(await run_in_threadpool(configured_model)).sha256
        except (ValueError,OSError,cv2.error):
            await file.close();raise HTTPException(409,'未配置可用 ONNX 模型，请先完成模型配置；不会回退成规则分析。')
    try:job=VIDEO.create(filename,Config(edge_ratio=edge_ratio,brightness=brightness),retain_source=retain_source,decision_engine=decision_engine,confidence=confidence,sample_hz=sample_hz,on_frames=on_frames,off_frames=off_frames,model_sha256=model_sha)
    except ValueError:
        await file.close();raise HTTPException(429,'任务已满，请等待或取消现有任务')
    size=0
    try:
        with (VIDEO.root/job/'source.video').open('wb') as target:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>MAX_VIDEO_BYTES:raise HTTPException(413,'视频不能超过50 MB')
                target.write(chunk)
        if not size:raise HTTPException(400,'视频为空')
        VIDEO.submit(job);return VIDEO.get(job)
    except Exception:
        VIDEO.update(job,status='failed',error='Upload failed')
        (VIDEO.root/job/'source.video').unlink(missing_ok=True)
        raise
    finally:await file.close()
@app.get('/api/videos')
def video_list():return [VIDEO.describe(row) for row in VIDEO.list()]
@app.get('/api/videos/{job}')
def video_status(job:str):
    row=VIDEO.get(job)
    if not row:raise HTTPException(404,'任务不存在')
    return row
@app.post('/api/videos/{job}/cancel')
def cancel_video(job:str):
    row=VIDEO.cancel(job)
    if not row:raise HTTPException(404,'任务不存在')
    return row
@app.get('/api/videos/{job}/files/{name}')
def video_asset(job:str,name:str):
    row=VIDEO.get(job)
    if not row:raise HTTPException(404,'任务不存在')
    if row['status']!='completed':raise HTTPException(409,'任务尚未完成')
    allowed={'review.html','video-report.json','timeline.csv'}
    import re
    if name not in allowed and not re.fullmatch(r'review-[0-9]{5,}\.jpg',name):raise HTTPException(404,'文件不存在')
    path=VIDEO.root/job/'analysis'/name
    if not path.is_file():raise HTTPException(404,'文件不存在')
    return FileResponse(path)

# Human annotations and experiments never overwrite the original prediction report.
from .review import ReviewStore,ReviewInput,CompareInput,evaluate,compare
REVIEWS=ReviewStore(VIDEO.root)
def completed_report(job):
 row=VIDEO.get(job)
 if not row:raise HTTPException(404,'任务不存在')
 if row['status']!='completed':raise HTTPException(409,'任务尚未完成')
 return json.loads((VIDEO.root/job/'analysis/video-report.json').read_text())
@app.get('/review/{job}')
def review_page(job:str):
 completed_report(job);return FileResponse(ROOT/'static/review-workspace.html')
@app.get('/api/videos/{job}/review')
def get_review(job:str):
 report=completed_report(job);review=REVIEWS.get(job)
 return dict(report=report,review=review,evaluation=evaluate(report,review),history=REVIEWS.history(job),source_available=(VIDEO.root/job/'source.video').is_file())
@app.put('/api/videos/{job}/review')
def save_review(job:str,value:ReviewInput):
 report=completed_report(job);review=REVIEWS.save(job,value,report)
 return dict(review=review,evaluation=evaluate(report,review))
@app.post('/api/videos/{job}/compare')
def compare_thresholds(job:str,value:CompareInput):
 completed_report(job);return compare(VIDEO.root/job/'analysis',value,REVIEWS.get(job))
@app.get('/api/videos/{job}/review-export')
def review_export(job:str):
 data=get_review(job);return Response(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),media_type='application/json',headers={'Content-Disposition':'attachment; filename="firewatch-review.json"'})
@app.get('/api/videos/{job}/source')
def retained_source(job:str):
 completed_report(job);path=VIDEO.root/job/'source.video'
 if not path.is_file():raise HTTPException(404,'本次上传未保留原视频；下次可勾选本机保留。')
 filename=VIDEO.get(job)['filename'];types={'.mp4':'video/mp4','.mov':'video/quicktime','.webm':'video/webm','.avi':'video/x-msvideo'}
 return FileResponse(path,media_type=types.get(Path(filename).suffix.lower(),'application/octet-stream'))

from .model import configured_model
@app.get('/api/model/status')
def model_status():
 try:
  m=configured_model();return dict(configured=True,model_sha256=m.sha256,class_names=m.contract['class_names'],target_classes=m.contract['target_classes'],output_layout=m.contract['output_layout'])
 except (ValueError,OSError,cv2.error):return dict(configured=False,message='未配置可用模型；请按 models/README.md 设置模型、类别和SHA256。')
@app.get('/model')
def model_page():return FileResponse(ROOT/'static/model.html')
@app.post('/api/model/analyze')
async def model_analyze(file:UploadFile=File(...),confidence:float=Form(.25,ge=0,le=1),iou:float=Form(.45,ge=0,le=1)):
 try:
  raw=await file.read(MAX_BYTES+1)
  if len(raw)>MAX_BYTES:raise HTTPException(413,'文件不能超过10MB')
  try:img=decode(raw)
  except ValueError as e:raise HTTPException(400,'无效图像') from e
  try:model=configured_model()
  except (ValueError,OSError,cv2.error) as e:raise HTTPException(409,'模型尚未配置或不能加载，请检查本机模型配置。') from e
  try:result,overlay=await run_in_threadpool(model.analyze,img,confidence,iou)
  except (ValueError,cv2.error) as e:raise HTTPException(422,'模型输出或算子不符合已声明的推理协议，请检查导出设置。') from e
  import base64
  ok,encoded=cv2.imencode('.jpg',overlay)
  if not ok:raise HTTPException(500,'结果图编码失败')
  result['source_sha256']=hashlib.sha256(raw).hexdigest();baseline,_=await run_in_threadpool(analyze,img,Config())
  return dict(model=result,baseline=dict(detected=baseline['detected'],area_ratio=baseline['area_ratio'],methods=baseline['methods']),overlay='data:image/jpeg;base64,'+base64.b64encode(encoded).decode())
 finally:await file.close()

@app.delete('/api/videos/{job}')
def delete_video(job:str):
    try:deleted=VIDEO.delete(job)
    except ValueError:raise HTTPException(409,'任务仍在处理或收尾，请先取消并稍后重试。')
    except OSError:raise HTTPException(500,'清理文件失败，请检查本机目录权限后重试。')
    if not deleted:raise HTTPException(404,'任务不存在')
    with REVIEWS.connect() as c:
        c.execute('DELETE FROM reviews WHERE job=?',(job,))
        c.execute('DELETE FROM revisions WHERE job=?',(job,))
    return {'deleted':True}

# Bounded evaluation runs share the same model adapter as interactive inference.
import threading as _threading
_eval_gate = _threading.BoundedSemaphore(1)
@app.get('/evaluation')
def evaluation_page():return FileResponse(ROOT/'static/evaluation.html')
@app.get('/api/evaluation/template')
def evaluation_template():
    return Response(json.dumps({'version':1,'target_class':0,'images':[{'id':'val-1','file':'validation.png','group':'source-A','split':'validation','boxes':[[10,10,30,30]]},{'id':'test-1','file':'test.png','group':'source-B','split':'test','boxes':[[10,10,30,30]]}]},ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename="manifest.json"'})
def _evaluate_and_save(raw):
    from .evaluation import evaluate_archive
    from .model import configured_model
    result=evaluate_archive(raw,configured_model(),decode);run_id=uuid.uuid4().hex
    folder=DATA/'evaluations';folder.mkdir(exist_ok=True)
    result.update(id=run_id,created=datetime.now(timezone.utc).isoformat())
    (folder/(run_id+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    return result
@app.post('/api/evaluations')
async def evaluate_dataset(file:UploadFile=File(...)):
    acquired=False
    try:
        raw=await file.read(20*1024*1024+1)
        if len(raw)>20*1024*1024:raise HTTPException(413,'ZIP 不能超过 20 MB')
        acquired=_eval_gate.acquire(blocking=False)
        if not acquired:raise HTTPException(429,'已有评测正在运行，请稍后再试')
        try:return await run_in_threadpool(_evaluate_and_save,raw)
        except (ValueError,zipfile.BadZipFile,KeyError,RuntimeError,cv2.error) as exc:raise HTTPException(400,str(exc)) from exc
    finally:
        if acquired:_eval_gate.release()
        await file.close()
@app.get('/api/evaluations/{run_id}')
def evaluation_report(run_id:str):
    import re
    if not re.fullmatch('[0-9a-f]{32}',run_id):raise HTTPException(404,'评测记录不存在')
    path=DATA/'evaluations'/(run_id+'.json')
    if not path.is_file():raise HTTPException(404,'评测记录不存在')
    return FileResponse(path,media_type='application/json',filename='detection-evaluation-'+run_id+'.json')

@app.post('/api/native/analyze')
async def native_detect(file:UploadFile=File(...),brightness:int=Form(150,ge=0,le=255),min_area_ratio:float=Form(.002,ge=0,le=1),min_component:int=Form(40,ge=1,le=100000)):
    try:
        raw=await file.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise HTTPException(413,'文件不能超过 10 MB')
        try:return await run_in_threadpool(persist,raw,file.filename or 'image',Config(brightness=brightness,min_area_ratio=min_area_ratio,min_component=min_component),True)
        except (ValueError,RuntimeError) as exc:raise HTTPException(400,str(exc)) from exc
    finally:await file.close()
