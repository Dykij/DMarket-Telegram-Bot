# 🧪 План тестирования DMarket Telegram Bot

**Дата:** 14 ноября 2024
**Текущее покрытие:** 8% (цель: 80%)
**Статус тестов:** 239 passed, 111 failed, 5 skipped из 355 тестов

---

## 📊 Анализ текущего состояния

### ✅ Хорошо протестированные модули (>50% покрытия)

- `src/dmarket/__init__.py` - 63.64%
- `src/utils/database.py` - 54.44%
- `src/utils/config.py` - 34.62%
- `src/utils/exceptions.py` - 32.52%

### ⚠️ Критичные модули с низким покрытием (<15%)

#### 1. **DMarket API (9.28%)** - КРИТИЧНО 🔴

**Файл:** `src/dmarket/dmarket_api.py`
**Проблемы:**

- ❌ Генерация подписей Ed25519 не работает корректно
- ❌ Парсинг баланса возвращает 0.0 вместо реальных данных
- ⚠️ Нет тестов для всех эндпоинтов API

**Необходимые тесты:**

```python
# tests/dmarket/test_dmarket_api_extended.py

class TestDMarketAPIExtended:
    """Расширенное тестирование DMarket API."""

    # Тесты аутентификации и подписей
    - test_ed25519_signature_generation()
    - test_signature_verification()
    - test_timestamp_format()
    - test_nonce_generation()

    # Тесты всех эндпоинтов
    - test_get_user_items()
    - test_get_user_offers()
    - test_create_offer()
    - test_edit_offer()
    - test_delete_offer()
    - test_buy_offer()
    - test_get_sales_history()
    - test_get_purchase_history()
    - test_get_currency_rates()

    # Тесты обработки ответов
    - test_parse_balance_all_formats()
    - test_parse_items_response()
    - test_parse_error_responses()
    - test_handle_api_rate_limits()
    - test_handle_api_timeouts()
    - test_handle_network_errors()

    # Тесты кэширования
    - test_cache_ttl()
    - test_cache_invalidation()
    - test_cache_per_endpoint()
```

#### 2. **Telegram Bot Handlers (0-15%)** - КРИТИЧНО 🔴

**Файлы:**

- `src/telegram_bot/handlers/*.py`
- `src/telegram_bot/initialization.py` (12.42%)

**Необходимые тесты:**

```python
# tests/telegram_bot/test_initialization.py

class TestBotInitialization:
    """Тестирование инициализации бота."""

    - test_initialize_bot_with_valid_token()
    - test_initialize_bot_with_invalid_token()
    - test_initialize_bot_with_persistence()
    - test_initialize_bot_without_persistence()
    - test_setup_logging()
    - test_register_handlers()
    - test_initialize_services()
    - test_setup_error_handler()
    - test_signal_handlers()
    - test_graceful_shutdown()

# tests/telegram_bot/handlers/test_commands_extended.py

class TestCommandHandlers:
    """Тестирование команд бота."""

    - test_start_command()
    - test_help_command()
    - test_balance_command()
    - test_market_command()
    - test_arbitrage_command()
    - test_settings_command()
    - test_profile_command()
    - test_unknown_command()
    - test_command_with_args()
    - test_command_without_permissions()
    - test_command_rate_limiting()

# tests/telegram_bot/handlers/test_callbacks_extended.py

class TestCallbackHandlers:
    """Тестирование callback handlers."""

    - test_pagination_callback()
    - test_filter_callback()
    - test_action_callback()
    - test_confirm_callback()
    - test_cancel_callback()
    - test_invalid_callback_data()
    - test_expired_callback()
```

#### 3. **Арбитраж (7-8%)** - ВЫСОКИЙ ПРИОРИТЕТ 🟡

**Файлы:**

- `src/dmarket/arbitrage.py` (7.35%)
- `src/dmarket/arbitrage_scanner.py` (7.52%)
- `src/telegram_bot/arbitrage_scanner.py` (7.29%)

**Необходимые тесты:**

```python
# tests/dmarket/test_arbitrage_complete.py

class TestArbitrage:
    """Полное тестирование арбитража."""

    # Поиск возможностей
    - test_find_arbitrage_opportunities_basic()
    - test_find_arbitrage_opportunities_with_filters()
    - test_find_arbitrage_opportunities_multi_game()
    - test_find_arbitrage_opportunities_with_sales_data()
    - test_filter_by_profit_margin()
    - test_filter_by_price_range()
    - test_filter_by_liquidity()

    # Расчеты
    - test_calculate_profit()
    - test_calculate_profit_with_fees()
    - test_calculate_roi()
    - test_rank_opportunities()

    # Исполнение сделок
    - test_execute_arbitrage_trade()
    - test_execute_trade_insufficient_balance()
    - test_execute_trade_item_unavailable()
    - test_execute_trade_price_changed()
    - test_rollback_failed_trade()

    # Внутримаркетный арбитраж
    - test_find_price_anomalies()
    - test_find_trending_items()
    - test_find_mispriced_rare_items()
    - test_comprehensive_intramarket_scan()

# tests/telegram_bot/test_auto_arbitrage.py

class TestAutoArbitrage:
    """Тестирование автоматического арбитража."""

    - test_start_auto_arbitrage()
    - test_stop_auto_arbitrage()
    - test_auto_arbitrage_with_limits()
    - test_auto_arbitrage_notifications()
    - test_auto_arbitrage_error_recovery()
    - test_auto_arbitrage_balance_check()
```

