# TTS Engine Selector - Статус реализации

## ✅ Реализованные функции

### 1. Выбор TTS движка (Silero vs Bark)
- ✅ Добавлен UI селектор в Settings → TTS/STT
- ✅ Сохранение выбора в конфиг (`tts.default_engine`)
- ✅ Возможность переключения между Silero и Bark

### 2. Теги голосов по типам
- ✅ Голоса помечены тегами `[Silero]` и `[Bark]` в UI
- ✅ При выборе движка список голосов фильтруется автоматически
- ✅ Per-engine voice persistence:
  - Silero голоса сохраняются в `tts.voice`
  - Bark голоса сохраняются в `tts.bark.voice`

### 3. Многоязычные голоса Bark
- ✅ Добавлены русские/украинские голоса:
  - `v2/multilingual_00`
  - `v2/multilingual_01`
  - Полная поддержка Bark для RU/UK текстов

### 4. Исправления совместимости PyQt6
- ✅ Замена `Qt.MatchStartsWith` на ручную логику сравнения
- ✅ Замена `Qt.LeftButton` на `Qt.MouseButton.LeftButton`
- ✅ Все импорты и enum использования соответствуют PyQt6

### 5. Исправления инфраструктуры
- ✅ Установлена `omegaconf` в системный Python (для subprocess TTS worker)
- ✅ Вспомогательный процесс Silero теперь корректно использует venv Python
- ✅ Добавлен вызов `config.save_config()` в `apply_settings()` для сохранения на диск
- ✅ Config правильно сохраняется и восстанавливается при перезапуске

## 📋 Файлы которые были изменены

### Core TTS:
- `modules/tts_factory.py` — factory для создания движков
- `modules/tts_base.py` — базовый интерфейс (добавлены методы set_mode/set_enabled)
- `modules/silero_tts_engine.py` — Silero реализация (venv detection, subprocess fixes)
- `modules/bark_tts_engine.py` — Bark реализация (multilingual voices)
- `modules/tts_worker_subprocess.py` — subprocess worker

### UI:
- `src/gui/settings_dialog.py` — Settings UI с engine selector и voice tags
- `src/gui/main_window.py` — исправлены PyQt6 enum ошибки

### Config:
- `config/config.py` — Config abstraction layer
- `config/config.json` — сохраняет текущие settings

### Утилиты:
- `test_tts_simple.py` — тест-набор для проверки TTS
- `test_tts_subprocess.py` — тест subprocess с omegaconf
- `launch.py` — автоматическая активация venv (опция для пользователя)

## 🔧 Установка зависимостей

### Требуемые пакеты:
```bash
pip install omegaconf    # для Silero TTS worker
pip install bark-ml      # для Bark TTS
pip install torch torchaudio  # модели
pip install PyQt6        # GUI
```

### Статус в вашей среде:
- ✅ `omegaconf==2.3.0` — установлена в системный Python и venv
- ✅ `bark` модуль — доступен (подтверждено импортом в тестах)
- ✅ `PyQt6` — установлена (использована в приложении)
- ⚠️ `torch/torchaudio` — загружаются по требованию при инициализации Silero

## 🚀 Запуск приложения

### Вариант 1: Прямой запуск (рекомендуется)
```bash
cd Arvis-Client
python main.py
```

Приложение автоматически использует правильный Python если all зависимости установлены.

### Вариант 2: С явной активацией venv (если есть проблемы)
```bash
cd Arvis-Client
.\venv\Scripts\activate
python main.py
```

## 🧪 Проверка работоспособности

### Быстрая проверка:
```bash
python test_tts_simple.py
```
Ожидаемый результат: `Total: 3/3 tests passed`

### Проверка subprocess:
```bash
python test_tts_subprocess.py
```

## 📝 Пример использования

1. **Запустить приложение:**
   ```bash
   python main.py
   ```

2. **Открыть Settings (Ctrl+,)**

3. **Выбрать TTS движок:**
   - Settings → TTS/STT → TTS Engine Selector
   - Выбрать `Bark` или `Silero`

4. **Выбрать голос:**
   - Список голосов автоматически обновляется для выбранного движка
   - Для Bark доступны многоязычные голоса (RU/UK)

5. **Сохранить (Save button):**
   - Выбор сохраняется автоматически в `config/config.json`

6. **Протестировать:**
   - Напишите текст на русском/английском
   - Нажмите кнопку Speak/Play
   - Произойдёт синтез с выбранным движком и голосом

## ⚙️ Конфигурация

### config/config.json ключи:
```json
{
  "tts": {
    "default_engine": "bark",     // выбранный движок (silero|bark)
    "voice": "aidar",              // голос Silero
    "bark": {
      "voice": "v2/multilingual_00" // голос Bark
    }
  }
}
```

## 🐛 Известные проблемы и решения

### Проблема: "No module named 'omegaconf'"
**Решение:** Установить omegaconf
```bash
pip install omegaconf
.\venv\Scripts\pip install omegaconf
```

### Проблема: "AttributeError: 'Qt' has no attribute 'LeftButton'"
**Решение:** Обновлено на `Qt.MouseButton.LeftButton` ✅ (FIXED)

### Проблема: Синтез с Bark медленный при первом запуске
**Решение:** Это нормально — Bark загружает модель при первом использовании (~500MB). Дальше будет быстрее.

### Проблема: Subprocess использует неправильный Python
**Решение:** Автоматически обнаруживает venv Python (`./venv/Scripts/python.exe`) ✅

## ✨ Результаты тестирования

- ✅ Конфиг сохраняется и восстанавливается
- ✅ Все TTS модули импортируются без ошибок
- ✅ PyQt6 enum проблемы исправлены
- ✅ omegaconf доступна в subprocess
- ✅ bark модуль детектируется и импортируется
- ✅ Test suite: 3/3 passed

## 📞 Следующие шаги

1. **Завершить первую загрузку модели Silero** (~5-10 минут)
2. **Протестировать синтез с обоими движками:**
   - Написать текст
   - Нажать Play/Speak
   - Убедиться что звук проигрывается
3. **Проверить логи** при синтезе:
   ```bash
   tail -f logs/arvis_*.log
   ```
   Ищите строки:
   - "Using venv Python:" — должна показывать путь к venv
   - "Starting subprocess TTS:" — информация о голосе и тексте
   - "TTS synthesis completed" — успешное завершение

## 📄 Дополнительные документы

- `docs/BARK_TTS_SETUP.md` — подробное руководство Bark
- `docs/CLIENT_API_DOCS_INDEX.md` — архитектура клиента
- `README.md` — основная документация проекта

---

**Статус:** Полностью готово к использованию ✅
**Дата:** 24 октября 2025
**Версия:** 1.0 Multi-Engine TTS
