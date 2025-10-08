# Руководство по RBAC (Role-Based Access Control)

## Обзор

Система RBAC в Arvis обеспечивает разграничение прав доступа пользователей на основе ролей. Это позволяет контролировать доступ к критическим функциям системы и повышает безопасность.

## Роли

### 🔵 Guest (Гость)

**Уровень доступа:** Минимальный

**Права:**

- ✅ Использование чата
- ✅ Просмотр истории разговоров
- ✅ Модуль погоды
- ✅ Модуль новостей
- ❌ Системные команды
- ❌ Запуск приложений
- ❌ Выполнение скриптов

**Использование:** Демонстрации, гостевой доступ

---

### 🟢 User (Пользователь)

**Уровень доступа:** Стандартный

**Права:**

- ✅ Все права Guest
- ✅ Модуль календаря
- ✅ Модуль поиска
- ✅ Запуск приложений
- ✅ Открытие сайтов
- ✅ Блокировка системы
- ✅ Экспорт истории
- ✅ Выполнение workflows
- ❌ Выключение/перезагрузка
- ❌ Создание workflows
- ❌ Выполнение кода

**Использование:** Обычная повседневная работа

---

### 🟡 Power User (Продвинутый пользователь)

**Уровень доступа:** Расширенный

**Права:**

- ✅ Все права User
- ✅ Перезагрузка системы
- ✅ Запуск скриптов
- ✅ Создание workflows
- ✅ Редактирование workflows
- ✅ Импорт/экспорт истории
- ✅ Удаление истории
- ✅ Редактирование истории
- ✅ Использование API
- ✅ Изменение настроек
- ❌ Выполнение произвольного кода
- ❌ Управление пользователями

**Использование:** Разработка, автоматизация, расширенные функции

---

### 🔴 Admin (Администратор)

**Уровень доступа:** Полный

**Права:**

- ✅ Все права системы без исключений
- ✅ Выполнение кода (с подтверждением)
- ✅ Выключение системы
- ✅ Управление пользователями
- ✅ Управление ролями
- ✅ Управление API
- ✅ Просмотр аудит-лога
- ✅ Расширенные настройки безопасности

**Использование:** Администрирование системы

---

## Установка и настройка

### 1. Первый запуск

При первом запуске Arvis автоматически создаётся пользователь `admin` со случайным паролем.

Пароль сохраняется в файле:

```
data/.admin_password.txt
```

**⚠️ ВАЖНО:** Сохраните этот пароль и удалите файл после входа!

### 2. Вход в систему

```python
from utils.security import get_auth_manager

auth = get_auth_manager()

# Аутентификация
session = auth.authenticate(
    username="admin",
    password="your_password"
)

if session:
    print(f"Logged in successfully! Session: {session.session_id}")
else:
    print("Authentication failed")
```

### 3. Создание пользователей

```python
from utils.security import Role

# Создание обычного пользователя
user = auth.create_user(
    username="john",
    password="SecurePass123!",
    role=Role.USER
)

# Создание power user
power_user = auth.create_user(
    username="alice",
    password="P0werful#Pass",
    role=Role.POWER_USER
)
```

### 4. Проверка прав

```python
from utils.security import get_rbac_manager, Permission

rbac = get_rbac_manager()
rbac.set_role(Role.USER)

# Проверка одного права
if rbac.has_permission(Permission.SYSTEM_APPS):
    print("Can launch applications")

# Проверка нескольких прав
if rbac.has_all_permissions([Permission.CHAT_USE, Permission.MODULE_WEATHER]):
    print("Can use chat and weather module")

# Проверка хотя бы одного права
if rbac.has_any_permission([Permission.CODE_EXECUTE, Permission.SCRIPT_RUN]):
    print("Can execute code or run scripts")
```

## Использование в коде

### Декораторы

#### @require_permission

Требует наличие конкретного права:

```python
from utils.security import require_permission, Permission

@require_permission(Permission.SYSTEM_SHUTDOWN)
def shutdown_system():
    """Выключение системы (только для admin)"""
    os.system("shutdown /s /t 0")
```

#### @require_role

Требует наличие роли или выше:

```python
from utils.security import require_role, Role

@require_role(Role.POWER_USER)
def run_script(script_path):
    """Запуск скрипта (power_user или admin)"""
    subprocess.run(["python", script_path])
```

### Проверка в модулях

Пример интеграции в `SystemControlModule`:

