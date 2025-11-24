# 🔔 Настройка алертов Sentry для критических ошибок

**Дата**: 23 ноября 2025 г.
**Версия**: 1.0

---

## 📋 Обзор

Этот гайд поможет настроить автоматические уведомления о критических ошибках в вашем DMarket Telegram боте через Sentry.

---

## 🎯 Цели алертов

**Немедленное уведомление при:**
- 🚨 Критические ошибки (CRITICAL level)
- 💰 Ошибки при совершении сделок
- 🔑 Проблемы с API аутентификацией
- 📉 Rate limit превышения
- 🗄️ Ошибки базы данных
- 🔄 Неожиданные падения бота

---

## 🚀 Быстрая настройка

### Шаг 1: Открыть настройки алертов

1. Перейдите в ваш проект Sentry: https://sentry.io/organizations/your-org/projects/
2. Выберите проект DMarket Bot
3. Перейдите в **Alerts** → **Create Alert**

### Шаг 2: Выбрать тип алерта

Выберите **Issues**:
- Issues алерты срабатывают при появлении новых ошибок
- Можно настроить условия по уровню severity, тегам, и т.д.

### Шаг 3: Настроить условия (When)

#### Алерт 1: Критические ошибки

**Название**: `🚨 Critical Errors`

**Условия:**
```
When an event is captured by Sentry and matches ALL of the following:
  - level = error OR fatal
  - tags.severity = critical
```

**Дополнительные фильтры (опционально):**
```
AND environment = production
```

#### Алерт 2: Ошибки торговли

**Название**: `💰 Trading Errors`

**Условия:**
```
When an event is captured by Sentry and matches ALL of the following:
  - tags.component = trading
  - level = error OR fatal
```

#### Алерт 3: API Authentication Failed

**Название**: `🔑 API Auth Failed`

**Условия:**
```
When an event is captured by Sentry and matches ALL of the following:
  - exception.type = AuthenticationError
  - environment = production
```

#### Алерт 4: Rate Limit Exceeded

**Название**: `⚠️ Rate Limit Exceeded`

**Условия:**
```
When an event is captured by Sentry and matches ALL of the following:
  - exception.type = RateLimitError
  - The issue is seen more than 5 times in 1 hour
```

#### Алерт 5: Database Errors

**Название**: `🗄️ Database Connection Issues`

**Условия:**
```
When an event is captured by Sentry and matches ALL of the following:
  - tags.component = database
  - level = error OR fatal
```

#### Алерт 6: Bot Crashed

**Название**: `🔄 Bot Stopped Unexpectedly`

**Условия:**
```
When an event is captured by Sentry and matches ALL of the following:
  - message = "Bot stopped unexpectedly"
  - level = critical
```

### Шаг 4: Настроить действия (Then)

Для каждого алерта настройте:

**Кому отправлять:**
- ✅ **Email** - ваш email адрес
- ✅ **Telegram** - через Sentry Telegram integration
- ✅ **Slack** - если используете Slack (опционально)

**Частота уведомлений:**
- `Send at most one notification per issue in 30 minutes`
- Для критических: `Send at most one notification per issue in 5 minutes`

---

## 🔧 Интеграция с Telegram

### Настройка Telegram алертов

1. В Sentry перейдите в **Settings** → **Integrations**
2. Найдите **Telegram** и нажмите **Add to Slack** (или аналогичную кнопку)
3. Следуйте инструкциям для создания Telegram бота для алертов
4. Добавьте бота в ваш личный чат или группу администраторов

### Альтернатива: Webhook → Telegram

Можно настроить webhook, который будет отправлять сообщения в ваш основной бот:

