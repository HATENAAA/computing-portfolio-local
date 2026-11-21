#!/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
source scripts/env.sh
if command -v python3.12 >/dev/null; then PORTFOLIO_PY=python3.12; else PORTFOLIO_PY=python3; fi
"$PORTFOLIO_PY" scripts/manage.py install all
portfolio_result=$?
if [ "$portfolio_result" -eq 0 ]; then echo 'Installation complete. Open Launch Portfolio.command or Launch Project.command.'; else echo 'Installation did not finish. Check the error above and retry.'; fi
read -r -p 'Press Return to close.'
exit "$portfolio_result"
