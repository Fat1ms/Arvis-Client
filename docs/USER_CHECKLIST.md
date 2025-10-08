# ✅ Фаза 1: Чек-лист для пользователя

**Время выполнения:** 15-30 минут  
**Дата:** 4 октября 2025

---

## 🚨 КРИТИЧНО: Выполнить ПЕРВЫМ (5-10 мин)

### [ ] 1. Ротация API ключей

⚠️ **ВАЖНО:** Текущие ключи скомпрометированы и должны быть заменены!

#### OpenWeatherMap

- [ ] Открыть: <https://home.openweathermap.org/api_keys>
- [ ] Удалить ключ: ``
- [ ] Создать новый ключ
- [ ] Скопировать новый ключ в блокнот

#### NewsAPI

- [ ] Открыть: <https://newsapi.org/account>
- [ ] Деактивировать ключ: ``
- [ ] Создать новый ключ
- [ ] Скопировать новый ключ в блокнот

#### Google Custom Search

- [ ] Открыть: <https://console.cloud.google.com/apis/credentials>
- [ ] Отозвать ключ: ``
- [ ] Создать новый API Key
- [ ] Ограничить: только Custom Search API
- [ ] Скопировать новый ключ в блокнот

---

## 📝 Создание .env файла (3-5 мин)

### [ ] 2. Скопировать шаблон

```powershell
# В корне проекта (d:\AI\Arvis)
Copy-Item .env.example .env
```

### [ ] 3. Заполнить .env

```powershell
notepad .env
```

Вставить НОВЫЕ ключи:

```dotenv
# === API КЛЮЧИ (ЗАМЕНИТЬ НА СВОИ!) ===
WEATHER_API_KEY=ваш_новый_ключ_weather_здесь
NEWS_API_KEY=ваш_новый_ключ_news_здесь
GOOGLE_SEARCH_API_KEY=ваш_новый_ключ_google_здесь
GOOGLE_SEARCH_ENGINE_ID=ваш_engine_id_здесь

# === ПОЛЬЗОВАТЕЛЬ ===
USER_NAME=Андрей
USER_CITY=Киев

# === OLLAMA (можно оставить как есть) ===
OLLAMA_URL=http://127.0.0.1:11434
DEFAULT_LLM_MODEL=mistral:7b
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# === TTS ===
TTS_VOICE=aidar
TTS_SAMPLE_RATE=48000
TTS_DEVICE=cpu

# === STT ===
STT_MODEL_PATH=models/vosk-model-ru-0.42
STT_WAKE_WORD=Арвис
```

### [ ] 4. Сохранить .env

- Ctrl+S
- Закрыть Notepad

---

## 🗑️ Очистка config.json (2 мин)

### [ ] 5. Удалить старый config.json

```powershell
# ВНИМАНИЕ: Это удалит ваши настройки!
# Если нужно, сделайте backup:
# Copy-Item config\config.json config\config.json.backup

Remove-Item config\config.json
```

### [ ] 6. Скопировать безопасный шаблон

```powershell
Copy-Item config\config.json.example config\config.json
```

---

## ✅ Проверка (3-5 мин)

### [ ] 7. Проверить, что config.json безопасен

```powershell
Get-Content config\config.json | Select-String "api_key"
```

**Ожидаемый результат:** Все `api_key` должны быть **пустыми строками** `""`

```
"api_key": "",
"api_key": "",
"api_key": "",
```

### [ ] 8. Проверить, что .env содержит ключи

```powershell
Get-Content .env | Select-String "API_KEY"
```

**Ожидаемый результат:** Все `API_KEY` должны содержать **ваши новые ключи**

```
WEATHER_API_KEY=новый_ключ_здесь
NEWS_API_KEY=новый_ключ_здесь
GOOGLE_SEARCH_API_KEY=новый_ключ_здесь
```

### [ ] 9. Проверить .gitignore

```powershell
git check-ignore .env config\config.json
```

**Ожидаемый результат:** Оба файла должны быть **игнорированы**

```
.env
config\config.json
```

---

## 🧪 Тестирование (5-10 мин)

### [ ] 10. Запустить Arvis

```powershell
python main.py
```

**Ожидаемый результат:**

- ✅ Запускается без ошибок
- ✅ Нет сообщений об отсутствующих ключах

### [ ] 11. Тест модулей

В GUI Arvis:

- [ ] Отправить: "Какая погода?"
  - ✅ Должен вернуть данные о погоде

- [ ] Отправить: "Новости"
  - ✅ Должен вернуть новости

- [ ] Отправить: "Найди информацию о Python" (если включен поиск)
  - ✅ Должен вернуть результаты поиска

### [ ] 12. Тест регенерации (Баг #11)

- [ ] Отправить: "Привет"
- [ ] Дождаться ответа
- [ ] Нажать кнопку 🔄 "Попробовать ещё раз"
- [ ] Нажать кнопку истории чата
- [ ] **Проверить:** "Привет" должен быть **только ОДИН раз** ✅

### [ ] 13. Тест множественной регенерации

- [ ] Отправить: "Расскажи анекдот"
- [ ] Нажать 🔄 три раза подряд
- [ ] Проверить историю
- [ ] **Проверить:**
  - ✅ "Расскажи анекдот" - только **ОДИН раз**
  - ✅ Три **разных** ответа ассистента

