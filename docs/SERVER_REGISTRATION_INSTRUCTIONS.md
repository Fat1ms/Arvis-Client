# 📋 ИНСТРУКЦИЯ ДЛЯ РАЗРАБОТЧИКА СЕРВЕРА

## 🎯 Контекст задачи

**Проблема:** Пользователи, созданные через клиент Arvis, не появляются на странице сервера.

**Диагностика клиента показала:**
- ✅ Конфигурация клиента настроена правильно (`use_remote_server: true`)
- ✅ Клиент использует правильный URL сервера (`http://192.168.0.130:8000`)
- ✅ Код клиента исправлен - локальное создание пользователей отключено
- ✅ Клиент корректно вызывает `POST /api/client/register`

**Вывод:** Если после исправлений клиента проблема сохраняется, возможна проблема на стороне сервера.

---

## 🔍 Что нужно проверить на сервере

### 1. Проверка endpoint `/api/client/register`

**Файл:** `api/client.py`

**Проверить:**
```python
@router.post("/register")
async def register_user(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Регистрация нового пользователя
    """
    # ✅ УБЕДИТЕСЬ, что пользователь СОХРАНЯЕТСЯ в БД
    # ✅ УБЕДИТЕСЬ, что commit() вызывается
    # ✅ УБЕДИТЕСЬ, что возвращается user_id
    
    # Пример правильной реализации:
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role="user",
        is_active=True
    )
    
    db.add(user)
    db.commit()  # ← КРИТИЧНО! Без этого пользователь не сохранится
    db.refresh(user)  # ← Получить ID из БД
    
    return {
        "success": True,
        "message": "User registered successfully",
        "user_id": user.id,  # ← Вернуть ID
        "access_token": generate_token(user)
    }
```

### 2. Проверка схемы базы данных

**Файл:** `database/models.py` или `models/user.py`

**Убедитесь, что таблица `users` существует:**
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # ... другие поля
```

**Проверить в консоли:**
```bash
# SQLite
sqlite3 arvis.db ".schema users"

# PostgreSQL
psql -U arvis_user -d arvis_db -c "\d users"
```

### 3. Проверка CORS настроек

**Файл:** `main.py`

**Убедитесь, что CORS настроен правильно:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или конкретные IP клиентов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Проверка логов сервера

**Найдите логи сервера** (обычно `logs/`, `uvicorn.log`, `app.log`)

**Ищите записи при регистрации:**
```log
✅ ПРАВИЛЬНО:
POST /api/client/register
Creating user: testuser
User saved to database: testuser (ID: abc123)
Response: 200

❌ НЕПРАВИЛЬНО:
POST /api/client/register
Error: duplicate key constraint
Response: 500
```

### 5. Тестовый скрипт для сервера

**Создайте файл `test_registration_endpoint.py`:**
```python
"""
Тест endpoint регистрации на сервере
"""
import requests
import time

SERVER_URL = "http://192.168.0.130:8000"
username = f"servertest_{int(time.time())}"

# Тест регистрации
response = requests.post(
    f"{SERVER_URL}/api/client/register",
    json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "TestPass123!",
        "full_name": "Server Test User"
    },
    timeout=10
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    print("✓ Registration endpoint works!")
    user_id = response.json().get("user_id")
    
    # Проверяем, что пользователь в БД
    print(f"\nNow check database for user: {username} (ID: {user_id})")
    print("Run: python check_users.py")
else:
    print("✗ Registration failed!")
    print(f"Error: {response.json().get('detail')}")
```

**Запуск:**
```bash
cd /path/to/arvis-server
python test_registration_endpoint.py
```

### 6. Проверка check_users.py

**Убедитесь, что скрипт работает правильно:**
```python
"""
Проверка пользователей в базе данных
"""
from database.db import SessionLocal
from models.user import User

