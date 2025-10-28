# TTS Fix Summary (v1.5.2)

## ✅ Что было сделано

### 1. **TTS Factory с приоритизацией**
Переписан `modules/tts_factory.py` с поддержкой приоритетной цепочки fallback:

```
Silero (приоритет 1) 
  ↓ [если недоступна]
Bark (приоритет 2)
  ↓ [если недоступна]
SAPI5 (приоритет 3, Windows встроенный)
```

**Ключевые функции:**
- `TTSFactory.create_engine_with_fallback()` - автоматический выбор с fallback
- `TTSFactory.list_available_engines()` - список доступных движков
- `TTSFactory.get_engine_info()` - информация о движке
- Полная support для health check каждого движка

### 2. **SAPI5 TTS Engine**
Создан новый модуль `modules/system_tts.py` (SAPITTSEngine) - Windows встроенный синтез:

**Возможности:**
- Поддержка `pyttsx3` (удобный API, все платформы)
- Fallback на `win32com` SAPI прямое API
- Управление голосом, скоростью, громкостью
- Полная совместимость с TTSEngineBase

**Голоса:** Встроенные голоса Windows (Irina, Zira, David и т.д.)

### 3. **Обновлены требования**

**requirements.txt:**
- ✅ `bark-ml>=0.1.0` - Bark TTS синтез
- ✅ `pyttsx3>=2.90` - SAPI fallback
- ✅ `vosk==0.3.45` - речевое распознавание
- ✅ `torch`, `torchaudio` - для Silero/Bark

### 4. **Обновлена конфигурация**

**config.json:**
```json
{
  "tts": {
    "default_engine": "silero",
    "engines_priority": ["silero", "bark", "sapi"],
    "fallback_on_error": true,
    "engines": {
      "silero": {
        "enabled": true,
        "description": "Fast, offline, Russian support"
      },
      "bark": {
        "enabled": true,
        "model_size": "small",
        "description": "Quality, multilingual"
      },
      "sapi5": {
        "enabled": true,
        "rate": 150,
        "volume": 100,
        "description": "Windows system TTS"
      }
    }
  }
}
```

### 5. **Обновлен INSTALL.bat**

Добавлена:
- ✅ Загрузка Silero модели (100-200MB) при установке
- ✅ Пропуск Bark (большая модель, lazy loading)
- ✅ Правильная обработка ошибок
- ⚠️ PyAudio (опциональный, может не установиться на 3.13)

### 6. **Тестовый скрипт**

Создан `test_tts_fallback_chain.py`:
```bash
python test_tts_fallback_chain.py
```

Проверяет:
1. Зарегистрированные движки
2. Health status каждого
3. Приоритетную цепочку
4. Синтез речи

---

## 🔄 Как работает TTS теперь

### Инициализация (в ArvisCore)
```python
from modules.tts_factory import TTSFactory

# Создать TTS с автоматическим fallback
tts_engine = TTSFactory.create_engine_with_fallback(
    engine_names=None,  # Используем config.tts.engines_priority
    config=config,
    logger=logger
)
```

### Во время выполнения
```python
# Озвучить текст (выберет лучший доступный движок)
tts_engine.speak("Привет мир!")

# Потоковый синтез (для streaming ответов от LLM)
tts_engine.speak_streaming("Это ")
tts_engine.speak_streaming("потоковый ")
tts_engine.speak_streaming("синтез.")
tts_engine.flush_buffer()

# Остановить
tts_engine.stop()
```

### Fallback в действии
1. **Попытка Silero** → Если недоступна (нет torch, интернета и т.д.)
2. **Попытка Bark** → Если не установлена/загружена
3. **Используем SAPI5** → Windows встроенный, всегда доступен

Каждый переход логируется и отслеживается.

---

## ⚙️ Конфигурация

### Изменить приоритет
```json
{
  "tts": {
    "engines_priority": ["bark", "silero", "sapi"]  // Bark первым
  }
}
```

### Отключить движок
```json
{
  "tts": {
    "engines": {
      "silero": {
        "enabled": false  // Пропустить Silero
      }
    }
  }
}
```

### SAPI настройки
```json
{
  "tts": {
    "sapi": {
      "rate": 150,      // Скорость: 50-200
      "volume": 100,    // Громкость: 0-100
      "voice": null     // null = система по умолчанию
    }
  }
}
```

### Bark настройки
```json
{
  "tts": {
    "bark": {
      "voice": "v2/multilingual_00",  // Выбор голоса
      "model_size": "small"            // small или full
    }
  }
}
```

---

## 🧪 Установка и тестирование

### 1. Полная установка
```bash
INSTALL.bat
```

Загрузит:
- ✅ Python 3.11/3.12 зависимости
- ✅ Silero модель (первый запуск ~2-5 мин)
- ✅ Bark (lazy load, на первый синтез)
- ✅ pyttsx3 (fallback)

### 2. Быстрая проверка TTS
```bash
python test_tts_fallback_chain.py
```

### 3. Запуск приложения
```bash
LAUNCH.bat
```

---

## 🚨 Решение проблем

### Silero не загружается
```bash
# Принудительная загрузка модели
python -c "import torch; torch.hub.load('snakers4/silero-models', 'silero_tts', language='ru', speaker='v3_1_ru')"
```

### Bark очень медленно
Это нормально! Bark большая модель. Используйте `model_size: "small"` в конфиге.

```json
{
  "tts": {
    "bark": {
      "model_size": "small"  // Меньше памяти и быстрее
    }
  }
}
```

### SAPI5 не работает на Windows
Установите pyttsx3:
```bash
pip install pyttsx3
```

Если и это не помогает, используйте fallback на Silero/Bark.

### Python 3.13 + PyAudio
PyAudio несовместим с 3.13. Используйте Python 3.11 или 3.12.

---

## 📝 Изменения файлов

| Файл | Изменение |
|------|-----------|
| `modules/tts_factory.py` | ✅ Переписан с приоритизацией fallback |
| `modules/system_tts.py` | ✅ **НОВЫЙ** - SAPI5 TTS Engine |
| `requirements.txt` | ✅ Добавлены bark-ml, pyttsx3 |
| `config/config.json` | ✅ Добавлены engines_priority, SAPI настройки |
| `INSTALL.bat` | ✅ Добавлена загрузка Silero модели |
| `test_tts_fallback_chain.py` | ✅ **НОВЫЙ** - тестирование цепочки |

---

## 🎯 Итоговый порядок TTS

```
┌─────────────────────────────────────┐
│ Arvis TTS Fallback Chain (v1.5.2)   │
├─────────────────────────────────────┤
│                                     │
│ 1️⃣  SILERO (Primary)                │
│     • Fast (~1-3 сек/предложение)  │
│     • Russian + English              │
│     • Offline                        │
│                                     │
│     ↓ [if unavailable]              │
│                                     │
│ 2️⃣  BARK (Secondary)                │
│     • Quality, multilingual          │
│     • Slower (~5-10 сек)             │
│     • Offline                        │
│                                     │
│     ↓ [if unavailable]              │
│                                     │
│ 3️⃣  SAPI5 (Fallback)               │
│     • Windows native TTS             │
│     • Always available              │
│     • System voices                 │
│                                     │
└─────────────────────────────────────┘
```

---

**Версия**: 1.5.2  
**Дата**: 26.10.2025  
**Статус**: Production-ready ✅
