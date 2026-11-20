#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -f ../scripts/manage.py ]; then
  cd ..
  source scripts/env.sh
  exec python3 scripts/manage.py run manufacturing
fi
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
JAVA_EXEC="$(command -v java || true)"
if [ -z "$JAVA_EXEC" ] || ! "$JAVA_EXEC" -version >/dev/null 2>&1; then
  JAVA_EXEC='/Applications/IntelliJ IDEA.app/Contents/jbr/Contents/Home/bin/java'
fi
if [ ! -x "$JAVA_EXEC" ]; then echo '请安装 Java 17 或更新兼容版本，然后重试。'; read -r -p '按回车关闭'; exit 1; fi
if ! command -v node >/dev/null; then echo '请安装 Node.js 22 或更新版本，然后重试。'; read -r -p '按回车关闭'; exit 1; fi
if lsof -nP -iTCP:8080 -iTCP:8081 -sTCP:LISTEN >/dev/null 2>&1; then echo '8080 或 8081 端口已被占用。若平台已经启动，请直接打开 http://127.0.0.1:8081'; read -r -p '按回车关闭'; exit 1; fi
mkdir -p logs
(cd backend; exec "$JAVA_EXEC" -jar imcp-demo.jar) >logs/backend.log 2>&1 &
backend_pid=$!
trap 'kill "$backend_pid" 2>/dev/null || true' EXIT INT TERM
printf '制造协作平台：http://127.0.0.1:8081\n首次启动后台约需数秒。关闭此窗口会停止服务。\n'
node frontend/serve-built.mjs
