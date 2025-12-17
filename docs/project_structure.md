# Структура проекта DMarket Bot

**Версия**: 4.0
**Последнее обновление**: 17 декабря 2025 г.

---

В этом документе описана структура проекта DMarket Bot, роль каждой директории и основные компоненты системы.

## Общая структура

```
DMarket-Telegram-Bot/
├── config/                  # Конфигурационные файлы
│   ├── config.yaml
│   └── .env.example
├── docs/                    # Документация (60+ файлов)
│   ├── ARBITRAGE.md         # Полное руководство по арбитражу
│   ├── ARCHITECTURE.md      # Архитектура проекта
│   ├── QUICK_START.md       # Быстрый старт
│   ├── SECURITY.md          # Руководство по безопасности
│   └── ...
├── alembic/                 # Миграции базы данных
│   └── versions/
├── logs/                    # Логи приложения
├── scripts/                 # Скрипты для запуска и управления
│   ├── init_db.py
│   ├── validate_config.py
│   └── health_check.py
├── src/                     # Исходный код
│   ├── dmarket/             # Модули для работы с DMarket API
│   │   ├── api/             # Модульный API-клиент
│   │   │   ├── auth.py      # Ed25519/HMAC авторизация
│   │   │   ├── client.py    # HTTP клиент
│   │   │   ├── market.py    # Операции с рынком
│   │   │   ├── trading.py   # Торговые операции
│   │   │   ├── wallet.py    # Операции с кошельком
│   │   │   └── ...
│   │   ├── scanner/         # Сканер арбитража
│   │   │   ├── levels.py    # Уровни торговли
│   │   │   ├── cache.py     # Кэширование
│   │   │   ├── filters.py   # Фильтры
│   │   │   └── analysis.py  # Анализ прибыли
│   │   ├── targets/         # Управление таргетами
│   │   │   ├── manager.py   # Менеджер таргетов
│   │   │   ├── competition.py # Конкурентный анализ
│   │   │   └── validators.py
│   │   ├── arbitrage/       # Арбитражная логика
│   │   │   ├── core.py      # Основная логика
│   │   │   ├── trader.py    # Автотрейдер
│   │   │   └── ...
│   │   ├── filters/         # Фильтры для игр
│   │   │   └── game_filters.py
│   │   ├── dmarket_api.py   # Основной API клиент
│   │   ├── arbitrage_scanner.py
│   │   ├── liquidity_analyzer.py
│   │   ├── market_analysis.py
│   │   ├── auto_seller.py
│   │   ├── backtester.py
│   │   └── hft_mode.py
│   ├── telegram_bot/        # Модули для Telegram бота
│   │   ├── commands/        # Команды бота
│   │   ├── handlers/        # Обработчики событий
│   │   ├── keyboards/       # Клавиатуры
│   │   ├── notifications/   # Уведомления
│   │   ├── smart_notifications/
│   │   ├── i18n/            # Интернационализация
│   │   ├── keyboards.py     # Генераторы клавиатур
│   │   ├── localization.py  # Локализация
│   │   └── ...
│   ├── analytics/           # 📦 Аналитика (NEW)
│   │   ├── backtester.py
│   │   └── historical_data.py
│   ├── portfolio/           # 📦 Управление портфелем (NEW)
│   │   ├── manager.py
│   │   ├── analyzer.py
│   │   └── models.py
│   ├── web_dashboard/       # 📦 Веб-дашборд (NEW)
│   │   └── app.py
│   ├── models/              # Модели SQLAlchemy 2.0
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── target.py
│   │   ├── market.py
│   │   ├── alert.py
│   │   └── log.py
│   └── utils/               # Утилиты
│       ├── config.py
│       ├── database.py
│       ├── memory_cache.py
│       ├── redis_cache.py
│       ├── rate_limiter.py
│       ├── api_circuit_breaker.py
│       ├── sentry_integration.py
│       └── logging_utils.py
└── tests/                   # Тестирование (2348+ тестов)
    ├── unit/                # Юнит-тесты
    ├── integration/         # Интеграционные тесты
    ├── contracts/           # Контрактные тесты (Pact)
    ├── property_based/      # Property-based тесты
    ├── e2e/                 # End-to-end тесты
    ├── cassettes/           # VCR.py записи HTTP
    ├── conftest.py          # Основные фикстуры
    └── conftest_vcr.py      # VCR.py фикстуры
```

## Запуск приложения

Для запуска бота используйте скрипт:

```bash
python scripts/run_bot.py
```

Для тестирования используйте команду:

```bash
pytest
```

Для запуска с покрытием:

```bash
pytest --cov=src --cov-report=html
```

## Основные компоненты

### src/ - Исходный код

