# Batch Processing Guide

**Дата**: 17 декабря 2025 г.
**Версия**: 1.0

---

## Обзор

Модуль `batch_processor.py` предоставляет упрощенную систему пакетной обработки больших объемов данных без сложности распределенных очередей задач (Celery/RabbitMQ). Идеально подходит для single-user режима.

## Ключевые возможности

### 1. Simple Batch Processing

- ✅ Обработка по N предметов за раз
- ✅ Автоматическая memory cleanup между батчами
- ✅ Progress tracking через callbacks
- ✅ Error handling с graceful recovery

### 2. Concurrent Processing

- ✅ Ограниченное количество параллельных задач
- ✅ Semaphore-based concurrency control
- ✅ Automatic retry на ошибках
- ✅ Resource throttling

### 3. Progress Tracking

- ✅ Real-time progress updates
- ✅ Formatted progress strings
- ✅ Telegram integration ready

---

## SimpleBatchProcessor

### Базовое использование

```python
from src.utils.batch_processor import SimpleBatchProcessor

async def process_market_items():
    """Обработать большой список предметов."""
    # Получить список предметов
    items = await api.get_all_market_items(game="csgo")  # 5000+ items

    # Инициализировать processor
    processor = SimpleBatchProcessor(
        batch_size=100,              # 100 предметов за раз
        delay_between_batches=0.1    # 100ms задержка
    )

    # Функция обработки batch
    async def process_batch(batch):
        results = []
        for item in batch:
            # Анализ каждого предмета
            profit = calculate_arbitrage(item)
            if profit > 0:
                results.append({
                    "item": item["title"],
                    "profit": profit
                })
        return results

    # Обработать все предметы
    opportunities = await processor.process_in_batches(
        items=items,
        process_fn=process_batch
    )

    print(f"Найдено {len(opportunities)} возможностей")
```

### С progress tracking

```python
async def scan_with_progress(update: Update):
    """Сканирование с отображением прогресса."""
    items = await get_items()
    processor = SimpleBatchProcessor(batch_size=100)

    # Progress message
    msg = await update.message.reply_text("🔄 Начинаю сканирование...")

    # Progress callback
    async def update_progress(processed, total):
        percent = (processed / total) * 100
        await msg.edit_text(
            f"🔄 Сканирование: {processed}/{total} ({percent:.1f}%)\n"
            f"⏱️ Осталось: {total - processed} предметов"
        )

    # Обработать с progress
    results = await processor.process_in_batches(
        items=items,
        process_fn=analyze_items,
        progress_callback=update_progress
    )

    await msg.edit_text(f"✅ Готово! Найдено: {len(results)}")
```

### Error handling

```python
async def robust_processing():
    """Обработка с обработкой ошибок."""
    processor = SimpleBatchProcessor(batch_size=50)

    # Error callback
    async def handle_error(error, failed_batch):
        logger.error(
            f"Batch failed: {error}",
            batch_size=len(failed_batch)
        )
        # Можно сохранить failed batch для ручной обработки
        # await save_failed_batch(failed_batch)

    results = await processor.process_in_batches(
        items=items,
        process_fn=risky_operation,
        error_callback=handle_error  # Не падать при ошибках
    )
```

---

## Concurrent Processing

### Ограниченный параллелизм

```python
async def concurrent_api_calls():
    """Параллельные API вызовы с ограничением."""
    processor = SimpleBatchProcessor()
    items = [...список предметов...]

    async def fetch_item_details(item):
        """Получить детали одного предмета."""
        return await api.get_item_details(item["id"])

    # Обработать до 5 предметов параллельно
    details = await processor.process_with_concurrency(
        items=items,
        process_fn=fetch_item_details,
        max_concurrent=5  # Не перегружать API
    )

    return details
```

### Real-world пример: Bulk target creation

```python
async def create_targets_in_bulk(target_specs: list[dict]):
    """Создать множество таргетов эффективно."""
    processor = SimpleBatchProcessor(batch_size=10)  # DMarket лимит

    async def create_batch(batch):
        """Создать batch таргетов."""
        return await dmarket_api.create_targets(
            targets=[
                {
                    "Title": spec["title"],
                    "Price": {"Amount": spec["price"], "Currency": "USD"},
                    "Amount": 1
                }
                for spec in batch
            ]
        )

    results = await processor.process_in_batches(
        items=target_specs,
        process_fn=create_batch
    )

    return results
```

---

## ProgressTracker

### Standalone usage

```python
from src.utils.batch_processor import ProgressTracker

async def long_operation():
    """Длительная операция с progress tracking."""
    items = [...]  # 1000 предметов
    tracker = ProgressTracker(
        total=len(items),
        update_interval=50  # Обновлять каждые 50 предметов
    )

    for i, item in enumerate(items):
        # Обработка...
        process(item)

        # Обновить прогресс
        progress = tracker.update(i + 1)
        if progress:
            # progress вернется только каждые 50 предметов
            print(tracker.format_progress())
```

### Интеграция с Telegram

```python
async def scan_with_tracker(update: Update):
    """Сканирование с ProgressTracker."""
    items = await get_items()
    tracker = ProgressTracker(total=len(items), update_interval=100)

    msg = await update.message.reply_text("🔄 Запуск...")

    for i, item in enumerate(items):
        # Обработка
        result = await analyze_item(item)

        # Обновить прогресс
        progress = tracker.update(i + 1)
        if progress:
            # Обновить Telegram сообщение
            await msg.edit_text(tracker.format_progress(i + 1))

    await msg.edit_text("✅ Завершено!")
```

---

## Chunked API Calls

Для работы с rate-limited API:

