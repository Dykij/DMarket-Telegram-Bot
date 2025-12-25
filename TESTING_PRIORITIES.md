# 🎯 Приоритеты тестирования (Декабрь 2025)

> **Дата обновления:** 25 декабря 2025 г. (последнее обновление - 1770+ новых тестов добавлено!)
> **Текущее покрытие:** 60.09%+ ✅ (цель 60%+ достигнута!)
> **DMarket API покрытие:** 87.5%+ ✅ (цель 70%+ превышена!)
> **Всего тестов:** 4170+ (все проходят)
> **Добавлено в декабре 2025:** ~1770 новых тестов (22-25 декабря 2025)
> **В процессе:** Улучшение покрытия для достижения 70%

---

## ✅ ВАЖНОЕ ОБНОВЛЕНИЕ: Новые тесты (25 декабря 2025)

**🎉 Добавлено 150+ новых тестов для модулей notifications:**

| Модуль | Файл | Тесты | Покрытие | Статус |
| ------ | ---- | ----- | -------- | ------ |
| **Alerts** | `notifications/alerts.py` | 35 | ~80% | ✅ Новое |
| **Checker** | `notifications/checker.py` | 45 | ~75% | ✅ Новое |
| **Storage** | `notifications/storage.py` | 48 | ~85% | ✅ Новое |
| **Constants** | `notifications/constants.py` | 53 | 100% | ✅ Полное |

---

## ✅ ВАЖНОЕ ОБНОВЛЕНИЕ: Новые тесты (24 декабря 2025 - вечер)

**🎉 Добавлено 152+ новых теста для модулей arbitrage:**

| Модуль | Файл | Тесты | Покрытие | Статус |
| ------ | ---- | ----- | -------- | ------ |
| **Arbitrage Core** | `dmarket/arbitrage/core.py` | 21 | ~70% | ✅ Новое |
| **Arbitrage Search** | `dmarket/arbitrage/search.py` | 34 | ~70% | ✅ Новое |
| **Arbitrage Trader** | `dmarket/arbitrage/trader.py` | 45 | ~80% | ✅ Новое |
| **Scanner Levels** | `dmarket/scanner/levels.py` | 52 | ~90% | ✅ Отлично |

---

## ✅ ВАЖНОЕ ОБНОВЛЕНИЕ: Новые тесты (24 декабря 2025)

**🎉 Добавлено 174 новых теста для 5 модулей:**

| Модуль | Файл | Тесты | Покрытие | Статус |
| ------ | ---- | ----- | -------- | ------ |
| **API Validator** | `dmarket/api_validator.py` | 29 | ~70% | ✅ Новое |
| **Liquidity Rules** | `dmarket/liquidity_rules.py` | 46 | 100% | ✅ Полное |
| **AnyTool Integration** | `utils/anytool_integration.py` | 52 | ~85% | ✅ Новое |
| **Game Filter Handlers** | `telegram_bot/handlers/game_filter_handlers.py` | 27 | ~55% | ✅ Новое |
| **Sales Analysis Handlers** | `telegram_bot/handlers/sales_analysis_handlers.py` | 20 | ~95% | ✅ Отлично |

---

## ✅ ВАЖНОЕ ОБНОВЛЕНИЕ: DMarket API Тесты Завершены

**🎉 Поздравляем!** DMarket API модули успешно покрыты тестами:

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

## ✅ ЦЕЛЬ ДОСТИГНУТА

**Поздравляем!** Целевое покрытие 60%+ успешно достигнуто.

### 📊 Прогресс

| Метрика            | Значение       |
| ------------------ | -------------- |
| **Покрытие кода**  | 60.09%+        |
| **Покрытие веток** | 47.98%+        |
| **Всего файлов**   | 200+           |
| **Тестов**         | 3874+          |
| **Статус**         | ✅ Все проходят |
| **Добавлено (22-24 дек)** | 1474+ тестов |

---

## 🎯 Следующие цели (2025-2026)

### Цель 1: Довести до 70% (Q1 2026)

**Фокус:** Повысить покрытие веток с 47.98% до 60%+

### Цель 2: Довести до 80%+ (Q2 2026)

**Фокус:** Критически важные модули до 90%+

