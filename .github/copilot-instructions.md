# Arvis AI Assistant · Copilot Guide

## 🎯 Статус проекта: Тестирование и стабилизация
- **Версия**: v1.5.1 (централизованная в `version.py`)
- **NO CRITICAL CHANGES** без тщательного тестирования
- Фокус на исправлении багов, оптимизации производительности и улучшении документации
- **В разработке**: Система автообновления клиента (`utils/update_checker.py`)

## 📦 Структура проекта Arvis

Проект Arvis состоит из **двух отдельных репозиториев**:

### 1. **Arvis-Client** (этот репозиторий)
**Репозиторий**: https://github.com/Fat1ms/Arvis-Client

**Назначение**: Desktop приложение — голосовой ассистент с полным функционалом AI

**Технологии**:
- **UI**: PyQt5 (безрамочное окно, кастомные виджеты)
- **STT**: Vosk (офлайн распознавание речи, русский/английский)
- **TTS**: Silero (офлайн синтез речи)
- **LLM**: Ollama (локальный запуск моделей)
- **Базы данных**: SQLite для локального хранения пользователей
- **Безопасность**: RBAC, 2FA (TOTP), audit logging

**Ключевые компоненты**:
```
Arvis-Client/
├── main.py                    # Точка входа
├── src/
│   ├── core/arvis_core.py    # Центральный движок
│   └── gui/                   # PyQt5 интерфейс
├── modules/                   # STT, TTS, LLM, модули функций
├── utils/
│   ├── async_manager.py      # Асинхронные задачи
│   ├── fast_http.py          # Оптимизированный HTTP клиент
│   └── security/             # RBAC, аутентификация, audit
├── config/config.json        # Конфигурация приложения
└── data/                     # Локальные данные пользователей
```

**Режимы работы**:
- **Автономный**: Полностью офлайн, локальная БД пользователей
- **Гибридный**: Подключение к Arvis-Server с fallback на локальную БД

### 2. **Arvis-Server** (отдельный репозиторий)
**Репозиторий**: https://github.com/Fat1ms/Arvis-Server

**Назначение**: Централизованный сервер аутентификации и управления пользователями

**Технологии**:
- **Framework**: FastAPI (async REST API)
- **База данных**: PostgreSQL (основная) / SQLite (разработка)
- **Аутентификация**: JWT токены (60 мин время жизни)
- **Безопасность**: bcrypt (пароли), CORS, rate limiting
- **API документация**: Swagger UI (`/docs`)

**Ключевые возможности**:
- ✅ Централизованное управление пользователями (создание, редактирование, удаление)
- ✅ JWT-based аутентификация с refresh токенами
- ✅ RBAC проверка прав доступа через API
- ✅ 2FA управление (включение/отключение TOTP)
- ✅ Аудит всех операций
- ✅ Health check эндпоинты для мониторинга
- ✅ Синхронизация пользователей между несколькими клиентами
- ✅ **Client API** - специализированные эндпоинты для клиентских приложений (v1.0.0+)

**API структура**:
```
Arvis-Server/
├── main.py                      # FastAPI приложение
├── api/
│   ├── auth.py                 # Admin API: аутентификация
│   ├── users.py                # Admin API: управление пользователями
│   └── client.py               # 🆕 Client API: эндпоинты для клиентов
├── models/                      # Pydantic модели
├── database/                    # SQLAlchemy ORM
├── security/                    # JWT, bcrypt, permissions
└── config.py                    # Настройки сервера
```

**Основные эндпоинты**:

#### Admin API (`/api/*`) - для администрирования
```http
# Аутентификация
POST   /api/auth/login              # Вход (username, password → JWT)
POST   /api/auth/logout             # Выход
POST   /api/auth/refresh            # Обновление токена
POST   /api/auth/verify-2fa         # Проверка 2FA кода
GET    /api/auth/check-permission   # Проверка прав доступа

# Управление пользователями (требует admin)
GET    /api/users/                  # Список пользователей
POST   /api/users/                  # Создать пользователя
GET    /api/users/{user_id}         # Информация о пользователе
PUT    /api/users/{user_id}         # Обновить пользователя
DELETE /api/users/{user_id}         # Удалить пользователя

# Мониторинг
GET    /api/health                  # Статус сервера
GET    /version                     # Версия API
```

