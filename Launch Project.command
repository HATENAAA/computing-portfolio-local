#!/bin/zsh
set -e
cd "$(dirname "$0")"
source scripts/env.sh

printf '%s\n' '1 VRFitAI' '2 Manufacturing' '3 Flame Detection' '4 Hyperspectral Reconstruction' \
  '5 Signal Analysis' '6 Shanghai Heritage Atlas' '7 Satellite Bathymetry' \
  '8 All Projects' '9 Health Screening'
printf 'Choose a project [8]: '
read -r choice || exit 0
case "$choice" in
  1) project=vrfitai ;;
  2) project=manufacturing ;;
  3) project=firewatch ;;
  4) project=hsi ;;
  5) project=signal ;;
  6) project=city ;;
  7) project=bathymetry ;;
  8|'') project=all ;;
  9) project=medical ;;
  *) printf 'Invalid choice. Select a number from 1 to 9.\n' >&2; exit 2 ;;
esac
exec python3 scripts/manage.py run "$project"
