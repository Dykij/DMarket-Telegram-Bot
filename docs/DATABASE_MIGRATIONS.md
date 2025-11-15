# 📚 Руководство по миграциям базы данных

**Дата**: 13 ноября 2025 г.
**Версия**: 1.0

---

## 📋 Оглавление

- [Введение](#введение)
- [Alembic: Основы](#alembic-основы)
- [Создание миграций](#создание-миграций)
- [Применение миграций](#применение-миграций)
- [SQLite vs PostgreSQL](#sqlite-vs-postgresql)
- [Лучшие практики](#лучшие-практики)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Введение

DMarket Telegram Bot использует **Alembic** для управления миграциями базы данных. Это позволяет:

- ✅ Версионировать схему БД
- ✅ Безопасно обновлять структуру таблиц
- ✅ Откатывать изменения при необходимости
- ✅ Синхронизировать БД между окружениями

### Поддерживаемые БД

- **PostgreSQL** (рекомендуется для production)
- **SQLite** (для разработки и тестирования)

---

## 🔧 Alembic: Основы

### Установка и инициализация

Alembic уже настроен в проекте:

```
alembic/
├── env.py              # Конфигурация окружения
├── script.py.mako      # Шаблон миграций
└── versions/           # Директория с миграциями
    └── *.py            # Файлы миграций
```

### Конфигурация

Файл `alembic.ini` содержит основные настройки:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# URL БД (можно переопределить через переменную окружения)
sqlalchemy.url = sqlite:///./bot_database.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

### Переменные окружения

Для использования PostgreSQL задайте `DATABASE_URL`:

```bash
# .env файл
DATABASE_URL=postgresql://user:password@localhost/dmarket_bot
```

Alembic автоматически использует эту переменную вместо `alembic.ini`.

---

## 📝 Создание миграций

### Автоматическая генерация

```bash
# Создать новую миграцию с автоматическим определением изменений
alembic revision --autogenerate -m "Описание изменений"
```

Пример:

```bash
alembic revision --autogenerate -m "Add user settings table"
```

Alembic сравнит текущую схему SQLAlchemy моделей с БД и создаст миграцию.

**Созданный файл** (пример):

```
alembic/versions/001_add_user_settings_table.py
```

### Ручная миграция

Если автоматическая генерация не подходит, создайте пустую миграцию:

```bash
alembic revision -m "Custom migration"
```

Затем отредактируйте файл миграции:

```python
"""Add user settings table

Revision ID: 001abc123def
Revises:
Create Date: 2025-11-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001abc123def'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Применить изменения."""
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('language', sa.String(length=10), server_default='en'),
        sa.Column('timezone', sa.String(length=50), server_default='UTC'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'])

def downgrade():
    """Откатить изменения."""
    op.drop_index('ix_user_settings_user_id', table_name='user_settings')
    op.drop_table('user_settings')
```

---

## ⚡ Применение миграций

### Проверка текущей версии

```bash
# Посмотреть текущую версию БД
alembic current
```

Вывод:

```
001abc123def (head)
```

### Просмотр истории миграций

```bash
# Показать все миграции
alembic history

# Подробная история с содержимым
alembic history --verbose
```

### Применение миграций

#### Применить все до последней (head)

```bash
alembic upgrade head
```

Вывод:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 001abc123def, Add user settings table
```

#### Применить конкретную миграцию

```bash
alembic upgrade <revision_id>
```

Пример:

```bash
alembic upgrade 001abc123def
```

#### Применить следующую миграцию

```bash
# Применить следующую (+1)
alembic upgrade +1

# Применить 2 следующие
alembic upgrade +2
```

### Откат миграций

#### Откатить на предыдущую версию

```bash
alembic downgrade -1
```

#### Откатить до конкретной версии

```bash
alembic downgrade <revision_id>
```

#### Откатить все миграции

```bash
alembic downgrade base
```

**⚠️ Внимание**: Откат удаляет данные! Используйте с осторожностью в production.

---

## 🔄 SQLite vs PostgreSQL

### Различия в миграциях

#### PostgreSQL

```python
def upgrade():
    """PostgreSQL поддерживает все операции."""
    # Можно использовать:
    op.create_schema('analytics')
    op.alter_column('users', 'email', type_=sa.String(255))
    op.add_column('users', sa.Column('verified', sa.Boolean(), server_default='false'))
```

#### SQLite

SQLite имеет ограничения на `ALTER TABLE`:

```python
def upgrade():
    """SQLite требует workaround для некоторых операций."""
    # SQLite НЕ поддерживает:
    # - ALTER COLUMN (изменение типа)
    # - DROP COLUMN (удаление колонки)
    # - ADD CONSTRAINT (кроме NOT NULL при создании)

    # Workaround: создать новую таблицу, скопировать данные, переименовать
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('verified', sa.Boolean(), server_default='false'))
```

### Совместимость с обеими БД

Используйте условное выполнение:

```python
from alembic import op, context

def upgrade():
    """Миграция совместимая с SQLite и PostgreSQL."""
    conn = op.get_bind()

    if conn.dialect.name == 'postgresql':
        # PostgreSQL специфичный код
        op.execute("CREATE SCHEMA IF NOT EXISTS analytics")

    # Общий код для обеих БД
    op.create_table(
        'market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
```

### Тип UUID

В SQLite UUID хранится как String(36):

```python
from src.utils.database import SQLiteUUID

def upgrade():
    """UUID совместимый с обеими БД."""
    op.create_table(
        'users',
        sa.Column('id', SQLiteUUID(), primary_key=True, default=uuid.uuid4),
        # SQLAlchemy автоматически использует String(36) для SQLite
        # и UUID для PostgreSQL
    )
```

---

## 🎯 Лучшие практики

### 1. Всегда тестируйте миграции

```bash
# Тестовая БД
DATABASE_URL=sqlite:///test.db alembic upgrade head

# Проверка отката
DATABASE_URL=sqlite:///test.db alembic downgrade -1
DATABASE_URL=sqlite:///test.db alembic upgrade head
```

### 2. Используйте транзакции

Alembic использует транзакции автоматически, но для сложных миграций:

```python
def upgrade():
    """Миграция с явной транзакцией."""
    with op.get_context().autocommit_block():
        # Код вне транзакции
        pass

    # Код в транзакции
    op.create_table('new_table', ...)
```

### 3. Добавляйте данные осторожно

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    """Миграция с добавлением данных."""
    # Создать таблицу
    op.create_table('roles', ...)

    # Добавить данные
    roles_table = table(
        'roles',
        column('id', sa.Integer),
        column('name', sa.String),
    )

    op.bulk_insert(
        roles_table,
        [
            {'id': 1, 'name': 'admin'},
            {'id': 2, 'name': 'user'},
        ]
    )
```

### 4. Документируйте миграции

```python
"""Add user roles and permissions

Изменения:
- Создана таблица roles
- Создана таблица permissions
- Добавлено поле role_id в users
- Добавлены начальные роли (admin, user)

Revision ID: 002xyz456abc
Revises: 001abc123def
Create Date: 2025-11-13 14:00:00.000000

"""
```

### 5. Используйте batch операции для SQLite

```python
def upgrade():
    """SQLite batch операции для совместимости."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('verified', sa.Boolean(), server_default='false'))
        batch_op.create_index('ix_users_verified', ['verified'])
```

### 6. Проверяйте схему после миграции

```bash
# После применения миграции
alembic current

# Проверить схему БД
psql -d dmarket_bot -c "\dt"  # PostgreSQL
sqlite3 bot_database.db ".schema"  # SQLite
```

---

## 🚨 Troubleshooting

### Проблема: "Target database is not up to date"

```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Решение:**

```bash
# Пометить БД как актуальную
alembic stamp head

# Или применить миграции
alembic upgrade head
```

### Проблема: Конфликт миграций

```
FAILED: Multiple head revisions are present
```

**Решение:**

```bash
# Создать merge миграцию
alembic merge -m "Merge heads" <rev1> <rev2>

# Применить merge
alembic upgrade head
```

### Проблема: Ошибка при откате

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table
```

**Решение:**

Проверьте метод `downgrade()` - он должен корректно удалять таблицы в обратном порядке:

```python
def downgrade():
    """Правильный порядок удаления."""
    # Сначала удалить foreign keys
    op.drop_constraint('fk_user_settings_user_id', 'user_settings')

    # Затем индексы
    op.drop_index('ix_user_settings_user_id')

    # Потом таблицы
    op.drop_table('user_settings')
```

### Проблема: SQLite doesn't support ALTER COLUMN

```
NotImplementedError: ALTER COLUMN is not supported by SQLite
```

**Решение:**

Используйте `batch_alter_table`:

```python
def upgrade():
    """Изменение колонки в SQLite."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'email',
            type_=sa.String(255),
            existing_type=sa.String(100)
        )
```

### Проблема: Production миграция failed

**Решение:**

1. **Остановите приложение**:

   ```bash
   systemctl stop dmarket-bot
   ```

2. **Сделайте backup БД**:

   ```bash
   pg_dump dmarket_bot_prod > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Откатите миграцию**:

   ```bash
   alembic downgrade -1
   ```

4. **Проверьте данные**:

   ```bash
   psql -d dmarket_bot_prod
   ```

5. **Исправьте миграцию** и повторите

6. **Запустите приложение**:

   ```bash
   systemctl start dmarket-bot
   ```

---

## 📊 Workflow миграций

### Development

```bash
# 1. Изменить модели SQLAlchemy в src/utils/database.py
vim src/utils/database.py

# 2. Создать миграцию
alembic revision --autogenerate -m "Add new column to users"

# 3. Проверить миграцию
vim alembic/versions/003_add_new_column.py

# 4. Применить локально
DATABASE_URL=sqlite:///test.db alembic upgrade head

# 5. Тестировать
python -m pytest tests/test_database.py

# 6. Коммит
git add alembic/versions/003_add_new_column.py
git commit -m "feat(db): add new column to users table"
```

### Staging

```bash
# 1. Pull последних изменений
git pull origin main

# 2. Backup БД
pg_dump dmarket_bot_staging > backup.sql

# 3. Применить миграции
DATABASE_URL=postgresql://user:pass@staging/db alembic upgrade head

# 4. Проверить
alembic current
```

### Production

```bash
# 1. Backup
pg_dump dmarket_bot_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Maintenance mode
systemctl stop dmarket-bot

# 3. Применить миграции
DATABASE_URL=postgresql://user:pass@prod/db alembic upgrade head

# 4. Проверить схему
psql -d dmarket_bot_prod -c "\dt"

# 5. Старт приложения
systemctl start dmarket-bot

# 6. Проверка логов
journalctl -u dmarket-bot -f
```

---

## 📚 Дополнительные ресурсы

- [Официальная документация Alembic](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLite ALTER TABLE Limitations](https://www.sqlite.org/lang_altertable.html)

---

## ✅ Чеклист миграции

Перед применением миграции в production:

- [ ] Создан backup БД
- [ ] Миграция протестирована локально
- [ ] Миграция протестирована на staging
- [ ] Метод `downgrade()` реализован и протестирован
- [ ] Миграция совместима с SQLite и PostgreSQL (если нужно)
- [ ] Документация обновлена
- [ ] Приложение остановлено (если требуется downtime)
- [ ] План отката подготовлен
- [ ] Команда уведомлена о maintenance window

---

**Версия документа**: 1.0
**Последнее обновление**: 13 ноября 2025 г.

Для вопросов и проблем создавайте Issue на GitHub.