#### 4. **Аналитика и визуализация (0-11%)** - СРЕДНИЙ ПРИОРИТЕТ 🟢

**Файлы:**

- `src/utils/market_analyzer.py` (8.18%)
- `src/utils/analytics.py` (11.51%)
- `src/utils/market_visualizer.py` (4.95%)
- `src/utils/price_analyzer.py` (0%)

**Необходимые тесты:**

```python
# tests/utils/test_market_analyzer_extended.py

class TestMarketAnalyzer:
    """Тестирование анализа рынка."""

    - test_analyze_price_trends()
    - test_analyze_volume_trends()
    - test_detect_anomalies()
    - test_calculate_volatility()
    - test_find_support_resistance()
    - test_analyze_correlations()
    - test_generate_signals()

# tests/utils/test_price_analyzer.py

class TestPriceAnalyzer:
    """Тестирование анализа цен."""

    - test_calculate_moving_average()
    - test_calculate_ema()
    - test_calculate_rsi()
    - test_detect_breakout()
    - test_predict_price_movement()
    - test_analyze_spread()

# tests/utils/test_market_visualizer_extended.py

class TestMarketVisualizerExtended:
    """Расширенное тестирование визуализации."""

    - test_create_line_chart()
    - test_create_candlestick_chart()
    - test_create_volume_chart()
    - test_create_heatmap()
    - test_create_comparison_chart()
    - test_chart_with_indicators()
    - test_chart_export_formats()
    - test_chart_error_handling()
```

#### 5. **История продаж (10%)** - СРЕДНИЙ ПРИОРИТЕТ 🟢

**Файл:** `src/dmarket/sales_history.py`

**Необходимые тесты:**

```python
# tests/dmarket/test_sales_history_complete.py

class TestSalesHistory:
    """Полное тестирование истории продаж."""

    - test_fetch_sales_history()
    - test_parse_sales_data()
    - test_filter_sales_by_date()
    - test_filter_sales_by_item()
    - test_filter_sales_by_game()
    - test_aggregate_sales_stats()
    - test_calculate_average_price()
    - test_identify_trends()
    - test_save_sales_to_db()
    - test_load_sales_from_db()
```

#### 6. **Уведомления и алерты (0-10%)** - СРЕДНИЙ ПРИОРИТЕТ 🟢

**Файлы:**

- `src/telegram_bot/notifier.py` (0%)
- `src/telegram_bot/smart_notifier.py` (9.05%)
- `src/telegram_bot/market_alerts.py` (0%)

**Необходимые тесты:**

```python
# tests/telegram_bot/test_notifications.py

class TestNotifications:
    """Тестирование системы уведомлений."""

    - test_send_notification()
    - test_send_notification_to_multiple_users()
    - test_notification_with_buttons()
    - test_notification_with_image()
    - test_notification_rate_limiting()
    - test_notification_retry_on_failure()

# tests/telegram_bot/test_market_alerts_extended.py

class TestMarketAlerts:
    """Тестирование рыночных алертов."""

    - test_create_price_alert()
    - test_create_volume_alert()
    - test_create_arbitrage_alert()
    - test_trigger_alert()
    - test_delete_alert()
    - test_list_user_alerts()
    - test_alert_with_conditions()
    - test_recurring_alerts()
```

#### 7. **База данных (54%)** - УЛУЧШИТЬ 🟢

**Файл:** `src/utils/database.py` (54.44% - хорошо, но можно лучше)

**Дополнительные тесты:**

```python
# tests/test_database_extended.py

class TestDatabaseExtended:
    """Расширенное тестирование базы данных."""

    - test_transaction_commit()
    - test_transaction_rollback()
    - test_concurrent_access()
    - test_connection_pool()
    - test_query_optimization()
    - test_migration_scripts()
    - test_data_integrity()
    - test_backup_restore()
```

#### 8. **Профили пользователей (29%)** - СРЕДНИЙ ПРИОРИТЕТ 🟢

**Файл:** `src/telegram_bot/user_profiles.py`

**Необходимые тесты:**

```python
# tests/telegram_bot/test_user_profiles_extended.py

class TestUserProfiles:
    """Расширенное тестирование профилей."""

    - test_create_profile()
    - test_update_profile()
    - test_delete_profile()
    - test_profile_settings()
    - test_profile_preferences()
    - test_profile_statistics()
    - test_profile_permissions()
    - test_admin_profile()
    - test_profile_data_migration()
```

#### 9. **WebSocket и real-time (13%)** - НИЗКИЙ ПРИОРИТЕТ 🔵

