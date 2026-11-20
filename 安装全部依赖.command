#!/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
source scripts/env.sh
if command -v python3.12 >/dev/null; then PORTFOLIO_PY=python3.12; else PORTFOLIO_PY=python3; fi
"$PORTFOLIO_PY" scripts/manage.py install all
portfolio_result=$?
if [ "$portfolio_result" -eq 0 ]; then echo '安装完成。请双击“启动作品.command”。'; else echo '安装尚未完成，请保留上方错误信息。已成功安装的内容会保留，修复后可以重试。'; fi
read -r -p '按回车关闭。'
exit "$portfolio_result"