1. В Sentry: **Settings** → **Developer Settings** → **New Internal Integration**
2. Укажите Webhook URL: `https://your-bot-server.com/sentry-webhook`
3. Выберите разрешения: `Issue & Event - Read`
4. В вашем боте создайте endpoint `/sentry-webhook`:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/sentry-webhook")
async def sentry_webhook(request: Request):
    """Получить алерты от Sentry и отправить в Telegram."""
    data = await request.json()

    # Извлечь информацию
    issue_title = data.get("data", {}).get("issue", {}).get("title")
    issue_url = data.get("data", {}).get("issue", {}).get("web_url")
    level = data.get("data", {}).get("event", {}).get("level")

    # Отправить сообщение администратору
    admin_chat_id = os.getenv("ADMIN_TELEGRAM_CHAT_ID")

    message = f"""
🚨 <b>Sentry Alert</b>

<b>Issue:</b> {issue_title}
<b>Level:</b> {level.upper()}

<a href="{issue_url}">View in Sentry →</a>
"""

    await bot.send_message(
        chat_id=admin_chat_id,
        text=message,
        parse_mode="HTML"
    )

    return {"status": "ok"}
```

---

## 📊 Рекомендуемые алерты по приоритету

### Уровень 1 (Критический) - Немедленное действие

| Алерт            | Условие                            | Действие                     |
| ---------------- | ---------------------------------- | ---------------------------- |
| 🚨 Bot Crashed    | level=critical                     | Telegram + Email (мгновенно) |
| 💰 Trading Failed | component=trading, level=error     | Telegram + Email (5 мин)     |
| 🔑 Auth Failed    | exception=AuthenticationError      | Telegram + Email (5 мин)     |
| 🗄️ Database Down  | component=database, level=critical | Telegram + Email (мгновенно) |

### Уровень 2 (Важный) - В течение часа

| Алерт                 | Условие                           | Действие          |
| --------------------- | --------------------------------- | ----------------- |
| ⚠️ Rate Limit Exceeded | exception=RateLimitError, >5/hour | Email (30 мин)    |
| 📉 API Errors Spike    | component=api, >10 errors/hour    | Email (30 мин)    |
| 🔄 Repeated Failures   | same issue >20 times/hour         | Telegram (30 мин) |

### Уровень 3 (Мониторинг) - Ежедневно

| Алерт                 | Условие                | Действие             |
| --------------------- | ---------------------- | -------------------- |
| 📊 Daily Error Summary | all errors             | Email (1 раз в день) |
| 🎯 Warning Spike       | level=warning, >50/day | Email (1 раз в день) |

---

## 🎛️ Дополнительные настройки

### 1. Issue Owners

Настройте автоматическое назначение ответственных:

**Settings** → **Ownership Rules**

```
# Trading errors → Developer 1
tags.component:trading email@developer1.com

# API errors → Developer 2
tags.component:api email@developer2.com

# Critical → All admins
level:critical team:admins
```

### 2. Issue Grouping

Настройте правила группировки ошибок:

**Settings** → **General Settings** → **Grouping & Fingerprinting**

```python
# Группировать по типу исключения и компоненту
{{ exception.type }}|{{ tags.component }}

# Не группировать Rate Limit ошибки по времени
{% if exception.type == "RateLimitError" %}
  {{ exception.type }}|{{ timestamp | truncate(hour) }}
{% else %}
  {{ default }}
{% endif %}
```

### 3. Performance Monitoring

Настройте алерты на производительность:

**Alerts** → **Create Alert** → **Performance**

**Условия:**
```
When transaction duration for /arbitrage
  is greater than 5 seconds
  for at least 10 transactions in 1 hour
```

---

## 📝 Пример конфигурации .env

Добавьте в ваш `.env`:

```env
# Sentry Configuration
SENTRY_DSN=https://your-key@sentry.io/your-project
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Admin Notifications
ADMIN_TELEGRAM_CHAT_ID=123456789
ADMIN_EMAIL=admin@example.com

