# 🎯 Приоритеты тестирования (Декабрь 2025)

> **Дата обновления:** 27 декабря 2025 г. (версия 22.0)
> **Текущее покрытие:** ~90% ✅ (цель 80% достигнута!)
> **DMarket API покрытие:** 90%+ ✅ (auth.py, cache.py, liquidity_rules.py полностью покрыты)
> **Всего тестов:** 2935+ (все проходят)
> **В процессе:** Phase 4 - Достижение 100% покрытия - ПРОДОЛЖАЕТСЯ
> **Добавлено в этом PR:** 2935+ тестов ✅ (Phase 1: 640 + Phase 2: 87 + Phase 3: 1076 + Phase 4: 1132)

---

## 🎯 PHASE 4: Достижение 100% покрытия (Q1-Q3 2026)

> **Новая цель:** Довести каждый модуль до 100% покрытия

### 📊 Анализ модулей с покрытием ниже 50%

**Для достижения 100% покрытия необходимо довести ВСЕ модули до полного покрытия.**

#### 🔴 Критические модули с покрытием < 40% (требуют срочного внимания)

| Модуль | Файл | Строк | Текущее покрытие | Нужно тестов | Приоритет | Статус |
|--------|------|-------|------------------|--------------|-----------|--------|
| **dmarket_api.py** | `src/dmarket/dmarket_api.py` | 3092 | ~45% | 100+ | 🔥 КРИТИЧЕСКИЙ | ✅ +52 тестов (26.12.2025) |
| **portfolio_manager.py** | `src/dmarket/portfolio_manager.py` | 961 | ~45% | 60+ | 🔥 КРИТИЧЕСКИЙ | ✅ +38 тестов (26.12.2025) |
| **arbitrage_scanner.py** | `src/dmarket/arbitrage_scanner.py` | 1666 | ~50% | 150+ | 🔥 КРИТИЧЕСКИЙ | ✅ +76 тестов (26.12.2025) |
| **game_filter_handlers.py** | `src/telegram_bot/handlers/game_filter_handlers.py` | 1196 | ~55% | 100+ | 🔥 КРИТИЧЕСКИЙ | ✅ +68 тестов (26.12.2025) |
| **market_analysis_handler.py** | `src/telegram_bot/handlers/market_analysis_handler.py` | 1121 | ~60% | 40+ | 🔥 ВЫСОКИЙ | ✅ +76 тестов (26.12.2025) |
| **backtester.py** | `src/dmarket/backtester.py` | 1118 | ~55% | 50+ | 🔥 ВЫСОКИЙ | ✅ +94 тестов (26.12.2025) |
| **arbitrage_sales_analysis.py** | `src/dmarket/arbitrage_sales_analysis.py` | 998 | ~55% | 85+ | 🔥 ВЫСОКИЙ | ✅ +63 тестов (26.12.2025) |
| **market_analysis.py** | `src/dmarket/market_analysis.py` | 988 | ~55% | 80+ | 🔥 ВЫСОКИЙ | ✅ +62 тестов (26.12.2025) |
| **market_alerts_handler.py** | `src/telegram_bot/handlers/market_alerts_handler.py` | 934 | ~55% | 80+ | ⚡ ВЫСОКИЙ | ✅ +68 тестов (26.12.2025) |
| **market_visualizer.py** | `src/utils/market_visualizer.py` | 867 | ~55% | 90+ | ⚡ СРЕДНИЙ | ✅ +75 тестов (26.12.2025) |
| **smart_market_finder.py** | `src/dmarket/smart_market_finder.py` | 865 | ~55% | 70+ | ⚡ ВЫСОКИЙ | ✅ +96 тестов (26.12.2025) |

#### 🟡 Модули с покрытием 40-50% (требуют улучшения)

| Модуль | Файл | Строк | Текущее покрытие | Нужно тестов | Приоритет |
|--------|------|-------|------------------|--------------|-----------|
| **formatters.py** | `src/telegram_bot/utils/formatters.py` | 862 | ~50% | 60+ | ⚡ ВЫСОКИЙ |
| **database.py** | `src/utils/database.py` | 843 | ~55% | 70+ | ⚡ ВЫСОКИЙ | ✅ +76 тестов (26.12.2025) |
| **auto_seller.py** | `src/dmarket/auto_seller.py` | 828 | ~55% | 75+ | ⚡ ВЫСОКИЙ | ✅ +73 тестов (26.12.2025) |
| **game_filters/handlers.py** | `src/telegram_bot/handlers/game_filters/handlers.py` | 820 | ~45% | 65+ | ⚡ СРЕДНИЙ | ✅ +60 тестов (26.12.2025) |
| **market_alerts.py** | `src/telegram_bot/market_alerts.py` | 794 | ~50% | 55+ | ⚡ СРЕДНИЙ | ✅ +75 тестов (27.12.2025) |
| **notification_filters_handler.py** | `src/telegram_bot/handlers/notification_filters_handler.py` | 793 | ~45% | 60+ | ⚡ СРЕДНИЙ |
| **sales_history.py** | `src/dmarket/sales_history.py` | 787 | ~50% | 55+ | ⚡ СРЕДНИЙ |
| **exceptions.py** | `src/utils/exceptions.py` | 772 | ~40% | 65+ | ⚡ СРЕДНИЙ |
| **sales_analysis_callbacks.py** | `src/telegram_bot/sales_analysis_callbacks.py` | 764 | ~50% | 50+ | ⚡ СРЕДНИЙ |

#### 🟢 Модули с покрытием 50-70% (нужно довести до 100%)

| Модуль | Файл | Строк | Текущее покрытие | Нужно тестов | Приоритет |
|--------|------|-------|------------------|--------------|-----------|
| **realtime_price_watcher.py** | `src/dmarket/realtime_price_watcher.py` | 763 | ~55% | 45+ | 🟢 СРЕДНИЙ |
| **notification_digest_handler.py** | `src/telegram_bot/handlers/notification_digest_handler.py` | 762 | ~60% | 40+ | 🟢 СРЕДНИЙ |
| **arbitrage/trader.py** | `src/dmarket/arbitrage/trader.py` | 739 | ~55% | 45+ | 🟢 СРЕДНИЙ |
| **dashboard_handler.py** | `src/telegram_bot/handlers/dashboard_handler.py` | 737 | ~60% | 40+ | 🟢 СРЕДНИЙ |
| **market_analyzer.py** | `src/utils/market_analyzer.py` | 727 | ~50% | 50+ | 🟢 СРЕДНИЙ |
| **intramarket_arbitrage.py** | `src/dmarket/intramarket_arbitrage.py` | 726 | ~55% | 45+ | 🟢 СРЕДНИЙ |
| **market_analytics.py** | `src/utils/market_analytics.py` | 664 | ~65% | 35+ | 🟢 НИЗКИЙ |
| **logging_utils.py** | `src/utils/logging_utils.py` | 644 | ~60% | 40+ | 🟢 НИЗКИЙ |

### 📋 План достижения 100% покрытия

#### Этап 1: Критические модули (Q1 2026) - ~900 новых тестов

| Неделя | Модуль | Текущее | Цель | Тестов |
|--------|--------|---------|------|--------|
| 1-2 | `dmarket_api.py` | 30% | 100% | 200+ |
| 3-4 | `arbitrage_scanner.py` | 35% | 100% | 150+ |
| 5-6 | `game_filter_handlers.py` | 40% | 100% | 100+ |
| 7-8 | `market_analysis_handler.py` | 45% | 100% | 80+ |
| 9-10 | `backtester.py` | 40% | 100% | 90+ |
| 11-12 | `arbitrage_sales_analysis.py` | 35% | 100% | 85+ |
| 13-14 | `market_analysis.py` | 40% | 100% | 80+ |
| 15-16 | `portfolio_manager.py` | 30% | 100% | 100+ |

#### Этап 2: Высокий приоритет (Q2 2026) - ~600 новых тестов

| Неделя | Модуль | Текущее | Цель | Тестов |
|--------|--------|---------|------|--------|
| 1-2 | `market_alerts_handler.py` | 35% | 100% | 80+ |
| 3-4 | `market_visualizer.py` | 25% | 100% | 90+ |
| 5-6 | `smart_market_finder.py` | 45% | 100% | 70+ |
| 7-8 | `formatters.py` | 50% | 100% | 60+ |
| 9-10 | `database.py` | 45% | 100% | 70+ |
| 11-12 | `auto_seller.py` | 40% | 100% | 75+ |
| 13-14 | `exceptions.py` | 40% | 100% | 65+ |

#### Этап 3: Средний приоритет (Q3 2026) - ~500 новых тестов

| Неделя | Модуль | Текущее | Цель | Тестов |
|--------|--------|---------|------|--------|
| 1-2 | `game_filters/handlers.py` | 45% | 100% | 65+ |
| 3-4 | `market_alerts.py` | 50% | 100% | 55+ |
| 5-6 | `notification_filters_handler.py` | 45% | 100% | 60+ |
| 7-8 | `sales_history.py` | 50% | 100% | 55+ |
| 9-10 | `sales_analysis_callbacks.py` | 50% | 100% | 50+ |
| 11-12 | Остальные модули | 50-70% | 100% | 200+ |

### 📊 Итоговая сводка Phase 4

| Этап | Период | Тестов | Прирост покрытия |
|------|--------|--------|------------------|
| Этап 1 | Q1 2026 | ~900 | 80% → 90% |
| Этап 2 | Q2 2026 | ~600 | 90% → 95% |
| Этап 3 | Q3 2026 | ~500 | 95% → 100% |
| **ИТОГО** | **9 месяцев** | **~2000** | **80% → 100%** |

### 🎯 Детальные задачи для модулей с покрытием < 40%

#### 1. `dmarket_api.py` (3092 строки, 30% покрытие) → 100%

**Текущее состояние:** 30% покрытие, ~930 строк покрыто
**Необходимо:** +2160 строк покрытия = ~200 тестов

```python
# Категории тестов для dmarket_api.py
- API методы (GET/POST/DELETE): 50 тестов
- Rate limiting и retry logic: 30 тестов
- HMAC authentication: 20 тестов
- Error handling (HTTP 4xx/5xx): 25 тестов
- Параллельные запросы: 15 тестов
- Timeout обработка: 15 тестов
- Cache integration: 20 тестов
- Edge cases: 25 тестов
```

#### 2. `arbitrage_scanner.py` (1666 строк, 35% покрытие) → 100%

**Текущее состояние:** 35% покрытие, ~583 строки покрыто
**Необходимо:** +1083 строки покрытия = ~150 тестов

```python
# Категории тестов для arbitrage_scanner.py
- Scan levels (boost/standard/medium/advanced/pro): 40 тестов
- Profit calculation: 25 тестов
- Filtering и sorting: 30 тестов
- Multi-game support: 20 тестов
- Cache механизмы: 15 тестов
- Concurrent scanning: 10 тестов
- Edge cases: 10 тестов
```

#### 3. `portfolio_manager.py` (961 строка, 30% покрытие) → 100%

**Текущее состояние:** 30% покрытие, ~288 строк покрыто
**Необходимо:** +673 строки покрытия = ~100 тестов

```python
# Категории тестов для portfolio_manager.py
- Portfolio CRUD operations: 25 тестов
- Price tracking: 20 тестов
- Performance analysis: 20 тестов
- Risk assessment: 15 тестов
- Sync with DMarket API: 10 тестов
- Edge cases: 10 тестов
```

#### 4. `market_visualizer.py` (867 строк, 25% покрытие) → 100%

**Текущее состояние:** 25% покрытие, ~217 строк покрыто
**Необходимо:** +650 строк покрытия = ~90 тестов

```python
# Категории тестов для market_visualizer.py
- Chart generation (matplotlib): 30 тестов
- Data formatting: 20 тестов
- Color schemes: 10 тестов
- Export formats (PNG/PDF): 15 тестов
- Edge cases (empty data, large datasets): 15 тестов
```

---

---

## ✅ ВАЖНОЕ ОБНОВЛЕНИЕ: Phase 3 ЗАВЕРШЕНА (26 декабря 2025)

**🎉 ВСЕ модули Phase 3 покрыты тестами! Цель 80% достигнута!**

### 📊 Новые тесты Phase 3 (26 декабря 2025)

| Модуль | Тестов | Статус |
|--------|--------|--------|
| `auto_sell_handler_extended.py` | 30 | ✅ NEW |
| `price_alerts_handler_extended.py` | 23 | ✅ NEW |
| `arbitrage/calculations.py` | 76 | ✅ NEW |
| `targets/validators.py` | 42 | ✅ NEW |
| `game_filter_handlers.py` | 66 | ✅ NEW |
| `price_alerts_handler.py` | 44 | ✅ NEW |
| `settings_handlers.py` | 35 | ✅ NEW |
| `formatters_extended.py` | 66 | ✅ NEW |

### 📊 Результаты DMarket API (20 декабря 2025)

| Модуль             | Было   | Стало      | Улучшение | Тесты | Статус     |
| ------------------ | ------ | ---------- | --------- | ----- | ---------- |
| **wallet.py**      | 11.32% | **95.09%** | +83.77%   | 64    | ✅ ОТЛИЧНО! |
| **cache.py**       | 14.29% | **95.71%** | +81.42%   | 25    | ✅ ОТЛИЧНО! |
| **inventory.py**   | 34.00% | **96.00%** | +62.00%   | 27    | ✅ ОТЛИЧНО! |
| **client.py**      | 93.69% | **93.69%** | -         | 57    | ✅ ОТЛИЧНО! |
| **auth.py**        | 17.91% | **89.55%** | +71.64%   | 20    | ✅ ОТЛИЧНО! |
| **trading.py**     | 25.74% | **85.15%** | +59.41%   | 20    | ✅ ОТЛИЧНО! |
| **market.py**      | 58.23% | **83.54%** | +25.31%   | 38    | ✅ ОТЛИЧНО! |
| **targets_api.py** | 17.07% | **70.73%** | +53.66%   | 20    | ✅ ХОРОШО!  |

**Итого добавлено:** 35+ новых тестов
**Среднее покрытие API:** 87.5%+ ✅
**Модулей с 95%+:** 3 из 8 🎯
**Модулей с 85%+:** 5 из 8 🚀

---

## ✅ ЦЕЛЬ 80% ДОСТИГНУТА

**Поздравляем!** Целевое покрытие 80%+ успешно достигнуто.

### 📊 Прогресс

| Метрика            | Значение       |
| ------------------ | -------------- |
| **Покрытие кода**  | ~80%           |
| **Покрытие веток** | ~65%           |
| **Всего файлов**   | 200+           |
| **Тестов**         | 1803+          |
| **Статус**         | ✅ Все проходят |

---

## 🎯 Следующие цели (2026)

### Цель 1: Довести до 90% (Q1-Q2 2026)

**Фокус:** Модули с покрытием < 50% довести до 90%+

### Цель 2: Довести до 100% (Q2-Q3 2026)

**Фокус:** ВСЕ модули до 100% покрытия

---

## 🔴 Модули с покрытием < 50% (Приоритет для Phase 4)

> **Эти модули требуют срочного внимания для достижения 100%**

### Критические модули с низким покрытием

| Модуль          | Файл                             | Строк | Приоритет | Тестов     |
| --------------- | -------------------------------- | ----- | --------- | ---------- |
| **API клиент**  | `src/dmarket/api/client.py`      | 168   | 🔥 ВЫСШИЙ  | 40+ тестов |
| **Кошелек**     | `src/dmarket/api/wallet.py`      | 215   | 🔥 ВЫСШИЙ  | 25+ тестов |
| **Рынок**       | `src/dmarket/api/market.py`      | 114   | 🔥 ВЫСШИЙ  | 30+ тестов |
| **Торговля**    | `src/dmarket/api/trading.py`     | 97    | 🔥 ВЫСШИЙ  | 25+ тестов |
| **Таргеты API** | `src/dmarket/api/targets_api.py` | 66    | ⚡ ВЫСОКИЙ | 20+ тестов |

---

## ✅ DMarket API Modules - ВЫПОЛНЕНО! (Приоритет: 🔥 КРИТИЧЕСКИЙ)

**Статус:** ✅ **ЗАВЕРШЕНО** (20 декабря 2025)

| Модуль             | Файл                             | Строк | Покрытие     | Тестов | Статус    |
| ------------------ | -------------------------------- | ----- | ------------ | ------ | --------- |
| **Кошелек**        | `src/dmarket/api/wallet.py`      | 215   | **95.09%** ✅ | 64     | ✅ Отлично |
| **Кэш**            | `src/dmarket/api/cache.py`       | 46    | **95.71%** ✅ | 25     | ✅ Отлично |
| **Инвентарь**      | `src/dmarket/api/inventory.py`   | 44    | **96.00%** ✅ | 27     | ✅ Отлично |
| **API клиент**     | `src/dmarket/api/client.py`      | 168   | **93.69%** ✅ | 57     | ✅ Отлично |
| **Аутентификация** | `src/dmarket/api/auth.py`        | 55    | **89.55%** ✅ | 20     | ✅ Отлично |
| **Торговля**       | `src/dmarket/api/trading.py`     | 97    | **85.15%** ✅ | 20     | ✅ Отлично |
| **Рынок**          | `src/dmarket/api/market.py`      | 114   | **83.54%** ✅ | 38     | ✅ Отлично |
| **Таргеты API**    | `src/dmarket/api/targets_api.py` | 66    | **70.73%** ✅ | 20     | ✅ Хорошо  |

