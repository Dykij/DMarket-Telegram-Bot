# 🏗️ Архитектура проекта DMarket Telegram Bot

**Дата**: 12 декабря 2025 г.
**Версия**: 3.0
**Последнее обновление**: Рефакторинг R-1 (api/) и R-2 (scanner/) завершен

---

## 📋 Обзор

DMarket Telegram Bot — это асинхронное Python-приложение для автоматизации торговли игровыми предметами на платформе DMarket. Проект построен на современных архитектурных принципах и следует лучшим практикам разработки.

**Технологический стек**:

- Python 3.10+ (3.11+ рекомендуется)
- python-telegram-bot 20.7+
- httpx 0.27+ (async HTTP)
- SQLAlchemy 2.0+ (ORM)
- Pydantic 2.5+ (validation)
- Ruff 0.8+ (linting)
- MyPy 1.11+ (type checking)
- pytest 7.4+ (testing)

---

## 🎯 Ключевые принципы архитектуры

### 1. Модульность

Проект разделен на логические модули с четкой ответственностью:

- **DMarket API** - Взаимодействие с внешним API
- **Telegram Bot** - Интерфейс пользователя
- **Models** - Модели данных
- **Utils** - Вспомогательные утилиты

### 2. Асинхронность

Все операции ввода-вывода выполняются асинхронно с использованием `asyncio`:

```python
async def fetch_market_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### 3. Разделение ответственности (Separation of Concerns)

Каждый компонент отвечает за свою область:

- **API клиенты** - только HTTP запросы
- **Бизнес-логика** - в отдельных сервисах
- **Обработчики команд** - только маршрутизация
- **Модели** - только данные

### 4. Dependency Injection

Зависимости передаются через конструкторы:

```python
class ArbitrageScanner:
    def __init__(self, api_client: DMarketAPI, cache: Cache):
        self.api = api_client
        self.cache = cache
```

---

## 📦 Структура проекта

```
DMarket-Telegram-Bot/
├── src/                          # Исходный код
│   ├── dmarket/                  # Модуль DMarket API
│   │   ├── api/                 # 📦 Модульный API клиент (R-1)
│   │   │   ├── __init__.py
│   │   │   ├── endpoints.py     # API эндпоинты
│   │   │   ├── auth.py          # Ed25519/HMAC подписи
│   │   │   ├── cache.py         # Кэширование запросов
│   │   │   └── client.py        # HTTP клиент
│   │   ├── scanner/             # 📦 Модульный сканер (R-2)
│   │   │   ├── __init__.py      # Публичный API
│   │   │   ├── levels.py        # Конфигурации уровней
│   │   │   ├── cache.py         # ScannerCache с TTL
│   │   │   ├── filters.py       # ScannerFilters
│   │   │   └── analysis.py      # Расчет прибыли
│   │   ├── dmarket_api.py       # Основной API клиент
│   │   ├── arbitrage_scanner.py # Сканер арбитража
│   │   ├── targets.py           # Управление таргетами
│   │   ├── arbitrage.py         # Логика арбитража
│   │   ├── item_filters.py      # Blacklist/whitelist
│   │   └── game_filters.py      # Фильтры игр
│   │
│   ├── telegram_bot/             # Telegram бот
│   │   ├── commands/            # Обработчики команд
│   │   ├── handlers/            # Обработчики событий
│   │   ├── keyboards.py         # Клавиатуры
│   │   └── localization.py      # Локализация
│   │
│   ├── models/                   # Модели данных
│   │   ├── user.py              # Модель пользователя
│   │   └── target.py            # Модель таргета
│   │
│   └── utils/                    # Утилиты
│       ├── database.py          # База данных
│       ├── cache.py             # Кэширование
│       ├── rate_limiter.py      # Rate limiting
│       └── logging_utils.py     # Логирование
│
├── tests/                        # Тесты
├── docs/                         # Документация
└── config/                       # Конфигурация
```

---

## 🔄 Поток данных

### Запрос пользователя → Ответ

```
┌─────────────┐
│  Пользователь │
└──────┬──────┘
       │ Telegram сообщение
       ▼
