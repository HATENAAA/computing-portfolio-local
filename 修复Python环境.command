#!/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
source scripts/env.sh
if command -v python3.12 >/dev/null; then PORTFOLIO_PY=python3.12; else PORTFOLIO_PY=python3; fi
"$PORTFOLIO_PY" scripts/manage.py prepare-python
portfolio_result=$?
read -r -p '按回车关闭。'
exit "$portfolio_result"
