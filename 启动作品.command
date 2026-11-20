#!/bin/zsh
cd "$(dirname "$0")"
source scripts/env.sh
echo "选择：1 VRFitAI / 2 制造系统 / 3 火焰检测 / 4 高光谱 / 5 信号 / 6 城市地图 / 7 卫星测深 / 8 全部 / 9 熙心健康体检"
read choice
case "$choice" in
  1) project=vrfitai;; 2) project=manufacturing;; 3) project=firewatch;; 4) project=hsi;; 5) project=signal;; 6) project=city;; 7) project=bathymetry;; 9) project=medical;; *) project=all;;
esac
python3 scripts/manage.py run "$project"