# Alert Thresholds
RATE_LIMIT_ALERT_THRESHOLD=5
ERROR_SPIKE_THRESHOLD=10
```

---

## 🧪 Тестирование алертов

### 1. Проверить Email

```
/test_sentry error
```

Должен прийти email с темой:
```
[Sentry] dmarket-bot - Test Error
```

### 2. Проверить Telegram

Если настроена интеграция, выполните:

```
/test_sentry critical
```

Должно прийти сообщение в Telegram:
```
🚨 Sentry Alert
Issue: Test Critical Error
Level: CRITICAL
View in Sentry →
```

### 3. Проверить все алерты

Сгенерируйте разные типы ошибок:

```bash
# Trading error
/test_sentry trading

# Auth error
/test_sentry auth

# Database error
/test_sentry database

# Rate limit error
/test_sentry rate_limit
```

Проверьте, что для каждой пришло соответствующее уведомление.

---

## 🔄 Обслуживание алертов

### Еженедельно

- [ ] Проверить количество срабатываний каждого алерта
- [ ] Отключить алерты для resolved issues
- [ ] Обновить пороги срабатывания при необходимости

### Ежемесячно

- [ ] Проанализировать самые частые алерты
- [ ] Удалить неактуальные алерты
- [ ] Добавить новые алерты на основе опыта

### При изменении кода

- [ ] Обновить теги в коде при добавлении новых компонентов
- [ ] Создать алерты для новых критических функций
- [ ] Протестировать алерты для нового функционала

---

## 🎯 Best Practices

### 1. Не злоупотребляйте алертами

❌ **Плохо:**
```
Alert на каждый warning
Alert на каждую info запись
Alert на каждую попытку retry
```

✅ **Хорошо:**
```
Alert только на критические ошибки
Alert на повторяющиеся проблемы
Alert на бизнес-критичные события
```

### 2. Используйте правильные уровни severity

```python
# CRITICAL - бот упал, деньги потеряны, данные коррумпированы
logger.critical("Trading failed: lost $1000 due to API error")

# ERROR - функциональность нарушена, требует внимания
logger.error("Failed to fetch market data", exc_info=True)

# WARNING - потенциальная проблема, но работа продолжается
logger.warning("Rate limit approached: 90% of quota used")

# INFO - обычные операции
logger.info("Arbitrage scan completed", extra={"items": 150})
```

### 3. Добавляйте контекст в ошибки

```python
# ❌ Плохо
raise ValueError("Invalid price")

# ✅ Хорошо
raise ValueError(
    f"Invalid price for item {item_id}: "
    f"price={price}, min={min_price}, max={max_price}"
)
```

### 4. Группируйте похожие ошибки

Используйте fingerprinting для группировки:

```python
# В Sentry будут сгруппированы все ошибки одного типа для одного item
with sentry_sdk.configure_scope() as scope:
    scope.fingerprint = ["trading-error", item_id]
    raise TradingError(f"Failed to buy {item_id}")
```

---

## 📚 Дополнительные ресурсы

- [Sentry Alerts Documentation](https://docs.sentry.io/product/alerts/)
- [Sentry Integrations](https://docs.sentry.io/product/integrations/)
- [Best Practices for Alerts](https://docs.sentry.io/product/alerts/best-practices/)
- [Проект: SENTRY_TESTING_GUIDE.md](SENTRY_TESTING_GUIDE.md)

---

## ❓ FAQ

**Q: Сколько алертов нужно настроить?**
A: Начните с 3-5 критических алертов. Добавляйте новые по мере выявления проблем.

**Q: Куда лучше отправлять алерты: Email или Telegram?**
A: Telegram для критических (немедленное действие), Email для остальных.

**Q: Как избежать спама алертами?**
A: Используйте rate limiting (например, максимум 1 алерт в 30 минут для одного issue).

**Q: Что делать с тестовыми issues?**
A: Очистите их перед production (см. [SENTRY_CLEANUP.md](SENTRY_CLEANUP.md)).

---

**Настройте алерты сейчас и спите спокойно! 🛌**