```python
class SystemControlModule:
    def __init__(self, config: Config):
        self.rbac = get_rbac_manager()

    def system_power_command(self, command: str) -> str:
        """Выполнение системных команд питания"""

        if "выключи" in command:
            if not self.rbac.has_permission(Permission.SYSTEM_SHUTDOWN):
                return "❌ Недостаточно прав для выключения системы"
            # Выполнение команды

        elif "перезагрузи" in command:
            if not self.rbac.has_permission(Permission.SYSTEM_RESTART):
                return "❌ Недостаточно прав для перезагрузки системы"
            # Выполнение команды
```

## Аудит действий

Все критические операции логируются в аудит-журнал:

```python
from utils.security import get_audit_logger, AuditEventType, AuditSeverity

audit = get_audit_logger()

# Логирование события
audit.log_event(
    event_type=AuditEventType.SYSTEM_SHUTDOWN,
    action="System shutdown initiated",
    username="admin",
    ip_address="127.0.0.1",
    details={"reason": "manual"},
    success=True,
    severity=AuditSeverity.WARNING
)
```

### Просмотр событий

```python
from datetime import datetime, timedelta

# События за последний день
start = datetime.now() - timedelta(days=1)
events = audit.query_events(
    start_date=start,
    severity=AuditSeverity.WARNING,
    limit=100
)

for event in events:
    print(f"{event.timestamp} - {event.action} by {event.username}")
```

### Статистика пользователя

```python
stats = audit.get_user_activity("admin", days=7)
print(f"Total events: {stats['total_events']}")
print(f"Event types: {stats['event_types']}")
print(f"Failed events: {stats['failed_events']}")
```

## Настройка конфигурации

В `config.json` используйте новую вложенную структуру:

```json
{
    "security": {
        "auth": {
            "enabled": true,
            "require_login": true,
            "session_timeout_minutes": 60,
            "password_policy": {
                "min_length": 12,
                "require_uppercase": true,
                "require_lowercase": true,
                "require_digit": true,
                "require_special": true
            },
            "lockout": {
                "max_attempts": 5,
                "duration_seconds": 600
            },
            "two_factor": {
                "enabled": false,
                "enforced_roles": ["admin", "power_user"],
                "remember_devices_minutes": 10080
            }
        },
        "rbac": {
            "enabled": true,
            "default_role": "user",
            "fallback_role": "guest",
            "enforce_subscriptions": true
        },
        "subscriptions": {
            "enabled": true,
            "default_tier": "standard",
            "guest_tier": "free",
            "tiers": {
                "free": {"title": "Free", "role": "guest"},
                "standard": {"title": "Standard", "role": "user"},
                "pro": {"title": "Pro", "role": "power_user"},
                "enterprise": {"title": "Enterprise", "role": "admin"}
            },
            "user_assignments": {},
            "user_id_assignments": {}
        }
    },
    "audit": {
        "enabled": true,
        "max_log_size": 10485760,
        "max_log_age_days": 90
    }
}
```

## Смена пароля

```python
success = auth.change_password(
    username="john",
    old_password="OldPass123!",
    new_password="NewSecure#Pass456"
)

if success:
    # Логируем событие
    audit.log_event(
        AuditEventType.PASSWORD_CHANGED,
        "Password changed",
        username="john"
    )
```

## Управление сессиями

```python
# Валидация сессии
user = auth.validate_session(session_id)
if user:
    rbac.set_role(user.role)
    # Пользователь авторизован
else:
    # Сессия невалидна

# Выход
auth.logout(session_id)
audit.log_event(
    AuditEventType.LOGOUT,
    "User logged out",
    username=user.username
)
```

## Матрица прав

| Действие | Guest | User | Power User | Admin |
|----------|-------|------|------------|-------|
| Использование чата | ✅ | ✅ | ✅ | ✅ |
| Модуль погоды | ✅ | ✅ | ✅ | ✅ |
| Модуль новостей | ✅ | ✅ | ✅ | ✅ |
| Модуль календаря | ❌ | ✅ | ✅ | ✅ |
| Модуль поиска | ❌ | ✅ | ✅ | ✅ |
| Запуск приложений | ❌ | ✅ | ✅ | ✅ |
| Открытие сайтов | ❌ | ✅ | ✅ | ✅ |
| Блокировка системы | ❌ | ✅ | ✅ | ✅ |
| Перезагрузка | ❌ | ❌ | ✅ | ✅ |
| Выключение | ❌ | ❌ | ❌ | ✅ |
| Запуск скриптов | ❌ | ❌ | ✅ | ✅ |
| Выполнение кода | ❌ | ❌ | ❌ | ✅ |
| Создание workflows | ❌ | ❌ | ✅ | ✅ |
| Экспорт истории | ❌ | ✅ | ✅ | ✅ |
| Импорт истории | ❌ | ❌ | ✅ | ✅ |
| Удаление истории | ❌ | ❌ | ✅ | ✅ |
| GDPR удаление | ❌ | ❌ | ❌ | ✅ |
| Управление API | ❌ | ❌ | ❌ | ✅ |
| Управление пользователями | ❌ | ❌ | ❌ | ✅ |
| Просмотр аудит-лога | ❌ | ❌ | ❌ | ✅ |

