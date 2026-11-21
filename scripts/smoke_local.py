"""Exercise the installed portfolio from an isolated checkout."""
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener

from local_services import INDEX, DEFAULTS, active_port, listening

ROOT = Path(__file__).resolve().parents[1]
HTTP = build_opener(ProxyHandler({}))


def request(port, path, value=None, data=None, headers=None):
    headers = dict(headers or {})
    if value is not None:
        data = json.dumps(value).encode()
        headers['Content-Type'] = 'application/json'
    req = Request(f'http://127.0.0.1:{port}{path}', data, headers)
    with HTTP.open(req, timeout=20) as response:
        body = response.read()
        return json.loads(body) if 'application/json' in response.headers.get('Content-Type', '') else body


def smoke():
    env = dict(os.environ, PORTFOLIO_NO_BROWSER='1', PYTHONUTF8='1', PYTHONUNBUFFERED='1')
    args = [sys.executable, str(ROOT / 'scripts/manage.py'), 'run']
    flags = 0
    if os.name == 'nt':
        from ctypes import windll
        if not windll.kernel32.GetConsoleCP() and not windll.kernel32.AllocConsole():
            raise RuntimeError('Cannot allocate a console for testing Windows stop signals')
        flags = subprocess.CREATE_NEW_PROCESS_GROUP

    with tempfile.TemporaryDirectory(prefix='portfolio-smoke-') as workspace, socket.socket() as reserved:
        work = Path(workspace)
        env.update(FIREWATCH_DATA=str(work/'firewatch'), VRFITAI_DB=str(work/'vrfit.sqlite'),
                   SIGNAL_RUNS=str(work/'signal'))
        reserved.bind(('127.0.0.1', DEFAULTS['hub']))
        reserved.listen()
        log = work / 'launch.log'
        with log.open('wb') as stream:
            launcher = subprocess.Popen([*args, 'all'], cwd=ROOT, env=env, stdout=stream,
                                        stderr=subprocess.STDOUT, creationflags=flags)
        try:
            deadline = time.monotonic() + 150
            while '已就绪：' not in log.read_text(encoding='utf-8', errors='replace'):
                if launcher.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError('The full portfolio launcher did not become ready')
                time.sleep(.5)
            hub = active_port('hub')
            assert hub and hub != DEFAULTS['hub']
            ports = request(hub, '/api/services')
            assert set(ports) == set(INDEX) and all(ports.values()), ports
            for name, port in ports.items():
                assert request(port, '/'), name
            case = request(hub, '/projects/review/medical-en.html')
            assert b'src="../../assets/local-apps.js"' in case
            assert request(hub, '/assets/local-apps.js')
            print('Eight project home pages loaded; portfolio selected an alternate port.')

            assert request(ports['vrfitai'], '/api/programs')
            assert request(ports['hsi'], '/api/scenes')['scenes']
            assert request(ports['manufacturing'], '/api/auth/demo')['enabled']
            assert request(ports['medical'], '/api/health')['status'] == 'ok'
            assert request(ports['signal'], '/api/analyze', {})['peak_hz'] > 0
            assert request(ports['bathymetry'], '/api/train', {'demo': True})['samples'] == 120
            sample = (ROOT / 'firewatch/app/static/furg/Car1-00269.jpg').read_bytes()
            boundary = 'portfolio-check'
            body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="sample.jpg"\r\n'
                    'Content-Type: image/jpeg\r\n\r\n').encode() + sample + f'\r\n--{boundary}--\r\n'.encode()
            detected = request(ports['firewatch'], '/api/native/analyze', data=body,
                               headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
            assert detected['algorithm'] == 'cpp-region-motion-v1'
            print('Project APIs and native C++ image detection passed.')
            repeat = subprocess.run([*args, 'hub'], cwd=ROOT, env=env, creationflags=flags,
                                    capture_output=True, text=True, encoding='utf-8', timeout=20, check=True)
            assert f'复用 hub · {hub}' in repeat.stdout
        except BaseException:
            print(log.read_text(encoding='utf-8', errors='replace'), file=sys.stderr)
            raise
        finally:
            if launcher.poll() is None:
                try:
                    launcher.send_signal(signal.CTRL_BREAK_EVENT if os.name == 'nt' else signal.SIGINT)
                    launcher.wait(timeout=25)
                except (OSError, subprocess.TimeoutExpired):
                    if os.name == 'nt':
                        subprocess.run(['taskkill', '/PID', str(launcher.pid), '/T', '/F'],
                                       capture_output=True, check=False)
                    else:
                        launcher.kill()
                    launcher.wait(timeout=10)
                    raise
        deadline = time.monotonic() + 10
        owned = [hub, *ports.values()]
        while any(listening(port) for port in owned):
            if time.monotonic() > deadline:
                raise RuntimeError('A project port remained open after stopping the launcher')
            time.sleep(.25)
        print('Reused the same hub and released all managed ports on shutdown.')


if __name__ == '__main__':
    smoke()