#### src/dmarket/
- **api/** - Модульный API клиент
  - `endpoints.py` - API эндпоинты
  - `auth.py` - Ed25519/HMAC подписи
  - `cache.py` - кэширование запросов
  - `client.py` - базовый HTTP клиент
  - `inventory.py` - операции с инвентарем
  - `market.py` - операции с рынком
  - `targets_api.py` - API таргетов
  - `trading.py` - торговые операции
  - `wallet.py` - операции с кошельком
- **scanner/** - Модульный сканер арбитража
  - `__init__.py` - Публичный API пакета
  - `levels.py` - Конфигурации уровней (boost, standard, medium, advanced, pro)
  - `cache.py` - ScannerCache с TTL и статистикой
  - `filters.py` - ScannerFilters с blacklist/whitelist
  - `analysis.py` - Расчет прибыли и анализ возможностей
- **targets/** - Управление таргетами (Buy Orders)
  - `manager.py` - Менеджер таргетов
  - `competition.py` - Конкурентный анализ
  - `validators.py` - Валидация таргетов
- **arbitrage/** - Арбитражная логика
  - `core.py` - Основная логика арбитража
  - `calculations.py` - Расчеты прибыли
  - `cache.py` - Кэширование
  - `search.py` - Поиск возможностей
  - `trader.py` - Автотрейдер
- **filters/** - Фильтры для различных игр (CS:GO, Dota 2, TF2, Rust)
- **dmarket_api.py** - Основной API клиент
- **arbitrage_scanner.py** - Сканер арбитража
- **liquidity_analyzer.py** - Анализ ликвидности
- **market_analysis.py** - Анализ рынка и технические индикаторы
- **sales_history.py** - Работа с историей продаж
- **auto_seller.py** - Автоматическая продажа
- **backtester.py** - Бэктестинг стратегий
- **hft_mode.py** - High-frequency trading режим

#### src/analytics/
- **backtester.py** - Бэктестинг торговых стратегий
- **historical_data.py** - Работа с историческими данными

#### src/portfolio/
- **manager.py** - Управление портфелем
- **analyzer.py** - Анализ P&L и рисков
- **models.py** - Модели данных портфеля

#### src/web_dashboard/
- **app.py** - Веб-дашборд для мониторинга

#### src/telegram_bot/
- **commands/** - Команды бота
- **handlers/** - Обработчики команд, связанных с DMarket
- **keyboards/** - Генераторы клавиатур для Telegram-бота
- **notifications/** - Система уведомлений
- **smart_notifications/** - Умные уведомления
- **i18n/** - Интернационализация (RU, EN, ES, DE)
- **localization.py** - Локализация
- **profiles.py** - Управление профилями пользователей

#### src/utils/
- **config.py** - Конфигурация приложения (Pydantic Settings)
- **database.py** - Менеджер базы данных (SQLAlchemy 2.0)
- **memory_cache.py** - In-memory кэш (TTLCache)
- **redis_cache.py** - Redis кэширование
- **rate_limiter.py** - Rate limiting (aiolimiter)
- **api_circuit_breaker.py** - Circuit Breaker паттерн
- **sentry_integration.py** - Интеграция с Sentry
- **logging_utils.py** - Структурированное логирование (structlog)
- **api_error_handling.py** - Обработка ошибок API
- **rate_limiter.py** - Управление лимитами запросов к API
- **dmarket_api_utils.py** - Вспомогательные функции для API

### tests/ - Тестирование
- Содержит автоматические тесты для всех компонентов системы
- **conftest.py** - Конфигурация pytest и фикстуры

### scripts/ - Скрипты и примеры
- Примеры использования API и различных компонентов системы
- Утилиты для отладки и демонстрации функциональности

### docs/ - Документация
- Руководства по использованию различных компонентов системы
- Инструкции по настройке и развертыванию

## Конфигурация

### Переменные окружения (.env)
- **DMARKET_PUBLIC_KEY** - Публичный ключ API DMarket
- **DMARKET_SECRET_KEY** - Секретный ключ API DMarket
- **TELEGRAM_BOT_TOKEN** - Токен для Telegram бота

### Настройки линтеров и статического анализа
- **mypy.ini** - Настройки статической проверки типов
- **pyrightconfig.json** - Настройки Pyright для VS Code
- **pyproject.toml** - Настройки pytest, Black, Ruff

## Рекомендации по разработке

1. **Модульность**: Придерживайтесь принципа модульности. Каждый файл должен содержать только один класс или логически связанные функции.
2. **Типизация**: Используйте аннотации типов для облегчения понимания кода и раннего обнаружения ошибок.
3. **Документация**: Документируйте публичные API с помощью docstrings.
4. **Тестирование**: Пишите тесты для новой функциональности.
