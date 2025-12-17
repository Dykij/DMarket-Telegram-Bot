# State Management & Auto-Recovery Guide

**Дата**: 17 декабря 2025 г.
**Версия**: 1.0

---

## Обзор

Модуль `state_manager.py` обеспечивает сохранение состояния и автоматическое восстановление для длительных операций, таких как сканирование рынка. Это критично важно для single-user режима, где бот должен работать 24/7 без потери прогресса при сбоях.

## Ключевые возможности

### 1. Checkpoint System

- ✅ Автоматическое сохранение прогресса каждые N предметов
- ✅ Восстановление из последнего checkpoint при перезапуске
- ✅ Поддержка cursor-based пагинации
- ✅ Метаданные для контекста операции

### 2. Graceful Shutdown

- ✅ Обработка SIGTERM/SIGINT signals
- ✅ Сохранение финального checkpoint перед выходом
- ✅ Cleanup callbacks для ресурсов

### 3. Recovery Mechanisms

- ✅ Автоматическое обнаружение незавершенных операций
- ✅ Продолжение с последнего checkpoint
- ✅ Очистка старых checkpoints (>7 дней)

---

## Использование

### Базовый пример

```python
from uuid import uuid4
from src.utils.state_manager import StateManager
from src.utils.database import get_session

async def scan_market_with_recovery():
    """Сканирование рынка с checkpoint system."""
    async with get_session() as session:
        state_manager = StateManager(
            session=session,
            checkpoint_interval=100  # Сохранять каждые 100 предметов
        )

        # Создать новый scan
        scan_id = uuid4()
        await state_manager.create_checkpoint(
            scan_id=scan_id,
            user_id=123456789,
            operation_type="market_scan",
            metadata={
                "game": "csgo",
                "level": "standard",
                "started_at": datetime.utcnow().isoformat()
            }
        )

        # Регистрация graceful shutdown
        state_manager.register_shutdown_handlers(
            scan_id=scan_id,
            cleanup_callback=lambda: print("Cleanup resources...")
        )

        cursor = None
        processed = 0

        while True:
            # Получить batch предметов
            items, next_cursor = await fetch_items(cursor=cursor, limit=100)

            if not items:
                break

            # Обработать предметы
            for item in items:
                # ... обработка ...
                processed += 1

                # Автоматическое сохранение checkpoint
                if processed % state_manager.checkpoint_interval == 0:
                    await state_manager.save_checkpoint(
                        scan_id=scan_id,
                        cursor=next_cursor,
                        processed_items=processed,
                    )

            cursor = next_cursor

            if not cursor:
                break

        # Отметить как завершенное
        await state_manager.mark_checkpoint_completed(scan_id)
```

### Восстановление после сбоя

```python
async def resume_scan():
    """Продолжить прерванное сканирование."""
    async with get_session() as session:
        state_manager = StateManager(session)

        # Найти активные checkpoints
        active = await state_manager.get_active_checkpoints(
            user_id=123456789,
            operation_type="market_scan"
        )

        if not active:
            print("Нет незавершенных сканирований")
            return

        # Восстановить последний checkpoint
        checkpoint = active[0]
        print(f"Восстановление с позиции: {checkpoint.processed_items}")

        # Продолжить с cursor
        cursor = checkpoint.cursor
        processed = checkpoint.processed_items

        # Продолжить сканирование...
```

### Очистка старых checkpoints

```python
async def cleanup_old_data():
    """Очистить старые checkpoints."""
    async with get_session() as session:
        state_manager = StateManager(session)

        # Удалить checkpoints старше 7 дней
        deleted = await state_manager.cleanup_old_checkpoints(days=7)
        print(f"Удалено {deleted} старых checkpoints")
```

---

## Интеграция с Telegram Bot

### Пример: Уведомление о прогрессе

