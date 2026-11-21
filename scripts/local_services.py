"""Local service discovery shared by the launcher and the catalogue."""
import hashlib
import json
import os
import socket
import subprocess
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = {'vrfitai':8780,'firewatch':8765,'backend':8080,'manufacturing':8081,
            'hsi':8782,'signal':8783,'city':8766,'bathymetry':8784,'medical':8086,'hub':8790}
INDEX = {'vrfitai':'vrfitai/dist/index.html','firewatch':'firewatch/app/static/index.html',
         'manufacturing':'manufacturing-platform/frontend/dist/index.html','city':'city-explorer/dist/index.html',
         'hsi':'hsi-sr-lab/web/index.html','signal':'signal-lab/web/index.html','bathymetry':'bathymetry-lab/web/index.html',
         'medical':'case-studies/medical/source/dist/index.html'}
INSTANCE = hashlib.sha256(str(ROOT).encode()).hexdigest()[:20]
HTTP = build_opener(ProxyHandler({}))

def candidates(name):
    default=DEFAULTS[name]
    return [default]+[default+i*1000 for i in range(10,15)]

def listening(port):
    with socket.socket() as sock:
        sock.settimeout(.16)
        return sock.connect_ex(('127.0.0.1',port))==0

def available(port):
    with socket.socket() as sock:
        option = socket.SO_EXCLUSIVEADDRUSE if os.name == "nt" else socket.SO_REUSEADDR
        sock.setsockopt(socket.SOL_SOCKET, option, 1)
        try:sock.bind(('127.0.0.1',port))
        except OSError:return False
        return True

def matches(name,port):
    if not listening(port):return False
    endpoint={'hub':'/api/instance','backend':'/auth/demo','medical':'/api/health'}.get(name,'/')
    try:
        with HTTP.open(f'http://127.0.0.1:{port}{endpoint}',timeout=1.5) as response:
            if response.geturl()!=f'http://127.0.0.1:{port}{endpoint}':return False
            data=response.read(256*1024)
        if name=='hub':return json.loads(data).get('portfolio')==INSTANCE
        if name=='medical':return json.loads(data).get('project')=='medical-appointment'
        if name=='backend':
            record=json.loads(data)
            return isinstance(record.get('enabled'),bool) and isinstance(record.get('accounts'),dict)
        return data==(ROOT/INDEX[name]).read_bytes()
    except (OSError,ValueError,AttributeError):return False

def belongs_to_folder(port,folder):
    # On macOS distinguish identical builds in different copies of the portfolio.
    from shutil import which
    lsof=which('lsof')
    if not lsof:return True
    try:
        pids=subprocess.run([lsof,'-nP','-t',f'-iTCP:{port}','-sTCP:LISTEN'],capture_output=True,text=True,timeout=3).stdout.split()
        if not pids:return False
        result=subprocess.run([lsof,'-a','-p',','.join(pids),'-d','cwd','-Fn'],capture_output=True,text=True,timeout=3)
        return 'n'+str(folder.resolve()) in result.stdout.splitlines()
    except (OSError,subprocess.TimeoutExpired):return False

def active_port(name,folder=None):
    return next((port for port in candidates(name) if matches(name,port) and
                 (folder is None or belongs_to_folder(port,folder))),None)
