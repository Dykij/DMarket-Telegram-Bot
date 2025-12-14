# ✅ TODO: Юнит-тесты для достижения 60%+ покрытия

> **Текущее покрытие:** 53.35%
> **Целевое покрытие:** 60%+
> **Недостающее:** ~7% (~350 тестов)

---

## 🔥 WEEK 1: DMarket API Clients (Критический приоритет)

### `tests/dmarket/api/test_client.py` (НОВЫЙ ФАЙЛ)

**Цель:** 40+ тестов, покрытие 0% → 70%+

- [ ] **TestDMarketClientInitialization** (5 тестов)
  - [ ] `test_client_init_with_valid_credentials`
  - [ ] `test_client_init_with_empty_credentials_raises_error`
  - [ ] `test_client_sets_default_base_url`
  - [ ] `test_client_accepts_custom_base_url`
  - [ ] `test_client_initializes_http_client`

- [ ] **TestDMarketClientAuthentication** (8 тестов)
  - [ ] `test_generate_signature_creates_valid_hmac`
  - [ ] `test_generate_signature_with_get_method`
  - [ ] `test_generate_signature_with_post_method`
  - [ ] `test_generate_signature_with_different_paths`
  - [ ] `test_generate_headers_includes_all_required_fields`
  - [ ] `test_generate_headers_includes_timestamp`
  - [ ] `test_generate_headers_includes_signature`
  - [ ] `test_signature_changes_with_timestamp`

- [ ] **TestDMarketClientRequests** (12 тестов)
  - [ ] `test_get_request_success`
  - [ ] `test_get_request_with_params`
  - [ ] `test_post_request_success`
  - [ ] `test_post_request_with_body`
  - [ ] `test_patch_request_success`
  - [ ] `test_delete_request_success`
  - [ ] `test_request_includes_auth_headers`
  - [ ] `test_request_handles_timeout`
  - [ ] `test_request_handles_connection_error`
  - [ ] `test_request_handles_http_error`
  - [ ] `test_request_returns_json_response`
  - [ ] `test_request_handles_non_json_response`

- [ ] **TestDMarketClientRateLimiting** (5 тестов)
  - [ ] `test_rate_limiter_delays_requests`
  - [ ] `test_rate_limiter_respects_429_retry_after`
  - [ ] `test_rate_limiter_allows_requests_after_cooldown`
  - [ ] `test_multiple_requests_respect_rate_limit`
  - [ ] `test_rate_limit_error_logged`

- [ ] **TestDMarketClientRetry** (10 тестов)
  - [ ] `test_retry_on_500_error`
  - [ ] `test_retry_on_502_error`
  - [ ] `test_retry_on_503_error`
  - [ ] `test_retry_on_timeout`
  - [ ] `test_retry_on_connection_error`
  - [ ] `test_max_retries_exceeded_raises_error`
  - [ ] `test_retry_with_exponential_backoff`
  - [ ] `test_no_retry_on_400_error`
  - [ ] `test_no_retry_on_404_error`
  - [ ] `test_retry_count_logged`

---

### `tests/dmarket/api/test_wallet.py` (НОВЫЙ ФАЙЛ)

**Цель:** 25+ тестов, покрытие 0% → 75%+

- [ ] **TestWalletGetBalance** (8 тестов)
  - [ ] `test_get_balance_returns_usd_and_dmc`
  - [ ] `test_get_balance_with_valid_response`
  - [ ] `test_get_balance_with_zero_balance`
  - [ ] `test_get_balance_with_high_balance`
  - [ ] `test_get_balance_handles_api_error`
  - [ ] `test_get_balance_handles_timeout`
  - [ ] `test_get_balance_converts_cents_to_usd`
  - [ ] `test_get_balance_caches_result`

- [ ] **TestWalletTransactions** (8 тестов)
  - [ ] `test_get_transactions_returns_list`
  - [ ] `test_get_transactions_with_limit`
  - [ ] `test_get_transactions_with_offset`
  - [ ] `test_get_transactions_filters_by_type`
  - [ ] `test_get_transactions_filters_by_date_range`
  - [ ] `test_get_transactions_empty_list`
  - [ ] `test_get_transactions_pagination`
  - [ ] `test_get_transactions_handles_error`

- [ ] **TestWalletDeposit** (5 тестов)
  - [ ] `test_deposit_creates_invoice`
  - [ ] `test_deposit_with_valid_amount`
  - [ ] `test_deposit_with_minimum_amount`
  - [ ] `test_deposit_with_invalid_amount_raises_error`
  - [ ] `test_deposit_returns_payment_url`

