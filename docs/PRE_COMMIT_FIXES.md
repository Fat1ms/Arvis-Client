# 🔧 Pre-commit Hooks - Диагностика и исправления

**Дата:** 6 октября 2025  
**Статус:** 🔴 Требуется исправление

---

## 🚨 Обнаруженные проблемы

### 1. ❌ Trailing Whitespace (Исправлено автоматически)

**Проблема:** Пробелы в конце строк в нескольких файлах

**Затронутые файлы:**

- `main.py`
- `modules/calendar_module.py`
- `src/core/arvis_core.py`
- `modules/system_control.py`
- `utils/conversation_history.py`
- `src/gui/status_panel.py`
- `src/gui/main_window.py`
- `modules/search_module.py`

**Статус:** ✅ Автоматически исправлено pre-commit

**Действия:** Нет - хук автоматически очистил пробелы

---

### 2. ❌ Mixed Line Endings (Исправлено автоматически)

**Проблема:** Смешанные окончания строк (LF/CRLF) в файлах

**Затронутые файлы:**

- `src/core/arvis_core.py`
- `README.md`
- `docs/RELEASE_v1.3.3_COMMANDS.md`

**Статус:** ✅ Автоматически исправлено pre-commit

**Причина:** Работа в Windows с Git без правильной конфигурации

**Решение:**

```bash
# Настроить Git для правильной обработки line endings
git config --global core.autocrlf input
git config --global core.eol lf
```

---

### 3. ❌ YAML Syntax Error (Требует ручного исправления)

**Проблема:** Синтаксическая ошибка в `.github/workflows/ci.yml:149`

**Ошибка:**

```
mapping values are not allowed in this context
  in ".github/workflows/ci.yml", line 149, column 91
```

**Статус:** 🔴 Требует исправления

**Необходимо:** Проверить и исправить YAML файл вручную

---

## 🛠️ План исправления

### Этап 1: Исправление YAML файла

**Приоритет:** 🔴 Критичный

**Действия:**

1. Открыть `.github/workflows/ci.yml`
2. Перейти к строке 149
3. Проверить синтаксис YAML (возможно, лишние пробелы или неправильное выравнивание)
4. Использовать валидатор: <https://www.yamllint.com/>
5. Исправить и закоммитить

**Типичные проблемы YAML:**

- Неправильное выравнивание (должно быть 2 пробела)
- Двоеточие без пробела после него
- Кавычки не закрыты
- Специальные символы не экранированы

---

### Этап 2: Настройка Git для Windows

**Приоритет:** 🟡 Высокий

**Действия:**

```powershell
# Глобальная настройка для всех репозиториев
git config --global core.autocrlf input
git config --global core.eol lf

# Проверка настроек
git config --get core.autocrlf
git config --get core.eol

# Переиндексация файлов с правильными line endings
git rm --cached -r .
git reset --hard
```

**Создать `.gitattributes` в корне проекта:**

```
# Auto detect text files and perform LF normalization
* text=auto

# Force LF for specific files
*.py text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
*.txt text eol=lf
*.sh text eol=lf

# Force CRLF for batch files
*.bat text eol=crlf

# Binary files
*.png binary
*.jpg binary
*.svg binary
*.db binary
*.zip binary
```

---

### Этап 3: Проверка всех хуков

**Приоритет:** 🟡 Высокий

**Команды для проверки:**

```powershell
# Запустить все хуки на всех файлах
pre-commit run --all-files

# Запустить конкретный хук
pre-commit run trailing-whitespace --all-files
pre-commit run check-yaml --all-files
pre-commit run black --all-files

# Обновить хуки до последних версий
pre-commit autoupdate

# Очистить кэш и переустановить
pre-commit clean
pre-commit install
```

---

### Этап 4: Добавление дополнительных хуков

**Приоритет:** 🟢 Средний (после исправления основных проблем)

#### 4.1 Secret Scanning

**Файл:** `.pre-commit-config.yaml`

Добавить:

```yaml
# Secret detection
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
      exclude: package-lock.json
```

**Инициализация baseline:**

```bash
detect-secrets scan > .secrets.baseline
```

#### 4.2 Security Scanning

Добавить:

```yaml
# Security checks
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.5
  hooks:
    - id: bandit
      args: ['-r', 'src/', 'utils/', 'modules/', '-ll']
      exclude: tests/
```

#### 4.3 Markdown Linting

Добавить:

```yaml
# Markdown linting
- repo: https://github.com/igorshubovych/markdownlint-cli
  rev: v0.37.0
  hooks:
    - id: markdownlint
      args: ['--fix']
```

#### 4.4 Import Sorting (уже есть, но проверить конфиг)

Текущий конфиг:

```yaml
- repo: https://github.com/PyCQA/isort
  rev: 5.13.2
  hooks:
    - id: isort
      args: [--profile=black, --line-length=120]
```

**Создать `pyproject.toml` для настроек:**

```toml
[tool.black]
line-length = 120
target-version = ['py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 120
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src --cov=utils --cov=modules --cov-report=html --cov-report=term"
```

---

## 🧪 Тестирование Pre-commit

### Сценарий 1: Чистый коммит (должен пройти)

```bash
# Создать тестовый файл без проблем
echo "def hello():" > test_clean.py
echo "    return 'Hello, World!'" >> test_clean.py

# Добавить и закоммитить
git add test_clean.py
git commit -m "test: clean commit"
```

