# 📨 Инструкции для разработчиков сервера Arvis
## Проблема: Клиент не может подключиться к серверу

---

## 📊 Результаты диагностики клиента

✅ **Клиент настроен ПРАВИЛЬНО**:
- URL формируются корректно: `http://192.168.0.130:8000/api/client/register` ✅
- Timeout увеличен до 30 секунд ✅
- HTTP библиотека `requests` работает ✅
- Логирование подробное ✅

❌ **Проблема**: Сервер недоступен на `192.168.0.130:8000`

**Ошибка**:
```
HTTPConnectionPool(host='192.168.0.130', port=8000): Max retries exceeded
Failed to establish a new connection: [WinError 10061] 
Подключение не установлено, т.к. конечный компьютер отверг запрос на подключение
```

---

## 🔍 Что нужно проверить на сервере

### 1️⃣ Сервер запущен?

**Команда** (на компьютере с IP `192.168.0.130`):
```bash
# Linux/Mac
ps aux | grep "python.*main.py"
ps aux | grep uvicorn

# Windows PowerShell
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

**Ожидаемый результат**: Процесс Python с `main.py` или `uvicorn` должен быть в списке.

**Если не запущен** → Запустите сервер:
```bash
cd /path/to/Arvis-Server
python main.py
```

---

### 2️⃣ Сервер слушает правильный адрес?

**Проблема**: Сервер может слушать только `127.0.0.1` (localhost), а не `0.0.0.0` (все интерфейсы).

**Проверка**:
```bash
# Linux/Mac
netstat -tuln | grep 8000
# или
ss -tuln | grep 8000

# Windows
netstat -an | findstr :8000
```

**Правильный результат**:
```
TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING   ✅ (слушает ВСЕ интерфейсы)
```

**Неправильный результат**:
```
TCP    127.0.0.1:8000  0.0.0.0:0    LISTENING   ❌ (слушает только localhost)
```

**Исправление** (в `main.py` сервера):
```python
# ❌ НЕПРАВИЛЬНО
uvicorn.run(app, host="127.0.0.1", port=8000)

# ✅ ПРАВИЛЬНО
uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### 3️⃣ Firewall не блокирует порт 8000?

**Windows Server**:
```powershell
# Проверить правила firewall
netsh advfirewall firewall show rule name=all | findstr :8000

# Добавить правило если нужно
netsh advfirewall firewall add rule name="Arvis Server" dir=in action=allow protocol=TCP localport=8000
```

**Linux Server**:
```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 8000/tcp

# CentOS/RHEL
sudo firewall-cmd --list-ports
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

---

### 4️⃣ Эндпоинт `/api/client/register` доступен?

**Проверка с самого сервера**:
```bash
# На сервере (192.168.0.130)
curl http://localhost:8000/health
curl -X OPTIONS http://localhost:8000/api/client/register
```

**Ожидаемый результат**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-09T15:30:00",
  "version": "1.0.0"
}
```

**Если получили ошибку 404** → Проверьте маршруты в `api/client.py`.

---

### 5️⃣ CORS настроен правильно?

**Файл**: `main.py` (FastAPI приложение)

