#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -f ../scripts/manage.py ]; then
  cd ..
  source scripts/env.sh
  exec python3 scripts/manage.py run firewatch
fi
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c 'import sys;assert sys.version_info[:2]==(3,12)' >/dev/null 2>&1; then
  fire_python="$(command -v python3.12 || true)"
  if [ -z "$fire_python" ]; then
    for candidate in ../.tools/python/cpython-3.12-*/bin/python3.12 ../.tools/bin/python3.12 /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12; do
      if [ -x "$candidate" ]; then fire_python="$candidate"; break; fi
    done
  fi
  if [ -z "$fire_python" ]; then echo '需要Python 3.12。完整作品集可先运行“修复Python环境.command”；独立包请先安装Python 3.12。'; read -r -p '按回车关闭'; exit 1; fi
  if [ -d .venv ]; then mv .venv ".venv-backup-$(date +%Y%m%d-%H%M%S)"; fi
  "$fire_python" -m venv .venv
fi
if ! .venv/bin/python -c 'import fastapi,uvicorn,cv2,PIL' >/dev/null 2>&1; then .venv/bin/python -m pip install -r requirements.txt; fi
echo '打开 http://127.0.0.1:8765；视频标注从“视频任务”进入，模型对照是可选功能。关闭终端窗口停止服务。'
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