### [ ] 14. Тест защиты от spam

- [ ] Отправить любое сообщение
- [ ] БЫСТРО нажать 🔄 пять раз
- [ ] **Проверить:**
  - ✅ Появляется сообщение "Запрос обрабатывается"
  - ✅ Только одна генерация выполняется

---

## 🔬 Unit Tests (опционально, 5 мин)

### [ ] 15. Установить зависимости для тестов

```powershell
pip install pytest pytest-cov pytest-qt pytest-mock
```

### [ ] 16. Запустить тесты

```powershell
# Все тесты
pytest tests/ -v

# Только тесты бага #11
pytest tests/test_generation_state.py -v
pytest tests/test_conversation_history.py -v
```

**Ожидаемый результат:**

```
============= 22 passed in X.XXs =============
```

### [ ] 17. Проверить coverage (опционально)

```powershell
pytest tests/ -v --cov=src --cov=utils --cov-report=html
```

Открыть `htmlcov/index.html` в браузере для детального отчёта.

---

## 🔧 Pre-commit (опционально, 2 мин)

### [ ] 18. Установить pre-commit

```powershell
pip install pre-commit
pre-commit install
```

### [ ] 19. Первый запуск

```powershell
pre-commit run --all-files
```

**Ожидаемый результат:** Hooks должны пройти или автоматически исправить форматирование.

---

## 🚀 Git Commit (3 мин)

### [ ] 20. Проверить Git status

```powershell
git status
```

**Ожидаемый результат:**

- ✅ `.env` **НЕ** в списке (игнорируется)
- ✅ `config/config.json` **НЕ** в списке (игнорируется)
- ✅ Только изменения в src/, tests/, docs/

### [ ] 21. Commit изменений

```bash
git add .
git commit -m "Phase 1: Fix bug #11 and security hardening

- Fix duplicate messages on regeneration (issue #11)
- Add GenerationState state machine
- Move API keys to .env
- Add 22 unit tests with 90% coverage
- Setup CI/CD pipeline and pre-commit hooks
- Comprehensive documentation"

git push
```

---

## 📊 Проверка CI (опционально, 5 мин)

### [ ] 22. Проверить GitHub Actions

1. Открыть: <https://github.com/Fat1ms/Arvis-Sentenel/actions>
2. Найти последний workflow run
3. **Проверить:**
   - ✅ Lint job - passed
   - ✅ Test job - passed
   - ✅ Security job - passed
   - ✅ Build job - passed

---

## 🧹 Очистка Git истории (ОПЦИОНАЛЬНО, 10-15 мин)

⚠️ **ВНИМАНИЕ:** Это перепишет Git историю! Координируйте с командой.

### [ ] 23. (Опционально) Очистить историю от ключей

См. подробное руководство в `docs/SECURITY_MIGRATION.md`, раздел "Шаг 4: Очистка Git истории"

Кратко:

```powershell
# 1. Backup
git clone --mirror https://github.com/Fat1ms/Arvis-Sentenel.git arvis-backup

# 2. BFG Repo-Cleaner
# Скачать: https://rtyley.github.io/bfg-repo-cleaner/
bfg --replace-text passwords.txt

# 3. Force push
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

---

## ✅ Финальный чек-лист

После выполнения всех шагов:

- [ ] ✅ Все API ключи ротированы
- [ ] ✅ `.env` создан и заполнен новыми ключами
- [ ] ✅ `config.json` не содержит реальных ключей
- [ ] ✅ Arvis запускается без ошибок
- [ ] ✅ Модули погоды/новостей/поиска работают
- [ ] ✅ Регенерация НЕ создаёт дубликатов
- [ ] ✅ История чата корректна
- [ ] ✅ Тесты проходят (pytest)
- [ ] ✅ Pre-commit установлен
- [ ] ✅ Изменения закоммичены
- [ ] ✅ CI проходит на GitHub
- [ ] ✅ `.env` и `config.json` в `.gitignore`

---

## 🎉 Готово

**Фаза 1 завершена!**

Arvis теперь:

- ✅ Без бага #11
- ✅ Безопасно хранит секреты
- ✅ Защищён от race conditions
- ✅ Покрыт тестами
- ✅ Имеет CI/CD pipeline

Можно продолжать разработку! 🚀

---

## 📚 Дополнительная информация

- **Быстрый старт:** `docs/QUICKSTART_PHASE1.md`
- **Миграция безопасности:** `docs/SECURITY_MIGRATION.md`
- **Полный отчёт:** `docs/PHASE_1_COMPLETE.md`
- **Статус:** `docs/PHASE_1_STATUS.md`

---

## ❓ Проблемы?

### "Module not found" при pytest

```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### API ключи не работают

```powershell
# Проверить загрузку .env
python -c "from config.config import Config; c = Config(); print(c.get('weather.api_key'))"
# Должен вывести ваш ключ
```

### Pre-commit падает

```powershell
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### Arvis не запускается

1. Проверить, что `.env` существует
2. Проверить, что все ключи заполнены
3. Проверить логи: `logs/arvis_*.log`

---

**Время выполнения:** 15-30 минут  
**Сложность:** 🟢 Низкая

✅ **Готово к использованию!**

---

*Последнее обновление: 4 октября 2025*