def check_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Total users in database: {len(users)}")
        print("\nUsers:")
        for user in users:
            print(f"  - {user.username} ({user.role}) - {user.email}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
```

---

## 🔧 Возможные проблемы и решения

### Проблема 1: Пользователь создаётся, но не коммитится

**Симптом:** API возвращает 200, но пользователя нет в БД.

**Причина:** Отсутствует `db.commit()`

**Решение:**
```python
# ❌ НЕПРАВИЛЬНО:
db.add(user)
# ... return response (без commit)

# ✅ ПРАВИЛЬНО:
db.add(user)
db.commit()  # ← Добавить это!
db.refresh(user)
```

### Проблема 2: Транзакция откатывается

**Симптом:** Пользователь создаётся, но потом исчезает.

**Причина:** Необработанное исключение после commit.

**Решение:**
```python
try:
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"success": True, "user_id": user.id}
except Exception as e:
    db.rollback()
    logger.error(f"Registration failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Проблема 3: Неправильная схема БД

**Симптом:** Ошибка "column not found" или "no such table".

**Причина:** Миграции не применены.

**Решение:**
```bash
# Alembic
alembic upgrade head

# Или пересоздать БД
python -c "from database.db import Base, engine; Base.metadata.create_all(engine)"
```

### Проблема 4: Дублирование пользователей

**Симптом:** Ошибка "username already exists".

**Причина:** Проверка существования не работает.

**Решение:**
```python
# Добавить проверку перед созданием
existing_user = db.query(User).filter(
    (User.username == user_data.username) | 
    (User.email == user_data.email)
).first()

if existing_user:
    raise HTTPException(status_code=400, detail="User already exists")
```

### Проблема 5: Неправильная сессия БД

**Симптом:** Пользователи создаются в одной сессии, но не видны в другой.

**Причина:** Изоляция транзакций.

**Решение:**
```python
# Убедитесь, что используете правильную зависимость
from database.db import get_db

@router.post("/register")
async def register_user(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)  # ← Правильная инжекция
):
    # ...
```

---

## 📊 Чеклист для проверки сервера

- [ ] Endpoint `/api/client/register` существует и доступен
- [ ] В коде есть `db.commit()` после создания пользователя
- [ ] Endpoint возвращает `user_id` в ответе
- [ ] Таблица `users` существует в БД
- [ ] Миграции применены (`alembic upgrade head`)
- [ ] CORS настроен правильно
- [ ] Тестовый скрипт `test_registration_endpoint.py` проходит
- [ ] `check_users.py` показывает новых пользователей
- [ ] Логи сервера не содержат ошибок при регистрации
- [ ] Нет необработанных исключений в endpoint

---

## 🧪 Полный тест сервера

**Выполните последовательно:**

```bash
# 1. Проверка здоровья сервера
curl http://192.168.0.130:8000/health
# Ожидается: {"status":"healthy","database":"connected"}

# 2. Проверка версии API
curl http://192.168.0.130:8000/version
# Ожидается: {"version":"1.0.0",...}

# 3. Тестовая регистрация
curl -X POST http://192.168.0.130:8000/api/client/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"curltest",
    "email":"curltest@test.com",
    "password":"TestPass123!",
    "full_name":"Curl Test"
  }'
# Ожидается: {"success":true,"user_id":"..."}

# 4. Проверка в БД
python check_users.py
# Ожидается: пользователь "curltest" в списке
```

---

## 📞 Связь с клиентской командой

**Если всё работает на сервере, но проблема остаётся:**

1. Сообщите клиентской команде:
   - ✅ Endpoint работает корректно
   - ✅ Пользователи сохраняются в БД
   - ✅ Тестовая регистрация через curl прошла успешно

2. Попросите клиентскую команду:
   - Запустить `test_client_registration.py`
   - Предоставить логи клиента при регистрации
   - Проверить сетевое подключение (ping, traceroute)

3. Проверьте совместно:
   - Версии клиента и сервера совместимы
   - Формат запросов клиента соответствует ожидаемому серверу
   - Нет прокси/VPN между клиентом и сервером

---

## 📄 Документация

**Связанные документы:**
- `CLIENT_REGISTRATION_FIX.md` - Исправления на стороне клиента
- `CLIENT_API_GUIDE.md` - Полная документация Client API
- `SERVER_TROUBLESHOOTING.md` - Общая диагностика сервера

**Версия:** 1.0  
**Дата:** 09.10.2025  
**Автор:** Copilot (GitHub)

---

## ⚠️ Важно

**ДЛЯ РАЗРАБОТЧИКА СЕРВЕРА:**

Эта инструкция создана на основе диагностики клиента. Если после всех проверок проблема сохраняется, скорее всего:

1. **Отсутствует `db.commit()`** в endpoint регистрации
2. **Транзакция откатывается** из-за ошибки
3. **Схема БД не соответствует коду** (нет миграций)
4. **Неправильная сессия БД** (изоляция транзакций)

**Начните с проверки пункта 1 - это самая частая причина!**