**Итого:** 805 строк покрыты на 87.5%+ (~270 тестов, было ~190)

### 🎯 Достижения

- ✅ **35+ новых тестов** добавлено за одну сессию (20 декабря 2025)
- ✅ **3 модуля** достигли **95%+** покрытия (wallet, cache, inventory)
- ✅ **5 модулей** достигли **85%+** покрытия
- ✅ **Все 8 модулей** превысили целевой порог **70%**
- ✅ **Среднее покрытие API:** 87.5%+ (цель была 70%)

### 📝 Добавленные тесты

#### wallet.py (+6 тестов → 95.09%)

- ✅ `test_get_user_profile_success`
- ✅ `test_get_user_profile_handles_api_error`
- ✅ `test_get_user_profile_with_empty_response`
- ✅ `test_get_account_details_success`
- ✅ `test_get_account_details_handles_timeout`
- ✅ `test_get_account_details_with_partial_data`

#### inventory.py (+12 тестов → 96.00%)

- ✅ Тесты для `deposit_assets`
- ✅ Тесты для `get_deposit_status`
- ✅ Тесты для `withdraw_assets`
- ✅ Тесты для `sync_inventory`
- ✅ Тесты для `get_all_user_inventory`
- ✅ Edge case тесты

#### market.py (+20 тестов → 83.54%)

- ✅ Тесты для всех 10 методов API
- ✅ Price conversion тесты
- ✅ Pagination тесты
- ✅ Force refresh тесты
- ✅ Aggregated prices тесты

---

### ~~1. DMarket API Modules (Приоритет: 🔥 КРИТИЧЕСКИЙ)~~ ✅ ВЫПОЛНЕНО

~~**Итого:** 805 строк без покрытия, ~190 тестов необходимо~~

**РЕЗУЛЬТАТ:** 805 строк покрыты на 87.5%+, 270+ тестов создано ✅

---

##### 1.1 API Client (`src/dmarket/api/client.py`) - 40+ тестов

| Категория                   | Примеры тестов                                                                                         | Количество |
| --------------------------- | ------------------------------------------------------------------------------------------------------ | ---------- |
| **Инициализация клиента**   | `test_client_init_with_valid_credentials`, `test_client_init_with_empty_credentials_raises_error`      | 5          |
| **HMAC Аутентификация**     | `test_generate_signature_creates_valid_hmac`, `test_generate_headers_includes_timestamp_and_signature` | 8          |
| **HTTP-запросы (GET/POST)** | `test_get_request_success`, `test_post_request_with_body`, `test_request_handles_http_error`           | 10         |
| **Rate Limiting**           | `test_rate_limiter_delays_requests`, `test_rate_limit_respects_429_retry_after`                        | 6          |
| **Retry Logic**             | `test_retry_on_500_error`, `test_exponential_backoff`, `test_max_retries_exceeded_raises_error`        | 8          |
| **Edge Cases**              | `test_empty_response_body`, `test_invalid_json_response`, `test_network_timeout`                       | 5          |

**Команды:**

```bash
# Создать файл тестов
touch tests/dmarket/api/test_client.py

# Запустить тесты с покрытием
pytest tests/dmarket/api/test_client.py --cov=src/dmarket/api/client.py --cov-report=term-missing -v
```

##### 1.2 Wallet API (`src/dmarket/api/wallet.py`) - 25+ тестов

| Категория             | Примеры тестов                                                                        | Количество |
| --------------------- | ------------------------------------------------------------------------------------- | ---------- |
| **Получение баланса** | `test_get_balance_returns_usd_and_dmc`, `test_get_balance_handles_api_error`          | 5          |
| **Транзакции**        | `test_get_transactions_with_pagination`, `test_get_transactions_with_date_filter`     | 5          |
| **Депозиты**          | `test_create_deposit_with_valid_amount`, `test_deposit_with_zero_amount_raises_error` | 5          |
| **Выводы**            | `test_withdraw_success`, `test_withdraw_insufficient_balance_raises_error`            | 5          |
| **Edge Cases**        | `test_negative_balance`, `test_concurrent_transactions`, `test_invalid_currency`      | 5          |

##### 1.3 Market API (`src/dmarket/api/market.py`) - 30+ тестов

| Категория           | Примеры тестов                                                                                       | Количество |
| ------------------- | ---------------------------------------------------------------------------------------------------- | ---------- |
| **Получение Items** | `test_get_items_with_game_filter`, `test_get_item_by_id_returns_item`, `test_get_items_no_results`   | 8          |
| **Пагинация**       | `test_pagination_first_page`, `test_pagination_last_page`, `test_pagination_with_limit`              | 6          |
| **Фильтры**         | `test_filter_by_price_range`, `test_filter_by_game`, `test_filter_by_rarity`, `test_complex_filters` | 10         |
| **Edge Cases**      | `test_invalid_item_id`, `test_max_price_exceeded`, `test_empty_filter_results`                       | 6          |

##### 1.4 Trading API (`src/dmarket/api/trading.py`) - 25+ тестов

| Категория             | Примеры тестов                                                                                | Количество |
| --------------------- | --------------------------------------------------------------------------------------------- | ---------- |
| **Покупка Items**     | `test_buy_item_success`, `test_buy_item_insufficient_funds`, `test_buy_item_already_sold`     | 8          |
| **Продажа Items**     | `test_sell_item_with_valid_price`, `test_sell_item_not_owned`, `test_sell_item_price_too_low` | 8          |
| **Управление Offers** | `test_cancel_offer_success`, `test_update_offer_price`, `test_get_active_offers`              | 6          |
| **Edge Cases**        | `test_concurrent_buy_attempts`, `test_expired_offer`, `test_zero_price`                       | 3          |

##### 1.5 Targets API (`src/dmarket/api/targets_api.py`) - 20+ тестов

| Категория              | Примеры тестов                                                                                             | Количество |
| ---------------------- | ---------------------------------------------------------------------------------------------------------- | ---------- |
| **Создание Targets**   | `test_create_target_with_valid_params`, `test_create_target_duplicate`, `test_create_target_invalid_price` | 7          |
| **Получение Targets**  | `test_get_targets_with_active_filter`, `test_get_all_targets`, `test_get_targets_by_game`                  | 5          |
| **Обновление Targets** | `test_update_target_price`, `test_update_target_status`, `test_update_nonexistent_target`                  | 4          |
| **Удаление Targets**   | `test_delete_target_success`, `test_delete_target_not_found`, `test_delete_target_with_active_orders`      | 4          |

**Рекомендации по API тестам:**

- ✅ Использовать **мокирование** `httpx.AsyncClient` для изоляции
- ✅ Тестировать **обработку ошибок** (timeout, connection errors, HTTP 4xx/5xx)
- ✅ Использовать **@pytest.mark.parametrize** для множественных сценариев
- ✅ Следовать **AAA паттерну** (Arrange-Act-Assert)
- ✅ Добавить **Property-Based тесты** (Hypothesis) для валидации инвариантов

---

### 2. ~~Arbitrage Module~~ ✅ ХОРОШО ПОКРЫТ (Приоритет: 🔥 КРИТИЧЕСКИЙ)

**Статус:** ✅ **ХОРОШО ПОКРЫТ** (644+ тестов)

| Модуль       | Файл                       | Строк | Покрытие | Тестов | Статус   |
| ------------ | -------------------------- | ----- | -------- | ------ | -------- |
| **Арбитраж** | `src/dmarket/arbitrage.py` | 553   | ~75%     | 644+   | ✅ Хорошо |

**Итого:** Модуль имеет отличное тестовое покрытие с 644+ тестами включая:
- ✅ Unit тесты
- ✅ Integration тесты
- ✅ Property-based тесты (Hypothesis)
- ✅ Edge case тесты

**Дальнейшие действия не требуются** - переходим к следующему приоритету.

---

#### Детальный план тестирования Arbitrage модуля - 60+ тестов

| Категория                       | Примеры тестов                                                                                                     | Количество |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------- |
| **Инициализация сканера**       | `test_scanner_init_with_api_client`, `test_scanner_init_with_custom_filters`, `test_scanner_init_with_cache`       | 5          |
| **Сканирование уровней**        | `test_scan_level_boost_returns_opportunities`, `test_scan_level_standard`, `test_scan_level_with_min_profit`       | 10         |
| **Расчет прибыли**              | `test_calculate_profit_basic_scenario`, `test_calculate_profit_with_commission`, `test_profit_with_high_price`     | 8          |
| **Фильтрация opportunities**    | `test_filter_by_min_profit_percent`, `test_filter_by_price_range`, `test_filter_by_game`, `test_remove_duplicates` | 10         |
| **Сортировка результатов**      | `test_sort_by_profit_descending`, `test_sort_by_price_ascending`, `test_sort_by_liquidity`                         | 5          |
| **Валидация opportunities**     | `test_validate_opportunity_valid`, `test_validate_opportunity_price_changed`, `test_validate_outdated_data`        | 8          |
| **Property-Based (Hypothesis)** | `test_profit_never_negative_with_valid_inputs`, `test_filter_always_returns_subset`, `test_price_invariants`       | 9          |
| **Edge Cases**                  | `test_zero_buy_price`, `test_negative_profit`, `test_no_opportunities_found`, `test_concurrent_scans`              | 5          |

**Примеры Property-Based тестов с Hypothesis:**

```python
from hypothesis import given, strategies as st

@given(
    buy_price=st.floats(min_value=0.01, max_value=10000),
    sell_price=st.floats(min_value=0.01, max_value=10000),
    commission=st.floats(min_value=0, max_value=20)
)
def test_profit_never_negative_when_sell_higher_than_buy(buy_price, sell_price, commission):
    """Property: прибыль не отрицательная при sell >= buy после комиссии."""
    # Assume
    assume(sell_price >= buy_price)

    # Act
    profit = calculate_profit(buy_price, sell_price, commission)

    # Assert
    assert profit >= 0, f"Profit {profit} should be non-negative"

@given(opportunities=st.lists(st.dictionaries(
    keys=st.sampled_from(["item", "profit", "price"]),
    values=st.one_of(st.text(), st.floats(), st.integers())
)))
def test_filter_always_returns_subset(opportunities):
    """Property: фильтр всегда возвращает подмножество исходного списка."""
    # Act
    filtered = filter_opportunities(opportunities, min_profit=1.0)

    # Assert
    assert len(filtered) <= len(opportunities)
    assert all(item in opportunities for item in filtered)
```

**Команды:**

```bash
# Создать файл тестов
touch tests/dmarket/test_arbitrage.py

# Запустить тесты арбитража с покрытием
pytest tests/dmarket/test_arbitrage.py -v --cov=src/dmarket/arbitrage.py --cov-report=term-missing

# Запустить только Property-Based тесты
pytest tests/dmarket/test_arbitrage.py -k "property" -v
```

---

---

### 3. Telegram Bot Handlers (Приоритет: ⚡ ВЫСОКИЙ)

**Итого:** ~2100 строк без покрытия, ~155 тестов необходимо

#### 3.1 Commands - 30+ тестов

| Модуль              | Файл                                       | Строк | Приоритет | Тестов     |
| ------------------- | ------------------------------------------ | ----- | --------- | ---------- |
| **Balance Command** | `telegram_bot/commands/balance_command.py` | 112   | 🔥 ВЫСОКИЙ | 30+ тестов |
| **Resume Command**  | `telegram_bot/commands/resume_command.py`  | 28    | ⚡ СРЕДНИЙ | 10+ тестов |

**Детальный план для Balance Command - 30 тестов:**

| Категория              | Примеры тестов                                                                                        | Количество |
| ---------------------- | ----------------------------------------------------------------------------------------------------- | ---------- |
| **Выполнение команды** | `test_balance_command_shows_usd_balance`, `test_balance_command_shows_dmc_balance`                    | 5          |
| **Форматирование**     | `test_format_balance_with_decimals`, `test_format_large_balance`, `test_format_zero_balance`          | 5          |
| **Взаимодействие UI**  | `test_balance_command_sends_message`, `test_balance_command_shows_inline_keyboard`                    | 5          |
| **Обработка ошибок**   | `test_balance_command_handles_api_error`, `test_balance_command_handles_timeout`                      | 5          |
| **Rate Limiting**      | `test_balance_command_rate_limited`, `test_balance_command_cooldown_message`                          | 5          |
| **Edge Cases**         | `test_balance_command_unauthorized_user`, `test_balance_command_no_api_keys`, `test_concurrent_calls` | 5          |

#### 3.2 Game Filters - 50+ тестов

| Модуль       | Файл                                             | Строк | Приоритет | Тестов     |
| ------------ | ------------------------------------------------ | ----- | --------- | ---------- |
| **Handlers** | `telegram_bot/handlers/game_filters/handlers.py` | 287   | 🔥 ВЫСОКИЙ | 50+ тестов |
| **Utils**    | `telegram_bot/handlers/game_filters/utils.py`    | 47    | ⚡ СРЕДНИЙ | 15+ тестов |

**Детальный план для Game Filters Handlers - 50 тестов:**

| Категория               | Примеры тестов                                                                                        | Количество |
| ----------------------- | ----------------------------------------------------------------------------------------------------- | ---------- |
| **Выбор игр**           | `test_select_csgo_filter`, `test_select_dota2_filter`, `test_deselect_game`                           | 8          |
| **Применение фильтров** | `test_apply_filter_to_scan`, `test_apply_filter_to_arbitrage`, `test_clear_all_filters`               | 8          |
| **UI-меню**             | `test_show_game_filter_menu`, `test_update_menu_on_selection`, `test_menu_with_all_games_selected`    | 8          |
| **Persistence в БД**    | `test_save_game_filter_to_database`, `test_load_filters_from_database`, `test_update_existing_filter` | 10         |
| **Валидация**           | `test_validate_game_selection`, `test_validate_empty_selection`, `test_validate_invalid_game`         | 8          |
| **Edge Cases**          | `test_concurrent_filter_updates`, `test_database_error_handling`, `test_max_filters_limit`            | 8          |

#### 3.3 Notifications (9 файлов) - 75+ тестов

| Модуль              | Файл                                       | Строк | Приоритет | Тестов     |
| ------------------- | ------------------------------------------ | ----- | --------- | ---------- |
| **Digest Handler**  | `handlers/notification_digest_handler.py`  | 311   | 🔥 ВЫСОКИЙ | 40+ тестов |
| **Filters Handler** | `handlers/notification_filters_handler.py` | 259   | 🔥 ВЫСОКИЙ | 35+ тестов |
| **Checkers**        | `smart_notifications/checkers.py`          | 117   | ⚡ СРЕДНИЙ | 20+ тестов |
| **Senders**         | `smart_notifications/senders.py`           | 81    | ⚡ СРЕДНИЙ | 15+ тестов |
| **Utils**           | `smart_notifications/utils.py`             | 71    | ⚡ СРЕДНИЙ | 10+ тестов |

**Детальный план для Notification Digest Handler - 40 тестов:**

| Категория                 | Примеры тестов                                                                                            | Количество |
| ------------------------- | --------------------------------------------------------------------------------------------------------- | ---------- |
| **Создание дайджестов**   | `test_create_daily_digest`, `test_create_weekly_digest`, `test_create_monthly_digest`                     | 8          |
| **Обработка уведомлений** | `test_group_notifications_by_type`, `test_filter_duplicate_notifications`, `test_sort_by_priority`        | 8          |
| **Форматирование**        | `test_format_digest_with_multiple_items`, `test_format_empty_digest`, `test_format_digest_with_images`    | 8          |
| **Отправка**              | `test_send_digest_to_user`, `test_send_digest_to_multiple_users`, `test_handle_send_failure`              | 8          |
| **Edge Cases**            | `test_create_digest_empty_notifications`, `test_digest_with_max_size_exceeded`, `test_concurrent_digests` | 8          |

**Рекомендации по Telegram Handler тестам:**

- ✅ Мокировать **telegram.Update** и **telegram.ext.ContextTypes**
- ✅ Использовать **pytest-mock** для изоляции Telegram API вызовов
- ✅ Тестировать **callback query handlers** отдельно от command handlers
- ✅ Проверять **форматирование сообщений** и **inline keyboards**
- ✅ Тестировать **rate limiting** и **user authorization**
- ✅ Добавить **integration тесты** для полного flow (команда → обработка → ответ)

**Команды:**

```bash
# Создать директорию для тестов handlers
mkdir -p tests/telegram_bot/handlers/game_filters

# Запустить все тесты handlers
pytest tests/telegram_bot/handlers/ -v --cov=src/telegram_bot/handlers/

# Запустить только notification тесты
pytest tests/telegram_bot/handlers/ -k "notification" -v
```

---

### 4. Utils & Analytics (Приоритет: ⚡ СРЕДНИЙ)

**Итого:** ~780 строк без покрытия, ~115 тестов необходимо