**Файлы:**

- `src/utils/websocket_client.py` (13.04%)
- `src/dmarket/realtime_price_watcher.py` (10.55%)

**Необходимые тесты:**

```python
# tests/utils/test_websocket_extended.py

class TestWebSocket:
    """Тестирование WebSocket соединений."""

    - test_connect_websocket()
    - test_disconnect_websocket()
    - test_reconnect_on_failure()
    - test_handle_messages()
    - test_send_messages()
    - test_ping_pong()
    - test_connection_timeout()
```

---

## 🎯 Приоритетный план действий

### Фаза 1: Критичные тесты (1-2 дня)

1. ✅ **DMarket API подписи и аутентификация**
   - Исправить генерацию Ed25519 подписей
   - Тесты всех форматов баланса
   - Тесты rate limiting

2. ✅ **Базовые команды бота**
   - /start, /help, /balance
   - Обработка ошибок
   - Проверка разрешений

3. ✅ **Инициализация бота**
   - Корректный запуск/остановка
   - Регистрация handlers
   - Graceful shutdown

### Фаза 2: Важные функции (2-3 дня)

4. ✅ **Арбитраж - основные функции**
   - Поиск возможностей
   - Расчет прибыли
   - Фильтрация

5. ✅ **История продаж**
   - Получение данных
   - Анализ трендов
   - Сохранение в БД

6. ✅ **Callback handlers**
   - Пагинация
   - Фильтры
   - Действия

### Фаза 3: Продвинутые функции (3-5 дней)

7. ✅ **Автоматический арбитраж**
   - Исполнение сделок
   - Обработка ошибок
   - Лимиты и безопасность

8. ✅ **Аналитика и визуализация**
   - Графики
   - Статистика
   - Экспорт данных

9. ✅ **Уведомления и алерты**
   - Отправка уведомлений
   - Smart alerts
   - Rate limiting

### Фаза 4: Интеграционные тесты (2-3 дня)

10. ✅ **End-to-end тесты**
    - Полный цикл арбитража
    - Полный цикл пользовательского взаимодействия
    - Полный цикл аналитики

11. ✅ **Стресс-тесты**
    - Множество пользователей
    - Высокая нагрузка API
    - Длительная работа

---

## 📝 Шаблоны тестов

### Шаблон для async функций

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_async_function():
    """Test async function with mocks."""
    # Arrange
    mock_api = AsyncMock()
    mock_api.get_data.return_value = {"key": "value"}

    # Act
    result = await your_async_function(mock_api)

    # Assert
    assert result == expected_value
    mock_api.get_data.assert_called_once()
```

### Шаблон для Telegram handlers

```python
import pytest
from telegram import Update
from telegram.ext import ContextTypes
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_telegram_handler():
    """Test Telegram bot handler."""
    # Arrange
    update = MagicMock(spec=Update)
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot_data = {}

    # Act
    await your_handler(update, context)

    # Assert
    update.message.reply_text.assert_called_once()
    assert "expected text" in update.message.reply_text.call_args[0][0]
```

### Шаблон для тестов с фикстурами

```python
@pytest.fixture
def mock_dmarket_api():
    """Mock DMarket API client."""
    api = AsyncMock()
    api.get_balance.return_value = {"USD": 10000}
    api.get_market_items.return_value = {"items": []}
    return api

@pytest.mark.asyncio
async def test_with_fixture(mock_dmarket_api):
    """Test using fixture."""
    result = await function_using_api(mock_dmarket_api)
    assert result is not None
```

---

## 🔧 Инструменты для тестирования

### Запуск тестов

```bash
# Все тесты
pytest tests/ --no-cov -v

# Конкретный модуль
pytest tests/dmarket/test_dmarket_api.py -v

# С покрытием
pytest tests/ --cov=src --cov-report=html

# Только failed тесты
pytest tests/ --lf

# Параллельные тесты
pytest tests/ -n auto
```

### Coverage отчеты

```bash
# HTML отчет
pytest --cov=src --cov-report=html
# Откройте htmlcov/index.html

# Terminal отчет
pytest --cov=src --cov-report=term-missing

# XML для CI/CD
pytest --cov=src --cov-report=xml
```

---

## 🎓 Best Practices

1. **AAA Pattern** - Arrange, Act, Assert
2. **Один тест = одна проверка**
3. **Используйте фикстуры** для переиспользуемого кода
4. **Мокайте внешние зависимости** (API, DB, etc.)
5. **Тестируйте edge cases** и ошибки
6. **Имена тестов должны быть описательными**
7. **Используйте parametrize** для тестирования множества сценариев
8. **Изолируйте тесты** - они не должны зависеть друг от друга

---

## 📊 Целевые метрики

- **Покрытие кода:** 80%+
- **Проходящие тесты:** 95%+
- **Критичные модули:** 90%+ покрытие
- **Время выполнения:** < 5 минут для всех тестов

---

**Следующий шаг:** Начните с Фазы 1 (критичные тесты) и постепенно двигайтесь к полному покрытию.
