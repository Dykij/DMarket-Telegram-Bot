```markdown
# DMarket API - Правила для Copilot

> **Официальная документация**: https://docs.dmarket.com/v1/swagger.html
> **Примеры кода**: https://github.com/dmarket/dm-trading-tools
> **FAQ по API**: https://dmarket.com/faq#startUsingTradingAPI

## ⚠️ КРИТИЧНО: Ed25519 Аутентификация (НЕ HMAC!)

DMarket использует **Ed25519/NaCl подпись**, а не HMAC-SHA256!

### Заголовки запроса

```python
headers = {
    "X-Api-Key": public_key,           # Публичный ключ (hex, lowercase)
    "X-Sign-Date": str(timestamp),     # Unix timestamp (не старше 2 минут!)
    "X-Request-Sign": f"dmar ed25519 {signature}"  # Подпись
}
```

### Формула подписи

```python
# Строка для подписи (порядок ВАЖЕН!)
string_to_sign = METHOD + PATH_WITH_QUERY + BODY + TIMESTAMP

# Примеры:
# GET /account/v1/balance → "GET/account/v1/balance1699876543"
# POST /marketplace-api/v1/user-targets/create с body → "POST/marketplace-api/v1/user-targets/create{\"GameID\":\"a8db\"}1699876543"
```

### Корректная реализация подписи (NaCl)

```python
import time
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

def sign_request(
    secret_key: str,  # Приватный ключ (hex string)
    method: str,
    path: str,
    body: str = ""
) -> tuple[str, str]:
    """Создать Ed25519 подпись для DMarket API.

    Returns:
        tuple: (timestamp, signature)
    """
    timestamp = str(int(time.time()))

    # Формируем строку для подписи
    string_to_sign = method.upper() + path + body + timestamp

    # Подписываем с помощью NaCl
    signing_key = SigningKey(secret_key, encoder=HexEncoder)
    signed = signing_key.sign(string_to_sign.encode())
    signature = signed.signature.hex()

    return timestamp, signature
```

## 💰 Форматы цен (ВНИМАНИЕ: разные для разных эндпоинтов!)

### exchange/* эндпоинты → ЦЕНТЫ (coins)

```python
# GET /exchange/v1/market/items
# PATCH /exchange/v1/offers-buy
# Цены в ЦЕНТАХ (целые числа)

price_cents = 1250  # = $12.50
price_usd = price_cents / 100  # Конвертация в доллары

# Пример ответа:
{"price": {"USD": "1250"}}  # Строка! $12.50
```

### marketplace-api/* эндпоинты → USD (decimal)

```python
# POST /marketplace-api/v1/user-offers/create
# POST /marketplace-api/v1/user-targets/create
# Цены в долларах с десятичной частью

price_usd = "12.50"  # Строка! $12.50
price_cents = int(float(price_usd) * 100)  # Конвертация в центы

# Пример запроса:
{"Price": {"Currency": "USD", "Amount": "12.50"}}
```

## 🎮 Коды игр (gameId / GameID)

| Игра            | Код    |
| --------------- | ------ |
| CS:GO / CS2     | `a8db` |
| Dota 2          | `9a92` |
| Team Fortress 2 | `tf2`  |
| Rust            | `rust` |

## 📡 Основные эндпоинты

### Аккаунт

```python
# Профиль пользователя
GET /account/v1/user

# Баланс (ЦЕНТЫ!)
GET /account/v1/balance
# Response: {"usd": "12500", "dmc": "0"}  # $125.00
```

### Маркет

```python
# Список предметов на продаже (ЦЕНТЫ!)
GET /exchange/v1/market/items?gameId=a8db&limit=100&currency=USD

# Предложения по названию
GET /exchange/v1/offers-by-title?Title={title}&Limit=100

# Агрегированные цены
POST /marketplace-api/v1/aggregated-prices
# Body: {"Titles": ["AK-47 | Redline (Field-Tested)"], "Limit": "100"}
```

### Офферы (мои предложения)

```python
# Список моих офферов
GET /marketplace-api/v1/user-offers?GameID=a8db

# Создать оффер (USD decimal!)
POST /marketplace-api/v1/user-offers/create
# Body: {"Offers": [{"AssetID": "abc123", "Price": {"Currency": "USD", "Amount": "12.50"}}]}

# Изменить цену
POST /marketplace-api/v1/user-offers/edit
# Body: {"Offers": [{"OfferID": "offer123", "Price": {"Currency": "USD", "Amount": "15.00"}}]}

# Удалить офферы
DELETE /exchange/v1/offers
# Body: {"force": true, "objects": [{"offerId": "offer123"}]}
```

### Таргеты (Buy Orders)

```python
# Список моих таргетов
GET /marketplace-api/v1/user-targets?GameID=a8db

# Создать таргеты (USD decimal!)
POST /marketplace-api/v1/user-targets/create
# Body: {
#   "GameID": "a8db",
#   "Targets": [{
#     "Title": "AK-47 | Redline (Field-Tested)",
#     "Amount": "1",
#     "Price": {"Currency": "USD", "Amount": "8.50"}
#   }]
# }

