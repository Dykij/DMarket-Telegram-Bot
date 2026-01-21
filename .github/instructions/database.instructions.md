---
description: 'Database model and migration conventions'
applyTo: 'src/models/**/*.py, alembic/**/*.py'
---

# Database Instructions

Apply these conventions to database models and migrations:

## SQLAlchemy 2.0 Style

```python
from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    balance: Mapped[float] = mapped_column(Float, default=0.0)
```

## Async Session Pattern

```python
async with async_session() as session:
    async with session.begin():
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
```

## Migrations (Alembic)
- Never modify existing migrations
- Create new migration for each change
- Use descriptive revision messages
- Test migrations both up and down

## Indexes
- Always index foreign keys
- Index frequently queried columns
- Use composite indexes for common query patterns

## Naming Conventions
- Tables: plural snake_case (users, order_items)
- Columns: singular snake_case (user_id, created_at)
- Constraints: descriptive names (uq_users_telegram_id)