- [ ] **TestWalletWithdrawal** (4 тестов)
  - [ ] `test_withdraw_initiates_withdrawal`
  - [ ] `test_withdraw_with_valid_amount`
  - [ ] `test_withdraw_insufficient_balance_raises_error`
  - [ ] `test_withdraw_below_minimum_raises_error`

---

### `tests/dmarket/api/test_market.py` (НОВЫЙ ФАЙЛ)

**Цель:** 30+ тестов, покрытие 0% → 75%+

- [ ] **TestMarketGetItems** (10 тестов)
  - [ ] `test_get_items_returns_list`
  - [ ] `test_get_items_with_game_filter`
  - [ ] `test_get_items_with_price_filter`
  - [ ] `test_get_items_with_title_search`
  - [ ] `test_get_items_with_multiple_filters`
  - [ ] `test_get_items_with_pagination`
  - [ ] `test_get_items_with_limit`
  - [ ] `test_get_items_empty_result`
  - [ ] `test_get_items_handles_api_error`
  - [ ] `test_get_items_caches_result`

- [ ] **TestMarketGetItemById** (5 тестов)
  - [ ] `test_get_item_by_id_returns_item`
  - [ ] `test_get_item_by_id_with_valid_id`
  - [ ] `test_get_item_by_id_not_found_raises_error`
  - [ ] `test_get_item_by_id_handles_error`
  - [ ] `test_get_item_by_id_caches_result`

- [ ] **TestMarketFilters** (8 тестов)
  - [ ] `test_filter_by_price_range`
  - [ ] `test_filter_by_min_price`
  - [ ] `test_filter_by_max_price`
  - [ ] `test_filter_by_game_csgo`
  - [ ] `test_filter_by_game_dota2`
  - [ ] `test_filter_by_rarity`
  - [ ] `test_filter_by_type`
  - [ ] `test_multiple_filters_combined`

- [ ] **TestMarketPagination** (7 tестов)
  - [ ] `test_pagination_first_page`
  - [ ] `test_pagination_next_page`
  - [ ] `test_pagination_with_offset`
  - [ ] `test_pagination_with_limit`
  - [ ] `test_pagination_last_page`
  - [ ] `test_pagination_total_count`
  - [ ] `test_pagination_handles_empty_result`

---

### `tests/dmarket/api/test_trading.py` (НОВЫЙ ФАЙЛ)

**Цель:** 25+ тестов, покрытие 0% → 75%+

- [ ] **TestTradingBuyItem** (10 тестов)
  - [ ] `test_buy_item_success`
  - [ ] `test_buy_item_with_valid_item_id`
  - [ ] `test_buy_item_with_valid_price`
  - [ ] `test_buy_item_insufficient_balance_raises_error`
  - [ ] `test_buy_item_invalid_item_id_raises_error`
  - [ ] `test_buy_item_item_sold_raises_error`
  - [ ] `test_buy_item_returns_order_id`
  - [ ] `test_buy_item_updates_balance`
  - [ ] `test_buy_item_handles_timeout`
  - [ ] `test_buy_item_handles_api_error`

- [ ] **TestTradingSellItem** (8 тестов)
  - [ ] `test_sell_item_success`
  - [ ] `test_sell_item_with_valid_item_id`
  - [ ] `test_sell_item_with_valid_price`
  - [ ] `test_sell_item_below_minimum_price_raises_error`
  - [ ] `test_sell_item_not_owned_raises_error`
  - [ ] `test_sell_item_returns_offer_id`
  - [ ] `test_sell_item_handles_timeout`
  - [ ] `test_sell_item_handles_api_error`

- [ ] **TestTradingCancelOffer** (7 тестов)
  - [ ] `test_cancel_offer_success`
  - [ ] `test_cancel_offer_with_valid_offer_id`
  - [ ] `test_cancel_offer_invalid_id_raises_error`
  - [ ] `test_cancel_offer_already_sold_raises_error`
  - [ ] `test_cancel_offer_not_owned_raises_error`
  - [ ] `test_cancel_offer_handles_timeout`
  - [ ] `test_cancel_offer_handles_api_error`

---

### `tests/dmarket/api/test_targets_api.py` (НОВЫЙ ФАЙЛ)

**Цель:** 20+ тестов, покрытие 0% → 75%+

