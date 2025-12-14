# AGENTS.md — Scripts Module

> 📖 Вспомогательные скрипты для DMarket Telegram Bot
> Полные инструкции: `.github/copilot-instructions.md`

## 🎯 Назначение

`scripts/` содержит CLI-утилиты для:

- Запуска и управления ботом
- Диагностики и мониторинга
- Работы с базой данных
- Разработки и отладки

## 📁 Ключевые скрипты

### Запуск и управление

| Скрипт               | Описание                   | Использование                                      |
| -------------------- | -------------------------- | -------------------------------------------------- |
| `run_bot.py`         | Основной запуск бота       | `python scripts/run_bot.py [--debug] [--no-lock]`  |
| `health_check.py`    | Проверка здоровья сервисов | `python scripts/health_check.py [--cron] [--json]` |
| `validate_config.py` | Валидация конфигурации     | `python scripts/validate_config.py`                |

### База данных

| Скрипт               | Описание               | Использование                                         |
| -------------------- | ---------------------- | ----------------------------------------------------- |
| `init_db.py`         | Инициализация БД       | `python scripts/init_db.py`                           |
| `backup_database.py` | Бэкап БД               | `python scripts/backup_database.py --output backups/` |
| `migrate_users.py`   | Миграция пользователей | `python scripts/migrate_users.py`                     |

### Разработка и отладка

| Скрипт                | Описание               | Использование                                |
| --------------------- | ---------------------- | -------------------------------------------- |
| `check_code.py`       | Проверка качества кода | `python scripts/check_code.py`               |
| `check_cyrillic.py`   | Проверка на кириллицу  | `python scripts/check_cyrillic.py src/`      |
| `debug_suite.py`      | Отладочный набор       | `python scripts/debug_suite.py`              |
| `run_tests.py`        | Запуск тестов          | `python scripts/run_tests.py`                |
| `run_module_tests.py` | Тесты модуля           | `python scripts/run_module_tests.py dmarket` |

### Мониторинг и Sentry

| Скрипт                      | Описание              | Использование                              |
| --------------------------- | --------------------- | ------------------------------------------ |
| `sentry_cleanup.py`         | Очистка Sentry issues | `python scripts/sentry_cleanup.py`         |
| `github_actions_monitor.py` | Мониторинг CI/CD      | `python scripts/github_actions_monitor.py` |
| `run_monitor.ps1`           | PowerShell мониторинг | `./scripts/run_monitor.ps1`                |
| `run_monitor.sh`            | Bash мониторинг       | `./scripts/run_monitor.sh`                 |

### DMarket API тестирование

| Скрипт                         | Описание             | Использование                                 |
| ------------------------------ | -------------------- | --------------------------------------------- |
| `dmarket_api_example.py`       | Примеры API          | `python scripts/dmarket_api_example.py`       |
| `check_offers.py`              | Проверка предложений | `python scripts/check_offers.py`              |
| `test_balance.py`              | Тест баланса         | `python scripts/test_balance.py`              |
| `test_database_performance.py` | Тест БД              | `python scripts/test_database_performance.py` |

## ⚠️ Критические правила

### 1. Всегда добавляй путь к проекту

```python
import sys
from pathlib import Path

# Добавляем корень проекта в path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Теперь можно импортировать
from src.dmarket.dmarket_api import DMarketAPI
```

### 2. Используй argparse для CLI

```python
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="My Script")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--output", type=str, default="output/", help="Output directory")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    main(args)
```

### 3. Возвращай exit code

```python
def main() -> int:
    """Main function.

    Returns:
        0 on success, 1 on failure
    """
    try:
        # Логика
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 4. Логирование в файл и консоль

```python
import logging
import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/script.log"),
        logging.StreamHandler(),
    ],
)
```

### 5. Загружай .env

```python
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv не установлен
```

## 🏃 Типовые сценарии

### Запуск бота в production

```bash
# 1. Валидация конфигурации
python scripts/validate_config.py

# 2. Health check
python scripts/health_check.py

# 3. Запуск бота
python scripts/run_bot.py
```

### Развертывание с нуля

```bash
# 1. Создать .env
python scripts/create_env_file.py

# 2. Инициализировать БД
python scripts/init_db.py

# 3. Валидация
python scripts/validate_config.py

# 4. Запуск
python scripts/run_bot.py
```

### Диагностика проблем

```bash
# 1. Проверить конфигурацию
python scripts/validate_config.py

# 2. Проверить сервисы
python scripts/health_check.py --json

# 3. Проверить DMarket API
python scripts/test_balance.py

# 4. Проверить код
python scripts/check_code.py
```

### Cron задачи

```bash
# Health check каждые 5 минут (crontab)
*/5 * * * * /path/to/venv/bin/python /path/to/scripts/health_check.py --cron

# Бэкап БД ежедневно
0 3 * * * /path/to/venv/bin/python /path/to/scripts/backup_database.py
```

## 📂 deployment/

Содержит скрипты для развертывания:

- Docker конфигурация
- Kubernetes манифесты
- CI/CD пайплайны

## 🧪 Тестирование скриптов

```python
import subprocess

def test_validate_config_runs():
    """Test that validate_config.py runs without error."""
    result = subprocess.run(
        ["python", "scripts/validate_config.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0

def test_health_check_json_output():
    """Test health_check.py JSON output format."""
    result = subprocess.run(
        ["python", "scripts/health_check.py", "--json"],
        capture_output=True,
        text=True
    )
    import json
    data = json.loads(result.stdout)
    assert "all_healthy" in data
    assert "checks" in data
```

## ⚠️ Типичные ошибки

1. **`ModuleNotFoundError: No module named 'src'`**
   - Добавьте `sys.path.insert(0, str(Path(__file__).parent.parent))`

2. **Скрипт не находит .env**
   - Запускайте из корня проекта: `python scripts/script.py`

3. **Права доступа на .sh файлы**
   - `chmod +x scripts/*.sh`

4. **Кодировка вывода в Windows**
   - Добавьте `# -*- coding: utf-8 -*-` в начало файла

## 📚 Документация

- [QUICK_START.md](../docs/QUICK_START.md) — Быстрый старт
- [deployment.md](../docs/deployment.md) — Развертывание
- [DEBUG_WORKFLOW.md](../docs/DEBUG_WORKFLOW.md) — Отладка

---

*Следуй `.github/copilot-instructions.md` для полных правил разработки.*