---

## 🔴 Модули с нулевым покрытием (0%)

> **Эти модули требуют срочного внимания**

### 1. DMarket API Modules (Приоритет: 🔥 КРИТИЧЕСКИЙ)

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

## 🟡 Модули с низким покрытием (1-40%)

### Высокий приоритет для улучшения

| Модуль                     | Файл                                         | Покрытие | Пропущено | Приоритет | Статус |
| -------------------------- | -------------------------------------------- | -------- | --------- | --------- | ------ |
| **Price Analyzer**         | `utils/price_analyzer.py`                    | 6.15%    | 172       | 🔥 ВЫСОКИЙ | ✅ 39 тестов (22 дек 2025) |
| **Logs Command**           | `telegram_bot/commands/logs_command.py`      | 5.9%     | 78        | 🔥 ВЫСОКИЙ | ✅ 20 тестов (23 дек 2025) |
| **Market Alerts**          | `telegram_bot/market_alerts.py`              | 6.95%    | 270       | 🔥 ВЫСОКИЙ | ✅ 26 тестов |
| **Trading Notifications**  | `telegram_bot/notifications/trading.py`      | 11.76%   | 87        | ⚡ СРЕДНИЙ | ✅ 37 тестов (22 дек 2025) |
| **Daily Report Scheduler** | `utils/daily_report_scheduler.py`            | 12.03%   | 87        | ⚡ СРЕДНИЙ | ✅ 22 теста |
| **Scanner Cache**          | `dmarket/scanner/cache.py`                   | 25.76%   | 37        | ⚡ СРЕДНИЙ | ✅ 37 тестов (22 дек 2025) |
| **Settings Handler**       | `telegram_bot/handlers/settings_handler.py`  | 28.89%   | 130       | ⚡ СРЕДНИЙ | ✅ 42 теста (23 дек 2025) |
| **Logging Utils**          | `utils/logging_utils.py`                     | 29.94%   | 116       | ⚡ СРЕДНИЙ | ✅ 31 тест (22 дек 2025) |
| **Arbitrage Handler**      | `telegram_bot/handlers/arbitrage_handler.py` | 32.22%   | 190       | ⚡ СРЕДНИЙ | ⏳ |
| **Sales Analysis Callbacks** | `telegram_bot/sales_analysis_callbacks.py` | 6.0%     | 236       | 🔥 ВЫСОКИЙ | ✅ 30 тестов (22 дек 2025) |
| **User Profiles**          | `telegram_bot/user_profiles.py`              | ~30%     | 180       | ⚡ СРЕДНИЙ | ✅ 42 теста (23 дек 2025) |
| **Chart Generator**        | `telegram_bot/chart_generator.py`            | ~20%     | 120       | ⚡ СРЕДНИЙ | ✅ 30 тестов (23 дек 2025) |
| **Backtest Handler**       | `telegram_bot/handlers/backtest_handler.py`  | 0%       | ~350      | ⚡ СРЕДНИЙ | ✅ 35 тестов (23 дек 2025) |
| **Rate Limit Admin**       | `telegram_bot/handlers/rate_limit_admin.py`  | 0%       | ~255      | ⚡ СРЕДНИЙ | ✅ 34 теста (23 дек 2025) |
| **Resume Command**         | `telegram_bot/commands/resume_command.py`    | 0%       | 28        | ⚡ СРЕДНИЙ | ✅ 16 тестов (23 дек 2025) |
| **Notification Handlers**  | `telegram_bot/notifications/handlers.py`     | 8.4%     | ~450      | 🔥 ВЫСОКИЙ | ✅ 37 тестов (24 дек 2025) |
| **Notification Formatters**| `telegram_bot/notifications/formatters.py`   | 29.5%    | ~170      | ⚡ СРЕДНИЙ | ✅ 33 теста (24 дек 2025) |
| **Scanner Analysis**       | `dmarket/scanner/analysis.py`                | 0%       | ~332      | 🔥 ВЫСОКИЙ | ✅ 55 тестов (24 дек 2025) |
| **Scanner Filters**        | `dmarket/scanner/filters.py`                 | 21%      | ~213      | ⚡ СРЕДНИЙ | ✅ 45 тестов (24 дек 2025) |
| **State Manager**          | `utils/state_manager.py`                     | 41.7%    | ~558      | ⚡ СРЕДНИЙ | ✅ 36 тестов (24 дек 2025) |
| **Initialization**         | `telegram_bot/initialization.py`             | 19%      | ~260      | ⚡ СРЕДНИЙ | ✅ 45 тестов (24 дек 2025) |
| **Profiles**               | `telegram_bot/profiles.py`                   | 31%      | ~40       | ⚡ СРЕДНИЙ | ✅ 25 тестов (24 дек 2025) |
| **Targets Competition**    | `dmarket/targets/competition.py`             | 8.7%     | ~240      | 🔥 ВЫСОКИЙ | ✅ 38 тестов (24 дек 2025) |
| **Targets Validators**     | `dmarket/targets/validators.py`              | 47.9%    | ~50       | ⚡ СРЕДНИЙ | ✅ 34 теста (24 дек 2025) |
| **API Client**             | `telegram_bot/utils/api_client.py`           | 16.7%    | ~115      | ⚡ СРЕДНИЙ | ✅ 28 тестов (24 дек 2025) |
| **API Helper**             | `telegram_bot/utils/api_helper.py`           | 21.4%    | ~40       | ⚡ СРЕДНИЙ | ✅ 18 тестов (24 дек 2025) |
| **Arbitrage Calculations** | `dmarket/arbitrage/calculations.py`          | 58.4%    | ~110      | ⚡ СРЕДНИЙ | ✅ 107 тестов (24 дек 2025) |
| **MCP Server**             | `mcp_server/dmarket_mcp.py`                  | 22.2%    | ~260      | ⚡ СРЕДНИЙ | ✅ 35 тестов (24 дек 2025) |
| **Notification Digest**    | `telegram_bot/handlers/notification_digest_handler.py` | 0% | ~380   | 🔥 ВЫСОКИЙ | ✅ 40 тестов (existing)
| **Web Dashboard**          | `web_dashboard/app.py`                       | 0%       | ~17       | 🟢 НИЗКИЙ  | ✅ 13 тестов (24 дек 2025)
| **Intramarket Arbitrage Handler** | `telegram_bot/handlers/intramarket_arbitrage_handler.py` | 0% | ~485 | ⚡ СРЕДНИЙ | ✅ 35 тестов (24 дек 2025)
| **Liquidity Settings Handler** | `telegram_bot/handlers/liquidity_settings_handler.py` | 0% | ~462 | ⚡ СРЕДНИЙ | ✅ 32 теста (24 дек 2025)
| **Price Alerts Handler** | `telegram_bot/handlers/price_alerts_handler.py` | 0% | ~576 | ⚡ СРЕДНИЙ | ✅ 37 тестов (24 дек 2025)

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