┌─────────────────┐
│ Telegram Bot API │
└──────┬──────────┘
       │
       ▼
┌──────────────────────┐
│ Command Handler      │ (src/telegram_bot/handlers/)
│ - Валидация входных │
│ - Маршрутизация      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Business Logic Layer │ (src/dmarket/)
│ - ArbitrageScanner   │
│ - TargetManager      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ DMarket API Client   │ (src/dmarket/dmarket_api.py)
│ - HTTP запросы       │
│ - Аутентификация     │
│ - Rate limiting      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   DMarket API        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Response Processing  │
│ - Парсинг данных     │
│ - Кэширование        │
│ - Логирование        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Response to User     │
│ - Форматирование     │
│ - Локализация        │
└──────────────────────┘
```

---

## 🗃️ Слои приложения

### 1. Presentation Layer (Telegram Bot)

**Ответственность:**

- Прием команд от пользователя
- Валидация входных данных
- Форматирование ответов
- Локализация

**Компоненты:**

- `src/telegram_bot/handlers/` - обработчики команд
- `src/telegram_bot/keyboards.py` - UI элементы
- `src/telegram_bot/localization.py` - переводы

### 2. Business Logic Layer

**Ответственность:**

- Бизнес-логика арбитража
- Управление таргетами
- Анализ рынка
- Стратегии торговли

**Компоненты:**

- `src/dmarket/arbitrage_scanner.py`
- `src/dmarket/targets.py`
- `src/dmarket/arbitrage.py`

### 3. Data Access Layer

**Ответственность:**

- Взаимодействие с DMarket API
- Кэширование данных
- Rate limiting
- Обработка ошибок API

**Компоненты:**

- `src/dmarket/dmarket_api.py`
- `src/utils/cache.py`
- `src/utils/rate_limiter.py`

### 4. Persistence Layer

**Ответственность:**

- Работа с базой данных
- Хранение пользовательских данных
- История сделок

**Компоненты:**

- `src/models/` - модели SQLAlchemy
- `src/utils/database.py` - менеджер БД

---

## 🔌 Интеграции

### DMarket API

```python
class DMarketAPI:
    """Клиент для взаимодействия с DMarket API."""

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        base_url: str = "https://api.dmarket.com"
    ):
        self.public_key = public_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.rate_limiter = RateLimiter()

    async def _sign_request(self, method: str, path: str, body: str = "") -> dict:
        """Создать подпись для запроса."""
        timestamp = str(int(time.time()))
        string_to_sign = timestamp + method + path + body

        signature = hmac.new(
            self.secret_key.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            "X-Api-Key": self.public_key,
            "X-Sign-Date": timestamp,
            "X-Request-Sign": signature
        }

    async def get_market_items(self, game: str, **kwargs) -> dict:
        """Получить предметы с рынка."""
        await self.rate_limiter.wait_for_call('market')

        headers = await self._sign_request("GET", "/marketplace-api/v1/items")
        params = {"gameId": game, **kwargs}

        response = await self.client.get(
            f"{self.base_url}/marketplace-api/v1/items",
            headers=headers,
            params=params
        )

        return response.json()
```

### Telegram Bot API

```python
from telegram.ext import Application, CommandHandler

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Регистрация обработчиков
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("arbitrage", arbitrage_command))
application.add_handler(CommandHandler("targets", targets_command))

# Запуск бота
application.run_polling()
```

---

## 💾 Модели данных

### User Model

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    language = Column(String, default='ru')
    api_key_encrypted = Column(String)  # Зашифрованный API ключ
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### Target Model

```python
class Target(Base):
    __tablename__ = 'targets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    target_id = Column(String, unique=True)  # ID от DMarket
    game = Column(String, nullable=False)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Integer, default=1)
    status = Column(String, default='active')  # active, executed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
```

---

## 🔒 Безопасность

### Аутентификация

- HMAC-SHA256 подписи для DMarket API
- Шифрование API ключей пользователей в БД
- Rate limiting для предотвращения злоупотреблений

### Валидация

```python
from pydantic import BaseModel, validator

