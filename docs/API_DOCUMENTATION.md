# 📚 API Документация

## Обзор

DMarket Telegram Bot предоставляет REST API для интеграции с внешними сервисами.

**OpenAPI спецификация**: [`openapi.yaml`](./openapi.yaml)

## 🚀 Быстрый старт

### Просмотр документации

#### Swagger UI (рекомендуется)

```bash
# Установить swagger-ui-express
npm install -g swagger-ui-watcher

# Запустить просмотр
swagger-ui-watcher docs/openapi.yaml
```

Откроется по адресу: http://localhost:8000

#### Redoc

```bash
# Установить redoc-cli
npm install -g redoc-cli

# Сгенерировать HTML
redoc-cli bundle docs/openapi.yaml -o docs/api.html

# Открыть в браузере
start docs/api.html
```

#### Online просмотр

1. Зайти на https://editor.swagger.io/
2. File → Import File → выбрать `docs/openapi.yaml`

### Валидация спецификации

```bash
# Установить @apidevtools/swagger-cli
npm install -g @apidevtools/swagger-cli

# Валидировать
swagger-cli validate docs/openapi.yaml
```

## 🔐 Аутентификация

API использует JWT Bearer tokens для аутентификации.

### Получение токена

```bash
POST /auth/login
Content-Type: application/json

{
  "user_id": 123456789,
  "api_key": "your-api-key"
}
```

### Использование токена

```bash
GET /users/123456789
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📡 Основные эндпоинты

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-14T10:00:00Z",
  "version": "1.0.0"
}
```

### Сканирование арбитража

```bash
POST /arbitrage/scan
Content-Type: application/json
Authorization: Bearer <token>

{
  "level": "standard",
  "game": "csgo",
  "min_profit": 1.0
}
```

**Response:**
```json
{
  "opportunities": [
    {
      "item_id": "abc123",
      "item_name": "AK-47 | Redline (FT)",
      "buy_price": 10.50,
      "sell_price": 12.00,
      "profit": 0.86,
      "profit_percent": 8.19,
      "game": "csgo"
    }
  ],
  "total": 15,
  "scan_time": 2.5
}
```

### Создание таргета

```bash
POST /targets
Content-Type: application/json
Authorization: Bearer <token>

{
  "user_id": 123456789,
  "game": "csgo",
  "item_name": "AK-47 | Redline (FT)",
  "price": 10.50,
  "quantity": 1
}
```

**Response:**
```json
{
  "target_id": "target_xyz789",
  "user_id": 123456789,
  "game": "csgo",
  "item_name": "AK-47 | Redline (FT)",
  "price": 10.50,
  "quantity": 1,
  "status": "active",
  "created_at": "2025-12-14T10:00:00Z"
}
```

## ⚠️ Rate Limiting

API имеет следующие лимиты:

| Эндпоинт | Лимит |
|----------|-------|
| `/arbitrage/scan` | 10 запросов/минуту |
| `/targets` (POST) | 5 запросов/минуту |
| `/market/*` | 20 запросов/минуту |
| Остальные | 30 запросов/минуту |

При превышении лимита возвращается статус `429 Too Many Requests` с заголовком `Retry-After`.

## 🔄 Pagination

Эндпоинты со списками поддерживают cursor-based пагинацию:

```bash
GET /market/items?game=csgo&limit=100&cursor=abc123
```

**Response:**
```json
{
  "items": [...],
  "total": 500,
  "cursor": "xyz789"
}
```

Для получения следующей страницы используйте значение `cursor` из предыдущего ответа.

## 📊 Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Bad Request - невалидные параметры |
| 401 | Unauthorized - отсутствует или невалидный токен |
| 403 | Forbidden - недостаточно прав |
| 404 | Not Found - ресурс не найден |
| 429 | Too Many Requests - превышен rate limit |
| 500 | Internal Server Error - ошибка сервера |

### Формат ошибки

```json
{
  "error": "validation_error",
  "message": "Invalid price value",
  "code": 400
}
```

## 🧪 Тестирование

### Curl примеры

```bash
# Health check
curl -X GET http://localhost:8000/v1/health

# Сканирование арбитража
curl -X POST http://localhost:8000/v1/arbitrage/scan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "standard",
    "game": "csgo",
    "min_profit": 1.0
  }'

# Получить пользователя
curl -X GET http://localhost:8000/v1/users/123456789 \
  -H "Authorization: Bearer <token>"
```

### Postman коллекция

Импортируйте OpenAPI спецификацию в Postman:

1. File → Import → выбрать `docs/openapi.yaml`
2. Postman автоматически создаст коллекцию с запросами

### Python примеры

```python
import requests

API_URL = "http://localhost:8000/v1"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Сканирование арбитража
response = requests.post(
    f"{API_URL}/arbitrage/scan",
    headers=headers,
    json={
        "level": "standard",
        "game": "csgo",
        "min_profit": 1.0
    }
)

opportunities = response.json()["opportunities"]
print(f"Found {len(opportunities)} opportunities")
```

## 🔧 Разработка

### Обновление спецификации

1. Отредактировать `docs/openapi.yaml`
2. Валидировать изменения:
   ```bash
   swagger-cli validate docs/openapi.yaml
   ```
3. Сгенерировать документацию:
   ```bash
   redoc-cli bundle docs/openapi.yaml -o docs/api.html
   ```

### Генерация клиентов

Используйте OpenAPI Generator для генерации клиентов:

```bash
# Установить openapi-generator-cli
npm install -g @openapitools/openapi-generator-cli

# Python клиент
openapi-generator-cli generate \
  -i docs/openapi.yaml \
  -g python \
  -o clients/python

# TypeScript клиент
openapi-generator-cli generate \
  -i docs/openapi.yaml \
  -g typescript-axios \
  -o clients/typescript
```

## 📚 Дополнительные ресурсы

- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger Editor](https://editor.swagger.io/)
- [Redoc](https://github.com/Redocly/redoc)
- [OpenAPI Generator](https://openapi-generator.tech/)

## 🤝 Поддержка

При вопросах по API создавайте issue в GitHub репозитории.
