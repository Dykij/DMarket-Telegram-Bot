# План обновления - Персональное использование (Single User)

**Дата создания**: 20 ноября 2025 г.
**Режим**: 🔒 **Персональное использование (1 пользователь)**
**Фокус**: Стабильность, надежность, простота, compliance с DMarket ToS
**Версия**: 1.0

---

## 🎯 Цели для персонального использования

### Приоритеты

1. **Стабильность и надежность** - бот должен работать 24/7 без сбоев
2. **Простота развертывания** - минимум инфраструктуры
3. **Compliance с ToS** - только официальные API, без reverse engineering
4. **Эффективный арбитраж** - быстрое нахождение возможностей
5. **Низкие требования** - работа на обычном VPS/домашнем ПК

### Что НЕ нужно для 1 пользователя

- ❌ Webhooks (polling достаточно)
- ❌ Load balancing (нет нагрузки)
- ❌ Complex message queues (нет массовых рассылок)
- ❌ TreeFilters/web scraping (нарушает ToS)

---

## ✅ Завершенные этапы (Текущий прогресс)

### Этап 1-4: Базовая инфраструктура ✅ ЗАВЕРШЕНО

- ✅ **dmarket_api.py** - DMarket API v1.1.0 интеграция
- ✅ **market_models.py** - Pydantic 2.5+ модели
- ✅ **targets.py** - Умные таргеты
- ✅ **arbitrage_scanner.py** - Многоуровневое сканирование
- ✅ **market_analysis.py** - Анализ глубины рынка
- ✅ **Handlers** - Target, Scanner, Formatters
- ✅ **Tests** - 57 тестов, покрытие критической функциональности

---

## 🚀 Приоритетные улучшения для персонального использования

### Фаза 1: Стабильность и надежность (P1) - 7-10 дней

#### 1. Auto-recovery и State Persistence ⭐ КРИТИЧНО

**Цель**: Бот должен восстанавливаться после сбоев без потери данных

**Реализация**:

- Checkpoint система для длительных сканов
- Сохранение прогресса каждые 100 предметов
- Восстановление из последнего checkpoint при restart
- Graceful shutdown handlers (SIGTERM/SIGINT)

**Модуль**: `src/utils/state_manager.py` (НОВЫЙ)

```python
class StateManager:
    async def save_checkpoint(scan_id, cursor, processed_items)
    async def load_checkpoint(scan_id) -> CheckpointData | None
    async def cleanup_old_checkpoints(days=7)
```

**База данных**: PostgreSQL таблица `scan_checkpoints`

- scan_id (UUID)
- cursor (str)
- processed_items (int)
- timestamp (datetime)
- metadata (JSONB)

