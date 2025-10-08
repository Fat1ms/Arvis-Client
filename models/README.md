# Models Directory

Эта папка содержит локальные модели для Arvis AI Assistant.

## 📦 Требуемые модели

### Vosk (Speech-to-Text)

Скачайте одну из следующих моделей:

#### Рекомендуемая (легкая)
- **vosk-model-small-ru-0.22** (45 MB)
  - Скачать: https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
  - Быстрая, хорошо работает на слабом железе
  - Точность: средняя

#### Улучшенная точность
- **vosk-model-ru-0.42** (1.5 GB)
  - Скачать: https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip
  - Высокая точность распознавания
  - Требует больше ресурсов

## 📂 Структура после установки

```
models/
├── README.md (этот файл)
├── vosk-model-small-ru-0.22/
│   ├── am/
│   ├── conf/
│   ├── graph/
│   └── ...
└── vosk-model-ru-0.42/  (опционально)
    ├── am/
    ├── conf/
    ├── graph/
    └── ...
```

## ⚙️ Настройка

После скачивания модели обновите путь в `config/config.json` или `.env`:

**config.json:**
```json
{
  "stt": {
    "model_path": "models/vosk-model-small-ru-0.22"
  }
}
```

**или .env:**
```bash
STT_MODEL_PATH=models/vosk-model-small-ru-0.22
```

## 🚀 Автоматическая установка

Используйте скрипт `setup_arvis.bat`, который:
1. Проверит наличие моделей
2. Предложит скачать, если отсутствуют
3. Распакует в нужную папку

## 📝 Примечания

- Модели **НЕ включены** в Git репозиторий (слишком большие)
- Файлы `.zip` и папки моделей игнорируются через `.gitignore`
- Для других языков см. https://alphacephei.com/vosk/models

## ❓ Часто задаваемые вопросы

**Q: Какую модель выбрать?**
A: Для начала используйте `vosk-model-small-ru-0.22`. Если нужна лучшая точность и есть ресурсы - `vosk-model-ru-0.42`.

**Q: Можно ли использовать английские модели?**
A: Да! Скачайте английскую модель и измените настройки. Например: `vosk-model-en-us-0.22`.

**Q: Ошибка "Model not found"?**
A: Убедитесь, что:
1. Модель распакована в папку `models/`
2. Путь в конфиге указан правильно
3. Структура папок сохранена (am/, conf/, graph/)

## 🔗 Полезные ссылки

- [Официальный сайт Vosk](https://alphacephei.com/vosk/)
- [Список всех моделей](https://alphacephei.com/vosk/models)
- [Документация Vosk](https://alphacephei.com/vosk/documentation)
