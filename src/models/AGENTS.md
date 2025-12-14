# AGENTS.md — Models Module

> 📖 SQLAlchemy модели данных для DMarket Telegram Bot
> Полные инструкции: `.github/copilot-instructions.md`

## 🏗️ Структура модуля

```
src/models/
├── base.py       # DeclarativeBase + SQLiteUUID type
├── user.py       # User model (telegram users)
├── target.py     # Target + TradeHistory models
├── market.py     # MarketData + MarketDataCache
├── log.py        # CommandLog model
└── alert.py      # UserAlert model
```

## ⚠️ Критические правила

### 1. UUID vs Integer

```python
# User, MarketData - используют UUID
from src.models.base import Base, UUIDType
id = Column(UUIDType, primary_key=True, default=uuid4)

# Target, TradeHistory - используют Integer (autoincrement)
id = Column(Integer, primary_key=True, autoincrement=True)
```

### 2. Timezone-aware datetime

```python
# ✅ ПРАВИЛЬНО - с timezone
from datetime import UTC, datetime
created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

# ❌ НЕПРАВИЛЬНО - deprecated
created_at = Column(DateTime, default=datetime.utcnow)  # utcnow deprecated!
```

### 3. Индексы

**ВСЕГДА** создавай индексы для:
- Foreign keys (`user_id`, `telegram_id`)
- Часто запрашиваемых полей (`status`, `game`, `cache_key`)
- Полей для фильтрации (`is_active`, `expires_at`)

```python
telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
status = Column(String(50), default="active", index=True)
```

## 📊 Модели

### User (`user.py`)

| Поле                           | Тип         | Описание                           |
| ------------------------------ | ----------- | ---------------------------------- |
| `id`                           | UUID        | Первичный ключ                     |
| `telegram_id`                  | BigInteger  | Telegram user ID (unique, indexed) |
| `username`                     | String(255) | @username                          |
| `language_code`                | String(10)  | Язык (default: "en")               |
| `is_active`                    | Boolean     | Активен ли пользователь            |
| `is_admin`                     | Boolean     | Права админа                       |
| `is_banned`                    | Boolean     | Заблокирован                       |
| `dmarket_api_key_encrypted`    | Text        | Зашифрованный API ключ             |
| `dmarket_secret_key_encrypted` | Text        | Зашифрованный секрет               |

**Важно**: API ключи хранятся **ЗАШИФРОВАННЫМИ** (Fernet encryption).

### Target (`target.py`)

| Поле         | Тип         | Описание                  |
| ------------ | ----------- | ------------------------- |
| `id`         | Integer     | Autoincrement PK          |
| `user_id`    | BigInteger  | Telegram ID пользователя  |
| `target_id`  | String(255) | ID таргета от DMarket     |
| `game`       | String(50)  | csgo, dota2, tf2, rust    |
| `title`      | String(500) | Название предмета         |
| `price`      | Float       | Цена в USD                |
| `status`     | String(50)  | active/inactive/completed |
| `attributes` | JSON        | Float, phase, pattern     |

**Статусы таргетов**:
- `active` - активен, ожидает исполнения
- `inactive` - приостановлен
- `completed` - исполнен
- `cancelled` - отменен

### MarketDataCache (`market.py`)

| Поле         | Тип         | Описание            |
| ------------ | ----------- | ------------------- |
| `cache_key`  | String(500) | Ключ кэша (unique)  |
| `game`       | String(50)  | Код игры            |
| `data_type`  | String(50)  | Тип данных          |
| `data`       | JSON        | Кэшированные данные |
| `expires_at` | DateTime    | Время истечения     |

## 🔄 CRUD операции

### Async сессия

```python
from sqlalchemy.ext.asyncio import async_sessionmaker

async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

### Создание записи

```python
async def create_target(session: AsyncSession, data: dict) -> Target:
    target = Target(
        user_id=data["user_id"],
        target_id=data["target_id"],
        game=data["game"],
        title=data["title"],
        price=data["price"],
    )
    session.add(target)
    await session.commit()
    return target
```

### Bulk операции

```python
# Используй add_all для массовых вставок
session.add_all([Target(...) for _ in range(100)])
await session.commit()
```

## 🧪 Тестирование моделей

### Fixtures

```python
@pytest.fixture
async def db_session():
    """Async test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession)
    async with async_session() as session:
        yield session
```

### Тест примеры

```python
@pytest.mark.asyncio
async def test_user_creation(db_session):
    """Test user model creation."""
    user = User(
        telegram_id=123456789,
        username="test_user",
        language_code="ru"
    )
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.is_active is True
    assert user.is_admin is False
```

## 📐 Миграции (Alembic)

При изменении моделей:

```bash
# Создать миграцию
alembic revision --autogenerate -m "Add new field"

# Применить
alembic upgrade head
```

**Правила миграций**:
1. Всегда тестируй на копии prod БД
2. Делай бэкап перед миграцией
3. Используй `nullable=True` для новых полей
4. Для больших таблиц - batch миграции

## 🔗 Связи между моделями

```
User (1) ──── (N) Target
User (1) ──── (N) TradeHistory
User (1) ──── (N) CommandLog
User (1) ──── (N) UserAlert
```

**Внимание**: Связи через `user_id` (telegram_id), НЕ через UUID!

## 📚 Документация

- **Alembic**: `alembic/README.md`, `alembic/BEST_PRACTICES.md`
- **Async Migrations**: `alembic/ASYNC_MIGRATIONS.md`
- **Database Guide**: `docs/DATABASE_MIGRATIONS.md`

---

*Следуй `.github/copilot-instructions.md` для полных правил разработки.*
