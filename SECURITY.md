# 🔒 Security Policy

## Поддерживаемые версии

Мы активно поддерживаем следующие версии Arvis AI Assistant:

| Версия | Поддерживается          |
| ------ | ----------------------- |
| 1.3.x  | :white_check_mark: Да   |
| 1.2.x  | :white_check_mark: Да   |
| 1.1.x  | :x: Нет                 |
| < 1.0  | :x: Нет                 |

## 🛡️ Области безопасности

### Критичные области

Следующие компоненты требуют особого внимания с точки зрения безопасности:

1. **API ключи и секреты** (`config/config.json`, `.env`)
   - Хранение API ключей для внешних сервисов
   - Конфигурация доступа к Ollama
   - Токены для NewsAPI, OpenWeather, Google Custom Search

2. **Системное управление** (`modules/system_control.py`)
   - Выполнение системных команд
   - Управление питанием и процессами
   - Флаг безопасности `security.execution.allow_scripts`

3. **Сетевые запросы** (`modules/llm_client.py`, `utils/fast_http.py`)
   - Взаимодействие с локальным Ollama
   - API запросы к внешним сервисам
   - Обработка пользовательского ввода

4. **Файловая система** (`utils/conversation_history.py`)
   - Хранение истории диалогов
   - Логирование (может содержать чувствительные данные)
   - Кэширование и временные файлы

5. **Голосовой ввод** (`modules/stt_engine.py`, `modules/wake_word_detector.py`)
   - Обработка аудиопотока
   - Локальное распознавание речи

## 🚨 Сообщение об уязвимостях

### Responsible Disclosure

Если вы обнаружили уязвимость в Arvis, **пожалуйста, НЕ создавайте публичный issue на GitHub**.

Вместо этого, следуйте процедуре ответственного раскрытия:

### Процесс сообщения

1. **Email**: Отправьте описание уязвимости на [ваш контактный email]
   - Используйте тему письма: `[SECURITY] Arvis Vulnerability Report`

2. **Содержание отчёта** должно включать:
   - Описание уязвимости
   - Шаги для воспроизведения
   - Версия Arvis и зависимостей
   - Потенциальное влияние
   - Предложения по исправлению (если есть)
   - Ваши контактные данные для обратной связи

3. **Ожидаемый ответ**:
   - Подтверждение получения: в течение **48 часов**
   - Первичная оценка: в течение **7 дней**
   - План исправления: в течение **14 дней**

### Что ожидать

- Мы будем держать вас в курсе прогресса исправления
- После выпуска патча вы будете указаны в благодарностях (если пожелаете)
- Мы координируем с вами время публичного раскрытия
- Обычно 90 дней с момента отчёта до публичного раскрытия

### PGP

Для конфиденциальной переписки вы можете использовать PGP шифрование:

```
[Добавьте ваш публичный PGP ключ здесь, когда он будет создан]
```

## 🔐 Рекомендации по безопасности

### Для пользователей

1. **Защита API ключей**

   ```bash
   # Используйте .env файл вместо config.json
   cp .env.example .env
   # Отредактируйте .env и добавьте свои ключи

   # Убедитесь, что .env в .gitignore
   echo ".env" >> .gitignore
   ```

2. **Ollama безопасность**

    Рекомендуемая конфигурация (локальный доступ только):

    ```json
    {
       "security": {
          "ollama": {
             "bind_address": "127.0.0.1",
             "allow_external": false,
             "launch_mode": "background",
             "auto_restart": true
          }
       }
    }
    ```

    - НЕ используйте `0.0.0.0`, если не понимаете последствия. Для внешнего доступа переключите `allow_external=true` и задайте `bind_address=0.0.0.0`.

3. **Системные команды**

    ```json
    // config.json
    {
       "security": {
          "execution": {
             "allow_scripts": false,
             "restricted_extensions": ["bat", "cmd", "ps1", "js", "vbs"]
          }
       }
    }
    ```

4. **Логирование**
   - Регулярно проверяйте `logs/` на наличие чувствительной информации
   - Не делитесь полными логами публично
   - Используйте маскировку секретов (встроена в `utils.logger`)

