# 🛡️ Security Audit Report - Arvis v1.5.0-beta

**Дата аудита:** 6 октября 2025  
**Версия:** v1.5.0-beta (предрелиз)  
**Статус:** 🟡 Требует исправлений перед релизом

---

## 📊 Executive Summary

### Общая оценка безопасности: B+ (85/100)

| Категория | Оценка | Комментарий |
|-----------|--------|-------------|
| Аутентификация | A | Надёжное хеширование, 2FA реализован |
| Авторизация (RBAC) | B | Матрица прав хорошая, но найден баг с check_permission |
| Защита данных | B+ | Хорошее шифрование, но нужна защита БД |
| Логирование | C+ | Аудит есть, но возможны утечки в логах |
| Секреты | B | .env используется, но нужен secret scanning |
| Код | B | Pre-commit настроен, но нужен security scanning |

### Критические находки

1. 🔴 **CRITICAL**: Метод `check_permission()` не существует в RBACManager → **ИСПРАВЛЕНО**
2. 🔴 **CRITICAL**: Отсутствует secret scanning в pre-commit → **В РАБОТЕ**
3. 🟡 **HIGH**: База данных не зашифрована на диске → **ЗАПЛАНИРОВАНО**
4. 🟡 **HIGH**: Возможны утечки чувствительных данных в логах → **ТРЕБУЕТ АУДИТА**

---

## 1. Аутентификация и управление пользователями

### ✅ Что работает хорошо

1. **Хеширование паролей:** PBKDF2 + SHA-256 (600,000 итераций)

   ```python
   # utils/security/auth.py
   hashlib.pbkdf2_hmac('sha256', password.encode(), salt_bytes, 600_000)
   ```

2. **2FA (TOTP):**
   - Стандартный протокол (RFC 6238)
   - QR-коды для easy setup
   - Backup коды (хешированные)
   - Шифрование TOTP секретов

3. **Защита от brute-force:**
   - Rate limiting (5 попыток)
   - Lockout на 5 минут
   - Логирование неудачных попыток

4. **Сессии:**
   - Уникальные session_id (cryptographically secure)
   - Тайм-ауты (1 час по умолчанию)
   - Привязка к IP/User-Agent (опционально)

### 🚨 Проблемы и рекомендации

#### 1.1 Первый пароль администратора

**Проблема:** Пароль админа генерируется и сохраняется в `data/.admin_password.txt`

**Риск:** 🟡 MEDIUM

- Файл на диске в plaintext
- Может быть прочитан любым процессом пользователя
- Не требует обязательной смены при первом входе

**Рекомендации:**

1. Удалять файл после первого входа
2. Требовать смену пароля при первом логине
3. Или: не создавать админа автоматически, а через CLI tool

```python
# Пример: create_admin.py с требованием смены
def create_admin():
    password = generate_secure_password()
    print(f"Temporary password: {password}")
    print("⚠️ You MUST change this password on first login!")

    auth.create_user("admin", password, Role.ADMIN)
    auth.mark_password_temporary("admin")  # Требовать смену
```

#### 1.2 Хранение TOTP секретов

**Текущее состояние:** Секреты шифруются перед сохранением в БД

**Риск:** 🟢 LOW (но можно улучшить)

**Рекомендации:**

1. Использовать OS keyring для ключа шифрования
2. Ротация ключей шифрования
3. Hardware security module (HSM) для enterprise версии

#### 1.3 Валидация паролей

**Текущие требования:**

- Минимум 8 символов
- Проверка надёжности через `validate_password_strength()`

**Рекомендации:**

- ✅ Минимум 12 символов для новых паролей
- ✅ Требовать upper/lower/digit/special chars
- ✅ Проверка против списка слабых паролей (haveibeenpwned)
- ✅ Запрет повторного использования последних 5 паролей

---

## 2. Авторизация (RBAC)

### ✅ Что работает хорошо

1. **Четыре роли с ясной иерархией:**
   - GUEST → USER → POWER_USER → ADMIN

2. **Детализированные права (Permission enum):**
   - 30+ разрешений
   - Логичная группировка (chat, module, system, security)

3. **Матрица прав ROLE_PERMISSIONS:**
   - Ясное определение прав для каждой роли
   - Admin имеет все права

### 🚨 Проблемы и рекомендации

#### 2.1 🔴 CRITICAL: Баг с check_permission()

**Проблема:** В `main_window.py:833` вызывается `rbac.check_permission(user_id, permission)`, но метод не существует

**Исправление:** **✅ ИСПРАВЛЕНО**

