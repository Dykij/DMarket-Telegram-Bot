# Async Migrations with Alembic

## 🚀 Overview

Alembic теперь полностью поддерживает **асинхронные миграции** для SQLAlchemy 2.0.

### Возможности

- ✅ **Автоматическое определение async/sync** - на основе DATABASE_URL
- ✅ **Type comparison** - обнаружение изменений типов колонок
- ✅ **Server default comparison** - отслеживание изменений DEFAULT значений
- ✅ **PostgreSQL lock timeout** - предотвращение долгих блокировок (10s)
- ✅ **SQLite batch operations** - безопасные миграции для SQLite
- ✅ **Zero-downtime migrations** - async не блокирует event loop

## 📝 Использование

### Sync Migrations (по умолчанию)

```bash
# SQLite sync
export DATABASE_URL="sqlite:///bot_database.db"
alembic upgrade head

# PostgreSQL sync
export DATABASE_URL="postgresql://user:pass@localhost/db"
alembic upgrade head
```

### Async Migrations (новое!)

```bash
# SQLite async
export DATABASE_URL="sqlite+aiosqlite:///bot_database.db"
alembic upgrade head

# PostgreSQL async
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
alembic upgrade head
```

### Создание миграции

```bash
# Автогенерация миграции с type detection
alembic revision --autogenerate -m "Add user table"

# Результат будет включать:
# - Type changes (e.g., String(50) -> String(100))
# - Server default changes
# - Index changes
# - Constraint changes
```

## 🔧 Примеры миграций

### Добавление колонки с default

```python
def upgrade():
    op.add_column(
        'users',
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False)
    )

def downgrade():
    op.drop_column('users', 'is_active')
```

### Изменение типа колонки

```python
def upgrade():
    # Alembic автоматически обнаружит это изменение
    # благодаря compare_type=True
    op.alter_column(
        'users',
        'username',
        existing_type=sa.String(length=50),
        type_=sa.String(length=100),
        existing_nullable=False
    )

def downgrade():
    op.alter_column(
        'users',
        'username',
        existing_type=sa.String(length=100),
        type_=sa.String(length=50),
        existing_nullable=False
    )
```

### SQLite batch migration

```python
# Для SQLite миграции автоматически используют batch mode
def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(20), nullable=True))
        batch_op.create_index('ix_users_phone', ['phone'])

def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_phone')
        batch_op.drop_column('phone')
```

## 🎯 Best Practices

### 1. Всегда тестируйте миграции локально

```bash
# Проверить что будет создано
alembic upgrade head --sql > migration.sql

# Применить миграцию
alembic upgrade head

# Откатить если что-то пошло не так
alembic downgrade -1
```

### 2. Используйте транзакции

Миграции автоматически выполняются в транзакциях для безопасности.

### 3. Проверяйте schema drift

```bash
# Создать миграцию для обнаружения дрейфа схемы
alembic revision --autogenerate -m "Check schema drift"

# Если файл пустой - дрейфа нет
```

### 4. Lock timeouts для production

PostgreSQL автоматически использует:
- `lock_timeout = 10s` - макс. время ожидания блокировки
- `statement_timeout = 60s` - макс. время выполнения запроса

## ⚠️ Troubleshooting

### Проблема: "No changes detected"

**Решение:**
```bash
# 1. Убедитесь, что модели импортированы в env.py
# 2. Проверьте PYTHONPATH
export PYTHONPATH=$(pwd)

# 3. Проверьте target_metadata
alembic current
```

### Проблема: "Driver not found"

**Async drivers:**
```bash
# SQLite async
pip install aiosqlite

# PostgreSQL async
pip install asyncpg

# MySQL async
pip install aiomysql
```

### Проблема: "Lock timeout"

**Для production:**
```sql
-- Увеличить timeout в migration
connection.execute("SET lock_timeout = '30s'")
```

## 📚 Документация

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Schema Comparison](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#comparing-types)

---

**Версия**: 1.0
**Автор**: Production-grade improvements team
**Дата**: 22 ноября 2025 г.
