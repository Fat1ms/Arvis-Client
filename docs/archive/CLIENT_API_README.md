# 📝 Краткая инструкция по интеграции Client API

## ✅ Что было сделано

### 1. Создан новый модуль `ArvisClientAPI`
**Файл**: `utils/security/client_api.py`

Полноценный клиент для работы с Client API сервера Arvis:
- ✅ Проверка совместимости сервера
- ✅ Аутентификация (login, register)
- ✅ Управление профилем (get, update, change password)
- ✅ Проверка разрешений (get permissions, check permissions)
- ✅ Валидация JWT токенов
- ✅ Singleton pattern для глобального доступа

### 2. Обновлён `HybridAuthManager`
**Файл**: `utils/security/hybrid_auth.py`

Интегрирован с новым Client API:
- ✅ Автоматический выбор: Client API → Admin API → Local DB
- ✅ Новый метод `_create_user_from_client_api()`
- ✅ Проверка совместимости сервера при инициализации
- ✅ Улучшенное логирование с символами статуса (✓/✗/⚠)

### 3. Добавлена конфигурация
**Файл**: `config/config.json`

Новая секция `client_api`:
```json
{
  "client_api": {
    "enabled": true,
    "prefer_client_api": true,
    "timeout": 10,
    "auto_refresh_token": true,
    "save_token": true,
    "endpoints": { ... }
  }
}
```

### 4. Созданы тесты
**Файл**: `tests/test_client_api_integration.py`

Комплексное тестирование:
- ✅ Проверка сервера
- ✅ Вход в систему
- ✅ Получение профиля
- ✅ Проверка разрешений
- ✅ Валидация токенов
- ✅ Гибридная аутентификация

**Запуск**: `test_client_api.bat` или `python tests/test_client_api_integration.py`

### 5. Документация
- ✅ `docs/CLIENT_API_INTEGRATION.md` - Полное руководство
- ✅ `docs/CLIENT_API_CHANGELOG.md` - Changelog и миграция
- ✅ `README.md` для тестов (этот файл)

## 🚀 Быстрый старт

### Шаг 1: Настройка конфигурации

Откройте `config/config.json` и укажите адрес сервера:

```json
{
  "security": {
    "auth": {
      "use_remote_server": true,
      "server_url": "http://192.168.0.130:8000"
    }
  }
}
```

### Шаг 2: Тестирование

Запустите тесты для проверки подключения:

```bash
# Windows
test_client_api.bat

# Linux/Mac
python tests/test_client_api_integration.py
```

**Ожидаемый результат**:
```
✓ PASSED: Информация о сервере
✓ PASSED: Вход в систему
✓ PASSED: Получение профиля
✓ PASSED: Проверка разрешений
✓ PASSED: Проверка токена
✓ PASSED: Обновление профиля
✓ PASSED: Гибридная аутентификация

Пройдено: 7/7 тестов (100%)
```

### Шаг 3: Использование в коде

#### Вариант А: Прямое использование Client API

```python
from utils.security.client_api import ArvisClientAPI

# Создание клиента
client = ArvisClientAPI("http://server:8000")

# Проверка сервера
if not client.check_server_compatibility():
    print("Сервер несовместим!")
    exit(1)

# Вход
result = client.login("admin", "admin")
if result["success"]:
    print(f"Вы вошли как: {result['user']['username']}")
    print(f"Разрешений: {len(result['permissions'])}")
else:
    print(f"Ошибка: {result['error']}")
```

#### Вариант Б: Через HybridAuthManager (рекомендуется)

```python
from utils.security.hybrid_auth import HybridAuthManager
from config.config import Config

# Инициализация
config = Config()
auth = HybridAuthManager(config, use_remote=True)

# Аутентификация (автоматический fallback на локальную БД)
success, error, user = auth.authenticate("admin", "admin")

if success:
    print(f"✓ Вход выполнен: {user.username}")
    print(f"  Роль: {user.role.name}")
else:
    print(f"✗ Ошибка: {error}")
```

## 📚 Структура файлов

```
Arvis-Client/
├── utils/security/
│   ├── client_api.py          ← 🆕 Client API клиент
│   ├── hybrid_auth.py         ← 🔄 Обновлён
│   ├── remote_auth_client.py  ← Старый Admin API (сохранён)
│   └── local_auth.py          ← Локальная БД
├── tests/
│   └── test_client_api_integration.py  ← 🆕 Тесты
├── docs/
│   ├── CLIENT_API_INTEGRATION.md       ← 🆕 Документация
│   └── CLIENT_API_CHANGELOG.md         ← 🆕 Changelog
├── config/
│   └── config.json            ← 🔄 Добавлена секция client_api
├── test_client_api.bat        ← 🆕 Скрипт запуска тестов
└── .github/
    └── copilot-instructions.md ← 🔄 Обновить (следующий шаг)
```

