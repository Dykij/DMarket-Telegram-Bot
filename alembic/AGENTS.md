# AGENTS.md — Alembic Migrations

> 📖 Инструкции для AI-агентов по работе с миграциями базы данных
> Основная документация: `alembic/README.md`, `docs/DATABASE_MIGRATIONS.md`

## 🎯 Обзор модуля

**Alembic** — инструмент миграций для SQLAlchemy 2.0 с полной async поддержкой.

| Параметр           | Значение                          |
| ------------------ | --------------------------------- |
| **SQLAlchemy**     | 2.0+ с async support              |
| **База данных**    | PostgreSQL 16 / SQLite            |
| **Async драйверы** | asyncpg, aiosqlite                |
| **Метаданные**     | Combined из UserBase + TargetBase |

## ⚠️ Критические правила

### 1. NAMING_CONVENTION — ОБЯЗАТЕЛЬНО
```python
# ВСЕ constraint именуются по конвенции
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",           # Индексы
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # Unique
    "ck": "ck_%(table_name)s_%(constraint_name)s", # Check
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s", # FK
    "pk": "pk_%(table_name)s",               # Primary Key
}
```

### 2. Batch Operations для SQLite
```python
# ✅ ПРАВИЛЬНО — используй batch для SQLite совместимости
with op.batch_alter_table("users") as batch_op:
    batch_op.add_column(sa.Column("new_col", sa.String(100)))
    batch_op.drop_column("old_col")

# ❌ НЕПРАВИЛЬНО — прямые ALTER TABLE ломаются в SQLite
op.add_column("users", sa.Column("new_col", sa.String(100)))
```

### 3. Include/Exclude таблиц
```python
# Автоматически ИСКЛЮЧАЮТСЯ из autogenerate:
# - temp_* — временные таблицы
# - sqlite_* — системные SQLite таблицы
# - alembic_version — таблица версий Alembic

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        if name.startswith("temp_") or name.startswith("sqlite_"):
            return False
        if name == "alembic_version":
            return False
    return True
```

### 4. PostgreSQL оптимизации
```python
# В run_migrations_online() установлены:
# - lock_timeout='10s'      — не ждать lock дольше 10 сек
# - statement_timeout='60s' — прервать долгие запросы

# Для тяжелых миграций:
# 1. Используй CONCURRENTLY для индексов
# 2. Делай миграцию в maintenance window
# 3. Тестируй на копии production
```

## 🛠️ Основные команды

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "add_new_table"

# Применить все миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Посмотреть текущую версию
alembic current

# История миграций
alembic history --verbose

# Показать SQL без применения
alembic upgrade head --sql
```

## 📁 Структура файлов

```
alembic/
├── env.py                    # Конфигурация Alembic
├── script.py.mako            # Шаблон миграции
├── README.md                 # Документация
├── ASYNC_MIGRATIONS.md       # Async-специфика
├── BEST_PRACTICES.md         # Лучшие практики
└── versions/                 # Файлы миграций
    ├── 001_initial_migration.py
    ├── YYYYMMDD_HHMM-revision_description.py
    └── EXAMPLE_advanced_migration.py.disabled
```

## 📝 Формат имени миграции

```
YYYYMMDD_HHMM-revision_hash_description.py
│        │    │             │
│        │    │             └── Краткое описание (snake_case)
│        │    └── 12-символьный hash (автоматически)
│        └── Время создания (часы:минуты)
└── Дата создания
```

**Пример**: `20251120_2216-fb05e6a3795a_add_scan_checkpoints_table.py`

## 🧩 Шаблон миграции

```python
"""Description of changes.

Revision ID: abc123
Revises: prev_rev
Create Date: 2025-XX-XX
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "abc123"
down_revision: str | None = "prev_rev"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply migration."""
    # Создание таблицы
    op.create_table(
        "table_name",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_table_name_name", "table_name", ["name"])


def downgrade() -> None:
    """Rollback migration."""
    op.drop_table("table_name")
```

## 🔄 Data Migration шаблон

```python
from sqlalchemy import text

def upgrade() -> None:
    """Migrate data."""
    # Получить connection для data operations
    conn = op.get_bind()

    # Выполнить SELECT
    result = conn.execute(
        text("SELECT id, old_field FROM users WHERE old_field IS NOT NULL")
    )

    # Обновить данные
    for row in result:
        new_value = transform(row.old_field)
        conn.execute(
            text("UPDATE users SET new_field = :val WHERE id = :id"),
            {"val": new_value, "id": row.id}
        )


def downgrade() -> None:
    """Reverse data migration."""
    conn = op.get_bind()
    conn.execute(text("UPDATE users SET new_field = NULL"))
```

## 🗄️ Таблицы проекта (текущая схема)

| Таблица             | Назначение               | Ключевые поля                      |
| ------------------- | ------------------------ | ---------------------------------- |
| `users`             | Пользователи Telegram    | telegram_id, api_keys (encrypted)  |
| `user_preferences`  | Настройки пользователей  | default_game, notifications        |
| `targets`           | Buy Orders DMarket       | target_id, game, price, status     |
| `price_alerts`      | Ценовые алерты           | item_id, target_price, condition   |
| `trade_history`     | История сделок           | trade_type, profit, status         |
| `trading_settings`  | Настройки торговли       | max_trade_value, daily_limit       |
| `market_data_cache` | Кэш рыночных данных      | cache_key, data (JSON), expires_at |
| `scan_checkpoints`  | Checkpoints сканирования | scan_id, state, progress           |

## ✅ Чеклист перед production

- [ ] Протестировано на копии production БД
- [ ] `downgrade()` реально работает
- [ ] Нет блокирующих операций (долгих ALTER TABLE)
- [ ] Индексы созданы CONCURRENTLY (для PostgreSQL)
- [ ] Резервная копия БД создана
- [ ] Миграция занимает < 60 секунд

## 🚨 Частые ошибки

### 1. Забыли downgrade
```python
# ❌ ПЛОХО
def downgrade() -> None:
    pass  # Невозможно откатить!

# ✅ ХОРОШО
def downgrade() -> None:
    op.drop_table("new_table")
    op.drop_index("ix_new_index")
```

### 2. Не batch в SQLite
```python
# ❌ ПЛОХО — ломается в SQLite
op.alter_column("users", "name", nullable=False)

# ✅ ХОРОШО — работает везде
with op.batch_alter_table("users") as batch_op:
    batch_op.alter_column("name", nullable=False)
```

### 3. Hardcoded constraint names
```python
# ❌ ПЛОХО — конфликт с naming convention
op.create_foreign_key("fk_users_org", "users", "orgs", ["org_id"], ["id"])

# ✅ ХОРОШО — используй naming convention через metadata
# Constraint имена генерируются автоматически из NAMING_CONVENTION
```

## 📚 Связанная документация

- `alembic/README.md` — Полное руководство
- `alembic/ASYNC_MIGRATIONS.md` — Async-специфика
- `alembic/BEST_PRACTICES.md` — Лучшие практики
- `docs/DATABASE_MIGRATIONS.md` — Общая документация
- `src/models/AGENTS.md` — Модели SQLAlchemy

---

*Соответствует стандарту [AGENTS.md](https://agents.md)*