```python
# Добавлен метод в RBACManager:
def check_permission(self, user_id: Optional[str], permission: Permission) -> bool:
    """Проверить наличие права у конкретного пользователя"""
    if user_id and user_id != self.current_user:
        return False
    return self.has_permission(permission)
```

#### 2.2 Недостаточные проверки RBAC

**Проблема:** Не все критичные операции проверяют права

**Требует аудита:**

1. `SystemControlModule` - все команды (shutdown, restart, etc.)
2. `WorkflowModule` - создание vs выполнение
3. `HistoryManager` - экспорт vs удаление vs редактирование
4. `SettingsDialog` - просмотр vs редактирование разных секций

**Пример добавления проверки:**

```python
# modules/system_control.py
def execute_shutdown(self):
    rbac = get_rbac_manager()
    if not rbac.has_permission(Permission.SYSTEM_SHUTDOWN):
        raise PermissionError("Shutdown not allowed for your role")
    # ... выполнение команды
```

#### 2.3 Разделение прав управления пользователями

**Текущее состояние:**

- `Permission.USER_VIEW` - просмотр
- `Permission.USER_CREATE` - создание
- `Permission.USER_EDIT` - редактирование
- `Permission.USER_DELETE` - удаление
- `Permission.USER_ROLE_MANAGE` - управление ролями

**Рекомендации:** ✅ Хорошо разделено, но проверить применение

**Action items:**

- [ ] Убедиться, что UserManagementPanel проверяет каждое право перед действием
- [ ] Добавить Permission.USER_DEACTIVATE отдельно от DELETE

---

## 3. Защита данных

### ✅ Что работает хорошо

1. **Пароли:** Хешированы с солью
2. **TOTP секреты:** Зашифрованы
3. **Backup коды:** Хешированы (нельзя восстановить)
4. **Session tokens:** Cryptographically secure

### 🚨 Проблемы и рекомендации

#### 3.1 🟡 HIGH: База данных не зашифрована

**Проблема:** `data/users.db` хранится в plaintext на диске

**Риск:**

- Кто угодно с доступом к файловой системе может скопировать БД
- Хотя пароли хешированы, другие данные (usernames, TOTP secrets) доступны

**Рекомендации:**

1. SQLCipher для шифрования БД
2. Ключ хранить в OS keyring или .env
3. Права доступа к файлу (chmod 600 на Unix, hidden на Windows)

**Пример реализации:**

```python
# utils/security/storage.py
from sqlcipher3 import dbapi2 as sqlite3

def get_connection():
    conn = sqlite3.connect('data/users.db')
    # Ключ из environment variable или keyring
    key = os.getenv('DB_ENCRYPTION_KEY')
    conn.execute(f"PRAGMA key = '{key}'")
    return conn
```

#### 3.2 🟡 MEDIUM: Права доступа к файлам

**Текущее состояние:** Нет явной установки прав доступа

**Рекомендации:**

```python
# При создании файлов с чувствительными данными:
import os
import stat

def create_secure_file(path: str, content: str):
    with open(path, 'w') as f:
        f.write(content)
    # Только владелец может читать/писать
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
```

#### 3.3 🟢 LOW: Temporary files cleanup

**Текущее состояние:** `utils/housekeeping.py` реализован

**Рекомендации:**

- ✅ Убедиться, что housekeeping запускается при старте и каждые N часов
- ✅ Очищать temp/ при выходе пользователя
- ✅ Secure deletion для чувствительных файлов (перезапись перед удалением)

---

## 4. Логирование и аудит

### ✅ Что работает хорошо

1. **Audit logging реализован** (`utils/security/audit.py`)
2. **JSONL формат** для легкого парсинга
3. **Ротация логов** (10 MB, 90 дней TTL)
4. **Structured logging** (timestamp, user_id, action, details)

### 🚨 Проблемы и рекомендации

#### 4.1 🟡 HIGH: Возможны утечки в логах

**Проблема:** Нет централизованной санитизации логов

**Риск:** Пароли, токены, API ключи могут попасть в логи через debug/info сообщения

**Action items:**

1. Аудит всех `logger.info()`, `logger.debug()` вызовов
2. Поиск паттернов: `password`, `token`, `secret`, `key`, `api_key`
3. Создать `LogSanitizer` для автоматической фильтрации

**Пример:**

