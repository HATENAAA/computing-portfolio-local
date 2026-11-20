#!/usr/bin/env python3
"""Local portfolio setup and process runner; no global package installation."""
import argparse,os,sys,subprocess,shutil,signal,time,socket,webbrowser,hashlib
from urllib.request import urlopen
from pathlib import Path
from python_runtime import ensure_python312
import local_services as services
import fcntl,tempfile
ROOT=Path(__file__).resolve().parents[1]
PROJECTS={'vrfitai':('node','vrfitai',None),'firewatch':('python','firewatch','requirements.txt'),'manufacturing':('manufacturing','manufacturing-platform',None),'hsi':('python','hsi-sr-lab','requirements-eval.txt'),'signal':('python','signal-lab','requirements.txt'),'city':('node','city-explorer',None),'bathymetry':('python','bathymetry-lab','requirements.txt'),'medical':('medical','medical-platform',None)}
def execute(args,cwd=ROOT,env=None):
 print('→',' '.join(map(str,args)),flush=True);subprocess.run(list(map(str,args)),cwd=cwd,env=env,check=True)
def command(name):
 value=shutil.which(name)
 ide=Path('/Applications/IntelliJ IDEA.app/Contents')
 if name=='mvn' and not value:
  candidate=ide/'plugins/maven/lib/maven3/bin/mvn'
  if candidate.is_file():value=str(candidate)
 if name=='java' and (not value or value=='/usr/bin/java'):
  candidate=ide/'jbr/Contents/Home/bin/java'
  if candidate.is_file():value=str(candidate);os.environ['JAVA_HOME']=str(candidate.parent.parent)
 if not value:raise RuntimeError(f'找不到 {name}，请先按安装运行指南安装基础工具。')
 return value
def python_env(folder):return folder/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
_PYTHON312=None
def find_python312(install_missing=False):
 global _PYTHON312
 if _PYTHON312:return _PYTHON312
 _PYTHON312=ensure_python312(ROOT,download=install_missing)
 print('复用 Python 3.12：'+_PYTHON312,flush=True)
 return _PYTHON312
def install(name):
 kind,path,req=PROJECTS[name];folder=ROOT/path
 if kind=='python':
  base_python=find_python312(True)
  py=python_env(folder)
  if py.exists():
   version=subprocess.check_output([str(py),'-c','import sys;print(str(sys.version_info[0])+"."+str(sys.version_info[1]))'],text=True).strip()
   if version!='3.12':
    backup=folder/('.venv.backup-'+str(time.time_ns()));shutil.move(str(folder/'.venv'),str(backup));print('旧虚拟环境已备份到 '+str(backup),flush=True)
  if not py.exists():execute([base_python,'-m','venv',folder/'.venv'])
  execute([py,'-m','pip','install','-r','requirements-lock.txt' if (folder/'requirements-lock.txt').exists() else req],cwd=folder)
  if name=='firewatch':execute([py,'native/build.py'],cwd=folder)
 elif kind=='node':
  node=command('node');major,minor=map(int,subprocess.check_output([node,'-p','process.versions.node'],text=True).strip().split('.')[:2])
  if major<22 or (major==22 and minor<13):raise RuntimeError('需要 Node.js 22.13 或更新版本。')
  execute([command('npm'),'ci','--no-audit','--no-fund'],cwd=folder);execute([command('npm'),'run','build'],cwd=folder)
 elif kind=='medical':
  frontend=ROOT/'case-studies/medical/source'
  execute([command('npm'),'ci','--no-audit','--no-fund'],cwd=frontend)
  execute([command('npm'),'run','build'],cwd=frontend)
  command('java')
  execute([command('mvn'),'-DskipTests','package'],cwd=folder/'backend')
 else:
  command('java');execute([command('mvn'),'-DskipTests','package'],cwd=folder/'backend');shutil.copy2(folder/'backend/target/imcp-1.1.0.jar',folder/'backend/imcp-demo.jar');execute([command('npm'),'ci','--no-audit','--no-fund'],cwd=folder/'frontend');execute([command('npm'),'run','build'],cwd=folder/'frontend')
def require_file(p):
 if not p.exists():raise RuntimeError('缺少依赖或构建文件，请先运行安装全部依赖，或按指南安装对应项目。')
 return str(p)
def home_url(port=8790):
 token=hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()[:12]
 return f'http://127.0.0.1:{port}/?v='+token
