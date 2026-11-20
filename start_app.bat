@echo off
title AnimalCare AI - Full Stack Launcher
echo ========================================================
echo   AnimalCare AI - Animal Disease Detection System
echo   Starting Flask Backend (port 5000) and React UI (5173)
echo ========================================================

start "AnimalCare AI - Flask Backend" cmd /k "cd /d "%~dp0backend" && .\venv\Scripts\python.exe app.py"
start "AnimalCare AI - React Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both servers are launching in separate windows:
echo   - Backend API : http://localhost:5000
echo   - Frontend UI : http://localhost:5173
echo.
timeout /t 3 >nul
start http://localhost:5173