```python
from telegram import Update
from telegram.ext import ContextTypes

async def scan_with_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сканирование с отображением прогресса в Telegram."""
    user_id = update.effective_user.id
    scan_id = uuid4()

    async with get_session() as session:
        state_manager = StateManager(session)

        # Создать checkpoint
        await state_manager.create_checkpoint(
            scan_id=scan_id,
            user_id=user_id,
            operation_type="arbitrage_scan",
        )

        # Отправить начальное сообщение
        message = await update.message.reply_text(
            "🔄 Начинаю сканирование...\n"
            "Прогресс: 0/1000 (0%)"
        )

        cursor = None
        processed = 0
        total = 1000

        while processed < total:
            # Fetch batch
            items, cursor = await fetch_items(cursor=cursor, limit=100)

            # Process items
            for item in items:
                # ... обработка ...
                processed += 1

                # Обновить прогресс каждые 100 предметов
                if processed % 100 == 0:
                    await state_manager.save_checkpoint(
                        scan_id=scan_id,
                        cursor=cursor,
                        processed_items=processed,
                        total_items=total,
                    )

                    # Обновить сообщение в Telegram
                    percent = (processed / total) * 100
                    await message.edit_text(
                        f"🔄 Сканирование: {processed}/{total} ({percent:.0f}%)\n"
                        f"⏱️ Продолжаем..."
                    )

            if not cursor:
                break

        # Завершить
        await state_manager.mark_checkpoint_completed(scan_id)
        await message.edit_text(
            f"✅ Сканирование завершено!\n"
            f"📊 Обработано: {processed} предметов"
        )
```

---

## Local State Manager (для разработки)

Для разработки и тестирования доступна file-based версия:

```python
from src.utils.state_manager import LocalStateManager

# Инициализация
state_manager = LocalStateManager(state_dir="data/checkpoints")

# Сохранить checkpoint
await state_manager.save_checkpoint(
    scan_id=scan_id,
    cursor="next_page_token",
    processed_items=250,
)

# Загрузить checkpoint
checkpoint = await state_manager.load_checkpoint(scan_id)
if checkpoint:
    print(f"Восстановлено: {checkpoint.processed_items} предметов")
```

---

## База данных

### Схема таблицы `scan_checkpoints`

```sql
CREATE TABLE scan_checkpoints (
    id INTEGER PRIMARY KEY,
    scan_id UUID UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    cursor TEXT,
    processed_items INTEGER DEFAULT 0,
    total_items INTEGER,
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'in_progress',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_scan_checkpoints_scan_id ON scan_checkpoints(scan_id);
CREATE INDEX idx_scan_checkpoints_user_id ON scan_checkpoints(user_id);
```

---

## Лучшие практики

### 1. Checkpoint Interval

Выбирайте интервал в зависимости от объема:

- **Малые сканы** (<1000 предметов): каждые 50-100 предметов
- **Средние сканы** (1000-5000): каждые 100-200 предметов
- **Большие сканы** (>5000): каждые 200-500 предметов

### 2. Metadata

Сохраняйте полезный контекст в metadata:

```python
metadata = {
    "game": "csgo",
    "level": "pro",
    "filters": {"min_price": 100, "max_price": 1000},
    "started_at": datetime.utcnow().isoformat(),
    "initiated_by": "telegram_command",
}
```

### 3. Error Handling

Всегда отмечайте failed checkpoints с информацией об ошибке:

```python
try:
    # ... операция ...
    await state_manager.mark_checkpoint_completed(scan_id)
except Exception as e:
    await state_manager.mark_checkpoint_failed(
        scan_id=scan_id,
        error_message=str(e)
    )
    raise
```

### 4. Cleanup

Регулярно очищайте старые checkpoints (через cron или scheduled task):

```bash
# Пример cron task (каждый день в 3:00)
0 3 * * * python -m scripts.cleanup_checkpoints
```

---

## Troubleshooting

### Checkpoint не создается

**Проблема**: Checkpoint не сохраняется в БД.

**Решение**:

- Проверьте подключение к БД
- Убедитесь что таблица создана (alembic upgrade head)
- Проверьте права доступа

### Операция не восстанавливается

**Проблема**: После перезапуска операция начинается с нуля.

**Решение**:

- Проверьте что scan_id сохраняется корректно
- Убедитесь что cursor правильный
- Проверьте логи на наличие ошибок при загрузке checkpoint

### Слишком много checkpoints в БД

**Проблема**: БД переполнена старыми checkpoints.

**Решение**:

```python
# Очистить старые checkpoints
await state_manager.cleanup_old_checkpoints(days=7)
```

---

## Метрики успеха

### Ожидаемые показатели

- ✅ **Recovery Time**: <5 минут после сбоя
- ✅ **Data Loss**: 0% (максимум один batch = checkpoint_interval предметов)
- ✅ **Checkpoint Overhead**: <1% увеличение времени выполнения
- ✅ **Storage Growth**: <10MB/месяц для active user

---

**Обновлено**: 17 декабря 2025 г.
**Версия модуля**: 1.0
**Статус**: Production Ready
