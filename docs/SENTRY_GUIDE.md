# 🔍 Sentry Integration Guide

**Дата**: 12 декабря 2025 г.
**Версия**: 2.0

---

## 📋 Содержание

1. [Обзор](#обзор)
2. [Быстрый старт](#быстрый-старт)
3. [Тестирование интеграции](#тестирование-интеграции)
4. [Настройка алертов](#настройка-алертов)
5. [Очистка тестовых данных](#очистка-тестовых-данных)
6. [Best Practices](#best-practices)

---

## 🎯 Обзор

Sentry — система мониторинга ошибок и производительности для production. Бот интегрирован с Sentry для:

- ✅ Автоматического захвата всех ошибок
- ✅ Отслеживания контекста действий пользователя (breadcrumbs)
- ✅ Мониторинга производительности API запросов
- ✅ Алертов о критических событиях

### Что такое Breadcrumbs?

**Breadcrumbs** — "хлебные крошки" событий перед ошибкой:

```
[10:30:15] telegram: Bot command: /arbitrage (user_id: 123456789)
[10:30:16] trading: Trading action: arbitrage_scan_started (game: csgo)
[10:30:17] http: API request: GET /marketplace-api/v1/items (200, 450ms)
[10:30:18] error: RateLimitError - Too many requests
```

---

## 🚀 Быстрый старт

### Шаг 1: Создание проекта в Sentry

1. Зарегистрируйтесь на [sentry.io](https://sentry.io)
2. Создайте проект → выберите **Python**
3. Скопируйте **DSN**

### Шаг 2: Настройка .env

```env
# Sentry мониторинг
SENTRY_DSN=https://your-key@o12345.ingest.sentry.io/67890
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% для production
```

### Шаг 3: Проверка

Запустите бота и выполните:

```
/sentry_info
```

Должно показать: `✅ Sentry инициализирован`

---

## 🧪 Тестирование интеграции

### Тестовые команды

| Команда                    | Описание           |
| -------------------------- | ------------------ |
| `/sentry_info`             | Статус интеграции  |
| `/test_sentry all`         | Все тесты          |
| `/test_sentry breadcrumbs` | Только breadcrumbs |
| `/test_sentry error`       | Простая ошибка     |
| `/test_sentry api_error`   | Ошибка rate limit  |

### Проверка в Sentry Dashboard

1. Откройте [sentry.io](https://sentry.io) → Issues
2. Найдите тестовые ошибки:
   - `ValueError: Test error...`
   - `RuntimeError: API Rate Limit...`
   - `ZeroDivisionError`
3. Проверьте **Breadcrumbs** секцию в каждой ошибке

### Ожидаемые breadcrumbs

```
[timestamp] telegram - Bot command: /arbitrage
[timestamp] trading - arbitrage_scan_started (game: csgo, level: standard)
[timestamp] http - GET /marketplace-api/v1/items (200, 450ms)
[timestamp] trading - arbitrage_scan_completed (opportunities: 15)
```

---

## 🔔 Настройка алертов

### Рекомендуемые алерты

#### Уровень 1 (Критический) - Telegram + Email мгновенно

| Алерт            | Условие                              |
| ---------------- | ------------------------------------ |
| 🚨 Bot Crashed    | `level=critical`                     |
| 💰 Trading Failed | `component=trading, level=error`     |
| 🔑 Auth Failed    | `exception=AuthenticationError`      |
| 🗄️ Database Down  | `component=database, level=critical` |

#### Уровень 2 (Важный) - Email каждые 30 мин

| Алерт              | Условие                             |
| ------------------ | ----------------------------------- |
| ⚠️ Rate Limit       | `exception=RateLimitError, >5/hour` |
| 📉 API Errors Spike | `component=api, >10 errors/hour`    |

### Создание алерта

1. Sentry → **Alerts** → **Create Alert**
2. Выберите **Issues**
3. Настройте условия:

   ```
   level = error OR fatal
   tags.severity = critical
   environment = production
   ```

4. Действие: Email / Telegram / Slack

### Telegram интеграция через Webhook

```python
# В боте создайте endpoint /sentry-webhook
@app.post("/sentry-webhook")
async def sentry_webhook(request: Request):
    data = await request.json()
    issue = data.get("data", {}).get("issue", {})

    message = f"""
🚨 <b>Sentry Alert</b>
<b>Issue:</b> {issue.get("title")}
<a href="{issue.get("web_url")}">View in Sentry →</a>
"""
    await bot.send_message(ADMIN_CHAT_ID, message, parse_mode="HTML")
```

---

## 🧹 Очистка тестовых данных

### Зачем нужна очистка?

- 📊 Тестовые issues искажают статистику
- 🔔 Могут вызывать ложные алерты
- 💰 Расходуют квоту событий

### Автоматический скрипт

```bash
# Предпросмотр (без изменений)
python scripts/sentry_cleanup.py --test-only

# Пометить как resolved
python scripts/sentry_cleanup.py --test-only --execute

# Удалить полностью
python scripts/sentry_cleanup.py --test-only --delete --execute

# Удалить старые (>30 дней)
python scripts/sentry_cleanup.py --old 30 --delete --execute
```

### Ручная очистка через Web UI

1. Sentry → Issues
2. Поиск: `Test Error OR Test Critical`
3. Выбрать все → **Resolve** или **Delete**

### Что НЕ удалять

❌ Issues из production
❌ Нерешенные реальные баги
❌ Issues с активными обсуждениями

---

## 🎯 Best Practices

### 1. Sample Rate

```env
# Development - 100%
SENTRY_TRACES_SAMPLE_RATE=1.0

# Production - 10%
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 2. Правильные уровни severity

```python
# CRITICAL - бот упал, деньги потеряны
logger.critical("Trading failed: lost $1000")

# ERROR - функциональность нарушена
logger.error("Failed to fetch market data", exc_info=True)

# WARNING - потенциальная проблема
logger.warning("Rate limit approached: 90%")
```

### 3. Добавляйте контекст

```python
# ❌ Плохо
raise ValueError("Invalid price")

# ✅ Хорошо
raise ValueError(f"Invalid price for {item_id}: {price}, min={min_price}")
```

### 4. Breadcrumbs для важных действий

```python
from src.utils.sentry_breadcrumbs import add_trading_breadcrumb

add_trading_breadcrumb(
    action="buying_item",
    game="csgo",
    user_id=user_id,
    item_title="AK-47 | Redline",
    price_usd=10.50
)
```

### 5. Регулярное обслуживание

**Еженедельно:**

```bash
python scripts/sentry_cleanup.py --test-only --execute
```

**Ежемесячно:**

```bash
python scripts/sentry_cleanup.py --old 30 --delete --execute
```

---

## ✅ Production Checklist

- [ ] `SENTRY_DSN` установлен
- [ ] `SENTRY_ENVIRONMENT=production`
- [ ] `SENTRY_TRACES_SAMPLE_RATE≤0.1`
- [ ] `/sentry_info` показывает ✅
- [ ] `/test_sentry all` работает
- [ ] Issues появляются в dashboard
- [ ] Breadcrumbs отображаются
- [ ] Алерты настроены
- [ ] Тестовые issues очищены

---

## 🐛 Troubleshooting

### Sentry не инициализирован

```bash
# Проверить DSN
cat .env | grep SENTRY_DSN
# Должен быть формат: https://KEY@oXXXXX.ingest.sentry.io/XXXXX
```

### Breadcrumbs не появляются

```bash
# Проверить версию
pip show sentry-sdk  # >= 1.40.0

# Запустить тест
/test_sentry all
```

### Ошибки не отправляются

```python
# Включить debug
sentry_sdk.init(dsn="...", debug=True)
```

---

## 📚 Ресурсы

- [Sentry Python Documentation](https://docs.sentry.io/platforms/python/)
- [Breadcrumbs Guide](https://docs.sentry.io/platforms/python/enriching-events/breadcrumbs/)
- [Alerts Best Practices](https://docs.sentry.io/product/alerts/best-practices/)

---

**Документ консолидирован из:**

- SENTRY_ALERTS_SETUP.md
- SENTRY_CLEANUP.md
- SENTRY_TESTING_GUIDE.md
- SENTRY_PRODUCTION_QUICKSTART.md
