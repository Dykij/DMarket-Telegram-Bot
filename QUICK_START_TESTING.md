# 🚀 Quick Start: Улучшение покрытия тестами

> Быстрое руководство для разработчиков

---

## 📊 Текущая ситуация

```
Текущее покрытие: 53.35%
Целевое покрытие: 60%+
Недостающее:      ~7% (~355 тестов)
```

---

## 🎯 С чего начать?

### 1. Прочитайте документацию (5 минут)

- [ ] `LOW_COVERAGE_ANALYSIS.md` - полный анализ файлов с низким покрытием
- [ ] `TODO_UNIT_TESTS.md` - детальный план задач на 4 недели
- [ ] `docs/testing_guide.md` - руководство по написанию тестов

### 2. Выберите задачу (по приоритету)

#### 🔥 КРИТИЧЕСКИЙ ПРИОРИТЕТ

**Неделя 1: DMarket API** (самое важное!)
```bash
# Начните с основного клиента
tests/dmarket/api/test_client.py      # 40 тестов, 0% → 70%
tests/dmarket/api/test_wallet.py      # 25 тестов, 0% → 75%
tests/dmarket/api/test_market.py      # 30 тестов, 0% → 75%
```

**Неделя 2: Arbitrage** (core функциональность)
```bash
tests/dmarket/test_arbitrage.py       # 60 тестов, 0% → 80%
```

#### ⚡ ВЫСОКИЙ ПРИОРИТЕТ

**Неделя 3: Commands**
```bash
tests/telegram_bot/commands/test_balance_command.py          # 30 тестов
tests/telegram_bot/handlers/game_filters/test_handlers.py    # 50 тестов
```

---

## 📝 Шаблон теста (Copy-Paste)

```python
"""
Тесты для модуля <module_name>.

Этот модуль тестирует <краткое описание функциональности>.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.<path>.<module> import <ClassName>


class Test<ClassName><Feature>:
    """Тесты для <feature_description>."""

    def test_<function>_<condition>_<expected_result>(self):
        """Тест <что проверяется>."""
        # Arrange (Подготовка)
        <setup_test_data>

        # Act (Действие)
        result = <call_function>

        # Assert (Проверка)
        assert result == <expected>
        assert <additional_checks>

    @pytest.mark.asyncio
    async def test_<async_function>_<condition>_<result>(self):
        """Тест асинхронной функции."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.method = AsyncMock(return_value=<value>)

        # Act
        result = await <call_async_function>

        # Assert
        assert result is not None
        mock_client.method.assert_called_once()

    @pytest.mark.parametrize("input,expected", [
        (1, 10),
        (2, 20),
        (3, 30),
    ])
    def test_<function>_parametrized(self, input, expected):
        """Тест с параметризацией."""
        # Act
        result = <function>(input)

        # Assert
        assert result == expected
```

---

## ⚡ Быстрый старт за 10 минут

### Шаг 1: Создайте тестовый файл

```bash
# Создайте директорию (если нужно)
mkdir -p tests/dmarket/api

# Создайте файл
touch tests/dmarket/api/test_client.py
```

### Шаг 2: Скопируйте базовую структуру

```python
"""Тесты для DMarket API Client."""
import pytest
from unittest.mock import AsyncMock, patch

from src.dmarket.api.client import DMarketClient


class TestDMarketClientInitialization:
    """Тесты инициализации клиента."""

    def test_client_init_with_valid_credentials(self):
        """Тест создания клиента с валидными credentials."""
        # Arrange & Act
        client = DMarketClient(
            public_key="test_public",
            secret_key="test_secret"
        )

        # Assert
        assert client.public_key == "test_public"
        assert client.secret_key == "test_secret"
```

### Шаг 3: Запустите тесты

```bash
# Запустите конкретный файл
pytest tests/dmarket/api/test_client.py -v

# Проверьте покрытие
pytest tests/dmarket/api/test_client.py --cov=src.dmarket.api.client --cov-report=term-missing
```

### Шаг 4: Добавьте больше тестов

Следуйте checklist из `TODO_UNIT_TESTS.md` для вашего модуля.

---

## 🎯 Checklist для каждого теста

Перед коммитом убедитесь:

- [ ] ✅ Тест следует **AAA паттерну** (Arrange-Act-Assert)
- [ ] ✅ Имя теста **описательное**: `test_<функция>_<условие>_<результат>`
- [ ] ✅ Тест **независим** от других тестов
- [ ] ✅ Тест **быстрый** (< 100ms)
- [ ] ✅ Тест проверяет **одну вещь**
- [ ] ✅ Добавлен **docstring** с описанием
- [ ] ✅ Внешние зависимости **замокированы**
- [ ] ✅ Протестированы **edge cases**

---

## 🛠️ Полезные команды

```bash
# Запустить все тесты
pytest

# Запустить с покрытием
pytest --cov=src --cov-report=html

# Запустить только новые тесты
pytest tests/dmarket/api/ -v

# Запустить тесты с определенным маркером
pytest -m "not slow"

# Запустить тесты параллельно (быстрее)
pytest -n auto

# Показать медленные тесты
pytest --durations=10

# Запустить только упавшие тесты
pytest --lf

# Запустить с verbose output
pytest -vv

# Проверить покрытие конкретного модуля
pytest --cov=src.dmarket.api.client --cov-report=term-missing
```