- [ ] **TestTargetsCreate** (7 тестов)
  - [ ] `test_create_target_success`
  - [ ] `test_create_target_with_valid_params`
  - [ ] `test_create_target_with_game_filter`
  - [ ] `test_create_target_with_price_range`
  - [ ] `test_create_target_invalid_price_raises_error`
  - [ ] `test_create_target_returns_target_id`
  - [ ] `test_create_target_handles_error`

- [ ] **TestTargetsGet** (5 тестов)
  - [ ] `test_get_targets_returns_list`
  - [ ] `test_get_targets_with_active_filter`
  - [ ] `test_get_targets_with_game_filter`
  - [ ] `test_get_targets_empty_list`
  - [ ] `test_get_targets_handles_error`

- [ ] **TestTargetsDelete** (5 тестов)
  - [ ] `test_delete_target_success`
  - [ ] `test_delete_target_with_valid_id`
  - [ ] `test_delete_target_not_found_raises_error`
  - [ ] `test_delete_target_not_owned_raises_error`
  - [ ] `test_delete_target_handles_error`

- [ ] **TestTargetsUpdate** (3 теста)
  - [ ] `test_update_target_success`
  - [ ] `test_update_target_price`
  - [ ] `test_update_target_handles_error`

---

## 🔥 WEEK 2: Arbitrage Module (Критический приоритет)

### `tests/dmarket/test_arbitrage.py` (НОВЫЙ ФАЙЛ)

**Цель:** 60+ тестов, покрытие 0% → 80%+

- [ ] **TestArbitrageScannerInitialization** (5 тестов)
  - [ ] `test_scanner_init_with_api_client`
  - [ ] `test_scanner_init_sets_default_params`
  - [ ] `test_scanner_init_with_custom_params`
  - [ ] `test_scanner_init_creates_cache`
  - [ ] `test_scanner_init_with_filters`

- [ ] **TestArbitrageScanLevel** (15 тестов)
  - [ ] `test_scan_level_boost_returns_opportunities`
  - [ ] `test_scan_level_standard_returns_opportunities`
  - [ ] `test_scan_level_medium_returns_opportunities`
  - [ ] `test_scan_level_advanced_returns_opportunities`
  - [ ] `test_scan_level_pro_returns_opportunities`
  - [ ] `test_scan_level_with_game_filter`
  - [ ] `test_scan_level_with_price_filter`
  - [ ] `test_scan_level_with_min_profit_filter`
  - [ ] `test_scan_level_invalid_level_raises_error`
  - [ ] `test_scan_level_empty_result`
  - [ ] `test_scan_level_sorts_by_profit`
  - [ ] `test_scan_level_limits_results`
  - [ ] `test_scan_level_handles_api_error`
  - [ ] `test_scan_level_uses_cache`
  - [ ] `test_scan_level_invalidates_old_cache`

- [ ] **TestArbitrageProfitCalculation** (12 тестов)
  - [ ] `test_calculate_profit_basic_scenario`
  - [ ] `test_calculate_profit_with_commission`
  - [ ] `test_calculate_profit_high_prices`
  - [ ] `test_calculate_profit_low_prices`
  - [ ] `test_calculate_profit_minimal_profit`
  - [ ] `test_calculate_profit_zero_profit`
  - [ ] `test_calculate_profit_negative_profit`
  - [ ] `test_calculate_profit_with_custom_commission`
  - [ ] `test_calculate_profit_with_zero_buy_price_raises_error`
  - [ ] `test_calculate_profit_with_negative_price_raises_error`
  - [ ] `test_calculate_profit_returns_tuple`
  - [ ] `test_calculate_profit_precision`

- [ ] **TestArbitrageFiltering** (10 тестов)
  - [ ] `test_filter_by_min_profit_percent`
  - [ ] `test_filter_by_max_price`
  - [ ] `test_filter_by_min_price`
  - [ ] `test_filter_by_game`
  - [ ] `test_filter_by_multiple_games`
  - [ ] `test_filter_by_rarity`
  - [ ] `test_filter_by_liquidity`
  - [ ] `test_filter_removes_duplicates`
  - [ ] `test_filter_empty_result`
  - [ ] `test_filter_preserves_order`

- [ ] **TestArbitrageSorting** (5 тестов)
  - [ ] `test_sort_by_profit_descending`
  - [ ] `test_sort_by_profit_percent_descending`
  - [ ] `test_sort_by_price_ascending`
  - [ ] `test_sort_by_liquidity_descending`
  - [ ] `test_sort_stable_sorting`

