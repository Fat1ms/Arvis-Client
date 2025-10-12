@echo off
chcp 65001 > nul
echo ═══════════════════════════════════════════════════════════
echo   🧪 Тестирование интеграции с Client API сервера
echo ═══════════════════════════════════════════════════════════
echo.

REM Проверяем виртуальное окружение
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Виртуальное окружение не найдено!
    echo    Запустите сначала INSTALL.bat
    pause
    exit /b 1
)

REM Активируем виртуальное окружение
echo 🔧 Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Проверяем наличие тестового скрипта
if not exist "tests\test_client_api_registration.py" (
    echo ❌ Тестовый скрипт не найден!
    echo    Файл: tests\test_client_api_registration.py
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════
echo   � Проверка тестового пользователя...
echo ═══════════════════════════════════════════════════════════
echo.

REM Создаём тестового пользователя если не существует
python tests\create_test_user.py

echo.
echo ═══════════════════════════════════════════════════════════
echo   �📡 Запуск тестов...
echo ═══════════════════════════════════════════════════════════
echo.

REM Запускаем тесты
python tests\test_client_api_registration.py

REM Сохраняем код возврата
set TEST_RESULT=%ERRORLEVEL%

echo.
echo ═══════════════════════════════════════════════════════════

if %TEST_RESULT% EQU 0 (
    echo   ✅ Все тесты пройдены успешно!
) else (
    echo   ⚠️  Некоторые тесты не прошли
)

echo ═══════════════════════════════════════════════════════════
echo.

REM Деактивируем виртуальное окружение
call venv\Scripts\deactivate.bat 2>nul

echo Нажмите любую клавишу для выхода...
pause > nul

exit /b %TEST_RESULT%