class CreateTargetRequest(BaseModel):
    game: str
    title: str
    price: float
    amount: int = 1

    @validator('price')
    def validate_price(cls, v):
        if not 0.01 <= v <= 10000:
            raise ValueError('Price must be between 0.01 and 10000')
        return v

    @validator('game')
    def validate_game(cls, v):
        allowed_games = ['csgo', 'dota2', 'tf2', 'rust']
        if v not in allowed_games:
            raise ValueError(f'Game must be one of {allowed_games}')
        return v
```

---

## ⚡ Производительность

### Кэширование

```python
from aiocache import cached

@cached(ttl=300)  # Кэш на 5 минут
async def get_market_items(game: str) -> list[dict]:
    """Получить предметы с рынка (с кэшированием)."""
    return await api.get_market_items(game)
```

### Connection Pooling

```python
# HTTP клиент с пулом соединений
client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20
    )
)
```

### Rate Limiting

```python
from aiolimiter import AsyncLimiter

rate_limiter = AsyncLimiter(max_rate=30, time_period=60)  # 30 req/min

async def api_call():
    async with rate_limiter:
        response = await client.get(url)
        return response.json()
```

---

## 📊 Мониторинг и логирование

### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "arbitrage_scan_completed",
    game="csgo",
    opportunities_found=15,
    scan_duration_ms=1250,
    user_id=123456789
)
```

### Метрики (Prometheus)

```python
from prometheus_client import Counter, Histogram

request_count = Counter(
    'dmarket_api_requests_total',
    'Total DMarket API requests',
    ['endpoint', 'status']
)

response_time = Histogram(
    'dmarket_api_response_seconds',
    'DMarket API response time',
    ['endpoint']
)
```

---

## 🔄 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=src --cov-report=xml
      - run: ruff check .
      - run: mypy src/

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: ./deploy.sh
```

---

## 🚀 Масштабирование

### Горизонтальное масштабирование

Бот может быть развернут в нескольких экземплярах за load balancer:

```
                ┌─────────────┐
                │   Nginx     │
                │Load Balancer│
                └──────┬──────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼───┐     ┌────▼───┐     ┌────▼───┐
   │ Bot #1 │     │ Bot #2 │     │ Bot #3 │
   └────┬───┘     └────┬───┘     └────┬───┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                ┌──────▼──────┐
                │  PostgreSQL │
                │    + Redis  │
                └─────────────┘
```

### Вертикальное масштабирование

- Увеличение ресурсов сервера (CPU, RAM)
- Оптимизация запросов к БД
- Использование индексов
- Connection pooling

---

## 📚 Дополнительные ресурсы

- [Python Async Best Practices](https://realpython.com/async-io-python/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [DMarket API Documentation](https://docs.dmarket.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

---

## 📐 UML Диаграммы

### Диаграмма компонентов

```plantuml
@startuml
package "Telegram Bot Layer" {
  [Command Handlers]
  [Keyboards]
  [Localization]
  [Notification Manager]
}

package "Business Logic Layer" {
  [Arbitrage Scanner]
  [Target Manager]
  [Market Analyzer]
  [Price Predictor]
}

package "Data Access Layer" {
  [DMarket API Client]
  [Database Manager]
  [Cache Manager]
  [WebSocket Client]
}

package "Infrastructure" {
  [Rate Limiter]
  [Logger]
  [Config Manager]
  [Encryption Manager]
}

database "PostgreSQL" {
  [Users]
  [Targets]
  [Trades]
  [Analytics]
}

cloud "DMarket API" {
  [REST API]
  [WebSocket API]
}

[Command Handlers] --> [Arbitrage Scanner]
[Command Handlers] --> [Target Manager]
[Command Handlers] --> [Market Analyzer]

[Arbitrage Scanner] --> [DMarket API Client]
[Target Manager] --> [DMarket API Client]
[Market Analyzer] --> [Database Manager]

[DMarket API Client] --> [REST API]
[WebSocket Client] --> [WebSocket API]
[DMarket API Client] --> [Rate Limiter]