- [ ] **TestArbitrageValidation** (8 тестов)
  - [ ] `test_validate_opportunity_valid`
  - [ ] `test_validate_opportunity_invalid_price`
  - [ ] `test_validate_opportunity_insufficient_profit`
  - [ ] `test_validate_opportunity_item_sold`
  - [ ] `test_validate_opportunity_price_changed`
  - [ ] `test_validate_opportunity_outdated`
  - [ ] `test_validate_opportunity_handles_error`
  - [ ] `test_validate_multiple_opportunities`

- [ ] **TestArbitragePropertyBased** (5 тестов - Hypothesis)
  - [ ] `test_profit_never_negative_with_valid_inputs`
  - [ ] `test_higher_sell_price_always_more_profit`
  - [ ] `test_commission_reduces_profit`
  - [ ] `test_filter_always_returns_subset`
  - [ ] `test_sort_maintains_list_length`

---

## ⚡ WEEK 3: Telegram Commands (Высокий приоритет)

### `tests/telegram_bot/commands/test_balance_command.py` (НОВЫЙ ФАЙЛ)

**Цель:** 30+ тестов, покрытие 0% → 75%+

- [ ] **TestBalanceCommandExecution** (10 тестов)
  - [ ] `test_balance_command_shows_usd_balance`
  - [ ] `test_balance_command_shows_dmc_balance`
  - [ ] `test_balance_command_formats_currency`
  - [ ] `test_balance_command_with_zero_balance`
  - [ ] `test_balance_command_with_high_balance`
  - [ ] `test_balance_command_handles_api_error`
  - [ ] `test_balance_command_handles_timeout`
  - [ ] `test_balance_command_handles_invalid_credentials`
  - [ ] `test_balance_command_requires_setup`
  - [ ] `test_balance_command_logs_request`

- [ ] **TestBalanceCommandFormatting** (8 тестов)
  - [ ] `test_format_balance_with_decimals`
  - [ ] `test_format_balance_rounds_correctly`
  - [ ] `test_format_balance_with_thousands_separator`
  - [ ] `test_format_balance_in_different_locales`
  - [ ] `test_format_balance_emoji_icons`
  - [ ] `test_format_balance_markdown_formatting`
  - [ ] `test_format_balance_zero`
  - [ ] `test_format_balance_very_large_numbers`

- [ ] **TestBalanceCommandInteraction** (7 тестов)
  - [ ] `test_balance_command_sends_message`
  - [ ] `test_balance_command_reply_to_user`
  - [ ] `test_balance_command_with_inline_keyboard`
  - [ ] `test_balance_command_callback_refresh`
  - [ ] `test_balance_command_updates_cache`
  - [ ] `test_balance_command_respects_rate_limit`
  - [ ] `test_balance_command_logs_user_action`

- [ ] **TestBalanceCommandEdgeCases** (5 тестов)
  - [ ] `test_balance_command_concurrent_requests`
  - [ ] `test_balance_command_after_transaction`
  - [ ] `test_balance_command_multiple_currencies`
  - [ ] `test_balance_command_negative_balance_handled`
  - [ ] `test_balance_command_api_returns_invalid_data`

---

### `tests/telegram_bot/handlers/game_filters/test_handlers.py` (НОВЫЙ ФАЙЛ)

**Цель:** 50+ тестов, покрытие 0% → 70%+

- [ ] **TestGameFilterSelection** (12 тестов)
  - [ ] `test_select_csgo_filter`
  - [ ] `test_select_dota2_filter`
  - [ ] `test_select_tf2_filter`
  - [ ] `test_select_rust_filter`
  - [ ] `test_select_multiple_games`
  - [ ] `test_deselect_game`
  - [ ] `test_select_all_games`
  - [ ] `test_clear_all_selections`
  - [ ] `test_game_filter_callback_handler`
  - [ ] `test_game_filter_updates_user_settings`
  - [ ] `test_game_filter_shows_confirmation`
  - [ ] `test_game_filter_invalid_game_raises_error`

- [ ] **TestGameFilterApplication** (10 тестов)
  - [ ] `test_apply_filter_to_scan`
  - [ ] `test_apply_filter_to_arbitrage`
  - [ ] `test_apply_filter_to_targets`
  - [ ] `test_apply_multiple_filters`
  - [ ] `test_filter_removes_non_matching_items`
  - [ ] `test_filter_preserves_matching_items`
  - [ ] `test_filter_with_empty_result`
  - [ ] `test_filter_performance_with_large_dataset`
  - [ ] `test_filter_caches_result`
  - [ ] `test_filter_handles_error`

