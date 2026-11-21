#!/usr/bin/env python3
"""Find an existing Python first; bound every optional bootstrap download."""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

UV_VERSION = '0.13.7'
INSTALLERS = (
    'https://releases.astral.sh/github/uv/releases/download/' + UV_VERSION + '/uv-installer.sh',
    'https://github.com/astral-sh/uv/releases/download/' + UV_VERSION + '/uv-installer.sh',
)
PROBE = 'import sys,ssl,sqlite3,venv,ensurepip,json; print(json.dumps({"version":list(sys.version_info[:2]),"base":getattr(sys,"_base_executable",sys.executable)}))'


def candidates(root):
    home = Path.home()
    values = [os.environ.get('PORTFOLIO_PYTHON')]
    receipt = root / '.tools/python312.path'
    if receipt.is_file():
        values.append(receipt.read_text().strip())
    values += [sys.executable, shutil.which('python3.12')]
    for folder, pattern in (
        (root / '.tools/python', '*/bin/python3.12'),
        (home / '.local/share/uv/python', '*/bin/python3.12'),
        (home / '.pyenv/versions', '3.12*/bin/python3.12'),
    ):
        values += [str(p) for p in sorted(folder.glob(pattern), reverse=True)]
    values += [
        '/opt/homebrew/bin/python3.12', '/opt/homebrew/opt/python@3.12/bin/python3.12',
        '/usr/local/bin/python3.12', '/usr/local/opt/python@3.12/bin/python3.12',
        '/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12',
        # An optional installed application runtime; never required or copied.
        str(home / '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'),
    ]
    seen = set()
    for value in values:
        if not value:
            continue
        path = Path(value).expanduser()
        key = str(path.resolve())
        if key not in seen and path.is_file():
            seen.add(key)
            yield str(path)


def find_existing(root):
    for executable in candidates(root):
        try:
            result = subprocess.run([executable, '-I', '-c', PROBE], capture_output=True, text=True, timeout=8)
            data = json.loads(result.stdout) if result.returncode == 0 else {}
            if data.get('version') != [3, 12]:
                continue
            base = data.get('base', executable)
            if base != executable:
                check = subprocess.run([base, '-I', '-c', PROBE], capture_output=True, text=True, timeout=8)
                if check.returncode or json.loads(check.stdout).get('version') != [3, 12]:
                    continue
            return base
        except (OSError, ValueError, subprocess.TimeoutExpired):
            continue
    return None


def stop_process(process):
    if os.name == 'posix':
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        process.kill()
    process.wait()


def run_step(args, log, label, timeout, env=None, progress_file=None):
    print(label + '（最长 ' + str(timeout) + ' 秒）', flush=True)
    print('日志：' + str(log), flush=True)
    started = time.monotonic()
    next_notice = started + 5
    with log.open('ab', buffering=0) as output:
        process = subprocess.Popen(list(map(str, args)), stdout=output, stderr=subprocess.STDOUT,
                                   env=env, start_new_session=(os.name == 'posix'))
        try:
            while process.poll() is None:
                now = time.monotonic()
                if now - started >= timeout:
                    stop_process(process)
                    raise RuntimeError(label + '超时；已停止本步骤。请检查网络后重试，或自行安装 Python 3.12。日志：' + str(log))
                if now >= next_notice:
                    downloaded = ''
                    if progress_file and progress_file.exists():
                        downloaded = '，已下载 ' + str(progress_file.stat().st_size // 1024) + ' KB'
                    print('  ' + label + '：已用 ' + str(int(now - started)) + ' 秒' + downloaded, flush=True)
                    next_notice = now + 5
                time.sleep(0.2)
        except BaseException:
            if process.poll() is None:
                stop_process(process)
            raise
    if process.returncode:
        tail = log.read_text(errors='replace')[-1800:]
        raise RuntimeError(label + '失败（退出码 ' + str(process.returncode) + '）。\n' + tail + '\n日志：' + str(log))


def bootstrap(root):
    tools = root / '.tools'
    for name in ('bin', 'python', 'cache', 'logs'):
        (tools / name).mkdir(parents=True, exist_ok=True)
    log = tools / 'logs/python-setup.log'
    log.write_text('Python setup started\n')
    env = os.environ.copy()
    env.update(UV_PYTHON_INSTALL_DIR=str(tools / 'python'), UV_PYTHON_BIN_DIR=str(tools / 'bin'),
               UV_CACHE_DIR=str(tools / 'cache'), UV_UNMANAGED_INSTALL=str(tools / 'bin'),
               UV_NO_MODIFY_PATH='1', UV_NO_PROGRESS='1', UV_HTTP_CONNECT_TIMEOUT='10',
               UV_HTTP_TIMEOUT='30', UV_HTTP_RETRIES='1')
    uv = next((str(p) for p in (tools / 'bin/uv', Path.home() / '.local/bin/uv')
               if p.is_file() and os.access(p, os.X_OK)), None) or shutil.which('uv')
    if not uv:
        curl = shutil.which('curl')
        if not curl:
            raise RuntimeError('找不到 curl。请安装 Python 3.12 后重试。')
        installer = tools / 'uv-install.sh'
        errors = []
        for url in INSTALLERS:
            partial = tools / 'uv-install.sh.partial'
            if partial.exists():
                partial.unlink()
            print('下载来源：' + url, flush=True)
            try:
                run_step([curl, '--fail', '--location', '--show-error', '--silent',
                          '--connect-timeout', '10', '--max-time', '40', '--speed-limit', '512',
                          '--speed-time', '15', '--output', partial, url],
                         log, '下载环境工具安装脚本', 45, env, partial)
                if not partial.read_bytes().startswith(b'#!/'):
                    raise RuntimeError('下载内容不是有效安装脚本。')
                partial.replace(installer)
                break
            except RuntimeError as error:
                errors.append(str(error))
                print('当前下载源失败，尝试下一官方来源。', flush=True)
            finally:
                if partial.exists():
                    partial.unlink()
        else:
            raise RuntimeError('两个官方来源均未下载成功。请检查网络，或通过 python.org 安装 Python 3.12 后重试。\n' + '\n'.join(errors))
        run_step(['/bin/sh', installer], log, '安装环境工具 uv', 180, env)
        uv = str(tools / 'bin/uv')
        if not Path(uv).is_file():
            raise RuntimeError('环境工具未生成，详情见 ' + str(log))
    run_step([uv, 'python', 'install', '3.12', '--install-dir', tools / 'python'],
             log, '下载并安装 Python 3.12', 300, env)


def ensure_python312(root, download=False):
    root = Path(root).resolve()
    existing = find_existing(root)
    if existing:
        return existing
    if not download:
        raise RuntimeError('尚未找到可用的 Python 3.12。请安装 Python 3.12 后重试，或在仓库根目录运行 python3 scripts/manage.py prepare-python。')
    print('本机尚无可用 Python 3.12，开始准备；每个步骤均有超时和日志。', flush=True)
    bootstrap(root)
    existing = find_existing(root)
    if not existing:
        raise RuntimeError('下载结束后仍未找到可用的 Python 3.12，请查看 .tools/logs/python-setup.log。')
    return existing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--find-only', action='store_true')
    args = parser.parse_args()
    executable = ensure_python312(args.root, not args.find_only)
    print('Python 3.12 已就绪：' + executable, flush=True)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError) as error:
        print('环境准备未完成：' + str(error), file=sys.stderr)
        sys.exit(1)
