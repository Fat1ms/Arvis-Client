@echo off
REM Быстрая диагностика регистрации пользователей через сервер
REM Автор: Copilot (GitHub)
REM Дата: 09.10.2025

echo ============================================================
echo ARVIS CLIENT REGISTRATION DIAGNOSTIC TOOL
echo ============================================================
echo.

REM Активируем виртуальное окружение
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    echo Please run INSTALL.bat first
    pause
    exit /b 1
)

echo Running diagnostic tests...
echo.

REM Запускаем диагностику
python tests\test_client_registration.py

echo.
echo ============================================================
echo Diagnostic complete!
echo Check results above for any issues
echo ============================================================
echo.

pause