def jobs_for(name):
 if name=='all':
  jobs=[];ports=[]
  for item in ['vrfitai','firewatch','manufacturing','hsi','signal','city','bathymetry','medical','hub']:
   batch,used,_=jobs_for(item);jobs.extend(batch);ports.extend(used)
  return jobs,ports,home_url()
 if name=='hub':return [([sys.executable,'scripts/hub_server.py'],ROOT)],[8790],home_url()
 if name=='vrfitai':
  require_file(ROOT/'vrfitai/dist/index.html');return [([command('node'),'server/index.js'],ROOT/'vrfitai')],[8780],'http://127.0.0.1:8780'
 if name=='firewatch':return [([require_file(python_env(ROOT/'firewatch')),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8765'],ROOT/'firewatch')],[8765],'http://127.0.0.1:8765'
 if name=='manufacturing':
  folder=ROOT/'manufacturing-platform';require_file(folder/'frontend/dist/index.html');return [([command('java'),'-jar',require_file(folder/'backend/imcp-demo.jar')],folder/'backend'),([command('node'),'frontend/serve-built.mjs'],folder)],[8080,8081],'http://127.0.0.1:8081'
 if name=='medical':
  folder=ROOT/'medical-platform/backend'
  require_file(ROOT/'case-studies/medical/source/dist/index.html')
  return [([command('java'),'-jar',require_file(folder/'target/tijian-1.0.0.jar')],folder)],[8086],'http://127.0.0.1:8086'
 if name=='city':
  folder=ROOT/'city-explorer';require_file(folder/'dist/index.html')
  return [([sys.executable,'-m','http.server','8766','--bind','127.0.0.1','--directory','dist'],folder)],[8766],'http://127.0.0.1:8766'
 if name in ['hsi','signal','bathymetry']:
  folder=ROOT/PROJECTS[name][1];port={'hsi':8782,'signal':8783,'bathymetry':8784}[name]
  return [([require_file(python_env(folder)),'workbench.py','--port',str(port)],folder)],[port],'http://127.0.0.1:'+str(port)
 raise RuntimeError('未知网页项目')
def serve(name):
 jobs,defaults,_=jobs_for(name)
 names={port:key for key,port in services.DEFAULTS.items()}
 chosen={};children=[];starting={}
 lock=Path(tempfile.gettempdir())/('portfolio-'+services.INSTANCE+'.lock')
 try:
  with lock.open('a') as gate:
   fcntl.flock(gate,fcntl.LOCK_EX)
   for (args,cwd),default in zip(jobs,defaults):
    key=names[default]
    live=services.active_port(key,cwd)
    if live:
     chosen[key]=live
     print(f'复用 {key} · {live}',flush=True)
     continue
    port=next((p for p in services.candidates(key) if services.available(p)),None)
    if port is None:raise RuntimeError(f'{key} 的候选端口均在使用中。')
    chosen[key]=port
    env=os.environ.copy()
    if key=='vrfitai':env.update(PORT=str(port),HOST='127.0.0.1')
    elif key in ('backend','medical'):args=[*args,'--server.port='+str(port),'--server.address=127.0.0.1']
    elif key=='manufacturing':env.update(WEB_PORT=str(port),API_PORT=str(chosen['backend']))
    elif key=='hub':args=[*args,str(port)]
    else:args=[str(port) if str(arg)==str(default) else arg for arg in args]
    print(f'启动 {key} · {port}'+(f'（原端口 {default} 已占用）' if port!=default else ''),flush=True)
    child=subprocess.Popen(args,cwd=cwd,env=env);children.append(child);starting[key]=child
   pending=set(starting);deadline=time.monotonic()+90
   while pending:
    for key in tuple(pending):
     if starting[key].poll() is not None:raise RuntimeError(key+' 启动失败，请查看上方日志。')
     if services.matches(key,chosen[key]):pending.remove(key)
    if time.monotonic()>deadline:raise RuntimeError('未就绪的服务：'+', '.join(sorted(pending)))
    if pending:time.sleep(.25)
   if 'manufacturing' in chosen and not os.environ.get('DB_URL'):
    seed = ROOT/'manufacturing-platform/scripts/seed_demo.py'
    base = f"http://127.0.0.1:{chosen['manufacturing']}/api"
    try:
     execute([sys.executable, '-B', seed, '--base', base, '--inventory-only'])
    except subprocess.CalledProcessError:
     print('制造演示库存初始化失败，可重新运行启动器重试。', file=sys.stderr, flush=True)
  target='hub' if name=='all' else name
  url=home_url(chosen[target]) if target=='hub' else f'http://127.0.0.1:{chosen[target]}/'
  print('已就绪：'+url,flush=True)
  if os.environ.get('PORTFOLIO_NO_BROWSER')!='1':webbrowser.open(url)
  if children:print('关闭本窗口将停止本次新启动的服务。',flush=True)
  while children:
   for key,child in starting.items():
    if child.poll() is not None:raise RuntimeError(key+' 已退出，请查看上方日志。')
   time.sleep(.4)
 except KeyboardInterrupt:print('正在停止本次新启动的服务…',flush=True)
 finally:
  for child in children:
   if child.poll() is None:child.terminate()
  for child in children:
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:child.kill();child.wait()
def main():
 p=argparse.ArgumentParser(description='作品集依赖安装与启动');p.add_argument('action',choices=['install','run','check','prepare-python']);p.add_argument('project',nargs='?',default='all',choices=['all','hub']+list(PROJECTS));a=p.parse_args()
 if a.action=='prepare-python':
  print('作品集 Python 3.12：'+find_python312(True));return
 if a.action=='check':
  print('启动器 Python:',sys.version.split()[0]);
  try:print('依赖环境 Python:',find_python312(False))
  except RuntimeError:print('依赖环境 Python: 尚未准备，安装时将自动创建')
  for name in ['node','npm','java','mvn']:print(name+':',shutil.which(name) or '未找到')
  return
 if a.action=='install':
  names=list(PROJECTS) if a.project=='all' else [a.project]
  if a.project=='all':
   find_python312(True)
   for tool in ['node','npm','java','mvn']:command(tool)
  for name in names:
   if name=='hub':continue
   print('\n安装 '+name,flush=True);install(name)
  print('\n安装完成。请双击“启动作品.command”选择项目。')
 else:
  serve(a.project)
if __name__=='__main__':
 try:main()
 except (RuntimeError,subprocess.CalledProcessError) as e:print('\n操作未完成：'+str(e),file=sys.stderr);sys.exit(1)