**Приоритет**: P1
**Срок**: 3 дня
**Зависимости**: Batch processor (#3)

---

#### 2. Advanced Error Tracking с Sentry ⭐ КРИТИЧНО

**Цель**: Мониторинг ошибок в реальном времени

**Реализация**:

- Sentry SDK интеграция
- Автоматический capture всех exceptions
- User context (user_id, command, parameters)
- Performance monitoring (медленные API вызовы)
- Release tracking

**Alerting правила**:

- 🔴 **Critical**: API auth failures, database connection lost → instant alert
- 🟠 **High**: Rate limit exceeded, OOM errors → 5 min delay
- 🟡 **Medium**: Validation errors, single scan failures → daily digest
- 🔵 **Performance**: API calls > 5 seconds → weekly report

**Модуль**: Интеграция в `src/utils/logging_utils.py`

```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=0.1,  # 10% для персонального использования
    send_default_pii=False,
    before_send=filter_sensitive_data
)
```

**Приоритет**: P1
**Срок**: 2 дня
**Стоимость**: Sentry Free tier (5,000 errors/month) - достаточно

---

#### 3. Simplified Batch Processing для больших сканов

**Цель**: Эффективная обработка тысяч предметов без перегрузки памяти

**Реализация для single user**:

- Chunked processing по 50-100 предметов
- Простая asyncio.Queue (не нужна Celery/RabbitMQ)
- Memory cleanup между батчами
- Progress tracking через Telegram

**Модуль**: `src/utils/batch_processor.py` (УПРОЩЕННЫЙ)

```python
class SimpleBatchProcessor:
    async def process_in_batches(
        items: list,
        batch_size: int = 100,
        process_fn: Callable,
        progress_callback: Callable | None = None
    ):
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            await process_fn(batch)
            if progress_callback:
                await progress_callback(i + len(batch), len(items))
            await asyncio.sleep(0.1)  # Prevent overload
```

**Telegram progress**:

```
🔄 Сканирование: 250/1000 предметов (25%)
⏱️ Осталось: ~3 минуты
```

**Приоритет**: P1
**Срок**: 2 дня
**Зависимости**: Нет

---

#### 4. Schema Validation для API responses

**Цель**: Раннее обнаружение изменений API, защита от runtime errors

**Реализация**:

- Pydantic models для ВСЕХ API responses
- Автоматическая валидация при deserialization
- Clear error messages при schema mismatch
- Type safety для downstream code

**Модуль**: Расширение `src/dmarket/models/market_models.py`

**Пример**:

```python
from pydantic import BaseModel, Field, validator

class AggregatedPriceResponse(BaseModel):
    title: str
    order_best_price: str = Field(alias="orderBestPrice")
    order_count: int = Field(alias="orderCount")
    offer_best_price: str = Field(alias="offerBestPrice")
    offer_count: int = Field(alias="offerCount")

    @validator('order_best_price', 'offer_best_price')
    def validate_price(cls, v):
        if not v.isdigit():
            raise ValueError(f"Price must be numeric string, got {v}")
        return v
```

**Benefits**:

- ✅ Автоматическое обнаружение breaking changes в API
- ✅ IDE autocomplete и type hints
- ✅ Self-documenting code
- ✅ Prevention runtime errors

**Приоритет**: P1
**Срок**: 3 дня
**Зависимости**: Pydantic 2.5+ (уже установлен)

---

### Фаза 2: Оптимизация и качество жизни (P2) - 5-7 дней

#### 5. Расширенная детекция ликвидности

**Реализация**:

- Интеграция `/last-sales` endpoint для анализа объема
- Минимальный порог: ≥10 транзакций за 7 дней
- Фильтрация по txOperationType (Target/Offer)
- Метрика "trading velocity"

**Модуль**: `src/dmarket/liquidity_analyzer.py` (НОВЫЙ)

```python
class LiquidityAnalyzer:
    async def analyze_sales_volume(title: str, days: int = 7) -> int
    async def calculate_trading_velocity(title: str) -> float
    async def filter_by_liquidity(items: list, min_volume: int = 10) -> list
```

**Приоритет**: P2
**Срок**: 2 дня

---

#### 6. Улучшенная cursor-based пагинация

**Реализация**:

- max_pages параметр для ограничения сканов
- Progress callbacks для отслеживания
- Retry логика для прерванных курсоров
- Caching курсоров для повторного использования

**Модуль**: Обновление `src/dmarket/dmarket_api.py`

**Приоритет**: P2
**Срок**: 1 день

---

#### 7. Resource Monitor с auto-throttling

**Цель**: Защита от перегрузки системы

**Реализация для single user**:

- Мониторинг CPU/Memory/Disk с psutil
- Проверка каждые 30 секунд (не каждые 10 для экономии)
- Auto-throttling при CPU > 80%, Memory > 85%
- Уменьшение параллельных запросов при высокой нагрузке

**Модуль**: `src/utils/resource_monitor.py` (УПРОЩЕННЫЙ)

```python
class ResourceMonitor:
    async def monitor_continuously(check_interval: int = 30):
        while True:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent

            if cpu > 80 or mem > 85:
                await throttle_operations()

            await asyncio.sleep(check_interval)
```

**Приоритет**: P2
**Срок**: 2 дня

---

#### 8. WebSocket для real-time price updates

**Реализация**:

- Подписка на обновления конкретных предметов из watchlist
- Real-time мониторинг цен для арбитража
- Instant уведомления об изменениях > 5%
- Снижение нагрузки на REST API

**Модуль**: Расширение `src/utils/websocket_client.py`

**Приоритет**: P2
**Срок**: 3 дня

---

### Фаза 3: Улучшения UX (P3) - 3-4 дня

---

#### 9. Оптимизированный Polling для Telegram

---

#### 10. Оптимизированный Polling для Telegram

**Реализация для single user**:

- Увеличенный timeout (30-60 сек) для снижения нагрузки
- `allowed_updates` только для нужных типов
- Graceful handling reconnections
- Minimal memory footprint

**Модуль**: Обновление `src/telegram_bot/enhanced_bot.py`

**Приоритет**: P3
**Срок**: 0.5 дня

---

#### 11. Personal Watchlist с Checklists

**Реализация**:

- Простой checklist для личного watchlist
- Отметка купленных предметов
- Синхронизация с БД
- Без групповых функций

**Модуль**: `src/telegram_bot/handlers/watchlist_handler.py` (НОВЫЙ)

**Приоритет**: P3
**Срок**: 2 дня

---

#### 12. Динамические таргеты с атрибутами

**Реализация**:

- Использование `floatPartValue`, `phase`, `paintSeed`
- Анализ конкуренции через `/targets-by-title`
- Установка цены на 10-20% ниже `offerBestPrice`

**Модуль**: Расширение `src/dmarket/targets.py`

**Приоритет**: P2
**Срок**: 3 дня

---

## 📊 Итоговая таблица приоритетов (Single User Mode)

| #   | Идея                              | Приоритет | Срок    | Модуль                | Критичность | Рекомендация    |
| --- | --------------------------------- | --------- | ------- | --------------------- | ----------- | --------------- |
| 1   | Auto-recovery & State Persistence | P1        | 3 дня   | state_manager.py      | ⭐⭐⭐         | ✅ Обязательно   |
| 2   | Sentry Error Tracking             | P1        | 2 дня   | logging_utils.py      | ⭐⭐⭐         | ✅ Обязательно   |
| 3   | Simplified Batch Processing       | P1        | 2 дня   | batch_processor.py    | ⭐⭐          | ✅ Обязательно   |
| 4   | API Schema Validation             | P1        | 3 дня   | market_models.py      | ⭐⭐          | ✅ Обязательно   |
| 5   | Расширенная ликвидность           | P2        | 2 дня   | liquidity_analyzer.py | ⭐           | ✅ Рекомендуется |
| 6   | Cursor пагинация                  | P2        | 1 день  | dmarket_api.py        | ⭐           | ✅ Рекомендуется |
| 7   | Resource Monitor                  | P2        | 2 дня   | resource_monitor.py   | ⭐           | ✅ Рекомендуется |
| 8   | WebSocket real-time               | P2        | 3 дня   | websocket_client.py   | ⭐           | ✅ Полезно       |
| 9   | Optimized Polling                 | P3        | 0.5 дня | enhanced_bot.py       | -           | ✅ Полезно       |
| 10  | Personal Watchlist                | P3        | 2 дня   | watchlist_handler.py  | -           | ✅ Полезно       |
| 11  | Динамические таргеты              | P2        | 3 дня   | targets.py            | ⭐           | ✅ Рекомендуется |
| 12  | Управление инвентарем             | P2        | 3 дня   | inventory_manager.py  | ⭐           | ✅ Рекомендуется |
| 13  | Inline режим + клавиатуры         | P3        | 3-4 дня | inline_handler.py     | -           | ✅ Полезно       |

**Общий срок**: ~25 дней последовательно, **15-18 дней параллельно**

---

## 🎯 Рекомендуемая последовательность внедрения

### Week 1: Критичные улучшения (P1)

**Дни 1-2**: Sentry Error Tracking (#2)
**Дни 3-4**: Simplified Batch Processing (#3)
**Дни 5-7**: Auto-recovery & State Persistence (#1)
**Дни 8-10**: API Schema Validation (#4)

### Week 2: Оптимизация (P2)

**Дни 11-13**: Динамические таргеты (#11)
**Дни 14-15**: Расширенная ликвидность (#5)
**День 16**: Cursor пагинация (#6)
**Дни 17-18**: Resource Monitor (#7)
**Дни 19-21**: Управление инвентарем (#12)

### Week 3: Дополнительно (P2-P3)

**Дни 22-24**: WebSocket real-time (#8)
**Дни 25-26**: Personal Watchlist (#10)
**День 27**: Optimized Polling (#9)
**Дни 28-30**: Inline режим + клавиатуры (#13)

---

## 💻 Требования для развертывания (Single User)

### Минимальные требования

**VPS/Сервер**:

- CPU: 1 core (2 cores рекомендуется)
- RAM: 1 GB (2 GB рекомендуется)
- Disk: 5 GB SSD
- OS: Ubuntu 22.04 / Windows Server / любой с Docker

**Сеть**:

- Stable internet (не нужен публичный IP для polling режима)
- 100 MB/month минимум (для API calls и Telegram)

**Программное обеспечение**:

- Python 3.10+
- PostgreSQL 14+ (или SQLite для начала)
- Docker + Docker Compose (опционально, но рекомендуется)
- Git

### Рекомендуемое развертывание

**Docker Compose**:

```yaml
version: '3.8'

services:
  bot:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: dmarket_bot
      POSTGRES_USER: dmarketbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 🛡️ ToS Compliance Checklist

### ✅ Разрешено (используем)

- ✅ Официальные документированные DMarket API endpoints
- ✅ HMAC-SHA256 authentication по документации
- ✅ Rate limiting в пределах лимитов (30 req/min)
- ✅ Cursor-based пагинация
- ✅ Официальные фильтры (priceFrom/To, exterior[], etc.)

### ❌ Запрещено (НЕ используем)

- ❌ Web scraping через Selenium/Playwright
- ❌ Reverse-engineering недокументированных API
- ❌ DevTools network inspection для получения секретных параметров
- ❌ TreeFilters через reverse engineering
- ❌ Rate limit обход через прокси
- ❌ Fake user agents или bot detection bypass

---

---

## 📈 Метрики успеха

### Стабильность

- ✅ Uptime > 99.5% (max 3.6 часа простоя/месяц)
- ✅ Auto-recovery < 5 минут после crash
- ✅ Zero data loss при restart

### Производительность

- ✅ Scan 1000 предметов < 5 минут
- ✅ API response time < 2 секунды (95th percentile)
- ✅ Memory usage < 512 MB (steady state)

### Качество

- ✅ Sentry errors < 10/день
- ✅ False positive арбитража < 5%
- ✅ Test coverage > 80% для критических модулей

---

## 🔧 Maintenance Plan

### Ежедневно

- Проверка Sentry для критичных ошибок
- Мониторинг uptime (через health check)

### Еженедельно

- Обзор Sentry digest
- Проверка логов на аномалии
- Обновление зависимостей (если нужно)

### Ежемесячно

- Backup базы данных
- Очистка старых checkpoints (> 30 дней)
- Анализ производительности

---

## 📚 Дополнительно

### Backup стратегия

**База данных** (автоматически):

```bash
#!/bin/bash
# cron: 0 3 * * * (каждый день в 3:00)

DATE=$(date +%Y%m%d)
docker exec postgres pg_dump -U dmarketbot dmarket_bot > backup_${DATE}.sql
find . -name "backup_*.sql" -mtime +30 -delete
```

**Конфигурация**:

- .env файл → зашифровать и хранить отдельно
- docker-compose.yml → git repository

### Security best practices

- ✅ API ключи в .env (NEVER в коде)
- ✅ PostgreSQL password сильный (20+ символов)
- ✅ Sentry DSN не публичный
- ✅ Регулярные обновления зависимостей
- ✅ 2FA на всех аккаунтах (DMarket, Telegram, Sentry)

---

**Обновлено**: 20 ноября 2025 г.
**Статус**: Адаптировано под персональное использование (single user)
**Версия**: 2.0 - Добавлены все полезные идеи из UPDATE_PLAN.md (без нарушения ToS)
**Compliance**: ✅ Полное соответствие DMarket ToS
