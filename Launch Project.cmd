@echo off
setlocal
set "PYTHONUTF8=1"
pushd "%~dp0" || exit /b 1
echo 1 VRFitAI
echo 2 Manufacturing
echo 3 Flame Detection
echo 4 Hyperspectral Reconstruction
echo 5 Signal Analysis
echo 6 Shanghai Heritage Atlas
echo 7 Satellite Bathymetry
echo 8 All Projects
echo 9 Health Screening
choice /c 123456789 /m "Choose a project"
set "selected=%errorlevel%"
set "project="
if "%selected%"=="1" set "project=vrfitai"
if "%selected%"=="2" set "project=manufacturing"
if "%selected%"=="3" set "project=firewatch"
if "%selected%"=="4" set "project=hsi"
if "%selected%"=="5" set "project=signal"
if "%selected%"=="6" set "project=city"
if "%selected%"=="7" set "project=bathymetry"
if "%selected%"=="8" set "project=all"
if "%selected%"=="9" set "project=medical"
if not defined project (
  popd
  exit /b 1
)
py -3.12 scripts\manage.py run %project%
set "result=%errorlevel%"
if not "%result%"=="0" pause
popd
exit /b %result%