- [ ] **TestGameFilterUI** (15 тестов)
  - [ ] `test_show_game_filter_menu`
  - [ ] `test_game_filter_menu_buttons`
  - [ ] `test_game_filter_menu_layout`
  - [ ] `test_game_filter_menu_with_selections`
  - [ ] `test_game_filter_menu_checkmarks`
  - [ ] `test_game_filter_menu_localization`
  - [ ] `test_game_filter_menu_pagination`
  - [ ] `test_update_game_filter_menu`
  - [ ] `test_close_game_filter_menu`
  - [ ] `test_game_filter_menu_keyboard`
  - [ ] `test_game_filter_menu_callback_data`
  - [ ] `test_game_filter_menu_error_handling`
  - [ ] `test_game_filter_menu_accessibility`
  - [ ] `test_game_filter_menu_mobile_friendly`
  - [ ] `test_game_filter_menu_caches_state`

- [ ] **TestGameFilterPersistence** (8 тестов)
  - [ ] `test_save_game_filter_to_database`
  - [ ] `test_load_game_filter_from_database`
  - [ ] `test_update_game_filter_in_database`
  - [ ] `test_delete_game_filter_from_database`
  - [ ] `test_game_filter_persists_across_sessions`
  - [ ] `test_game_filter_default_values`
  - [ ] `test_game_filter_migration`
  - [ ] `test_game_filter_handles_database_error`

- [ ] **TestGameFilterValidation** (5 тестов)
  - [ ] `test_validate_game_selection`
  - [ ] `test_validate_filter_parameters`
  - [ ] `test_validate_filter_combination`
  - [ ] `test_invalid_game_rejected`
  - [ ] `test_conflicting_filters_rejected`

---

## 🔧 WEEK 4: Notifications & Utils (Средний приоритет)

### `tests/telegram_bot/handlers/test_notification_digest_handler.py` (НОВЫЙ)

**Цель:** 40+ тестов, покрытие 0% → 70%+

- [ ] **TestDigestCreation** (10 тестов)
  - [ ] `test_create_daily_digest`
  - [ ] `test_create_weekly_digest`
  - [ ] `test_create_digest_with_notifications`
  - [ ] `test_create_digest_empty_notifications`
  - [ ] `test_create_digest_groups_by_category`
  - [ ] `test_create_digest_sorts_by_priority`
  - [ ] `test_create_digest_limits_items`
  - [ ] `test_create_digest_formats_message`
  - [ ] `test_create_digest_adds_summary`
  - [ ] `test_create_digest_handles_error`

- [ ] **TestDigestScheduling** (10 тестов)
  - [ ] `test_schedule_daily_digest`
  - [ ] `test_schedule_weekly_digest`
  - [ ] `test_digest_runs_at_specified_time`
  - [ ] `test_digest_respects_timezone`
  - [ ] `test_digest_skips_if_disabled`
  - [ ] `test_digest_retries_on_failure`
  - [ ] `test_digest_handles_concurrent_jobs`
  - [ ] `test_digest_cancels_old_jobs`
  - [ ] `test_digest_logs_execution`
  - [ ] `test_digest_handles_scheduling_error`

- [ ] **TestDigestDelivery** (10 тестов)
  - [ ] `test_send_digest_to_user`
  - [ ] `test_send_digest_to_multiple_users`
  - [ ] `test_digest_respects_user_preferences`
  - [ ] `test_digest_skips_inactive_users`
  - [ ] `test_digest_handles_send_error`
  - [ ] `test_digest_retries_failed_sends`
  - [ ] `test_digest_marks_as_delivered`
  - [ ] `test_digest_tracks_delivery_stats`
  - [ ] `test_digest_handles_rate_limit`
  - [ ] `test_digest_logs_delivery`

- [ ] **TestDigestCustomization** (10 тестов)
  - [ ] `test_customize_digest_frequency`
  - [ ] `test_customize_digest_categories`
  - [ ] `test_customize_digest_time`
  - [ ] `test_customize_digest_format`
  - [ ] `test_save_digest_preferences`
  - [ ] `test_load_digest_preferences`
  - [ ] `test_reset_digest_preferences`
  - [ ] `test_validate_digest_preferences`
  - [ ] `test_digest_preferences_ui`
  - [ ] `test_digest_preferences_persistence`