#### 🆕 Client API (`/api/client/*`) - для клиентских приложений
```http
# Информация о сервере (без аутентификации)
GET    /api/client/server-info      # Версия сервера, совместимость

# Аутентификация (без предварительной аутентификации)
POST   /api/client/login            # Вход (username, password → JWT + user + permissions)
POST   /api/client/register         # Регистрация нового пользователя
GET    /api/client/validate-token   # Проверка токена (требует Bearer token)

# Профиль пользователя (требует Bearer token)
GET    /api/client/profile          # Получить профиль
PUT    /api/client/profile          # Обновить профиль (full_name, email)
PUT    /api/client/change-password  # Сменить пароль

# Разрешения (требует Bearer token)
GET    /api/client/my-permissions   # Получить все разрешения
POST   /api/client/check-permissions # Проверить конкретные разрешения
```

**Отличия Client API от Admin API**:
| Функция | Admin API | Client API |
|---------|-----------|------------|
| Аутентификация | ✅ `/api/auth/login` | ✅ `/api/client/login` (+ permissions в ответе) |
| Регистрация | ❌ | ✅ `/api/client/register` |
| Профиль | ✅ `/api/auth/me` | ✅ `/api/client/profile` + update |
| Смена пароля | ❌ | ✅ `/api/client/change-password` |
| Разрешения | ✅ `/api/auth/check-permission` | ✅ `/api/client/my-permissions` (все сразу) |
| Управление пользователями | ✅ `/api/users/*` | ❌ (только admin API) |
| Требуемые права | Admin для большинства | User для всех |

**Стандартные учётные данные** (первый запуск):
- Username: `admin`
- Password: `ChangeMeOnFirstRun123!`

**Настройка подключения** (на клиенте):
```json
// config/config.json
{
  "security": {
    "auth": {
      "use_remote_server": true,
      "server_url": "http://192.168.0.130:8000"
    }
  }
}
```

**Важно для разработчиков**:
- 🔒 **Сервер в продакшене** — избегайте критических изменений без тестирования
- 🔄 **Гибридная архитектура** — клиент автоматически переключается на локальную БД если сервер недоступен
- 📡 **API версионирование** — проверяйте совместимость версий клиента и сервера
- 🛡️ **Безопасность** — все операции логируются в `logs/audit/*.jsonl`

## 🏗️ Общая архитектура

### Точка входа и инициализация
- **`main.py`**: Создаёт `ArvisApp` → Qt application → splash screen → `MainWindow` → login dialog → основной интерфейс
- **`src/gui/main_window.py`**: Безрамочное окно, координирует `ChatPanel`, `StatusPanel`, `OrbitWidget`
- **`src/core/arvis_core.py`**: Центральный мозг приложения — управляет STT, TTS, LLM, модулями, историей, RBAC

### Асинхронная инициализация компонентов
```python
# ArvisCore.__init__ → init_components_async()
# Порядок загрузки (в потоке, не блокируя UI):
1. LLMClient (быстро)
2. TTSEngine (медленно, может использовать subprocess)
3. STTEngine (медленно, загружает Vosk модель)
4. KaldiWakeWordDetector (опционально, если stt.wake_word_engine="kaldi")
5. Модули: WeatherModule, NewsModule, SystemControlModule, CalendarModule, SearchModule
```

**Важно**: Подключайте Qt сигналы ДО присваивания компонента переменной экземпляра (см. `init_components_async` → подключение `stt_instance.speech_recognized` перед `self.stt_engine = stt_instance`).

## 🔄 Ключевые потоки данных

### Обработка сообщений пользователя
```
Пользователь → ChatPanel.send_message()
  ↓
ArvisCore.process_message(text)
  ↓ (RBAC проверка: Permission.CHAT_USE)
  ↓
handle_module_commands(text) — пытается распарсить как команду (погода, новости и т.д.)
  ↓ если не модуль →
LLMClient.stream_response() — стриминг от Ollama
  ↓ (буферизация в _stream_buffer_text, ≥20 символов)
  ↓
partial_response.emit() → ChatPanel обновляет UI
  ↓
TTSEngine.speak_streaming(chunk) — озвучивает в реальном времени
  ↓
response_ready.emit() → сохранение в ConversationHistory
```

### Голосовая активация (wake word)
```
1. KaldiWakeWordDetector (или встроенный Vosk) слушает "Арвис/Jarvis"
2. wake_word_detected.emit()
3. ArvisCore._on_wake_word_detected():
   - ОСТАНАВЛИВАЕТ wake word detection
   - Проигрывает короткую фразу подтверждения ("Слушаю")
   - _speak_and_start_recording_after_tts() — начинает запись после TTS
4. STTEngine.speech_recognized.emit(text)
5. ArvisCore.process_voice_input(text):
   - Проверяет, не просто ли имя ("Арвис" без команды)
   - Если команда → process_message(text)
   - Перезапускает wake word detection после обработки
```

