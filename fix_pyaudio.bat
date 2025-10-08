@echo off
chcp 65001 > nul
title Исправление проблемы PyAudio (Python 3.13)

echo ========================================
echo   ДИАГНОСТИКА ПРОБЛЕМЫ PYAUDIO
echo ========================================
echo.

REM Проверка Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден!
    echo Установите Python 3.11 или 3.12: https://python.org
    pause
    exit /b 1
)

echo ✅ Python найден
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Версия: %PYTHON_VERSION%
echo.

REM Проверка на Python 3.13
echo %PYTHON_VERSION% | findstr /C:"3.13" >nul
if %errorlevel% equ 0 (
    echo ⚠️  Обнаружен Python 3.13 - НЕСОВМЕСТИМ с PyAudio!
    echo.
    echo 📋 Доступные решения:
    echo.
    echo 1. РЕКОМЕНДУЕТСЯ: Переустановить Python 3.11 или 3.12
    echo 2. Установить предкомпилированный PyAudio wheel
    echo 3. Работать без PyAudio (только текстовый режим)
    echo.
    set /p CHOICE="Выберите вариант (1-3): "

    if "%CHOICE%"=="1" (
        echo.
        echo 📖 Инструкция:
        echo 1. Удалите Python 3.13 через "Установка и удаление программ"
        echo 2. Скачайте Python 3.11.9 или 3.12.x с https://www.python.org/downloads/
        echo 3. Удалите папку venv: rmdir /s /q venv
        echo 4. Запустите setup_arvis.bat заново
        echo.
        echo 🔗 Подробнее: docs\PYTHON_313_COMPATIBILITY.md
        start https://www.python.org/downloads/
        pause
        exit /b 0
    )

    if "%CHOICE%"=="2" (
        echo.
        echo 📖 Инструкция по установке wheel:
        echo 1. Скачайте PyAudio wheel с:
        echo    https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
        echo 2. Выберите файл: PyAudio-0.2.14-cp313-cp313-win_amd64.whl
        echo 3. Установите: pip install PyAudio-0.2.14-cp313-cp313-win_amd64.whl
        echo.
        echo 🔗 Подробнее: docs\PYAUDIO_PYTHON313_INSTALL.md
        start https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
        pause
        exit /b 0
    )

    if "%CHOICE%"=="3" (
        echo.
        echo 📖 Работа без PyAudio:
        echo.
        echo ✅ Будет работать:
        echo    - Текстовый ввод в чат
        echo    - LLM (Ollama)
        echo    - TTS (озвучка ответов)
        echo    - Все модули (погода, новости и т.д.)
        echo.
        echo ❌ НЕ будет работать:
        echo    - Голосовой ввод (STT)
        echo    - Wake word detection
        echo.
        echo Отключите голосовые функции в config.json:
        echo.
        echo   "stt": {
        echo     "enabled": false
        echo   },
        echo   "wake_word": {
        echo     "enabled": false
        echo   }
        echo.
        echo 🔗 Подробнее: docs\PYTHON_313_COMPATIBILITY.md
        pause
        exit /b 0
    )

    echo ❌ Неверный выбор
    pause
    exit /b 1
)

REM Проверка для Python 3.11/3.12
echo %PYTHON_VERSION% | findstr /C:"3.11 3.12" >nul
if %errorlevel% equ 0 (
    echo ✅ Python %PYTHON_VERSION% совместим с Arvis!
    echo.
    echo Попытка установки PyAudio...

    if not exist "venv" (
        echo ❌ Виртуальное окружение не найдено!
        echo Запустите сначала setup_arvis.bat
        pause
        exit /b 1
    )

    call venv\Scripts\activate.bat

    echo Установка PyAudio...
    pip install pyaudio==0.2.13

    if %errorlevel% equ 0 (
        echo ✅ PyAudio установлен успешно!
        echo.
        echo Проверка установки...
        python -c "import pyaudio; print('✅ PyAudio работает!')"
        if %errorlevel% equ 0 (
            echo.
            echo 🎉 Всё готово! Можете запускать Arvis.
        ) else (
            echo ❌ PyAudio не импортируется
            echo Возможно, требуется Visual C++ Redistributable
            echo Скачайте: https://aka.ms/vs/17/release/vc_redist.x64.exe
        )
    ) else (
        echo ❌ Ошибка установки PyAudio
        echo.
        echo Возможные причины:
        echo 1. Не установлен Visual C++ Build Tools
        echo 2. Проблемы с pip
        echo.
        echo Попробуйте:
        echo    pip install --upgrade pip
        echo    pip install pyaudio==0.2.13
    )

    pause
    exit /b 0
)

REM Другие версии Python
echo ⚠️  Python %PYTHON_VERSION% может быть несовместим
echo Рекомендуется Python 3.11 или 3.12
echo.
pause
exit /b 1
