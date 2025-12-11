# 🔧 Руководство по рефакторингу проекта DMarket Telegram Bot

**Дата создания**: 11 декабря 2025 г.
**Последнее обновление**: 11 декабря 2025 г.
**Версия**: 1.0

---

## 📋 Обзор

Этот документ содержит полный анализ кодовой базы проекта на предмет необходимого рефакторинга. Используя инструмент **Ruff**, мы выявили **103 проблемы сложности кода** в 25 файлах проекта.

## 🎯 Цели рефакторинга

1. **Уменьшить цикломатическую сложность** функций (C901 < 12)
2. **Сократить количество ветвлений** в функциях (PLR0912 < 15)
3. **Уменьшить количество операторов** в функциях (PLR0915 < 60)
4. **Улучшить читаемость и поддерживаемость** кода
5. **Облегчить тестирование** через декомпозицию

---

## 📊 Статистика проблем

### Общая статистика

| Категория проблемы | Код | Количество | Описание |
|--------------------|-----|------------|----------|
| Высокая сложность | C901 | 49 | Функции с цикломатической сложностью > 12 |
| Много ветвлений | PLR0912 | 26 | Функции с количеством if/elif/else > 15 |
| Много операторов | PLR0915 | 24 | Функции с количеством statements > 60 |
| Много return | PLR0911 | 3 | Функции с количеством return > 8 |
| Много аргументов | PLR0913 | 1 | Функции с количеством параметров > 10 |
| **ИТОГО** | | **103** | |

### Распределение по модулям

| Модуль | Количество файлов | Количество проблем |
|--------|-------------------|-------------------|
| `src/dmarket/` | 7 | 33 |
| `src/telegram_bot/handlers/` | 7 | 30 |
| `src/telegram_bot/commands/` | 2 | 6 |
| `src/utils/` | 9 | 34 |
| **ИТОГО** | **25** | **103** |

---

## 🔝 Топ-10 файлов требующих рефакторинга

### 1. ✅ src/dmarket/dmarket_api.py (10 проблем)

**Статус**: ⚡ РЕФАКТОРИНГ ЗАВЕРШЁН (11.12.2025)

**Проблемы**:
- ✅ `get_balance()`: C901=~~53~~→**13**, PLR0912=~~59~~→**0**, PLR0915=~~200~~→**67**
- ⚠️ `_request()`: C901=27, PLR0912=29, PLR0915=110
- ⚠️ `direct_balance_request()`: C901=13, PLR0915=72

**Результат**:
- Complexity снижена на 77%
- Удалено 143 строки дублирующегося кода
- Созданы 4 helper метода
- Улучшена тестируемость

### 2. ⚠️ src/telegram_bot/handlers/market_alerts_handler.py (4 проблемы)

**Статус**: ❌ ТРЕБУЕТ РЕФАКТОРИНГА

**Самая критичная функция**: `alerts_callback()`
- Complexity (C901): **34** (worst in telegram_bot!)
- Branches (PLR0912): **43**
- Statements (PLR0915): **106**
- Размер: **218 строк**

**Другие проблемы**:
- `alerts_command()`: C901=13

**Рекомендуемый подход**:
```python
# До (command dispatcher в одной функции)
async def alerts_callback(update, context):
    action = query.data.split(":")[1]
    if action == "toggle":
        # 50 строк логики
    elif action == "subscribe_all":
        # 30 строк логики
    elif action == "unsubscribe_all":
        # 30 строк логики
    # ... ещё 10 actions

# После (отдельные handler функции)
ALERT_ACTIONS = {
    "toggle": handle_toggle_action,
    "subscribe_all": handle_subscribe_all_action,
    "unsubscribe_all": handle_unsubscribe_all_action,
    # ... mapping для всех actions
}

async def alerts_callback(update, context):
    action = query.data.split(":")[1]
    handler = ALERT_ACTIONS.get(action)
    if handler:
        await handler(update, context, query)
    else:
        await query.answer("Неверное действие")
```

### 3. ⚠️ src/dmarket/intramarket_arbitrage.py (10 проблем)

**Статус**: ❌ ТРЕБУЕТ РЕФАКТОРИНГА

**Проблемные функции**:
- `find_trending_items()`: C901=27, PLR0912=27, PLR0915=70
- `find_price_anomalies()`: C901=24, PLR0912=25, PLR0915=65
- `find_mispriced_rare_items()`: C901=22, PLR0912=22
- `scan_for_intramarket_opportunities()`: C901=17, PLR0912=17

**Рекомендуемый подход**: Extract Method для validation, filtering, и scoring logic

### 4. ⚠️ src/telegram_bot/commands/balance_command.py (3 проблемы)

