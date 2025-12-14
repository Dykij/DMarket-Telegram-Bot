# End-to-End Testing Guide

## Обзор

E2E тесты проверяют работу бота от начала до конца, симулируя реальные пользовательские сценарии.

## Установка

```bash
# Установить зависимости
pip install playwright pytest-playwright
python -m playwright install
```

## Структура

```
tests/e2e/
├── conftest.py           # Фикстуры и настройки
├── test_user_flow.py     # Тесты пользовательских сценариев
├── test_arbitrage.py     # Тесты арбитража
├── test_targets.py       # Тесты таргетов
└── pages/                # Page Object Model
    ├── base_page.py
    ├── main_menu.py
    └── arbitrage_page.py
```

## Запуск

```bash
# Все E2E тесты
pytest tests/e2e/ -v

# С UI (headful mode)
pytest tests/e2e/ --headed

# Медленная скорость для отладки
pytest tests/e2e/ --slowmo 500

# Скриншоты при ошибках
pytest tests/e2e/ --screenshot on-failure
```

## Примеры тестов

### Базовый сценарий

```python
@pytest.mark.e2e
async def test_user_starts_bot(telegram_page):
    """Тест запуска бота."""
    # Отправить /start
    await telegram_page.send_command("/start")

    # Проверить приветствие
    message = await telegram_page.wait_for_message()
    assert "Добро пожаловать" in message

    # Проверить главное меню
    buttons = await telegram_page.get_buttons()
    assert "🔍 Арбитраж" in buttons
```

### Полный флоу арбитража

```python
@pytest.mark.e2e
async def test_arbitrage_scan_flow(telegram_page):
    """Тест полного флоу сканирования арбитража."""
    # 1. Открыть меню арбитража
    await telegram_page.click_button("🔍 Арбитраж")

    # 2. Выбрать уровень
    await telegram_page.click_button("📊 Стандарт")

    # 3. Выбрать игру
    await telegram_page.click_button("🎮 CS:GO")

    # 4. Дождаться результатов
    message = await telegram_page.wait_for_message(timeout=30000)
    assert "возможност" in message.lower()

    # 5. Проверить наличие кнопок с предметами
    buttons = await telegram_page.get_buttons()
    assert len(buttons) > 0
```

## CI/CD Integration

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright pytest-playwright
          python -m playwright install --with-deps

      - name: Run E2E tests
        run: pytest tests/e2e/ -v --screenshot on-failure
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}

      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-screenshots
          path: test-results/
```

## Лучшие практики

1. **Изоляция**: Каждый тест независим
2. **Надежность**: Используйте явные ожидания
3. **Скорость**: Группируйте похожие тесты
4. **Очистка**: Удаляйте тестовые данные после прогона
5. **Скриншоты**: Сохраняйте при ошибках для отладки