```python
from src.utils.batch_processor import chunked_api_calls

async def fetch_aggregated_prices():
    """Получить цены для многих предметов."""
    items = ["AK-47 | Redline", "AWP | Asiimov", ...]  # 500 предметов

    async def get_prices_batch(titles_batch):
        """API вызов для batch."""
        return await dmarket_api.get_aggregated_prices(
            game="csgo",
            titles=titles_batch
        )

    # Разбить на chunks по 100 (DMarket лимит)
    all_prices = await chunked_api_calls(
        items=items,
        api_call_fn=get_prices_batch,
        chunk_size=100,
        delay=0.5  # 500ms между вызовами
    )

    return all_prices
```

---

## Интеграция со State Manager

Комбинация batch processing + state persistence:

```python
from src.utils.batch_processor import SimpleBatchProcessor
from src.utils.state_manager import StateManager
from uuid import uuid4

async def resilient_scan():
    """Сканирование с checkpoints и batching."""
    scan_id = uuid4()
    processor = SimpleBatchProcessor(batch_size=100)

    async with get_session() as session:
        state = StateManager(session, checkpoint_interval=100)

        # Создать checkpoint
        await state.create_checkpoint(
            scan_id=scan_id,
            user_id=user_id,
            operation_type="market_scan"
        )

        items = await get_items()
        processed_count = 0

        # Progress callback с checkpoint
        async def save_progress(processed, total):
            nonlocal processed_count
            processed_count = processed

            # Сохранить checkpoint
            await state.save_checkpoint(
                scan_id=scan_id,
                processed_items=processed,
                total_items=total
            )

        # Обработать с автоматическими checkpoints
        results = await processor.process_in_batches(
            items=items,
            process_fn=analyze_batch,
            progress_callback=save_progress
        )

        # Отметить завершение
        await state.mark_checkpoint_completed(scan_id)

        return results
```

---

## Оптимизация производительности

### Memory Management

```python
import gc

async def memory_efficient_processing():
    """Обработка с принудительной очисткой памяти."""
    processor = SimpleBatchProcessor(batch_size=100)

    async def process_batch(batch):
        results = []
        for item in batch:
            # Обработка
            results.append(heavy_computation(item))

        # Принудительная сборка мусора после batch
        gc.collect()
        return results

    return await processor.process_in_batches(
        items=large_dataset,
        process_fn=process_batch
    )
```

### Resource Throttling

```python
import psutil

async def adaptive_processing():
    """Адаптивная обработка с мониторингом ресурсов."""
    processor = SimpleBatchProcessor(batch_size=100)

    async def smart_batch_processor(batch):
        # Проверить использование CPU
        cpu_percent = psutil.cpu_percent()

        if cpu_percent > 80:
            # Снизить batch size
            mini_batches = [batch[i:i+20] for i in range(0, len(batch), 20)]
            results = []
            for mini in mini_batches:
                results.extend(await process_mini_batch(mini))
                await asyncio.sleep(0.5)  # Дополнительная задержка
            return results
        else:
            # Нормальная обработка
            return await process_normal_batch(batch)

    return await processor.process_in_batches(
        items=items,
        process_fn=smart_batch_processor
    )
```

---

## Лучшие практики

### 1. Выбор batch_size

| Сценарий                 | Batch Size | Обоснование             |
| ------------------------ | ---------- | ----------------------- |
| API calls (rate limited) | 10-50      | Избежать rate limit     |
| Memory-intensive         | 20-50      | Предотвратить OOM       |
| Fast operations          | 100-200    | Минимизировать overhead |
| Large datasets           | 50-100     | Баланс скорости/памяти  |

### 2. Delay Configuration

```python
# Для API с rate limiting
processor = SimpleBatchProcessor(
    batch_size=50,
    delay_between_batches=0.5  # 500ms = безопасно
)

# Для локальных операций
processor = SimpleBatchProcessor(
    batch_size=200,
    delay_between_batches=0.01  # 10ms = минимально
)
```

### 3. Error Strategies

**Fail Fast** (по умолчанию):

```python
# При ошибке - остановить всё
results = await processor.process_in_batches(
    items=items,
    process_fn=strict_operation
    # error_callback НЕ указан
)
```

**Continue on Error**:

```python
# Продолжить при ошибках
async def log_and_continue(error, batch):
    logger.error(f"Batch failed: {error}")
    # Не re-raise

results = await processor.process_in_batches(
    items=items,
    process_fn=lenient_operation,
    error_callback=log_and_continue
)
```

---

## Метрики производительности

### Ожидаемые показатели

- ✅ **Throughput**: 100-500 items/second (зависит от операции)
- ✅ **Memory Overhead**: <50MB дополнительно
- ✅ **CPU Usage**: <60% на batch processing
- ✅ **Latency**: <10ms overhead на batch

### Мониторинг

```python
import time

async def monitored_processing():
    """Обработка с мониторингом."""
    start_time = time.time()
    processor = SimpleBatchProcessor(batch_size=100)

    results = await processor.process_in_batches(
        items=items,
        process_fn=operation
    )

    duration = time.time() - start_time
    throughput = len(items) / duration

    logger.info(
        "Processing completed",
        total_items=len(items),
        duration_seconds=duration,
        throughput_items_per_sec=throughput
    )

    return results
```

---

## Troubleshooting

### Проблема: Медленная обработка

**Решение**: Увеличить batch_size или использовать concurrent processing

### Проблема: Out of Memory

**Решение**: Уменьшить batch_size, добавить gc.collect() в process_fn

### Проблема: Rate Limit Errors

**Решение**: Увеличить delay_between_batches, уменьшить batch_size

---

**Обновлено**: 17 декабря 2025 г.
**Версия модуля**: 1.0
**Статус**: Production Ready
