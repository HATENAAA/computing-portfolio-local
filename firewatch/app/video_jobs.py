"""Bounded local video jobs with persisted status, cooperative cancellation and review files."""
import json,sqlite3,threading,uuid,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from scripts.analyze_video import video_report
from .detector import Config
from dataclasses import asdict

class VideoJobs:
    def __init__(self,root,runner=video_report):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.db=self.root/'jobs.sqlite3';self.lock=threading.RLock();self.executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='fire-video');self.runner=runner;self.futures={}
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,status TEXT,progress REAL,filename TEXT,error TEXT,cancel INTEGER DEFAULT 0)')
            c.execute("UPDATE jobs SET status='failed',error='Service restarted; please upload again' WHERE status IN ('uploading','queued','running')")
    def connect(self):return sqlite3.connect(self.db,timeout=10)
    def create(self,filename,config=None,retain_source=False,decision_engine="rules",confidence=.25,sample_hz=5,on_frames=3,off_frames=2,model_sha256=None):
        settings=asdict(config or Config())
        with self.lock,self.connect() as c:
            count=c.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('uploading','queued','running')").fetchone()[0]
            if count>=3:raise ValueError('queue full')
            job=uuid.uuid4().hex
            c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,0)',(job,'uploading',0,filename,'',))
            (self.root/job).mkdir()
            (self.root/job/'settings.json').write_text(json.dumps(settings))
            (self.root/job/'options.json').write_text(json.dumps(dict(retain_source=bool(retain_source),decision_engine=decision_engine,confidence=confidence,sample_hz=sample_hz,on_frames=on_frames,off_frames=off_frames,model_sha256=model_sha256)))
            return job
    def update(self,job,**values):
        allowed={'status','progress','error','cancel'}
        if not values or not set(values)<=allowed:raise ValueError('invalid job fields')
        with self.lock,self.connect() as c:c.execute('UPDATE jobs SET '+','.join(k+'=?' for k in values)+' WHERE id=?',(*values.values(),job))
    def get(self,job):
        with self.connect() as c:
            c.row_factory=sqlite3.Row;row=c.execute('SELECT * FROM jobs WHERE id=?',(job,)).fetchone()
        return dict(row) if row else None
    def list(self):
        with self.connect() as c:
            c.row_factory=sqlite3.Row;return [dict(r) for r in c.execute('SELECT * FROM jobs ORDER BY rowid DESC LIMIT 30')]
    def cancelled(self,job):return bool(self.get(job)['cancel'])
    def cancel(self,job):
        with self.lock:
            row=self.get(job)
            if row and row['status'] in ('uploading','queued','running'):
                self.update(job,cancel=1)
                if row['status']!='running':self.update(job,status='cancelled')
        return self.get(job)
    def submit(self,job):
        with self.lock:
            if self.cancelled(job):
                (self.root/job/'source.video').unlink(missing_ok=True);return
            self.update(job,status='queued');self.futures[job]=self.executor.submit(self.run,job)
    def run(self,job):
        folder=self.root/job;options={}
        try:
            with self.lock:
                if self.cancelled(job):return
                self.update(job,status='running')
            settings=folder/'settings.json'
            cfg=Config(**json.loads(settings.read_text())) if settings.exists() else Config()
            options=json.loads((folder/'options.json').read_text())
            model=None
            if options.get('decision_engine')=='model':
                from .model import configured_model
                model=configured_model()
                if model.sha256!=options.get('model_sha256'):raise ValueError('model changed after upload')
            self.runner(folder/'source.video',folder/'analysis',progress=lambda v:self.update(job,progress=v),cancelled=lambda:self.cancelled(job),config=cfg,source_name=self.get(job)['filename'],model=model,**({'native':True} if options.get('decision_engine')=='cpp' else {}),confidence=options.get('confidence',.25),sample_hz=options.get('sample_hz',5),on_frames=options.get('on_frames',3),off_frames=options.get('off_frames',2))
            with self.lock:
                if self.cancelled(job):raise InterruptedError()
                self.update(job,status='completed',progress=1)
        except InterruptedError:
            shutil.rmtree(folder/'analysis',ignore_errors=True);self.update(job,status='cancelled')
        except Exception:
            shutil.rmtree(folder/'analysis',ignore_errors=True)
            self.update(job,status='failed',error='模型推理或视频解码失败，请检查模型协议和视频编码。' if options.get('decision_engine')=='model' else 'C++ 内核未就绪或视频分析失败。请先运行 native/build.py，并检查视频编码。' if options.get('decision_engine')=='cpp' else '视频解码或分析失败，请使用受支持的常帧率视频。')
        finally:
            options=json.loads((folder/'options.json').read_text()) if (folder/'options.json').exists() else {}
            if self.get(job)['status']!='completed' or not options.get('retain_source'):(folder/'source.video').unlink(missing_ok=True)
    def describe(self,row):
        folder=self.root/row['id'];result=dict(row)
        try:
            options=json.loads((folder/'options.json').read_text());result['decision_engine']=options.get('decision_engine','rules')
            report=folder/'analysis/video-report.json'
            if report.is_file():
                r=json.loads(report.read_text());result.update(events=len(r.get('events',[])),sampled_frames=r.get('sampled_frames',0),truncated=r.get('truncated',False),duration_analyzed_s=r.get('duration_analyzed_s',0))
            result['source_retained']=(folder/'source.video').is_file() and row['status']=='completed'
            result['storage_bytes']=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())
        except (OSError,ValueError):pass
        return result
    def delete(self,job):
        with self.lock:
            row=self.get(job)
            if row is None:return False
            future=self.futures.get(job)
            if row['status'] in ('uploading','queued','running') or (future and not future.done()):raise ValueError('task is still active')
            if (self.root/job).exists():shutil.rmtree(self.root/job,ignore_errors=False)
            with self.connect() as c:c.execute('DELETE FROM jobs WHERE id=?',(job,))
            self.futures.pop(job,None)
            return True
    def close(self):self.executor.shutdown(wait=True,cancel_futures=True)
