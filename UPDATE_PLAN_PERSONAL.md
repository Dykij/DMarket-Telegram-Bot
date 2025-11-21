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

### Фаза 1 (P1): ✅ ЗАВЕРШЕНА - 4/4 (20 ноября 2025)

#### ✅ 1. Auto-recovery & State Persistence - ЗАВЕРШЕНО

- ✅ StateManager с checkpoint system
- ✅ Graceful shutdown handlers (SIGTERM/SIGINT)
- ✅ Database model ScanCheckpoint
- ✅ LocalStateManager для разработки (file-based)
- ✅ Cleanup old checkpoints
- ✅ Recovery mechanisms
- ✅ Полная документация в docs/state_management_guide.md

**Статус**: Требует миграции БД ⚠️
**Файлы**:

- `src/utils/state_manager.py` (новый, 450+ строк)
- `docs/state_management_guide.md` (новый, полное руководство)
**TODO**: Создать Alembic миграцию для scan_checkpoints

#### ✅ 2. Sentry Error Tracking - ЗАВЕРШЕНО

- ✅ Интеграция Sentry SDK в logging_utils.py
- ✅ Автоматический capture всех exceptions
- ✅ Фильтрация чувствительных данных
- ✅ LoggingIntegration, AsyncioIntegration, HttpxIntegration
- ✅ Обновлен .env.example с SENTRY_DSN и BOT_VERSION
- ✅ Документация: error tracking встроен в setup_logging()

**Статус**: Production Ready ✅
**Файлы**:

- `src/utils/logging_utils.py` (обновлен)
- `.env.example` (обновлен)

#### ✅ 3. Simplified Batch Processing - ЗАВЕРШЕНО

- ✅ SimpleBatchProcessor для memory-efficient обработки
- ✅ Concurrent processing с semaphore control
- ✅ ProgressTracker для real-time progress
- ✅ Chunked API calls для rate limiting
- ✅ Error handling с callbacks
- ✅ Полная документация в docs/batch_processing_guide.md

**Статус**: Production Ready ✅
**Файлы**:

- `src/utils/batch_processor.py` (новый, 280+ строк)
- `docs/batch_processing_guide.md` (новый, полное руководство)

#### ✅ 4. API Schema Validation - ЗАВЕРШЕНО

- ✅ Расширенные Pydantic models для ВСЕХ API responses
- ✅ MarketItemsResponse, AggregatedPricesResponse
- ✅ UserTargetsResponse, UserOffersResponse, UserInventoryResponse
- ✅ BuyItemResponse, CreateOfferResponse
- ✅ LastSalesResponse, ClosedTargetsResponse
- ✅ OffersByTitleResponse, InventoryItem
- ✅ Properties для конверсий (центы → доллары)
- ✅ Validation на все критические поля
- ✅ Clear error messages при schema mismatch
- ✅ Полная документация в docs/schema_validation_guide.md
- ✅ Покрытие: 11/11 критических эндпоинтов (100%)

**Статус**: Production Ready ✅
**Файлы**:

- `src/dmarket/models/market_models.py` (расширен, 600+ строк)
- `docs/schema_validation_guide.md` (новый, полное руководство)
**TODO**: Unit тесты для всех моделей

---

## 🎉 Фаза 1 - ПОЛНОСТЬЮ ЗАВЕРШЕНА! (20 ноября 2025)

**Достижения**:

- ✅ 4/4 критических задач реализованы
- ✅ Auto-recovery для надежности 24/7
- ✅ Sentry для real-time error tracking
- ✅ Batch processing для эффективности
- ✅ Schema validation для type safety
- ✅ 1,800+ строк нового кода
- ✅ 4 полноценных руководства

**Следующая фаза**: P2 - Оптимизация и качество жизни

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

#### ✅ 5. Circuit Breaker Pattern для API вызовов - ЗАВЕРШЕНО

**Цель**: Защита от каскадных сбоев при отказе внешних сервисов

**Реализация**:

- ✅ Интеграция кастомного `CircuitBreaker` (без внешних зависимостей)
- ✅ Circuit breaker для DMarket API
- ✅ Три состояния: Closed (норма), Open (блокировка), Half-Open (проверка)
- ✅ Настройка: 5 failures за 60 секунд → Open (блокировка на 60 сек)
- ✅ Fallback strategies: корректная обработка ошибок
- ✅ Monitoring integration (логирование изменений состояния)