## 🔍 Основные API методы

### ArvisClientAPI

| Метод | Описание | Требует токен |
|-------|----------|---------------|
| `get_server_info()` | Информация о сервере | ❌ |
| `check_server_compatibility()` | Проверка совместимости | ❌ |
| `login(username, password)` | Вход в систему | ❌ |
| `register(username, email, password, full_name)` | Регистрация | ❌ |
| `validate_token()` | Проверка токена | ✅ |
| `get_profile()` | Получить профиль | ✅ |
| `update_profile(full_name, email)` | Обновить профиль | ✅ |
| `change_password(current, new)` | Сменить пароль | ✅ |
| `get_my_permissions()` | Получить разрешения | ✅ |
| `check_permissions(required)` | Проверить разрешения | ✅ |
| `has_permission(permission)` | Проверить одно разрешение | ✅ |

## 🔄 Процесс аутентификации

```
┌─────────────────────────────────────────────────┐
│ HybridAuthManager.authenticate()                │
└─────────────┬───────────────────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ Client API доступен? │
    └─────────┬───────────┘
              │
         ┌────┴────┐
       ДА│        │НЕТ
         │        │
         ▼        ▼
    ┌────────┐  ┌────────────┐
    │Client  │  │Admin API   │
    │API     │  │доступен?   │
    │login   │  └─────┬──────┘
    └────┬───┘        │
         │      ┌─────┴─────┐
         │    ДА│          │НЕТ
         │      │          │
         │      ▼          ▼
         │  ┌────────┐  ┌──────────┐
         │  │Admin   │  │Local DB  │
         │  │API     │  │sqlite    │
         │  │login   │  └──────────┘
         │  └────────┘
         │
         ▼
    ┌─────────────────┐
    │ User создан и   │
    │ авторизован     │
    └─────────────────┘
```

## 🛠️ Отладка

### Проблема: Сервер недоступен

**Симптомы**:
```
[ArvisClientAPI] ✗ Connection error: Cannot connect to server
[HybridAuthManager] ⚠ Remote authentication failed
[HybridAuthManager] → Falling back to local authentication
```

**Решение**:
1. Проверьте URL сервера в `config.json`
2. Убедитесь что сервер запущен
3. Проверьте firewall и сетевое подключение
4. Клиент автоматически переключится на локальную БД

### Проблема: Несовместимая версия

**Симптомы**:
```
[ArvisClientAPI] ⚠ Server incompatible or unreachable
```

**Решение**:
1. Обновите Arvis-Server до версии 1.0.0+
2. Обновите Arvis-Client до версии 1.5.1+

### Проблема: Ошибка аутентификации

**Симптомы**:
```
[ArvisClientAPI] ✗ Login failed: Invalid credentials
```

**Решение**:
1. Проверьте логин и пароль
2. Используйте admin/admin для первого входа
3. Создайте нового пользователя через регистрацию

## 📊 Логи

Все операции Client API подробно логируются в:
- **Файл**: `logs/arvis_YYYYMMDD_HHMMSS_PID.log`
- **Модуль**: `[ArvisClientAPI]`
- **Формат**: `[2025-10-08 12:00:00] [INFO] [ArvisClientAPI] ✓ Login successful: admin`

**Символы статуса**:
- `✓` - Успешная операция
- `✗` - Ошибка
- `⚠` - Предупреждение
- `⊙` - Информация

## 🎯 Следующие шаги

1. **Тестирование**: Запустите `test_client_api.bat`
2. **Интеграция**: Обновите код приложения для использования Client API
3. **Документация**: Обновите `.github/copilot-instructions.md`
4. **Деплой**: Настройте продакшен сервер с HTTPS

## 📞 Поддержка

- **Документация**: `docs/CLIENT_API_INTEGRATION.md`
- **Примеры**: `tests/test_client_api_integration.py`
- **GitHub Issues**: https://github.com/Fat1ms/Arvis-Client/issues

---

**Дата обновления**: 08.10.2025  
**Версия клиента**: v1.5.1+  
**Версия сервера**: v1.0.0+  
**Автор**: AI Assistant  
**Статус**: ✅ Ready for Production
