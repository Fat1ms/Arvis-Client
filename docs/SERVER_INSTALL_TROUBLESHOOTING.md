# 🔧 Решение проблем установки Arvis на сервере/ноутбуке

## Диагностика перед установкой

**Запустите диагностику для определения проблемы:**

```powershell
diagnose_setup.bat
```

Скрипт проверит:
- ✅ Наличие и версию Python
- ✅ Совместимость с Arvis (3.11/3.12 рекомендуется, 3.13 НЕ поддерживается)
- ✅ Работоспособность pip и venv
- ✅ Совместимость существующего venv с текущим Python
- ✅ Права доступа и структуру проекта
- ✅ Ollama (опционально)

---

## Проблема 1: Python не найден

### Симптомы:
```
❌ Python не найден!
'python' is not recognized as an internal or external command
```

### Решение:

1. **Установите Python 3.11.9 или 3.12.x:**
   - Скачайте с [python.org/downloads](https://www.python.org/downloads/)
   - ⚠️ **НЕ УСТАНАВЛИВАЙТЕ Python 3.13** (несовместим с PyAudio)

2. **При установке обязательно отметьте:**
   - ☑️ **"Add Python to PATH"** (критично!)
   - ☑️ "pip"
   - ☑️ "tcl/tk and IDLE"

3. **Перезагрузите компьютер**

4. **Проверьте установку:**
   ```powershell
   python --version
   python -m pip --version
   ```

5. **Запустите установку:**
   ```powershell
   setup_arvis.bat
   ```

---

## Проблема 2: Python 3.13 установлен

### Симптомы:
```
⚠️  Python 3.13 НЕ ПОДДЕРЖИВАЕТСЯ!
PyAudio несовместим с Python 3.13
AttributeError: module 'pkgutil' has no attribute 'ImpImporter'
```

### Причина:
Python 3.13 удалил `pkgutil.ImpImporter`, который нужен для компиляции PyAudio.

### Решение (РЕКОМЕНДУЕТСЯ):

1. **Удалите Python 3.13:**
   - Windows: Панель управления → Программы → Удалить Python 3.13

2. **Установите Python 3.11.9 или 3.12.x:**
   - [Python 3.11.9](https://www.python.org/downloads/release/python-3119/)
   - [Python 3.12.x](https://www.python.org/downloads/)

3. **Удалите старое виртуальное окружение:**
   ```powershell
   rmdir /s /q venv
   ```

4. **Запустите установку заново:**
   ```powershell
   setup_arvis.bat
   ```

### Альтернатива (для опытных пользователей):

Если вы хотите оставить Python 3.13, используйте предкомпилированный wheel:

1. **Скачайте PyAudio wheel:**
   - [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
   - Выберите: `PyAudio-0.2.14-cp313-cp313-win_amd64.whl`

2. **Установите вручную:**
   ```powershell
   venv\Scripts\activate
   pip install путь\к\PyAudio-0.2.14-cp313-cp313-win_amd64.whl
   ```

📖 **Подробнее:** `docs\PYTHON_313_COMPATIBILITY.md`

---

## Проблема 3: Несовместимое виртуальное окружение

### Симптомы:
```
❌ venv НЕ совместимо с Python 3.12
No Python at '"C:\Users\...\Python311\python.exe'
Fatal error in launcher: Unable to create process
```

### Причина:
Виртуальное окружение создано с другой версией Python (например, venv от Python 3.11, а сейчас установлен 3.12).

### Решение 1 (автоматическое):

```powershell
fix_venv.bat
```

### Решение 2 (вручную):

1. **Закройте все терминалы и VS Code**

2. **Удалите старое окружение:**
   ```powershell
   rmdir /s /q venv
   ```

3. **Создайте новое:**
   ```powershell
   python -m venv venv
   ```

4. **Запустите установку:**
   ```powershell
   setup_arvis.bat
   ```

📖 **Подробнее:** `docs\VENV_FIX_GUIDE.md`

---

## Проблема 4: Ошибка установки зависимостей

### Симптомы:
```
❌ Ошибка установки зависимостей
pip install -r requirements.txt FAILED
ERROR: Could not install packages due to an OSError
```

### Возможные причины:

#### 4.1 Недостаточно прав доступа

**Решение:**
- Запустите `setup_arvis.bat` **от имени администратора**
- ПКМ → "Запустить от имени администратора"

#### 4.2 Антивирус блокирует установку

**Решение:**
- Временно отключите антивирус/Windows Defender
- Добавьте папку проекта в исключения антивируса
- Запустите установку снова

#### 4.3 Недостаточно места на диске

**Проверка:**
```powershell
dir C:\ | findstr "bytes free"
```

**Требования:**
- Минимум **2 GB** свободного места
- Рекомендуется **5 GB+** (для моделей Vosk)

#### 4.4 Проблемы с сетью (pip не может скачать пакеты)

**Решение:**

1. **Проверьте интернет-соединение**

2. **Используйте другое зеркало pip:**
   ```powershell
   venv\Scripts\activate
   pip install -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **Установите критичные пакеты вручную:**
   ```powershell
   venv\Scripts\activate
   pip install PyQt5==5.15.10
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   pip install requests vosk sounddevice
   ```

---

## Проблема 5: PyAudio не устанавливается

### Симптомы:
```
⚠️  PyAudio не установлен через pip
error: Microsoft Visual C++ 14.0 or greater is required
```

### Решение 1 (через pipwin):

```powershell
venv\Scripts\activate
pip install pipwin
pipwin install pyaudio
```

### Решение 2 (предкомпилированный wheel):

1. **Скачайте wheel для вашей версии Python:**
   - [PyAudio Wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
   - Python 3.11: `PyAudio-0.2.14-cp311-cp311-win_amd64.whl`
   - Python 3.12: `PyAudio-0.2.14-cp312-cp312-win_amd64.whl`

2. **Установите:**
   ```powershell
   venv\Scripts\activate
   pip install путь\к\PyAudio-0.2.14-cpXXX-cpXXX-win_amd64.whl
   ```

### Решение 3 (использовать скрипт):

```powershell
fix_pyaudio.bat
```

### ⚠️ Важно:
Arvis может работать **без PyAudio**, но с ограничениями:
- ✅ Текстовый ввод работает
- ✅ TTS (озвучка) работает
- ❌ STT (распознавание речи) НЕ работает
- ❌ Wake word detection НЕ работает

📖 **Подробнее:** `docs\PYAUDIO_PYTHON313_INSTALL.md`

---

## Проблема 6: Torch (PyTorch) не устанавливается

### Симптомы:
```
ERROR: Could not find a version that satisfies the requirement torch>=2.0.0
```

### Решение (установка CPU версии):

```powershell
venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Для GPU (NVIDIA CUDA 11.8):

```powershell
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## Проблема 7: Ollama не работает

### Симптомы:
```
⚠️  Ollama не запущен
Connection refused: localhost:11434
```

### Решение:

1. **Установите Ollama:**
   - [ollama.ai](https://ollama.ai)
   - Скачайте Windows installer

2. **Запустите Ollama:**
   ```powershell
   ollama serve
   ```

3. **Скачайте модель:**
   ```powershell
   ollama pull llama3.2
   ```

4. **Проверьте:**
   ```powershell
   ollama list
   curl http://localhost:11434/api/version
   ```

📖 **Управление Ollama:**
```powershell
ollama_manager.bat
```

---

## Проблема 8: Модели Vosk не скачиваются

### Симптомы:
```
❌ Ошибка загрузки моделей Vosk
Invoke-WebRequest: Unable to connect to the remote server
```

### Решение:

1. **Скачайте модели вручную:**

   Для русского языка:
   - [vosk-model-small-ru-0.22.zip](https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip) (50 MB)
   - [vosk-model-ru-0.42.zip](https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip) (2.5 GB, опционально)

2. **Распакуйте в папку `models/`:**
   ```
   models/
   ├── vosk-model-small-ru-0.22/
   │   ├── am/
   │   ├── conf/
   │   ├── graph/
   │   └── ...
   ```

3. **Проверьте структуру:**
   ```powershell
   dir models\vosk-model-small-ru-0.22
   ```

---

## Проблема 9: Ошибки при запуске после установки

### Симптомы:
```
ModuleNotFoundError: No module named 'PyQt5'
ImportError: DLL load failed while importing _internal
```

### Решение:

1. **Проверьте, что venv активирован:**
   ```powershell
   venv\Scripts\activate
   python -c "import sys; print(sys.prefix)"
   # Должно указать на venv\
   ```

2. **Переустановите критичные пакеты:**
   ```powershell
   pip install --force-reinstall PyQt5==5.15.10
   ```

3. **Используйте правильный скрипт запуска:**
   ```powershell
   start_arvis.bat
   ```
   (НЕ запускайте `python main.py` напрямую без активации venv)

---

## Проблема 10: "Permission Denied" / "Access Denied"

### Симптомы:
```
PermissionError: [WinError 5] Access is denied
```

### Решение:

1. **Закройте все терминалы и редакторы**
   - VS Code
   - PyCharm
   - Все окна PowerShell/CMD

2. **Перезагрузите компьютер**

3. **Запустите от имени администратора:**
   - ПКМ на `setup_arvis.bat` → "Запустить от имени администратора"

4. **Проверьте антивирус:**
   - Добавьте папку проекта в исключения
   - Временно отключите "Контроль приложений" / "Sandbox"

---

## Общие рекомендации для серверов/ноутбуков

### Требования:
- **OS:** Windows 10/11 (64-bit)
- **RAM:** Минимум 8 GB (рекомендуется 16 GB)
- **Диск:** 5 GB+ свободного места
- **Python:** 3.11.9 или 3.12.x (НЕ 3.13!)
- **Интернет:** для установки зависимостей и моделей

### Чеклист установки:

1. ✅ Установите Python 3.11/3.12 с "Add to PATH"
2. ✅ Перезагрузите компьютер
3. ✅ Запустите диагностику: `diagnose_setup.bat`
4. ✅ Исправьте найденные проблемы
5. ✅ Запустите установку: `setup_arvis.bat`
6. ✅ Установите Ollama (опционально, но рекомендуется)
7. ✅ Проверьте работу: `status_check.bat`
8. ✅ Запустите: `start_arvis.bat`

### Полезные команды:

```powershell
# Диагностика установки
diagnose_setup.bat

# Полная установка
setup_arvis.bat

# Исправление venv
fix_venv.bat

# Исправление PyAudio
fix_pyaudio.bat

# Пересоздание venv
recreate_venv.bat

# Проверка статуса
status_check.bat

# Диагностика производительности
diagnose_performance.bat

# Управление Ollama
ollama_manager.bat
```

---

## Получение помощи

Если проблема не решена:

1. **Запустите диагностику и сохраните лог:**
   ```powershell
   diagnose_setup.bat
   ```
   Лог будет сохранён в `setup_diagnostic_*.log`

2. **Откройте Issue на GitHub:**
   - Приложите файл лога
   - Укажите версию Python: `python --version`
   - Укажите версию Windows: `winver`

3. **Проверьте документацию:**
   - `docs/PYTHON_313_COMPATIBILITY.md`
   - `docs/PYAUDIO_PYTHON313_INSTALL.md`
   - `docs/VENV_FIX_GUIDE.md`
   - `QUICKFIX_PYTHON313.md`

---

## Известные проблемы

| Проблема | Версия Python | Решение |
|----------|---------------|---------|
| PyAudio не компилируется | 3.13 | Используйте 3.11/3.12 или предкомпилированный wheel |
| venv несовместим | Любая (после смены версии) | `fix_venv.bat` |
| Torch не устанавливается | Любая | Используйте `--index-url` с PyTorch repo |
| DLL load failed | 3.11+ | Переустановите Visual C++ Redistributable |
| ModuleNotFoundError | Любая | Активируйте venv перед запуском |

---

**Последнее обновление:** Октябрь 2025  
**Версия Arvis:** 1.5.1+
