"""Small loopback-only numerical workbench host, shared by two standalone labs."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import json,threading,argparse

def serve(app,static,default_port):
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=default_port);args=parser.parse_args();static=Path(static);slots=threading.BoundedSemaphore(2)
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def reply(self,status,data,content_type='application/json; charset=utf-8',attachment=None):
   if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
   self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
   if attachment:self.send_header('Content-Disposition','attachment; filename="'+attachment+'"')
   self.end_headers();self.wfile.write(data)
  def allowed_host(self):
   return self.headers.get('Host') in ['127.0.0.1:'+str(args.port),'localhost:'+str(args.port)]
  def do_GET(self):
   if not self.allowed_host():return self.reply(403,{'error':'仅允许本机访问'})
   acquired=False
   try:
    parsed=urlsplit(self.path);path=parsed.path
    if path=='/api/health':return self.reply(200,{'status':'ok','project':app.name})
    if path.startswith('/api/'):
     if path=='/api/view':
      acquired=slots.acquire(blocking=False)
      if not acquired:return self.reply(429,{'error':'有分析正在运行，请稍后重试'})
     result=app.get(path,parse_qs(parsed.query));return self.reply(*result) if isinstance(result,tuple) else self.reply(200,result)
    name='index.html' if path=='/' else path[1:]
    if name not in ['index.html','app.js','style.css','compare.html','evidence.html','tokens.css','plot-data.js','template.csv','mitdb-100-10s.csv']:return self.reply(404,{'error':'页面不存在'})
    types={'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8','csv':'text/csv; charset=utf-8'}
    self.reply(200,(static/name).read_bytes(),types[name.split('.')[-1]])
   except (ValueError,KeyError,FileNotFoundError) as e:self.reply(400,{'error':str(e)})
   except (BrokenPipeError,ConnectionResetError):pass
   except Exception:self.reply(500,{'error':'读取结果失败，请检查本机运行日志。'})
   finally:
    if acquired:slots.release()
  def do_POST(self):
   if not self.allowed_host():return self.reply(403,{'error':'仅允许本机访问'})
   origin=self.headers.get('Origin')
   if origin and origin not in ['http://127.0.0.1:'+str(args.port),'http://localhost:'+str(args.port)]:return self.reply(403,{'error':'请求来源不允许'})
   if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply(415,{'error':'需要JSON请求'})
   try:length=int(self.headers.get('Content-Length','-1'))
   except ValueError:length=-1
   if length<0 or length>48*1024*1024:return self.reply(413,{'error':'请求过大，最大48MB'})
   if not slots.acquire(blocking=False):return self.reply(429,{'error':'有分析正在运行，请稍后重试'})
   try:
    value=json.loads(self.rfile.read(length),parse_constant=lambda v:(_ for _ in ()).throw(ValueError('不允许NaN或Infinity')))
    if not isinstance(value,dict):raise ValueError('请求须为对象')
    self.reply(200,app.post(urlsplit(self.path).path,value))
   except (ValueError,KeyError,TypeError,UnicodeError) as e:self.reply(400,{'error':str(e)})
   except (BrokenPipeError,ConnectionResetError):pass
   except Exception:self.reply(500,{'error':'分析失败，未发布部分结果，请检查数据与本机日志。'})
   finally:slots.release()
 server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.daemon_threads=True
 print(app.name+'  http://127.0.0.1:'+str(args.port),flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
