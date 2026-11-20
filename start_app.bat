@echo off
title AnimalCare AI - Full Stack Launcher
echo ========================================================
echo   AnimalCare AI - Animal Disease Detection System
echo   Starting Flask Backend (127.0.0.1:5000) and React UI
echo ========================================================
if "%ADMIN_TOKEN%"=="" (
  echo [Note] ADMIN_TOKEN is not set. History delete actions stay disabled
  echo        until you set ADMIN_TOKEN before starting the backend.
)

start "AnimalCare AI - Flask Backend" cmd /k "cd /d "%~dp0" && .\backend\venv\Scripts\python.exe -m backend.app"
start "AnimalCare AI - React Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both servers are launching in separate windows:
echo   - Backend API : http://127.0.0.1:5000
echo   - Frontend UI : http://localhost:5173
echo.
timeout /t 3 >nul
start http://localhost:5173