# Удалить таргеты
POST /marketplace-api/v1/user-targets/delete
# Body: {"Targets": [{"TargetID": "target123"}]}

# Таргеты по названию предмета
GET /marketplace-api/v1/targets-by-title/{game_id}/{title}
```

### Покупка

```python
# Купить офферы (ЦЕНТЫ!)
PATCH /exchange/v1/offers-buy
# Body: {"offers": [{"offerId": "abc123", "price": {"amount": "1250", "currency": "USD"}}]}
```

### Инвентарь

```python
# Мой инвентарь
GET /marketplace-api/v1/user-inventory?GameID=a8db

# Синхронизировать со Steam
POST /marketplace-api/v1/user-inventory/sync

# Депозит предметов (из Steam)
POST /marketplace-api/v1/deposit-assets

# Вывод предметов (в Steam)
POST /exchange/v1/withdraw-assets
```

### История продаж

```python
# Последние продажи предмета
GET /trade-aggregator/v1/last-sales?gameId=a8db&title={title}&limit=20
```

## ⏱️ Rate Limiting

- **Лимит**: ~30 запросов в минуту
- **При превышении**: HTTP 429 Too Many Requests
- **Рекомендация**: использовать aiolimiter или подобное

```python
from aiolimiter import AsyncLimiter

rate_limiter = AsyncLimiter(max_rate=30, time_period=60)

async def api_call():
    async with rate_limiter:
        # ... выполнить запрос
```

## 🔄 Обработка ошибок

```python
async def safe_api_call(method: str, path: str, **kwargs) -> dict:
    """API вызов с retry логикой."""
    for attempt in range(3):
        try:
            response = await make_request(method, path, **kwargs)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                await asyncio.sleep(retry_after)
                continue

            if response.status_code >= 500:
                await asyncio.sleep(2 ** attempt)
                continue

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            if attempt == 2:
                raise
            await asyncio.sleep(1)

    raise APIError("Max retries exceeded")
```

## 🏗️ Шаблон API клиента

```python
import httpx
import time
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder
from aiolimiter import AsyncLimiter


class DMarketClient:
    """Асинхронный клиент DMarket API с Ed25519 аутентификацией."""

    BASE_URL = "https://api.dmarket.com"

    def __init__(self, public_key: str, secret_key: str):
        self.public_key = public_key
        self.secret_key = secret_key
        self._rate_limiter = AsyncLimiter(max_rate=30, time_period=60)
        self._client = httpx.AsyncClient(timeout=30.0)

    def _sign(self, method: str, path: str, body: str = "") -> dict[str, str]:
        """Создать заголовки с Ed25519 подписью."""
        timestamp = str(int(time.time()))
        string_to_sign = method.upper() + path + body + timestamp

        signing_key = SigningKey(self.secret_key, encoder=HexEncoder)
        signed = signing_key.sign(string_to_sign.encode())
        signature = signed.signature.hex()

        return {
            "X-Api-Key": self.public_key,
            "X-Sign-Date": timestamp,
            "X-Request-Sign": f"dmar ed25519 {signature}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> dict:
        """Выполнить подписанный запрос к API."""
        async with self._rate_limiter:
            # Формируем path с query string для подписи
            if params:
                query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
                full_path = f"{path}?{query}"
            else:
                full_path = path

            body = ""
            if json_body:
                import json
                body = json.dumps(json_body, separators=(",", ":"))

            headers = self._sign(method, full_path, body)

            response = await self._client.request(
                method=method,
                url=f"{self.BASE_URL}{path}",
                params=params,
                content=body if body else None,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    # === Account ===

    async def get_balance(self) -> dict:
        """Получить баланс (в центах)."""
        return await self._request("GET", "/account/v1/balance")

    # === Market ===

    async def get_market_items(
        self,
        game_id: str = "a8db",
        limit: int = 100,
        **filters,
    ) -> dict:
        """Получить предметы с маркета."""
        params = {"gameId": game_id, "limit": limit, "currency": "USD", **filters}
        return await self._request("GET", "/exchange/v1/market/items", params=params)

    # === Targets ===

    async def create_target(
        self,
        game_id: str,
        title: str,
        price_usd: float,
        amount: int = 1,
    ) -> dict:
        """Создать таргет (buy order)."""
        body = {
            "GameID": game_id,
            "Targets": [{
                "Title": title,
                "Amount": str(amount),
                "Price": {"Currency": "USD", "Amount": f"{price_usd:.2f}"},
            }],
        }
        return await self._request("POST", "/marketplace-api/v1/user-targets/create", json_body=body)

    # === Cleanup ===

    async def close(self):
        """Закрыть HTTP клиент."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
```

## 📚 Дополнительные ресурсы

- **Swagger UI**: https://docs.dmarket.com/v1/swagger.html
- **GitHub примеры**: https://github.com/dmarket/dm-trading-tools
- **FAQ**: https://dmarket.com/faq#startUsingTradingAPI
- **Проект docs**: `docs/DMARKET_API_FULL_SPEC.md`
```
