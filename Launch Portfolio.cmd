@echo off
setlocal
set "PYTHONUTF8=1"
pushd "%~dp0" || exit /b 1
py -3.12 scripts\manage.py run all
set "result=%errorlevel%"
if not "%result%"=="0" (
  echo Launch failed. Follow the Windows setup in README.md or run Install Dependencies.cmd.
  pause
)
popd
exit /b %result%