**Модуль**: `src/utils/api_circuit_breaker.py` (НОВЫЙ) и интеграция в `src/dmarket/dmarket_api.py`

**Benefits**:

- ✅ Предотвращение перегрузки при сбоях API
- ✅ Быстрый fail-fast вместо таймаутов
- ✅ Автоматическое восстановление после downtime
- ✅ Экономия ресурсов (threads, connections)

**Приоритет**: P1 (повышен с P2)
**Срок**: 2 дня
**Статус**: Production Ready ✅

---

#### ✅ 6. Database Connection Pooling & Optimization - ЗАВЕРШЕНО

**Цель**: Эффективное использование БД, предотвращение connection exhaustion

**Реализация**:

- ✅ SQLAlchemy connection pool configuration (QueuePool)
- ✅ Индексация критических полей (telegram_id, item_id, timestamps)
- ✅ Connection health checks (`pool_pre_ping=True`)
- ✅ Pool size tuning для single-user режима (size=5, overflow=10)

**Модуль**: Обновлен `src/utils/database.py`

**Приоритет**: P1 (повышен с P2)
**Срок**: 2 дня
**Статус**: Production Ready ✅

---

#### 7. Расширенная детекция ликвидности

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

#### 8. Enhanced Monitoring с Grafana Dashboards ⭐ ВАЖНО

**Цель**: Визуализация метрик и проактивный мониторинг

**Реализация**:

- Grafana для визуализации Prometheus метрик
- Custom dashboards для ключевых KPI:
  - API response times (p50, p95, p99)
  - Error rates по типам
  - Arbitrage opportunities found/hour
  - Target execution success rate
  - Memory/CPU usage trends
- Alerting rules через Grafana Alerts:
  - 🔴 Critical: API auth failure → Telegram alert
  - 🟠 High: Error rate > 10/min → Email
  - 🟡 Medium: Slow queries > 5s → Daily digest
- Integration с Telegram для alerts

**Модуль**: Docker Compose добавление Grafana

```yaml
# docker-compose.yml
grafana:
  image: grafana/grafana:latest
  restart: unless-stopped
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
  volumes:
    - grafana_data:/var/lib/grafana
    - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
```

**Pre-configured dashboards**:

- Bot Health Overview
- API Performance Metrics
- Trading Activity Dashboard
- Error Tracking & Logs

**Приоритет**: P2
**Срок**: 2 дня
**Стоимость**: Free (self-hosted)

---

#### 9. Security Hardening & Automated Audits

**Цель**: Регулярная проверка безопасности кода и зависимостей

**Реализация**:

- Bandit для статического анализа безопасности
- Trivy для сканирования Docker образов
- Safety для проверки known vulnerabilities в зависимостях
- pre-commit hooks для автоматических проверок
- GitHub Dependabot alerts (уже активирован)

**Модуль**: Интеграция в CI/CD pipeline

```yaml
# .github/workflows/security.yml
name: Security Audit

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json

      - name: Run Safety
        run: |
          pip install safety
          safety check --json

      - name: Scan Docker Image
        run: |
          docker build -t dmarket-bot:scan .
          trivy image dmarket-bot:scan
```

**Pre-commit configuration**:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
```

**Приоритет**: P2
**Срок**: 1 день
**Зависимости**: `pip install bandit safety`

---

#### 10. Load & Stress Testing Suite

**Цель**: Проверка стабильности под нагрузкой, поиск bottlenecks

**Реализация**:

- Locust для load testing REST API endpoints
- Chaos testing для симуляции сбоев (опционально)
- Performance benchmarks для critical paths
- Memory leak detection с tracemalloc
- CI integration для regression testing

**Модуль**: `tests/performance/` (НОВЫЙ)

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class BotLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def scan_arbitrage(self):
        self.client.get("/api/arbitrage/scan?game=csgo&level=standard")

    @task(1)
    def get_targets(self):
        self.client.get("/api/targets?status=active")
```

**Load test scenarios**:

- Arbitrage scanning: 100 concurrent scans
- Target creation: burst of 50 targets/second
- Database queries: 1000 reads/second
- WebSocket connections: 10 simultaneous streams

