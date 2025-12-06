# Анализ 236 упавших тестов

**Дата**: 25 ноября 2025 г.
**Источник**: `.pytest_cache/v/cache/lastfailed`
**Всего упавших**: 236 тестов

---

## 📊 Категоризация по модулям

### 1. **Telegram Bot Handlers** - 173 теста (73.3%)

#### 1.1 Auto Arbitrage - 2 теста
- `tests/telegram_bot/test_auto_arbitrage.py` - весь модуль упал
- `tests/dmarket/test_auto_arbitrage.py` - весь модуль упал

#### 1.2 Market Alerts Handler - 27 тестов
```
tests/telegram_bot/handlers/test_market_alerts_handler.py:
- TestAlertsCommand: 2 теста (exception handling)
- TestAlertsCallback: 2 теста (exception handling)
- TestAlertsCommand: 2 теста (no/with subscriptions)
- TestAlertsCallback: 5 тестов (toggle, subscribe/unsubscribe, my_alerts)
- TestRegisterAlertsHandlers: 1 тест
- TestInitializeAlertsManager: 1 тест
- TestUpdateAlertsKeyboard: 2 теста
- TestShowUserAlertsList: 3 теста
- TestShowCreateAlertForm: 1 тест
- TestShowAlertsSettings: 2 теста
- TestAlertsCallbackAdditional: 6 тестов
```

#### 1.3 Intramarket Handler - 7 тестов
```
tests/telegram_bot/test_intramarket_handler.py:
- TestStartArbitrage: 1 тест
- TestHandleIntramarketCallback: 6 тестов (anomaly, trend, rare, invalid, no_results, error)
```

#### 1.4 DMarket Status Handler - 6 тестов
```
tests/telegram_bot/handlers/test_dmarket_status.py:
- TestDMarketStatusBasic: 3 теста (with profile keys, env keys, without keys)
- TestDMarketStatusErrors: 2 теста (401 error, general exception)
- TestDMarketStatusIntegration: 1 тест (client always closed)
```

#### 1.5 Scanner Handler - 2 теста
```
tests/telegram_bot/handlers/test_scanner_handler.py:
- test_handle_level_scan_exception
- test_handle_market_overview_exception
```

#### 1.6 Target Handler - 1 тест
```
tests/telegram_bot/handlers/test_target_handler.py:
- test_handle_target_callback_smart_action
```

#### 1.7 Game Filter Handlers - 56 тестов
```
tests/telegram_bot/test_game_filter_handlers.py (весь модуль):
- Определение констант: 6 тестов (cs2 categories/rarities/exteriors, dota2 heroes/rarities/slots)
- Управление фильтрами: 5 тестов (get/update filters)
- Клавиатуры: 2 теста (csgo/dota2)
- Описание фильтров: 2 теста
- API параметры: 2 теста
- Обработчики: 16 тестов (различные коллбэки для игр)
- Дополнительные: 23 теста
```

#### 1.8 Arbitrage Callback Implementation - 5 тестов
```
tests/telegram_bot/handlers/test_arbitrage_callback_impl.py:
- test_arbitrage_callback_impl_shows_menu
- test_handle_dmarket_arbitrage_boost_success
- test_handle_dmarket_arbitrage_rate_limit_error
- test_handle_game_selection_impl_shows_menu
- test_handle_game_selected_impl_saves_game
```

#### 1.9 Notifier - 42 теста
```
tests/telegram_bot/test_notifier.py (весь модуль):
- Load/Save alerts: 3 теста
- Add price alert: 3 теста
- Remove price alert: 3 теста
- Get user alerts: 3 теста
- Update user settings: 3 теста
- Format alert message: 2 теста
- Get current price: 4 теста
- Multiple alerts: 3 теста
- Error handling: 3 теста
- Check price alert: 8 тестов
- Check all alerts: 7 тестов
```

#### 1.10 Sales Analysis Handlers - 11 тестов
```
tests/telegram_bot/test_sales_analysis_handlers.py:
- test_handle_sales_analysis_success
- test_handle_sales_analysis_no_data
- test_handle_sales_analysis_api_error
- test_handle_sales_analysis_missing_item_name
- test_handle_arbitrage_with_sales (2 теста)
- test_handle_liquidity_analysis
- test_handle_sales_volume_stats
- test_get_trend_emoji
- test_get_liquidity_emoji
```

#### 1.11 Price Alerts Handler - 34 теста
```
tests/telegram_bot/test_price_alerts_handler.py:
- TestPriceAlertsHandlerInitialization: 2 теста
- TestEnsureWatcherStarted: 3 теста
- TestHandlePriceAlertsCommand: 2 теста
- TestHandleAlertListCallback: 3 теста
- TestHandleAddAlertCallback: 3 теста
- TestHandleItemNameInput: 3 теста
- TestHandleAlertPriceInput: 5 тестов
- TestHandleAlertConditionCallback: 4 теста
- TestHandleRemoveAlertCallback: 2 теста
- TestHandleCancel: 2 теста
- TestGetHandlers: 3 теста
- TestIntegrationScenarios: 2 теста
```

---

### 2. **Models** - 1 тест (0.4%)

```
tests/models/test_user.py:
- TestUserPreferencesModel - весь тест-класс упал
```

---

### 3. **Database & Caching** - 13 тестов (5.5%)

#### 3.1 SQLite Fallback - 9 тестов
```
tests/test_sqlite_fallback.py:
- TestSQLiteFallback: 9 тестов (connection, tables, models, indexes, constraints, concurrent writes)
- TestDatabaseManagerSQLite: 4 теста
- TestSQLiteVsPostgreSQL: 2 теста
- TestSQLiteIntegration: 1 тест
```

