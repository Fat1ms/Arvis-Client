# 🚀 Установка и интеграция Gemma 2b

**Документ**: Инструкция по установке и использованию Gemma 2b с Arvis  
**Дата**: October 21, 2025  
**Статус**: Готовая документация  
**Язык**: Русский (Russian) + English

---

## 📋 Содержание

1. [Что такое Gemma 2b?](#что-такое-gemma-2b)
2. [Системные требования](#системные-требования)
3. [Установка через Ollama](#установка-через-ollama)
4. [Прямая интеграция](#прямая-интеграция)
5. [Конфигурация в Arvis](#конфигурация-в-arvis)
6. [Использование](#использование)
7. [Оптимизация](#оптимизация)
8. [Troubleshooting](#troubleshooting)

---

## Что такое Gemma 2b?

**Gemma 2b** — это легкая и быстрая языковая модель от Google:

| Параметр | Значение |
|----------|----------|
| **Разработчик** | Google |
| **Параметры** | 2 млрд (2B) |
| **Размер** | ~5 ГБ на диске |
| **RAM** | 4-6 ГБ (минимум) |
| **Скорость** | Быстрая (оптимальна для боевых систем) |
| **Качество** | Хорошее для русского языка |
| **Лицензия** | Apache 2.0 |

**Преимущества**:
- ✅ Легче, чем Mistral (7B) или Llama 2 (7B)
- ✅ Быстрее, чем большие модели
- ✅ Хороший баланс качества/скорости
- ✅ Поддерживает русский язык
- ✅ Подходит для боевых систем с ограниченной памятью

**Недостатки**:
- ⚠️ Меньше контекста (4K токенов)
- ⚠️ Менее "знающая" чем GPT
- ⚠️ Требует Ollama или прямой интеграции

---

## Системные требования

### Минимум (на пределе)
```
CPU: Intel Core i5 (6-ядерный) / AMD Ryzen 5
RAM: 6 ГБ (+ 4 ГБ подкачка на диске)
GPU: Не требуется, но ускорит работу (NVIDIA, AMD)
SSD: 10 ГБ свободного места
```

### Рекомендуется
```
CPU: Intel Core i7 / AMD Ryzen 7 (8+ ядер)
RAM: 8-16 ГБ
GPU: NVIDIA (CUDA) или AMD (ROCm) - сильно ускоряет
SSD: 20 ГБ свободного места
```

### Проверить у себя

**Windows PowerShell:**
```powershell
# Процессор
Get-ComputerInfo | Select-Object CsProcessors

# Память
Get-ComputerInfo | Select-Object CsTotalPhysicalMemory

# Диск (C:)
Get-Volume -DriveLetter C | Select-Object SizeRemaining
```

---

## Установка через Ollama

### Вариант 1: Самый простой (рекомендуется)

#### Шаг 1: Установить Ollama
1. Скачать [ollama.ai](https://ollama.ai) для Windows/Mac/Linux
2. Установить обычным способом
3. Перезагрузить компьютер

#### Шаг 2: Загрузить Gemma 2b
```bash
# Откройте PowerShell/Terminal и запустите

ollama pull gemma:2b

# Вывод должен быть:
# pulling manifest ✓
# pulling 5f9b... ✓
# Success! Model downloaded
```

⏱️ **Время первой загрузки**: 5-15 минут (зависит от интернета)

#### Шаг 3: Проверить установку
```bash
# Запустить модель один раз
ollama run gemma:2b

# Ввести: "Hello"
# Выход: Gemma должна ответить

# Выход: Ctrl+D или quit
```

✅ Готово! Gemma 2b установлена и работает.

---

### Вариант 2: Установить все модели сразу

Если хотите несколько моделей (рекомендуется):

```bash
# Gemma 2b (быстрая)
ollama pull gemma:2b

# Mistral 7b (качественнее, медленнее)
ollama pull mistral:7b

# Phi 2b (альтернатива Gemma)
ollama pull phi:2b

# Зейфур (русскоязычная)
ollama pull zephyr:7b
```

---

## Прямая интеграция

### Если Ollama не подходит

Можно использовать Gemma 2b напрямую через Python:

#### Установить зависимости
```bash
# Windows PowerShell
.venv\Scripts\pip install transformers torch bitsandbytes

# Если на GPU (NVIDIA)
.venv\Scripts\pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Загрузить модель
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Первый раз загрузится ~5 ГБ с Hugging Face
model_id = "google/gemma-2b-it"  # 'it' = Instruct-tuned (лучше для чата)

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,  # Экономит память
    device_map="auto"            # Автоматически на GPU если есть
)
```

#### Использовать
```python
prompt = "Привет, как дела?"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0]))
```

---

## Конфигурация в Arvis

### Обновить config.json

```json
{
    "llm": {
        "default_model": "gemma:2b",
        "ollama_url": "http://localhost:11434",
        "temperature": 0.7,
        "max_tokens": 512,
        "stream": true,
        "models": {
            "gemma:2b": {
                "name": "Gemma 2B",
                "description": "Быстрая модель для боевого использования",
                "context_length": 8192,
                "parameters": 2000000000,
                "recommend_for": ["fast", "low_memory", "russian"]
            },
            "mistral:7b": {
                "name": "Mistral 7B",
                "description": "Качественнее, но медленнее",
                "context_length": 32000,
                "parameters": 7000000000,
                "recommend_for": ["quality", "long_context"]
            }
        }
    }
}
```

### Или в code (Python)

```python
from config.config import Config

config = Config()
config.set("llm.default_model", "gemma:2b")
config.set("llm.temperature", 0.7)
config.set("llm.max_tokens", 512)  # Меньше для быстрости
```

---

## Использование

### Базовое использование

```python
from utils.operation_mode_manager import OperationModeManager
from utils.providers.llm.gemma_provider import GemmaLLMProvider

# Инициализировать
manager = OperationModeManager(config)
gemma_provider = GemmaLLMProvider(config)
manager.register_provider(gemma_provider)

# Запустить
if manager.initialize_mode():
    # Простой запрос
    response = gemma_provider.generate_response(
        prompt="Привет, Gemma! Представься.",
        temperature=0.7,
        max_tokens=256
    )
    print(response)
    
    # Потоком (streaming)
    for chunk in gemma_provider.stream_response(
        prompt="Расскажи мне 3 интересных факта о Python",
        max_tokens=512
    ):
        print(chunk, end="", flush=True)
```

### С системным промптом

```python
# Установить роль модели
response = gemma_provider.generate_response(
    prompt="Какой сейчас год?",
    system_prompt="Ты - дружелюбный русскоязычный ассистент. Отвечай кратко.",
    temperature=0.5  # Ниже → более детерминированные ответы
)
```

### С fallback между моделями

```python
# Автоматически переключится на другую модель если Gemma недоступна
result = manager.llm_fallback.execute(
    operation=lambda p: p.generate_response("Привет!"),
    operation_name="llm_generation"
)
```

---

## Оптимизация

### 1. Уменьшить температуру для боевого использования

```json
{
    "llm": {
        "temperature": 0.3,  // Более консервативные ответы
        "max_tokens": 256    // Короче, быстрее
    }
}
```

### 2. Использовать quantization (сжатие)

**Экономит память на 50%**, но немного медленнее:

```bash
ollama pull gemma:2b-q4_K_M  # Quantized версия
```

### 3. Ограничить контекст

```python
response = gemma_provider.generate_response(
    prompt=prompt,
    max_tokens=256,  # Вместо 512
    temperature=0.5
)
```

### 4. Кешировать популярные запросы

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_response(prompt: str) -> str:
    return gemma_provider.generate_response(prompt)
```

### 5. Запускать Ollama в фоне

```json
{
    "startup": {
        "autostart_ollama": true,
        "ollama_launch_mode": "background"
    }
}
```

---

## Troubleshooting

### ❌ "Ollama is not reachable"

**Решение 1**: Запустить Ollama
```bash
ollama serve
```

**Решение 2**: Проверить URL
```bash
# Проверить, работает ли Ollama
curl http://localhost:11434/api/tags

# Должен вернуть список моделей
```

**Решение 3**: Переустановить Ollama
```bash
# Удалить Ollama и переустановить с ollama.ai
```

---

### ❌ "Out of memory"

**Решение 1**: Использовать quantized модель
```bash
ollama pull gemma:2b-q4_K_M  # Меньше памяти
```

**Решение 2**: Закрыть другие приложения
- Браузеры
- IDE
- Медиаплееры

**Решение 3**: Расширить виртуальную память (Windows)
```powershell
# Settings → Advanced System Settings → 
# Performance → Advanced → Virtual Memory
# Установить на 8-16 ГБ на SSD
```

---

### ❌ "Slow responses" (медленные ответы)

**Решение 1**: Уменьшить max_tokens
```json
{
    "llm": {
        "max_tokens": 256  // Вместо 2048
    }
}
```

**Решение 2**: Включить GPU ускорение
- Установить NVIDIA CUDA 11.8+
- Ollama автоматически будет использовать GPU

**Решение 3**: Использовать Phi вместо Gemma (ещё быстрее)
```bash
ollama pull phi:2b
```

---

### ❌ "Плохое качество ответов на русском"

**Решение 1**: Использовать system_prompt
```python
response = gemma_provider.generate_response(
    prompt=prompt,
    system_prompt="Ты - опытный русскоязычный ассистент. Отвечай на русском.",
    temperature=0.7
)
```

**Решение 2**: Использовать более крупную модель
```bash
ollama pull mistral:7b  # Лучше качество
```

**Решение 3**: Fine-tune модель (продвинуто)
- Требует большего количества примеров
- Требует GPU
- Смотрите: https://ollama.ai/docs

---

## 📊 Сравнение моделей

| Модель | Размер | Скорость | Качество | Русский | RAM | GPU |
|--------|--------|----------|----------|---------|-----|-----|
| **Gemma 2b** ⭐ | 5 ГБ | ⚡⚡⚡ | ⭐⭐⭐ | ✓ | 4 ГБ | ❌ |
| **Phi 2b** | 4 ГБ | ⚡⚡⚡ | ⭐⭐ | ✓ | 4 ГБ | ❌ |
| **Mistral 7b** | 13 ГБ | ⚡⚡ | ⭐⭐⭐⭐ | ✓✓ | 8 ГБ | ✓ |
| **Llama 2 7b** | 14 ГБ | ⚡⚡ | ⭐⭐⭐⭐ | ✓ | 8 ГБ | ✓ |
| **Zephyr 7b** | 15 ГБ | ⚡⚡ | ⭐⭐⭐⭐ | ✓ | 8 ГБ | ✓ |

**Рекомендация**: 
- 4 ГБ RAM → **Gemma 2b** или **Phi 2b**
- 8 ГБ RAM → **Mistral 7b** или **Zephyr 7b** (русский лучше)
- 16+ ГБ RAM → **Llama 2 70b** (максимальное качество)

---

## 🔗 Ссылки

- **Ollama**: https://ollama.ai
- **Gemma на Hugging Face**: https://huggingface.co/google/gemma-2b
- **Документация Ollama**: https://github.com/ollama/ollama
- **Документация Transformers**: https://huggingface.co/docs/transformers

---

## 📝 Примеры использования

### Пример 1: Chat-бот

```python
from utils.providers.llm.gemma_provider import GemmaLLMProvider

provider = GemmaLLMProvider(config)
provider.initialize()

# История разговора
messages = [
    {"role": "user", "content": "Привет, Gemma!"},
]

prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
prompt += "\nassistant: "

response = provider.generate_response(
    prompt=prompt,
    system_prompt="Ты - дружелюбный ассистент.",
    temperature=0.7,
    max_tokens=256
)

print(f"Gemma: {response}")
```

### Пример 2: С потоком

```python
print("Gemma: ", end="", flush=True)

for chunk in provider.stream_response(
    prompt="Расскажи мне о Python",
    temperature=0.5,
    max_tokens=512
):
    print(chunk, end="", flush=True)

print()  # Новая строка в конце
```

### Пример 3: Интеграция с Arvis

```python
from src.core.arvis_core import ArvisCore

# В ArvisCore.__init__
def init_components():
    # ...
    gemma_provider = GemmaLLMProvider(self.config)
    self.operation_mode_manager.register_provider(gemma_provider)
    
    # Использовать с fallback
    response = self.operation_mode_manager.llm_fallback.execute(
        lambda p: p.generate_response(prompt),
        operation_name="llm_response"
    )
```

---

## ✅ Checklist установки

- [ ] Ollama установлена (`ollama --version`)
- [ ] Gemma 2b загружена (`ollama list | grep gemma`)
- [ ] Gemma запускается (`ollama run gemma:2b` → ответит на тест)
- [ ] Config.json обновлен с `gemma:2b`
- [ ] GemmaLLMProvider создан в `utils/providers/llm/`
- [ ] Тесты проходят (`pytest tests/test_gemma_provider.py`)
- [ ] Интегрировано в ArvisCore

---

**Версия документа**: 1.0  
**Статус**: Готово  
**Дата обновления**: October 21, 2025