[Database Manager] --> [Users]
[Database Manager] --> [Targets]
[Database Manager] --> [Trades]

[Cache Manager] --> [PostgreSQL]
@enduml
```

### Диаграмма последовательности: Поиск арбитража

```plantuml
@startuml
actor User
participant "Telegram Bot" as Bot
participant "ArbitrageScanner" as Scanner
participant "DMarket API" as API
participant "MarketAnalyzer" as Analyzer
participant "Cache" as Cache
database "Database" as DB

User -> Bot: /arbitrage standard csgo
activate Bot

Bot -> Scanner: scan_level("standard", "csgo")
activate Scanner

Scanner -> Cache: get_cached_items("csgo")
activate Cache
Cache --> Scanner: None (cache miss)
deactivate Cache

Scanner -> API: get_market_items(game="csgo", price_from=300, price_to=1000)
activate API
API --> Scanner: items_data
deactivate API

Scanner -> Scanner: filter_by_profit(items, min_profit=5%)

loop For each profitable item
  Scanner -> Analyzer: calculate_fair_price(item)
  activate Analyzer
  Analyzer -> DB: get_price_history(item_id)
  activate DB
  DB --> Analyzer: price_history
  deactivate DB
  Analyzer --> Scanner: fair_price
  deactivate Analyzer

  Scanner -> Analyzer: predict_price_drop(item)
  activate Analyzer
  Analyzer --> Scanner: prediction
  deactivate Analyzer
end

Scanner -> Cache: cache_items(items, ttl=300)
activate Cache
deactivate Cache

Scanner --> Bot: opportunities[]
deactivate Scanner

Bot -> Bot: format_results(opportunities)
Bot -> User: "Найдено 5 возможностей:\n..."
deactivate Bot
@enduml
```

### Диаграмма последовательности: Создание таргета

```plantuml
@startuml
actor User
participant "Telegram Bot" as Bot
participant "TargetManager" as TM
participant "DMarket API" as API
participant "Database" as DB
participant "Notifier" as Notifier

User -> Bot: /targets create\nAK-47 | Redline\nPrice: $8.00
activate Bot

Bot -> TM: create_target(user_id, title, price)
activate TM

TM -> API: get_aggregated_prices(title)
activate API
API --> TM: current_prices
deactivate API

TM -> TM: validate_target_price(price, current_prices)

alt Price is valid
  TM -> API: create_targets([target_data])
  activate API
  API --> TM: {"TargetID": "123", "Status": "Created"}
  deactivate API

  TM -> DB: save_target(user_id, target_id, title, price)
  activate DB
  DB --> TM: target_saved
  deactivate DB

  TM -> Notifier: send_notification(user_id, "Target created")
  activate Notifier
  deactivate Notifier

  TM --> Bot: {"success": True, "target_id": "123"}
else Price is too low
  TM --> Bot: {"error": "Price too low"}
end

deactivate TM

Bot -> User: "✅ Таргет создан!"
deactivate Bot
@enduml
```

### Диаграмма последовательности: WebSocket уведомления

```plantuml
@startuml
participant "ReactiveDMarketWS" as WS
participant "Observable" as Obs
participant "Observer 1\n(Balance Monitor)" as Obs1
participant "Observer 2\n(Trading Bot)" as Obs2
participant "Telegram Notifier" as Notif
database "Database" as DB

WS -> WS: connect()
activate WS

WS -> Obs: create(EventType.BALANCE_UPDATE)
activate Obs

Obs1 -> Obs: subscribe(on_balance_update)
Obs2 -> Obs: subscribe(on_balance_change)

WS -> WS: _listen_for_events()

loop WebSocket messages
  WS -> WS: receive_message()
  WS -> WS: parse_event(message)

  alt Event is BALANCE_UPDATE
    WS -> Obs: notify_observers(balance_data)

    Obs -> Obs1: on_balance_update(balance_data)
    activate Obs1
    Obs1 -> DB: log_balance_change(balance_data)
    deactivate Obs1

    Obs -> Obs2: on_balance_change(balance_data)
    activate Obs2
    Obs2 -> Obs2: check_trading_conditions()
    Obs2 -> Notif: send_notification(user_id, "Balance updated")
    deactivate Obs2
  end
