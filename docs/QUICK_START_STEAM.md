# ⚡ Quick Start: Steam Integration для арбитража

> Быстрая шпаргалка для внедрения Steam API в DMarket бот

---

## ✅ Статус выполнения задач

| Задача | Статус | Дата | Примечания |
|--------|--------|------|------------|
| 1️⃣ База данных | ✅ **ВЫПОЛНЕНО** | 03.01.2026 | `src/utils/steam_db_handler.py` создан, 15/15 тестов ✅ |
| 2️⃣ Steam API | ✅ **ВЫПОЛНЕНО** | 03.01.2026 | `src/dmarket/steam_api.py` создан с Rate Limit защитой |
| 3️⃣ Тесты | ✅ **ВЫПОЛНЕНО** | 03.01.2026 | Все тесты прошли, mypy проверка ✅ |
| 4️⃣ .env конфигурация | ✅ **ВЫПОЛНЕНО** | 03.01.2026 | Steam API ключ добавлен |
| 5️⃣ Интеграция | ✅ **ВЫПОЛНЕНО** | 03.01.2026 | `steam_arbitrage_enhancer.py` + команды ✅ |
| 6️⃣ Команды бота | ✅ **ВЫПОЛНЕНО** | 03.01.2026 | `/stats`, `/top`, `/steam_settings` ✅ |
| 7️⃣ Тестирование E2E | ✅ **ВЫПОЛНЕНО** | 03.01.2026 | `test_steam_integration.py` - все работает! ✅ |

**Прогресс MVP**: 7/7 задач (100%) ✅🎉 **MVP ЗАВЕРШЕН!**

---

## 🎯 Минимальный план (3 дня → работающий арбитраж)

### День 1: База данных

```bash
# Создать файл
src/utils/db_handler.py

# Запустить тест
python -m pytest tests/test_db_handler.py
```

### День 2: Steam API

```bash
# Создать файл
src/dmarket/steam_api.py

# Тестовый запрос
python -c "import asyncio; from src.dmarket.steam_api import get_steam_price; print(asyncio.run(get_steam_price('AK-47 | Slate (Field-Tested)')))"
```

### День 3: Интеграция

```bash
# Обновить файл
src/main.py

# Запустить бота
python src/main.py
```

---

## 📋 Чеклист перед стартом

### Окружение

- [ ] Python 3.11+ установлен
- [ ] `httpx` установлен (`pip install httpx`)
- [ ] `aiosqlite` установлен (`pip install aiosqlite`)
- [ ] Папка `data/` существует

### Конфигурация

- [ ] `.env` файл создан
- [ ] `TELEGRAM_BOT_TOKEN` заполнен
- [ ] `DMARKET_PUBLIC_KEY` заполнен
- [ ] `DMARKET_SECRET_KEY` заполнен
- [ ] `ADMIN_ID` заполнен

### Безопасность

- [ ] `.env` добавлен в `.gitignore`
- [ ] Rate limit защита реализована (2 сек между запросами)
- [ ] Backoff при 429 ошибке (5 мин пауза)

---

## 🔥 Критические параметры

```python
# Steam API
STEAM_REQUEST_DELAY = 2  # секунды между запросами
STEAM_BACKOFF_MINUTES = 5  # пауза при 429 ошибке
STEAM_CACHE_HOURS = 6  # актуальность кэша

# Арбитраж
MIN_PROFIT_PERCENT = 10.0  # минимальный профит
MIN_VOLUME = 50  # минимальный объем продаж/день
DMARKET_FEE = 0.05  # комиссия DMarket 5%
STEAM_FEE = 0.1304  # комиссия Steam 13.04%

# App IDs
CSGO_APP_ID = 730
DOTA2_APP_ID = 570
TF2_APP_ID = 440
RUST_APP_ID = 252490
```

---

## 💻 Минимальный код (копипаста)

### 1. Steam API (`src/dmarket/steam_api.py`)

```python
import httpx
from datetime import datetime, timedelta

steam_backoff_until = None

async def get_steam_price(item_name: str, app_id: int = 730):
    global steam_backoff_until

    if steam_backoff_until and datetime.now() < steam_backoff_until:
        return None

    url = "https://steamcommunity.com/market/priceoverview/"
    params = {'appid': app_id, 'currency': 1, 'market_hash_name': item_name}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=10)

        if response.status_code == 429:
            steam_backoff_until = datetime.now() + timedelta(minutes=5)
            return None

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return {
                    'price': float(data['lowest_price'].replace('$', '').replace(',', '')),
                    'volume': int(data['volume'].replace(',', ''))
                }
    return None

def calculate_arbitrage(dmarket_price: float, steam_price: float) -> float:
    return round(((steam_price * 0.8696 - dmarket_price) / dmarket_price) * 100, 2)
```

### 2. База данных (`src/utils/db_handler.py`)

