@echo off
setlocal
set "PYTHONUTF8=1"
pushd "%~dp0" || exit /b 1
py -3.12 scripts\configure_ai.py
set "result=%errorlevel%"
popd
pause
exit /b %result%