end

deactivate Obs
deactivate WS
@enduml
```

### Диаграмма классов: Аналитика рынка

```plantuml
@startuml
class TechnicalIndicators {
  + {static} rsi(prices: List[float], period: int = 14): Optional[float]
  + {static} macd(prices: List[float], fast: int = 12, slow: int = 26): Optional[Dict]
  + {static} bollinger_bands(prices: List[float], period: int = 20): Optional[Dict]
  - {static} _calculate_sma(prices: List[float], period: int): float
  - {static} _calculate_ema(prices: List[float], period: int): float
}

class MarketAnalyzer {
  - min_data_points: int
  + calculate_fair_price(history: List[PricePoint], method: str): Optional[float]
  + detect_trend(history: List[PricePoint], short: int, long: int): TrendDirection
  + predict_price_drop(history: List[PricePoint], threshold: float): Dict
  + calculate_support_resistance(history: List[PricePoint]): Dict
  + analyze_liquidity(history: List[PricePoint], period: int): Dict
  + generate_trading_insights(history: List[PricePoint], current_price: float): Dict
  - _calculate_vwap(history: List[PricePoint]): float
}

class PricePoint {
  + timestamp: datetime
  + price: float
  + volume: Optional[int]
  __init__(timestamp, price, volume)
}

enum TrendDirection {
  BULLISH
  BEARISH
  NEUTRAL
}

enum SignalType {
  BUY
  SELL
  HOLD
}

MarketAnalyzer --> TechnicalIndicators: uses
MarketAnalyzer --> PricePoint: analyzes
MarketAnalyzer --> TrendDirection: returns
MarketAnalyzer --> SignalType: returns
@enduml
```

### Диаграмма классов: WebSocket Observable Pattern

```plantuml
@startuml
class Observable<T> {
  - _observers: List[Observer]
  + subscribe(observer: Observer): None
  + unsubscribe(observer: Observer): None
  + notify(data: T): None
}

interface Observer {
  + on_next(data: Any): None
  + on_error(error: Exception): None
  + on_complete(): None
}

class ReactiveDMarketWebSocket {
  - _url: str
  - _session: Optional[ClientSession]
  - _ws: Optional[ClientWebSocketResponse]
  - _observables: Dict[EventType, Observable]
  - _subscriptions: Dict[str, Subscription]
  - _reconnect_delay: int

  + connect(): None
  + disconnect(): None
  + subscribe_to(event_type: EventType, observer: Observer): str
  + unsubscribe(subscription_id: str): None
  + subscribe_to_balance_updates(callback): str
  + subscribe_to_order_events(callback): str
  + subscribe_to_market_prices(item_ids: List[str], callback): str
  + get_subscription_stats(subscription_id: str): Dict
  - _listen_for_events(): None
  - _handle_event(event_type: EventType, data: Any): None
  - _reconnect(): None
}

class Subscription {
  + id: str
  + event_type: EventType
  + observer: Observer
  + state: SubscriptionState
  + created_at: datetime
  + stats: Dict
}

enum EventType {
  BALANCE_UPDATE
  ORDER_CREATED
  ORDER_UPDATED
  ORDER_CANCELLED
  ORDER_FILLED
  TRADE_EXECUTED
  TARGET_EXECUTED
  MARKET_PRICE_UPDATE
  ITEM_SOLD
  ERROR
}

enum SubscriptionState {
  IDLE
  SUBSCRIBING
  ACTIVE
  PAUSED
  ERROR
  CLOSED
}

ReactiveDMarketWebSocket *-- Observable: manages
ReactiveDMarketWebSocket *-- Subscription: tracks
Observable o-- Observer: notifies
Subscription --> EventType: categorizes
Subscription --> SubscriptionState: tracks
Subscription --> Observer: wraps
@enduml
```

### Диаграмма развертывания

```plantuml
@startuml
node "Application Server" {
  component "DMarket Bot" {
    [Telegram Bot]
    [Business Logic]
    [API Client]
  }
}

