# Анализ 10 оставшихся ошибок handler тестов

**Дата**: 25 ноября 2025 г.
**Статус**: После исправления decorator - из 173 упавших стало **10 упавших** (94.6% успеха)

---

## 📊 Категории оставшихся ошибок

### 1️⃣ Тесты ожидают reraise exception (3 теста) ⚠️ РЕШЕНИЕ: Нужно изменить тесты

#### a) `test_handle_dmarket_arbitrage_rate_limit_error`
- **Файл**: `tests/telegram_bot/handlers/test_arbitrage_callback_impl.py:153`
- **Проблема**: Тест ожидает `pytest.raises(APIError)`, но decorator перехватывает
- **Решение**: Изменить тест - проверять `reply_text` вместо exception:

```python
# БЫЛО:
with pytest.raises(APIError, match="Rate limit exceeded"):
    await handle_dmarket_arbitrage_impl(...)

# ДОЛЖНО БЫТЬ:
await handle_dmarket_arbitrage_impl(...)
mock_update.message.reply_text.assert_called()
call_text = mock_update.message.reply_text.call_args.args[0]
assert "❌" in call_text or "ошибка" in call_text.lower()
```

#### b) `test_initialize_api_failure`
- **Файл**: `tests/telegram_bot/handlers/test_dmarket_handlers.py:104`
- **Проблема**: Тест ожидает `pytest.raises(Exception, match="API Error")`
- **Решение**: Decorator теперь sync (не async), НЕ отправляет сообщения (это init метод, не handler)
- **Вариант 1**: Убрать decorator из `initialize_api` (это не Telegram handler)
- **Вариант 2**: Добавить `reraise=True` для init метода

#### c) `test_balance_command_exception`
- **Файл**: `tests/telegram_bot/handlers/test_dmarket_handlers.py:205`
- **Проблема**: Тест ожидает `pytest.raises(Exception, match="API Error")`
- **Решение**: Изменить тест аналогично (a)

---

### 2️⃣ Mock проблемы с getenv (2 теста) 🐛 РЕШЕНИЕ: Исправить тесты

#### d) `test_with_env_keys`
- **Файл**: `tests/telegram_bot/handlers/test_dmarket_status.py:75`
- **Проблема**: `AttributeError: does not have attribute 'getenv'`
- **Причина**: Тест делает `patch('src.telegram_bot.handlers.dmarket_status.getenv')`, но в модуле нет такого импорта
- **Решение**: Патчить `os.getenv` вместо `dmarket_status.getenv`:

```python
# БЫЛО:
with patch('src.telegram_bot.handlers.dmarket_status.getenv', ...):

# ДОЛЖНО БЫТЬ:
with patch('os.getenv', ...):
```

#### e) `test_without_keys`
- **Файл**: `tests/telegram_bot/handlers/test_dmarket_status.py:109`
- **Проблема**: Та же - AttributeError
- **Решение**: То же - патчить `os.getenv`

---

### 3️⃣ BUG в коде arbitrage_scanner (4 теста) 🐛 РЕШЕНИЕ: Исправить код

#### f) `test_with_profile_keys`
- **Файл**: `tests/telegram_bot/handlers/test_dmarket_status.py:70`
- **Проблема**: `'bool' object has no attribute 'get'` в `arbitrage_scanner.py:553`
- **Root Cause**:
  ```python
  # src/dmarket/arbitrage_scanner.py:553
  error_message = balance_response.get("error", {}).get(...)
  # balance_response = False (bool), а не dict!
  ```
- **Решение**: Добавить проверку типа:
  ```python
  if balance_response is False or not balance_response:
      # Обработать ошибку без .get()
      error_message = "Не удалось получить баланс"
  elif isinstance(balance_response, dict):
      error_message = balance_response.get("error", {}).get("message", "Неизвестная ошибка")
  ```

#### g) `test_401_error`
- **Файл**: `tests/telegram_bot/handlers/test_dmarket_status.py:164`
- **Проблема**: То же - `'bool' object has no attribute 'get'`
- **Решение**: То же - исправить arbitrage_scanner.py

#### h) `test_general_exception`
- **Файл**: `tests/telegram_bot/handlers/test_dmarket_status.py:221`
- **Проблема**: `_close_client not called`
- **Root Cause**: При exception `_close_client()` не вызывается
- **Решение**: Добавить `try/finally` в dmarket_status.py:
  ```python
  async def dmarket_status_command(...):
      api = None
      try:
          api = DMarketAPI(...)
          # ... логика
      finally:
          if api:
              await api._close_client()
  ```

#### i) `test_client_always_closed`
- **Файл**: `tests/telegram_bot/handlers/test_dmarket_status.py:275`
- **Проблема**: То же - `_close_client not called`
- **Решение**: То же - try/finally

---

### 4️⃣ Callback query handlers (1 тест) 🔧 РЕШЕНИЕ: Улучшить decorator

#### j) `test_alerts_callback_exception_handling`
- **Файл**: `tests/telegram_bot/handlers/test_market_alerts_handler.py:234`
- **Проблема**: `callback_query.answer не вызван` при exception
- **Root Cause**: Decorator автоматически вызывает `update.message.reply_text()`, но НЕ `update.callback_query.answer()`
- **Решение**: Расширить decorator для поддержки callback queries:
  ```python
  # В exceptions.py async_wrapper:
  if not reraise and args and hasattr(args[0], "callback_query"):
      try:
          update = args[0]
          if update.callback_query:
              await update.callback_query.answer(
                  text=f"❌ {default_error_message}",
                  show_alert=True
              )
      except Exception as answer_error:
          logger_instance.exception(f"Не удалось отправить answer: {answer_error}")
  elif not reraise and args and hasattr(args[0], "message"):
      # ... существующий код для message
  ```

---

## 🎯 План исправлений

### Приоритет 1: Исправить BUG в коде (критично)
- [ ] `arbitrage_scanner.py:553` - добавить проверку типа `balance_response`
- [ ] `dmarket_status.py` - добавить `try/finally` для `_close_client()`

### Приоритет 2: Улучшить decorator (1 строка кода)
- [ ] `exceptions.py` - добавить поддержку `callback_query.answer()`

### Приоритет 3: Исправить тесты (не код)
- [ ] 3 теста - убрать `pytest.raises`, проверять `reply_text` вместо exception
- [ ] 2 теста - патчить `os.getenv` вместо `dmarket_status.getenv`

---

## 📈 Прогресс

- **До исправления**: 173 упавших handler теста
- **После decorator fix**: **10 упавших** (94.6% успеха!)
- **После всех исправлений**: Ожидаем **0-3 упавших**

---

## ⏱️ Оценка времени

- **Приоритет 1** (bug fixes): 15 минут
- **Приоритет 2** (decorator): 5 минут
- **Приоритет 3** (тесты): 10 минут

**Всего**: ~30 минут для полного исправления handlers.
