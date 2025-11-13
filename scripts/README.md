# 📊 GitHub Actions Monitor

Скрипт для мониторинга и анализа GitHub Actions workflows с расчетом success rate.

## 🎯 Возможности

- 📈 Расчет Success Rate для каждого workflow
- 📊 Детальная статистика запусков
- 💡 Автоматические рекомендации по улучшению
- 📝 Генерация детальных отчетов в Markdown
- 🔍 Анализ проваленных jobs и steps
- ⚡ Мониторинг времени выполнения

## 🚀 Быстрый старт

### Windows (PowerShell)

```powershell
# Использование wrapper-скрипта (рекомендуется)
.\scripts\run_monitor.ps1

# Или напрямую с настройкой кодировки
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
python scripts/github_actions_monitor.py
```

### Linux/macOS

```bash
# Сделать скрипт исполняемым (первый раз)
chmod +x scripts/run_monitor.sh

# Запуск
./scripts/run_monitor.sh

# Или напрямую
python scripts/github_actions_monitor.py
```

## 📋 Требования

- Python 3.11+
- Установленные зависимости: `pip install -r requirements.txt`
- (Опционально) GitHub Personal Access Token для увеличения rate limit

### Установка GitHub Token

Для увеличения лимита API запросов к GitHub:

```bash
# Получить токен: https://github.com/settings/tokens
# Установить переменную окружения

# Windows PowerShell
$env:GITHUB_TOKEN = "your_token_here"

# Linux/macOS
export GITHUB_TOKEN="your_token_here"
```

## 📊 Пример вывода

```
📊 Анализ GitHub Actions Workflows

       📈 Success Rate по Workflows
┏━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ Workflow        ┃ Total ┃ ✅ Success ┃ ❌ Failed ┃  Success ┃ Status ┃
┃                 ┃       ┃           ┃           ┃     Rate ┃        ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
┃ Pre-commit      ┃     7 ┃         7 ┃         0 ┃   100.0% ┃   ✅   ┃
┃ Checks          ┃       ┃           ┃           ┃          ┃        ┃
┃ Python Tests    ┃     5 ┃         4 ┃         1 ┃    80.0% ┃   ⚠️    ┃
┃ Code Quality    ┃     7 ┃         6 ┃         1 ┃    85.7% ┃   ✅   ┃
└─────────────────┴───────┴───────────┴───────────┴──────────┴────────┘

📊 Общая статистика:
  • Всего запусков: 35
  • Успешных: 28
  • Overall Success Rate: 80.0%
  • Среднее время: 2.3 мин
```

## 📝 Отчеты

Отчеты сохраняются в директории `build/reports/`:

```
build/reports/github_actions_report_YYYYMMDD_HHMMSS.md
```

Каждый отчет содержит:

- 📈 Общую статистику
- 📊 Метрики по каждому workflow
- 🔍 Анализ проваленных jobs
- 💡 Рекомендации по улучшению
- 📋 Детальные шаги для исправления

## ⚙️ Настройка

### Целевой Success Rate

По умолчанию: **80%**

Изменить в коде:

```python
# scripts/github_actions_monitor.py
self.target_success_rate = 80.0  # Измените на желаемое значение
```

### Репозиторий

```python
# scripts/github_actions_monitor.py
REPO_OWNER = "Dykij"
REPO_NAME = "DMarket-Telegram-Bot"
```

## 🔧 Устранение неполадок

### Проблема: Некорректное отображение эмодзи в Windows

**Решение**: Используйте `run_monitor.ps1` или установите UTF-8 кодировку:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### Проблема: Rate limit exceeded

**Решение**: Установите GitHub Token:

```bash
export GITHUB_TOKEN="your_token_here"
```

### Проблема: CancelledError при прерывании

**Решение**: Обновлено в последней версии. Теперь корректно обрабатывается `Ctrl+C`.

## 📚 Документация

- [GitHub Actions Monitor - Быстрый старт](../docs/MONITOR_QUICK_START.md)
- [GitHub Actions - Мониторинг](../docs/github_actions_monitoring.md)
- [Документация GitHub API](https://docs.github.com/en/rest/actions)

## 🎯 Цели проекта

| Метрика              | Цель  | Текущее |
| -------------------- | ----- | ------- |
| Overall Success Rate | ≥ 80% | 57.1%   |
| Pre-commit Checks    | ≥ 95% | 100.0%  |
| Python Tests         | ≥ 80% | 20.0%   |
| Code Quality         | ≥ 80% | 57.1%   |
| Security Analysis    | ≥ 80% | 57.1%   |

## 🤝 Вклад в проект

Приветствуются улучшения и предложения! См. [CONTRIBUTING.md](../docs/CONTRIBUTING.md)

## 📄 Лицензия

См. [LICENSE](../LICENSE)