| Модуль                 | Файл                                | Строк | Приоритет | Тестов     |
| ---------------------- | ----------------------------------- | ----- | --------- | ---------- |
| **Market Analytics**   | `src/utils/market_analytics.py`     | 224   | 🔥 ВЫСОКИЙ | 35+ тестов |
| **Reactive WebSocket** | `src/utils/reactive_websocket.py`   | 253   | ⚡ СРЕДНИЙ | 30+ тестов |
| **Batch Processor**    | `src/utils/batch_processor.py`      | 98    | ⚡ СРЕДНИЙ | 20+ тестов |
| **Price Sanity**       | `src/utils/price_sanity_checker.py` | 77    | ⚡ СРЕДНИЙ | 15+ тестов |
| **Trading Notifier**   | `src/utils/trading_notifier.py`     | 46    | 🟢 НИЗКИЙ  | 15+ тестов |

#### Детальный план тестирования Utils модулей

##### 4.1 Market Analytics (`src/utils/market_analytics.py`) - 35 тестов

| Категория         | Примеры тестов                                                                                  | Количество |
| ----------------- | ----------------------------------------------------------------------------------------------- | ---------- |
| **Анализ цен**    | `test_calculate_rsi_indicator`, `test_calculate_macd`, `test_bollinger_bands`                   | 8          |
| **Sanity Checks** | `test_price_sanity_check_valid`, `test_price_sanity_check_outlier`, `test_detect_price_anomaly` | 8          |
| **Тренды рынка**  | `test_detect_uptrend`, `test_detect_downtrend`, `test_sideways_market`                          | 6          |
| **Ликвидность**   | `test_calculate_liquidity_score`, `test_high_liquidity_item`, `test_low_liquidity_warning`      | 6          |
| **Edge Cases**    | `test_empty_price_history`, `test_insufficient_data_for_rsi`, `test_negative_prices`            | 7          |

**Пример теста для Market Analytics:**

```python
@pytest.mark.parametrize("prices,expected_trend", [
    ([10, 12, 14, 16, 18], "uptrend"),      # Восходящий тренд
    ([18, 16, 14, 12, 10], "downtrend"),    # Нисходящий тренд
    ([10, 11, 10, 11, 10], "sideways"),     # Боковой тренд
])
def test_detect_market_trend_various_scenarios(prices, expected_trend):
    """Тест определения тренда для различных ценовых паттернов."""
    # Arrange
    analyzer = MarketAnalytics()

    # Act
    trend = analyzer.detect_trend(prices)

    # Assert
    assert trend == expected_trend
```

##### 4.2 Reactive WebSocket (`src/utils/reactive_websocket.py`) - 30 тестов

| Категория               | Примеры тестов                                                                                        | Количество |
| ----------------------- | ----------------------------------------------------------------------------------------------------- | ---------- |
| **Подключение**         | `test_websocket_connect_success`, `test_websocket_reconnect_on_disconnect`, `test_connection_timeout` | 8          |
| **Обработка сообщений** | `test_receive_message_json`, `test_receive_message_binary`, `test_handle_malformed_message`           | 8          |
| **Observable паттерн**  | `test_subscribe_to_updates`, `test_unsubscribe_from_updates`, `test_notify_subscribers`               | 6          |
| **Обработка ошибок**    | `test_handle_connection_error`, `test_handle_message_error`, `test_exponential_backoff`               | 5          |
| **Edge Cases**          | `test_concurrent_subscriptions`, `test_max_reconnect_attempts`, `test_graceful_shutdown`              | 3          |

**Пример асинхронного теста для WebSocket:**

```python
@pytest.mark.asyncio
async def test_websocket_reconnect_after_disconnect():
    """Тест переподключения WebSocket после разрыва соединения."""
    # Arrange
    ws = ReactiveWebSocket(url="wss://test.com")
    reconnect_count = 0

    async def mock_connect():
        nonlocal reconnect_count
        reconnect_count += 1
        if reconnect_count == 1:
            raise ConnectionError("First attempt fails")
        return MagicMock()  # Successful connection

    ws._connect = mock_connect

    # Act
    await ws.connect()

    # Assert
    assert reconnect_count == 2, "Should reconnect after first failure"
    assert ws.is_connected is True
```

##### 4.3 Batch Processor (`src/utils/batch_processor.py`) - 20 тестов

| Категория                  | Примеры тестов                                                                       | Количество |
| -------------------------- | ------------------------------------------------------------------------------------ | ---------- |
| **Пакетная обработка**     | `test_process_batch_items`, `test_batch_size_limit`, `test_process_empty_batch`      | 6          |
| **Параллельная обработка** | `test_parallel_processing`, `test_concurrent_batches`, `test_thread_pool_size`       | 6          |
| **Обработка ошибок**       | `test_batch_partial_failure`, `test_retry_failed_items`, `test_max_retries_exceeded` | 5          |
| **Edge Cases**             | `test_single_item_batch`, `test_very_large_batch`, `test_processing_timeout`         | 3          |

##### 4.4 Price Sanity Checker (`src/utils/price_sanity_checker.py`) - 15 тестов

| Категория                | Примеры тестов                                                                           | Количество |
| ------------------------ | ---------------------------------------------------------------------------------------- | ---------- |
| **Валидация цен**        | `test_valid_price_range`, `test_price_too_low`, `test_price_too_high`                    | 5          |
| **Обнаружение аномалий** | `test_detect_price_spike`, `test_detect_price_drop`, `test_gradual_price_change`         | 5          |
| **Edge Cases**           | `test_zero_price`, `test_negative_price`, `test_extreme_price_values`, `test_null_price` | 5          |

**Команды:**

```bash
# Создать тесты для utils модулей
touch tests/utils/test_market_analytics.py
touch tests/utils/test_reactive_websocket.py
touch tests/utils/test_batch_processor.py

# Запустить все utils тесты
pytest tests/utils/ -v --cov=src/utils/ --cov-report=term-missing

# Запустить только асинхронные тесты
pytest tests/utils/ -m asyncio -v
```

---

## 📋 Общие рекомендации по тестированию

### Принципы FIRST

**Все тесты ДОЛЖНЫ следовать принципам FIRST:**

| Принцип                                 | Описание                                   | Реализация                                           |
| --------------------------------------- | ------------------------------------------ | ---------------------------------------------------- |
| **F**ast (Быстрые)                      | Тесты выполняются за миллисекунды          | Мокировать I/O, использовать in-memory БД            |
| **I**ndependent (Независимые)           | Каждый тест изолирован от других           | Использовать fixtures, очищать состояние после теста |
| **R**epeatable (Повторяемые)            | Одинаковые результаты в любом окружении    | Не зависеть от времени, сети, внешних API            |
| **S**elf-Validating (Самопроверяющиеся) | Автоматическая проверка через assert       | Четкие assert, без ручной проверки                   |
| **T**imely (Своевременные)              | Писать тесты до или сразу после реализации | TDD подход, тесты как часть DoD                      |

### AAA Паттерн (Arrange-Act-Assert)

**ВСЕГДА структурировать тесты по AAA паттерну:**

```python
@pytest.mark.asyncio
async def test_get_balance_returns_correct_value():
    """Тест проверяет корректный возврат баланса."""
    # Arrange (Подготовка) - настройка тестового окружения
    api_client = DMarketAPI(public_key="test", secret_key="test")
    mock_response = {"usd": "10000", "dmc": "5000"}

    # Act (Действие) - выполнение тестируемой функции
    with patch.object(api_client, '_request', return_value=mock_response):
        balance = await api_client.get_balance()

    # Assert (Проверка) - проверка результата
    assert balance["usd"] == "10000"
    assert balance["dmc"] == "5000"
```

### Именование тестов

**Формат:** `test_<функция>_<условие>_<ожидаемый_результат>`

**Примеры:**

```python
# ✅ Правильно - понятно что тестируется
def test_calculate_profit_with_zero_price_returns_zero()
def test_create_target_with_invalid_price_raises_validation_error()
def test_scan_arbitrage_when_no_items_returns_empty_list()

# ❌ Неправильно - неинформативно
def test_profit()
def test_target()
def test_scan()
```

### Изоляция и мокирование

**Правила мокирования:**

- ✅ **ВСЕГДА** мокировать внешние зависимости (API, БД, файловая система)
- ✅ Использовать `unittest.mock.AsyncMock` для async функций
- ✅ Использовать `pytest-mock` для удобного мокирования
- ✅ Использовать `httpx.MockTransport` для HTTP-запросов

**Примеры:**

```python
from unittest.mock import AsyncMock, patch, MagicMock

# Мокирование async функции
@pytest.mark.asyncio
async def test_api_call_with_mock():
    api_client = DMarketAPI(public_key="test", secret_key="test")
    api_client._request = AsyncMock(return_value={"status": "ok"})

    result = await api_client.get_balance()

    assert result["status"] == "ok"
    api_client._request.assert_called_once()

# Мокирование HTTP клиента
def test_http_client_with_mock_transport():
    def mock_handler(request):
        return httpx.Response(200, json={"balance": "1000"})

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(transport=transport)

    response = client.get("https://api.dmarket.com/balance")

    assert response.json()["balance"] == "1000"
```

### Параметризация тестов

**Использовать `@pytest.mark.parametrize` для множественных сценариев:**

```python
@pytest.mark.parametrize("price,commission,expected_profit", [
    (10.0, 7.0, 0.30),      # Стандартный случай
    (100.0, 7.0, 3.00),     # Высокая цена
    (0.50, 7.0, 0.015),     # Низкая цена
    (10.0, 0.0, 1.00),      # Без комиссии
])
def test_calculate_profit_various_scenarios(price, commission, expected_profit):
    """Проверка расчета прибыли для различных сценариев."""
    result = calculate_profit(
        buy_price=price,
        sell_price=price + 1.0,
        commission_percent=commission
    )
    assert abs(result - expected_profit) < 0.01  # Допуск для float
```

### Тестирование крайних случаев (Edge Cases)

**ВСЕГДА тестировать:**

- ✅ Нулевые и отрицательные значения
- ✅ Очень большие значения (max int, max float)
- ✅ Пустые коллекции ([], {}, "")
- ✅ None значения
- ✅ Граничные условия (min/max)
- ✅ Конкурентные вызовы
- ✅ Таймауты и сетевые ошибки

**Пример:**

```python
@pytest.mark.asyncio
async def test_create_target_with_edge_cases():
    """Тест проверяет обработку граничных случаев."""
    manager = TargetManager(api_client=mock_api)

    # Минимальная цена
    result = await manager.create_target("csgo", "Item", price=0.01)
    assert result["success"] is True

    # Максимальная цена
    result = await manager.create_target("csgo", "Item", price=10000.0)
    assert result["success"] is True

    # Нулевая цена (невалидно)
    with pytest.raises(ValidationError):
        await manager.create_target("csgo", "Item", price=0.0)

    # Отрицательная цена (невалидно)
    with pytest.raises(ValidationError):
        await manager.create_target("csgo", "Item", price=-5.0)

    # Пустое название
    with pytest.raises(ValidationError):
        await manager.create_target("csgo", "", price=10.0)
```

### Тестирование исключений

**Использовать `pytest.raises` для проверки исключений:**

```python
@pytest.mark.asyncio
async def test_api_call_handles_rate_limit_error():
    """Тест проверяет обработку ошибки rate limit."""
    api_client = DMarketAPI(public_key="test", secret_key="test")

    # Mock для симуляции 429 ошибки
    with patch.object(api_client, '_request') as mock_request:
        mock_request.side_effect = RateLimitError(
            message="Too many requests",
            retry_after=60
        )

        # Проверяем что исключение выбрасывается
        with pytest.raises(RateLimitError) as exc_info:
            await api_client.get_market_items("csgo")

        # Дополнительные проверки
        assert exc_info.value.retry_after == 60
        assert "Too many requests" in str(exc_info.value)
```

### Использование фикстур

**Переиспользование настроек через pytest fixtures:**

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_dmarket_api():
    """Фикстура для мокированного DMarket API клиента."""
    api = AsyncMock(spec=DMarketAPI)
    api.get_balance = AsyncMock(return_value={
        "usd": "10000",
        "dmc": "5000"
    })
    api.get_market_items = AsyncMock(return_value={
        "objects": [
            {"title": "Test Item", "price": {"USD": "1000"}}
        ]
    })
    return api

@pytest.fixture
async def test_database():
    """Фикстура для тестовой базы данных."""
    # Setup
    db = DatabaseManager("sqlite:///:memory:")
    await db.init_database()

    yield db  # Предоставляем БД тестам

    # Teardown
    await db.close()

# Использование фикстур
@pytest.mark.asyncio
async def test_user_creation(test_database):
    """Тест создания пользователя."""
    user = await test_database.create_user(
        telegram_id=123456789,
        username="test_user"
    )
    assert user.telegram_id == 123456789
    assert user.username == "test_user"
```

### Асинхронные тесты

**Использовать `@pytest.mark.asyncio` для async функций:**

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Тест асинхронной операции."""
    result = await async_function()
    assert result is not None

# Конфигурация в pytest.ini или pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # Автоматическое определение async тестов
```

### Анти-паттерны (ИЗБЕГАТЬ)

**❌ НЕ добавлять логику в тесты:**

```python
# НЕПРАВИЛЬНО - логика в тесте
def test_process_items():
    items = get_items()
    for item in items:  # Избегать циклов
        if item.price > 100:  # Избегать условий
            assert process(item) == "success"

# ПРАВИЛЬНО - простые, линейные тесты
def test_process_expensive_item():
    item = create_item(price=150)
    result = process(item)
    assert result == "success"
```

**❌ НЕ использовать магические числа:**

```python
# НЕПРАВИЛЬНО
def test_calculate():
    assert calculate(5, 10) == 50

# ПРАВИЛЬНО
def test_calculate_area_of_rectangle():
    width = 5
    height = 10
    expected_area = 50

    result = calculate(width, height)

    assert result == expected_area
```

**❌ НЕ тестировать несколько вещей в одном тесте:**

```python
# НЕПРАВИЛЬНО - слишком много проверок
def test_user_operations():
    user = create_user()
    assert user.id is not None
    assert user.name == "Test"
    assert update_user(user) is True
    assert delete_user(user) is True

# ПРАВИЛЬНО - разделить на отдельные тесты
def test_create_user_assigns_id():
    user = create_user()
    assert user.id is not None

def test_create_user_sets_name():
    user = create_user(name="Test")
    assert user.name == "Test"

def test_update_user_returns_success():
    user = create_user()
    result = update_user(user)
    assert result is True
```

---

## 🟡 Модули с низким покрытием (1-40%) - ОБНОВЛЕНО 25 декабря 2025

### ✅ УЛУЧШЕНО в этом PR

| Модуль                     | Файл                                         | Было     | Стало        | Статус      |
| -------------------------- | -------------------------------------------- | -------- | ------------ | ----------- |
| **Price Analyzer**         | `utils/price_analyzer.py`                    | 6.15%    | **85.77%** ✅ | ✅ ЗАВЕРШЕНО |
| **Market Alerts**          | `telegram_bot/market_alerts.py`              | 6.95%    | **73.62%** ✅ | ✅ ЗАВЕРШЕНО |
| **Trading Notifications**  | `telegram_bot/notifications/trading.py`      | 11.76%   | **90%+** ✅   | ✅ ЗАВЕРШЕНО |
| **Market Analytics**       | `utils/market_analytics.py`                  | 11.84%   | **90.13%** ✅ | ✅ ЗАВЕРШЕНО |
| **Daily Report Scheduler** | `utils/daily_report_scheduler.py`            | 12.03%   | **95.49%** ✅ | ✅ ЗАВЕРШЕНО |
| **Scanner Cache**          | `dmarket/scanner/cache.py`                   | 25.76%   | **90%+** ✅   | ✅ ЗАВЕРШЕНО |
| **Settings Handler**       | `telegram_bot/handlers/settings_handler.py`  | 28.89%   | **72.20%** ✅ | ✅ ЗАВЕРШЕНО |
| **Logging Utils**          | `utils/logging_utils.py`                     | 29.94%   | **87.08%** ✅ | ✅ ЗАВЕРШЕНО |
| **Arbitrage Handler**      | `telegram_bot/handlers/arbitrage_handler.py` | 32.22%   | **95.71%** ✅ | ✅ ЗАВЕРШЕНО |

### ✅ Все критические модули с низким покрытием теперь завершены!

**Статус:** Все модули из списка "низкого покрытия" теперь имеют покрытие 70%+

---

## 🟢 Модули с хорошим покрытием (60%+)

> **Эти модули имеют приемлемое покрытие, но его можно улучшить до 80%+**

| Модуль                             | Покрытие | Статус      |
| ---------------------------------- | -------- | ----------- |
| **Config**                         | 80.67%   | ✅ Отлично   |
| **Models (User)**                  | 76.19%   | ✅ Хорошо    |
| **Schemas**                        | 74.89%   | ✅ Хорошо    |
| **Game Filters**                   | 73.53%   | ✅ Хорошо    |
| **Arbitrage Scanner (новый)**      | 71.35%   | ✅ Хорошо    |
| **Targets**                        | 70.27%   | ✅ Хорошо    |
| **Models (Notification Settings)** | 66.67%   | ✅ Хорошо    |
| **Item Filters**                   | 61.11%   | ✅ Приемлемо |

---

## 📋 План действий на Q1 2026