**Критично**: Wake word detection НЕ должен работать во время TTS воспроизведения или обработки запроса (см. `_on_wake_word_detected` — проверка `self._is_tts_playing` и `self.is_processing`).

### TTS буферизация и стриминг
- **Минимальный размер буфера**: 20 символов или граница слова (`. , ! ? ; : \n`)
- **Subprocess fallback**: `modules/tts_worker_subprocess.py` для долгих операций
- **Предзагрузка фраз подтверждения**: `_prime_name_ack_cache_async()` генерирует аудио для "Слушаю", "Да?" и т.д. в фоне

## 🔐 Система безопасности (RBAC + 2FA)

### Роли и разрешения
```python
# utils/security/rbac.py
Role.GUEST      → минимальные права (чат, погода, новости)
Role.USER       → стандартные права (+ модули, история, блокировка системы)
Role.POWER_USER → расширенные (+ перезагрузка, скрипты, импорт/экспорт)
Role.ADMIN      → ВСЕ разрешения (+ управление пользователями, безопасность)
```

### Проверка прав в коде
```python
from utils.security import get_rbac_manager, require_permission, Permission

# Декоратор
@require_permission(Permission.SYSTEM_SHUTDOWN)
def shutdown_system():
    os.system("shutdown /s /t 0")

# Явная проверка
rbac = get_rbac_manager()
rbac.set_current_user(user_id)
rbac.set_role(user.role)
if not rbac.has_permission(Permission.MODULE_WEATHER):
    raise PermissionError("Access denied")
```

### Аутентификация (гибридная)

**Архитектура четырёх уровней** (обновлено в v1.5.1+):
1. **`utils/security/hybrid_auth.py`**: Главный менеджер — выбирает режим (Client API → Admin API → локально)
2. **`utils/security/client_api.py`**: 🆕 REST API клиент для Client API (`/api/client/*`) — основной способ
3. **`utils/security/remote_auth_client.py`**: REST API клиент для Admin API (`/api/*`) — fallback для admin функций
4. **`utils/security/local_auth.py`**: Локальное хранилище SQLite (`data/users.db`) — последний fallback

**Поток аутентификации** (обновлено в v1.5.1+):
```
GUI (LoginDialog) 
  ↓
HybridAuthManager.authenticate(username, password)
  ↓
1. Пробует ArvisClientAPI.login() → /api/client/login
   ↓ (если сервер доступен и совместим)
   ✅ JWT токен + user data + permissions → сохранение в session
   ↓ (если Client API недоступен)
2. Fallback #1: RemoteAuthClient.login() → /api/auth/login (Admin API)
   ↓ (если сервер доступен)
   ✅ JWT токен + user data → сохранение в session
   ↓ (если сервер полностью недоступен)
3. Fallback #2: LocalAuth.authenticate() → data/users.db
   ↓
   ✅ Локальная сессия + user data
```

**Создание пользователя через сервер**:
```
UserManagementDialog.create_user()
  ↓
HybridAuthManager.create_user()
  ↓
1. RemoteAuthClient.create_user() → POST /api/users/ (требует admin token)
   ↓ (успешно)
   ✅ Пользователь создан на сервере
   ↓ (сервер недоступен)
2. Fallback: LocalAuth.create_user() → data/users.db
   ↓
   ✅ Пользователь создан локально
```

**Режимы работы**:
```python
# Только сервер (рекомендуется для prod)
config.json: {"auth": {"use_remote_server": true}}
→ Все операции через Arvis-Server, fallback отключен

# Только локально (автономный режим)
config.json: {"auth": {"use_remote_server": false}}
→ Все операции через SQLite, сервер игнорируется

# Гибридный (по умолчанию)
config.json: {"auth": {"use_remote_server": true}}
→ Пробует сервер, при недоступности → локальная БД
```

**2FA интеграция**:
- **TOTP**: `utils/security/totp_manager.py` (генерация QR, проверка кодов)
- **UI**: `src/gui/two_factor_setup_dialog.py`, `src/gui/two_factor_verification_dialog.py`
- **Backup коды**: Генерируются при включении 2FA, хранятся хешированные
- **Синхронизация**: 2FA настройки хранятся как на сервере, так и локально

**Audit logging**: `utils/security/audit.py` → `logs/audit/*.jsonl` (ротация 10 МБ, 90 дней TTL)

## 🛠️ Паттерны и конвенции

