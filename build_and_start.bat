@echo off
setlocal enabledelayedexpansion

echo =======================================================================
echo          VoiceNexus Conversational IVR Platform - Build & Run
echo =======================================================================

echo [1/3] Building React Production Frontend...
cd /d "%~dp0frontend"
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed!
    pause
    exit /b %errorlevel%
)

echo [2/3] Detecting Local IP for Team Network Testing...
for /f "tokens=4" %%a in ('route print ^| findstr 0.0.0.0 ^| findstr /v "0.0.0.0.*0.0.0.0"') do (
    set LOCAL_IP=%%a
)

echo =======================================================================
echo VoiceNexus is ready for real-time team testing:
echo.
echo   [Portal Gateway]:        http://localhost:8000/
echo   [1] PhoneCall:           http://localhost:8000/customer
echo   [2] Agent Workspace:     http://localhost:8000/agent
echo   [3] Care-Ops:            http://localhost:8000/ops
echo   [4] Admin Manager:       http://localhost:8000/admin
echo.
if defined LOCAL_IP (
    echo For Mobile Phones & Team Testing on Same Wi-Fi Network:
    echo   Customer Mobile Phone:   http://!LOCAL_IP!:8000/customer
    echo   Agent Laptop:            http://!LOCAL_IP!:8000/agent
    echo.
)
echo Tip for Echo-Free Audio Testing:
echo   Open [Customer Phone] in Window 1 and [Agent Desktop] in Window 2.
echo =======================================================================
echo.

echo [3/3] Starting VoiceNexus Uvicorn Server on 0.0.0.0:8000...
cd /d "%~dp0backend"
set PYTHONPATH=%~dp0backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
