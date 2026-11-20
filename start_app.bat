@echo off
title AnimalCare AI - Full Stack Launcher
echo ========================================================
echo   AnimalCare AI - Animal Disease Detection System
echo   Starting Flask Backend (127.0.0.1:5000) and React UI
echo ========================================================

if "%ADMIN_TOKEN%"=="" set ADMIN_TOKEN=local-dev-admin

start "AnimalCare AI - Flask Backend" cmd /k "cd /d "%~dp0" && set ADMIN_TOKEN=%ADMIN_TOKEN%&& .\backend\venv\Scripts\python.exe -m backend.app"
start "AnimalCare AI - React Frontend" cmd /k "cd /d "%~dp0frontend" && set VITE_ADMIN_TOKEN=%ADMIN_TOKEN%&& npm run dev"

echo.
echo Both servers are launching in separate windows:
echo   - Backend API : http://127.0.0.1:5000
echo   - Frontend UI : http://localhost:5173
echo.
timeout /t 3 >nul
start http://localhost:5173