---

### `tests/utils/test_market_analytics.py` (НОВЫЙ ФАЙЛ)

**Цель:** 35+ тестов, покрытие 0% → 75%+

- [ ] **TestPriceAnalysis** (10 тестов)
  - [ ] `test_calculate_average_price`
  - [ ] `test_calculate_median_price`
  - [ ] `test_calculate_price_percentiles`
  - [ ] `test_calculate_price_volatility`
  - [ ] `test_detect_price_outliers`
  - [ ] `test_price_trend_detection`
  - [ ] `test_price_analysis_empty_data`
  - [ ] `test_price_analysis_single_datapoint`
  - [ ] `test_price_analysis_handles_error`
  - [ ] `test_price_analysis_caches_result`

- [ ] **TestTechnicalIndicators** (12 тестов)
  - [ ] `test_calculate_rsi`
  - [ ] `test_calculate_macd`
  - [ ] `test_calculate_bollinger_bands`
  - [ ] `test_calculate_moving_average`
  - [ ] `test_calculate_ema`
  - [ ] `test_rsi_oversold_signal`
  - [ ] `test_rsi_overbought_signal`
  - [ ] `test_macd_crossover_signal`
  - [ ] `test_bollinger_squeeze_detection`
  - [ ] `test_indicators_with_insufficient_data`
  - [ ] `test_indicators_precision`
  - [ ] `test_indicators_performance`

- [ ] **TestMarketTrends** (8 тестов)
  - [ ] `test_identify_uptrend`
  - [ ] `test_identify_downtrend`
  - [ ] `test_identify_sideways_trend`
  - [ ] `test_trend_strength_calculation`
  - [ ] `test_trend_reversal_detection`
  - [ ] `test_support_resistance_levels`
  - [ ] `test_trend_with_noisy_data`
  - [ ] `test_trend_handles_gaps`

- [ ] **TestLiquidityAnalysis** (5 тестов)
  - [ ] `test_calculate_liquidity_score`
  - [ ] `test_liquidity_high_volume`
  - [ ] `test_liquidity_low_volume`
  - [ ] `test_liquidity_with_price_spread`
  - [ ] `test_liquidity_over_time`

---

## 📋 Прогресс трекинг

### Неделя 1 (DMarket API) - 140 тестов

- [ ] test_client.py - 40 тестов
- [ ] test_wallet.py - 25 тестов
- [ ] test_market.py - 30 тестов
- [ ] test_trading.py - 25 тестов
- [ ] test_targets_api.py - 20 тестов

### Неделя 2 (Arbitrage) - 60 тестов

- [ ] test_arbitrage.py - 60 тестов

### Неделя 3 (Commands) - 80 тестов

- [ ] test_balance_command.py - 30 тестов
- [ ] test_game_filters_handlers.py - 50 тестов

### Неделя 4 (Notifications) - 75 тестов

- [ ] test_notification_digest_handler.py - 40 тестов
- [ ] test_market_analytics.py - 35 тестов

---

## 📊 Ожидаемые результаты

| Неделя | Новых тестов | Прирост покрытия | Итоговое покрытие |
|--------|--------------|------------------|-------------------|
| 0 (сейчас) | 0 | 0% | 53.35% |
| 1 | 140 | +3.5% | 56.85% |
| 2 | 60 | +2% | 58.85% |
| 3 | 80 | +1.5% | **60.35%** ✅ |
| 4 | 75 | +1.5% | 61.85% |

**Цель 60% будет достигнута через 3 недели!**

---

## 🎯 Ключевые метрики качества

### Каждый тест должен

- ✅ Следовать **AAA паттерну** (Arrange-Act-Assert)
- ✅ Иметь **описательное имя** (`test_<функция>_<условие>_<результат>`)
- ✅ Быть **независимым** от других тестов
- ✅ Быть **быстрым** (< 100ms для unit тестов)
- ✅ Тестировать **одну вещь**
- ✅ Включать **docstring** с описанием

### Checklist для review

- [ ] Все тесты проходят локально
- [ ] Покрытие модуля увеличилось
- [ ] Нет дублирования кода
- [ ] Использованы фикстуры где необходимо
- [ ] Моки изолируют внешние зависимости
- [ ] Тестированы edge cases
- [ ] Добавлены параметризованные тесты где уместно

---

**Последнее обновление:** 14 декабря 2025 г.
**Статус:** 🟢 Готово к выполнению
