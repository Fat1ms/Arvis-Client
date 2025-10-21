@echo off
chcp 65001 > nul
title Arvis AI Assistant
cd /d "%~dp0"

echo ========================================
echo      ARVIS AI ASSISTANT LAUNCH
echo ========================================
echo.

REM Check virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Run first: INSTALL.bat
    echo.
    pause
    exit /b 1
)

echo OK: Activating environment...
call venv\Scripts\activate.bat

REM Check dependencies
echo Checking dependencies...
python -c "import PyQt6" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PyQt6 not installed!
    echo Run: INSTALL.bat
    pause
    exit /b 1
)

REM Start Ollama
echo Starting Ollama...
tasklist | findstr "ollama" >nul 2>&1
if %errorlevel% neq 0 (
    echo Starting Ollama in separate window...
    start "Ollama Server" cmd /k "ollama serve"
    timeout /t 5 /nobreak >nul
) else (
    echo OK: Ollama already running
)

REM Check Ollama availability
python -c "import requests; requests.get('http://127.0.0.1:11434/api/version', timeout=2)" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Ollama not responding
    echo AI features may be unavailable
    echo.
)

echo.
echo Starting Arvis GUI...
echo ========================================
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Arvis failed to start
    echo.
    echo For diagnostics run: DIAGNOSTIC.bat
    echo Check logs in: logs\
    echo.
    pause
) else (
    echo.
    echo OK: Arvis closed correctly
)