```python
import sqlite3
from datetime import datetime, timedelta

class DatabaseHandler:
    def __init__(self, db_path="data/bot_database.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS steam_cache (
                    market_hash_name TEXT PRIMARY KEY,
                    lowest_price REAL,
                    volume INTEGER,
                    last_updated TIMESTAMP
                )
            """)

    def update_steam_price(self, name: str, price: float, volume: int):
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO steam_cache VALUES (?, ?, ?, ?)",
                (name, price, volume, datetime.now())
            )

    def get_steam_data(self, name: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT lowest_price, volume, last_updated FROM steam_cache WHERE market_hash_name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return {'price': row[0], 'volume': row[1], 'last_updated': row[2]}
        return None

    def is_actual(self, last_updated, hours=6):
        return datetime.now() - datetime.fromisoformat(last_updated) < timedelta(hours=hours)
```

### 3. Интеграция (`src/main.py` - фрагмент)

```python
import asyncio
from src.dmarket.steam_api import get_steam_price, calculate_arbitrage
from src.utils.db_handler import DatabaseHandler

db = DatabaseHandler()

async def scan_arbitrage():
    # 1. Получить предметы с DMarket
    dmarket_items = await dmarket_api.get_market_items(limit=50)

    for item in dmarket_items:
        # 2. Проверить кэш Steam
        steam_data = db.get_steam_data(item['title'])

        if not steam_data or not db.is_actual(steam_data['last_updated']):
            # 3. Запрос к Steam (с паузой!)
            steam_data = await get_steam_price(item['title'])
            if steam_data:
                db.update_steam_price(item['title'], steam_data['price'], steam_data['volume'])
            await asyncio.sleep(2)  # КРИТИЧНО!

        # 4. Анализ профита
        if steam_data and steam_data['volume'] >= 50:
            profit = calculate_arbitrage(item['price'], steam_data['price'])
            if profit >= 10:
                print(f"🔥 {item['title']}: {profit}% профит!")
```

---

## 🚨 Типичные ошибки

### ❌ Ошибка 1: Бан Steam API

**Симптом**: `429 Too Many Requests`

**Решение**:

```python
# Добавьте паузу ВЕЗДЕ
await asyncio.sleep(2)

# И backoff при 429
if response.status_code == 429:
    await asyncio.sleep(300)  # 5 минут
```

### ❌ Ошибка 2: Название не найдено

**Симптом**: `success: false`

**Решение**:

```python
# Нормализация названия
name = name.replace("Field Tested", "Field-Tested")
```

### ❌ Ошибка 3: База данных заблокирована

**Симптом**: `database is locked`

**Решение**:

```python
# Используйте один экземпляр БД
db = DatabaseHandler()  # Создать один раз!

# Не создавайте в каждой функции
```

---

## 📊 Проверка работы

### Тест 1: Steam API работает

```bash
python -c "
import asyncio
from src.dmarket.steam_api import get_steam_price

result = asyncio.run(get_steam_price('AK-47 | Slate (Field-Tested)'))
print(f'Цена: {result[\"price\"]}$ | Объем: {result[\"volume\"]}')
"
```

Ожидаемый результат: `Цена: 2.15$ | Объем: 145`

### Тест 2: БД сохраняет данные

```bash
python -c "
from src.utils.db_handler import DatabaseHandler

db = DatabaseHandler()
db.update_steam_price('Test Item', 10.50, 100)
data = db.get_steam_data('Test Item')
print(f'Сохранено: {data}')
"
```

Ожидаемый результат: `Сохранено: {'price': 10.5, 'volume': 100, ...}`

### Тест 3: Арбитраж работает

```bash
python -c "
from src.dmarket.steam_api import calculate_arbitrage

profit = calculate_arbitrage(dmarket_price=2.0, steam_price=2.5)
print(f'Профит: {profit}%')
"
```

Ожидаемый результат: `Профит: 8.7%`

---

## 🎓 Полезные команды

### Очистка кэша

```python
db.conn.execute("DELETE FROM steam_cache WHERE last_updated < datetime('now', '-1 day')")
db.conn.commit()
```

### Просмотр статистики БД

```python
cursor = db.conn.cursor()
cursor.execute("SELECT COUNT(*) FROM steam_cache")
print(f"В кэше: {cursor.fetchone()[0]} предметов")
```

### Проверка Rate Limit

```python
from datetime import datetime
if steam_backoff_until:
    remaining = (steam_backoff_until - datetime.now()).total_seconds()
    print(f"Backoff активен. Осталось: {remaining:.0f} сек")
```

---

## 📚 Документация

- **Подробный план**: `STEAM.md`
- **Steam API справка**: `docs/STEAM_API_REFERENCE.md`
- **Архитектура проекта**: `docs/ARCHITECTURE.md`

---

## 💬 Поддержка

Если что-то не работает:

1. Проверьте логи: `logs/bot.log`
2. Проверьте БД: `sqlite3 data/bot_database.db ".tables"`
3. Проверьте Steam API вручную:

   ```bash
   curl "https://steamcommunity.com/market/priceoverview/?appid=730&currency=1&market_hash_name=AK-47%20%7C%20Slate%20(Field-Tested)"
   ```

---

**Готово к старту!** 🚀

Следуйте чеклисту и через 3 дня у вас будет работающий арбитражный бот.