---

## 📚 Примеры распространенных паттернов

### Мокирование HTTP запросов

```python
@pytest.mark.asyncio
async def test_api_call_success(self):
    """Тест успешного API вызова."""
    # Arrange
    client = DMarketClient("key", "secret")

    with patch.object(client, '_request') as mock_request:
        mock_request.return_value = {"status": "ok"}

        # Act
        result = await client.get_balance()

        # Assert
        assert result["status"] == "ok"
        mock_request.assert_called_once()
```

### Параметризованные тесты

```python
@pytest.mark.parametrize("price,commission,expected", [
    (10.0, 7.0, 9.30),
    (100.0, 7.0, 93.00),
    (1.0, 7.0, 0.93),
])
def test_calculate_net_price(self, price, commission, expected):
    """Тест расчета цены с комиссией."""
    result = calculate_net_price(price, commission)
    assert abs(result - expected) < 0.01
```

### Тестирование исключений

```python
def test_invalid_input_raises_error(self):
    """Тест выброса ошибки при невалидном вводе."""
    with pytest.raises(ValueError) as exc_info:
        process_item(price=-10)

    assert "negative price" in str(exc_info.value)
```

### Использование фикстур

```python
@pytest.fixture
def mock_api_client():
    """Фикстура для мокированного API клиента."""
    client = AsyncMock(spec=DMarketAPI)
    client.get_balance = AsyncMock(return_value={"usd": 10000})
    return client


def test_with_fixture(mock_api_client):
    """Тест использует фикстуру."""
    balance = await mock_api_client.get_balance()
    assert balance["usd"] == 10000
```

---

## 🎓 Обучающие ресурсы

### Внутренние
- `docs/testing_guide.md` - полное руководство по тестированию
- `docs/code_quality_tools_guide.md` - инструменты качества
- `tests/` - примеры существующих тестов

### Внешние
- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)

---

## 📊 Трекинг прогресса

Используйте этот чеклист для отслеживания прогресса:

### Неделя 1: DMarket API
- [ ] `test_client.py` - 40 тестов
- [ ] `test_wallet.py` - 25 тестов
- [ ] `test_market.py` - 30 тестов
- [ ] `test_trading.py` - 25 тестов
- [ ] `test_targets_api.py` - 20 тестов

**Прогресс:** [ ] 0/140 тестов

### Неделя 2: Arbitrage
- [ ] `test_arbitrage.py` - 60 тестов

**Прогресс:** [ ] 0/60 тестов

### Неделя 3: Commands
- [ ] `test_balance_command.py` - 30 тестов
- [ ] `test_game_filters_handlers.py` - 50 тестов

**Прогресс:** [ ] 0/80 тестов

### Неделя 4: Notifications
- [ ] `test_notification_digest_handler.py` - 40 тестов
- [ ] `test_market_analytics.py` - 35 тестов

**Прогресс:** [ ] 0/75 тестов

---

## 🐛 Troubleshooting

### Проблема: Тесты не находят модули

**Решение:**
```bash
# Убедитесь, что PYTHONPATH настроен
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Или установите проект в режиме разработки
pip install -e .
```

### Проблема: Асинхронные тесты не работают

**Решение:**
```python
# Убедитесь, что у вас установлен pytest-asyncio
pip install pytest-asyncio

# Добавьте маркер
@pytest.mark.asyncio
async def test_async_function():
    ...
```

### Проблема: Моки не работают

**Решение:**
```python
# Используйте правильный путь для patch
# ❌ Неправильно
@patch('src.module.function')

# ✅ Правильно
@patch('src.module.ClassName.method')
```

---

## ✨ Tips & Tricks

1. **Начните с простых тестов** - не пытайтесь сразу покрыть все edge cases
2. **Используйте TDD** - пишите тест перед кодом
3. **Один тест = одна проверка** - не смешивайте несколько assert'ов для разных вещей
4. **Моки важны** - изолируйте внешние зависимости
5. **Фикстуры экономят время** - переиспользуйте настройки
6. **Параметризация = меньше кода** - тестируйте множественные сценарии
7. **Читайте существующие тесты** - смотрите на примеры в проекте

---

## 🎯 Следующие шаги

1. **Выберите модуль** из `TODO_UNIT_TESTS.md`
2. **Создайте тестовый файл** по шаблону выше
3. **Напишите 5-10 тестов** для начала
4. **Запустите тесты** и проверьте покрытие
5. **Создайте Pull Request** с новыми тестами
6. **Повторите** для следующего модуля

---

**Удачи! 🚀**

Если возникнут вопросы, обращайтесь к:
- `LOW_COVERAGE_ANALYSIS.md` - детальный анализ
- `TODO_UNIT_TESTS.md` - подробный план
- `docs/testing_guide.md` - руководство по тестированию