### Неделя 1-2: DMarket API (🔥 КРИТИЧЕСКИЙ) - ✅ ЗАВЕРШЕНО

**Цель:** Покрыть 8 модулей API тестами (~190 тестов)

- [x] **client.py** - 57 тестов ✅ (HMAC auth, HTTP requests, rate limiting, retry logic) - 93.69%
- [x] **wallet.py** - 64 теста ✅ (balance, transactions, deposits, withdrawals) - 95.09%
- [x] **market.py** - 38 тестов ✅ (items, filters, pagination) - 83.54%
- [x] **trading.py** - 20 тестов ✅ (buy, sell, offers, cancellations) - 85.15%
- [x] **targets_api.py** - 20 тестов ✅ (create, delete, update targets) - 70.73%
- [x] **auth.py** - 20 тестов ✅ (authentication flow) - 89.55%
- [x] **cache.py** - 25 тестов ✅ (caching logic, TTL, eviction) - 95.71%
- [x] **inventory.py** - 27 тестов ✅ (inventory operations) - 96.00%

**Результат:** ✅ 0% → 87.5%+ покрытие API модулей ДОСТИГНУТО! (20 декабря 2025)

---

### Неделя 3-4: Arbitrage Module (🔥 КРИТИЧЕСКИЙ) - ✅ ХОРОШО ПОКРЫТ

**Цель:** Довести arbitrage.py до 80%+ покрытия (~60 тестов)

- [x] **arbitrage.py** - 644+ тестов ✅ (цель превышена!)
  - Инициализация сканера ✅
  - Сканирование уровней: boost, standard, medium, advanced, pro ✅
  - Расчет прибыли с различными комиссиями ✅
  - Фильтрация по прибыли/цене/игре/ликвидности ✅
  - Сортировка результатов ✅
  - Валидация opportunities ✅
  - Property-based тесты (Hypothesis) - инварианты прибыли ✅
  - Edge cases: нулевые цены, отрицательная прибыль, пустые результаты ✅

**Результат:** ✅ ~75% покрытие arbitrage.py ДОСТИГНУТО с 644+ тестами!

---

### Неделя 5-6: Telegram Handlers (⚡ ВЫСОКИЙ) - ✅ ЗАВЕРШЕНО (25 декабря 2025)

**Цель:** Покрыть основные handlers (~155 тестов)

**Статус:** ✅ **ЗАВЕРШЕНО** (531+ тестов добавлено)

- [x] **notification_digest_handler.py** - 58 тестов ✅ (было 13 падающих → все исправлены + новые)
  - ✅ Все 58 тестов проходят
  - ✅ Покрытие: 88.46%
  - ✅ Исправлена архитектура для работы с NotificationDigestManager

- [x] **notification_filters_handler.py** - 52 теста ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: 88.62%
  - ✅ NotificationFilters class полностью покрыт
  - ✅ Фильтры games, profit, levels, types
  - ✅ Menu display, toggle operations

- [x] **game_filters/handlers.py** - 28 тестов ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: 54.78%
  - ✅ handle_game_filters, handle_select_game_filter_callback
  - ✅ handle_price_range_callback, handle_float_range_callback
  - ✅ Category/rarity/exterior/hero/class handlers

- [x] **smart_notifications/checkers.py** - 16 тестов ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: 67.48%
  - ✅ check_price_alerts, check_market_opportunities
  - ✅ start_notification_checker

- [x] **smart_notifications/senders.py** - 17 тестов ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: 97.03%
  - ✅ send_price_alert_notification, send_market_opportunity_notification
  - ✅ notify_user

- [x] **smart_notifications/utils.py** - 40 тестов ✅ (НОВЫЙ ФАЙЛ)
  - ✅ get_market_data_for_items, get_item_by_id
  - ✅ get_market_items_for_game, get_price_history_for_items
  - ✅ get_item_price с error handling

- [x] **market_alerts.py** - 72 теста ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: 6.95% → **73.62%** (+66.67%)
  - ✅ MarketAlertsManager initialization, subscription management
  - ✅ Alert thresholds, background monitoring
  - ✅ Alert checks, sent alerts management, edge cases

- [x] **settings_handlers.py** - 26 тестов ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: 28.89% → **72.20%** (+43.31%)
  - ✅ Language settings, notification settings
  - ✅ API key management, theme settings, user preferences

- [x] **arbitrage_callback_impl.py** - 24 теста ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: ~32% → **95.71%** (+63%)
  - ✅ Arbitrage modes, games, pagination, error handling

**Результат:** ✅ 283+ тестов для Telegram Handlers, покрытие значительно улучшено!

---

### Неделя 7-8: Utils & Analytics (⚡ СРЕДНИЙ) - ✅ ЗАВЕРШЕНО (25 декабря 2025)

**Цель:** Улучшить покрытие утилит (~115 тестов)

**Статус:** ✅ **ЗАВЕРШЕНО** (248+ тестов добавлено)

- [x] **market_analytics.py** - 41 тест ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: 11.84% → **90.13%** (+78.29%)
  - ✅ MarketAnalytics class initialization
  - ✅ Price history analysis, trend detection
  - ✅ Volatility calculation, price predictions
  - ✅ Edge cases

- [x] **price_analyzer.py** - 35 тестов ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: 6.15% → **85.77%** (+79.62%)
  - ✅ calculate_price_trend (7 тестов)
  - ✅ find_undervalued_items (6 тестов)
  - ✅ analyze_supply_demand (6 тестов)
  - ✅ get_investment_recommendations (5 тестов)
  - ✅ get_investment_reason (11 тестов)

- [x] **batch_processor.py** - 47 тестов (14 было + 33 новых) ✅
  - ✅ Покрытие: ~40% → **80%+** (+40%)
  - ✅ process_with_concurrency тесты
  - ✅ ProgressTracker тесты
  - ✅ chunked_api_calls тесты

- [x] **reactive_websocket.py** - 49 тестов (32 было + 17 новых) ✅
  - ✅ Покрытие: ~50% → **70%+** (+20%)
  - ✅ Observable clear/error handling
  - ✅ Subscription class тесты
  - ✅ WebSocket initialization/stats

- [x] **daily_report_scheduler.py** - 33 теста ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: ~12% → **95.49%** (+83%)
  - ✅ Edge cases, error handling
  - ✅ Report formatting, scheduler operations

- [x] **logging_utils.py** - 39 тестов ✅ (НОВЫЙ ФАЙЛ)
  - ✅ Покрытие: ~30% → **87.08%** (+57%)
  - ✅ BotLogger class тесты
  - ✅ Setup functions, Sentry integration
  - ✅ Log formatting

**Результат:** ✅ 248+ тестов для Utils & Analytics, все модули достигли 70%+ покрытия!

---

## 🛠️ Инструменты и команды

### Запуск тестов с покрытием

```bash
# Все тесты с покрытием
pytest --cov=src --cov-report=html --cov-report=term-missing

# Конкретный модуль
pytest tests/dmarket/api/test_client.py --cov=src/dmarket/api/client.py --cov-report=term

# С подробным выводом
pytest -v --cov=src --cov-report=html

# Только unit тесты
pytest tests/unit/ --cov=src

# Только integration тесты
pytest tests/integration/ --cov=src
```

### Анализ покрытия

```bash
# Сгенерировать HTML отчет
pytest --cov=src --cov-report=html
# Открыть в браузере: htmlcov/index.html

# JSON отчет
pytest --cov=src --cov-report=json
# Файл: coverage.json

# Только файлы с покрытием < 60%
pytest --cov=src --cov-report=term-missing --cov-fail-under=60
```

### Проверка качества кода

```bash
# Ruff линтинг
ruff check src/ tests/

# MyPy проверка типов
mypy src/

# Форматирование Black
black src/ tests/

# Все проверки разом
ruff check src/ && mypy src/ && black --check src/
```

---

## 📚 Примеры тестов

### Пример 1: Тест API клиента

```python
import pytest
from unittest.mock import AsyncMock
from src.dmarket.api.client import DMarketClient


@pytest.mark.asyncio
async def test_client_get_balance_returns_valid_data():
    """Тест получения баланса через API клиент."""
    # Arrange
    client = DMarketClient(public_key="test", secret_key="test")
    mock_response = {"usd": "10000", "dmc": "5000"}

    # Mock HTTP request
    client._request = AsyncMock(return_value=mock_response)

    # Act
    balance = await client.get_balance()

    # Assert
    assert balance["usd"] == "10000"
    assert balance["dmc"] == "5000"
    client._request.assert_called_once()
```

### Пример 2: Тест арбитража

```python
import pytest
from src.dmarket.arbitrage import ArbitrageScanner


@pytest.mark.parametrize("buy,sell,expected_profit", [
    (10.0, 15.0, 3.95),   # Стандартная прибыль
    (100.0, 120.0, 11.60), # Высокая цена
    (1.0, 1.5, 0.395),    # Низкая цена
])
def test_calculate_profit_various_scenarios(buy, sell, expected_profit):
    """Тест расчета прибыли для различных сценариев."""
    # Arrange
    scanner = ArbitrageScanner()

    # Act
    profit = scanner.calculate_profit(
        buy_price=buy,
        sell_price=sell,
        commission=7.0
    )

    # Assert
    assert abs(profit - expected_profit) < 0.01
```

### Пример 3: Тест Telegram handler

```python
import pytest
from telegram import Update
from unittest.mock import AsyncMock, MagicMock
from src.telegram_bot.commands.balance_command import balance_command


@pytest.mark.asyncio
async def test_balance_command_shows_correct_balance(mock_update, mock_context):
    """Тест команды /balance отображает правильный баланс."""
    # Arrange
    mock_update.message = MagicMock()
    mock_update.effective_user = MagicMock(id=123)
    mock_context.bot_data = {"api": AsyncMock()}
    mock_context.bot_data["api"].get_balance = AsyncMock(
        return_value={"USD": "100.50", "DMC": "50.25"}
    )

    # Act
    await balance_command(mock_update, mock_context)

    # Assert
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "$100.50" in call_args
```

---

## 🎯 Метрики успеха

### Количественные

- ✅ **70%+ общее покрытие** (Q1 2026)
- ✅ **80%+ покрытие критических модулей** (Q2 2026)
- ✅ **60%+ покрытие веток** (Q1 2026)
- ✅ **500+ новых тестов** (Q1 2026)

### Качественные

- ✅ Все тесты следуют **AAA паттерну**
- ✅ Описательные имена тестов
- ✅ Тестирование edge cases
- ✅ Использование фикстур
- ✅ Изоляция тестов

---

## 📊 Прогноз достижения 70%

| Период          | Фокус                  | Прирост | Итого        |
| --------------- | ---------------------- | ------- | ------------ |
| **До PR**       | -                      | -       | **60.09%**   |
| Недели 1-2      | DMarket API            | +4-5%   | 64-65% ✅     |
| Недели 3-4      | Arbitrage              | +2-3%   | 66-68% ✅     |
| **Недели 5-6**  | **Handlers + Utils**   | **+5%** | **65%+** ✅   |
| **25.12.2025**  | **PR с 531+ тестами**  | **+5%** | **~65-68%** ✅|
| Q1 2026         | E2E + Integration      | +2-3%   | **70%+** 🎯  |

**✅ Цель 65%+ достигнута! Осталось ~105 тестов для 70%**

---

## ✅ РЕЗУЛЬТАТЫ PR (25 декабря 2025)

### Добавленные тесты по модулям

| Модуль | Файл тестов | Тестов | Покрытие До | Покрытие После |
|--------|-------------|--------|-------------|----------------|
| notification_digest_handler | test_notification_digest_handler.py | 58 | ~30% | **88.46%** |
| notification_filters_handler | test_notification_filters_handler.py | 52 | 0% | **88.62%** |
| smart_notifications/checkers | test_checkers.py | 16 | 0% | **67.48%** |
| smart_notifications/senders | test_senders.py | 17 | 0% | **97.03%** |
| smart_notifications/utils | test_utils.py | 40 | 0% | ~70% |
| game_filters/handlers | test_handlers.py | 28 | 0% | **54.78%** |
| market_alerts | test_market_alerts_manager.py | 72 | 6.95% | **73.62%** |
| price_analyzer | test_price_analyzer.py | 35 | 6.15% | **85.77%** |
| market_analytics | test_market_analytics_extended.py | 41 | 11.84% | **90.13%** |
| settings_handlers | test_settings_handlers_extended.py | 26 | 28.89% | **72.20%** |
| batch_processor | test_batch_processor.py | +33 | ~40% | **80%+** |
| reactive_websocket | test_reactive_websocket.py | +17 | ~50% | **70%+** |
| daily_report_scheduler | test_daily_report_scheduler_extended.py | 33 | ~12% | **95.49%** |
| logging_utils | test_logging_utils_bot_logger.py | 39 | ~30% | **87.08%** |
| arbitrage_callback_impl | test_arbitrage_callback_impl_extended.py | 24 | ~32% | **95.71%** |
| **notifications/trading** | **test_trading.py** | **34** | **11.76%** | **90%+** |
| **scanner/cache** | **test_cache.py** | **42** | **25.76%** | **90%+** |

**ИТОГО: 607+ новых тестов**

### Ключевые улучшения покрытия

| Модуль | Улучшение |
|--------|-----------|
| `daily_report_scheduler.py` | +83.46% (12% → 95.49%) |
| `price_analyzer.py` | +79.62% (6.15% → 85.77%) |
| `notifications/trading.py` | +78.24% (11.76% → 90%+) |
| `market_analytics.py` | +78.29% (11.84% → 90.13%) |
| `market_alerts.py` | +66.67% (6.95% → 73.62%) |
| `scanner/cache.py` | +64.24% (25.76% → 90%+) |
| `arbitrage_callback_impl.py` | +63.49% (32% → 95.71%) |
| `logging_utils.py` | +57.14% (30% → 87.08%) |
| `settings_handlers.py` | +43.31% (28.89% → 72.20%) |
| `batch_processor.py` | +40% (40% → 80%+) |
| `reactive_websocket.py` | +20% (50% → 70%+) |

---

## 📊 Анализ существующих тестов

### Текущее состояние (197 тестовых файлов, ~2356 тестов)

| Категория             | Файлов | Тестов | Статус                 | Рекомендации                   |
| --------------------- | ------ | ------ | ---------------------- | ------------------------------ |
| **DMarket API**       | 9      | 239    | ✅ Хорошее покрытие     | Улучшить edge cases            |
| **Arbitrage**         | 9      | 347    | ✅ Отличное покрытие    | Добавить integration тесты     |
| **Telegram Handlers** | 13     | 245    | ⚡ Среднее покрытие     | Требуется расширение           |
| **Utils**             | 31     | 664    | ✅ Хорошее покрытие     | Улучшить async тесты           |
| **Property-Based**    | 3      | ~20    | ✅ Хорошее начало       | Расширить Hypothesis стратегии |
| **Integration**       | 11     | ~150   | ⚡ Требует расширения   | Добавить full workflow тесты   |
| **E2E**               | 2      | ~30    | ⚡ Минимальное покрытие | Критически важно расширить     |
| **Contract (Pact)**   | 4      | 43     | ✅ Реализовано          | Поддерживать актуальность      |

### Качественный анализ

#### ✅ Сильные стороны

1. **API Module (`tests/dmarket/api/`)** - 239 тестов
   - ✅ Хорошее покрытие client.py (57 тестов)
   - ✅ Отличное покрытие wallet.py (54 теста)
   - ✅ Property-based тесты присутствуют (9 тестов)
   - ✅ Следуют AAA паттерну
   - ✅ Используют фикстуры правильно

2. **Arbitrage Module** - 347 тестов
   - ✅ Множественные файлы покрывают разные аспекты
   - ✅ Хорошие parametrized тесты
   - ✅ Property-based тесты с Hypothesis

3. **Utils Module** - 900+ тестов (было 664)
   - ✅ Широкое покрытие утилит
   - ✅ Хорошие async тесты
   - ✅ Тесты для rate limiters, cache, circuit breaker
   - ✅ **НОВОЕ:** market_analytics (41 тест), price_analyzer (35 тестов)
   - ✅ **НОВОЕ:** batch_processor (+33), reactive_websocket (+17)
   - ✅ **НОВОЕ:** daily_report_scheduler (33), logging_utils (39)

4. **Telegram Handlers** - 500+ тестов (было 245) ✅ ЗНАЧИТЕЛЬНО УЛУЧШЕНО
   - ✅ **НОВОЕ:** notification_digest_handler (58 тестов)
   - ✅ **НОВОЕ:** notification_filters_handler (52 теста)
   - ✅ **НОВОЕ:** game_filters/handlers (28 тестов)
   - ✅ **НОВОЕ:** smart_notifications (73 теста)
   - ✅ **НОВОЕ:** market_alerts (72 теста)
   - ✅ **НОВОЕ:** settings_handlers (26 тестов)
   - ✅ **НОВОЕ:** arbitrage_callback_impl (24 теста)

#### ⚠️ Области для улучшения (оставшиеся)

1. **Trading Notifications** - требует тестирования
   - ⚠️ `telegram_bot/notifications/trading.py` (~11.76% покрытия)
   - 📝 Рекомендуется добавить 15+ тестов

2. **Scanner Cache** - требует расширения
   - ⚠️ `dmarket/scanner/cache.py` (~25.76% покрытия)
   - 📝 Рекомендуется добавить 10+ тестов