node "Database Server" {
  database "PostgreSQL" {
    [Users DB]
    [Targets DB]
    [Analytics DB]
  }
}

node "Cache Server" {
  database "Redis" {
    [Market Data Cache]
    [Session Cache]
  }
}

cloud "External Services" {
  [Telegram API]
  [DMarket REST API]
  [DMarket WebSocket]
}

[Telegram Bot] --> [Telegram API]: HTTPS
[API Client] --> [DMarket REST API]: HTTPS
[API Client] --> [DMarket WebSocket]: WSS
[Business Logic] --> [PostgreSQL]: TCP
[Business Logic] --> [Redis]: TCP

note right of [DMarket Bot]
  Python 3.11+
  python-telegram-bot 20.7+
  httpx 0.27+
  SQLAlchemy 2.0+
end note

note right of [PostgreSQL]
  Version 14+
  TimescaleDB extension
  for time-series data
end note

note right of [Redis]
  Version 7+
  Used for caching
  and rate limiting
end note
@enduml
```

### Диаграмма состояний: Жизненный цикл таргета

```plantuml
@startuml
[*] --> Created: create_target()

Created --> Active: activate()
Created --> Cancelled: cancel()

Active --> Executing: item_found()
Active --> Paused: pause()
Active --> Cancelled: cancel()

Paused --> Active: resume()
Paused --> Cancelled: cancel()

Executing --> Executed: purchase_success()
Executing --> Failed: purchase_failed()
Executing --> Active: retry()

Executed --> [*]
Failed --> Active: retry()
Failed --> Cancelled: cancel()
Cancelled --> [*]

note right of Active
  Listening for matching items
  on DMarket marketplace
end note

note right of Executing
  Attempting to purchase
  the matched item
end note
@enduml
```

### Диаграмма use case

```plantuml
@startuml
left to right direction

actor "Пользователь" as User
actor "DMarket API" as API

rectangle "DMarket Telegram Bot" {
  usecase "Поиск арбитража" as UC1
  usecase "Создать таргет" as UC2
  usecase "Просмотр баланса" as UC3
  usecase "Анализ рынка" as UC4
  usecase "Автоторговля" as UC5
  usecase "Получить уведомления" as UC6
  usecase "Просмотр статистики" as UC7

  usecase "Расчет справедливой цены" as UC8
  usecase "Предсказание цен" as UC9
  usecase "Технический анализ" as UC10
}

User --> UC1
User --> UC2
User --> UC3
User --> UC4
User --> UC5
User --> UC6
User --> UC7

UC1 ..> UC8: <<include>>
UC1 ..> UC9: <<include>>
UC4 ..> UC8: <<include>>
UC4 ..> UC9: <<include>>
UC4 ..> UC10: <<include>>

UC5 ..> UC1: <<extend>>
UC5 ..> UC2: <<extend>>

UC1 --> API: запрос данных
UC2 --> API: создание заявки
UC3 --> API: запрос баланса
UC5 --> API: покупка/продажа
@enduml
```

---

## 📊 Метрики архитектуры

### Показатели качества

| Метрика                      | Текущее значение | Целевое значение |
| ---------------------------- | ---------------- | ---------------- |
| Test Coverage                | 25% → 85%        | 90%+             |
| Code Complexity (cyclomatic) | < 10             | < 10             |
| Duplication                  | < 3%             | < 5%             |
| Type Coverage (MyPy)         | 100% (strict)    | 100%             |
| Dependencies                 | 45               | < 50             |

### Performance KPIs

| Операция                   | SLA     | Текущее |
| -------------------------- | ------- | ------- |
| Arbitrage Scan (100 items) | < 2s    | ~1.2s   |
| Target Creation            | < 500ms | ~300ms  |
| WebSocket Reconnect        | < 5s    | ~2s     |
| Fair Price Calculation     | < 100ms | ~50ms   |
| Price Prediction           | < 200ms | ~120ms  |

---

**Архитектура проекта постоянно эволюционирует для соответствия новым требованиям и best practices.**
