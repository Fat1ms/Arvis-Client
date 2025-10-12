# 🔄 Client API Integration Guide

## Обзор

В версии **v1.5.1+** Arvis Client интегрирован с новым **Client API** сервера Arvis, который предоставляет упрощённые и оптимизированные эндпоинты для клиентских приложений.

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    Arvis Client                         │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │         HybridAuthManager (слой абстракции)        │ │
│  └────────────┬────────────────────────┬───────────────┘ │
│               │                        │                 │
│  ┌────────────▼────────────┐  ┌────────▼────────────┐  │
│  │   ArvisClientAPI        │  │  LocalAuthManager   │  │
│  │   (новый Client API)    │  │  (локальная БД)     │  │
│  └────────────┬────────────┘  └─────────────────────┘  │
└───────────────┼─────────────────────────────────────────┘
                │
                │ HTTP/JSON (JWT tokens)
                ▼
┌─────────────────────────────────────────────────────────┐
│                    Arvis Server                         │
│                                                           │
│  /api/client/*     - Client API (для приложений)        │
│  /api/*            - Admin API (для управления)         │
└─────────────────────────────────────────────────────────┘
```

## Новые компоненты

### 1. `ArvisClientAPI` (`utils/security/client_api.py`)

Основной клиент для работы с Client API сервера.

**Основные методы**:

```python
from utils.security.client_api import ArvisClientAPI

# Создание клиента
client = ArvisClientAPI("http://server:8000", timeout=10)

# Проверка сервера
server_info = client.get_server_info()
compatible = client.check_server_compatibility()

# Аутентификация
result = client.login("username", "password")
if result["success"]:
    token = result["token"]
    user = result["user"]
    permissions = result["permissions"]

# Регистрация
result = client.register("username", "email@example.com", "password")

# Работа с профилем
profile = client.get_profile()
client.update_profile(full_name="New Name", email="new@email.com")
client.change_password("old_pass", "new_pass")

# Проверка разрешений
permissions = client.get_my_permissions()
has_perm = client.has_permission("chat.use")
check = client.check_permissions(["module.weather", "system.shutdown"])

# Валидация токена
validation = client.validate_token()
if validation["valid"]:
    print("Token is valid")
```

### 2. Обновлённый `HybridAuthManager`

`HybridAuthManager` теперь автоматически использует `ArvisClientAPI` для работы с удалённым сервером:

```python
from utils.security.hybrid_auth import HybridAuthManager
from config.config import Config

config = Config()
auth = HybridAuthManager(config, use_remote=True)

# Аутентификация (автоматически пробует Client API → fallback на локальную БД)
success, error, user = auth.authenticate("username", "password")

if success:
    print(f"Logged in as: {user.username}")
    print(f"Role: {user.role.name}")
```

## Эндпоинты Client API

### Информация о сервере

```http
GET /api/client/server-info
```

**Ответ**:
```json
{
  "server_version": "1.0.0",
  "api_version": "1.0",
  "compatible": true,
  "server_time": "2025-01-08T12:00:00"
}
```

### Аутентификация

#### Вход
```http
POST /api/client/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}
```

**Ответ**:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "123",
    "username": "admin",
    "email": "admin@arvis.ai",
    "full_name": "Administrator",
    "role": "admin",
    "is_active": true
  },
  "permissions": ["chat.use", "module.*", "admin.*"]
}
```

#### Регистрация
```http
POST /api/client/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "New User"
}
```

#### Проверка токена
```http
GET /api/client/validate-token
Authorization: Bearer <token>
```

**Ответ**:
```json
{
  "valid": true,
  "user": { ... },
  "expires_at": "2025-01-08T13:00:00"
}
```

### Профиль пользователя

#### Получение профиля
```http
GET /api/client/profile
Authorization: Bearer <token>
```

#### Обновление профиля
```http
PUT /api/client/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Updated Name",
  "email": "new@email.com"
}
```

#### Смена пароля
```http
PUT /api/client/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

### Разрешения

#### Получение всех разрешений
```http
GET /api/client/my-permissions
Authorization: Bearer <token>
```

**Ответ**:
```json
{
  "permissions": [
    "chat.use",
    "module.weather",
    "module.news",
    "system.lock",
    "admin.users.create"
  ]
}
```

#### Проверка разрешений
```http
POST /api/client/check-permissions
Authorization: Bearer <token>
Content-Type: application/json

{
  "required_permissions": ["module.weather", "module.news"]
}
```

**Ответ**:
```json
{
  "has_permission": true,
  "missing_permissions": []
}
```

## Конфигурация

В `config/config.json` добавлена секция `client_api`:

```json
{
  "security": {
    "auth": {
      "use_remote_server": true,
      "server_url": "http://192.168.0.130:8000"
    }
  },
  "client_api": {
    "enabled": true,
    "prefer_client_api": true,
    "timeout": 10,
    "auto_refresh_token": true,
    "save_token": true,
    "endpoints": {
      "server_info": "/api/client/server-info",
      "login": "/api/client/login",
      "register": "/api/client/register",
      "validate_token": "/api/client/validate-token",
      "profile": "/api/client/profile",
      "change_password": "/api/client/change-password",
      "permissions": "/api/client/my-permissions",
      "check_permissions": "/api/client/check-permissions"
    }
  }
}
```

**Параметры**:
- `enabled`: Включить Client API
- `prefer_client_api`: Использовать Client API вместо Admin API (если доступен)
- `timeout`: Таймаут запросов в секундах
- `auto_refresh_token`: Автоматически обновлять токен при истечении
- `save_token`: Сохранять токен для автоматического входа

## Миграция с Admin API

### Старый способ (Admin API):

```python
from utils.security.remote_auth_client import RemoteAuthClient

client = RemoteAuthClient("http://server:8000")
success, response = client.login("username", "password")

if success:
    token = response.get("access_token")
    user_id = response.get("user_id")
```

### Новый способ (Client API):

```python
from utils.security.client_api import ArvisClientAPI

client = ArvisClientAPI("http://server:8000")
result = client.login("username", "password")

if result["success"]:
    token = result["token"]
    user = result["user"]
    permissions = result["permissions"]
```

## Обработка ошибок

```python
from utils.security.client_api import ArvisClientAPI

client = ArvisClientAPI("http://server:8000")

# Все методы возвращают словарь с результатом
result = client.login("user", "pass")

if result.get("success"):
    # Успешная операция
    print("Success!")
else:
    # Ошибка
    error = result.get("error", "Unknown error")
    print(f"Error: {error}")
    
    # HTTP статус (если есть)
    status = result.get("status_code")
    if status == 401:
        print("Authentication required")
    elif status == 403:
        print("Access denied")
```

## Тестирование

Запустите тестовый скрипт:

```bash
python tests/test_client_api_integration.py
```

**Тесты включают**:
1. ✅ Проверка информации о сервере
2. ✅ Вход в систему
3. ✅ Получение профиля
4. ✅ Проверка разрешений
5. ✅ Валидация токена
6. ✅ Обновление профиля (опционально)
7. ✅ Гибридная аутентификация

## Отличия от Admin API

| Функция | Admin API (`/api/*`) | Client API (`/api/client/*`) |
|---------|---------------------|------------------------------|
| **Аутентификация** | `/api/auth/login` | `/api/client/login` |
| **Регистрация** | ❌ Нет | ✅ `/api/client/register` |
| **Профиль** | `/api/auth/me` | ✅ `/api/client/profile` |
| **Смена пароля** | ❌ Нет | ✅ `/api/client/change-password` |
| **Разрешения** | `/api/auth/check-permission` | ✅ `/api/client/my-permissions` |
| **Управление пользователями** | ✅ `/api/users/*` | ❌ Нет (только admin) |
| **Токены** | JWT (60 мин) | JWT (60 мин) |
| **Требует прав** | Admin для большинства | User для всех |

## Преимущества Client API

1. **🎯 Специализация**: Эндпоинты оптимизированы для клиентских приложений
2. **🔒 Безопасность**: Меньше административных эндпоинтов доступно клиенту
3. **📦 Полнота**: Включает все необходимые операции (профиль, регистрация, разрешения)
4. **🚀 Производительность**: Меньше данных передаётся по сети
5. **📚 Документация**: Специализированная документация для разработчиков

## Fallback на локальную БД

`HybridAuthManager` автоматически переключается на локальную БД если:
- ❌ Сервер недоступен
- ❌ Сервер не совместим
- ❌ Ошибка сети
- ❌ Таймаут запроса

**Пример работы**:
```
1. Попытка Client API → ❌ Сервер недоступен
2. Fallback → ✅ Локальная БД (data/users.db)
3. Пользователь авторизован локально
```

## Логирование

Все операции Client API логируются:

```log
[ArvisClientAPI] ✓ Server info: v1.0.0 (compatible: True)
[ArvisClientAPI] ✓ Login successful: admin (role: admin)
[ArvisClientAPI] ✓ Retrieved 15 permissions
[ArvisClientAPI] ✗ Login failed: Invalid credentials
```

**Файл логов**: `logs/arvis_*.log`

## Следующие шаги

1. ✅ **Базовая интеграция** — Client API подключен
2. 🔄 **2FA поддержка** — Добавить поддержку двухфакторной аутентификации через Client API
3. 🔄 **Автообновление токенов** — Реализовать refresh token механизм
4. 🔄 **Оффлайн кеширование** — Сохранять данные профиля локально
5. 🔄 **Синхронизация** — Синхронизировать настройки между устройствами

---

**Версия**: 1.0  
**Дата**: 08.01.2025  
**Статус**: ✅ Готово к использованию