3. **Integration и E2E тесты** - можно улучшить
   - ⚠️ Добавить больше full workflow тестов
   - ⚠️ Расширить E2E покрытие

### ✅ Модули с нулевым покрытием - УСТРАНЕНО (25 декабря 2025)

Все критические модули теперь имеют тесты:
- ✅ `src/telegram_bot/handlers/notification_digest_handler.py` - **58 тестов** (было 0)
- ✅ `src/telegram_bot/handlers/notification_filters_handler.py` - **52 теста** (было 0)
- ✅ `src/telegram_bot/smart_notifications/checkers.py` - **16 тестов** (было 0)
- ✅ `src/telegram_bot/smart_notifications/senders.py` - **17 тестов** (было 0)
- ✅ `src/telegram_bot/smart_notifications/utils.py` - **40 тестов** (было 0)

### Конкретные рекомендации по улучшению существующих тестов

#### 1. test_balance_command.py (существует, ~20 тестов)

**Добавить недостающие тесты:**

```python
# Отсутствуют тесты для:
- test_balance_command_concurrent_calls()  # Конкурентные вызовы
- test_balance_command_with_large_balance()  # Очень большие суммы
- test_balance_command_with_zero_balance()  # Нулевой баланс
- test_balance_command_rate_limit_exceeded()  # Превышение rate limit
- test_balance_command_with_malformed_api_response()  # Некорректный ответ API
- test_balance_command_timeout_handling()  # Таймаут запроса
- test_balance_command_unauthorized_user()  # Неавторизованный пользователь
- test_balance_command_with_missing_api_keys()  # Отсутствующие ключи
- test_balance_command_formatting_edge_cases()  # Форматирование граничных значений
- test_balance_command_retry_on_temporary_failure()  # Повторная попытка
```

**Цель:** Добавить 10 тестов для достижения 90%+ покрытия

#### 2. test_client.py (57 тестов, хорошо)

**Улучшить существующие тесты:**

```python
# Добавить property-based тесты:
@given(st.integers(min_value=1, max_value=1000))
def test_client_handles_various_timeouts(timeout):
    """Property: клиент корректно обрабатывает любые таймауты."""
    # Тест с Hypothesis

# Добавить тесты для граничных условий:
- test_client_with_max_retry_attempts()  # Максимальное количество попыток
- test_client_with_very_long_request_url()  # Очень длинный URL
- test_client_with_unicode_in_request_body()  # Unicode в теле запроса
- test_client_connection_pool_exhaustion()  # Исчерпание пула соединений
```

**Цель:** Добавить 4-5 тестов для 95%+ покрытия

#### 3. test_arbitrage.py (существует, но требует расширения)

**Создать новый файл test_arbitrage_edge_cases.py:**

```python
"""Edge cases для модуля арбитража."""

class TestArbitrageEdgeCases:
    """Граничные случаи арбитража."""

    @pytest.mark.asyncio
    async def test_arbitrage_with_zero_buy_price(self):
        """Тест арбитража при нулевой цене покупки."""
        # Проверка обработки некорректных данных

    @pytest.mark.asyncio
    async def test_arbitrage_with_negative_profit(self):
        """Тест арбитража при отрицательной прибыли."""
        # Должен отфильтровать

    @pytest.mark.asyncio
    async def test_arbitrage_with_extreme_commission(self):
        """Тест арбитража при экстремальных комиссиях (99%)."""
        # Граничное условие

    @pytest.mark.asyncio
    async def test_arbitrage_concurrent_scans(self):
        """Тест конкурентного сканирования нескольких игр."""
        # Параллельное выполнение
```

**Цель:** Создать файл с 15+ edge case тестами

#### 4. Создать test_notification_digest_handler.py (НОВЫЙ ФАЙЛ)

```python
"""
Тесты для notification_digest_handler.py - КРИТИЧЕСКИ ВАЖНО

Этот файл полностью отсутствует! Требуется создать 40+ тестов.
"""

class TestNotificationDigestCreation:
    """Тесты создания дайджестов."""

    @pytest.mark.asyncio
    async def test_create_daily_digest_with_multiple_notifications(self):
        """Тест создания дневного дайджеста с несколькими уведомлениями."""
        # Arrange: 10 уведомлений разных типов
        # Act: создать дайджест
        # Assert: корректное группирование и форматирование

    @pytest.mark.asyncio
    async def test_create_weekly_digest_aggregates_correctly(self):
        """Тест агрегации недельного дайджеста."""
        # Тест агрегации за неделю

    @pytest.mark.asyncio
    async def test_digest_with_empty_notifications(self):
        """Тест дайджеста без уведомлений."""
        # Edge case: пустой список

class TestNotificationDigestFormatting:
    """Тесты форматирования дайджестов."""

    def test_format_digest_with_html_special_chars(self):
        """Тест экранирования HTML символов."""
        # Тест безопасности

    def test_format_digest_exceeds_telegram_limit(self):
        """Тест разбивки на несколько сообщений при превышении лимита."""
        # Telegram limit: 4096 символов
```

**Цель:** Создать файл с 40 тестами (согласно плану)

#### 5. Создать test_game_filters_extended.py

**Расширить покрытие game_filters/handlers.py:**

```python
"""
Расширенные тесты для game_filters.

Добавить тесты для сложных сценариев взаимодействия фильтров.
"""

class TestGameFiltersPersistence:
    """Тесты сохранения фильтров в БД."""

    @pytest.mark.asyncio
    async def test_save_filters_handles_database_error(self):
        """Тест обработки ошибки БД при сохранении."""
        # Mock database error
        # Проверить graceful handling

    @pytest.mark.asyncio
    async def test_load_filters_with_corrupted_data(self):
        """Тест загрузки при поврежденных данных."""
        # Edge case: некорректные данные в БД

    @pytest.mark.asyncio
    async def test_concurrent_filter_updates_race_condition(self):
        """Тест race condition при конкурентных обновлениях."""
        # Критический тест для многопоточности

class TestGameFiltersUI:
    """Тесты UI взаимодействия."""

    @pytest.mark.asyncio
    async def test_filter_menu_updates_after_selection(self):
        """Тест обновления меню после выбора."""
        # Проверка корректности UI состояния

    @pytest.mark.asyncio
    async def test_filter_menu_with_all_games_selected(self):
        """Тест меню когда выбраны все игры."""
        # Граничное условие
```

**Цель:** Добавить 30 тестов для расширенного покрытия

### Приоритетный список улучшений (Top 10) - ОБНОВЛЕНО 25 декабря 2025

| Приоритет | Файл/Модуль                               | Было тестов | Сейчас тестов | Статус       |
| --------- | ----------------------------------------- | ----------- | ------------- | ------------ |
| 1         | `test_notification_digest_handler.py`     | **13 падающих** | **58** ✅  | ✅ ЗАВЕРШЕНО |
| 2         | `test_notification_filters_handler.py`    | **0**       | **52** ✅      | ✅ ЗАВЕРШЕНО |
| 3         | `test_smart_notifications_checkers.py`    | **0**       | **16** ✅      | ✅ ЗАВЕРШЕНО |
| 4         | `test_smart_notifications_senders.py`     | **0**       | **17** ✅      | ✅ ЗАВЕРШЕНО |
| 5         | `test_smart_notifications_utils.py`       | **0**       | **40** ✅      | ✅ ЗАВЕРШЕНО |
| 6         | `test_game_filters_handlers.py`           | **0**       | **28** ✅      | ✅ ЗАВЕРШЕНО |
| 7         | `test_market_alerts_manager.py`           | **0**       | **72** ✅      | ✅ ЗАВЕРШЕНО |
| 8         | `test_price_analyzer.py`                  | **0**       | **35** ✅      | ✅ ЗАВЕРШЕНО |
| 9         | `test_market_analytics_extended.py`       | **0**       | **41** ✅      | ✅ ЗАВЕРШЕНО |
| 10        | `test_settings_handlers_extended.py`      | **0**       | **26** ✅      | ✅ ЗАВЕРШЕНО |

**Дополнительные тесты (сверх плана):**

| Файл/Модуль                               | Тестов | Статус       |
| ----------------------------------------- | ------ | ------------ |
| `test_batch_processor.py` (расширение)    | +33    | ✅ ЗАВЕРШЕНО |
| `test_reactive_websocket.py` (расширение) | +17    | ✅ ЗАВЕРШЕНО |
| `test_daily_report_scheduler_extended.py` | +33    | ✅ ЗАВЕРШЕНО |
| `test_logging_utils_bot_logger.py`        | +39    | ✅ ЗАВЕРШЕНО |
| `test_arbitrage_callback_impl_extended.py`| +24    | ✅ ЗАВЕРШЕНО |
| **`test_trading.py`**                     | **+34** | ✅ ЗАВЕРШЕНО |
| **`test_cache.py` (scanner)**             | **+42** | ✅ ЗАВЕРШЕНО |

**Итого добавлено в этом PR:** 607+ тестов ✅

---

## 🎯 Следующие приоритеты (Q1 2026)

### Высокий приоритет

| Приоритет | Файл/Модуль                               | Текущие тесты | Нужно тестов   | Критичность   |
| --------- | ----------------------------------------- | ------------- | -------------- | ------------- |
| ~~1~~     | ~~`test_trading_notifications.py`~~       | ~~34~~        | ~~35~~         | ✅ ЗАВЕРШЕНО   |
| ~~2~~     | ~~`test_scanner_cache.py`~~               | ~~42~~        | ~~45~~         | ✅ ЗАВЕРШЕНО   |
| ~~3~~     | ~~`test_balance_command.py` (расширить)~~ | ~~31~~        | ~~30~~         | ✅ ЗАВЕРШЕНО   |
| ~~4~~     | ~~E2E workflow тесты (расширить)~~        | ~~26~~        | ~~40~~         | ✅ ЗАВЕРШЕНО   |
| ~~5~~     | ~~Integration тесты (расширить)~~         | ~~21~~        | ~~20~~         | ✅ ЗАВЕРШЕНО   |

**Итого осталось:** ✅ 0 тестов - ВСЕ ЦЕЛИ ДОСТИГНУТЫ!

---

## 📊 Сводная таблица необходимых тестов

### По модулям

| Категория             | Модулей | Тестов   | Приоритет     | Срок         |
| --------------------- | ------- | -------- | ------------- | ------------ |
| **DMarket API**       | 8       | ~190     | 🔥 КРИТИЧЕСКИЙ | Недели 1-2   |
| **Arbitrage**         | 1       | ~60      | 🔥 КРИТИЧЕСКИЙ | Недели 3-4   |
| **Telegram Handlers** | 5+      | ~155     | ⚡ ВЫСОКИЙ     | Недели 5-6   |
| **Utils & Analytics** | 5       | ~115     | ⚡ СРЕДНИЙ     | Недели 7-8   |
| **ИТОГО**             | **19+** | **520+** | -             | **8 недель** |

### Детализация по категориям

#### 1. DMarket API Modules (~190 тестов)

| Модуль         | Тестов | Категории                                                              |
| -------------- | ------ | ---------------------------------------------------------------------- |
| client.py      | 40     | Init (5), HMAC (8), HTTP (10), Rate Limit (6), Retry (8), Edge (5)     |
| wallet.py      | 25     | Balance (5), Transactions (5), Deposits (5), Withdrawals (5), Edge (5) |
| market.py      | 30     | Items (8), Pagination (6), Filters (10), Edge (6)                      |
| trading.py     | 25     | Buy (8), Sell (8), Offers (6), Edge (3)                                |
| targets_api.py | 20     | Create (7), Get (5), Update (4), Delete (4)                            |
| auth.py        | 15     | Authentication flow                                                    |
| cache.py       | 20     | Caching logic, TTL, eviction                                           |
| inventory.py   | 15     | Inventory operations                                                   |

#### 2. Arbitrage Module (~60 тестов)

| Категория      | Тестов | Описание                                                     |
| -------------- | ------ | ------------------------------------------------------------ |
| Инициализация  | 5      | Создание сканера с различными параметрами                    |
| Сканирование   | 10     | 5 уровней арбитража (boost, standard, medium, advanced, pro) |
| Расчет прибыли | 8      | Различные сценарии с комиссиями                              |
| Фильтрация     | 10     | По прибыли, цене, игре, ликвидности                          |
| Сортировка     | 5      | По различным критериям                                       |
| Валидация      | 8      | Проверка корректности opportunities                          |
| Property-Based | 9      | Hypothesis тесты для инвариантов                             |
| Edge Cases     | 5      | Граничные условия                                            |

#### 3. Telegram Handlers (~155 тестов)

| Модуль                          | Тестов | Категории                                                       |
| ------------------------------- | ------ | --------------------------------------------------------------- |
| balance_command.py              | 30     | Command (5), Format (5), UI (5), Errors (5), Rate (5), Edge (5) |
| game_filters/handlers.py        | 50     | Select (8), Apply (8), UI (8), DB (10), Validate (8), Edge (8)  |
| notification_digest_handler.py  | 40     | Create (8), Process (8), Format (8), Send (8), Edge (8)         |
| notification_filters_handler.py | 35     | Управление фильтрами уведомлений                                |

#### 4. Utils & Analytics (~115 тестов)

| Модуль                | Тестов | Категории                                                       |
| --------------------- | ------ | --------------------------------------------------------------- |
| market_analytics.py   | 35     | Prices (8), Sanity (8), Trends (6), Liquidity (6), Edge (7)     |
| price_analyzer.py     | 30     | Анализ паттернов, аномалии, edge cases                          |
| batch_processor.py    | 20     | Batch (6), Parallel (6), Errors (5), Edge (3)                   |
| reactive_websocket.py | 30     | Connect (8), Messages (8), Observable (6), Errors (5), Edge (3) |

### По приоритетам

| Приоритет     | Тестов   | Модулей | % от общего |
| ------------- | -------- | ------- | ----------- |
| 🔥 КРИТИЧЕСКИЙ | ~250     | 9       | 48%         |
| ⚡ ВЫСОКИЙ     | ~155     | 5       | 30%         |
| ⚡ СРЕДНИЙ     | ~115     | 5       | 22%         |
| **ИТОГО**     | **520+** | **19+** | **100%**    |

### По типам тестов

| Тип теста             | Количество | Примечания                                           |
| --------------------- | ---------- | ---------------------------------------------------- |
| **Unit тесты**        | ~450       | Основная масса, изолированные тесты                  |
| **Property-Based**    | ~20        | Hypothesis тесты для инвариантов                     |
| **Параметризованные** | ~50        | @pytest.mark.parametrize для множественных сценариев |
| **Async тесты**       | ~200       | @pytest.mark.asyncio для async функций               |
| **Edge Cases**        | ~50        | Граничные условия и аномальные ситуации              |

---

## 🔗 Полезные ссылки

### Документация проекта

- `docs/testing_guide.md` - Руководство по тестированию
- `docs/code_quality_tools_guide.md` - Инструменты качества
- `docs/CONTRACT_TESTING.md` - Контрактное тестирование
- `CONTRIBUTING.md` - Как помочь проекту

### Внешние ресурсы

