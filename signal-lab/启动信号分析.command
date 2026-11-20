#!/bin/zsh
cd "$(dirname "$0")/.." || exit 1
source scripts/env.sh
exec python3 scripts/manage.py run signal
