# 🤝 Contributing to Arvis AI Assistant

Спасибо за ваш интерес к развитию Arvis! Мы приветствуем вклад от сообщества и ценим каждое предложение.

## 📋 Содержание

- [Кодекс поведения](#кодекс-поведения)
- [Как я могу помочь?](#как-я-могу-помочь)
- [Процесс разработки](#процесс-разработки)
- [Стиль кода](#стиль-кода)
- [Тестирование](#тестирование)
- [Документация](#документация)

## 📜 Кодекс поведения

Участвуя в этом проекте, вы соглашаетесь соблюдать наш [Кодекс поведения](CODE_OF_CONDUCT.md). Пожалуйста, прочтите его перед началом работы.

## 🎯 Как я могу помочь?

### 🐛 Сообщить об ошибке

1. Проверьте, не была ли ошибка уже [зарегистрирована](https://github.com/Fat1ms/Arvis-Sentenel/issues)
2. Используйте шаблон для создания issue
3. Предоставьте максимально подробную информацию:
   - Версия Arvis (см. `version.py`)
   - Операционная система и версия Python
   - Шаги для воспроизведения
   - Ожидаемое и фактическое поведение
   - Логи из папки `logs/` (удалите личные данные и API ключи!)

### 💡 Предложить улучшение

1. Проверьте существующие [issues](https://github.com/Fat1ms/Arvis-Sentenel/issues) и [discussions](https://github.com/Fat1ms/Arvis-Sentenel/discussions)
2. Создайте Feature Request через шаблон
3. Опишите:
   - Проблему, которую решает ваше предложение
   - Предлагаемое решение
   - Альтернативы, которые вы рассматривали

### 🔧 Исправить ошибку или добавить функцию

См. [Процесс разработки](#процесс-разработки) ниже.

## 🚀 Процесс разработки

### 1. Fork и клонирование

```bash
# Fork через GitHub UI, затем:
git clone https://github.com/YOUR-USERNAME/Arvis-Sentenel.git
cd Arvis-Sentenel
git remote add upstream https://github.com/Fat1ms/Arvis-Sentenel.git
```

### 2. Настройка окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Установка dev-зависимостей
pip install -r requirements-dev.txt  # если существует
```

### 3. Создание ветки

```bash
git checkout -b feature/your-feature-name
# или
git checkout -b fix/issue-number-description
```

**Правила именования веток:**

- `feature/` — новая функциональность
- `fix/` — исправление ошибки
- `docs/` — изменения в документации
- `refactor/` — рефакторинг без изменения функциональности
- `test/` — добавление или исправление тестов

### 4. Разработка

- Следуйте [стилю кода](#стиль-кода)
- Пишите понятные commit messages
- Покрывайте код тестами
- Обновляйте документацию при необходимости

### 5. Коммит изменений

```bash
git add .
git commit -m "type: краткое описание изменений

Более подробное описание (опционально):
- Что было изменено
- Почему было изменено
- Ссылки на issues"
```

**Типы коммитов:**

- `feat:` — новая функциональность
- `fix:` — исправление ошибки
- `docs:` — изменения в документации
- `style:` — форматирование кода (без изменения логики)
- `refactor:` — рефакторинг
- `test:` — добавление тестов
- `chore:` — обновление зависимостей, конфигурации и т.д.

### 6. Отправка Pull Request

```bash
# Синхронизация с upstream
git fetch upstream
git rebase upstream/main

# Отправка в ваш fork
git push origin feature/your-feature-name
```

Затем создайте Pull Request через GitHub UI:

1. Заполните все поля шаблона PR
2. Свяжите с соответствующими issues (используйте `Closes #123`)
3. Дождитесь review
4. Внесите запрошенные изменения при необходимости

## 🎨 Стиль кода

### Python

Мы следуем **PEP 8** с небольшими модификациями:

```python
# Импорты
import os
import sys
from typing import Optional, List, Dict

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget

# Константы
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# Классы
class MyClass:
    """Docstring описывающий класс."""

    def __init__(self, param: str):
        """Инициализация класса.

        Args:
            param: Описание параметра
        """
        self.param = param

    def my_method(self) -> Optional[str]:
        """Метод с типизацией."""
        return self.param

# Функции
def my_function(arg1: int, arg2: str = "default") -> bool:
    """Краткое описание.

    Args:
        arg1: Описание аргумента 1
        arg2: Описание аргумента 2

    Returns:
        Описание возвращаемого значения
    """
    pass
```

**Основные правила:**

- Отступы: 4 пробела
- Максимальная длина строки: 120 символов (для кода), 80 для docstrings
- Используйте type hints
- Пишите docstrings для всех публичных классов/методов/функций
- Имена переменных: `snake_case`
- Имена классов: `PascalCase`
- Константы: `UPPER_SNAKE_CASE`

### Линтеры

```bash
# Форматирование
black . --line-length 120

# Проверка стиля
flake8 . --max-line-length 120

# Сортировка импортов
isort .

# Статическая проверка типов (опционально)
mypy src/ modules/ --ignore-missing-imports
```

### Git

- Пишите коммиты на английском или русском (проект на русском)
- Один коммит = одна логическая единица изменений
- Избегайте коммитов типа "fix typo" после PR — используйте `git commit --amend` или `git rebase -i`

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest tests/

# С покрытием
pytest --cov=src --cov=modules tests/

# Конкретный тест
pytest tests/test_arvis.py::test_specific_function
```

### Написание тестов

- Размещайте тесты в `tests/`
- Имя файла: `test_<module_name>.py`
- Имя теста: `test_<what_it_tests>`
- Используйте fixtures для повторяющейся настройки
- Покрывайте edge cases и error paths

```python
# tests/test_example.py
import pytest
from modules.example import ExampleClass

@pytest.fixture
def example_instance():
    """Fixture для создания экземпляра."""
    return ExampleClass(param="test")

def test_example_method(example_instance):
    """Тест метода example."""
    result = example_instance.example_method()
    assert result is True

def test_example_error_handling():
    """Тест обработки ошибок."""
    with pytest.raises(ValueError):
        ExampleClass(param=None)
```

## 📖 Документация

### Обновление документации

При добавлении новых функций обновляйте:

- `README.md` — для значимых изменений
- Docstrings в коде
- `.github/copilot-instructions.md` — для архитектурных изменений
- Changelog (будет создан в Фазе 1)

### Стиль документации

- Используйте Markdown
- Добавляйте примеры кода
- Включайте скриншоты для UI изменений
- Документируйте API и конфигурационные опции

## 🔒 Безопасность

### Важно

- **НЕ коммитьте** API ключи, токены, пароли
- **НЕ коммитьте** персональные данные
- Используйте `.env` для локальных секретов
- Добавляйте чувствительные файлы в `.gitignore`

### Обнаружили уязвимость?

**НЕ создавайте публичный issue!** См. [SECURITY.md](SECURITY.md) для инструкций по responsible disclosure.

## ❓ Вопросы?

- 💬 [GitHub Discussions](https://github.com/Fat1ms/Arvis-Sentenel/discussions) — общие вопросы
- 🐛 [GitHub Issues](https://github.com/Fat1ms/Arvis-Sentenel/issues) — баги и feature requests
- 📧 Email: [ваш контакт] — приватные вопросы

## 📝 Лицензия

Внося вклад в Arvis, вы соглашаетесь, что ваш код будет распространяться под [MIT License](LICENSE).

---

**Спасибо за ваш вклад! 🎉**

Вместе мы делаем Arvis лучше!