## Безопасность

### Хранение паролей

- Используется PBKDF2 с SHA-256 (100,000 итераций)
- Каждый пароль имеет уникальную соль (salt)
- Пароли никогда не хранятся в открытом виде

### Требования к паролю

- Минимум 8 символов (настраивается)
- Минимум 3 из 4 типов символов:
  - Заглавные буквы (A-Z)
  - Строчные буквы (a-z)
  - Цифры (0-9)
  - Спецсимволы (!@#$%^&* и т.д.)

### Защита от брутфорса

- Максимум 5 неудачных попыток (настраивается)
- Блокировка на 5 минут после превышения лимита
- Все попытки логируются в аудит

### Сессии

- Автоматическое истечение через 1 час (настраивается)
- Токены генерируются криптографически безопасным генератором
- Очистка истёкших сессий

## Примеры использования

### Простой чат-бот с RBAC

```python
from utils.security import get_rbac_manager, Permission, Role

def process_command(user_role: Role, command: str):
    rbac = get_rbac_manager()
    rbac.set_role(user_role)

    if "выключи компьютер" in command:
        if rbac.has_permission(Permission.SYSTEM_SHUTDOWN):
            return shutdown_system()
        else:
            return "❌ У вас нет прав для выключения системы"

    elif "запусти скрипт" in command:
        if rbac.has_permission(Permission.SCRIPT_RUN):
            return run_script(command)
        else:
            return "❌ У вас нет прав для запуска скриптов"
```

### API с проверкой прав

```python
from fastapi import FastAPI, Depends, HTTPException
from utils.security import get_auth_manager, get_rbac_manager, Permission

app = FastAPI()

def get_current_user(session_id: str):
    auth = get_auth_manager()
    user = auth.validate_session(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

@app.post("/api/execute")
def execute_code(
    code: str,
    user = Depends(get_current_user)
):
    rbac = get_rbac_manager()
    rbac.set_role(user.role)

    if not rbac.has_permission(Permission.CODE_EXECUTE):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Выполнение кода...
    return {"status": "executed"}
```

## Отладка

### Включение debug режима

```python
from utils.logger import ModuleLogger

logger = ModuleLogger("RBAC")
logger.setLevel("DEBUG")
```

### Просмотр текущих прав

```python
rbac = get_rbac_manager()
current_perms = rbac.get_role_permissions()
print(f"Current role: {rbac.get_role()}")
print(f"Permissions: {[p.value for p in current_perms]}")
```

### Проверка недостающих прав

```python
required = [Permission.CODE_EXECUTE, Permission.SYSTEM_SHUTDOWN]
missing = rbac.get_missing_permissions(required)
if missing:
    print(f"Missing permissions: {[p.value for p in missing]}")
```

## FAQ

**Q: Как сбросить пароль admin?**  
A: Удалите файл `data/.admin_password.txt` и перезапустите Arvis. Будет создан новый пароль.

**Q: Можно ли изменить иерархию ролей?**  
A: Да, отредактируйте `utils/security/rbac.py` и добавьте/измените роли в `Role` enum и `ROLE_PERMISSIONS`.

**Q: Где хранятся данные пользователей?**  
A: В будущей версии - в зашифрованной SQLite БД. Сейчас - в памяти (теряются при перезапуске).

**Q: Как включить 2FA?**  
A: Установите `user.require_2fa = True`. Полная поддержка TOTP будет добавлена в v1.5.0.

**Q: Можно ли отключить RBAC?**  
A: Да, установите `security.rbac.enabled = false` в конфигурации. По умолчанию будет роль `admin`.

---

*Версия документа: 1.0*  
*Последнее обновление: 5 октября 2025*
