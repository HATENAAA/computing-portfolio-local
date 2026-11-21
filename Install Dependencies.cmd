@echo off
setlocal
set "PYTHONUTF8=1"
pushd "%~dp0" || exit /b 1
py -3.12 -c "import sys" >nul 2>&1
if errorlevel 1 (
  echo Install Python 3.12 for Windows with the Python Launcher. See README.md.
  popd
  pause
  exit /b 1
)
py -3.12 scripts\manage.py install all
set "result=%errorlevel%"
if not "%result%"=="0" echo Installation did not finish. See the error above and the Windows setup guide in README.md.
popd
pause
exit /b %result%
