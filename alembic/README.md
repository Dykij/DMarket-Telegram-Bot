# 🗄️ Database Migrations (Alembic)

Эта папка содержит миграции базы данных для проекта DMarket Telegram Bot.

---

## 📁 Структура

```
alembic/
├── README.md                     # Этот файл (краткий обзор)
├── README_DETAILED.md            # Подробное руководство по best practices
├── env.py                        # Конфигурация Alembic environment
├── script.py.mako                # Шаблон для новых миграций
└── versions/                     # Папка с миграциями
    ├── 001_initial_migration.py  # Начальная миграция
    └── EXAMPLE_advanced_migration.py.disabled  # Примеры паттернов
```

---

## 🚀 Быстрый старт

### Создать новую миграцию (autogenerate)

```bash
alembic revision --autogenerate -m "Краткое описание изменений"
```

### Применить миграции

```bash
alembic upgrade head
```

### Откатить последнюю миграцию

```bash
alembic downgrade -1
```

### Посмотреть текущую версию БД

```bash
alembic current
```

---

## ✨ Ключевые улучшения

### 1. **Naming Conventions**

Все constraint'ы автоматически именуются по стандарту:

- `ix_table_column` - индексы
- `uq_table_column` - unique constraints
- `fk_table_column_reftable` - foreign keys
- `pk_table` - primary keys

### 2. **Include/Exclude Logic**

Автоматически исключаются из миграций:

- Временные таблицы (`temp_*`)
- SQLite системные таблицы (`sqlite_*`)
- Alembic версионная таблица (`alembic_version`)

### 3. **Batch Operations (SQLite)**

Автоматически используется batch mode для SQLite для операций ALTER TABLE.

### 4. **PostgreSQL Оптимизации**

- Таймауты блокировок (`lock_timeout = 5s`)
- Таймауты запросов (`statement_timeout = 60s`)
- Поддержка concurrent индексов

### 5. **Type Comparison**

Включено сравнение типов (`compare_type=True`) и server defaults (`compare_server_default=True`).

---

## 📚 Примеры использования

### Создание таблицы

```python
def upgrade() -> None:
    """Create notifications table."""
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('is_read', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # Индексы создаются автоматически по naming convention
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
```

### Data Migration

```python
def upgrade() -> None:
    """Set default game for existing users."""
    conn = op.get_bind()

    users = table('users', column('id', sa.String))

    stmt = sa.update(users).where(
        users.c.default_game.is_(None)
    ).values(default_game='csgo')

    conn.execute(stmt)
```

### Batch Operations (SQLite)

```python
def upgrade() -> None:
    """Add column (SQLite-compatible)."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(20)))
        batch_op.create_index('ix_users_phone', ['phone'])
```

---

## ⚠️ Важные правила

1. **ВСЕГДА проверяйте autogenerate** - не доверяйте на 100%
2. **ВСЕГДА пишите downgrade()** - даже если это `pass`
3. **НЕ импортируйте модели** - используйте SQLAlchemy Core
4. **Тестируйте миграции** перед production
5. **Используйте осмысленные сообщения** при создании миграций

---

## 🔍 Troubleshooting

### Autogenerate не видит изменения?

Проверьте что модели импортированы в `env.py`:

```python
from src.models.user import Base as UserBase
from src.models.target import Base as TargetBase
```

### Ошибка при применении миграции?

```bash
# Откатить на шаг назад
alembic downgrade -1

# Посмотреть SQL без выполнения
alembic upgrade head --sql
```

### Конфликт миграций (multiple heads)?

```bash
# Создать merge миграцию
alembic merge -m "Merge branches" head1 head2
```

---

## 📖 Дополнительная документация

- **[README_DETAILED.md](README_DETAILED.md)** - Подробное руководство с best practices
- **[EXAMPLE_advanced_migration.py.disabled](versions/EXAMPLE_advanced_migration.py.disabled)** - Примеры advanced паттернов
- **[Официальная документация Alembic](https://alembic.sqlalchemy.org/)**

---

## 🎯 Checklist перед production

- [ ] Миграция протестирована локально
- [ ] Написана функция `downgrade()`
- [ ] Сгенерирован SQL для review: `alembic upgrade head --sql > migration.sql`
- [ ] Проверено что нет блокирующих операций для больших таблиц
- [ ] Добавлены комментарии для сложных операций
- [ ] Миграция применена на staging окружении

---

**Версия**: 2.0
**Последнее обновление**: Январь 2026
