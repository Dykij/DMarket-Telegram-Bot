# 🔍 Руководство по тестированию Sentry интеграции

**Дата**: 23 ноября 2025 г.
**Версия**: 1.0

---

## 📋 Оглавление

- [Обзор](#обзор)
- [Настройка Sentry](#настройка-sentry)
- [Тестовые команды](#тестовые-команды)
- [Проверка в Sentry Dashboard](#проверка-в-sentry-dashboard)
- [Ожидаемые breadcrumbs](#ожидаемые-breadcrumbs)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Обзор

Sentry — это система мониторинга ошибок и производительности для production. Бот интегрирован с Sentry для:

- ✅ Автоматического захвата всех ошибок
- ✅ Отслеживания контекста действий пользователя (breadcrumbs)
- ✅ Мониторинга производительности API запросов
- ✅ Анализа паттернов ошибок

### Что такое Breadcrumbs?

**Breadcrumbs** — это "хлебные крошки" событий, которые происходили перед ошибкой:

```
[10:30:15] telegram: Bot command: /arbitrage (user_id: 123456789)
[10:30:16] trading: Trading action: arbitrage_scan_started (game: csgo, level: standard)
[10:30:16] http: API request: GET /marketplace-api/v1/items
[10:30:17] http: API request: GET /marketplace-api/v1/items (200, 450ms)
[10:30:18] error: RateLimitError - Too many requests
```

Это позволяет **точно** понять, что делал пользователь перед ошибкой.

---

## 🔧 Настройка Sentry

### 1. Создание проекта в Sentry

1. Зарегистрируйтесь на [sentry.io](https://sentry.io)
2. Создайте новый проект → выберите **Python**
3. Скопируйте **DSN** (Data Source Name)

### 2. Настройка .env файла

Добавьте в `.env`:

```env
# Sentry мониторинг
SENTRY_DSN=https://your-key@o12345.ingest.sentry.io/67890
SENTRY_ENVIRONMENT=production  # или development
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% для тестирования
```

**ВАЖНО:** Не коммитьте `.env` в git!

### 3. Проверка инициализации

Запустите бота:

```bash
python src/main.py
```

В логах должно быть:

```
INFO - Sentry initialized successfully
INFO - Sentry DSN: https://...ingest.sentry.io/...
INFO - Environment: production
```

---

## 🧪 Тестовые команды

Бот предоставляет специальные команды для тестирования Sentry:

### `/sentry_info` - Информация о Sentry

Показывает статус интеграции и список доступных тестов:

```
📊 Sentry Integration Status

✅ Sentry инициализирован

Доступные тесты:
• /test_sentry breadcrumbs - Тест breadcrumbs
• /test_sentry error - Тест простой ошибки
• /test_sentry api_error - Тест API ошибки
• /test_sentry division - Тест деления на ноль
• /test_sentry all - Все тесты
```

### `/test_sentry all` - Полное тестирование

Запускает все тесты последовательно:

```bash
# В Telegram боте
/test_sentry all
```

**Что происходит:**

1. ✅ **Breadcrumbs тест** - создает серию breadcrumbs:
   - Начало сканирования арбитража
   - API запрос к DMarket
   - Успешный ответ API
   - Завершение сканирования

2. ✅ **Simple error тест** - генерирует простую ошибку:
   ```python
   ValueError("Test error: This is intentional for Sentry testing")
   ```

3. ✅ **API error тест** - симулирует ошибку rate limit:
   ```python
   RuntimeError("API Rate Limit: Too many requests (429)")
   ```

4. ✅ **Division error тест** - деление на ноль:
   ```python
   ZeroDivisionError
   ```

### `/test_sentry breadcrumbs` - Только breadcrumbs

Тестирует только создание breadcrumbs без ошибок:

```bash
/test_sentry breadcrumbs
```

### `/test_sentry error` - Простая ошибка

Генерирует простую ошибку для проверки захвата:

```bash
/test_sentry error
```

### `/test_sentry api_error` - API ошибка с контекстом

Симулирует ошибку rate limit с полным контекстом:

```bash
/test_sentry api_error
```

---

## 📊 Проверка в Sentry Dashboard

### 1. Открыть Sentry Dashboard

Перейдите на [https://sentry.io](https://sentry.io) → ваш проект

### 2. Раздел Issues

**Issues** → последние ошибки

Вы должны увидеть:

- ✅ `ValueError: Test error: This is intentional...`
- ✅ `RuntimeError: API Rate Limit: Too many requests`
- ✅ `ZeroDivisionError: division by zero`

### 3. Детали ошибки

Кликните на любую ошибку → **Breadcrumbs** секция:

```
[10:30:15] telegram
  Bot command: /test_sentry
  user_id: 123456789
  username: john_doe

[10:30:16] trading
  Trading action: arbitrage_scan_started
  game: csgo
  level: standard
  user_id: 123456789
  balance: $100.50

[10:30:16] http
  API request: GET /marketplace-api/v1/items
  retry: 0
  game: csgo

[10:30:17] http
  API request: GET /marketplace-api/v1/items
  status_code: 200
  response_time_ms: 450.50

[10:30:18] trading
  Trading action: arbitrage_scan_completed
  opportunities_found: 5
  scan_duration_ms: 1250

[10:30:18] error
  Error: RateLimitError
  error_message: Too many requests
  retry_after: 60
```

### 4. User Context

В секции **User** должны быть данные:

```
ID: 123456789
Username: john_doe
Role: tester
```

### 5. Tags

В секции **Tags**:

```
environment: production
level: error
user_id: 123456789
```

---

## 🎯 Ожидаемые breadcrumbs

### Для команды `/arbitrage`

```
[timestamp] telegram
  Bot command: /arbitrage
  user_id: XXX
  username: john_doe

[timestamp] trading
  Trading action: arbitrage_scan_started
  game: csgo
  level: standard

[timestamp] http
  API request: GET /marketplace-api/v1/items
  retry: 0

[timestamp] http
  API request: GET /marketplace-api/v1/items
  status_code: 200
  response_time_ms: 450

[timestamp] trading
  Trading action: arbitrage_scan_completed
  opportunities_found: 15
  scan_duration_ms: 1250
```

### Для команды `/balance`

```
[timestamp] telegram
  Bot command: /balance
  user_id: XXX

[timestamp] http
  API request: GET /account/v1/balance
  retry: 0

[timestamp] http
  API request: GET /account/v1/balance
  status_code: 200
  response_time_ms: 320
```

### При ошибке API

```
[timestamp] telegram
  Bot command: /arbitrage
  user_id: XXX

[timestamp] trading
  Trading action: scanning_market
  game: csgo

[timestamp] http
  API request: GET /marketplace-api/v1/items
  retry: 0

[timestamp] http
  API request: GET /marketplace-api/v1/items
  retry: 1

[timestamp] http
  API request: GET /marketplace-api/v1/items
  retry: 2

[timestamp] error
  Error: RateLimitError
  error_message: Too many requests
  retry_after: 60
  endpoint: /marketplace-api/v1/items

[timestamp] error (CAPTURED)
  RateLimitError: API rate limit exceeded (429)
```

---

## 🔥 Production Testing Workflow

### Полный тест в production окружении

1. **Настроить production Sentry:**

   ```env
   SENTRY_DSN=https://your-production-key@sentry.io/your-project
   SENTRY_ENVIRONMENT=production
   SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% для production
   ```

2. **Запустить бота:**

   ```bash
   python src/main.py
   ```

3. **Выполнить тестовые команды:**

   ```
   /sentry_info          # Проверить статус
   /test_sentry all      # Запустить все тесты
   ```

4. **Проверить Sentry Dashboard:**

   - Issues → должны появиться новые ошибки
   - Каждая ошибка → Breadcrumbs → полный контекст

5. **Выполнить реальные команды:**

   ```
   /start
   /arbitrage
   /balance
   ```

6. **Сгенерировать ошибку (опционально):**

   - Установить невалидный API key
   - Выполнить `/balance`
   - Проверить ошибку в Sentry с breadcrumbs

---

## 🐛 Troubleshooting

### Sentry не инициализирован

**Проблема:**
```
❌ Sentry НЕ инициализирован
```

**Решение:**

1. Проверить `.env` файл:
   ```bash
   cat .env | grep SENTRY_DSN
   ```

2. Убедиться, что DSN правильный:
   ```env
   SENTRY_DSN=https://KEY@oXXXXX.ingest.sentry.io/XXXXX
   ```

3. Перезапустить бота

### Breadcrumbs не появляются в Sentry

**Проблема:** В Issues нет секции Breadcrumbs

**Решение:**

1. Убедиться, что Sentry инициализирован:
   ```bash
   /sentry_info
   ```

2. Проверить версию sentry-sdk:
   ```bash
   pip show sentry-sdk
   # Должна быть >= 1.40.0
   ```

3. Запустить тест:
   ```bash
   /test_sentry all
   ```

4. Проверить логи бота:
   ```bash
   grep "Sentry breadcrumb added" logs/bot.log
   ```

### Ошибки не отправляются в Sentry

**Проблема:** Issues не появляются в dashboard

**Решение:**

1. Проверить SENTRY_DSN:
   ```python
   import os
   print(os.getenv("SENTRY_DSN"))
   ```

2. Проверить сеть:
   ```bash
   ping sentry.io
   ```

3. Проверить логи:
   ```bash
   grep "sentry" logs/bot.log -i
   ```

4. Включить debug Sentry:
   ```python
   sentry_sdk.init(
       dsn="...",
       debug=True  # Добавить
   )
   ```

### Test команды не работают

**Проблема:**
```
❌ Эта команда доступна только администраторам
```

**Решение:**

1. Добавить себя в администраторы в `.env`:
   ```env
   ADMIN_USERS=123456789,987654321
   ```

2. Или включить DEBUG режим:
   ```env
   DEBUG=true
   ```

3. Перезапустить бота

---

## 📈 Метрики и мониторинг

### Полезные фильтры в Sentry

**По типу ошибки:**
```
error.type:RateLimitError
```

**По пользователю:**
```
user.id:123456789
```

**По команде:**
```
breadcrumb.message:"Bot command: /arbitrage"
```

**По игре:**
```
breadcrumb.data.game:csgo
```

### Настройка алертов

1. Sentry → **Alerts** → **Create Alert Rule**
2. Условия:
   - `error.type = RateLimitError`
   - Больше 5 раз за 5 минут
3. Действие:
   - Email уведомление
   - Slack webhook

---

## 🎓 Best Practices

### 1. Не тестировать в production постоянно

Используйте `/test_sentry` **только для проверки** интеграции, не для постоянных тестов.

### 2. Очистка тестовых ошибок

После тестирования удалите тестовые issues в Sentry:

1. Dashboard → Issues
2. Фильтр: `error.value:*test*`
3. Bulk actions → Resolve

### 3. Настройка sample rate для production

```env
# Development - 100%
SENTRY_TRACES_SAMPLE_RATE=1.0

# Production - 10%
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 4. Мониторинг критических операций

Добавляйте breadcrumbs для важных действий:

```python
from src.utils.sentry_breadcrumbs import add_trading_breadcrumb

add_trading_breadcrumb(
    action="buying_item",
    game="csgo",
    user_id=user_id,
    item_title="AK-47 | Redline (FT)",
    price_usd=10.50
)
```

---

## 📚 Дополнительные ресурсы

- [Sentry Documentation](https://docs.sentry.io/platforms/python/)
- [Breadcrumbs Guide](https://docs.sentry.io/platforms/python/enriching-events/breadcrumbs/)
- [Error Monitoring Best Practices](https://blog.sentry.io/error-monitoring-best-practices/)
- [src/utils/sentry_breadcrumbs.py](../src/utils/sentry_breadcrumbs.py) - Исходный код breadcrumbs

---

## ✅ Checklist для production

- [ ] SENTRY_DSN установлен в `.env`
- [ ] SENTRY_ENVIRONMENT = "production"
- [ ] SENTRY_TRACES_SAMPLE_RATE <= 0.1
- [ ] `/sentry_info` показывает "✅ Sentry инициализирован"
- [ ] `/test_sentry all` успешно выполнен
- [ ] Issues появляются в Sentry dashboard
- [ ] Breadcrumbs отображаются в каждой ошибке
- [ ] User context установлен корректно
- [ ] Алерты настроены для критических ошибок
- [ ] Тестовые issues очищены из dashboard

---

**Версия документа**: 1.0
**Последнее обновление**: 23 ноября 2025 г.
