---
description: 'DMarket and Waxpeer API integration guidelines'
applyTo: 'src/dmarket/**/*.py, src/waxpeer/**/*.py'
---

# API Integration Instructions

Apply these rules when working with marketplace API files:

## DMarket API
- **Prices in CENTS**: 1000 = $10.00 USD
- **Commission**: 7% on sales
- **Rate limit**: 30 requests/minute
- **Auth**: HMAC-SHA256 signatures

## Waxpeer API
- **Prices in MILS**: 1000 mils = $1.00 USD
- **Commission**: 6% on sales
- **Auth**: API key in X-API-KEY header

## Price Conversions

```python
# DMarket: cents to dollars
price_usd = api_response["price"]["USD"] / 100

# Waxpeer: mils to dollars
price_usd = api_response["price"] / 1000
```

## Cross-Platform Arbitrage

```python
# DMarket → Waxpeer formula
net_profit = (waxpeer_price * 0.94) - dmarket_price
roi_percent = (net_profit / dmarket_price) * 100
```

## HTTP Client Pattern

```python
async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.get(url, headers=self._get_headers())
    response.raise_for_status()
    return response.json()
```

## Error Handling
- Handle rate limits (429) with exponential backoff
- Use circuit breaker for repeated failures
- Log all API errors with full context
- Never expose API keys in logs or errors
