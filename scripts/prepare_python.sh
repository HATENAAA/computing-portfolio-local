#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
if command -v python3.12 >/dev/null; then
  portfolio_launcher="$(command -v python3.12)"
else
  portfolio_launcher="$(command -v python3)"
fi
exec "$portfolio_launcher" scripts/python_runtime.py