### Асинхронные задачи (не блокируем Qt UI)
```python
from utils.async_manager import task_manager

def heavy_task():
    # Долгая операция...
    return result

def on_complete(task_id, result):
    # Обработка в UI потоке
    self.update_ui(result)

def on_error(task_id, error):
    self.show_error(error)

task_manager.run_async(
    "my_task_id", 
    heavy_task,
    on_complete=on_complete,
    on_error=on_error
)
```

**Никогда не вызывайте** долгие операции (STT, TTS, HTTP) напрямую в обработчиках Qt событий!

### HTTP запросы к Ollama
```python
from utils.fast_http import FastHTTPClient

# Автоматически заменяет localhost → 127.0.0.1 (избегаем IPv6 зависаний)
client = FastHTTPClient("http://localhost:11434", timeout=5.0)
result = client.get("/api/tags")  # Кешируется 5 секунд
```

### Локализация (i18n)
```python
from i18n import _, apply_to_widget_tree

# В коде
label.setText(_("Привет, мир!"))

# После изменения языка
new_lang = "en"
I18N.get().set_language(new_lang)
apply_to_widget_tree(self)  # Обновить весь виджет дерево
```

Все UI строки **должны** быть обёрнуты в `_()`.

### Конфигурация
- **`config/config.json`**: Основные настройки (объединяется с `.env` через `config/config.py`)
- **Секреты**: `.env` файл (API ключи, токены)
- **Wake words**: `stt.kaldi_wake_words` (список вариантов распознавания)

```python
from config.config import Config
config = Config()
value = config.get("llm.default_model", "auto")
config.set("modules.voice_activation_enabled", True)
```

### История разговоров
```python
from utils.conversation_history import ConversationHistory

history = ConversationHistory(config)
history.add_message("user", "Привет")
history.add_message("assistant", "Здравствуйте!")
# Автосохранение каждые 5 сообщений в data/conversation_history.json
# Триммится до 50 последних записей
```

## 🧪 Рабочие процессы разработчика

### Быстрый старт (Windows)
```bat
# Первая установка
INSTALL.bat

# Запуск
LAUNCH.bat

# Или вручную
venv\Scripts\activate
python main.py
```

**Требования**: Python 3.11 или 3.12 (PyAudio несовместим с 3.13!)

### Диагностика
```bat
diagnose_setup.bat       # Проверка окружения, зависимостей
diagnose_performance.bat # Мониторинг CPU/RAM/GPU
STATUS.bat               # Быстрая проверка статуса
ollama_manager.bat       # Управление Ollama сервером
```

### Тестирование
```python
# Unit тесты
pytest tests/

# Голосовая интеграция
python tests\debug_test.py

# Проверка синтаксиса и линтинг (перед коммитом)
pre-commit run --all-files
```

**Правило**: Все тесты должны проходить перед коммитом!

### Добавление нового модуля
1. Создать `modules/my_module.py` с классом `MyModule(config)`
2. Зарегистрировать в `ArvisCore.init_modules()`:
   ```python
   self.my_module = MyModule(self.config)
   ```
3. Добавить обработку в `ArvisCore.handle_module_commands()`:
   ```python
   if "ключевое слово" in message.lower():
       if self.rbac.has_permission(Permission.MODULE_MY):
           return self.my_module.process(message)
       else:
           raise PermissionError("Доступ запрещён")
   ```
4. Обновить `utils/security/rbac.py` → добавить `Permission.MODULE_MY` в матрицу ролей

## ⚠️ Частые ловушки и решения

### 1. IPv6 зависания с localhost
**Проблема**: `localhost` резолвится в `::1` и виснет на некоторых конфигурациях Windows.
**Решение**: Всегда используйте `127.0.0.1` или `FastHTTPClient` (автоматически заменяет).

```python
# ❌ Плохо
url = "http://localhost:11434"

# ✅ Хорошо
url = "http://127.0.0.1:11434"
# или
from utils.fast_http import FastHTTPClient
client = FastHTTPClient("http://localhost:11434")  # Автозамена внутри
```

### 2. Долгая инициализация Vosk модели
**Проблема**: Полная модель `vosk-model-ru-0.22` загружается ~2 минуты.
**Решение**: Используйте `vosk-model-small-ru-0.22` для wake word detection, полную — только для STT.

```json
// config.json
{
  "stt": {
    "model_path": "models/vosk-model-ru-0.22",
    "kaldi_model_path": "models/vosk-model-small-ru-0.22",
    "wake_word_engine": "kaldi"
  }
}
```

### 3. TTS блокирует UI
**Проблема**: Синтез речи может занять секунды и заморозить интерфейс.
**Решение**: TTS автоматически использует `task_manager.run_async()`, но для особо долгих операций есть subprocess fallback.

