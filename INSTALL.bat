@echo off
chcp 65001 > nul
title Arvis Installation
cd /d "%~dp0"

echo ========================================
echo     ARVIS AI ASSISTANT INSTALLATION
echo ========================================
echo.

REM Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo.
    echo Install Python 3.11.9 or 3.12.x from https://python.org
    echo Check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo OK: Python found
python --version
echo.

REM Check Python version
echo [2/6] Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Version: %PYTHON_VERSION%

echo %PYTHON_VERSION% | findstr /C:"3.13" >nul
if %errorlevel% equ 0 (
    echo.
    echo WARNING: Python 3.13 has limited support
    echo PyAudio may not work, Python 3.11 or 3.12 recommended
    echo.
    timeout /t 3 /nobreak >nul
)

REM Create virtual environment
echo.
echo [3/6] Creating virtual environment...
if exist "venv" (
    echo Removing old environment...
    rmdir /s /q venv 2>nul
    timeout /t 1 /nobreak >nul
)

python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    echo Try running as administrator
    pause
    exit /b 1
)
echo OK: Virtual environment created

REM Activate environment
echo.
echo [4/6] Activating environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate environment
    pause
    exit /b 1
)

REM Update pip
echo.
echo [5/6] Updating pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install dependencies
echo.
echo [6/6] Installing dependencies (5-10 minutes)...
echo    - Main packages...
pip install -r requirements.txt --no-warn-script-location
if %errorlevel% neq 0 (
    echo WARNING: Some packages failed
    echo Installing critical packages...
    pip install PyQt5 requests vosk soundfile numpy torch torchaudio --index-url https://download.pytorch.org/whl/cpu
)

echo    - PyAudio (may fail on Python 3.13)...
pip install pyaudio >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: PyAudio not installed - some audio features unavailable
) else (
    echo OK: PyAudio installed
)

REM Create folders
if not exist "logs" mkdir logs
if not exist "models" mkdir models
if not exist "data" mkdir data
if not exist "temp" mkdir temp

echo.
echo ========================================
echo        INSTALLATION COMPLETE!
echo ========================================
echo.
echo OK: Arvis is ready to use
echo.
echo NEXT STEPS:
echo    1. Install Ollama: https://ollama.ai
echo    2. Run: LAUNCH.bat
echo.
echo ADDITIONAL COMMANDS:
echo    STATUS.bat        - check system
echo    DIAGNOSTIC.bat    - troubleshooting
echo.
pause
