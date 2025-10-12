@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     ARVIS CLIENT - ТЕСТ ПОДКЛЮЧЕНИЯ К СЕРВЕРУ             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📡 Проверка подключения к Arvis Server...
echo.

REM Получение настроек из config.json
echo [1/5] Чтение конфигурации...
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"\"server_url\"" config\config.json') do set "SERVER_URL=%%~a"
set "SERVER_URL=%SERVER_URL:"=%"
echo     Адрес сервера: %SERVER_URL%
echo.

REM Извлечение хоста и порта
for /f "tokens=2 delims=/" %%a in ("%SERVER_URL%") do set "SERVER_HOST_PORT=%%a"
for /f "tokens=1 delims=:" %%a in ("%SERVER_HOST_PORT%") do set "SERVER_HOST=%%a"
for /f "tokens=2 delims=:" %%a in ("%SERVER_HOST_PORT%") do set "SERVER_PORT=%%a"
if not defined SERVER_PORT set SERVER_PORT=8000
echo     Хост: %SERVER_HOST%
echo     Порт: %SERVER_PORT%
echo.

REM Тест 1: Ping
echo [2/5] Ping хоста...
ping -n 2 %SERVER_HOST% >nul 2>&1
if %errorlevel%==0 (
    echo     ✅ Хост доступен
) else (
    echo     ❌ Хост недоступен ^(сеть не работает^)
    goto :error
)
echo.

REM Тест 2: Telnet порта (через PowerShell)
echo [3/5] Проверка порта %SERVER_PORT%...
powershell -Command "try { $client = New-Object System.Net.Sockets.TcpClient('%SERVER_HOST%', %SERVER_PORT%); $client.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel%==0 (
    echo     ✅ Порт %SERVER_PORT% открыт
) else (
    echo     ❌ Порт %SERVER_PORT% закрыт ^(firewall или сервер не запущен^)
    goto :error
)
echo.

REM Тест 3: HTTP запрос /health
echo [4/5] Проверка API endpoint /health...
powershell -Command "try { $response = Invoke-WebRequest -Uri '%SERVER_URL%/health' -Method Get -TimeoutSec 5 -UseBasicParsing; Write-Host $response.Content; exit 0 } catch { Write-Host 'Ошибка:' $_.Exception.Message; exit 1 }"
if %errorlevel%==0 (
    echo     ✅ Сервер отвечает
) else (
    echo     ❌ Сервер не отвечает
    goto :error
)
echo.

REM Тест 4: Client API /server-info
echo [5/5] Проверка Client API /server-info...
powershell -Command "try { $response = Invoke-WebRequest -Uri '%SERVER_URL%/api/client/server-info' -Method Get -TimeoutSec 5 -UseBasicParsing; Write-Host $response.Content; exit 0 } catch { Write-Host 'Ошибка:' $_.Exception.Message; exit 1 }"
if %errorlevel%==0 (
    echo     ✅ Client API доступен
) else (
    echo     ⚠️ Client API недоступен ^(может быть старая версия сервера^)
)
echo.

echo ╔════════════════════════════════════════════════════════════╗
echo ║                     ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Сервер доступен и готов к работе!
echo Можете запускать клиент: LAUNCH.bat
echo.
pause
exit /b 0

:error
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                  ❌ ПОДКЛЮЧЕНИЕ НЕ УДАЛОСЬ                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 🔧 Что делать:
echo.
echo 1. Убедитесь, что команда СЕРВЕРА выполнила инструкции:
echo    - Добавила firewall правило на сервере
echo    - Проверила что netstat показывает 0.0.0.0:8000
echo.
echo 2. Если сервер настроен правильно, попробуйте:
echo    - Отключить firewall на СВОЁМ компьютере временно
echo    - Проверить что вы в одной сети с сервером
echo.
echo 3. Для диагностики отправьте команде сервера:
echo    "❌ Клиент не может подключиться. Результаты тестов выше."
echo.
pause
exit /b 1