**Ожидаемый результат:** Все хуки passed ✅

---

### Сценарий 2: Коммит с trailing whitespace (должен исправиться автоматически)

```bash
# Создать файл с пробелами в конце строк
echo "def hello():    " > test_whitespace.py  # trailing spaces
echo "    return 'Hello'" >> test_whitespace.py

# Добавить и закоммитить
git add test_whitespace.py
git commit -m "test: whitespace fix"
```

**Ожидаемый результат:** Хук исправит пробелы, нужно добавить изменения и закоммитить снова

---

### Сценарий 3: Коммит с синтаксической ошибкой Python (должен упасть)

```bash
# Создать файл с синтаксической ошибкой
echo "def hello(" > test_syntax.py  # missing closing parenthesis

# Добавить и закоммитить
git add test_syntax.py
git commit -m "test: syntax error"
```

**Ожидаемый результат:** Хук `check-ast` должен упасть ❌

---

### Сценарий 4: Коммит с API ключом (должен упасть если добавлен detect-secrets)

```bash
# Создать файл с фейковым API ключом
echo "API_KEY = 'sk-1234567890abcdef'" > test_secret.py

# Добавить и закоммитить
git add test_secret.py
git commit -m "test: secret detection"
```

**Ожидаемый результат:** Хук `detect-secrets` должен упасть ❌

---

## 📊 Статус внедрения

| Хук | Статус | Приоритет | Дата внедрения |
|-----|--------|-----------|----------------|
| trailing-whitespace | ✅ Работает | Критичный | Реализовано |
| end-of-file-fixer | ✅ Работает | Критичный | Реализовано |
| check-yaml | 🔴 Падает | Критичный | Требует исправления |
| check-json | ✅ Работает | Высокий | Реализовано |
| check-added-large-files | ✅ Работает | Высокий | Реализовано |
| check-merge-conflict | ✅ Работает | Высокий | Реализовано |
| check-case-conflict | ✅ Работает | Высокий | Реализовано |
| mixed-line-ending | ✅ Работает | Критичный | Реализовано |
| check-ast | ✅ Работает | Критичный | Реализовано |
| check-docstring-first | ✅ Работает | Средний | Реализовано |
| debug-statements | ✅ Работает | Высокий | Реализовано |
| detect-private-key | ✅ Работает | Критичный | Реализовано |
| black | ⏳ Не протестирован | Высокий | Реализовано, требует проверки |
| isort | ⏳ Не протестирован | Высокий | Реализовано, требует проверки |
| flake8 | ⏳ Не протестирован | Высокий | Реализовано, требует проверки |
| detect-secrets | ❌ Не добавлен | Критичный | Планируется |
| bandit | ❌ Не добавлен | Высокий | Планируется |
| markdownlint | ❌ Не добавлен | Средний | Опционально |
| mypy | ❌ Не добавлен | Средний | Опционально |

---

## 🚦 Рекомендации

### Для разработчиков

1. **Всегда запускайте перед коммитом:**

   ```bash
   pre-commit run --all-files
   ```

2. **Если хук упал:**
   - Прочитайте сообщение об ошибке
   - Исправьте проблему вручную
   - Добавьте исправленные файлы: `git add .`
   - Попробуйте коммит снова

3. **Для быстрых фиксов (НЕ рекомендуется):**

   ```bash
   git commit --no-verify -m "message"  # ТОЛЬКО в крайнем случае!
   ```

### Для CI/CD

1. **Добавить в GitHub Actions:**

   ```yaml
   - name: Run pre-commit
     run: |
       pip install pre-commit
       pre-commit run --all-files
   ```

2. **Fail CI если pre-commit не проходит**

3. **Кэшировать pre-commit окружения:**

   ```yaml
   - uses: actions/cache@v3
     with:
       path: ~/.cache/pre-commit
       key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}
   ```

---

## 🔗 Полезные ссылки

- [Pre-commit документация](https://pre-commit.com/)
- [Pre-commit hooks список](https://pre-commit.com/hooks.html)
- [Black форматтер](https://black.readthedocs.io/)
- [Flake8 линтер](https://flake8.pycqa.org/)
- [isort](https://pycqa.github.io/isort/)
- [Bandit security](https://bandit.readthedocs.io/)
- [Detect secrets](https://github.com/Yelp/detect-secrets)

---

## 📝 Следующие шаги

### Немедленные действия (сегодня)

- [ ] Исправить YAML файл `.github/workflows/ci.yml:149`
- [ ] Создать `.gitattributes` для line endings
- [ ] Настроить Git конфиг для Windows
- [ ] Протестировать все хуки: `pre-commit run --all-files`

### Краткосрочные (эта неделя)

- [ ] Добавить detect-secrets хук
- [ ] Добавить bandit хук
- [ ] Создать `pyproject.toml` с настройками инструментов
- [ ] Добавить pre-commit в CI/CD pipeline
- [ ] Документировать процесс для контрибьюторов

### Долгосрочные (следующий релиз)

- [ ] Добавить mypy для type checking
- [ ] Добавить coverage требования
- [ ] Настроить автоматические PR checks
- [ ] Создать pre-push хуки для тестов

---

**Обновлено:** 6 октября 2025, 00:45  
**Ответственный:** @Fat1ms
