# AnyTool Integration Guide

## 📋 Обзор

AnyTool - это интеграция DMarket Telegram Bot с Model Context Protocol (MCP), позволяющая AI инструментам напрямую взаимодействовать с DMarket API через стандартизированный протокол.

## 🎯 Возможности

- **6 MCP инструментов** для работы с DMarket
- **Асинхронное выполнение** всех операций
- **Callback система** для отслеживания событий
- **Автоматическая валидация** параметров через Pydantic
- **Структурированное логирование** всех операций

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install mcp>=1.0.0
```

### 2. Конфигурация

Создайте файл `anytool/config/config_mcp.json`:

```json
{
  "mcpServers": {
    "dmarket-bot": {
      "command": "python",
      "args": ["-m", "src.mcp_server.dmarket_mcp"],
      "env": {
        "DMARKET_PUBLIC_KEY": "${DMARKET_PUBLIC_KEY}",
        "DMARKET_SECRET_KEY": "${DMARKET_SECRET_KEY}"
      }
    }
  }
}
```

### 3. Использование в коде

```python
from src.utils.anytool_integration import initialize_anytool

# Инициализация
client = await initialize_anytool()

# Вызов инструмента
result = await client.call_tool("get_balance", {})
print(result)  # {"success": True, "balance": {"usd": "10000"}}
```

## 🛠️ Доступные инструменты

### 1. get_balance

Получить баланс пользователя на DMarket.

**Параметры**: нет

**Пример**:
```python
result = await client.call_tool("get_balance", {})
# {"success": True, "balance": {"usd": "10000", "dmc": "5000"}}
```

### 2. get_market_items

Получить список предметов на рынке.

**Параметры**:
- `game` (str, required): Игра (csgo, dota2, rust, tf2)
- `limit` (int, optional): Количество предметов (по умолчанию 10, макс 100)
- `price_from` (int, optional): Минимальная цена в центах USD
- `price_to` (int, optional): Максимальная цена в центах USD

**Пример**:
```python
result = await client.call_tool("get_market_items", {
    "game": "csgo",
    "limit": 20,
    "price_from": 500,  # $5.00
    "price_to": 2000    # $20.00
})
```

### 3. scan_arbitrage

Сканировать арбитражные возможности.

**Параметры**:
- `game` (str, required): Игра для сканирования
- `level` (str, optional): Уровень арбитража (boost, standard, medium, advanced, pro)
- `min_profit` (float, optional): Минимальная прибыль в USD (по умолчанию 0.5)

**Пример**:
```python
result = await client.call_tool("scan_arbitrage", {
    "game": "csgo",
    "level": "standard",
    "min_profit": 1.0
})
# {"success": True, "opportunities": [...]}
```

### 4. get_item_details

Получить детальную информацию о предмете.

**Параметры**:
- `item_id` (str, required): ID предмета на DMarket

**Пример**:
```python
result = await client.call_tool("get_item_details", {
    "item_id": "abc123xyz"
})
```

### 5. create_target

Создать таргет (buy order) на предмет.

**Параметры**:
- `game` (str, required): Игра
- `title` (str, required): Название предмета
- `price` (float, required): Цена в USD
- `amount` (int, optional): Количество предметов (по умолчанию 1)

**Пример**:
```python
result = await client.call_tool("create_target", {
    "game": "csgo",
    "title": "AK-47 | Redline (Field-Tested)",
    "price": 10.50,
    "amount": 2
})
```

### 6. get_targets

Получить список активных таргетов.

**Параметры**: нет

**Пример**:
```python
result = await client.call_tool("get_targets", {})
# {"success": True, "count": 3, "targets": [...]}
```

## 🔔 Callback система

Регистрируйте callbacks для отслеживания событий:

```python
# Callback при любом вызове инструмента
def on_tool_called(data):
    print(f"Tool called: {data['tool']}")
    print(f"Result: {data['result']}")

client.register_callback("tool_called", on_tool_called)

# Асинхронный callback
async def on_tool_called_async(data):
    await send_notification(f"Tool {data['tool']} completed")

client.register_callback("tool_called", on_tool_called_async)
```

## 📦 Экспорт конфигурации

```python
# Экспорт в файл
client.export_config("anytool/config/config_mcp.json")
```

## 🔒 Безопасность

### Переменные окружения

**ВСЕГДА** используйте переменные окружения для секретов:

```bash
export DMARKET_PUBLIC_KEY="your_public_key"
export DMARKET_SECRET_KEY="your_secret_key"
```

### Отключение интеграции

```python
config = AnyToolConfig(enabled=False)
client = AnyToolClient(config=config)

# Вызов вызовет ошибку
await client.call_tool("get_balance", {})
# ValueError: AnyTool integration is disabled
```

## 🧪 Тестирование

Запуск тестов:

```bash
pytest tests/unit/test_anytool_integration.py -v
pytest tests/unit/test_mcp_server.py -v
```

Проверка покрытия:

```bash
pytest tests/unit/test_anytool_integration.py --cov=src.utils.anytool_integration
pytest tests/unit/test_mcp_server.py --cov=src.mcp_server
```

## 🚀 Запуск MCP сервера

### Прямой запуск

```bash
python -m src.mcp_server.dmarket_mcp
```

### Через AnyTool

После настройки конфигурации, AnyTool автоматически запустит MCP сервер при необходимости.

## 📊 Мониторинг

Все операции логируются через structlog:

```python
logger.info("anytool_call", tool="get_balance", arguments={})
logger.info("anytool_initialized")
logger.error("anytool_call_failed", tool="scan_arbitrage", error=str(e))
```

Просмотр логов:

```bash
grep "anytool" logs/app.log
```

## 🔧 Расширенная настройка

### Кастомная конфигурация

```python
config = AnyToolConfig(
    mcp_server_path="custom.module:main",
    timeout=60,
    max_retries=5,
    enabled=True
)

client = AnyToolClient(config=config)
```

### Использование с custom API клиентом

```python
from src.dmarket.dmarket_api import DMarketAPI

api_client = DMarketAPI(
    public_key="your_key",
    secret_key="your_secret",
    base_url="https://api.dmarket.com"
)

client = AnyToolClient(api_client=api_client)
```

## ⚠️ Ограничения

- **Rate Limiting**: Соблюдайте лимиты DMarket API (30 запросов/минуту)
- **Timeout**: По умолчанию 30 секунд для каждого запроса
- **Max Results**: `scan_arbitrage` возвращает максимум 20 возможностей

## 📚 Дополнительные ресурсы

- [DMarket API Documentation](https://docs.dmarket.com/)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [Project Architecture](./ARCHITECTURE.md)
- [Security Guide](./SECURITY.md)

## 🤝 Интеграция с n8n

Для автоматизации workflow см. [n8n Integration Guide](./ANYTOOL_N8N_INTEGRATION_GUIDE.md).

## 📝 Changelog

### v1.0.0 (2025-12-20)
- ✅ Первый релиз AnyTool интеграции
- ✅ 6 MCP инструментов
- ✅ Callback система
- ✅ Полное тестовое покрытие
- ✅ Документация

---

**Версия**: 1.0.0  
**Последнее обновление**: 20 декабря 2025 г.
