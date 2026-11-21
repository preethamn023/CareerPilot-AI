@echo off
setlocal
title CareerPilot AI Launcher
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================================
echo                   CareerPilot AI Launcher
echo ================================================================
echo.

:: 1. Check Python
where python >nul 2>nul
if errorlevel 1 goto :no_python

:: 2. Check Node / npm
where npm >nul 2>nul
if errorlevel 1 goto :no_npm

:: 3. Check frontend dependencies
if not exist "frontend\node_modules\" goto :install_frontend
echo [1/3] Frontend dependencies already installed.
goto :start_servers

:install_frontend
echo [1/3] Installing frontend dependencies - first-time setup, please wait...
cd frontend
call npm install
if errorlevel 1 goto :npm_failed
cd ..
echo Frontend dependencies installed successfully.
echo.
goto :start_servers

:start_servers
:: 4. Start Backend
echo [2/3] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "CareerPilot AI - Backend" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --reload --port 8000"

:: 5. Start Frontend
echo [3/3] Starting React Frontend on http://localhost:3000 ...
start "CareerPilot AI - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: 6. Wait briefly for servers to boot and open browser
echo.
echo Waiting for servers to initialize...
ping 127.0.0.1 -n 5 >nul

echo Opening CareerPilot AI in your browser...
start http://localhost:3000

echo.
echo ================================================================
echo CareerPilot AI is up and running!
echo.
echo   - Web UI:       http://localhost:3000
echo   - Backend API:  http://127.0.0.1:8000
echo   - API Docs:     http://127.0.0.1:8000/docs
echo ================================================================
echo.
echo Note: The backend and frontend are running in separate terminal windows.
echo To stop CareerPilot AI, close those terminal windows or press Ctrl+C in them.
echo.
pause
exit /b 0

:no_python
echo [ERROR] Python was not found in your PATH.
echo Please install Python 3.11 or higher and ensure "Add Python to PATH" is checked.
echo.
pause
exit /b 1

:no_npm
echo [ERROR] Node.js or npm was not found in your PATH.
echo Please install Node.js v18 or higher from https://nodejs.org/
echo.
pause
exit /b 1

:npm_failed
echo [ERROR] npm install failed.
cd ..
pause
exit /b 1