```python
# TTSEngine автоматически выбирает лучший метод
tts_engine.speak(text)  # Неблокирующий
```

### 4. Wake word продолжает слушать во время TTS
**Проблема**: Ложные срабатывания, когда ассистент слышит себя.
**Решение**: `_on_wake_word_detected()` **ВСЕГДА** останавливает wake word detection перед TTS, перезапускает после.

```python
# Паттерн для остановки wake word
wake_word_detector.stop_detection()
# ... TTS воспроизведение ...
QTimer.singleShot(600, lambda: self._restart_wake_listening_if_enabled())
```

### 5. Audit логи разрастаются
**Проблема**: `logs/audit/*.jsonl` может занять много места.
**Решение**: Автоматическая ротация (10 МБ) и очистка (90 дней) через `utils/housekeeping.py`.

Настройки в `config.json`:
```json
{
  "audit": {
    "enabled": true,
    "max_log_size": 10485760,
    "max_log_age_days": 90
  }
}
```

### 6. PyInstaller сборка
**Текущий статус**: Сборочные скрипты в разработке (см. упоминания `build_exe.bat` в коде)
**Важно**: При создании включите в пакет `models/`, `config/`, `UXUI/`, `data/` (без секретов!)

```bat
pyinstaller --onefile --windowed --add-data "models;models" main.py
```

## 🆕 Система автообновления (в разработке)

### Архитектура
```
utils/update_checker.py → GitHub Releases API
  ↓ (сравнение version.py с latest release)
  ↓ если новая версия →
Скачивание → Проверка контрольных сумм → Создание бэкапа
  ↓
Применение обновления → Перезапуск приложения
  ↓ (если ошибка)
Rollback из бэкапа
```

### Требования к реализации
- **Неблокирующая проверка**: фоновая задача через `task_manager`
- **Согласие пользователя**: UI диалог перед обновлением
- **Сохранение данных**: `data/`, `config/`, `logs/` не затрагиваются
- **Целостность**: SHA256 хеши для всех файлов
- **Настройка**: `config.json` → `auto_update.enabled`

## 📚 Дополнительная документация

### Безопасность и аутентификация
- **[CLIENT_API_INTEGRATION.md](docs/CLIENT_API_INTEGRATION.md)**: 🆕 Интеграция с Client API сервера (v1.5.1+)
- **[CLIENT_API_README.md](docs/CLIENT_API_README.md)**: 🆕 Краткая инструкция по Client API
- **[CLIENT_API_CHANGELOG.md](docs/CLIENT_API_CHANGELOG.md)**: 🆕 Changelog и миграция

### Прочее (если документация существует)
- **RBAC_GUIDE.md**: Полное руководство по системе безопасности
- **USER_MANAGEMENT_GUIDE.md**: Управление пользователями
- **USER_GUIDE_2FA.md**: Настройка двухфакторной аутентификации
- **SECURITY_AUDIT_REPORT.md**: Аудит безопасности

## 🔥 Правила коммитов

1. **Все тесты проходят**: `pytest tests/` — зелёный
2. **Pre-commit хуки**: `pre-commit run --all-files` без ошибок
3. **Обратная совместимость**: Не ломайте существующие конфиги и данные пользователей
4. **Маленькие изменения**: Лучше 5 коммитов по 50 строк, чем 1 на 250 строк
5. **Документация**: Обновите CHANGELOG.md и релевантные `.md` файлы

## 🎓 Быстрые примеры кода

### Добавить сообщение в чат
```python
from src.core.arvis_core import ArvisCore

core = ArvisCore(config)
core.process_message("Привет, Арвис!")
```

### Проверить права пользователя
```python
from utils.security import get_rbac_manager, Permission, Role

rbac = get_rbac_manager()
rbac.set_role(Role.USER)
if rbac.has_permission(Permission.SYSTEM_SHUTDOWN):
    print("Может выключить систему")
```

### Создать пользователя
```python
from utils.security import get_auth_manager, Role

auth = get_auth_manager()
user = auth.create_user(
    username="ivan",
    password="SecurePass123!",
    role=Role.USER
)
```

### Асинхронная загрузка данных
```python
from utils.async_manager import task_manager

def fetch_data():
    # Долгая операция
    return {"result": "success"}

task_manager.run_async(
    "fetch_task",
    fetch_data,
    on_complete=lambda tid, res: print(f"Готово: {res}")
)
```

---

**Версия документа**: 2.0 (обновлено 08.10.2025)  
**Для вопросов**: См. [CONTRIBUTING.md](CONTRIBUTING.md) или откройте issue на GitHub
