# Changelog - Arvis AI Assistant

Все важные изменения в проекте Arvis будут документированы в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
и этот проект придерживается [Semantic Versioning](https://semver.org/lang/ru/).

---

## [Unreleased] - Phase 3 Feature #1: Multi-Engine TTS System

### Added (21.10.2025)
- 🎤 **Multi-Engine TTS System**: Factory pattern для управления несколькими TTS движками
  - `modules/tts_factory.py`: Singleton фабрика с авто-регистрацией
  - `modules/tts_base.py`: Базовый класс и интерфейсы для всех TTS движков
  - Поддержка 3 движков: Silero (по умолчанию), Bark, SAPI5

- 🔄 **Runtime Engine Switching**: Переключение TTS движков без перезапуска
  - Метод `ArvisCore.switch_tts_engine_async()` для смены движка
  - Qt сигнал `tts_engine_switched` для уведомления о смене
  - Health check валидация перед переключением

- 🌐 **Server Negotiation Placeholder**: Заготовка для гибридной системы
  - Метод `_negotiate_engine_with_server()` в ArvisCore
  - Готово для интеграции с Arvis-Server (Phase 3 Feature #2)

- ⚙️ **Enhanced Configuration**: Расширенная конфигурация TTS
  - Секция `tts.engines` в config.json с настройками для каждого движка
  - Методы `Config.get_enabled_tts_engines()` и `get_tts_engine_config()`
  - Поддержка `default_engine`, `fallback_on_error`, `health_check_interval`

- 🧪 **Comprehensive Testing**: 78 тестов (64 unit + 14 integration)
  - Новый файл: `tests/integration/test_arviscore_tts_integration.py` (14 тестов)
  - 100% успешных прохождений всех тестов
  - Покрытие: инициализация фабрики, переключение движков, сигналы, конфигурация

- 🔧 **TTS Engine Implementations**:
  - `modules/tts_silero.py`: Silero TTS движок с оптимизацией
  - `modules/tts_bark.py`: Bark TTS с качественным голосом
  - `modules/tts_sapi5.py`: Windows SAPI5 для совместимости

### Changed (21.10.2025)
- 🏗️ **ArvisCore Refactoring**: Переход на factory pattern
  - Модифицирован `src/core/arvis_core.py` (1873 → 1901 строк)
  - TTS инициализация теперь через `_create_tts_engine_with_fallback()`
  - Добавлены переменные: `_tts_factory`, `_tts_engine_type`, `_available_tts_engines`
  - 4 новых метода для управления TTS движками

- 📋 **Configuration Management**: Улучшенная работа с конфигурацией
  - `config/config.py`: Добавлены helper методы для TTS
  - `config/config.json`: Расширена секция `tts` с подсекцией `engines`

### Performance (21.10.2025)
- ⚡ **Factory Overhead**: Минимальный (<1ms для singleton)
- ⚡ **Health Checks**: Асинхронные, неблокирующие (~50-100ms)
- ⚡ **Engine Switching**: <2 секунд (включая cleanup + init)
- 💾 **Memory**: Только активный движок в памяти

### Testing (21.10.2025)
- ✅ **78/78 тестов** пройдены успешно
- ✅ Нет регрессий в существующем функционале
- ✅ Интеграционные тесты покрывают все точки интеграции
- ⏱️ Время выполнения тестов: ~4 секунды

### Known Issues (21.10.2025)
- ⚠️ 11 pytest warnings (asyncio marker на sync функциях) - косметические
- ⚠️ `test_gemma_provider.py` исключён из запуска (syntax error, не связан с TTS)
- ⚠️ Vosk модель отсутствует (STT тесты используют моки)

### Documentation (21.10.2025)
- 📚 Создан `docs/PHASE3_FEATURE1_DAYS4-5_REPORT.md` с полным отчётом
- 📚 TODO: Обновить README.md с информацией о multi-engine TTS
- 📚 TODO: Создать `docs/TTS_ENGINE_GUIDE.md` для разработчиков

---

## [1.5.1] - 2025-10-XX

### Added
- 🔐 Client API интеграция (`utils/security/client_api.py`)
- 🔄 Гибридная аутентификация (Client API → Admin API → Local fallback)
- 📊 Audit logging для всех операций безопасности

### Changed
- 🔧 Переход с Admin API на Client API для клиентских операций
- 🔐 Улучшенная обработка JWT токенов

### Fixed
- 🐛 Исправлены проблемы с подключением к Arvis-Server
- 🐛 Улучшена обработка ошибок при регистрации пользователей

---

## [1.5.0] - 2025-10-XX

### Added
- 🎙️ Голосовая активация через wake word ("Арвис", "Jarvis")
- 🔊 Kaldi wake word detector для офлайн распознавания
- 🤖 Интеграция с Ollama для локального LLM
- 🗣️ Silero TTS для синтеза речи
- 🎤 Vosk STT для распознавания речи
- 🔐 RBAC система с ролями (Guest, User, Power User, Admin)
- 🔒 2FA поддержка (TOTP + backup коды)
- 📊 Audit logging в JSON Lines формат
- 🌐 Гибридная архитектура (Remote Server + Local fallback)
- 🎨 PyQt5 GUI с безрамочным окном
- 💬 Чат-панель с историей разговоров
- 📦 Модульная система (Weather, News, System Control, Calendar, Search)

### Changed
- 🏗️ Полная переработка архитектуры на PyQt5
- 🔄 Асинхронная инициализация компонентов
- 📝 Улучшенная система логирования

### Security
- 🔐 Bcrypt для хеширования паролей
- 🔑 JWT токены для аутентификации
- 🛡️ RBAC проверка прав на всех уровнях
- 📊 Полный audit trail всех операций

---

## [1.0.0] - 2025-09-XX

### Added
- 🎉 Первый релиз Arvis AI Assistant
- 💬 Базовый чат с пользователем
- 🤖 Интеграция с OpenAI API
- 🔊 Простой TTS через pyttsx3
- 🎤 Простой STT через speech_recognition

---

## Типы изменений

- `Added` - новые функции
- `Changed` - изменения в существующем функционале
- `Deprecated` - функции, которые скоро будут удалены
- `Removed` - удалённые функции
- `Fixed` - исправления багов
- `Security` - изменения безопасности
- `Performance` - улучшения производительности
- `Testing` - изменения в тестах
- `Documentation` - изменения в документации

---

**Версия документа**: 1.0  
**Последнее обновление**: 21.10.2025