**Acceptance criteria**:

- ✅ API response time < 2s under 100 RPS
- ✅ Memory usage stable < 1GB during 1-hour test
- ✅ No connection pool exhaustion
- ✅ Error rate < 1% under load

**Приоритет**: P3
**Срок**: 2 дня
**Зависимости**: `pip install locust pytest-benchmark`

---

#### 11. WebSocket для real-time price updates

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

#### 12. Оптимизированный Polling для Telegram

**Реализация для single user**:

- Увеличенный timeout (30-60 сек) для снижения нагрузки
- `allowed_updates` только для нужных типов
- Graceful handling reconnections
- Minimal memory footprint

**Модуль**: Обновление `src/telegram_bot/enhanced_bot.py`

**Приоритет**: P3
**Срок**: 0.5 дня

---

#### 13. Personal Watchlist с Checklists

**Реализация**:

- Простой checklist для личного watchlist
- Отметка купленных предметов
- Синхронизация с БД
- Без групповых функций

**Модуль**: `src/telegram_bot/handlers/watchlist_handler.py` (НОВЫЙ)

**Приоритет**: P3
**Срок**: 2 дня

---

#### 14. Динамические таргеты с атрибутами

**Реализация**:

- Использование `floatPartValue`, `phase`, `paintSeed`
- Анализ конкуренции через `/targets-by-title`
- Установка цены на 10-20% ниже `offerBestPrice`

**Модуль**: Расширение `src/dmarket/targets.py`

**Приоритет**: P2
**Срок**: 3 дня

---

## 📊 Итоговая таблица приоритетов (Single User Mode) - ОБНОВЛЕНО