**Статус**: ❌ ТРЕБУЕТ РЕФАКТОРИНГА

**Проблемная функция**: `check_balance_command()`
- Complexity (C901): **29**
- Branches (PLR0912): **39**
- Statements (PLR0915): **108**

**Рекомендуемый подход**: Extract formatting helpers

```python
# До
async def check_balance_command(update, context):
    # 108 строк форматирования, валидации, логики

# После
async def check_balance_command(update, context):
    balance_data = await fetch_balance(user_id)
    formatted_message = format_balance_message(balance_data)
    keyboard = create_balance_keyboard(balance_data)
    await send_balance_response(update, formatted_message, keyboard)

def format_balance_message(balance_data):
    # Форматирование текста
    pass

def create_balance_keyboard(balance_data):
    # Создание клавиатуры
    pass
```

### 5. ⚠️ src/telegram_bot/handlers/callbacks.py (3 проблемы)

**Статус**: ❌ ТРЕБУЕТ РЕФАКТОРИНГА

**Проблемная функция**: `button_callback_handler()`
- Complexity (C901): **38** (worst overall in handlers!)
- Branches (PLR0912): **39**
- Statements (PLR0915): **96**

**Рекомендуемый подход**: Command dispatcher pattern (аналогично #2)

### 6. ⚠️ src/telegram_bot/handlers/settings_handlers.py (3 проблемы)

**Проблемная функция**: `settings_callback()`
- Complexity (C901): **19**
- Branches (PLR0912): **22**
- Statements (PLR0915): **91**

### 7. ⚠️ src/utils/telegram_error_handlers.py (3 проблемы)

**Проблемные функции**:
- `telegram_error_boundary()`: C901=26, PLR0915=66
- `decorator()`: C901=25, PLR0915=64
- `wrapper()`: C901=24, PLR0912=23, PLR0915=63

**Рекомендуемый подход**: Extract error message formatters

### 8. ⚠️ src/dmarket/arbitrage_sales_analysis.py (3 проблемы)

**Проблемные функции**:
- `evaluate_arbitrage_potential()`: C901=21, PLR0912=21
- `estimate_time_to_sell()`: C901=16, PLR0912=22
- `analyze_price_trends()`: C901=13

### 9. ⚠️ src/dmarket/arbitrage_scanner.py (5 проблем)

**Проблемные функции**:
- `auto_trade_items()`: C901=18, PLR0912=19, PLR0915=81
- `_analyze_item()`: C901=18, PLR0912=18
- `scan_game()`: C901=16, PLR0912=17, PLR0915=61
- `scan_level()`: C901=14

### 10. ⚠️ src/utils/market_analyzer.py (1 проблема)

**Проблемная функция**: `analyze_market_opportunity()`
- Complexity (C901): **23**
- Branches (PLR0912): **25**
- Statements (PLR0915): **67**

---

## 🛠️ Паттерны рефакторинга

### 1. Extract Method

**Когда использовать**: Функция слишком длинная или делает несколько вещей

**Пример**:
```python
# До
async def get_balance(self):
    # Проверка ключей (10 строк)
    if not self.public_key or not self.secret_key:
        return {"error": True, ...}
    
    # Попытка прямого запроса (50 строк)
    try:
        direct_response = await self.direct_balance_request()
        # ... 40 строк обработки
    except Exception:
        pass
    
    # Попытка через эндпоинты (70 строк)
    for endpoint in endpoints:
        # ... 60 строк логики
    
    # Парсинг ответа (80 строк)
    if "usd" in response:
        # ... 70 строк парсинга
    
    # Возврат результата (20 строк)
    return {...}

# После
async def get_balance(self):
    if not self._validate_api_keys():
        return self._create_error_response("Missing API keys", 401)
    
    try:
        direct_result = await self._try_direct_request()
        if direct_result:
            return direct_result
    except Exception:
        pass
    
    response = await self._try_all_endpoints()
    if not response:
        return self._create_error_response("No response", 500)
    
    balance_data = self._parse_balance_response(response)
    return self._create_balance_response(**balance_data)
```

### 2. Command Dispatcher Pattern

**Когда использовать**: Большой if-elif chain для обработки различных команд/actions

**Пример**:
```python
# До
async def callback_handler(update, context):
    action = query.data.split(":")[1]
    
    if action == "action1":
        # 50 строк
    elif action == "action2":
        # 30 строк
    elif action == "action3":
        # 40 строк
    # ... 10+ actions

# После
class CallbackDispatcher:
    def __init__(self):
        self.handlers = {
            "action1": self._handle_action1,
            "action2": self._handle_action2,
            "action3": self._handle_action3,
        }
    
    async def dispatch(self, update, context):
        action = query.data.split(":")[1]
        handler = self.handlers.get(action)
        if handler:
            await handler(update, context)
        else:
            await query.answer("Unknown action")
    
    async def _handle_action1(self, update, context):
        # Dedicated method for action1
        pass
```

### 3. Strategy Pattern

**Когда использовать**: Различные алгоритмы для одной задачи (например, парсинг разных форматов)

**Пример**:
```python
# До
def parse_response(response):
    if "format1_key" in response:
        # Parse format 1 (20 строк)
    elif "format2_key" in response:
        # Parse format 2 (20 строк)
    elif "format3_key" in response:
        # Parse format 3 (20 строк)

# После
class ResponseParser:
    def __init__(self):
        self.parsers = [
            Format1Parser(),
            Format2Parser(),
            Format3Parser(),
        ]
    
    def parse(self, response):
        for parser in self.parsers:
            if parser.can_parse(response):
                return parser.parse(response)
        return None

class Format1Parser:
    def can_parse(self, response):
        return "format1_key" in response
    
    def parse(self, response):
        # Parse format 1
        return {...}
```

### 4. Early Return

**Когда использовать**: Уменьшить вложенность и упростить логику

**Пример**:
```python
# До
def process(data):
    if data is not None:
        if data.is_valid():
            if data.has_permission():
                # Process (30 строк)
                result = ...
                return result
            else:
                return error1
        else:
            return error2
    else:
        return error3

# После
def process(data):
    if data is None:
        return error3
    
    if not data.is_valid():
        return error2
    
    if not data.has_permission():
        return error1
    
    # Process (30 строк)
    result = ...
    return result
```

---

## 📝 Чеклист для рефакторинга

### Перед рефакторингом

- [ ] Запустить существующие тесты: `pytest tests/`
- [ ] Проверить покрытие: `pytest --cov=src`
- [ ] Зафиксировать текущее поведение (записать expected output)
- [ ] Создать ветку: `git checkout -b refactor/module-name`

### Во время рефакторинга

- [ ] Делать маленькие, инкрементальные изменения
- [ ] Коммитить после каждого успешного изменения
- [ ] Запускать тесты после каждого изменения
- [ ] Сохранять публичные API (не breaking changes)
- [ ] Добавлять docstrings для новых методов
- [ ] Сохранять type hints

### После рефакторинга

- [ ] Запустить все тесты: `pytest tests/`
- [ ] Проверить покрытие: `pytest --cov=src`
- [ ] Запустить линтинг: `ruff check src/`
- [ ] Запустить type checking: `mypy src/`
- [ ] Обновить документацию (если нужно)
- [ ] Создать PR с описанием изменений
- [ ] Использовать prefix `refactor:` в commit message

---

## 🎯 План рефакторинга по приоритетам

### Фаза 1: Критические файлы (40-60 часов)

**Приоритет P0** - Блокирующие проблемы:

1. ✅ **src/dmarket/dmarket_api.py::get_balance** (ЗАВЕРШЕНО)
   - Complexity 53 → 13 (-77%)
   - Statements 200 → 67 (-67%)
   - Время: 6 часов ✅

2. **src/telegram_bot/handlers/callbacks.py::button_callback_handler**
   - Complexity: 38, Branches: 39, Statements: 96
   - Подход: Command dispatcher
   - Время: 8-10 часов

3. **src/telegram_bot/handlers/market_alerts_handler.py::alerts_callback**
   - Complexity: 34, Branches: 43, Statements: 106
   - Подход: Command dispatcher
   - Время: 8-10 часов

4. **src/telegram_bot/commands/balance_command.py::check_balance_command**
   - Complexity: 29, Branches: 39, Statements: 108
   - Подход: Extract formatting helpers
   - Время: 6-8 часов

5. **src/dmarket/dmarket_api.py::_request**
   - Complexity: 27, Branches: 29, Statements: 110
   - Подход: Extract retry logic, error handling
   - Время: 8-10 часов

### Фаза 2: Важные файлы (60-80 часов)

**Приоритет P1** - Важные для поддержки:

6. **src/dmarket/intramarket_arbitrage.py** (4 функции)
   - find_trending_items (C901=27)
   - find_price_anomalies (C901=24)
   - find_mispriced_rare_items (C901=22)
   - scan_for_intramarket_opportunities (C901=17)
   - Подход: Extract validation, filtering, scoring
   - Время: 20-25 часов

7. **src/utils/telegram_error_handlers.py** (3 функции)
   - telegram_error_boundary (C901=26)
   - decorator (C901=25)
   - wrapper (C901=24)
   - Подход: Extract error formatters
   - Время: 12-15 часов

8. **src/utils/market_analyzer.py::analyze_market_opportunity**
   - Complexity: 23, Branches: 25, Statements: 67
   - Подход: Extract scoring logic
   - Время: 6-8 часов

9. **src/dmarket/arbitrage_sales_analysis.py** (3 функции)
   - evaluate_arbitrage_potential (C901=21)
   - estimate_time_to_sell (C901=16)
   - analyze_price_trends (C901=13)
   - Подход: Extract calculation helpers
   - Время: 15-18 часов

10. **src/dmarket/arbitrage_scanner.py** (4 функции)
    - auto_trade_items (C901=18)
    - _analyze_item (C901=18)
    - scan_game (C901=16)
    - scan_level (C901=14)
    - Подход: Extract filtering and scoring
    - Время: 18-22 часа

### Фаза 3: Остальные файлы (40-60 часов)

**Приоритет P2** - Улучшения качества:

11-25. Остальные 15 файлов с minor проблемами
    - Время: 40-60 часов

---

## 📈 Метрики качества

### Целевые показатели

| Метрика | Текущее | Целевое | Статус |
|---------|---------|---------|--------|
| Сложность (C901) | 103 проблемы | 0 проблем | 🔴 7% done |
| Max complexity | 53 | <15 | 🟡 13 (текущий max) |
| Ветвления (PLR0912) | 26 проблем | 0 проблем | 🔴 4% done |
| Операторы (PLR0915) | 24 проблемы | 0 проблем | 🔴 4% done |
| Средняя длина функции | ~80 строк | <50 строк | 🔴 |

### Прогресс

- ✅ **Фаза 0**: Анализ завершён (100%)
- 🟡 **Фаза 1**: Критические файлы (7% done - 1/5 files)
- 🔴 **Фаза 2**: Важные файлы (0% done)
- 🔴 **Фаза 3**: Остальные файлы (0% done)

**Общий прогресс**: 7/103 проблем решены (7%)

---

## 🔧 Инструменты

### Анализ сложности

```bash
# Проверка сложности всего проекта
ruff check src/ --select C90,PLR0911,PLR0912,PLR0913,PLR0915

# Проверка конкретного файла
ruff check src/dmarket/dmarket_api.py --select C90,PLR0912,PLR0915

# Статистика проблем
ruff check src/ --select C90,PLR0912,PLR0915 --statistics

# JSON вывод для автоматизации
ruff check src/ --select C90 --output-format=json
```

### Тестирование после рефакторинга

```bash
# Запуск всех тестов
pytest tests/

# Запуск тестов для конкретного модуля
pytest tests/dmarket/test_dmarket_api.py

# С покрытием
pytest --cov=src --cov-report=html --cov-report=term-missing

# Только быстрые тесты
pytest -m "not slow"
```

### Type checking

```bash
# Проверка типов
mypy src/

# С более строгими правилами
mypy src/ --strict

# Конкретный файл
mypy src/dmarket/dmarket_api.py
```

---

## 📚 Дополнительные ресурсы

### Документация проекта

- `docs/code_quality_tools_guide.md` - Руководство по Ruff, MyPy, Black
- `docs/CONTRIBUTING.md` - Правила внесения изменений
- `docs/ARCHITECTURE.md` - Архитектура проекта
- `ROADMAP.md` - План развития
- `.github/copilot-instructions.md` - Правила кодирования

### Внешние ресурсы

- [Refactoring Guru](https://refactoring.guru/) - Паттерны рефакторинга
- [Martin Fowler - Refactoring](https://martinfowler.com/books/refactoring.html) - Книга о рефакторинге
- [Ruff Rules](https://docs.astral.sh/ruff/rules/) - Документация правил Ruff
- [Python Patterns](https://python-patterns.guide/) - Паттерны проектирования в Python

---

## 🤝 Вклад в рефакторинг

Если хотите помочь с рефакторингом:

1. Выберите файл из списка приоритетов
2. Создайте issue с описанием планируемых изменений
3. Создайте ветку: `refactor/имя-модуля`
4. Следуйте паттернам из этого документа
5. Добавляйте/обновляйте тесты
6. Создайте PR с prefix `refactor:` в заголовке

**Пример PR**:
```
refactor(dmarket_api): Extract helper methods from _request method

- Extracted retry logic into _handle_retry()
- Extracted error handling into _handle_api_error()
- Reduced complexity from 27 to 12 (-56%)
- Added unit tests for new helper methods

Fixes #123
```

---

**Дата последнего обновления**: 11 декабря 2025 г.
**Автор**: GitHub Copilot Agent
**Версия документа**: 1.0