### Неделя 5-6: Telegram Handlers (⚡ ВЫСОКИЙ) - 🔄 В ПРОЦЕССЕ

**Цель:** Покрыть основные handlers (~155 тестов)

**Статус на 22 декабря 2025:**

- [x] **notification_digest_handler.py** - 20 тестов созданы (требуется исправление)
  - ⚠️ 13 тестов падают из-за несоответствия mock-структуры
  - ✅ 7 тестов проходят успешно
  - 📝 Требуется: обновить тесты для работы с DigestManager

- [x] **balance_command.py** - существующие тесты ✅
  - Тесты уже существуют в tests/telegram_bot/commands/test_balance_command.py

- [x] **game_filters/handlers.py** - 44 тестов ✅ (22 декабря 2025)
  - Выбор/деселекция игр (8 тестов)
  - Применение фильтров (8 тестов)
  - UI-меню (8 тестов)
  - Константы для всех игр (8 тестов)
  - Утилиты для работы с фильтрами (12 тестов)

- [x] **notification_filters_handler.py** - 24 теста ✅ (22 декабря 2025)
  - NotificationFilters class
  - Управление фильтрами пользователей
  - Логика should_notify
  - Edge cases

- [x] **portfolio_handler.py** - 11 тестов ✅ (22 декабря 2025)
  - PortfolioHandler инициализация
  - Обработка команд
  - Callback handlers

