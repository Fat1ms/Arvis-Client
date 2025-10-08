# Установка PyAudio для Python 3.13 (Windows)

## Проблема
PyAudio 0.2.13 не компилируется на Python 3.13 из-за удаления `pkgutil.ImpImporter`.

## Решение 1: Предкомпилированный wheel (РЕКОМЕНДУЕТСЯ)

### Шаг 1: Скачайте wheel
Перейдите на [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

Найдите файл для Python 3.13:
- **PyAudio‑0.2.14‑cp313‑cp313‑win_amd64.whl** (64-bit Windows)
- **PyAudio‑0.2.14‑cp313‑cp313‑win32.whl** (32-bit Windows)

### Шаг 2: Установите wheel
```powershell
# Активируйте виртуальное окружение
venv\Scripts\activate

# Перейдите в папку с загруженным файлом
cd C:\Users\YourName\Downloads

# Установите wheel
pip install PyAudio-0.2.14-cp313-cp313-win_amd64.whl
```

### Шаг 3: Проверьте установку
```powershell
python -c "import pyaudio; print('PyAudio OK')"
```

Если видите `PyAudio OK` — всё готово! ✅

---

## Решение 2: Компиляция из исходников (для продвинутых)

### Требования:
- Visual Studio 2022 с C++ Build Tools
- PortAudio SDK

### Шаги:

1. **Установите Visual Studio Build Tools:**
   https://visualstudio.microsoft.com/downloads/
   - Выберите "Desktop development with C++"

2. **Скачайте PortAudio:**
   http://www.portaudio.com/download.html
   - Распакуйте в `C:\portaudio`

3. **Соберите PyAudio:**
   ```powershell
   # Клонируйте репозиторий PyAudio
   git clone https://github.com/intxcc/pyaudio_portaudio.git
   cd pyaudio_portaudio

   # Соберите и установите
   python setup.py install
   ```

---

## Решение 3: Использование pipwin (может не работать)

```powershell
venv\Scripts\activate
pip install pipwin
pipwin install pyaudio
```

⚠️ **Примечание:** pipwin может быть устаревшим для Python 3.13

---

## Решение 4: Работа БЕЗ PyAudio

Если вы не используете голосовой ввод (STT/Wake Word):

1. **Закомментируйте импорты PyAudio:**

   В файле `modules/stt_engine.py`:
   ```python
   # import pyaudio
   ```

   В файле `modules/wake_word_detector.py`:
   ```python
   # import pyaudio
   ```

2. **Отключите голосовые функции в config.json:**
   ```json
   {
     "stt": {
       "enabled": false
     },
     "wake_word": {
       "enabled": false
     }
   }
   ```

3. **Используйте только текстовый ввод** ✅

---

## Проверка установки

### 1. Проверить версию Python:
```powershell
python --version
```

### 2. Проверить PyAudio:
```powershell
venv\Scripts\activate
python -c "import pyaudio; print(pyaudio.get_portaudio_version())"
```

Ожидаемый вывод: `1900` (или другое число версии PortAudio)

### 3. Запустить диагностику Arvis:
```powershell
venv\Scripts\activate
python diagnose_startup.py
```

---

## Альтернатива: Downgrade на Python 3.11/3.12

Самый надежный способ — использовать **Python 3.11 или 3.12**:

```powershell
# Удалите виртуальное окружение
rmdir /s /q venv

# Установите Python 3.11 или 3.12
# https://www.python.org/downloads/

# Запустите установку заново
setup_arvis.bat
```

---

## Помощь

Если проблемы остаются:
- [Создайте issue на GitHub](https://github.com/Fat1ms/Arvis-Sentenel/issues)
- Укажите версию Python: `python --version`
- Приложите вывод: `pip list | findstr -i pyaudio`
