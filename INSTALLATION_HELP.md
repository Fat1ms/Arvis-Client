# 🚨 Не могу установить Arvis? Быстрая помощь

## Запустите диагностику

```powershell
diagnose_setup.bat
```

Скрипт автоматически найдёт проблему и покажет решение.

---

## Топ-5 проблем и решений

### 1️⃣ Python не найден
```powershell
❌ Python не найден!
```

**Решение:**
- Установите [Python 3.11.9](https://www.python.org/downloads/release/python-3119/) или [Python 3.12.x](https://www.python.org/downloads/)
- ⚠️ При установке отметьте **"Add Python to PATH"**
- Перезагрузите компьютер

---

### 2️⃣ Python 3.13 не поддерживается
```powershell
⚠️  Python 3.13 НЕ ПОДДЕРЖИВАЕТСЯ!
PyAudio несовместим с Python 3.13
```

**Решение:**
1. Удалите Python 3.13
2. Установите Python 3.11.9 или 3.12.x
3. Удалите venv: `rmdir /s /q venv`
4. Запустите: `setup_arvis.bat`

📖 **Подробнее:** [docs/PYTHON_313_COMPATIBILITY.md](docs/PYTHON_313_COMPATIBILITY.md)

---

### 3️⃣ Виртуальное окружение несовместимо
```powershell
❌ venv НЕ совместимо с текущей версией Python
```

**Решение:**
```powershell
fix_venv.bat
```

Или вручную:
```powershell
rmdir /s /q venv
setup_arvis.bat
```

---

### 4️⃣ PyAudio не устанавливается
```powershell
⚠️  PyAudio не установлен через pip
error: Microsoft Visual C++ 14.0 or greater is required
```

**Решение:**
```powershell
fix_pyaudio.bat
```

Или скачайте wheel вручную:
- [PyAudio для Python 3.11/3.12](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

📖 **Подробнее:** [docs/PYAUDIO_PYTHON313_INSTALL.md](docs/PYAUDIO_PYTHON313_INSTALL.md)

---

### 5️⃣ Ошибка установки зависимостей
```powershell
❌ Ошибка установки зависимостей
pip install -r requirements.txt FAILED
```

**Решения:**
- Запустите `setup_arvis.bat` **от имени администратора** (ПКМ → "Запустить от имени администратора")
- Временно отключите антивирус
- Проверьте интернет-соединение
- Освободите место на диске (нужно 2+ GB)

---

## Полное руководство

📖 **[docs/SERVER_INSTALL_TROUBLESHOOTING.md](docs/SERVER_INSTALL_TROUBLESHOOTING.md)**

Подробное описание всех проблем и решений с командами и скриншотами.

---

## Полезные команды

| Команда | Описание |
|---------|----------|
| `diagnose_setup.bat` | Автоматическая диагностика проблем |
| `setup_arvis.bat` | Полная установка |
| `fix_venv.bat` | Исправить виртуальное окружение |
| `fix_pyaudio.bat` | Установить PyAudio вручную |
| `recreate_venv.bat` | Пересоздать venv с нуля |
| `status_check.bat` | Проверить установленные компоненты |

---

## Минимальные требования

- **OS:** Windows 10/11 (64-bit)
- **Python:** 3.11.9 или 3.12.x (НЕ 3.13!)
- **RAM:** 8 GB минимум (рекомендуется 16 GB)
- **Диск:** 5 GB свободного места
- **Интернет:** для установки зависимостей

---

## Получить помощь

Если проблема не решена:

1. Запустите `diagnose_setup.bat` и сохраните лог
2. Откройте [Issue на GitHub](https://github.com/Fat1ms/Arvis-Sentenel/issues)
3. Приложите файл лога `setup_diagnostic_*.log`

---

**Последнее обновление:** Октябрь 2025  
**Версия:** 1.5.1+
