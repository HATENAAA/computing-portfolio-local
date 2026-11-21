#!/bin/bash
set -e
cd "$(dirname "$0")"
source scripts/env.sh
if command -v python3.12 >/dev/null; then PORTFOLIO_PY=python3.12; else PORTFOLIO_PY=python3; fi
"$PORTFOLIO_PY" scripts/manage.py run all
