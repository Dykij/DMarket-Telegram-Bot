# GitHub Copilot - Контекст рабочего пространства

## 🎯 О проекте

**DMarket Telegram Bot** - асинхронный Python-бот для автоматизации торговли игровыми предметами на платформе DMarket.

### Ключевые возможности

- 🎯 5 уровней арбитража (от новичка до профессионала)
- 🤖 Автоматические Buy Orders (таргеты)
- 📊 Real-time мониторинг через WebSocket
- 🎮 Поддержка: CS:GO, Dota 2, TF2, Rust
- 📈 Анализ рынка с ML-предсказаниями
- 🌐 Мультиязычность: RU, EN, ES, DE
- 🔒 Шифрование API-ключей
- 🧪 85%+ покрытие тестами

## 🏗️ Архитектура

### Основные модули

```
src/
├── dmarket/              # DMarket API клиент
│   ├── dmarket_api.py   # HMAC-SHA256 аутентификация
│   ├── arbitrage_scanner.py  # 5-уровневый сканер
│   ├── targets.py       # Управление таргетами
│   └── game_filters.py  # Фильтры для игр
├── telegram_bot/         # Telegram интерфейс
│   ├── handlers/        # Обработчики команд
│   ├── keyboards.py     # UI клавиатуры
│   └── localization.py  # i18n
├── utils/                # Утилиты
│   ├── rate_limiter.py  # API rate limiting
│   ├── cache.py         # Redis кэш
│   └── logging_utils.py # Структурированное логирование
└── models/               # SQLAlchemy 2.0 модели
```

### Технологический стек

**Backend:**

- Python 3.11+ (async/await)
- httpx (HTTP клиент)
- SQLAlchemy 2.0 + asyncpg
- Redis + aiocache
- structlog (JSON logging)

**Telegram:**

- python-telegram-bot 20.7+
- Inline keyboards
- Webhook поддержка

**DevOps:**

- Docker + docker-compose
- GitHub Actions CI/CD
- Sentry (мониторинг)
- Prometheus (метрики)

**Качество кода:**

- Ruff (линтер + форматтер)
- MyPy (strict mode)
- pytest + pytest-asyncio
- Coverage 85%+

## 📝 Стандарты кодирования

### Асинхронность

**✅ Правильно:**

```python
async def fetch_items(game: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/items?game={game}")
        return response.json()
```

**❌ Неправильно:**

```python
def fetch_items(game: str) -> list[dict]:  # Нет типов, синхронно
    response = requests.get(f"/items?game={game}")
    return response.json()
```

### Типизация

**Всегда используйте аннотации типов:**

```python
from typing import TypeAlias

PriceData: TypeAlias = dict[str, float | int]

async def get_price(
    item_id: str,
    currency: str = "USD"
) -> PriceData | None:
    """Получить цену предмета."""
    ...
```

### Логирование

**Структурированное логирование:**

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "order_processed",
    order_id=order_id,
    user_id=user_id,
    amount=amount
)
```

### Обработка ошибок

**С retry логикой:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def api_call(url: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error("api_call_failed", url=url, error=str(e))
        raise
```

## 🔧 Инструменты разработки

### Запуск проверок

```bash
# Линтинг + форматирование
ruff check src/ --fix
ruff format src/

# Проверка типов
mypy src/

# Тесты с покрытием
pytest --cov=src --cov-report=html

# Всё вместе
ruff check . && mypy src/ && pytest
```

### VS Code задачи

- **Ruff: Check** - проверка кода
- **Ruff: Fix** - автоисправление
- **MyPy: Type Check** - проверка типов
- **Pytest: Run All Tests** - все тесты
- **QA: Run All Checks** - полная проверка

## 🎮 DMarket API

### Аутентификация

```python
# HMAC-SHA256 подпись
timestamp = str(int(time.time()))
string_to_sign = timestamp + method + path + body
signature = hmac.new(
    secret_key.encode(),
    string_to_sign.encode(),
    hashlib.sha256
).hexdigest()
```

### Основные эндпоинты

- **GET** `/account/v1/balance` - баланс
- **GET** `/exchange/v1/market/items` - предметы на рынке
- **POST** `/marketplace-api/v1/user-targets/create` - создать таргеты
- **GET** `/marketplace-api/v1/user-targets` - получить таргеты

### Game IDs

- CS:GO/CS2: `a8db`
- Dota 2: `9a92`
- TF2: `tf2`
- Rust: `rust`

## 📚 Документация

Подробная документация в `docs/`:

- `QUICK_START.md` - быстрый старт
- `ARCHITECTURE.md` - архитектура
- `MULTI_LEVEL_ARBITRAGE_GUIDE.md` - арбитраж
- `DMARKET_API_FULL_SPEC.md` - API спецификация
- `SECURITY.md` - безопасность
- `code_quality_tools_guide.md` - инструменты качества

## 🚫 Что НЕ делать

- ❌ НЕ создавать отчетные MD-файлы после задач
- ❌ НЕ использовать синхронный код для I/O
- ❌ НЕ хардкодить секреты
- ❌ НЕ использовать голые `except:`
- ❌ НЕ пропускать аннотации типов
- ❌ НЕ игнорировать rate limiting

## ✅ Best Practices

- ✅ Async/await для всех I/O операций
- ✅ Типы везде (MyPy strict mode)
- ✅ Структурированное логирование
- ✅ Retry логика с tenacity
- ✅ Rate limiting для API
- ✅ Кэширование с Redis
- ✅ Тесты для всего (80%+)
- ✅ Docstrings (Google Style)

## 🔄 Git Workflow

### Conventional Commits

```
feat(arbitrage): add cross-game scanning
fix(api): handle rate limit errors
docs(readme): update installation steps
test(targets): add integration tests
refactor(cache): improve Redis client
```

### Pre-commit

```bash
# Установить hooks
pre-commit install

# Проверка перед коммитом:
# - Ruff check + fix
# - Ruff format
# - MyPy
# - Trailing whitespace
```

## 📊 Метрики качества

| Метрика           | Цель   | Текущая |
| ----------------- | ------ | ------- |
| Покрытие тестами  | 85%    | 85%+    |
| MyPy строгость    | strict | ✅       |
| Ruff ошибки       | 0      | ✅       |
| Сложность функций | ≤10    | ✅       |

## 🔐 Безопасность

- Шифрование API-ключей (Fernet)
- .env для секретов
- Rate limiting (30 req/min)
- Валидация входных данных
- HTTPS для всех запросов
- Логирование без секретов

## 🐳 Docker

```bash
# Сборка
docker build -t dmarket-bot .

# Запуск с compose
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot
```

## 🤖 Copilot подсказки

При генерации кода:

- Используй async/await
- Добавляй типы
- Логируй важные события
- Обрабатывай ошибки
- Пиши docstrings
- Следуй PEP 8
- Используй современный синтаксис Python 3.11+

---

**Версия**: 1.0
**Обновлено**: 15 ноября 2025 г.