| #   | Идея                                    | Приоритет | Срок       | Модуль                     | Критичность | Рекомендация        |
| --- | --------------------------------------- | --------- | ---------- | -------------------------- | ----------- | ------------------- |
| 1   | ✅ **Auto-recovery & State Persistence** | P1        | 3 дня      | state_manager.py           | ⭐⭐⭐         | **✅ ЗАВЕРШЕНО**     |
| 2   | ✅ **Sentry Error Tracking**             | P1        | 2 дня      | logging_utils.py           | ⭐⭐⭐         | **✅ ЗАВЕРШЕНО**     |
| 3   | ✅ **Simplified Batch Processing**       | P1        | 2 дня      | batch_processor.py         | ⭐⭐          | **✅ ЗАВЕРШЕНО**     |
| 4   | ✅ **API Schema Validation**             | P1        | 3 дня      | market_models.py           | ⭐⭐          | **✅ ЗАВЕРШЕНО**     |
| 5   | ✅ **Circuit Breaker Pattern**           | **P1**    | **2 дня**  | **api_circuit_breaker.py** | **⭐⭐⭐**     | **✅ ЗАВЕРШЕНО**     |
| 6   | ✅ **Database Connection Pooling**       | **P1**    | **2 дня**  | **database.py**            | **⭐⭐**      | **✅ ЗАВЕРШЕНО**     |
| 7   | Расширенная ликвидность                 | P2        | 2 дня      | liquidity_analyzer.py      | ⭐           | ✅ Рекомендуется     |
| 8   | **Enhanced Monitoring (Grafana)**       | **P2**    | **2 дня**  | **docker-compose.yml**     | **⭐⭐**      | **✅ Рекомендуется** |
| 9   | **Security Hardening (Bandit)**         | **P2**    | **1 день** | **CI/CD**                  | **⭐**       | **✅ Рекомендуется** |
| 10  | **Load & Stress Testing**               | **P3**    | **2 дня**  | **tests/performance/**     | **⭐**       | **✅ Полезно**       |
| 11  | WebSocket real-time                     | P2        | 3 дня      | websocket_client.py        | ⭐           | ✅ Полезно           |
| 12  | Optimized Polling                       | P3        | 0.5 дня    | enhanced_bot.py            | -           | ✅ Полезно           |
| 13  | Personal Watchlist                      | P3        | 2 дня      | watchlist_handler.py       | -           | ✅ Полезно           |
| 14  | Динамические таргеты                    | P2        | 3 дня      | targets.py                 | ⭐           | ✅ Рекомендуется     |
| 15  | Cursor пагинация                        | P2        | 1 день     | dmarket_api.py             | ⭐           | ✅ Рекомендуется     |
| 16  | Resource Monitor                        | P2        | 2 дня      | resource_monitor.py        | ⭐           | ✅ Рекомендуется     |
| 17  | Управление инвентарем                   | P2        | 3 дня      | inventory_manager.py       | ⭐           | ✅ Рекомендуется     |
| 18  | Inline режим + клавиатуры               | P3        | 3-4 дня    | inline_handler.py          | -           | ✅ Полезно           |

**Общий срок**: ~35 дней последовательно, **20-25 дней параллельно**

**Новые добавления (на основе анализа)**:

- ✅ **#5**: Circuit Breaker Pattern - критично для надежности API
- ✅ **#6**: Database Connection Pooling - важно для производительности
- ✅ **#8**: Enhanced Monitoring (Grafana) - визуализация метрик
- ✅ **#9**: Security Hardening - автоматические security audits
- ✅ **#10**: Load Testing - проверка стабильности под нагрузкой

---

## 🎯 Рекомендуемая последовательность внедрения - ОБНОВЛЕНО

### Week 1: Критичные улучшения (P1)

**Дни 1-2**: Sentry Error Tracking (#2)
**Дни 3-4**: Circuit Breaker Pattern (#5) ⭐ НОВОЕ
**Дни 5-6**: Database Connection Pooling (#6) ⭐ НОВОЕ
**Дни 7-8**: Simplified Batch Processing (#3)
**Дни 9-11**: Auto-recovery & State Persistence (#1)
**Дни 12-14**: API Schema Validation (#4)

### Week 2: Оптимизация (P2)

**День 15**: Security Hardening (#9) ⭐ НОВОЕ
**Дни 16-17**: Enhanced Monitoring - Grafana (#8) ⭐ НОВОЕ
**Дни 18-20**: Динамические таргеты (#14)
**Дни 21-22**: Расширенная ликвидность (#7)
**День 23**: Cursor пагинация (#15)
**Дни 24-25**: Resource Monitor (#16)

### Week 3: Дополнительные улучшения (P2-P3)

**Дни 26-28**: Управление инвентарем (#17)
**Дни 29-30**: Load & Stress Testing (#10) ⭐ НОВОЕ
**Дни 31-33**: WebSocket real-time (#11)
**Дни 34-35**: Personal Watchlist (#13)

### Week 4: Финальные штрихи (P3)

**День 36**: Optimized Polling (#12)
**Дни 37-40**: Inline режим + клавиатуры (#18)

**Общая продолжительность**: 40 дней (6 недель) при последовательной работе
**Ускоренный вариант**: 25-30 дней при параллельной разработке

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
**Версия**: 3.0 - Добавлены улучшения из external analysis (Circuit Breaker, DB Pooling, Monitoring, Security)
**Compliance**: ✅ Полное соответствие DMarket ToS
**Новые задачи**: +5 критичных улучшений для надежности и безопасности

---

## 📝 Changelog версий

### v3.0 (20 ноября 2025) - External Analysis Integration

**Добавлено**:

- ✅ Circuit Breaker Pattern (P1) - защита от каскадных сбоев API
- ✅ Database Connection Pooling (P1) - оптимизация БД, индексы
- ✅ Enhanced Monitoring с Grafana (P2) - визуализация метрик
- ✅ Security Hardening (P2) - Bandit, Safety, Trivy audits
- ✅ Load & Stress Testing (P3) - Locust для performance testing

**Изменено**:

- Повышен приоритет Circuit Breaker и DB Pooling до P1
- Обновлена roadmap: 40 дней вместо 30
- Расширена таблица приоритетов: 18 задач вместо 13

**Итого**: 5 новых критичных улучшений для enterprise-level надежности

### v2.0 (20 ноября 2025) - ToS Compliance Update

**Добавлено**:

- Все полезные идеи из UPDATE_PLAN.md без нарушения ToS
- Расширенная детекция ликвидности, WebSocket, Resource Monitor

### v1.0 (20 ноября 2025) - Initial Personal Plan

**Создано**:

- Базовый план для single-user режима
- Фаза 1 (P1): Auto-recovery, Sentry, Batch Processing, Schema Validation

---
