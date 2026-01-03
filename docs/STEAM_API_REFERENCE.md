# 📚 Steam API Reference для DMarket Арбитража

> **Официальная документация Steam API и практические примеры**
>
> **Источник**: https://steamcommunity.com/dev
> **Дата**: Январь 2026
> **Язык**: Русский

---

## 📋 Содержание

1. [Обзор Steam Web API](#обзор-steam-web-api)
2. [Получение API ключа](#получение-api-ключа)
3. [Market Price Overview API](#market-price-overview-api)
4. [Коды валют](#коды-валют)
5. [App ID игр](#app-id-игр)
6. [Ограничения и лимиты](#ограничения-и-лимиты)
7. [Коды ошибок](#коды-ошибок)
8. [Примеры использования](#примеры-использования)
9. [Best Practices](#best-practices)

---

## 🌐 Обзор Steam Web API

### Что такое Steam Web API?

Steam Web API — это набор HTTP endpoints, которые позволяют получать данные о:
- Ценах предметов на Steam Market
- Профилях пользователей
- Достижениях в играх
- Информации об играх

### Базовые URL

```
# Community Market API (без ключа)
https://steamcommunity.com/market/priceoverview/

# Official Web API (требует ключ)
https://api.steampowered.com/
```

**Для арбитража используется**: Community Market API (не требует ключ).

---

## 🔑 Получение API ключа

### Когда нужен API ключ?

API ключ Steam **НЕ НУЖЕН** для получения цен через Market API (`priceoverview`).

API ключ нужен только для:
- Получения информации о профилях пользователей
- Работы с инвентарем через официальное API
- Получения информации о достижениях

### Как получить ключ (на будущее):

1. Перейти на https://steamcommunity.com/dev/apikey
2. Войти в Steam аккаунт
3. Указать домен (можно `localhost` для тестов)
4. Получить ключ формата: `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

⚠️ **ВАЖНО**: Не публикуйте ключ в открытом доступе!

---

## 💰 Market Price Overview API

### Endpoint

```
GET https://steamcommunity.com/market/priceoverview/
```

### Параметры запроса

| Параметр           | Тип     | Обязательный | Описание                                |
| ------------------ | ------- | ------------ | --------------------------------------- |
| `appid`            | integer | ✅ Да         | ID игры (730 = CS:GO/CS2, 570 = Dota 2) |
| `market_hash_name` | string  | ✅ Да         | Название предмета (URL-encoded)         |
| `currency`         | integer | ❌ Нет        | Код валюты (по умолчанию 1 = USD)       |

### Структура ответа (успех)

```json
{
  "success": true,
  "lowest_price": "$1.23",
  "volume": "1,234",
  "median_price": "$1.25"
}
```

### Структура ответа (ошибка)

```json
{
  "success": false
}
```

### Поля ответа

| Поле           | Тип     | Описание                                       |
| -------------- | ------- | ---------------------------------------------- |
| `success`      | boolean | `true` если запрос успешен                     |
| `lowest_price` | string  | Самая низкая цена на рынке (с символом валюты) |
| `volume`       | string  | Количество проданных предметов за 24 часа      |
| `median_price` | string  | Медианная цена (средняя из последних продаж)   |

⚠️ **Важно**:
- Цены возвращаются как строки с символом валюты (`"$1.23"`)
- Volume может содержать запятые (`"1,234"`)
- Нужно очищать от символов перед преобразованием в число

---

## 💱 Коды валют

| Код  | Валюта | Символ |
| ---- | ------ | ------ |
| `1`  | USD    | $      |
| `2`  | GBP    | £      |
| `3`  | EUR    | €      |
| `4`  | CHF    | CHF    |
| `5`  | RUB    | ₽      |
| `6`  | PLN    | zł     |
| `7`  | BRL    | R$     |
| `8`  | JPY    | ¥      |
| `9`  | NOK    | kr     |
| `10` | IDR    | Rp     |
| `11` | MYR    | RM     |
| `12` | PHP    | ₱      |
| `13` | SGD    | S$     |
| `14` | THB    | ฿      |
| `15` | VND    | ₫      |
| `16` | KRW    | ₩      |
| `17` | TRY    | TL     |
| `18` | UAH    | ₴      |
| `19` | MXN    | Mex$   |
| `20` | CAD    | CDN$   |
| `21` | AUD    | A$     |
| `22` | NZD    | NZ$    |
| `23` | CNY    | ¥      |
| `24` | INR    | ₹      |
| `25` | CLP    | CLP$   |
| `26` | PEN    | S/.    |
| `27` | COP    | COL$   |
| `28` | ZAR    | R      |
| `29` | HKD    | HK$    |
| `30` | TWD    | NT$    |
| `31` | SAR    | SR     |
| `32` | AED    | AED    |
| `33` | SEK    | kr     |
| `34` | ARS    | ARS$   |
| `35` | ILS    | ₪      |
| `36` | BYN    | Br     |
| `37` | KZT    | ₸      |
| `38` | KWD    | KD     |
| `39` | QAR    | QR     |
| `40` | CRC    | ₡      |
| `41` | UYU    | $U     |

**Для арбитража рекомендуется**: `1` (USD) - стандартная валюта DMarket.

---

## 🎮 App ID игр

### Основные игры для арбитража

| Игра                                 | App ID   | Рынок                  |
| ------------------------------------ | -------- | ---------------------- |
| **Counter-Strike 2**                 | `730`    | ✅ Активный             |
| **Counter-Strike: Global Offensive** | `730`    | ✅ Активный (тот же ID) |
| **Dota 2**                           | `570`    | ✅ Активный             |
| **Team Fortress 2**                  | `440`    | ✅ Активный             |
| **Rust**                             | `252490` | ✅ Активный             |
| **PUBG**                             | `578080` | ⚠️ Низкая ликвидность   |
| **Z1 Battle Royale**                 | `433850` | ❌ Мертвый рынок        |

### Как найти App ID любой игры

1. Перейти на страницу игры в Steam Store
2. Посмотреть URL: `https://store.steampowered.com/app/730/`
3. Число после `/app/` — это App ID (730)

---

## ⚠️ Ограничения и лимиты

### Rate Limits (неофициальные)

Steam не публикует официальные лимиты, но по опыту сообщества:

| Параметр               | Значение     |
| ---------------------- | ------------ |
| **Запросов в минуту**  | ~30-50       |
| **Запросов в час**     | ~200-300     |
| **Бан при превышении** | 15-60 минут  |
| **Тип бана**           | По IP-адресу |

⚠️ **Критично**:
- Всегда делайте паузу **минимум 2 секунды** между запросами
- Используйте кэширование (6-12 часов для цен)
- При получении 429 ошибки — остановите запросы на 5+ минут

### Другие ограничения

- **URL encoding**: Все пробелы и спецсимволы в `market_hash_name` должны быть закодированы
- **Case sensitive**: Название предмета чувствительно к регистру
- **Timeout**: Запросы могут занимать 1-5 секунд
- **No bulk requests**: Нет endpoint для получения множества цен одним запросом

---

## 🚨 Коды ошибок

### HTTP статус коды

| Код   | Название              | Значение                | Действие               |
| ----- | --------------------- | ----------------------- | ---------------------- |
| `200` | OK                    | Запрос успешен          | Парсить JSON           |
| `400` | Bad Request           | Неверные параметры      | Проверить URL encoding |
| `429` | Too Many Requests     | Превышен лимит запросов | **ПАУЗА 5+ минут**     |
| `500` | Internal Server Error | Ошибка на стороне Steam | Повторить через 10 сек |
| `502` | Bad Gateway           | Steam перегружен        | Повторить через 30 сек |
| `503` | Service Unavailable   | Сервис недоступен       | Повторить через 1 мин  |
| `504` | Gateway Timeout       | Таймаут                 | Повторить через 10 сек |

### Коды ответа в JSON

```json
{
  "success": false
}
```

**Причины `success: false`**:
- Предмет не найден на рынке
- Неверное название предмета
- Предмет снят с продажи
- Неверный App ID

---

## 💡 Примеры использования

### Пример 1: Базовый запрос (Python)

```python
import requests
from urllib.parse import quote

item_name = "AK-47 | Slate (Field-Tested)"
app_id = 730  # CS:GO/CS2
currency = 1  # USD

# URL-encode названия
encoded_name = quote(item_name)

url = f"https://steamcommunity.com/market/priceoverview/"
params = {
    'appid': app_id,
    'currency': currency,
    'market_hash_name': item_name  # requests автоматически кодирует
}

response = requests.get(url, params=params, timeout=10)

if response.status_code == 200:
    data = response.json()
    if data.get('success'):
        print(f"Цена: {data['lowest_price']}")
        print(f"Объем: {data['volume']}")
    else:
        print("Предмет не найден")
else:
    print(f"Ошибка: {response.status_code}")
```

### Пример 2: Асинхронный запрос (Python)

```python
import httpx
import asyncio

async def get_price(item_name: str, app_id: int = 730):
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        'appid': app_id,
        'currency': 1,
        'market_hash_name': item_name
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Очистка от символов
                    price = float(data['lowest_price'].replace('$', '').replace(',', ''))
                    volume = int(data['volume'].replace(',', ''))
                    return {'price': price, 'volume': volume}

            return None

        except Exception as e:
            print(f"Error: {e}")
            return None

# Использование
result = await get_price("AK-47 | Slate (Field-Tested)")
print(result)  # {'price': 2.15, 'volume': 145}
```

### Пример 3: С обработкой Rate Limit

```python
import httpx
import asyncio
from datetime import datetime, timedelta

backoff_until = None

async def get_price_safe(item_name: str):
    global backoff_until

    # Проверка backoff
    if backoff_until and datetime.now() < backoff_until:
        print("Ждем окончания backoff...")
        return None

    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        'appid': 730,
        'currency': 1,
        'market_hash_name': item_name
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=10)

        if response.status_code == 429:
            # Rate limit hit!
            backoff_until = datetime.now() + timedelta(minutes=5)
            print("⚠️ Rate Limit! Пауза на 5 минут.")
            return None

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return {
                    'price': float(data['lowest_price'].replace('$', '').replace(',', '')),
                    'volume': int(data['volume'].replace(',', ''))
                }

    return None
```

### Пример 4: Batch processing с паузами

```python
async def get_prices_batch(items: list[str]):
    results = {}

    for item in items:
        result = await get_price_safe(item)
        if result:
            results[item] = result

        # КРИТИЧНО: пауза между запросами
        await asyncio.sleep(2)

    return results

# Использование
items = [
    "AK-47 | Slate (Field-Tested)",
    "AWP | Asiimov (Battle-Scarred)",
    "M4A4 | Howl (Factory New)"
]

prices = await get_prices_batch(items)
```

### Пример 5: Полный URL

```
https://steamcommunity.com/market/priceoverview/?appid=730&currency=1&market_hash_name=AK-47%20%7C%20Slate%20%28Field-Tested%29
```

**Разбор**:
- `appid=730` - CS:GO/CS2
- `currency=1` - USD
- `market_hash_name=AK-47%20%7C%20Slate%20%28Field-Tested%29` - название (URL-encoded)

---

## 🎯 Best Practices

### 1. Всегда используйте кэширование

```python
# ❌ Плохо - запрос при каждом обращении
for item in items:
    price = await get_steam_price(item.name)

# ✅ Хорошо - проверка кэша
for item in items:
    cached = db.get_steam_price(item.name)
    if cached and is_fresh(cached, hours=6):
        price = cached
    else:
        price = await get_steam_price(item.name)
        db.save_steam_price(item.name, price)
```

### 2. Используйте экспоненциальный backoff

```python
async def get_with_retry(item_name: str, max_retries: int = 3):
    for attempt in range(max_retries):
        result = await get_steam_price(item_name)

        if result:
            return result

        # Экспоненциальная задержка: 2, 4, 8 секунд
        wait_time = 2 ** attempt
        await asyncio.sleep(wait_time)

    return None
```

### 3. Логируйте все запросы

```python
import logging

logger = logging.getLogger(__name__)

async def get_steam_price(item_name: str):
    logger.info(f"Requesting price for: {item_name}")

    try:
        # ... запрос
        logger.info(f"Success: {item_name} = ${price}")
        return price
    except Exception as e:
        logger.error(f"Error for {item_name}: {e}")
        return None
```

### 4. Нормализуйте названия предметов

```python
def normalize_item_name(name: str) -> str:
    """
    Приводит название к формату Steam Market.

    DMarket может использовать:
    - "AK-47 | Slate (Field Tested)"  # Без дефиса

    Steam требует:
    - "AK-47 | Slate (Field-Tested)"  # С дефисом
    """
    # Замены для качества
    replacements = {
        "Factory New": "Factory New",
        "Minimal Wear": "Minimal Wear",
        "Field Tested": "Field-Tested",  # Важно!
        "Well Worn": "Well-Worn",
        "Battle Scarred": "Battle-Scarred"
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    return name
```

### 5. Проверяйте формат перед парсингом

```python
def parse_price(price_str: str) -> float:
    """Безопасно парсит цену из строки."""
    try:
        # Убираем все кроме цифр и точки
        cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
        return float(cleaned)
    except ValueError:
        return 0.0

# Использование
price = parse_price(data['lowest_price'])  # "$1,234.56" → 1234.56
```

### 6. Используйте Connection Pooling

```python
import httpx

# Создаем клиент один раз
client = httpx.AsyncClient(
    timeout=10.0,
    limits=httpx.Limits(max_connections=10)
)

async def get_price(item_name: str):
    # Используем глобальный клиент
    response = await client.get(url, params=params)
    return response.json()

# Закрываем при завершении
await client.aclose()
```

### 7. Мониторьте Rate Limits

```python
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int = 30, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = timedelta(seconds=time_window)
        self.requests = deque()

    async def wait_if_needed(self):
        now = datetime.now()

        # Удаляем старые запросы
        while self.requests and now - self.requests[0] > self.time_window:
            self.requests.popleft()

        # Если лимит достигнут - ждем
        if len(self.requests) >= self.max_requests:
            wait_time = (self.requests[0] + self.time_window - now).total_seconds()
            print(f"Rate limit reached, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time + 1)

        # Регистрируем новый запрос
        self.requests.append(now)

# Использование
limiter = RateLimiter(max_requests=25, time_window=60)

async def get_price_with_limit(item_name: str):
    await limiter.wait_if_needed()
    return await get_steam_price(item_name)
```

---

## 🔗 Полезные ссылки

### Официальная документация
- **Steam Web API**: https://steamcommunity.com/dev
- **Steam API Terms**: https://steamcommunity.com/dev/apiterms

### Неофициальные ресурсы
- **Steam API Documentation (GitHub)**: https://github.com/DoctorMcKay/steam-api-docs
- **Steam Market API examples**: https://github.com/nombersDev/steam-market-api-examples

### Альтернативные источники цен
- **SteamApis**: https://steamapis.com/ (агрегатор цен)
- **PriceEmpire**: https://pricempire.com/api (кросс-платформенный)
- **CSGOFloat**: https://csgofloat.com/api (специфично для CS:GO)

---

## 📊 Сравнение методов получения цен

| Метод                   | Rate Limit | Требует ключ | Bulk запросы | Надежность |
| ----------------------- | ---------- | ------------ | ------------ | ---------- |
| **Steam Community API** | ~30/мин    | ❌ Нет        | ❌ Нет        | ⭐⭐⭐        |
| **SteamApis**           | 100/мин    | ✅ Да         | ✅ Да         | ⭐⭐⭐⭐       |
| **PriceEmpire**         | 60/мин     | ✅ Да         | ✅ Да         | ⭐⭐⭐⭐⭐      |
| **CSGOFloat**           | 30/мин     | ✅ Да         | ✅ Да         | ⭐⭐⭐⭐       |

**Рекомендация**: Начните с Steam Community API (бесплатно), затем при необходимости переходите на SteamApis или PriceEmpire.

---

## ⚡ Quick Reference

### Минимальный рабочий пример

```python
import httpx
import asyncio

async def get_item_price(item_name: str) -> dict:
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        'appid': 730,
        'currency': 1,
        'market_hash_name': item_name
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return {
                    'price': float(data['lowest_price'].replace('$', '').replace(',', '')),
                    'volume': int(data['volume'].replace(',', ''))
                }

    return None

# Запуск
price_data = await get_item_price("AK-47 | Slate (Field-Tested)")
print(price_data)
```

### Шпаргалка по параметрам

```python
# CS:GO/CS2
appid = 730

# Dota 2
appid = 570

# TF2
appid = 440

# Rust
appid = 252490

# USD
currency = 1

# Пауза между запросами
await asyncio.sleep(2)

# Timeout
timeout = 10  # секунд
```

---

## 🎓 Типичные ошибки и решения

### Ошибка 1: `KeyError: 'lowest_price'`

**Причина**: Предмет не найден или `success: false`

**Решение**:
```python
if data.get('success'):
    price = data.get('lowest_price', '$0')
else:
    print("Предмет не найден")
```

### Ошибка 2: `ValueError: could not convert string to float`

**Причина**: Не очищена строка цены от символов

**Решение**:
```python
price_str = data['lowest_price']  # "$1,234.56"
price = float(price_str.replace('$', '').replace(',', ''))
```

### Ошибка 3: Постоянно 429 ошибка

**Причина**: Слишком много запросов

**Решение**:
```python
# Увеличьте паузу
await asyncio.sleep(3)  # Было 1-2 секунды

# Используйте кэш
if cached and age < 6_hours:
    return cached
```

### Ошибка 4: Timeout при запросах

**Причина**: Медленный интернет или перегрузка Steam

**Решение**:
```python
# Увеличьте timeout
async with httpx.AsyncClient(timeout=30.0) as client:
    ...

# Добавьте retry
for attempt in range(3):
    try:
        response = await client.get(url, timeout=30)
        break
    except httpx.TimeoutException:
        if attempt == 2:
            raise
        await asyncio.sleep(5)
```

---

**Документация готова к использованию!** 🚀

Используйте эту страницу как справочник при работе с Steam API для вашего арбитражного бота.
