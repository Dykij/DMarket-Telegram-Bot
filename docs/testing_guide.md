# Руководство по запуску тестов

**Версия**: 2.0
**Последнее обновление**: 19 ноября 2025 г.

---

В этом руководстве объясняется, как правильно запустить тесты в проекте DMarket Tools с корректной настройкой PYTHONPATH.

## Настройка PYTHONPATH

Тесты в проекте DMarket Tools используют относительные импорты из корневой директории проекта. Для корректной работы этих импортов необходимо добавить корневую директорию проекта в PYTHONPATH.

### Windows (PowerShell)

```powershell
# Временная настройка в текущей сессии
$env:PYTHONPATH = "$(Get-Location)"

# Запуск всех тестов
python -m pytest tests

# Запуск конкретного теста
python -m pytest tests/test_bot_v2.py
```

### Linux/macOS (Bash)

```bash
# Временная настройка в текущей сессии
export PYTHONPATH=$(pwd)

# Запуск всех тестов
python -m pytest tests

# Запуск конкретного теста
python -m pytest tests/test_bot_v2.py
```

## Использование VS Code

### Настройка VS Code для тестирования

1. Откройте VS Code settings.json (Ctrl+Shift+P -> Preferences: Open Settings (JSON))
2. Добавьте следующие настройки:

```json
{
    "python.testing.pytestEnabled": true,
    "python.envFile": "${workspaceFolder}/.env",
    "python.analysis.extraPaths": ["${workspaceFolder}"]
}
```

3. Теперь вы можете использовать встроенную в VS Code панель тестирования для запуска тестов.

## Запуск конкретных тестов

### Запуск по имени модуля

```
python -m pytest tests/test_bot_v2.py
```

### Запуск по имени теста

```
python -m pytest tests/test_bot_v2.py::test_start_command
```

### Запуск с повышенной детализацией

```
python -m pytest tests/test_bot_v2.py -v
```

## Отладка тестов

### Отладка в VS Code

1. Установите точки останова в коде теста
2. Выберите тест в панели тестирования VS Code
3. Щелкните правой кнопкой мыши и выберите "Debug Test"

### Отладка с помощью pdb

```
python -m pytest tests/test_bot_v2.py --pdb
```

## Дополнительные опции pytest

- `--pdb`: Вход в отладчик при ошибке
- `-v`: Подробный вывод
- `-xvs`: Отключает захват вывода, полезно для отладки
- `--no-header --no-summary -q`: Минимальный вывод
- `-k "expression"`: Запускает тесты, соответствующие выражению

## Примечания

- Тесты используют асинхронные функции, требующие поддержки pytest-asyncio
- Файл конфигурации pytest находится в `pyproject.toml`
- При запуске тестов через VS Code убедитесь, что выбран правильный интерпретатор Python

---

## VCR.py - Запись и воспроизведение HTTP-взаимодействий

VCR.py позволяет записывать HTTP-взаимодействия с внешними API и воспроизводить
их в тестах. Это обеспечивает:

- **Детерминированность** - одинаковые ответы при каждом запуске
- **Скорость** - нет сетевых задержек
- **Офлайн-тестирование** - тесты работают без доступа к API
- **CI/CD** - не нужны реальные API ключи

### Конфигурация

Конфигурация VCR находится в `tests/conftest_vcr.py`. Кассеты (записи HTTP)
хранятся в `tests/cassettes/`.

### Использование в тестах

```python
import pytest

@pytest.mark.vcr()
@pytest.mark.asyncio()
async def test_get_balance(vcr_cassette_async):
    """Тест получения баланса с записью HTTP."""
    api = DMarketAPI(public_key="test", secret_key="test")
    balance = await api.get_balance()
    assert "balance" in balance
```

### Основные фикстуры

| Фикстура              | Описание                          |
| --------------------- | --------------------------------- |
| `vcr_cassette`        | Автоматическое имя кассеты        |
| `vcr_cassette_async`  | Для async тестов (httpx, aiohttp) |
| `vcr_cassette_custom` | Кастомное имя кассеты             |
| `vcr_cassette_dir`    | Путь к директории кассет модуля   |

### Режимы записи

```bash
# Первый запуск - запись кассет
pytest tests/dmarket/test_api.py

# Записать только новые кассеты
pytest --vcr-record=new_episodes tests/

# Перезаписать все кассеты
pytest --vcr-record=all tests/dmarket/test_api.py

# Не записывать, только воспроизведение
pytest --vcr-record=none tests/
```

### Структура кассет

```text
tests/cassettes/
├── dmarket/
│   ├── test_dmarket_api/
│   │   ├── test_get_balance.yaml
│   │   └── test_get_market_items.yaml
│   └── test_arbitrage_scanner/
│       └── test_scan_level.yaml
└── telegram/
    └── test_bot_commands/
        └── test_start.yaml
```

### Фильтрация чувствительных данных

VCR автоматически фильтрует:

- `X-Api-Key` - API ключ DMarket
- `X-Sign-Date` - timestamp подписи
- `X-Request-Sign` - HMAC подпись
- `Authorization` - токены авторизации
- `Cookie` - куки сессии

### Пример: Миграция теста с httpx-mock на VCR

**До (httpx-mock):**

```python
async def test_get_balance(httpx_mock):
    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        json={"balance": 100.50}
    )
    api = DMarketAPI(...)
    balance = await api.get_balance()
    assert balance["balance"] == 100.50
```

**После (VCR.py):**

```python
@pytest.mark.vcr()
async def test_get_balance(vcr_cassette_async):
    # Первый запуск: реальный API вызов, запись в кассету
    # Последующие запуски: воспроизведение из кассеты
    api = DMarketAPI(...)
    balance = await api.get_balance()
    assert balance["balance"] >= 0
```

### Полезные советы

1. **Коммитьте кассеты в git** - они содержат ожидаемые ответы API
2. **Перезаписывайте при изменении API** - `--vcr-record=all`
3. **Используйте `@pytest.mark.vcr()`** для маркировки тестов
4. **Проверяйте фильтрацию** - убедитесь, что секреты не попадают в кассеты
