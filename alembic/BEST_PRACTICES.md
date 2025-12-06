# Alembic Migrations - Best Practices

**Дата**: 19 ноября 2025 г.
**Версия**: 2.0

---

## 📋 Оглавление

- [Основы](#основы)
- [Создание миграций](#создание-миграций)
- [Naming Conventions](#naming-conventions)
- [Batch Operations](#batch-operations)
- [Data Migrations](#data-migrations)
- [Тестирование миграций](#тестирование-миграций)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Основы

### Текущая конфигурация

- **Naming conventions**: Все constraint'ы именуются автоматически по стандартной схеме
- **Autogenerate**: Включено с `compare_type=True` и `compare_server_default=True`
- **Batch operations**: Автоматически для SQLite
- **Include/exclude**: Фильтрация временных таблиц и системных объектов

### Основные команды

```bash
# Создать новую миграцию (autogenerate)
alembic revision --autogenerate -m "Описание изменений"

# Создать пустую миграцию (для data migrations)
alembic revision -m "Data migration: описание"

# Применить миграции
alembic upgrade head

# Откатить одну миграцию
alembic downgrade -1

# Посмотреть текущую версию БД
alembic current

# Посмотреть историю миграций
alembic history

# Генерация SQL без выполнения (для review)
alembic upgrade head --sql > migration.sql
```

---

## 🔧 Создание миграций

### 1. Schema Migrations (автоматически)

**Используйте autogenerate**, но **ВСЕГДА проверяйте** сгенерированный код:

```bash
# Шаг 1: Изменить модели в src/models/
# Шаг 2: Создать миграцию
alembic revision --autogenerate -m "Add user_settings table"

# Шаг 3: ОБЯЗАТЕЛЬНО проверить сгенерированный файл
# alembic/versions/XXXX_add_user_settings_table.py

# Шаг 4: Применить миграцию
alembic upgrade head
```

**❗ Важно**: Autogenerate может пропустить:
- Изменения типов колонок (особенно в SQLite)
- Изменения в enums
- Изменения в check constraints
- Partitioning таблиц
- Materialized views

### 2. Data Migrations (вручную)

Для миграций данных создавайте **пустую миграцию** и используйте SQLAlchemy Core:

```python
"""Add default preferences for existing users.

Revision ID: 002
Revises: 001
Create Date: 2025-11-19 12:00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column

# revision identifiers
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """Add default preferences for all existing users."""
    # Используйте SQLAlchemy Core вместо raw SQL
    conn = op.get_bind()

    # Определите таблицу (без импорта моделей!)
    users = table(
        'users',
        column('id', sa.String),
        column('telegram_id', sa.BigInteger),
    )

    user_preferences = table(
        'user_preferences',
        column('id', sa.String),
        column('user_id', sa.String),
        column('default_game', sa.String),
        column('notification_enabled', sa.Boolean),
    )

    # Получить всех пользователей
    stmt = sa.select(users.c.id, users.c.telegram_id)
    existing_users = conn.execute(stmt).fetchall()

    # Создать настройки по умолчанию
    for user in existing_users:
        insert_stmt = user_preferences.insert().values(
            id=f"pref_{user.id}",
            user_id=user.id,
            default_game="csgo",
            notification_enabled=True,
        )
        conn.execute(insert_stmt)


def downgrade() -> None:
    """Remove preferences added in upgrade."""
    # Обратная операция
    conn = op.get_bind()

    user_preferences = table(
        'user_preferences',
        column('id', sa.String),
    )

    # Удалить только те настройки, которые были созданы миграцией
    stmt = user_preferences.delete().where(
        user_preferences.c.id.like('pref_%')
    )
    conn.execute(stmt)
```

### 3. Complex Schema Changes (Stairway Pattern)

Для сложных изменений используйте **stairway pattern** — разбивайте на несколько миграций:

**Миграция 1**: Добавить новую колонку (nullable)
```python
def upgrade() -> None:
    """Add new_column as nullable."""
    op.add_column('users', sa.Column('new_column', sa.String(), nullable=True))
```

**Миграция 2**: Заполнить данные
```python
def upgrade() -> None:
    """Populate new_column with data."""
    conn = op.get_bind()
    # ... populate data
```

**Миграция 3**: Сделать NOT NULL
```python
def upgrade() -> None:
    """Make new_column non-nullable."""
    op.alter_column('users', 'new_column', nullable=False)
```

---

## 📏 Naming Conventions

Проект использует **автоматические naming conventions**:

```python
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",                           # Индексы
    "uq": "uq_%(table_name)s_%(column_0_name)s",            # Unique
    "ck": "ck_%(table_name)s_%(constraint_name)s",          # Check
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # FK
    "pk": "pk_%(table_name)s",                               # Primary Key
}
```

**Примеры**:
- `ix_users_telegram_id` - индекс на `users.telegram_id`
- `uq_users_username` - unique constraint на `users.username`
- `fk_targets_user_id_users` - foreign key от `targets.user_id` к `users`

**✅ Правильно**:
```python
op.create_index('ix_users_email', 'users', ['email'])
```

**❌ Неправильно**:
```python
op.create_index('my_custom_index_name', 'users', ['email'])  # Не следует схеме
```

---

## ⚡ Batch Operations

### Для SQLite

SQLite не поддерживает многие ALTER операции. Используйте **batch mode**:

```python
def upgrade() -> None:
    """Add column to users table (SQLite-compatible)."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(20), nullable=True))
        batch_op.create_index('ix_users_phone', ['phone'])
```

### Для PostgreSQL (оптимизация)

Для больших таблиц используйте batch operations с lock timeout:

```python
def upgrade() -> None:
    """Add index with reduced lock time."""
    # Установить таймаут блокировки
    op.execute("SET lock_timeout = '5s'")

    # Создать индекс конкурентно (без блокировки таблицы)
    op.create_index(
        'ix_users_created_at',
        'users',
        ['created_at'],
        postgresql_concurrently=True,
    )
```

---

## 📊 Data Migrations

### Правила для data migrations:

1. **НЕ импортируйте модели** из `src/models/` в миграции
2. **Используйте SQLAlchemy Core** (`table()`, `column()`)
3. **Обрабатывайте большие объемы данных порциями**
4. **Всегда пишите downgrade()**

### Пример: Batch processing

```python
def upgrade() -> None:
    """Update prices for all items (batch processing)."""
    conn = op.get_bind()

    items = table('items', column('id', sa.Integer), column('price', sa.Float))

    # Обработка по 1000 записей
    batch_size = 1000
    offset = 0

    while True:
        stmt = sa.select(items.c.id, items.c.price).limit(batch_size).offset(offset)
        batch = conn.execute(stmt).fetchall()

        if not batch:
            break

        for item in batch:
            # Обновить цену
            update_stmt = items.update().where(
                items.c.id == item.id
            ).values(price=item.price * 1.1)
            conn.execute(update_stmt)

        offset += batch_size
```

---

## 🧪 Тестирование миграций

### Локальное тестирование

```bash
# 1. Создать тестовую БД
createdb dmarket_test

# 2. Применить все миграции
DATABASE_URL=postgresql://user:pass@localhost/dmarket_test alembic upgrade head

# 3. Откатить все миграции
alembic downgrade base

# 4. Повторно применить
alembic upgrade head
```

### Pytest интеграция

```python
# tests/test_migrations.py
import pytest
from alembic import command
from alembic.config import Config


@pytest.fixture
def alembic_config():
    """Создать Alembic конфигурацию для тестов."""
    config = Config("alembic.ini")
    return config


def test_migrations_upgrade_downgrade(alembic_config, test_database):
    """Тест полного цикла миграций."""
    # Применить все миграции
    command.upgrade(alembic_config, "head")

    # Откатить все миграции
    command.downgrade(alembic_config, "base")

    # Повторно применить
    command.upgrade(alembic_config, "head")


def test_migration_data_integrity(alembic_config, test_database):
    """Тест сохранности данных при миграции."""
    # Применить миграции до определенной версии
    command.upgrade(alembic_config, "001")

    # Добавить тестовые данные
    # ...

    # Применить новую миграцию
    command.upgrade(alembic_config, "002")

    # Проверить что данные сохранились
    # ...
```

---

## 🔍 Troubleshooting

### Проблема: "Target database is not up to date"

```bash
# Посмотреть текущую версию
alembic current

# Посмотреть pending миграции
alembic heads

# Решение: применить миграции
alembic upgrade head
```

### Проблема: Конфликт миграций (multiple heads)

```bash
# Посмотреть heads
alembic heads

# Создать merge миграцию
alembic merge -m "Merge branches" head1 head2
```

### Проблема: Autogenerate не видит изменения

**Причины**:
1. Модели не импортированы в `env.py`
2. Изменения в типах данных (SQLite)
3. Изменения в enums

**Решение**:
```python
# alembic/env.py
# Убедитесь что все Base импортированы
from src.models.user import Base as UserBase
from src.models.target import Base as TargetBase
# ... другие модели
```

### Проблема: Ошибка при применении миграции

```bash
# Откатить на одну миграцию назад
alembic downgrade -1

# Посмотреть SQL без выполнения
alembic upgrade head --sql

# Применить с подробным логированием
alembic upgrade head -v
```

---

## 📚 Дополнительные ресурсы

- [Официальная документация Alembic](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html)

---

## ⚠️ Важные напоминания

1. **НИКОГДА не доверяйте autogenerate на 100%** - всегда проверяйте сгенерированный код
2. **Всегда пишите downgrade()** - даже если это `pass` или `raise NotImplementedError()`
3. **НЕ импортируйте модели** в миграции - используйте SQLAlchemy Core
4. **Тестируйте миграции** перед применением в production
5. **Используйте осмысленные сообщения** при создании миграций
6. **Генерируйте SQL для review** перед production deployment

---

**Версия документа**: 2.0
**Последнее обновление**: 19 ноября 2025 г.
