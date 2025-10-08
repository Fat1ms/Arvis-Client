# Python 3.13 Compatibility Guide

## ⚠️ Проблема совместимости

**Arvis НЕ полностью совместим с Python 3.13** из-за зависимости **PyAudio 0.2.13**.

### Причина
Python 3.13 удалил устаревший атрибут `pkgutil.ImpImporter`, который используется старыми версиями setuptools при компиляции PyAudio из исходников. Это приводит к ошибке:

```
AttributeError: module 'pkgutil' has no attribute 'ImpImporter'
```

---

## ✅ Рекомендуемое решение

### Используйте Python 3.11 или 3.12

1. **Удалите Python 3.13**
2. **Установите Python 3.11.9 или 3.12.x** с [python.org](https://www.python.org/downloads/)
3. **Запустите `setup_arvis.bat`** заново

---

## 🔧 Альтернативные решения для Python 3.13

Если вы настаиваете на использовании Python 3.13, попробуйте следующие варианты:

### Вариант 1: Предкомпилированный wheel (Windows)

1. Скачайте совместимый wheel с [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
   - Например: `PyAudio-0.2.14-cp313-cp313-win_amd64.whl`

2. Установите wheel вручную:
   ```powershell
   venv\Scripts\activate
   pip install PyAudio-0.2.14-cp313-cp313-win_amd64.whl
   ```

### Вариант 2: Использовать pipwin (может не работать)

```powershell
venv\Scripts\activate
pip install pipwin
pipwin install pyaudio
```

### Вариант 3: Работа БЕЗ PyAudio (ограниченная функциональность)

Arvis может работать с **ограниченными аудио-возможностями** без PyAudio:
- ✅ TTS (Silero) будет работать
- ✅ LLM и текстовый интерфейс работают полностью
- ❌ STT (Vosk) и wake word detection **НЕ** будут работать

**Запуск без PyAudio:**
1. Закомментируйте `import pyaudio` в:
   - `modules/stt_engine.py`
   - `modules/wake_word_detector.py`
2. Используйте только текстовый ввод (без голосовых команд)

---

## 📝 Автоматическая установка через setup_arvis.bat

Скрипт `setup_arvis.bat` автоматически пытается:
1. Установить PyAudio через pip
2. Если не удалось → попробовать pipwin
3. Если не удалось → показать инструкции по ручной установке

**Arvis продолжит работу** даже без PyAudio, но с ограничениями.

---

## 🐛 Отладка проблем

### Проверить версию Python:
```powershell
python --version
```

### Проверить установленные пакеты:
```powershell
venv\Scripts\activate
pip list | findstr -i "pyaudio torch vosk"
```

### Запустить диагностику:
```powershell
venv\Scripts\activate
python diagnose_startup.py
```

---

## 🔄 Миграция с Python 3.13 → 3.11/3.12

1. **Удалите виртуальное окружение:**
   ```powershell
   rmdir /s /q venv
   ```

2. **Переустановите Python 3.11 или 3.12**

3. **Запустите установку заново:**
   ```powershell
   setup_arvis.bat
   ```

---

## 📌 Статус поддержки версий Python

| Версия Python | Статус | Примечание |
|---------------|--------|------------|
| 3.8 - 3.10    | ⚠️ Не рекомендуется | Старые версии |
| **3.11.x**    | ✅ **Рекомендуется** | Стабильная работа |
| **3.12.x**    | ✅ **Рекомендуется** | Полная поддержка |
| 3.13.x        | ❌ Не поддерживается | PyAudio несовместим |

---

## 🆘 Помощь

Если проблемы остаются:
1. Создайте issue на [GitHub](https://github.com/Fat1ms/Arvis-Sentenel/issues)
2. Приложите вывод `diagnose_startup.py`
3. Укажите версию Python: `python --version`