- [pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Testing asyncio code](https://pytest-asyncio.readthedocs.io/)
- [Hypothesis property-based testing](https://hypothesis.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

## 🆕 PHASE 2: Расширенные методы тестирования (Q1-Q2 2026)

### 📊 Анализ текущих видов тестирования

| Тип тестирования | Статус | Текущее количество | Рекомендуется | Приоритет |
|------------------|--------|-------------------|---------------|-----------|
| **Unit тесты** | ✅ Реализовано | 2800+ тестов | ✅ Достаточно | - |
| **Integration тесты** | ✅ Реализовано | 150+ тестов | ✅ Хорошо | - |
| **E2E/Системные тесты** | ✅ Реализовано | 30+ тестов | ✅ Хорошо | - |
| **Property-Based тесты** | ✅ Реализовано | 20+ тестов | +30 тестов | ⚡ СРЕДНИЙ |
| **Contract тесты (Pact)** | ✅ Реализовано | 43 теста | ✅ Хорошо | - |
| **Smoke тесты** | ✅ Реализовано | 10+ тестов | ✅ Достаточно | - |
| **Regression тесты** | ✅ Реализовано | 15+ тестов | ✅ Хорошо | - |
| **Performance тесты** | ⚠️ Минимально | 5 тестов | +25 тестов | 🔥 ВЫСОКИЙ |
| **Security тесты** | ⚠️ Частично | 10 тестов | +20 тестов | 🔥 ВЫСОКИЙ |
| **Fuzz тесты** | ❌ Отсутствует | 0 тестов | +15 тестов | ⚡ СРЕДНИЙ |
| **Load тесты** | ❌ Отсутствует | 0 тестов | +10 тестов | ⚡ СРЕДНИЙ |
| **Acceptance (BDD)** | ❌ Отсутствует | 0 тестов | +20 сценариев | 🟢 НИЗКИЙ |

### 🔥 Новые виды тестирования для внедрения

#### 1. Performance/Load тесты (Приоритет: 🔥 ВЫСОКИЙ) - 35 тестов

**Инструменты:** `pytest-benchmark`, `locust`, `k6`

```python
# tests/performance/test_api_performance.py
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

@pytest.mark.benchmark
def test_arbitrage_scan_performance(benchmark):
    """Тест производительности сканирования арбитража."""
    result = benchmark(scanner.scan_level, "standard", "csgo")
    assert len(result) >= 0
    # Ожидание: < 500ms для стандартного уровня

@pytest.mark.benchmark  
def test_price_calculation_performance(benchmark):
    """Тест производительности расчета цен."""
    result = benchmark(calculator.calculate_profit, 10.0, 15.0, 7.0)
    assert result > 0
    # Ожидание: < 1ms на расчет
```

**План тестов:**
| Категория | Тестов | Описание |
|-----------|--------|----------|
| API Response Time | 10 | Время ответа различных API endpoints |
| Scan Performance | 8 | Производительность сканирования по уровням |
| Cache Performance | 7 | Производительность кэширования |
| Database Performance | 5 | Производительность запросов к БД |
| Memory Usage | 5 | Потребление памяти при нагрузке |

#### 2. Security тесты (Приоритет: 🔥 ВЫСОКИЙ) - 20 тестов

**Инструменты:** `bandit`, `safety`, `pytest-security`

```python
# tests/security/test_api_security.py
import pytest

class TestAPIKeySecurity:
    """Тесты безопасности API ключей."""
    
    def test_api_key_not_logged(self):
        """API ключ не должен попадать в логи."""
        # Проверка отсутствия ключей в логах
        
    def test_api_key_encryption_at_rest(self):
        """API ключ должен быть зашифрован в БД."""
        # Проверка шифрования
        
    def test_sql_injection_prevention(self):
        """Защита от SQL-инъекций."""
        malicious_inputs = ["'; DROP TABLE users;--", "1 OR 1=1"]
        for input in malicious_inputs:
            with pytest.raises(ValidationError):
                process_user_input(input)
```

**План тестов:**
| Категория | Тестов | Описание |
|-----------|--------|----------|
| API Key Security | 5 | Защита API ключей |
| Input Validation | 5 | Валидация входных данных |
| SQL Injection | 3 | Защита от SQL-инъекций |
| XSS Prevention | 3 | Защита от XSS |
| Rate Limiting | 4 | Тесты rate limiting |

#### 3. Fuzz тесты (Приоритет: ⚡ СРЕДНИЙ) - 15 тестов

**Инструменты:** `hypothesis`, `atheris`

```python
# tests/fuzz/test_fuzz_inputs.py
from hypothesis import given, strategies as st
import atheris

@given(st.binary(min_size=1, max_size=1000))
def test_parse_item_data_fuzz(data):
    """Fuzz тест парсинга данных предмета."""
    try:
        parse_item_data(data)
    except (ValueError, TypeError):
        pass  # Ожидаемые исключения
    # Не должно быть краша или утечки памяти

@given(st.floats(allow_nan=True, allow_infinity=True))
def test_price_calculation_fuzz(price):
    """Fuzz тест расчета цен с экстремальными значениями."""
    try:
        calculate_price(price)
    except ValueError:
        pass  # Ожидаемое исключение для невалидных цен
```

**План тестов:**
| Категория | Тестов | Описание |
|-----------|--------|----------|
| JSON Parsing | 5 | Fuzz парсинга JSON |
| Price Calculations | 4 | Fuzz расчетов цен |
| Filter Inputs | 3 | Fuzz входных фильтров |
| API Responses | 3 | Fuzz обработки ответов API |

#### 4. Расширенные Property-Based тесты (Приоритет: ⚡ СРЕДНИЙ) - 30 тестов

**Инструменты:** `hypothesis`

```python
# tests/property_based/test_invariants.py
from hypothesis import given, strategies as st, assume

@given(
    items=st.lists(st.dictionaries(
        keys=st.sampled_from(["price", "title", "game"]),
        values=st.one_of(st.floats(min_value=0.01), st.text())
    ), min_size=0, max_size=100)
)
def test_filter_preserves_subset_invariant(items):
    """Property: фильтрация всегда возвращает подмножество."""
    filtered = filter_items(items, min_price=1.0)
    assert len(filtered) <= len(items)
    assert all(item in items for item in filtered)

@given(
    balance=st.floats(min_value=0, max_value=1000000),
    price=st.floats(min_value=0.01, max_value=100000)
)
def test_purchase_never_exceeds_balance(balance, price):
    """Property: покупка никогда не превышает баланс."""
    assume(price <= balance)
    result = simulate_purchase(balance, price)
    assert result.remaining_balance >= 0
```

**План тестов:**
| Категория | Тестов | Описание |
|-----------|--------|----------|
| Arbitrage Invariants | 10 | Инварианты арбитража |
| Price Invariants | 8 | Инварианты цен |
| Filter Invariants | 7 | Инварианты фильтров |
| State Invariants | 5 | Инварианты состояния |

#### 5. Acceptance/BDD тесты (Приоритет: 🟢 НИЗКИЙ) - 20 сценариев

**Инструменты:** `behave`, `pytest-bdd`

```gherkin
# features/arbitrage.feature
Feature: Arbitrage Scanning
  As a trader
  I want to scan for arbitrage opportunities
  So that I can make profit

  Scenario: Successful scan on standard level
    Given I have valid API credentials
    And I select "csgo" game
    When I scan "standard" level
    Then I should see opportunities with profit > 5%
    And each opportunity should have buy and sell prices

  Scenario: No opportunities found
    Given I have valid API credentials
    And market conditions are unfavorable
    When I scan "boost" level
    Then I should see empty results
    And receive a message "No opportunities found"
```

### 📋 Итого новых тестов для Phase 2

| Тип | Тестов | Срок | Приоритет |
|-----|--------|------|-----------|
| Performance | 35 | Q1 2026 | 🔥 ВЫСОКИЙ |
| Security | 20 | Q1 2026 | 🔥 ВЫСОКИЙ |
| Fuzz | 15 | Q1 2026 | ⚡ СРЕДНИЙ |
| Property-Based | 30 | Q2 2026 | ⚡ СРЕДНИЙ |
| BDD/Acceptance | 20 | Q2 2026 | 🟢 НИЗКИЙ |
| **ИТОГО** | **120** | **6 месяцев** | - |

---

## 🔧 РЕКОМЕНДАЦИИ ПО РЕФАКТОРИНГУ

### Модули требующие рефакторинга

| Модуль | Файл | Проблема | Рекомендация |
|--------|------|----------|--------------|
| **Arbitrage Tests** | `tests/dmarket/test_arbitrage*.py` | 9 файлов, 6184 строк - много дублирования | Консолидировать в 3 файла: basic, advanced, properties |
| **DMarket API** | `src/dmarket/dmarket_api.py` | Устаревший модуль, дублирует `api/client.py` | Удалить, использовать `api/client.py` |
| **Utils** | `src/utils/analytics.py` | Дублирует функционал `market_analytics.py` | Объединить в один модуль |
| **Filters** | `src/dmarket/filters/` | Пустая директория с `__init__.py` | Удалить или использовать |
| **User Profiles** | `src/telegram_bot/user_profiles.json` | Хардкод данных в JSON | Перенести в БД |

### Рекомендуемая структура тестов после рефакторинга

```
tests/
├── unit/                    # Юнит-тесты (изолированные)
│   ├── dmarket/
│   │   ├── api/
│   │   ├── arbitrage/
│   │   └── scanner/
│   ├── telegram_bot/
│   └── utils/
├── integration/             # Интеграционные тесты
├── e2e/                     # End-to-End тесты
├── performance/             # Тесты производительности (НОВОЕ)
├── security/                # Тесты безопасности (НОВОЕ)
├── fuzz/                    # Fuzz тесты (НОВОЕ)
├── property_based/          # Property-based тесты
├── contracts/               # Contract тесты (Pact)
├── smoke/                   # Smoke тесты
└── regression/              # Regression тесты
```

---

## 🗑️ МОДУЛИ И ФАЙЛЫ ДЛЯ УДАЛЕНИЯ

### ⚠️ ВАЖНО: Корректировка списка (25 декабря 2025)

После анализа кодовой базы выяснилось:

**НЕ подлежат удалению (активно используются):**
| Файл/Папка | Причина НЕ удалять | Использований |
|------------|-------------------|---------------|
| ~~`src/dmarket/dmarket_api.py`~~ | **ОСНОВНОЙ модуль API** - используется в 20+ файлах | 20+ imports |
| ~~`src/dmarket/filters/`~~ | **НЕ пустая** - содержит `game_filters.py` | Активно используется |
| ~~`anytool/`~~ | **Активный MCP интеграционный модуль** | MCP integration |

**Кандидаты на удаление (после проверки):**

| Файл/Папка | Причина | Связанные тесты | Статус |
|------------|---------|-----------------|--------|
| `src/utils/analytics.py` | Возможно дублирует `market_analytics.py` | Нужна проверка | ⚠️ Требует анализа |
| `src/telegram_bot/user_profiles.json` | Хардкод данных | Нет тестов | ⚠️ Требует анализа |

**ВАЖНО:** 
1. **`dmarket_api.py` - ОСНОВНОЙ модуль**, используется в:
   - `src/main.py`
   - `src/utils/websocket_client.py`
   - `src/utils/trading_notifier.py`
   - `src/utils/price_analyzer.py`
   - `src/dmarket/arbitrage/` (3 файла)
   - И еще 15+ файлов
   
2. **`anytool/` - Активный MCP модуль** с:
   - `anytool/config/config_mcp.json` - конфигурация MCP
   - `src/utils/anytool_integration.py` - интеграционный код (305 строк)
   - `tests/unit/test_anytool_integration.py` - тесты
   - `docs/ANYTOOL_INTEGRATION_GUIDE.md` - документация

3. **`filters/` - НЕ пустая директория**, содержит:
   - `game_filters.py` - 10175 строк функционального кода

### Процедура проверки перед удалением

**ВАЖНО:** Перед удалением ЛЮБОГО модуля:
1. **Проверить использование:** `grep -r "import module_name" src/ tests/`
2. Проверить что функционал перенесен в другие модули
3. Удалить связанные тесты
4. Обновить импорты во всех файлах
5. Запустить полный тестовый набор

```bash
# Проверка использования dmarket_api.py (20+ imports - НЕ УДАЛЯТЬ!)
grep -r "from src.dmarket.dmarket_api import" src/ tests/

# Проверка использования analytics.py (0 imports - можно удалить)
grep -r "from src.utils.analytics import" src/ tests/
```

---

## 📊 Сводная таблица Phase 2

### Новые тесты (120+ тестов)

| Категория | Q1 2026 | Q2 2026 | Итого | Статус |
|-----------|---------|---------|-------|--------|
| Security | 23 | - | 23 | ✅ ЗАВЕРШЕНО (tests/security/test_api_key_security.py) |
| Performance | 20 | - | 20 | ✅ ЗАВЕРШЕНО (tests/performance/test_benchmarks.py) |
| Fuzz | 12 | - | 12 | ✅ ЗАВЕРШЕНО (tests/property_based/test_fuzz_inputs.py) |
| Property-Based | 14 | - | 14 | ✅ ЗАВЕРШЕНО (tests/property_based/test_arbitrage_properties.py) |
| BDD/Acceptance | 18 | - | 18 | ✅ ЗАВЕРШЕНО (tests/bdd/test_bdd_scenarios.py) |
| **Итого** | **87** | **0** | **87** | ✅ ВСЕ ЗАВЕРШЕНО |

### Рефакторинг тестов (сокращение дублирования)

| До рефакторинга | После рефакторинга | Экономия |
|-----------------|-------------------|----------|
| 9 файлов arbitrage | 3 файла | -6 файлов |
| 6184 строк | ~3000 строк | -3184 строк |

### Удаление устаревших модулей

⚠️ **КОРРЕКТИРОВКА:** После анализа кодовой базы:

| Модуль | Строк кода | Статус | Примечание |
|--------|-----------|--------|------------|
| ~~`dmarket_api.py`~~ | 115838 | **НЕ УДАЛЯТЬ** ❌ | **ОСНОВНОЙ модуль** - 20+ imports |
| `analytics.py` | ~18307 | ⚠️ Требует проверки | Возможно дублирует `market_analytics.py` |
| ~~`anytool/`~~ | - | **НЕ УДАЛЯТЬ** ❌ | **Активный MCP модуль** |
| ~~`filters/`~~ | - | **НЕ УДАЛЯТЬ** ❌ | Содержит `game_filters.py` |

**Итог:** Только `analytics.py` может быть кандидатом на удаление после тщательного анализа.

---

## ✅ Phase 2 Progress (25 декабря 2025)

### Добавленные тесты Phase 2

| Файл | Тестов | Категория | Статус |
|------|--------|-----------|--------|
| `tests/security/test_api_key_security.py` | 23 | Security | ✅ ВСЕ ПРОХОДЯТ |
| `tests/performance/test_benchmarks.py` | 20 | Performance | ✅ ВСЕ ПРОХОДЯТ |
| `tests/performance/conftest.py` | - | Config | ✅ Добавлен для async |
| `tests/property_based/test_fuzz_inputs.py` | 12 | Fuzz | ✅ ВСЕ ПРОХОДЯТ |
| `tests/property_based/test_arbitrage_properties.py` | 14 | Property-Based | ✅ ВСЕ ПРОХОДЯТ |
| `tests/bdd/test_bdd_scenarios.py` | 18 | BDD/Acceptance | ✅ ВСЕ ПРОХОДЯТ |
| **Итого Phase 2** | **87** | - | ✅ ВСЕ 87 ПРОХОДЯТ |

### Security тесты (23 теста) ✅ ВСЕ ПРОХОДЯТ
- ✅ API key not logged (4 теста)
- ✅ API key encryption (2 теста)
- ✅ Input validation - SQL injection (5 тестов)
- ✅ Input validation - XSS prevention (3 теста)
- ✅ Command injection prevention (1 тест)
- ✅ Rate limiting (2 теста)
- ✅ Secure randomness (2 теста)
- ✅ Authentication security (2 теста)
- ✅ Sensitive data handling (2 теста)

### Performance тесты (20 тестов) ✅ ВСЕ ПРОХОДЯТ
**Требования:** `pytest-benchmark`, `pytest-asyncio`
- ✅ Price calculation (3 теста)
- ✅ Cache performance (3 теста)
- ✅ Filtering performance (2 теста)
- ✅ Sorting performance (2 теста)
- ✅ Pagination performance (2 теста)
- ✅ String operations (2 теста)
- ✅ JSON performance (2 теста)
- ✅ Async performance (2 теста)
- ✅ Memory efficiency (2 теста)

### Property-Based/Fuzz тесты (26 тестов) ✅ ВСЕ ПРОХОДЯТ
- ✅ Fuzz inputs (12 тестов): price parsing, item data, API response, balance, game ID, arbitrage, targets, filters
- ✅ Arbitrage properties (14 тестов): profit calculation, price validation, commission, edge cases, invariants

### BDD/Acceptance тесты (18 сценариев) ✅ ВСЕ ПРОХОДЯТ
**Расположение:** `tests/bdd/`
- ✅ Arbitrage Scanning (5 сценариев)
  - Successful scan on standard level
  - No opportunities on boost level
  - Scan multiple games simultaneously
  - Filter by minimum profit
  - Filter by price range
- ✅ Balance Management (4 сценария)
  - Check balance successfully
  - Check balance with zero funds
  - Handle API error gracefully
  - Balance updates after purchase
- ✅ Trading Operations (4 сценария)
  - Successful item purchase
  - Purchase fails insufficient balance
  - Successful item listing
  - Cancel active listing
- ✅ Notification Management (5 сценариев)
  - Enable price alert notifications
  - Set price drop alert
  - Receive notification on price drop
  - Disable all notifications
  - Configure digest frequency

---

**Версия:** 8.0 (Phase 3 - Roadmap to 80% Coverage)
**Последнее обновление:** 25 декабря 2025 г.
**Статус:** 🟢 Phase 1 завершена (640+ тестов), Phase 2 ЗАВЕРШЕНА (87 тестов) - ВСЕГО 727+ тестов
**Текущее покрытие:** ~70%
**Целевое покрытие:** 80%

---

## 🎯 PHASE 3: Достижение 80% покрытия (Q1-Q2 2026)

### 📊 Анализ модулей с 0% покрытием (всего ~3100 строк)

**Для достижения 80% покрытия необходимо добавить ~1000 новых тестов**

### 🔥 Высокий приоритет (Критические модули - 0% покрытия)

#### 1. Telegram Bot Handlers (0% покрытия) - ~400 тестов

| Модуль | Строк | Тестов | Приоритет | Срок |
|--------|-------|--------|-----------|------|
| `market_analysis_handler.py` | 334 | 80 | ✅ **ЗАВЕРШЕНО** | 25.12.2025 |
| `sales_analysis_handlers.py` | 98 | 25 | ✅ **ЗАВЕРШЕНО** | 25.12.2025 |
| `intramarket_arbitrage_handler.py` | 151 | 40 | ✅ **ЗАВЕРШЕНО** | 26.12.2025 |
| `dmarket_status.py` | 69 | 20 | ✅ **ЗАВЕРШЕНО** | 26.12.2025 |
| `scanner_handler.py` | 183 | 45 | ✅ **ЗАВЕРШЕНО** | ранее |
| `settings_handlers.py` | 169 | 40 | ✅ **ЗАВЕРШЕНО** | ранее |
| `target_handler.py` | 92 | 35 | ✅ **ЗАВЕРШЕНО** | 26.12.2025 |
| `liquidity_settings_handler.py` | 127 | 51 | ✅ **ЗАВЕРШЕНО** | 26.12.2025 |
| `rate_limit_admin.py` | 125 | 41 | ✅ **ЗАВЕРШЕНО** | 26.12.2025 |
| `backtest_handler.py` | 95 | 36 | ✅ **ЗАВЕРШЕНО** | 26.12.2025 |
| `dashboard_handler.py` | 250 | 39 | ✅ **ЗАВЕРШЕНО** | 26.12.2025 |
| `portfolio_handler.py` | 149 | 37 | ✅ **ЗАВЕРШЕНО** | 26.12.2025 |

**✅ market_analysis_handler.py - ЗАВЕРШЕНО (25 декабря 2025):**
- 64 теста добавлено
- Покрытие всех функций: command, callback, pagination, period/risk change
- Edge cases и error handling

**✅ sales_analysis_handlers.py - ЗАВЕРШЕНО (25 декабря 2025):**
- 41 тест добавлено  
- Покрытие всех функций форматирования и callbacks

**✅ rate_limit_admin.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 41 тест добавлено (NEW)
- Покрытие: is_admin, rate_limit_stats_command, rate_limit_reset_command
- rate_limit_whitelist_command (add/remove/check), rate_limit_config_command
- Admin authorization, rate limiter не настроен, error handling
- Stats formatting: low/medium/high usage indicators

**✅ intramarket_arbitrage_handler.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 41 тест добавлено
- Покрытие: formatting, pagination, callbacks, edge cases
- Тесты для всех типов: UNDERPRICED, TRENDING_UP, RARE_TRAITS

**✅ dmarket_status.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 27 тестов (8 базовых + 19 расширенных)
- Покрытие: edge cases, balance display, error messages, troubleshooting
- Тесты HTML parse mode и chat actions

**✅ target_handler.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 35 тестов (существовало ранее + расширено)
- Покрытие: target menu, smart targets, competition analysis
- Callback handlers и error handling

**✅ liquidity_settings_handler.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 51 тест (NEW)
- Покрытие: settings CRUD, toggle, reset, value input processing
- Edge cases и boundary validation

**✅ backtest_handler.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 36 тестов (NEW)
- Покрытие: BacktestHandler initialization, set_api
- handle_backtest_command: days parsing, min/max limits, invalid days, keyboard display
- handle_callback: results, settings, balance change
- _run_backtest: no API, loading message, error handling
- _display_result: positive/negative profit, statistics display
- _show_results: empty results, with results
- Edge cases: float precision balance, zero balance, large balance

**✅ dashboard_handler.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 39 тестов (NEW)
- Покрытие: ScannerDashboard initialization
- add_scan_result: single, multiple, history limit, timestamp
- get_user_stats: empty, single scan, multiple scans, filter by user
- mark_scan_active/complete: timestamps, replace previous
- get_dashboard_keyboard: markup structure, buttons
- format_stats_message: zero stats, with data, time formatting (just now, minutes, hours, days)
- get_scanner_control_keyboard: with/without level, back button
- Dashboard callbacks: query handling, message handling
- Edge cases: empty opportunities, missing profit key, negative profit, large history

**✅ portfolio_handler.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 37 тестов (NEW)
- Покрытие: PortfolioHandler initialization, set_api
- handle_portfolio_command: no message, no user, summary display, keyboard
- handle_callback: details, performance, risk, diversification, sync, update_prices, back, remove
- handle_add_item_id: no message, no user_data, no text, invalid format, valid format, success message
- _format_summary: empty portfolio, with data
- Edge cases: whitespace handling, item ID generation, case insensitive game, comma in name, zero/large price

**Детальный план:**

```python
# tests/telegram_bot/handlers/test_market_analysis_handler.py (~80 тестов)
- test_handle_price_analysis_command (8 тестов)
- test_handle_trend_analysis_command (8 тестов)
- test_handle_volatility_analysis (8 тестов)
- test_handle_rsi_macd_analysis (10 тестов)
- test_handle_support_resistance_levels (8 тестов)
- test_format_analysis_message (10 тестов)
- test_handle_analysis_callback (10 тестов)
- test_error_handling (10 тестов)
- test_rate_limiting (8 тестов)

# tests/telegram_bot/handlers/test_scanner_handler.py (~45 тестов)
- test_start_scan_command (8 тестов)
- test_scan_by_level (10 тестов - boost, standard, medium, advanced, pro)
- test_scan_by_game (8 тестов - csgo, dota2, tf2, rust)
- test_scan_results_formatting (8 тестов)
- test_scan_pagination (5 тестов)
- test_scan_error_handling (6 тестов)
```

#### 2. Smart Notifications - ~120 тестов (✅ ЗАВЕРШЕНО 26.12.2025)

| Модуль | Строк | Тестов | Приоритет | Статус |
|--------|-------|--------|-----------|--------|
| `checkers.py` | 117 | 16 | 🔥 ВЫСОКИЙ | ✅ ЗАВЕРШЕНО |
| `senders.py` | 81 | 17 | 🔥 ВЫСОКИЙ | ✅ ЗАВЕРШЕНО |
| `utils.py` | 71 | 40 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО |
| `handlers.py` | 56 | 18 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО (NEW) |
| `preferences.py` | 53 | 23 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО (NEW) |
| `alerts.py` | 38 | 14 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО (NEW) |

**✅ handlers.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 18 тестов добавлено (NEW)
- Покрытие: handle_notification_callback (12 тестов)
- register_notification_handlers (4 теста)
- Edge cases (2 теста)

**✅ preferences.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 23 теста добавлено (NEW)
- Покрытие: get/set user preferences, load/save operations
- Register user, update preferences, get_user_prefs
- Edge cases: special characters, concurrent updates

**✅ alerts.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 14 тестов добавлено (NEW)
- Покрытие: create_alert, deactivate_alert, get_user_alerts
- UUID uniqueness, timestamp validation, initial state

#### 3. Analytics Module (0% покрытия) - ~120 тестов

| Модуль | Строк | Тестов | Приоритет |
|--------|-------|--------|-----------|
| `backtester.py` | 210 | 46 | ✅ **ЗАВЕРШЕНО** 26.12.2025 |
| `historical_data.py` | 136 | 46 | ✅ **ЗАВЕРШЕНО** 26.12.2025 |

**✅ backtester.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 46 тестов добавлено (NEW)
- Покрытие: Trade, Position, BacktestResult dataclasses
- SimpleArbitrageStrategy buy/sell logic
- Backtester run, metrics calculation (drawdown, sharpe)
- Integration tests для полных trading cycles

**✅ historical_data.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 46 тестов добавлено (NEW)
- Покрытие: PricePoint, PriceHistory dataclasses
- HistoricalDataCollector: collect_price_history, collect_batch
- Cache management: cache_hit, cache_bypass, clear_cache, get_cache_stats
- API parsing: sales_history, aggregated_prices, timestamp formats
- Edge cases: unicode titles, large prices, special characters

#### 4. Portfolio Module (0% покрытия) - ~60 тестов

| Модуль | Строк | Тестов | Приоритет |
|--------|-------|--------|-----------|
| `analyzer.py` | 182 | 42 | ✅ **ЗАВЕРШЕНО** 26.12.2025 |

**✅ analyzer.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 42 теста добавлено (NEW)
- Покрытие: ConcentrationRisk, DiversificationReport, RiskReport dataclasses
- PortfolioAnalyzer: analyze_diversification, analyze_risk
- get_top_performers, get_worst_performers
- Private methods: _calculate_distribution, _calculate_volatility_score
- _calculate_liquidity_score, _calculate_concentration_score
- _find_high_risk_items, _generate_diversification_recommendations
- Edge cases: very large portfolio, extreme price differences

#### 5. DMarket API (0% покрытия) - ~40 тестов (✅ ЗАВЕРШЕНО 26.12.2025)

| Модуль | Строк | Тестов | Приоритет | Статус |
|--------|-------|--------|-----------|--------|
| `api/auth.py` | 55 | 25 | 🔥 ВЫСОКИЙ | ✅ ЗАВЕРШЕНО (existing) |
| `api/cache.py` | 46 | 25 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО (existing) |
| `liquidity_rules.py` | 27 | 37 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО (NEW) |

**✅ api/auth.py - ЗАВЕРШЕНО (existing):**
- 25 тестов (уже существовали)
- Покрытие: generate_signature_ed25519 (6 тестов)
- _convert_secret_key (4 теста) - HEX, Base64, long HEX, unknown format
- generate_signature_hmac (4 теста) - with/without body, timestamp, hexdigest
- Edge cases (3 теста) - special chars, unicode, different methods
- Additional API tests (8 тестов)

**✅ api/cache.py - ЗАВЕРШЕНО (existing):**
- 25 тестов (уже существовали)
- Покрытие: get_cache_key (6 тестов) - simple, params, data, consistency
- is_cacheable (7 тестов) - short/medium/long TTL, POST not cacheable
- save_to_cache/get_from_cache (6 тестов) - basic, TTL types
- clear_cache operations (4 тестов) - all, by endpoint
- Edge cases (2 теста) - unknown TTL, overwrite, empty data

**✅ liquidity_rules.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 37 тестов добавлено (NEW)
- Покрытие: LiquidityRules dataclass (4 теста)
- Preset rules: CONSERVATIVE, BALANCED, AGGRESSIVE (6 тестов)
- LIQUIDITY_SCORE_WEIGHTS (4 теста)
- LIQUIDITY_THRESHOLDS (2 теста)
- LIQUIDITY_RECOMMENDATIONS (4 теста)
- get_liquidity_category (10 тестов) - boundary tests
- get_liquidity_recommendation (7 тестов)

#### 6. Pagination & Callbacks - ~100 тестов (✅ ЗАВЕРШЕНО 26.12.2025)

| Модуль | Строк | Тестов | Приоритет | Статус |
|--------|-------|--------|-----------|--------|
| `pagination.py` | 132 | 23 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО (ранее) |
| `sales_analysis_callbacks.py` | 236 | 44 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО (NEW) |

**✅ pagination.py - ЗАВЕРШЕНО (ранее):**
- 23 теста
- Покрытие: PaginationManager initialization, add_items, get_page
- Page navigation (next/prev), items_per_page settings
- Filter and sort, get_mode, clear_user_data
- Pagination keyboard, format_current_page

**✅ sales_analysis_callbacks.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 44 теста добавлено (NEW)
- Покрытие: handle_sales_history_callback (8 тестов)
- handle_liquidity_callback (6 тестов)
- handle_refresh_sales_callback (4 теста)
- handle_refresh_liquidity_callback (2 теста)
- handle_all_arbitrage_sales_callback (5 тестов)
- handle_refresh_arbitrage_sales_callback (3 теста)
- handle_setup_sales_filters_callback (4 теста)
- handle_all_volume_stats_callback (4 теста)
- handle_refresh_volume_stats_callback (3 теста)
- price_trend_to_text helper (5 тестов)
- Edge cases, error handling, API errors

#### 7. Utils Module (0% покрытия) - ~60 тестов (✅ ЗАВЕРШЕНО 26.12.2025)

| Модуль | Строк | Тестов | Приоритет | Статус |
|--------|-------|--------|-----------|--------|
| `performance.py` | 76 | 55 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО (36 existing + 19 NEW) |
| `rate_limit_decorator.py` | 34 | 10 | ⚡ СРЕДНИЙ | ✅ ЗАВЕРШЕНО (existing) |
| `prometheus_server.py` | 38 | 17 | 🟢 НИЗКИЙ | ✅ ЗАВЕРШЕНО (existing) |

**✅ prometheus_server.py - ЗАВЕРШЕНО (existing):**
- 17 тестов (уже существовали)
- Покрытие: PrometheusServer class (12 тестов)
  - init (default/custom port), routes configured
  - metrics_handler, health_handler
  - start/stop server, lifecycle
- run_prometheus_server (2 теста) - cancellation, custom port
- Integration tests (2 теста) - full lifecycle, bytes content
- Edge cases (1 тест) - multiple instances, idempotent stop

**✅ performance.py - ЗАВЕРШЕНО (26 декабря 2025):**
- 55 тестов (36 existing + 19 NEW)
- Покрытие: AdvancedCache (36 тестов) - invalidate, clear_all, get_stats
- cached decorator (6 тестов) - sync/async functions, custom key
- profile_performance decorator (6 тестов) - logging, exception handling
- AsyncBatch (9 тестов) - concurrency, ordering, error handling
- GlobalCache (3 теста) - singleton pattern

---

### 📋 Сводная таблица Phase 3

| Категория | Модулей | Строк | Тестов | Срок |
|-----------|---------|-------|--------|------|
| Telegram Handlers | 9 | 1348 | 400 | Q1 2026 |
| Smart Notifications | 6 | 416 | 120 | Q1 2026 |
| Analytics | 2 | 346 | 120 | Q1 2026 |
| Portfolio | 1 | 182 | 60 | Q2 2026 |
| DMarket API | 3 | 128 | 40 | Q2 2026 |
| Pagination/Callbacks | 2 | 368 | 100 | Q2 2026 |
| Utils | 4 | 168 | 60 | Q2 2026 |
| **ИТОГО** | **27** | **2956** | **~900** | **6 месяцев** |

---

### ⏰ Временная шкала Phase 3

| Неделя | Фокус | Тестов | Целевое покрытие |
|--------|-------|--------|------------------|
| 1-2 | Telegram Handlers (часть 1) | 200 | 72% |
| 3-4 | Telegram Handlers (часть 2) | 200 | 74% |
| 5-6 | Smart Notifications | 120 | 76% |
| 7-8 | Analytics + Portfolio | 180 | 78% |
| 9-10 | DMarket API + Utils | 100 | 79% |
| 11-12 | Pagination + Final | 100 | **80%** |

---

### ✅ Arbitrage Test Consolidation (ЗАВЕРШЕНО)

#### Было:
- 9 файлов, 6184 строк в `tests/dmarket/test_arbitrage*.py`

#### Стало (консолидировано):
- `test_arbitrage_consolidated.py` - основные unit тесты (объединены из basic, extended, advanced)
- `test_arbitrage_scanner.py` - тесты сканера (оставлен как есть)
- `test_arbitrage_properties.py` - property-based тесты (перенесены в property_based/)

#### Экономия:
- -6 файлов
- ~-3000 строк (дубликаты удалены)
- 364 теста сохранены

---

### 🎯 Оставшиеся оптимизационные задачи

#### 1. Консолидация arbitrage тестов (✅ АНАЛИЗ ЗАВЕРШЕН)

**Текущее состояние:**
- 9 файлов, 6184 строк в `tests/dmarket/test_arbitrage*.py`
- 364 теста

**Рекомендация для консолидации:**
| Исходные файлы | Целевой файл | Действие |
|----------------|--------------|----------|
| test_arbitrage.py (2100 строк) | test_arbitrage.py | Оставить как основной |
| test_arbitrage_scanner.py (1133 строки) | test_arbitrage_scanner.py | Оставить |
| test_arbitrage_basic.py (400 строк) | → test_arbitrage.py | Объединить |
| test_arbitrage_extended.py (545 строк) | → test_arbitrage.py | Объединить |
| test_arbitrage_advanced.py (280 строк) | → test_arbitrage.py | Объединить |
| test_arbitrage_additional.py (260 строк) | → test_arbitrage.py | Объединить |
| test_arbitrage_sales_analysis.py (400 строк) | test_arbitrage_sales_analysis.py | Оставить |
| test_arbitrage_scanner_extended.py (840 строк) | → test_arbitrage_scanner.py | Объединить |
| test_arbitrage_scanner_new.py (300 строк) | → test_arbitrage_scanner.py | Объединить |

**Результат консолидации:**
- 9 файлов → 3 файла
- 6184 строк → ~3500 строк (дубликаты удалены)
- 364 теста сохранены

#### 2. Анализ `analytics.py` (✅ ЗАВЕРШЕНО - НЕ ДУБЛИКАТ)

**Результат анализа:**
- `src/utils/analytics.py` (18307 байт) - **Chart Generation** (matplotlib, seaborn)
- `src/utils/market_analytics.py` (отдельный) - **Market Analysis** (numpy, statistics)

**Вывод:** Модули имеют **РАЗНОЕ назначение** и НЕ дублируют друг друга.

---

### 📊 Итоговый статус проекта

| Фаза | Тестов | Статус | Примечание |
|------|--------|--------|------------|
| **Phase 1** | 640+ | ✅ ЗАВЕРШЕНО | Все критические модули 70%+ |
| **Phase 2** | 87 | ✅ ЗАВЕРШЕНО | Security, Performance, BDD |
| **Phase 3** | ~900 (план) | 🔄 В ПРОЦЕССЕ | Roadmap to 80% coverage |
| **ИТОГО** | **727+ (текущих)** | 🎯 **Цель: 1627+** | 80% покрытие |

---

### 🏆 Приоритеты для немедленного выполнения

**Топ-5 модулей для тестирования (наибольший impact на покрытие):**

1. **`market_analysis_handler.py`** (334 строки, 80 тестов) - 🔥 КРИТИЧЕСКИЙ
2. **`backtester.py`** (210 строки, 55 тестов) - 🔥 КРИТИЧЕСКИЙ
3. **`scanner_handler.py`** (183 строки, 45 тестов) - 🔥 КРИТИЧЕСКИЙ
4. **`portfolio/analyzer.py`** (182 строки, 60 тестов) - 🔥 КРИТИЧЕСКИЙ
5. **`settings_handlers.py`** (169 строк, 40 тестов) - 🔥 ВЫСОКИЙ

**Примечание:** Эти 5 модулей составляют ~1078 строк кода. Покрытие их тестами даст значительный прирост общего покрытия (~+5-7%).

---

## 📚 DOCUMENTATION REVIEW (25 декабря 2025)

### 📊 Анализ документации (.md файлов)

**Всего файлов документации:** 26

### 🔴 Высокий приоритет (требуют обновления)

| Файл | Проблема | Рекомендация | Приоритет |
|------|----------|--------------|-----------|
| `docs/testing_guide.md` | Версия 3.0, не отражает Phase 2 тесты | Обновить до версии 4.0, добавить секции Security/Performance/BDD | 🔥 КРИТИЧЕСКИЙ |
| `docs/README.md` | Версия 5.0, устаревшая структура тестов (2348 тестов) | Обновить до 727+ тестов, добавить Phase 2 | 🔥 КРИТИЧЕСКИЙ |
| `README.md` | Версия 4.0, устаревшие данные о тестах | Синхронизировать с docs/README.md | 🔥 ВЫСОКИЙ |
| `CHANGELOG.md` | Нет записи о Phase 2 тестах | Добавить запись о 727+ тестах, Phase 2 | 🔥 ВЫСОКИЙ |

### 🤖 GitHub Agents и Copilot (`.github/` директория)

> **⚠️ Важно:** Файлы в `.github/agents/` требуют особого внимания для корректной работы Copilot

| Файл | Описание | Рекомендация | Приоритет |
|------|----------|--------------|-----------|
| `.github/agents/ProjectPlan.agent.md` | Конфигурация Copilot Agent | Обновить цели покрытия: 70% → 80% | 🔥 ВЫСОКИЙ |
| `.github/copilot-instructions.md` | Инструкции для Copilot | Добавить Phase 3 приоритеты, обновить TESTING_PRIORITIES.md ссылки | 🔥 ВЫСОКИЙ |
| `.github/ISSUE_TEMPLATE/copilot-task.md` | Шаблон задач для Copilot | Добавить тип "testing" с Phase 3 контекстом | ⚡ СРЕДНИЙ |
| `.github/pull_request_template.md` | Шаблон PR | Обновить checklist с Phase 2/3 требованиями | ⚡ СРЕДНИЙ |

**План обновления `.github/` файлов (Неделя 1-2):**
1. [ ] Обновить `.github/agents/ProjectPlan.agent.md` - обновить цели покрытия
2. [ ] Обновить `.github/copilot-instructions.md` - добавить Phase 3 информацию
3. [ ] Обновить `.github/ISSUE_TEMPLATE/copilot-task.md` - добавить testing тип
4. [ ] Обновить `.github/pull_request_template.md` - обновить checklist

### ⚡ Средний приоритет (рекомендуется обновление)

| Файл | Проблема | Рекомендация | Приоритет |
|------|----------|--------------|-----------|
| `docs/ARCHITECTURE.md` | Версия 4.0, нет секции тестирования | Добавить раздел о тестовой архитектуре | ⚡ СРЕДНИЙ |
| `docs/CONTRIBUTING.md` | Версия 3.0, 80% coverage требование неточно | Обновить требования к тестам | ⚡ СРЕДНИЙ |
| `docs/api_reference.md` | Версия 3.0, нет примеров тестов API | Добавить примеры тестирования | ⚡ СРЕДНИЙ |
| `docs/CONTRACT_TESTING.md` | Версия 1.0, нет примеров Phase 2 | Обновить примеры Pact тестов | ⚡ СРЕДНИЙ |
| `docs/SECURITY.md` | Версия 3.0, нет секции о Security тестах | Добавить раздел о security тестировании | ⚡ СРЕДНИЙ |

### 🟢 Низкий приоритет (актуальны)

| Файл | Статус | Примечание |
|------|--------|------------|
| `docs/QUICK_START.md` | ✅ Актуален | Базовая документация |
| `docs/ARBITRAGE.md` | ✅ Актуален | Специфичная для арбитража |
| `docs/DMARKET_API_FULL_SPEC.md` | ✅ Актуален | API спецификация |
| `docs/TELEGRAM_BOT_API.md` | ✅ Актуален | Telegram API |
| `docs/game_filters_guide.md` | ✅ Актуален | Руководство по фильтрам |
| `docs/CACHING_GUIDE.md` | ✅ Актуален | Кэширование |
| `docs/DATABASE_MIGRATIONS.md` | ✅ Актуален | Миграции |
| `docs/ERROR_HANDLING_GUIDE.md` | ✅ Актуален | Обработка ошибок |
| `docs/DEPENDENCY_INJECTION.md` | ✅ Актуален | DI паттерн |
| `docs/DATA_STRUCTURES_GUIDE.md` | ✅ Актуален | Структуры данных |
| `docs/ANYTOOL_INTEGRATION_GUIDE.md` | ✅ Актуален | MCP интеграция |
| `docs/API_DOCUMENTATION.md` | ✅ Актуален | Документация API |
| `alembic/README.md` | ✅ Актуален | Alembic |
| `src/telegram_bot/i18n/README.md` | ✅ Актуален | Локализация |
| `SECURITY.md` | ✅ Актуален | Безопасность |
| `CONTRIBUTING.md` | ⚠️ Проверить | Дубликат docs/CONTRIBUTING.md |

### 📋 План обновления документации

**Неделя 1 (🔥 Критический приоритет):**
1. [ ] Обновить `docs/testing_guide.md` до версии 4.0
   - Добавить секцию "Phase 2: Advanced Testing"
   - Добавить примеры Security, Performance, BDD тестов
   - Обновить команды запуска тестов

2. [ ] Обновить `docs/README.md` до версии 6.0
   - Исправить количество тестов: 2348 → 727+ (Phase 1+2), ~3000+ (всего)
   - Добавить ссылки на Phase 2 тесты
   - Обновить структуру тестовых директорий

**Неделя 2 (🔥 Высокий приоритет):**
3. [ ] Обновить `README.md` (корень)
   - Синхронизировать с docs/README.md
   - Добавить badge с количеством тестов

4. [ ] Обновить `CHANGELOG.md`
   - Добавить запись [Unreleased] о Phase 2 тестах
   - Добавить 727+ тестов, Security/Performance/BDD
   - Добавить Phase 3 roadmap

**Неделя 3-4 (⚡ Средний приоритет):**
5. [ ] Обновить `docs/ARCHITECTURE.md`
6. [ ] Обновить `docs/CONTRIBUTING.md`
7. [ ] Обновить `docs/api_reference.md`
8. [ ] Обновить `docs/CONTRACT_TESTING.md`
9. [ ] Обновить `docs/SECURITY.md`

### 📊 Итого по документации

| Категория | Файлов | Статус |
|-----------|--------|--------|
| 🔴 Требуют обновления | 4 | Критический |
| 🤖 GitHub Agents | 4 | Высокий |
| ⚡ Рекомендуется обновление | 5 | Средний |
| ✅ Актуальны | 17 | OK |
| **ВСЕГО** | **30** | - |

---

## 🎯 PHASE 4: ДЕТАЛЬНЫЙ ПЛАН 100% ПОКРЫТИЯ

> **Обновлено:** 26 декабря 2025
> **Цель:** Каждый модуль должен иметь 100% покрытие кода

### 📊 Полный список модулей с покрытием < 50%

#### 🔴 Категория A: Покрытие 0-30% (Критический приоритет)

| # | Модуль | Путь | Строк | Покрытие | Тестов нужно | Срок |
|---|--------|------|-------|----------|--------------|------|
| 1 | dmarket_api | `src/dmarket/dmarket_api.py` | 3092 | ~30% | 200+ | Неделя 1-2 |
| 2 | portfolio_manager | `src/dmarket/portfolio_manager.py` | 961 | ~30% | 100+ | Неделя 3-4 |
| 3 | market_visualizer | `src/utils/market_visualizer.py` | 867 | ~25% | 90+ | Неделя 5-6 |

**Детальный план для dmarket_api.py (200+ тестов):**
```
Категория 1: API методы (80 тестов)
- get_balance (10 тестов): success, error, timeout, empty response
- get_market_items (15 тестов): pagination, filters, sorting
- buy_item (10 тестов): success, insufficient funds, item sold
- sell_item (10 тестов): success, invalid price, not owned
- get_targets (10 тестов): active, completed, cancelled
- create_target (10 тестов): valid, duplicate, invalid price
- delete_target (8 тестов): success, not found, already executed
- update_target (7 тестов): price change, status change

Категория 2: Authentication (30 тестов)
- HMAC signature (10 тестов)
- Ed25519 signature (10 тестов)
- Header generation (10 тестов)

Категория 3: Error Handling (40 тестов)
- HTTP 400-499 errors (15 тестов)
- HTTP 500 errors (10 тестов)
- Network errors (10 тестов)
- Timeout handling (5 тестов)

Категория 4: Rate Limiting (25 тестов)
- Rate limit detection (10 тестов)
- Retry logic (10 тестов)
- Backoff strategy (5 тестов)

Категория 5: Edge Cases (25 тестов)
- Concurrent requests (10 тестов)
- Large payloads (5 тестов)
- Unicode handling (5 тестов)
- Empty responses (5 тестов)
```

#### 🟠 Категория B: Покрытие 30-40% (Высокий приоритет)

| # | Модуль | Путь | Строк | Покрытие | Тестов нужно | Срок |
|---|--------|------|-------|----------|--------------|------|
| 4 | arbitrage_scanner | `src/dmarket/arbitrage_scanner.py` | 1666 | ~35% | 150+ | Неделя 7-8 |
| 5 | arbitrage_sales_analysis | `src/dmarket/arbitrage_sales_analysis.py` | 998 | ~35% | 85+ | Неделя 9-10 |
| 6 | market_alerts_handler | `src/telegram_bot/handlers/market_alerts_handler.py` | 934 | ~35% | 80+ | Неделя 11-12 |

**Детальный план для arbitrage_scanner.py (150+ тестов):**
```
Категория 1: Scanning Levels (50 тестов)
- boost_scan (10 тестов): min/max price, profit threshold
- standard_scan (10 тестов): filters, sorting
- medium_scan (10 тестов): multi-game support
- advanced_scan (10 тестов): liquidity filters
- pro_scan (10 тестов): complex criteria

Категория 2: Profit Calculation (30 тестов)
- calculate_profit (10 тестов): basic, with commission
- calculate_roi (10 тестов): percentage, absolute
- filter_by_profit (10 тестов): min/max profit

Категория 3: Filtering (40 тестов)
- game_filter (10 тестов): csgo, dota2, tf2, rust
- price_filter (10 тестов): min/max price ranges
- liquidity_filter (10 тестов): volume, sales count
- combine_filters (10 тестов): multiple criteria

Категория 4: Cache Integration (20 тестов)
- cache_hit (10 тестов)
- cache_miss (5 тестов)
- cache_invalidation (5 тестов)

Категория 5: Edge Cases (10 тестов)
- empty_results, concurrent_scans, timeout
```

#### 🟡 Категория C: Покрытие 40-50% (Средний приоритет)

| # | Модуль | Путь | Строк | Покрытие | Тестов нужно | Срок |
|---|--------|------|-------|----------|--------------|------|
| 7 | game_filter_handlers | `src/telegram_bot/handlers/game_filter_handlers.py` | 1196 | ~40% | 100+ | Неделя 13-14 |
| 8 | market_analysis_handler | `src/telegram_bot/handlers/market_analysis_handler.py` | 1121 | ~45% | 80+ | Неделя 15-16 |
| 9 | backtester | `src/dmarket/backtester.py` | 1118 | ~40% | 90+ | Неделя 17-18 |
| 10 | market_analysis | `src/dmarket/market_analysis.py` | 988 | ~40% | 80+ | Неделя 19-20 |
| 11 | smart_market_finder | `src/dmarket/smart_market_finder.py` | 865 | ~45% | 70+ | Неделя 21-22 |
| 12 | formatters | `src/telegram_bot/utils/formatters.py` | 862 | ~50% | 60+ | Неделя 23-24 |
| 13 | database | `src/utils/database.py` | 843 | ~45% | 70+ | Неделя 25-26 |
| 14 | auto_seller | `src/dmarket/auto_seller.py` | 828 | ~40% | 75+ | Неделя 27-28 |

### 📋 Итоговая таблица Phase 4

| Категория | Модулей | Строк кода | Тестов нужно | Срок |
|-----------|---------|------------|--------------|------|
| A (0-30%) | 3 | 4920 | ~390 | Q1 2026 |
| B (30-40%) | 3 | 3598 | ~315 | Q1 2026 |
| C (40-50%) | 8 | 8005 | ~625 | Q2 2026 |
| **ИТОГО** | **14** | **16523** | **~1330** | **6 месяцев** |

### ⏰ Временная шкала Phase 4 (100% Coverage)

| Этап | Период | Модулей | Тестов | Целевое покрытие |
|------|--------|---------|--------|------------------|
| 1 | Январь 2026 | dmarket_api, portfolio_manager | 300 | 85% |
| 2 | Февраль 2026 | arbitrage_scanner, market_visualizer | 240 | 88% |
| 3 | Март 2026 | arbitrage_sales, market_alerts | 165 | 91% |
| 4 | Апрель 2026 | game_filter, market_analysis_handler | 180 | 94% |
| 5 | Май 2026 | backtester, market_analysis | 170 | 97% |
| 6 | Июнь 2026 | Остальные модули | 275 | **100%** |
| **ИТОГО** | **6 месяцев** | **14** | **~1330** | **100%** |

---

## 📊 Приоритеты тестов для каждого модуля (100% покрытие)

### 1. dmarket_api.py → 100% (200 тестов)
- [ ] API методы: 80 тестов
- [ ] Authentication: 30 тестов  
- [ ] Error handling: 40 тестов
- [ ] Rate limiting: 25 тестов
- [ ] Edge cases: 25 тестов

### 2. arbitrage_scanner.py → 100% (150 тестов)
- [ ] Scanning levels: 50 тестов
- [ ] Profit calculation: 30 тестов
- [ ] Filtering: 40 тестов
- [ ] Cache: 20 тестов
- [ ] Edge cases: 10 тестов

### 3. game_filter_handlers.py → 100% (100 тестов)
- [ ] Filter callbacks: 30 тестов
- [ ] Keyboard generation: 25 тестов
- [ ] State management: 20 тестов
- [ ] Persistence: 15 тестов
- [ ] Edge cases: 10 тестов

### 4. portfolio_manager.py → 100% (100 тестов)
- [ ] CRUD operations: 30 тестов
- [ ] Price tracking: 25 тестов
- [ ] Performance analysis: 20 тестов
- [ ] Sync: 15 тестов
- [ ] Edge cases: 10 тестов

### 5. market_visualizer.py → 100% (90 тестов)
- [ ] Chart generation: 35 тестов
- [ ] Data formatting: 25 тестов
- [ ] Export formats: 20 тестов
- [ ] Edge cases: 10 тестов

### 6. backtester.py → 100% (90 тестов)
- [ ] Strategy execution: 30 тестов
- [ ] Trade simulation: 25 тестов
- [ ] Metrics calculation: 20 тестов
- [ ] Historical data: 10 тестов
- [ ] Edge cases: 5 тестов

### 7. market_analysis.py → 100% (80 тестов)
- [ ] Price analysis: 25 тестов
- [ ] Trend detection: 20 тестов
- [ ] RSI/MACD: 20 тестов
- [ ] Support/Resistance: 10 тестов
- [ ] Edge cases: 5 тестов

### 8. auto_seller.py → 100% (75 тестов)
- [ ] Auto-sell logic: 25 тестов
- [ ] Price monitoring: 20 тестов
- [ ] Notification: 15 тестов
- [ ] Configuration: 10 тестов
- [ ] Edge cases: 5 тестов

### 9. smart_market_finder.py → 100% (70 тестов)
- [ ] Market search: 25 тестов
- [ ] Opportunity detection: 20 тестов
- [ ] Filtering: 15 тестов
- [ ] Ranking: 5 тестов
- [ ] Edge cases: 5 тестов

### 10. database.py → 100% (70 тестов)
- [ ] Connection management: 20 тестов
- [ ] CRUD operations: 25 тестов
- [ ] Transactions: 15 тестов
- [ ] Migration: 5 тестов
- [ ] Edge cases: 5 тестов

---

**Версия:** 11.0 (Phase 4 - 100% Coverage Roadmap)
**Последнее обновление:** 26 декабря 2025 г.
**Статус:** 🟢 Phase 3 ЗАВЕРШЕНА, Phase 4 НАЧАТА
**Текущее покрытие:** ~80%
**Целевое покрытие:** 100%
