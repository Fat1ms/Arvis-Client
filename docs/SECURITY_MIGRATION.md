# 🚨 СРОЧНАЯ МИГРАЦИЯ: Безопасность API ключей

**Дата:** 4 октября 2025  
**Приоритет:** 🔴 КРИТИЧЕСКИЙ  
**Статус:** ⚠️ ТРЕБУЕТСЯ ДЕЙСТВИЕ

---

## ⚠️ ПРОБЛЕМА

В файле `config/config.json` обнаружены **реальные API ключи** в публичном репозитории:

```json
"weather": {
    "api_key": "d6bbfdd9eef854a98655617d77102027"  // ⚠️ ОТКРЫТ!
},
"news": {
    "api_key": "aa06872270204a658619b7e67663a33f"  // ⚠️ ОТКРЫТ!
},
"search": {
    "api_key": "AIzaSyA-4cmUhfRF-L-JV-sfHBDjurgK82JE_4o"  // ⚠️ ОТКРЫТ!
}
```

### Риски

- ❌ Злоупотребление API квотами (расходы)
- ❌ Компрометация аккаунтов
- ❌ Нарушение ToS сервисов
- ❌ Утечка данных пользователей

---

## 🛠️ НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ

### Шаг 1: Ротация ключей (СРОЧНО!)

#### OpenWeatherMap API

1. Войти: <https://home.openweathermap.org/api_keys>
2. Удалить скомпрометированный ключ: `d6bbfdd9eef854a98655617d77102027`
3. Создать новый ключ
4. Добавить в `.env` (НЕ в `config.json`)

#### NewsAPI

1. Войти: <https://newsapi.org/account>
2. Деактивировать ключ: `aa06872270204a658619b7e67663a33f`
3. Создать новый ключ
4. Добавить в `.env`

#### Google Custom Search API

1. Войти: <https://console.cloud.google.com/apis/credentials>
2. Отозвать ключ: `AIzaSyA-4cmUhfRF-L-JV-sfHBDjurgK82JE_4o`
3. Создать новый API Key с ограничениями:
   - Только Custom Search API
   - IP restriction (опционально)
4. Добавить в `.env`

### Шаг 2: Миграция на .env

#### Создать файл `.env` в корне проекта

```bash
# Скопировать из .env.example
cp .env.example .env

# Открыть в редакторе
notepad .env
```

#### Заполнить новыми ключами

```dotenv
# API КЛЮЧИ (заменить YOUR_KEY на реальные значения)
WEATHER_API_KEY=your_new_openweather_key_here
NEWS_API_KEY=your_new_newsapi_key_here
GOOGLE_SEARCH_API_KEY=your_new_google_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here

# ПОЛЬЗОВАТЕЛЬ
USER_NAME=Андрей
USER_CITY=Киев

# OLLAMA
OLLAMA_URL=http://127.0.0.1:11434
DEFAULT_LLM_MODEL=mistral:7b
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

### Шаг 3: Очистка config.json

**Заменить `config/config.json` на пример:**

```bash
# Windows PowerShell
Remove-Item config\config.json
Copy-Item config\config.json.example config\config.json
```

Убедиться, что `config.json` содержит только пустые значения:

```json
"weather": {
    "api_key": "",  // ✅ Пусто - берётся из .env
    ...
}
```

### Шаг 4: Очистка Git истории

⚠️ **ВНИМАНИЕ:** Это перепишет историю! Координируйте с командой.

```bash
# 1. Создать backup
git clone --mirror https://github.com/Fat1ms/Arvis-Sentenel.git arvis-backup

# 2. Установить BFG Repo-Cleaner
# Скачать: https://rtyley.github.io/bfg-repo-cleaner/
# Или через Scoop: scoop install bfg

# 3. Создать файл passwords.txt со скомпрометированными ключами
@"
d6bbfdd9eef854a98655617d77102027
aa06872270204a658619b7e67663a33f
AIzaSyA-4cmUhfRF-L-JV-sfHBDjurgK82JE_4o
"@ | Out-File -Encoding UTF8 passwords.txt

# 4. Очистить историю
bfg --replace-text passwords.txt --no-blob-protection

# 5. Принудительно очистить Git объекты
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 6. Force push (предупредить команду!)
git push --force --all
```

---

## ✅ ПРОВЕРКА МИГРАЦИИ

### Чеклист

- [ ] Все API ключи заменены на новые
- [ ] Файл `.env` создан и заполнен
- [ ] `config.json` не содержит реальных ключей
- [ ] `.gitignore` игнорирует `.env` и `config.json`
- [ ] Git история очищена от старых ключей
- [ ] Приложение запускается с новыми ключами
- [ ] Модули работают корректно

### Команды для проверки

```powershell
# Проверить .gitignore
Get-Content .gitignore | Select-String -Pattern "\.env|config\.json"

# Проверить config.json на ключи
Get-Content config\config.json | Select-String -Pattern "api_key"

# Проверить Git историю (не должно быть совпадений)
git log --all --full-history --source --pretty=format:"%H" -- config/config.json | ForEach-Object {
    git show $_:config/config.json | Select-String -Pattern "d6bbfdd9|aa068722|AIzaSyA"
}

# Запустить приложение
python main.py
```

---

## 📚 ДАЛЬНЕЙШИЕ ШАГИ

### 1. Настроить Secret Scanner в CI

`.github/workflows/security.yml`:

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Полная история для сканирования

      - name: Gitleaks Scan
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Добавить pre-commit hook

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### 3. Обновить документацию

- [ ] `README.md` - инструкции по `.env`
- [ ] `CONTRIBUTING.md` - правила работы с секретами
- [ ] `SECURITY.md` - политика безопасности

---

## 🚨 ЧТО ДЕЛАТЬ, ЕСЛИ КЛЮЧИ УЖЕ ИСПОЛЬЗОВАНЫ

### Если обнаружена подозрительная активность

1. **Немедленно отозвать все ключи**
2. **Проверить биллинг** всех сервисов:
   - OpenWeatherMap: <https://home.openweathermap.org/subscriptions>
   - NewsAPI: <https://newsapi.org/pricing>
   - Google Cloud: <https://console.cloud.google.com/billing>

3. **Настроить алерты** на превышение лимитов
4. **Ограничить IP** для новых ключей (если возможно)

### Контакты поддержки

- **OpenWeatherMap:** <https://openweathermap.org/faq>
- **NewsAPI:** <support@newsapi.org>
- **Google Cloud:** <https://cloud.google.com/support>

---

## 📊 Мониторинг

### Команда для проверки статуса ключей

```python
# tests/check_api_keys.py
import os
from dotenv import load_dotenv

load_dotenv()

keys = {
    "WEATHER_API_KEY": os.getenv("WEATHER_API_KEY"),
    "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
    "GOOGLE_SEARCH_API_KEY": os.getenv("GOOGLE_SEARCH_API_KEY"),
}

for name, key in keys.items():
    if not key:
        print(f"❌ {name} не установлен")
    elif len(key) < 20:
        print(f"⚠️ {name} слишком короткий")
    elif key.startswith("your_"):
        print(f"⚠️ {name} использует placeholder")
    else:
        print(f"✅ {name} установлен ({key[:6]}...{key[-4:]})")
```

---

## 🔗 Полезные ссылки

- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub Secrets Security](https://docs.github.com/en/code-security/secret-scanning)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)

---

**⏰ Время выполнения:** 30-60 минут  
**⚠️ Критичность:** МАКСИМАЛЬНАЯ

*Документ создан: 4 октября 2025*