```python
# utils/log_sanitizer.py
import re

SENSITIVE_PATTERNS = [
    (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', re.I), 'password=***'),
    (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', re.I), 'token=***'),
    (re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'}\s]+)', re.I), 'api_key=***'),
    (re.compile(r'(sk-[a-zA-Z0-9]{32,})', re.I), 'sk-***'),  # OpenAI-like keys
]

def sanitize_log(message: str) -> str:
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message
```

**Применение:**

```python
# utils/logger.py
class ModuleLogger:
    def info(self, message):
        sanitized = sanitize_log(str(message))
        self._logger.info(sanitized)
```

#### 4.2 🟢 MEDIUM: Централизованный мониторинг

**Рекомендации для enterprise:**

- Отправка логов на SIEM (Splunk, ELK)
- Алерты на подозрительную активность
- Dashboard для админов

---

## 5. Секреты и конфигурация

### ✅ Что работает хорошо

1. **.env для секретов** (не в git)
2. **.gitignore правильно настроен**
3. **config.json для несекретных настроек**

### 🚨 Проблемы и рекомендации

#### 5.1 🔴 CRITICAL: Отсутствует secret scanning

**Проблема:** Нет автоматической проверки на утечку секретов в коде

**Решение:** Добавить в `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
      exclude: package-lock.json
```

**Инициализация:**

```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
git add .secrets.baseline
pre-commit run detect-secrets --all-files
```

#### 5.2 🟡 MEDIUM: Проверка наличия обязательных секретов

**Рекомендация:** Валидация при старте

```python
# config/config.py
REQUIRED_SECRETS = [
    'OLLAMA_API_KEY',  # если используется
    'GOOGLE_API_KEY',  # для поиска
    'WEATHER_API_KEY',
    # ... другие
]

def validate_secrets():
    missing = [key for key in REQUIRED_SECRETS if not os.getenv(key)]
    if missing:
        raise ValueError(f"Missing required secrets: {missing}")
```

#### 5.3 🟢 LOW: Secret rotation

**Рекомендация:** Документировать процесс ротации API ключей

- Как обновить ключи без даунтайма
- Как уведомить пользователей
- Как отозвать старые ключи

---

## 6. Качество кода и безопасность разработки

### ✅ Что работает хорошо

1. **Pre-commit hooks настроены**
2. **Black + isort + flake8 для консистентности**
3. **detect-private-key хук активен**

### 🚨 Проблемы и рекомендации

#### 6.1 🔴 HIGH: Отсутствует security linting

**Решение:** Добавить Bandit в pre-commit

```yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.5
  hooks:
    - id: bandit
      args: ['-r', 'src/', 'utils/', 'modules/', '-ll']
      exclude: tests/
```

**Что проверяет Bandit:**

- Hardcoded passwords
- SQL injection
- Shell injection
- Insecure random
- Unsafe YAML loading
- Assert statements
- Exec/eval usage

#### 6.2 🟡 MEDIUM: Dependency scanning

**Рекомендация:** Регулярно проверять зависимости

```bash
# Проверка известных уязвимостей
pip install safety
safety check

# Или через GitHub Dependabot (рекомендуется)
```

**Настроить `.github/dependabot.yml`:**

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

#### 6.3 🟢 LOW: Code coverage

**Текущее покрытие:** Неизвестно

**Рекомендация:**

```bash
pytest --cov=src --cov=utils --cov=modules --cov-report=html
```

**Цель:** 70%+ для критических модулей (security, auth, rbac)

---

## 7. Специфичные угрозы

### 7.1 SQL Injection

**Статус:** 🟢 PROTECTED

**Анализ:** Используется SQLite с parameterized queries

```python
# utils/security/storage.py
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

**Рекомендация:** ✅ Хорошая практика, продолжать так же

---

### 7.2 Command Injection

**Статус:** 🟡 POTENTIAL RISK

**Проблема:** `SystemControlModule` выполняет системные команды

**Анализ:**

```python
# modules/system_control.py
os.system(f"start {app_path}")  # Потенциально опасно!
```

**Рекомендация:** Использовать `subprocess` с shell=False

```python
import subprocess
subprocess.Popen([app_path], shell=False)
```

**Action items:**

- [ ] Аудит всех вызовов `os.system()`, `os.popen()`, `subprocess.call()`
- [ ] Валидация всех путей к приложениям
- [ ] Whitelist разрешённых команд
- [ ] Санитизация всех пользовательских вводов

---

### 7.3 Path Traversal

**Статус:** 🟡 POTENTIAL RISK

**Проблема:** Работа с файлами по путям из конфигурации или пользовательского ввода

**Рекомендация:** Всегда нормализовать и валидировать пути

```python
import os
from pathlib import Path

