# 🛡️ Руководство по санитарной проверке цен

**Дата**: 23 ноября 2025 г.
**Версия**: 1.0

---

## 📋 Обзор

Модуль **Price Sanity Checker** (`src/utils/price_sanity_checker.py`) обеспечивает защиту от покупок по аномально завышенным ценам, предотвращая финансовые потери из-за:

- ❌ Ошибок в API данных
- ❌ Манипуляций ценами на рынке
- ❌ Устаревших или некорректных данных
- ❌ Багов в логике арбитража

---

## 🔧 Как это работает

### Алгоритм проверки

1. **Получение истории цен** за последние 7 дней из базы данных
2. **Расчет средней цены** на основе исторических данных
3. **Определение максимальной допустимой цены**:
   ```
   Макс. допустимая цена = Средняя цена × 1.5
   ```
4. **Сравнение** текущей цены с максимальной допустимой
5. **Блокировка покупки** если цена превышает лимит

### Константы по умолчанию

| Константа                   | Значение | Описание                            |
| --------------------------- | -------- | ----------------------------------- |
| `MAX_PRICE_MULTIPLIER`      | 1.5      | Макс. 50% выше средней цены         |
| `HISTORY_DAYS`              | 7        | Период анализа истории              |
| `MIN_HISTORY_SAMPLES`       | 3        | Минимум записей для расчета средней |
| `enable_price_sanity_check` | True     | Проверка включена по умолчанию      |

---

## 🚀 Использование

### Базовый пример

```python
from src.utils.price_sanity_checker import PriceSanityChecker
from src.utils.database import DatabaseManager
from src.telegram_bot.notifier import TradingNotifier
from decimal import Decimal

# Инициализация
db = DatabaseManager(database_url="sqlite:///data/dmarket_bot.db")
notifier = TradingNotifier(bot_token="your_token", user_id=123456789)

checker = PriceSanityChecker(
    database_manager=db,
    notifier=notifier
)

# Проверка цены перед покупкой
try:
    result = await checker.check_price_sanity(
        item_name="AK-47 | Redline (Field-Tested)",
        current_price=Decimal("12.50"),
        game="csgo"
    )

    if result["passed"]:
        print(f"✅ Проверка пройдена!")
        print(f"Средняя цена: ${result['average_price']:.2f}")
        print(f"Отклонение: {result['price_deviation_percent']:.1f}%")

        # Продолжить с покупкой
        await buy_item(...)

except PriceSanityCheckFailed as e:
    print(f"❌ Покупка заблокирована: {e.message}")
    # Покупка автоматически заблокирована
```

### Интеграция в ArbitrageScanner

```python
from src.dmarket.arbitrage_scanner import ArbitrageScanner
from src.utils.price_sanity_checker import PriceSanityChecker

class SafeArbitrageScanner(ArbitrageScanner):
    """Сканер арбитража с санитарной проверкой цен."""

    def __init__(self, api_client, config, database, notifier):
        super().__init__(api_client, config)

        self.price_checker = PriceSanityChecker(
            database_manager=database,
            notifier=notifier
        )

    async def buy_item_safe(self, item_name: str, price: float, game: str):
        """Покупка предмета с проверкой цены."""
        from decimal import Decimal

        # Проверить адекватность цены
        try:
            await self.price_checker.check_price_sanity(
                item_name=item_name,
                current_price=Decimal(str(price)),
                game=game
            )
        except PriceSanityCheckFailed as e:
            logger.critical(
                "purchase_blocked_sanity_check",
                item=item_name,
                price=price,
                reason=e.message
            )
            # Отправить уведомление пользователю
            return {"success": False, "reason": "Price sanity check failed"}

        # Проверка пройдена - продолжить покупку
        return await self.api_client.buy_item(item_name, price)
```

---

## ⚙️ Конфигурация

### Через переменные окружения (.env)

```env
# Санитарная проверка цен
MAX_PRICE_MULTIPLIER=1.5          # Макс. 50% выше средней
PRICE_HISTORY_DAYS=7              # Анализировать 7 дней истории
MIN_HISTORY_SAMPLES=3             # Минимум 3 записи для расчета
ENABLE_PRICE_SANITY_CHECK=true    # Включить проверку
```

