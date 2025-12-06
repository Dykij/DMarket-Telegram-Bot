# 🚀 Production Ready: Sentry Integration Quick Start

**Дата**: 23 ноября 2025 г.

---

## ⚡ Быстрая настройка для production

### 1. Настройка Sentry DSN

Добавьте в `.env`:

```env
SENTRY_DSN=https://your-key@sentry.io/your-project
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 2. Запуск бота

```bash
python src/main.py
```

### 3. Проверка статуса

В Telegram боте выполните:

```
/sentry_info
```

Должно быть:
```
✅ Sentry инициализирован
```

### 4. Тестирование

Выполните полный тест:

```
/test_sentry all
```

### 5. Проверка в Sentry Dashboard

1. Откройте [https://sentry.io](https://sentry.io)
2. Перейдите в **Issues**
3. Проверьте тестовые ошибки
4. Откройте любую ошибку → **Breadcrumbs**

**Ожидаемые breadcrumbs:**

```
[timestamp] telegram
  Bot command: /test_sentry
  user_id: XXX

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

[timestamp] error
  Error: RateLimitError
  error_message: Too many requests
```

---

## 🧪 Реальное тестирование

После успешных тестов выполните реальные команды:

```
/start
/arbitrage
/balance
```

Затем проверьте в Sentry:
- Breadcrumbs для каждой команды
- Контекст пользователя
- Метрики производительности

---

## 📋 Checklist для production

- [x] SENTRY_DSN установлен
- [x] SENTRY_ENVIRONMENT = "production"
- [x] SENTRY_TRACES_SAMPLE_RATE <= 0.1
- [x] `/sentry_info` показывает "✅ Sentry инициализирован"
- [x] `/test_sentry all` выполнен успешно
- [x] Issues появились в Sentry dashboard
- [x] Breadcrumbs отображаются корректно
- [x] Алерты настроены для критических ошибок
- [x] Тестовые issues очищены

---

## 🎯 Следующие шаги

### 1. Настройка алертов

Настройте уведомления для критических ошибок:

```bash
# Откройте гайд по настройке алертов
# См. docs/SENTRY_ALERTS_SETUP.md
```

**Рекомендуемые алерты:**
- 🚨 Критические ошибки (level=critical)
- 💰 Ошибки торговли (component=trading)
- 🔑 Ошибки аутентификации (exception=AuthenticationError)
- ⚠️ Rate limit превышения (exception=RateLimitError)
- 🗄️ Ошибки БД (component=database)

### 2. Очистка тестовых issues

Перед production удалите тестовые данные:

```bash
# Шаг 1: Настройте переменные в .env
SENTRY_AUTH_TOKEN=your_token_here
SENTRY_ORGANIZATION=your-org
SENTRY_PROJECT=your-project

# Шаг 2: Предпросмотр (dry-run)
python scripts/sentry_cleanup.py --test-only

# Шаг 3: Выполнить очистку
python scripts/sentry_cleanup.py --test-only --execute

# Полная инструкция: docs/SENTRY_CLEANUP.md
```

---

## 📚 Дополнительно

Полная документация: [SENTRY_TESTING_GUIDE.md](SENTRY_TESTING_GUIDE.md)