**Должно быть**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или конкретные IP: ["http://192.168.0.100"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Проверка**:
```bash
curl -X OPTIONS http://192.168.0.130:8000/api/client/register \
  -H "Origin: http://192.168.0.100" \
  -H "Access-Control-Request-Method: POST"
```

**Ожидаемый заголовок в ответе**:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, OPTIONS
```

---

### 6️⃣ Логи сервера показывают ошибки?

**Где найти логи**:
- Консоль, где запущен сервер
- Файл `logs/server.log` (если настроено)
- Системный журнал (journalctl, Event Viewer)

**Что искать**:
- ❌ Ошибки запуска (module not found, import errors)
- ❌ Database connection errors
- ❌ Port already in use
- ❌ Permission denied

---

## 🧪 Тесты для проверки

### Тест 1: Проверка доступности с клиента

**На клиенте** (IP `192.168.0.XXX`):
```powershell
# PowerShell
Test-NetConnection -ComputerName 192.168.0.130 -Port 8000

# Или через curl
curl http://192.168.0.130:8000/health
```

**Ожидаемый результат**:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0"
}
```

### Тест 2: Проверка эндпоинта регистрации

**На клиенте**:
```powershell
curl -X POST http://192.168.0.130:8000/api/client/register `
  -H "Content-Type: application/json" `
  -d '{\"username\":\"test123\",\"email\":\"test@test.com\",\"password\":\"TestPass123!\"}'
```

**Ожидаемый статус**: `200 OK` или `400 Bad Request` (если пользователь существует)

**НЕ ожидается**: `Connection refused`, `Timeout`, `404 Not Found`

### Тест 3: Симулятор в браузере

Откройте в браузере:
```
http://192.168.0.130:8000/static/client_simulator.html
```

Заполните форму и нажмите "Simulate Client Registration".

**Если работает** → Проблема в клиенте  
**Если не работает** → Проблема на сервере

---

## 📋 Чек-лист перед тестированием клиента

Пройдите по всем пунктам:

- [ ] ✅ Сервер запущен (процесс Python активен)
- [ ] ✅ Сервер слушает `0.0.0.0:8000` (не `127.0.0.1`)
- [ ] ✅ Порт 8000 открыт в firewall
- [ ] ✅ Эндпоинт `/health` отвечает HTTP 200
- [ ] ✅ Эндпоинт `/api/client/register` доступен (OPTIONS)
- [ ] ✅ CORS настроен (`allow_origins=["*"]`)
- [ ] ✅ Логи сервера не показывают ошибок
- [ ] ✅ Симулятор в браузере работает
- [ ] ✅ `curl` с клиента доходит до сервера

**Если все пункты ✅** → Сообщите разработчикам клиента, запустите тест:
```powershell
# На клиенте
cd d:\AI\Arvis-Client
test_client_api.bat
```

---

## 🔧 Типичные проблемы и решения

### Проблема 1: "Connection refused"
**Причина**: Сервер не запущен или слушает неправильный адрес  
**Решение**: Запустите с `host="0.0.0.0"`

### Проблема 2: "Timeout"
**Причина**: Firewall блокирует порт  
**Решение**: Откройте порт 8000 в firewall

### Проблема 3: "404 Not Found" на `/api/client/register`
**Причина**: Эндпоинт не зарегистрирован в FastAPI  
**Решение**: Проверьте `api/client.py` и `main.py` (app.include_router)

### Проблема 4: "CORS policy" в браузере
**Причина**: CORS не настроен  
**Решение**: Добавьте CORSMiddleware с `allow_origins=["*"]`

### Проблема 5: "Port already in use"
**Причина**: Другой процесс занял порт 8000  
**Решение**: Завершите старый процесс или используйте другой порт

---

## 📞 Связь с разработчиками клиента

**После исправления** отправьте подтверждение:

```
✅ Сервер запущен на: 192.168.0.130:8000
✅ Health check работает: curl http://192.168.0.130:8000/health
✅ Register endpoint доступен: curl -X OPTIONS http://192.168.0.130:8000/api/client/register
✅ Логи: [прикрепить последние 20 строк]
```

**Разработчики клиента** запустят тест и сообщат о результатах.

---

## 📚 Дополнительные ресурсы

1. **FastAPI CORS**: https://fastapi.tiangolo.com/tutorial/cors/
2. **Uvicorn deployment**: https://www.uvicorn.org/deployment/
3. **Firewall Windows**: https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/
4. **Firewall Linux**: https://ubuntu.com/server/docs/firewalls

---

## ✅ Подтверждение готовности

Когда всё исправлено, проверьте командой с **другого компьютера** в сети:

```bash
curl -v http://192.168.0.130:8000/health
```

**Ожидаемый вывод**:
```
* Connected to 192.168.0.130 (192.168.0.130) port 8000
> GET /health HTTP/1.1
> Host: 192.168.0.130:8000
>
< HTTP/1.1 200 OK
< content-type: application/json
{
  "status": "healthy",
  ...
}
```

**Если видите это** → ✅ Сервер готов к работе с клиентом!

---

**Успехов в отладке!** 🚀