- [x] **smart_notifications/** - 20 тестов ✅ (22 декабря 2025)
  - Constants (3 теста)
  - Utils (4 теста)
  - Preferences (4 теста)
  - Throttling (2 теста)
  - Senders (2 теста)
  - Checkers (2 теста)
  - Alerts (1 тест)
  - Handlers (1 тест)
  - Integration (1 тест)

**Ожидаемый результат:** 0% → 70%+ покрытие handlers, +2-3% общего покрытия

---

### Неделя 7-8: Utils & Analytics (⚡ СРЕДНИЙ) - 🔄 В ПРОЦЕССЕ

**Цель:** Улучшить покрытие утилит (~115 тестов)

**Статус на 22 декабря 2025:**

- [x] **analytics.py** - 40 тестов ✅ (22 декабря 2025)
  - ChartGenerator инициализация и конфигурация
  - Создание графиков цен (price history)
  - Создание обзорных графиков рынка
  - Визуализация арбитражных возможностей
  - Анализ объёмов торговли
  - Расчёт статистики цен
  - Детекция трендов

- [x] **daily_report_scheduler.py** - 22 теста ✅ (22 декабря 2025)
  - Инициализация планировщика
  - Старт/стоп планировщика
  - Генерация отчётов
  - Сбор статистики
  - Форматирование отчётов

- [x] **main.py** - 15 тестов ✅ (22 декабря 2025)
  - Application инициализация
  - Shutdown процедуры
  - Signal handlers
  - Crash notifications

- [x] **market_analytics.py** - существующие тесты ✅
  - Тесты уже существуют в tests/utils/test_market_analytics.py

- [x] **price_analyzer.py** - существующие тесты ✅
  - Тесты уже существуют в tests/utils/test_price_analyzer.py

- [ ] **market_analytics.py** - 35 тестов
  - Анализ цен: RSI, MACD, Bollinger Bands (8 тестов)
  - Sanity checks (8 тестов)
  - Определение трендов (6 тестов)
  - Анализ ликвидности (6 тестов)
  - Edge cases (7 тестов)
- [ ] **price_analyzer.py** - 30 тестов
  - Анализ ценовых паттернов
  - Обнаружение аномалий
  - Edge cases
- [x] **batch_processor.py** - 25 тестов ✅ (22 декабря 2025)
  - SimpleBatchProcessor инициализация (3 теста)
  - Пакетная обработка (8 тестов)
  - Progress callbacks (3 теста)
  - Error callbacks (2 теста)
  - Edge cases (6 тестов)
  - Integration tests (3 теста)
- [x] **reactive_websocket.py** - 23 теста ✅ (22 декабря 2025)
  - EventType enum (2 теста)
  - SubscriptionState enum (2 теста)
  - Observable pattern (11 тестов)
  - Edge cases (3 теста)
  - Generic types (2 теста)
  - Integration tests (3 теста)
- [x] **market_alerts.py** - 26 тестов ✅ (22 декабря 2025)
  - MarketAlertsManager инициализация (9 тестов)
  - Subscriber management (4 теста)
  - Monitoring control (2 теста)
  - Alert management (2 теста)
  - Threshold configuration (4 теста)
  - Check intervals (2 теста)
  - Integration tests (3 теста)
- [x] **dashboard_handler.py** - 26 тестов ✅ (22 декабря 2025)
  - ScannerDashboard инициализация (3 теста)
  - Scan result management (4 теста)
  - User statistics (6 тестов)
  - Dashboard constants (1 тест)
  - Active scans (3 теста)
  - Edge cases (4 теста)
  - Integration tests (1 тест)

**Ожидаемый результат:** 6-30% → 70%+ покрытие utils, +1-2% общего покрытия

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

| Период      | Фокус       | Прирост | Итого        |
| ----------- | ----------- | ------- | ------------ |
| **Текущее** | -           | -       | **60.09%** ✅ |
| Недели 1-2  | DMarket API | +4-5%   | 64-65%       |
| Недели 3-4  | Arbitrage   | +2-3%   | 66-68%       |
| Недели 5-6  | Handlers    | +2-3%   | 68-71%       |
| Недели 7-8  | Utils       | +1-2%   | **70-73%** 🎯 |

**Цель 70% будет достигнута через 8 недель (Q1 2026)**

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

3. **Utils Module** - 664 теста
   - ✅ Широкое покрытие утилит
   - ✅ Хорошие async тесты
   - ✅ Тесты для rate limiters, cache, circuit breaker

#### ⚠️ Области для улучшения

1. **Telegram Handlers** - 245 тестов (недостаточно)
   - ⚠️ Отсутствуют тесты для `notification_digest_handler.py` (0 тестов, нужно 40)
   - ⚠️ Отсутствуют тесты для `notification_filters_handler.py` (0 тестов, нужно 35)
   - ⚠️ Недостаточное покрытие `game_filters/handlers.py` (нужно добавить 30+ тестов)
   - ⚠️ Слабое покрытие error handling и edge cases

2. **DMarket API Modules** - требуют расширения
   - ⚠️ `test_market.py` - 28 тестов (нужно 30+, добавить 2+)
   - ⚠️ `test_trading.py` - 17 тестов (нужно 25+, добавить 8+)
   - ⚠️ `test_targets_api.py` - 17 тестов (нужно 20+, добавить 3+)
   - ⚠️ `test_inventory.py` - 15 тестов (нужно 15+, норма, но улучшить edge cases)
   - ⚠️ `test_auth.py` - 17 тестов (нужно 15+, норма, но улучшить error handling)

3. **Модули с нулевым покрытием**
   - ❌ `src/telegram_bot/handlers/notification_digest_handler.py` - **0 тестов**
   - ❌ `src/telegram_bot/handlers/notification_filters_handler.py` - **0 тестов**
   - ❌ `src/telegram_bot/smart_notifications/checkers.py` - **0 тестов**
   - ❌ `src/telegram_bot/smart_notifications/senders.py` - **0 тестов**
   - ❌ `src/telegram_bot/smart_notifications/utils.py` - **0 тестов**

4. **Integration и E2E тесты** - критически недостаточно
   - ⚠️ Только 11 integration тестовых файлов
   - ⚠️ Только 2 E2E тестовых файла
   - ❌ Отсутствуют полные user workflow тесты
   - ❌ Нет тестов для multi-module interactions

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

### Приоритетный список улучшений (Top 10)

| Приоритет | Файл/Модуль                               | Текущие тесты | Нужно тестов   | Критичность   |
| --------- | ----------------------------------------- | ------------- | -------------- | ------------- |
| 1         | `test_notification_digest_handler.py`     | **0**         | **40**         | 🔥 КРИТИЧЕСКАЯ |
| 2         | `test_notification_filters_handler.py`    | **0**         | **35**         | 🔥 КРИТИЧЕСКАЯ |
| 3         | `test_smart_notifications_checkers.py`    | **0**         | **20**         | 🔥 КРИТИЧЕСКАЯ |
| 4         | `test_trading.py` (расширить)             | 17            | **25** (+8)    | ⚡ ВЫСОКАЯ     |
| 5         | `test_game_filters_extended.py` (создать) | ~15           | **50** (+35)   | ⚡ ВЫСОКАЯ     |
| 6         | `test_arbitrage_edge_cases.py` (создать)  | в основных    | **15** (новых) | ⚡ ВЫСОКАЯ     |
| 7         | `test_balance_command.py` (расширить)     | ~20           | **30** (+10)   | ⚡ СРЕДНЯЯ     |
| 8         | `test_market.py` (edge cases)             | 28            | **30** (+2)    | ⚡ СРЕДНЯЯ     |
| 9         | `test_targets_api.py` (edge cases)        | 17            | **20** (+3)    | ⚡ СРЕДНЯЯ     |
| 10        | E2E workflow тесты (расширить)            | ~30           | **50** (+20)   | ⚡ СРЕДНЯЯ     |

**Итого для Top 10:** +188 тестов

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

**Версия:** 3.0 (Расширенная)
**Последнее обновление:** 20 декабря 2025 г.
**Статус:** 🟢 Цель 60%+ достигнута! Переход к 70%+ с детальным планом ~520 тестов
**Готовность плана:** ✅ Полностью детализирован с примерами кода и структурой тестов