### Через config.yaml

```yaml
trading_safety:
  max_price_multiplier: 1.5
  price_history_days: 7
  min_history_samples: 3
  enable_price_sanity_check: true
```

### Программная настройка

```python
from src.utils.config import Config

config = Config.load()

# Изменить параметры
config.trading_safety.max_price_multiplier = 2.0  # Разрешить +100%
config.trading_safety.price_history_days = 14     # Анализировать 14 дней

# Отключить проверку (только для тестирования!)
config.trading_safety.enable_price_sanity_check = False
```

---

## 📊 Логирование

### Успешная проверка

```python
logger.info(
    "price_sanity_check_passed",
    item="AK-47 | Redline (FT)",
    current_price=12.50,
    average_price=11.80,
    deviation_percent=5.9
)
```

### Проваленная проверка (CRITICAL)

```python
logger.critical(
    "PRICE_SANITY_CHECK_FAILED",
    item="AK-47 | Redline (FT)",
    current_price=20.00,
    average_price=11.80,
    max_allowed=17.70,
    deviation_percent=69.5,
    multiplier=1.5
)
```

---

## 🚨 Уведомления в Telegram

При проваленной проверке отправляется критический алерт:

```
🚨 КРИТИЧЕСКИЙ АЛЕРТ: Санитарная проверка цены

❌ Заблокирована покупка
📦 Предмет: AK-47 | Redline (Field-Tested)

💵 Текущая цена: $20.00
📊 Средняя (7д): $11.80
🚫 Макс. допустимая: $17.70
📈 Превышение: +69.5%

⚠️ Возможные причины:
• Ошибка API
• Манипуляция ценой
• Устаревшие данные

✅ Покупка заблокирована автоматически
```

---

## 🧪 Тестирование

### Отключение проверки для тестов

```python
from src.utils.price_sanity_checker import PriceSanityChecker

checker = PriceSanityChecker(database_manager=db)

# Отключить проверку
checker.disable()

# Теперь проверка не будет блокировать покупки
result = await checker.check_price_sanity(...)
# result["passed"] всегда True

# Включить обратно
checker.enable()
```

### Mock истории цен для тестов

```python
from unittest.mock import AsyncMock

# Mock DatabaseManager
mock_db = AsyncMock()
mock_db.get_price_history = AsyncMock(return_value=[
    {"price_usd": 10.50, "timestamp": datetime.now()},
    {"price_usd": 11.00, "timestamp": datetime.now()},
    {"price_usd": 11.50, "timestamp": datetime.now()},
])

checker = PriceSanityChecker(database_manager=mock_db)

# Тестировать с mock данными
result = await checker.check_price_sanity(
    item_name="Test Item",
    current_price=Decimal("12.00"),
    game="csgo"
)
```

---

## ⚠️ Важные замечания

### Когда проверка НЕ выполняется

1. **Недостаточно истории** (< 3 записей):
   - Логируется предупреждение
   - Покупка **разрешается** с флагом `warning: True`
   - Рекомендуется накопить больше данных

2. **Проверка отключена** (`enable_price_sanity_check=false`):
   - Используйте только для тестирования!
   - В production всегда держите включенной

3. **Ошибка при получении истории**:
   - Покупка **блокируется** для безопасности
   - Исключение `PriceSanityCheckFailed` выбрасывается

### Рекомендации

✅ **DO:**
- Всегда проверяйте цену перед реальными покупками
- Регулярно сохраняйте market_data в БД для истории
- Мониторьте логи на `PRICE_SANITY_CHECK_FAILED`
- Настройте критические алерты в Telegram

❌ **DON'T:**
- Не отключайте проверку в production
- Не игнорируйте критические алерты
- Не устанавливайте `MAX_PRICE_MULTIPLIER` > 2.0 без веской причины

---

## 📚 См. также

- [SECURITY.md](SECURITY.md) - Общие вопросы безопасности
- [ROADMAP.md](../ROADMAP.md) - План развития проекта
- [QUICK_START.md](QUICK_START.md) - Быстрый старт

---

**Версия**: 1.0
**Последнее обновление**: 23 ноября 2025 г.
