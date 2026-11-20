#!/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
source scripts/env.sh
python3 scripts/update_portfolio.py
portfolio_update_result=$?
read -r -p '按回车关闭。'
exit "$portfolio_update_result"