#### 3.2 Database Caching - 4 теста
```
tests/utils/test_database_caching.py:
- TestCacheConsistency: 1 тест (cache_consistency_after_update)
- TestDatabaseCachedQueries: 3 теста (cached basic, non-existent, invalidate)
```

---

### 4. **Utils** - 3 теста (1.3%)

```
tests/utils/test_sentry_breadcrumbs.py:
- TestTradingBreadcrumbs: 2 теста (minimal, full)
- TestAPIBreadcrumbs: 1 тест (success)
```

---

### 5. **Integration Tests** - 46 тестов (19.5%)

#### 5.1 Full Workflows - 2 теста
```
tests/integration/test_full_workflows.py:
- TestErrorRecoveryWorkflows: 1 тест (scan_with_partial_api_failure)
- TestConcurrentOperations: 1 тест (concurrent_user_creation)
```

#### 5.2 Arbitrage Edge Cases - 13 тестов
```
tests/integration/test_arbitrage_edge_cases.py:
- TestArbitrageScannerEdgeCases: 7 тестов (missing price, invalid format, API errors, extreme ranges, concurrent, rate limit, partial data)
- TestArbitrageScannerPerformance: 2 теста (large dataset, multiple pages)
- TestArbitrageScannerFiltering: 2 теста (minimum profit, category)
```

#### 5.3 Targets Edge Cases - 18 тестов
```
tests/integration/test_targets_edge_cases.py:
- TestTargetsEdgeCases: 11 тестов (minimum/maximum price, special attributes, batch, duplicate, exceeds limit, nonexistent, filters, pagination, unicode, history)
- TestTargetsValidation: 6 тестов (zero/negative price, zero/exceeds amount, empty title, invalid currency)
```

---

## 🔍 Анализ по типам ошибок

### ✅ **ПОДТВЕРЖДЕННАЯ ПРИЧИНА #1: Отсутствующие файлы модулей**

**Критичность**: 🔴 КРИТИЧНО

Обнаружено отсутствие ключевых файлов:

1. ❌ `tests/telegram_bot/test_auto_arbitrage.py` - **НЕ СУЩЕСТВУЕТ**
2. ❌ `tests/dmarket/test_auto_arbitrage.py` - **НЕ СУЩЕСТВУЕТ**
3. ❌ `src/telegram_bot/market_alerts.py` - **НЕ СУЩЕСТВУЕТ** (импортируется в `market_alerts_handler.py`)

**Последствия**:
- 27+ тестов в `test_market_alerts_handler.py` падают из-за `ImportError` при импорте `from src.telegram_bot.market_alerts import get_alerts_manager`
- 2 модуля auto_arbitrage вообще отсутствуют в проекте
- Невозможно запустить функциональность управления уведомлениями

**Решение**:
- Либо создать отсутствующие модули
- Либо удалить зависимые тесты из `.pytest_cache/lastfailed`
- Либо закомментировать импорты и создать заглушки

---

### Гипотезы о причинах (требуется проверка запуском тестов):

#### 1. **Fixture/Mock проблемы** (средняя вероятность)
- Telegram bot handlers требуют moк update/context объектов
- DMarket API клиент требует мок HTTP responses
- Database требует мок SQLAlchemy session

#### 2. **Async/Await проблемы**
- Многие тесты используют `pytest-asyncio`
- Возможны проблемы с event loop

#### 3. **Import ошибки** (✅ ПОДТВЕРЖДЕНО - см. выше)
- ✅ `src/telegram_bot/market_alerts.py` отсутствует
- ❌ Циклические импорты (не проверено)

#### 4. **Deprecated API**
- python-telegram-bot 20.7+ изменил API
- Старые тесты могут использовать устаревшие методы

#### 5. **Database проблемы**
- SQLite fallback тесты требуют правильной настройки БД
- Connection pool issues

---

## 📋 План действий

### Приоритет 1 (КРИТИЧНО) - Блокирующие тесты:

1. **Auto Arbitrage** (2 модуля) - блокирует основной функционал
2. **DMarket Status** (6 тестов) - блокирует проверку статуса API
3. **Scanner Handler** (2 теста) - блокирует сканирование

### Приоритет 2 (ВАЖНО) - Функциональные тесты:

4. **Market Alerts** (27 тестов) - система уведомлений
5. **Price Alerts** (34 теста) - ценовые алерты
6. **Notifier** (42 теста) - базовая система оповещений
7. **Intramarket Handler** (7 тестов) - внутренний арбитраж

### Приоритет 3 (СРЕДНЕЕ) - Вспомогательные:

8. **Game Filters** (56 тестов) - фильтрация по играм
9. **Sales Analysis** (11 тестов) - анализ продаж
10. **Integration Tests** (46 тестов) - интеграционное тестирование

### Приоритет 4 (НИЗКОЕ) - Edge Cases:

11. **SQLite Fallback** (16 тестов) - fallback на SQLite
12. **Database Caching** (4 теста) - кэширование БД
13. **Sentry Breadcrumbs** (3 теста) - логирование в Sentry
14. **Models** (1 тест) - модели данных

---

## 🎯 Следующие шаги

1. **Запустить конкретный упавший тест** для просмотра трейса ошибки:
   ```bash
   pytest tests/telegram_bot/test_auto_arbitrage.py -v
   ```

2. **Категоризировать по реальным ошибкам** (не гипотезам)

3. **Исправить по приоритетам** (начиная с P1)

4. **Запустить regression suite** после каждого исправления
