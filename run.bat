@echo off
title Lenny Growth Assistant
echo.
echo  ========================================
echo    Lenny Growth Assistant - Starting...
echo  ========================================
echo.

:: Start Backend
echo  [1/2] Starting Backend (FastAPI) on http://localhost:8000 ...
cd /d "%~dp0backend"
start "Lenny Backend" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Give backend a moment to initialize
timeout /t 3 /nobreak >nul

:: Start Frontend
echo  [2/2] Starting Frontend (Vite) on http://localhost:3000 ...
cd /d "%~dp0frontend"
start "Lenny Frontend" cmd /k "npm run dev"

:: Wait briefly then open browser
timeout /t 3 /nobreak >nul
echo.
echo  ========================================
echo    All services started!
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo  ========================================
echo.
echo  Opening browser...
start http://localhost:3000
echo.
echo  Press any key to stop all services...
pause >nul

:: Kill the servers
taskkill /FI "WINDOWTITLE eq Lenny Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Lenny Frontend" /F >nul 2>&1
echo  Services stopped. Goodbye!