def safe_path(base_dir: str, user_path: str) -> Path:
    """Безопасное объединение путей без path traversal"""
    full_path = (Path(base_dir) / user_path).resolve()
    base = Path(base_dir).resolve()

    if not full_path.is_relative_to(base):
        raise ValueError("Path traversal detected!")

    return full_path
```

---

### 7.4 XSS / Code Injection в UI

**Статус:** 🟢 LOW RISK (desktop app)

**Анализ:** Qt apps менее подвержены XSS чем web, но:

- Если HTML рендерится в QTextBrowser/QLabel
- Если используется QWebEngineView

**Рекомендация:** Экранировать все пользовательские inputs перед отображением

---

## 8. Compliance и стандарты

### 8.1 GDPR (если применимо)

**Требования:**

- ✅ Право на удаление данных (реализовано через history.gdpr permission)
- ✅ Право на экспорт данных (реализовано)
- ⏳ Согласие на обработку данных (не реализовано для гостей)
- ⏳ Уведомления о breach (процедура не документирована)

**Рекомендации:**

1. Добавить GDPR disclaimer при первом запуске
2. Логировать согласия пользователей
3. Документировать процесс data breach response

### 8.2 OWASP Top 10

| Угроза | Статус | Комментарий |
|--------|--------|-------------|
| A01:2021 – Broken Access Control | 🟡 | RBAC реализован, но найден баг (исправлен) |
| A02:2021 – Cryptographic Failures | 🟢 | Хорошее хеширование, но БД не зашифрована |
| A03:2021 – Injection | 🟡 | SQL защищено, но command injection возможен |
| A04:2021 – Insecure Design | 🟢 | Дизайн безопасности хороший |
| A05:2021 – Security Misconfiguration | 🟡 | Нужны security hardening гайды |
| A06:2021 – Vulnerable Components | 🟡 | Нет dependency scanning |
| A07:2021 – Auth Failures | 🟢 | Хорошая защита от brute-force, 2FA |
| A08:2021 – Software/Data Integrity | 🟢 | Code signing желательно добавить |
| A09:2021 – Security Logging Failures | 🟡 | Аудит есть, но возможны утечки в логах |
| A10:2021 – SSRF | 🟢 | Не применимо (desktop app) |

---

## 9. Roadmap исправлений

### Критичные (до релиза беты)

- [x] Исправить баг с `check_permission()` в RBACManager
- [ ] Добавить detect-secrets в pre-commit
- [ ] Добавить Bandit security linting
- [ ] Аудит логов на утечки чувствительных данных
- [ ] Добавить валидацию системных команд
- [ ] Документировать security best practices

### Высокий приоритет (v1.5.1)

- [ ] Зашифровать базу данных (SQLCipher)
- [ ] Требовать смену пароля админа при первом входе
- [ ] Добавить LogSanitizer для автоматической фильтрации
- [ ] Настроить Dependabot для dependency scanning
- [ ] Увеличить требования к паролям (12+ символов)

### Средний приоритет (v1.6.0)

- [ ] OS Keyring integration для секретов
- [ ] GDPR compliance improvements
- [ ] Security hardening guide
- [ ] Penetration testing
- [ ] Bug bounty program

### Низкий приоритет (будущие версии)

- [ ] HSM support для enterprise
- [ ] SIEM integration
- [ ] Code signing для релизов
- [ ] Security audit by third party

---

## 10. Выводы и рекомендации

### Сильные стороны

1. ✅ Надёжная система аутентификации
2. ✅ 2FA реализован правильно
3. ✅ RBAC с детализированными правами
4. ✅ Хорошее хеширование паролей
5. ✅ Аудит логирование

### Слабые места

1. 🔴 Отсутствие security scanning в CI/CD
2. 🟡 База данных не зашифрована
3. 🟡 Возможны утечки в логах
4. 🟡 Command injection риски
5. 🟡 Нет dependency scanning

### Общая рекомендация

**Можно релизить бета-версию** после исправления критических находок:

1. Баг с check_permission() - **ИСПРАВЛЕНО** ✅
2. Добавить detect-secrets в pre-commit - **В РАБОТЕ** ⏳
3. Добавить Bandit security linting - **ЗАПЛАНИРОВАНО** ⏳
4. Аудит логов - **ТРЕБУЕТСЯ** ⏳

**Остальные находки** можно исправить в последующих патч-релизах (v1.5.1, v1.5.2).

---

**Подготовил:** GitHub Copilot Security Audit  
**Дата:** 6 октября 2025  
**Версия отчёта:** 1.0