5. **Обновления**

   ```bash
   # Регулярно обновляйте зависимости
   pip install --upgrade -r requirements.txt

   # Проверяйте уязвимости
   pip install safety
   safety check
   ```

### Для разработчиков

1. **Никогда не коммитьте секреты**

   ```bash
   # Используйте pre-commit hooks
   pip install pre-commit
   pre-commit install

   # Проверка на секреты
   git secrets --scan
   ```

2. **Валидация ввода**

   ```python
   # Всегда валидируйте пользовательский ввод
   def process_command(user_input: str):
       # Sanitize input
       safe_input = sanitize(user_input)
       # Validate
       if not is_safe(safe_input):
           raise ValueError("Unsafe input")
       # Process
       ...
   ```

3. **Минимальные привилегии**

   ```python
   # Не запускайте subprocess с shell=True
   subprocess.run(["command", "arg"], shell=False)

   # Используйте whitelist для системных команд
   ALLOWED_COMMANDS = ["shutdown", "restart"]
   if command not in ALLOWED_COMMANDS:
       raise PermissionError()
   ```

4. **Безопасные зависимости**

   ```bash
   # Зафиксируйте версии в requirements.txt
   pip freeze > requirements.txt

   # Регулярно проверяйте CVE
   pip-audit
   ```

5. **Code review**
   - Все изменения в критичных модулях требуют review
   - Обращайте внимание на `subprocess`, `eval`, `exec`, `os.system`
   - Проверяйте обработку ошибок и утечки информации

## 🔍 Известные ограничения

### Текущие ограничения безопасности (будут исправлены в будущих версиях)

1. **Хранение API ключей** (v1.3.2)
   - ❌ API ключи в `config.json` (plain text)
   - ✅ Поддержка переменных окружения
   - 🔄 Планируется: OS keyring integration (Фаза 1)

2. **Системные команды** (v1.3.2)
   - ⚠️ Ограниченная валидация команд
   - ✅ Флаг `allow_scripts` по умолчанию false
   - 🔄 Планируется: Строгий whitelist и RBAC (Фаза 2)

3. **Логирование** (v1.3.2)
   - ✅ Базовая маскировка секретов
   - ⚠️ Могут логироваться длинные промпты
   - 🔄 Планируется: Улучшенная фильтрация (Фаза 1)

4. **Сетевая изоляция** (v1.3.2)
   - ⚠️ Ollama может быть доступен извне при неправильной настройке
   - 🔄 Планируется: Автопроверка bind адресов (Фаза 1)

## 📋 Security Checklist

### Перед развёртыванием

- [ ] Переменные окружения настроены (`.env` создан)
- [ ] API ключи не в config.json
- [ ] `security.execution.allow_scripts` установлен корректно
- [ ] Ollama слушает только `127.0.0.1` (если не требуется внешний доступ)
- [ ] Зависимости обновлены (`pip install --upgrade -r requirements.txt`)
- [ ] Логи не содержат чувствительной информации
- [ ] Файрвол настроен корректно
- [ ] `.gitignore` содержит `.env`, `config.json`, `logs/`, `data/`

### Регулярное обслуживание

- [ ] Еженедельно: проверка обновлений зависимостей
- [ ] Ежемесячно: audit безопасности (`safety check`, `pip-audit`)
- [ ] Ежеквартально: review конфигурации безопасности
- [ ] После инцидента: анализ логов и причин

## 🏆 Благодарности

Мы благодарны следующим исследователям безопасности за responsible disclosure:

- *Пока список пуст - будьте первым!*

## 📚 Дополнительные ресурсы

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [PyTorch Security](https://pytorch.org/docs/stable/notes/security.html)

## 📞 Контакты

- **Security Team**: [security@your-domain.com] (создать при необходимости)
- **General Issues**: [GitHub Issues](https://github.com/Fat1ms/Arvis-Sentenel/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Fat1ms/Arvis-Sentenel/discussions)

---

**Последнее обновление**: 4 октября 2025  
**Версия документа**: 1.0
