@echo off
chcp 65001 >nul
title Hardware Engineering Toolbox - Dev App Launcher
echo ====================================================================
echo   Launching Desktop Dev Environment (Electron + React + FastAPI)
echo ====================================================================

echo [0/2] Cleaning up any leftover processes on port 5173 and 8000...
taskkill /f /im electron.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
  echo Killing process %%a on port 5173...
  taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
  echo Killing process %%a on port 8000...
  taskkill /f /pid %%a >nul 2>&1
)

:: Move to Source_Code directory
cd /d "%~dp0\Source_Code"

:: Check main shell dependencies
if not exist node_modules (
  echo [1/2] node_modules not found. Running npm install for Electron shell...
  call npm install
) else (
  echo [1/2] Electron shell dependencies are ready.
)

:: Check frontend dependencies
if not exist frontend\node_modules (
  echo [2/2] frontend node_modules not found. Running npm install for Vite...
  cd frontend
  call npm install
  cd ..
) else (
  echo [2/2] Frontend dependencies are ready.
)

echo ====================================================================
echo   Environment verified. Launching services and opening Electron window...
echo ====================================================================

call npm start

if %errorlevel% neq 0 (
  echo.
  echo [Diagnostics] Launcher exited with code %errorlevel%.
  pause
)
