@echo off
setlocal enabledelayedexpansion

echo =======================================================================
echo          VoiceNexus Conversational IVR Platform
echo =======================================================================
echo Starting VoiceNexus on http://0.0.0.0:8000...
echo.
echo Available Portals:
echo   [Portal Gateway]:        http://localhost:8000/
echo   [1] PhoneCall:           http://localhost:8000/customer
echo   [2] Agent Workspace:     http://localhost:8000/agent
echo   [3] Care-Ops:            http://localhost:8000/ops
echo   [4] Admin Manager:       http://localhost:8000/admin
echo.
echo For Echo-Free Voice Testing:
echo   Open Window 1 at http://localhost:8000/customer
echo   Open Window 2 at http://localhost:8000/agent
echo =======================================================================
echo.

cd /d "%~dp0backend"
set PYTHONPATH=%~dp0backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
