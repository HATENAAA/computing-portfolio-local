#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -f ../scripts/manage.py ]; then
  cd ..
  source scripts/env.sh
  exec python3 scripts/manage.py run vrfitai
fi
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v node >/dev/null; then echo '需要 Node.js 22.13 或更新版本。'; read -r -p '按回车关闭'; exit 1; fi
if ! node -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit(a>22||a===22&&b>=13?0:1)'; then echo 'Node.js 版本过低，需要22.13或更新版本。'; read -r -p '按回车关闭'; exit 1; fi
if ! node --input-type=module -e "await import('express');await import('zod')" >/dev/null 2>&1; then npm ci --no-audit --no-fund; fi
if [ ! -f dist/index.html ]; then npm run build; fi
echo '打开 http://127.0.0.1:8780；关闭此窗口会停止服务。'
npm start
