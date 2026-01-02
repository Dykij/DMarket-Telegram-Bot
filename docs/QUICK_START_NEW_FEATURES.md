# 🚀 Quick Start: Новые функции (02 января 2026)

## 📦 Быстрый запуск новых фич

Этот документ содержит примеры использования всех новых функций, добавленных в бота.

---

## 1️⃣ TreeFilters - Категорийная фильтрация

### Использование в коде

```python
from src.dmarket.scanner.tree_filters import TreeFilterBuilder

# Создать фильтр для CS:GO Rifles
filter_builder = TreeFilterBuilder("csgo")
tree_filters = filter_builder.rifles().factory_new().build()

# Использовать в API запросе
params = {
    "gameId": "csgo",
    "treeFilters": tree_filters,
    "priceFrom": 1000,  # $10
    "priceTo": 5000,    # $50
}

items = await api_client.get_market_items(**params)
```

### Доступные категории

**CS:GO**:
- `.rifles()` - Винтовки
- `.pistols()` - Пистолеты
- `.knives()` - Ножи
- `.gloves()` - Перчатки

**Dota 2**:
- `.weapons()` - Оружие
- `.armor()` - Броня
- `.couriers()` - Курьеры

---

## 2️⃣ Aggregated Pre-Scan - Быстрое сканирование

### Использование

```python
from src.dmarket.scanner.aggregated_scanner import AggregatedScanner

scanner = AggregatedScanner(api_client)

# Быстрое сканирование топ-возможностей
top_opportunities = await scanner.quick_scan(
    game="csgo",
    titles=["AK-47 | Redline", "AWP | Asiimov", "M4A4 | Howl"],
    min_spread_percent=5.0,  # Минимум 5% спред
    limit=10
)

# Результат: список возможностей с best buy/sell ценами
for opp in top_opportunities:
    print(f"{opp['title']}: Spread ${opp['spread']:.2f} ({opp['spread_percent']:.1f}%)")
```

---

## 3️⃣ Attribute Filters - Фильтрация по атрибутам

### Использование

```python
from src.dmarket.scanner.attribute_filters import AttributeFilterBuilder

# CS:GO: Factory New с float < 0.01
builder = AttributeFilterBuilder("csgo")
filters = builder.exterior("Factory New").float_max(0.01).rarity("Covert").build()

# Применить к items
filtered_items = [item for item in items if builder.matches(item)]
```

### Примеры фильтров

**CS:GO**:
```python
# Float range
.float_range(0.00, 0.07)

# Stickers
.has_sticker("Katowice 2014")

# Multiple conditions
.exterior("Minimal Wear").rarity("Classified").weapon_type("Rifle")
```

**Dota 2**:
```python
# Hero-specific
.hero("Pudge").slot("Weapon").quality("Arcana")
```

---

## 4️⃣ Sales History - Анализ ликвидности

### Использование

```python
from src.dmarket.scanner.sales_history import SalesHistoryAnalyzer

analyzer = SalesHistoryAnalyzer(api_client)

# Получить ликвидность предмета
liquidity = await analyzer.get_item_liquidity(
    title="AK-47 | Redline (Field-Tested)",
    game_id="csgo",
    days=7  # За последнюю неделю
)

# Результат
print(f"Average Price: ${liquidity['average_price']:.2f}")
print(f"Sales Count: {liquidity['sales_count']}")
print(f"Volatility: {liquidity['volatility']:.2f}%")
print(f"Liquidity Score: {liquidity['liquidity_score']}/100")

# Фильтрация по ликвидности
is_liquid = liquidity["liquidity_score"] > 50
```

---

## 5️⃣ Scanner Manager - Унифицированный сканер

### Использование (All-in-One)

```python
from src.dmarket.scanner_manager import ScannerManager

manager = ScannerManager(api_client)

# Полное сканирование с всеми фильтрами
opportunities = await manager.scan_with_filters(
    game="csgo",
    level="standard",  # boost, standard, medium, advanced, pro

    # TreeFilters
    categories=["Rifle", "Pistol"],

    # Attribute Filters
    exterior="Factory New",
    float_max=0.02,
    rarity="Covert",

    # Sales History
    min_liquidity_score=60,
    min_sales_count=5,

    # Aggregated Pre-Scan
    use_pre_scan=True,
    min_spread_percent=3.0,
)

# Результат: отфильтрованные возможности арбитража
for opp in opportunities:
    print(f"{opp['title']}: ${opp['buy_price']:.2f} → ${opp['sell_price']:.2f}")
    print(f"  Profit: ${opp['profit']:.2f} ({opp['margin']:.1f}%)")
    print(f"  Liquidity: {opp['liquidity_score']}/100")
```

