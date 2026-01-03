# 🔧 ВАЖНО: Изменение архитектуры доступа к зависимостям

## ⚠️ Критическое изменение

**Проблема:** `TypeError: cannot pickle 'module' object` при завершении бота
**Причина:** Persistence пытался сериализовать несериализуемые объекты из `bot_data`

---

## ✅ Решение

Все несериализуемые объекты теперь хранятся как **атрибуты application**, а не в `bot_data`.

---

## 🔄 Миграция для разработчиков

### ❌ СТАРЫЙ способ (вызывает ошибку pickle):

```python
async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ❌ НЕПРАВИЛЬНО - bot_data больше не содержит эти объекты
    dmarket_api = context.bot_data.get("dmarket_api")
    database = context.bot_data.get("database")
    scanner = context.bot_data.get("scanner_manager")
```

### ✅ НОВЫЙ способ (работает):

```python
async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ✅ ПРАВИЛЬНО - используем application атрибуты
    dmarket_api = context.application.dmarket_api
    database = context.application.database
    scanner = context.application.scanner_manager

    # Или с fallback:
    dmarket_api = getattr(context.application, "dmarket_api", None)
```

---

## 📋 Полный список изменений

| Объект            | Старое местоположение                 | Новое местоположение                        |
| ----------------- | ------------------------------------- | ------------------------------------------- |
| DMarket API       | `bot_data["dmarket_api"]`             | `application.dmarket_api`                   |
| Database          | `bot_data["database"]`                | `application.database` или `application.db` |
| State Manager     | `bot_data["state_manager"]`           | `application.state_manager`                 |
| Bot Instance      | `bot_data["bot_instance"]`            | `application.bot_instance`                  |
| Scanner Manager   | `bot_data["scanner_manager"]`         | `application.scanner_manager`               |
| Steam Arbitrage   | `bot_data["steam_arbitrage_scanner"]` | `application.steam_arbitrage_scanner`       |
| Auto Buyer        | `bot_data["auto_buyer"]`              | `application.auto_buyer`                    |
| Auto Seller       | `bot_data["auto_seller"]`             | `application.auto_seller`                   |
| Orchestrator      | `bot_data["orchestrator"]`            | `application.orchestrator`                  |
| WebSocket Manager | `bot_data["websocket_manager"]`       | `application.websocket_manager`             |
| Daily Report      | `bot_data["daily_report_scheduler"]`  | `application.daily_report_scheduler`        |
| Health Monitor    | `bot_data["health_check_monitor"]`    | `application.health_check_monitor`          |

### ⚠️ Исключение: Config остается в bot_data

```python
# Config МОЖНО хранить в bot_data (он сериализуемый)
config = context.bot_data.get("config")
```

---

## 🛠 Примеры обновления handlers

### Пример 1: Простой handler

```python
# ❌ БЫЛО:
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data.get("dmarket_api")
    balance = await api.get_balance()

# ✅ СТАЛО:
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.application.dmarket_api
    balance = await api.get_balance()
```

### Пример 2: Handler с проверкой

```python
# ✅ Безопасный способ с проверкой
async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scanner = getattr(context.application, "scanner_manager", None)
    if not scanner:
        await update.message.reply_text("Scanner not initialized")
        return

    results = await scanner.scan("csgo")
```

### Пример 3: Callback handler

```python
# ✅ В callback handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # Доступ через application
    db = context.application.database
    api = context.application.dmarket_api

    # Обработка callback
    await query.answer()
```

---

## 🔍 Как найти места для обновления

### Поиск в коде:

```bash
# Найти все использования bot_data для доступа к объектам
grep -r "bot_data\[\"dmarket_api\"\]" src/
grep -r "bot_data.get(\"database\")" src/
grep -r "bot_data\[\"scanner_manager\"\]" src/
```

### Автоматическая замена (bash):

```bash
# Заменить во всех handlers
find src/telegram_bot/handlers -name "*.py" -exec sed -i \
    's/context\.bot_data\.get("dmarket_api")/context.application.dmarket_api/g' {} +
```

---

## ✅ Преимущества нового подхода

1. **Нет ошибок pickle** - при завершении бота
2. **Более чистая архитектура** - атрибуты application для несериализуемых объектов
3. **Проще отладка** - прямой доступ через атрибуты
4. **Лучшая производительность** - нет лишней сериализации

---

## 🎯 TODO для разработчиков

- [ ] Обновить все handlers в `src/telegram_bot/handlers/`
- [ ] Обновить все commands в `src/telegram_bot/commands/`
- [ ] Проверить callbacks в `src/telegram_bot/callbacks.py`
- [ ] Запустить тесты: `pytest tests/`
- [ ] Проверить бота: `python -m src.main`

---

**Дата изменения:** 03.01.2026
**Версия:** 2.0 (Pickle-safe architecture)
