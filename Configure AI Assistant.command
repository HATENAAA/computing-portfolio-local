#!/bin/bash
set -e
cd "$(dirname "$0")"
source scripts/env.sh
python3 scripts/configure_ai.py
printf '\nPress Return to close.'
read -r