### Adaptive & Parallel Scanning

```python
# Adaptive Scanner - динамические интервалы
await manager.start_adaptive_scan(
    game="csgo",
    initial_interval=60,  # 1 минута
    max_interval=300,     # 5 минут
    volatility_threshold=5.0
)

# Parallel Scanner - мульти-игра
results = await manager.scan_all_games_parallel(
    games=["csgo", "dota2", "rust"],
    level="standard",
    max_concurrent=3
)
```

---

## 6️⃣ Telegram Bot - Минималистичный UI

### Кнопки главного меню

После запуска бота (`/start`), доступны кнопки:

1. **Automatic Arbitrage**
   - Выбор режима: Boost/Medium/Pro
   - API check перед сканированием
   - Мульти-игровое сканирование

2. **View Items**
   - Проданные предметы + прибыль
   - Выставленные предметы + ожидаемая прибыль

3. **Detailed Settings**
   - Настройка фильтров
   - Редактирование ценовых диапазонов

4. **API Check**
   - Standalone проверка DMarket API

### Пример использования

```python
# В main.py регистрация handlers
from src.telegram_bot.register_all_handlers import register_all_handlers

application = Application.builder().token(TOKEN).build()
register_all_handlers(application)
application.run_polling()
```

---

## 🧪 Тестирование новых фич

### Unit тесты

```bash
# TreeFilters
pytest tests/unit/dmarket/scanner/test_tree_filters.py -v

# Aggregated Scanner
pytest tests/unit/dmarket/scanner/test_aggregated_scanner.py -v

# Attribute Filters
pytest tests/unit/dmarket/scanner/test_attribute_filters.py -v

# Sales History
pytest tests/unit/dmarket/scanner/test_sales_history.py -v

# Scanner Manager
pytest tests/unit/dmarket/test_scanner_manager.py -v
```

### Integration тесты

```bash
# Полное сканирование
pytest tests/integration/ -v -k "scanner"

# Telegram Bot
pytest tests/telegram_bot/ -v
```

---

## 📝 Примеры конфигурации

### .env файл

```env
# DMarket API
DMARKET_PUBLIC_KEY=your_public_key
DMARKET_SECRET_KEY=your_secret_key
DRY_RUN=true  # Режим тестирования

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_USER_ID=123456789

# Scanner Settings
DEFAULT_SCAN_LEVEL=standard
ENABLE_PRE_SCAN=true
MIN_LIQUIDITY_SCORE=50
MIN_SPREAD_PERCENT=3.0
```

### config.yaml

```yaml
scanner:
  aggregated_pre_scan: true
  use_tree_filters: true
  min_liquidity_score: 60
  attribute_filters:
    csgo:
      exteriors: ["Factory New", "Minimal Wear"]
      max_float: 0.07
      rarities: ["Covert", "Classified"]
```

---

## 🚨 Важные замечания

### DRY_RUN режим

**ВСЕГДА** тестируйте новые функции в DRY_RUN режиме:

```python
api_client = DMarketAPI(
    public_key=os.getenv("DMARKET_PUBLIC_KEY"),
    secret_key=os.getenv("DMARKET_SECRET_KEY"),
    dry_run=True  # ✅ Безопасно для тестирования
)
```

### Rate Limiting

Все новые модули уважают DMarket API rate limits:
- Aggregated Scanner: max 30 req/min
- Sales History: max 20 req/min
- TreeFilters: не увеличивает количество запросов

### Ошибки

Если видите ошибки импорта (aiolimiter, vcr, hypothesis):

```bash
# Установить опциональные зависимости
pip install aiolimiter vcrpy hypothesis
```

---

## 📚 Дополнительная документация

- `docs/ARBITRAGE_IMPROVEMENTS_2026.md` - техническая спецификация
- `INTEGRATION_COMPLETE.md` - примеры интеграции
- `TELEGRAM_BOT_IMPROVEMENTS_COMPLETE.md` - Telegram bot гайд

---

**Дата**: 02 января 2026 г.
**Автор**: GitHub Copilot CLI
**Статус**: ✅ Готово к использованию
