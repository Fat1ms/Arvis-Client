# 🏗️ Гибридная архитектура Arvis - Дизайн документ

**Версия**: 1.0  
**Дата**: 21 октября 2025  
**Статус**: In Development  

---

## 📌 Содержание
1. [Обзор](#обзор)
2. [Режимы работы](#режимы-работы)
3. [Архитектурные слои](#архитектурные-слои)
4. [Точки расширения](#точки-расширения)
5. [Диаграммы](#диаграммы)
6. [Миграция и переключение](#миграция-и-переключение)
7. [Технические спецификации](#технические-спецификации)

---

## 🎯 Обзор

Гибридная архитектура Arvis позволяет клиенту работать в трёх режимах:

| Режим | Источник данных | Приватность | Функционал | Использование |
|-------|-----------------|-------------|-----------|---|
| **STANDALONE** | Локальный (Ollama, Vosk) | ✅ Полная | Базовый | Оффлайн, дома |
| **HYBRID** | Локальный + Сервер | ✅ Хорошая | Полный | Стандартный |
| **CLOUD** | Облачные сервисы (OpenAI, Azure, etc) | ⚠️ Зависит от провайдера | Расширенный | Профессиональный |

### Ключевые принципы:
- 🔄 **Автоматический fallback** - если облако недоступно → локальные ресурсы
- 🎛️ **Явный выбор режима** - пользователь может выбрать режим в настройках
- 📦 **Минимальные зависимости** - STANDALONE работает без интернета
- 🔐 **Приватность по умолчанию** - данные остаются локально, если не включен облак
- ⚡ **Производительность** - локальные компоненты приоритизированы

---

## 🔄 Режимы работы

### 1️⃣ STANDALONE (Полностью автономный)
```
┌─────────────────────────────────────────┐
│         Arvis-Client (STANDALONE)       │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐  │
│  │     STT: Vosk (локальный)         │  │
│  │     TTS: Silero (локальный)        │  │
│  │     LLM: Ollama (локальный)       │  │
│  │     БД: SQLite (локальная)        │  │
│  └───────────────────────────────────┘  │
│                                         │
│         Никакого сетевого доступа      │
│         ✅ Оффлайн работа             │
│         ✅ Максимальная приватность    │
│         ⚠️ Ограниченный функционал    │
└─────────────────────────────────────────┘
```

**Компоненты:**
- 🎙️ STT: `vosk-model-*` (локальная модель)
- 🔊 TTS: Silero v3 (локальный синтез)
- 🧠 LLM: Ollama (mistral:7b, llama2, etc)
- 💾 Auth: SQLite (`data/users.db`)

**Конфигурация:**
```json
{
  "operation_mode": "standalone",
  "security.auth.use_remote_server": false,
  "security.auth.fallback_to_local": false,
  "llm.type": "local",
  "stt.type": "local",
  "tts.type": "local"
}
```

**Ограничения:**
- Нет синхронизации между девайсами
- Нет облачных плагинов
- Нет коллаборации
- Нет лицензирования (только локальное)

---

### 2️⃣ HYBRID (Локальный + Сервер)
```
┌──────────────────────────────────────────────────┐
│        Arvis-Client (HYBRID MODE)                │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │     Локальные компоненты (PRIMARY)         │  │
│  │  ┌──────────────┐  ┌──────────────────┐   │  │
│  │  │ STT: Vosk    │  │ TTS: Silero      │   │  │
│  │  │ LLM: Ollama  │  │ БД: SQLite       │   │  │
│  │  └──────────────┘  └──────────────────┘   │  │
│  └────────────────────────────────────────────┘  │
│                  ↓ (fallback)                     │
│  ┌────────────────────────────────────────────┐  │
│  │   Arvis-Server (OPTIONAL)                  │  │
│  │  • Client API (v1.0+)                     │  │
│  │  • Синхронизация пользователей            │  │
│  │  • Cloud plugins                          │  │
│  │  • Audit logging                          │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
└──────────────────────────────────────────────────┘

        ✅ Оффлайн режим (локально)
        ✅ Облачные возможности (опционально)
        ✅ Синхронизация
        ✅ Лучший выбор для большинства
```

**Компоненты:**
- 📱 **Primary Layer** (локальный - всегда работает):
  - STT: Vosk
  - TTS: Silero
  - LLM: Ollama
  - Auth: SQLite + Client API
  
- ☁️ **Optional Layer** (сервер - если доступен):
  - Cloud plugins
  - Синхронизация настроек
  - Расширенные функции
  - User synchronization

**Конфигурация:**
```json
{
  "operation_mode": "hybrid",
  "security.auth.use_remote_server": true,
  "security.auth.fallback_to_local": true,
  "security.auth.server_url": "http://arvis-server:8000",
  "llm.type": "local",
  "stt.type": "local",
  "tts.type": "local",
  "sync.enabled": true,
  "plugins.cloud_enabled": true
}
```

**Преимущества:**
- ✅ Работает оффлайн
- ✅ Синхронизация между девайсами
- ✅ Облачные плагины
- ✅ Лучший баланс приватности и функционала

---

### 3️⃣ CLOUD (Облачный режим)
```
┌──────────────────────────────────────────────────┐
│         Arvis-Client (CLOUD MODE)                │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │   Облачные компоненты (PRIMARY)            │  │
│  │  ┌────────────────┐  ┌─────────────────┐  │  │
│  │  │ STT: OpenAI    │  │ TTS: Azure      │  │  │
│  │  │ LLM: OpenAI/  │  │ Auth: Remote    │  │  │
│  │  │     Claude     │  │ Sync: Cloud DB  │  │  │
│  │  └────────────────┘  └─────────────────┘  │  │
│  └────────────────────────────────────────────┘  │
│                  ↓ (fallback)                     │
│  ┌────────────────────────────────────────────┐  │
│  │   Локальный fallback (OPTIONAL)            │  │
│  │  • STT: Vosk                              │  │
│  │  • TTS: Silero                            │  │
│  │  • LLM: Ollama                            │  │
│  │  (только если облако недоступно)         │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
└──────────────────────────────────────────────────┘

        ⚠️ Требует интернета
        ✅ Лучшие модели
        ⚠️ Меньше приватности
        ✅ Максимальный функционал
```

**Компоненты:**
- ☁️ **Primary Layer** (облачные сервисы):
  - STT: OpenAI Whisper, Google Speech-to-Text, Azure
  - TTS: Azure TTS, Google TTS, ElevenLabs
  - LLM: OpenAI GPT, Claude, Google Gemini
  - Auth: Удаленный сервер
  
- 📱 **Fallback Layer** (локальный - если облако упало):
  - STT: Vosk
  - TTS: Silero
  - LLM: Ollama

**Конфигурация:**
```json
{
  "operation_mode": "cloud",
  "security.auth.use_remote_server": true,
  "security.auth.fallback_to_local": true,
  "llm": {
    "type": "cloud",
    "provider": "openai",
    "api_key": "sk-...",
    "model": "gpt-4",
    "fallback_local": true
  },
  "stt": {
    "type": "cloud",
    "provider": "openai",
    "api_key": "sk-...",
    "fallback_local": true
  },
  "tts": {
    "type": "cloud",
    "provider": "azure",
    "api_key": "...",
    "fallback_local": true
  }
}
```

**Особенности:**
- Требует API ключей
- Высокие затраты (за API вызовы)
- Лучшие модели AI
- Облачное хранилище
- Максимальный функционал

---

## 🏗️ Архитектурные слои

### Layer Stack (по приоритету):

```
┌─────────────────────────────────────────────────────┐
│  UI Layer (GUI, Settings, Mode Selection)           │
├─────────────────────────────────────────────────────┤
│  Application Layer (ArvisCore, Main Logic)          │
├─────────────────────────────────────────────────────┤
│  Provider Abstraction Layer                         │
│  ┌──────────────┬──────────────┬──────────────┐     │
│  │ STT Provider │ TTS Provider │ LLM Provider │     │
│  │  Adapter     │  Adapter     │  Adapter     │     │
│  └──────────────┴──────────────┴──────────────┘     │
├─────────────────────────────────────────────────────┤
│  Implementation Layer                               │
│  ┌────────────────────┬────────────────────────┐    │
│  │  Local Engines     │  Cloud Adapters        │    │
│  │  • Vosk STT        │  • OpenAI STT/TTS/LLM  │    │
│  │  • Silero TTS      │  • Azure TTS           │    │
│  │  • Ollama LLM      │  • Google Speech       │    │
│  │  • SQLite Auth     │  • Claude              │    │
│  └────────────────────┴────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│  Fallback & Caching Layer                           │
│  • Automatic failover                               │
│  • Result caching                                   │
│  • Retry logic                                      │
├─────────────────────────────────────────────────────┤
│  External Services                                  │
│  • Arvis-Server / Cloud APIs                        │
│  • Ollama server                                    │
└─────────────────────────────────────────────────────┘
```

### Component Adapters (Provider Pattern):

```python
class STTProvider(ABC):
    @abstractmethod
    def recognize(audio: bytes) -> str: pass
    
    @abstractmethod
    def is_available() -> bool: pass

# Реализации:
- VoskSTT(STTProvider)          # Локальный
- OpenAIWhisper(STTProvider)    # Облачный
- GoogleSpeech(STTProvider)     # Облачный
- AzureSpeech(STTProvider)      # Облачный

# Выбор провайдера:
stts = []
if mode in [STANDALONE, HYBRID]:
    stts.append(VoskSTT())
if mode in [CLOUD, HYBRID] and cloud_enabled:
    stts.append(OpenAIWhisper())
    
stt_engine = FallbackSTT(stts)  # Пытается по порядку
```

---

## 🔌 Точки расширения

### 1. Новые облачные провайдеры

**Добавить поддержку Google Cloud Speech-to-Text:**

```python
# utils/providers/stt/google_stt.py
from utils.providers.stt import STTProvider

class GoogleSpeechToText(STTProvider):
    def __init__(self, config: Config):
        self.api_key = config.get("stt.cloud.google.api_key")
        self.client = speech.SpeechClient()
    
    def recognize(self, audio: bytes) -> str:
        # Реализация
        pass
    
    def is_available(self) -> bool:
        return bool(self.api_key) and self.check_connection()

# config.json
{
  "stt": {
    "cloud": {
      "google": {
        "api_key": "...",
        "enabled": true
      }
    }
  }
}
```

### 2. Новые локальные модели

**Добавить поддержку других Vosk моделей:**

```python
# modules/stt_engine.py - уже поддерживает конфиг
{
  "stt": {
    "engine": "vosk",
    "model_path": "models/vosk-model-en-0.22",  # Переключение языка
    "wake_word": "alexa"  # Кастомное wake word
  }
}
```

### 3. Кастомные LLM провайдеры

**Добавить Hugging Face:**

```python
# utils/providers/llm/huggingface_llm.py
class HuggingFaceLLM(LLMProvider):
    def stream_response(self, prompt: str):
        # Стриминг от Hugging Face API
        pass

# Регистрация в ArvisCore:
providers_llm = {
    "openai": OpenAILLM,
    "claude": ClaudeLLM,
    "ollama": OllamaLLM,
    "huggingface": HuggingFaceLLM,  # Новый!
}
```

### 4. Кастомные модули синхронизации

```python
# modules/sync_module.py
class SyncModule:
    def sync_settings(self):
        # Синхронизация с сервером/облаком
        
    def sync_history(self):
        # Синхронизация истории чатов
        
    def sync_plugins(self):
        # Загрузка cloud plugins
```

---

## 📊 Диаграммы

### Диаграмма состояний режимов:

```
┌─────────────┐
│  STANDALONE │
└──────┬──────┘
       │ enable_cloud
       ↓
┌─────────────┐
│   HYBRID    │ ← → ┌──────────────┐
│             │     │ offline mode │
└──────┬──────┘     └──────────────┘
       │ disable_fallback + cloud_only
       ↓
┌─────────────┐
│    CLOUD    │
└──────┬──────┘
       │ disable_cloud
       ↓
┌─────────────┐
│  STANDALONE │
└─────────────┘
```

### Data Flow (HYBRID mode):

```
User Input
    ↓
ArvisCore.process_message()
    ↓
Check Operation Mode
    ↓
┌─────────────────────────────────┐
│  Mode = HYBRID?                 │
└─────────────────────────────────┘
        ↙                    ↘
    YES                      NO
    ↓                        ↓
Local Engine          Cloud Engine
(Primary)            (Primary)
    ↓                        ↓
    ├─→ Success ──→ ┌──────────┐
    │               │  Return  │
    │        ┌─────→└──────────┘
    └─→ Fail │
         ↓   │
    Cloud    │
    Engine   │
    (Fallback)
         ↓
    ├─→ Success → Return
    │
    └─→ Fail → Error
```

### Configuration Hierarchy:

```
application/launch
    ↓
config/config.json (base settings)
    ↓
operation_mode selector
    ├─→ STANDALONE
    │   ├─ local_stt
    │   ├─ local_tts
    │   ├─ local_llm
    │   └─ local_auth
    │
    ├─→ HYBRID
    │   ├─ primary: local_*
    │   ├─ fallback: cloud_* (optional)
    │   └─ sync: enabled
    │
    └─→ CLOUD
        ├─ primary: cloud_*
        ├─ fallback: local_* (optional)
        └─ api_keys: required
    ↓
Load specific providers
    ↓
Initialize components
```

---

## 🔄 Миграция и переключение

### Переключение режимов:

```python
class OperationModeManager:
    def switch_mode(self, new_mode: OperationMode):
        """
        Переключение между режимами с миграцией данных
        """
        # 1. Сохранить текущее состояние
        self.backup_current_state()
        
        # 2. Остановить текущие компоненты
        self.shutdown_components()
        
        # 3. Синхронизировать данные
        self.sync_data(from_mode=self.current_mode, to_mode=new_mode)
        
        # 4. Переключить конфиг
        self.update_config(new_mode)
        
        # 5. Инициализировать новые компоненты
        self.initialize_components(new_mode)
        
        # 6. Проверить миграцию
        if not self.verify_migration():
            self.rollback_to_backup()
            raise MigrationError()
    
    def backup_current_state(self):
        """Сохраняет текущее состояние"""
        backup = {
            "mode": self.current_mode,
            "config": copy.deepcopy(self.config),
            "auth": self.save_auth_state(),
            "data": self.save_user_data(),
            "history": self.save_conversation_history(),
        }
        self.backups[datetime.now()] = backup
```

### Сценарии переключения:

**STANDALONE → HYBRID:**
```
1. Загрузить локальные данные пользователя
2. Подключиться к серверу (если доступен)
3. Синхронизировать историю чатов
4. Включить облачные плагины
5. Сохранить новые настройки
```

**HYBRID → CLOUD:**
```
1. Загрузить облачные конфиги (API ключи)
2. Проверить доступ к облачным сервисам
3. Миграция пользовательских данных
4. Настроить fallback (локальные компоненты)
5. Сохранить новые настройки
```

**CLOUD → STANDALONE:**
```
1. Сохранить облачные данные (если возможно)
2. Очистить API ключи из памяти
3. Переключиться на локальные компоненты
4. Отключить облачные плагины
5. Сохранить новые настройки
```

---

## 💻 Технические спецификации

### OperationMode Enum:

```python
from enum import Enum

class OperationMode(Enum):
    """Режимы работы Arvis"""
    
    STANDALONE = "standalone"  # Полностью локальный
    HYBRID = "hybrid"          # Локальный + опциональный сервер
    CLOUD = "cloud"            # Облачный с локальным fallback
    
    def get_display_name(self) -> str:
        names = {
            OperationMode.STANDALONE: "Автономный режим",
            OperationMode.HYBRID: "Гибридный режим",
            OperationMode.CLOUD: "Облачный режим",
        }
        return names.get(self, self.value)
    
    def is_requires_internet(self) -> bool:
        return self != OperationMode.STANDALONE
    
    def is_requires_server(self) -> bool:
        return self in [OperationMode.HYBRID, OperationMode.CLOUD]
```

### Configuration Schema:

```json
{
  "operation_mode": "hybrid",
  
  "modes": {
    "standalone": {
      "stt.type": "local",
      "tts.type": "local",
      "llm.type": "local",
      "auth.type": "local",
      "requires_internet": false
    },
    
    "hybrid": {
      "stt.type": "local",
      "tts.type": "local",
      "llm.type": "local",
      "auth.type": "hybrid",
      "sync.enabled": true,
      "cloud_plugins.enabled": true,
      "fallback_to_cloud": true,
      "requires_internet": false
    },
    
    "cloud": {
      "stt.type": "cloud",
      "tts.type": "cloud",
      "llm.type": "cloud",
      "auth.type": "remote",
      "sync.enabled": true,
      "cloud_plugins.enabled": true,
      "fallback_to_local": true,
      "requires_internet": true,
      "cloud_providers": {
        "stt": "openai",
        "tts": "azure",
        "llm": "openai"
      },
      "api_keys": {
        "openai": "sk-...",
        "azure": "...",
        "google": "..."
      }
    }
  }
}
```

### Provider Interface:

```python
from abc import ABC, abstractmethod
from typing import Optional

class Provider(ABC):
    """Базовый интерфейс для всех провайдеров"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверить, доступен ли провайдер"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Получить статус провайдера"""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Приоритет (ниже = приоритетнее)"""
        pass

class STTProvider(Provider):
    @abstractmethod
    def recognize(self, audio: bytes) -> str:
        """Распознать речь"""
        pass

class TTSProvider(Provider):
    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Синтезировать речь"""
        pass

class LLMProvider(Provider):
    @abstractmethod
    def stream_response(self, prompt: str):
        """Генерировать ответ (streaming)"""
        pass

class AuthProvider(Provider):
    @abstractmethod
    def authenticate(self, username: str, password: str) -> User:
        """Аутентифицировать пользователя"""
        pass
```

### Fallback Manager:

```python
class FallbackManager:
    """Управляет fallback логикой между провайдерами"""
    
    def __init__(self, providers: List[Provider]):
        self.providers = sorted(providers, key=lambda p: p.get_priority())
    
    def execute(self, operation: Callable, *args, **kwargs):
        """Пытается выполнить операцию с fallback"""
        last_error = None
        
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"Provider {provider} not available, skipping")
                continue
            
            try:
                logger.debug(f"Trying provider: {provider}")
                result = operation(provider, *args, **kwargs)
                logger.info(f"Success with provider: {provider}")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider} failed: {e}")
                continue
        
        if last_error:
            raise last_error
        else:
            raise RuntimeError("No available providers")
```

---

## 🎯 Фазы реализации

### Фаза 1: Фундамент (Шаг 1-2)
- ✅ Создать enum `OperationMode`
- ✅ Обновить config.json структуру
- ✅ Создать `FallbackManager`
- ✅ Создать Provider interfaces

### Фаза 2: UI и логика (Шаг 3)
- ⏳ Settings dialog для выбора режима
- ⏳ Mode switcher UI
- ⏳ OperationModeManager
- ⏳ Migration логика

### Фаза 3: Адаптация компонентов (Шаг 4)
- ⏳ STT: multi-provider adapter
- ⏳ TTS: multi-provider adapter
- ⏳ LLM: multi-provider adapter
- ⏳ Auth: multi-provider adapter

### Фаза 4: Cloud интеграция (Шаг 5)
- ⏳ OpenAI adapter (STT, TTS, LLM)
- ⏳ Azure adapter (TTS, Speech)
- ⏳ Лицензирование система
- ⏳ Синхронизация данных

### Фаза 5: Тестирование (Шаг 6)
- ⏳ Unit tests для каждого режима
- ⏳ Integration tests
- ⏳ Документация пользователя
- ⏳ Migration guide

---

## 📚 Ссылки

- [Arvis-Client](https://github.com/Fat1ms/Arvis-Client)
- [Arvis-Server](https://github.com/Fat1ms/Arvis-Server)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Документ в разработке.** Обновляется по мере прогресса реализации.
