# 🔄 Обновление v1.5.1 - Управление версиями и совместимость

## ✨ Новые возможности

### 1. Автоматическое управление версиями
- Централизованная система версий между клиентом и сервером
- Автоматическая проверка совместимости
- API эндпоинты для проверки версий

### 2. Улучшенный запуск сервера
- Исправлены все проблемы с зависимостями
- Улучшенные скрипты установки и запуска
- Диагностические инструменты

### 3. Мягкая совместимость
- Не нужно вручную совмещать версии на разных устройствах
- Автоматическая синхронизация
- Поддержка обратной совместимости

## 📦 Новые файлы

### Управление версиями:
- `utils/version_manager.py` - Менеджер версий
- `server/version.py` - Информация о версии сервера

### Скрипты запуска:
- `server/START.bat` - Быстрый запуск (НОВЫЙ!)
- `server/setup_server.bat` - Установка зависимостей
- `server/start_server.ps1` - PowerShell версия
- `server/check_server.ps1` - PowerShell диагностика

### Документация:
- `server/LAUNCH_SUCCESS.md` - Руководство по решению проблем
- `server/README_QUICKSTART.md` - Быстрый старт

## 🚀 Как использовать:

### Первый запуск (установка):
```bash
cd server
setup_server.bat
```

### Последующие запуски:
```bash
cd server
START.bat
```

### Проверка статуса:
```bash
cd server
check_server.bat
```

## 🔗 API эндпоинты версий:

### Информация о версии:
```
GET http://localhost:8000/version
```

Ответ:
```json
{
  "name": "Arvis Auth Server",
  "version": "1.5.1",
  "api_version": "v1",
  "min_client_version": "1.5.0"
}
```

### Проверка совместимости:
```
GET http://localhost:8000/version/check?client_version=1.5.1
```

Ответ:
```json
{
  "compatible": true,
  "message": "Версии совместимы",
  "server_version": "1.5.1",
  "client_version": "1.5.1"
}
```

## 🛠️ Технические детали:

### Исправленные зависимости:
- ❌ Удален: `python-cors==1.0.0` (не существует)
- ✅ Добавлен: `email-validator` (для Pydantic)
- ✅ Все пакеты обновлены до совместимых версий

### Система совместимости:
- Проверка мажорных версий (должны совпадать)
- Проверка минимальных требований
- Поддержка режимов: auto, strict, legacy

## 📝 Для разработчиков:

### Использование менеджера версий в коде:

```python
from utils.version_manager import get_version_manager

vm = get_version_manager()

# Получить версию клиента
client_version = vm.get_client_version()

# Проверить совместимость с сервером
is_compatible, message = vm.check_compatibility("1.5.1")

# Обновить информацию о версии сервера
vm.update_server_version("1.5.1")

# Установить режим совместимости
vm.set_compatibility_mode("auto")  # auto, strict, legacy
```

### Проверка версий на сервере:

```python
from server.version import check_client_compatibility

is_compatible, message = check_client_compatibility("1.5.1")
if not is_compatible:
    raise ValueError(f"Incompatible version: {message}")
```

## 🎯 Преимущества:

1. **Простота** - Один скрипт для запуска
2. **Надежность** - Автоматическая проверка всех зависимостей
3. **Совместимость** - Работает на всех устройствах без ручной настройки
4. **Диагностика** - Встроенные инструменты для поиска проблем
5. **Гибкость** - Поддержка разных режимов совместимости

## 📚 Документация:

- [Решение проблем запуска](server/LAUNCH_SUCCESS.md)
- [Быстрый старт](server/README_QUICKSTART.md)
- [Полная документация](server/README.md)

---

**Дата обновления:** 7 октября 2025  
**Версия:** 1.5.1  
**Статус:** ✅ Стабильная
