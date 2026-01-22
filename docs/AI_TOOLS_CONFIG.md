# AI Tools Configuration Guide

Этот проект поддерживает три AI-инструмента для разработки: **GitHub Copilot**, **Claude Code** и **Cursor AI**. Все настройки унифицированы для обеспечения согласованности кода.

## 🔧 Обзор конфигураций

| Инструмент | Основной файл | Дополнительные файлы |
|------------|---------------|----------------------|
| **GitHub Copilot** | `.github/copilot-instructions.md` | `.github/instructions/*.instructions.md`, `.github/prompts/*.prompt.md` |
| **Claude Code** | `CLAUDE.md` | Поддержка `@ref/claude/...` для внешних ссылок |
| **Cursor AI** | `.cursorrules` | `.cursor/rules/*.mdc` (модульные правила) |

---

## 🤖 GitHub Copilot

### Основная конфигурация

**Файл**: `.github/copilot-instructions.md`

Применяется ко всем запросам Copilot Chat, Agent и Code Review в этом репозитории.

### Инструкции по типам файлов

Файлы в `.github/instructions/` применяются автоматически на основе glob-паттернов:

```markdown
---
description: 'Описание правила'
applyTo: 'src/**/*.py'
---

# Заголовок

Правила применяются здесь...
```

### Доступные инструкции

| Файл | applyTo | Описание |
|------|---------|----------|
| `python-style.instructions.md` | `src/**/*.py` | Стиль Python кода |
| `testing.instructions.md` | `tests/**/*.py` | Правила тестирования |
| `workflows.instructions.md` | `.github/workflows/**` | GitHub Actions |
| `api-integration.instructions.md` | `src/dmarket/**`, `src/waxpeer/**` | API интеграции |
| `telegram-bot.instructions.md` | `src/telegram_bot/**` | Telegram handlers |
| `database.instructions.md` | `src/models/**`, `alembic/**` | База данных |
| `documentation.instructions.md` | `docs/**/*.md`, `*.md` | Документация |

### Переиспользуемые промпты

Файлы в `.github/prompts/` можно вызывать в Copilot Chat:

```
/prompt python-async
```

| Файл | Описание |
|------|----------|
| `python-async.prompt.md` | Генерация async кода |
| `test-generator.prompt.md` | Генерация тестов (AAA) |
| `telegram-handler.prompt.md` | Telegram handlers |
| `refactor-early-returns.prompt.md` | Рефакторинг вложенности |
| `add-docstrings.prompt.md` | Google-style docstrings |
| `pydantic-model.prompt.md` | Pydantic v2 модели |
| `error-handling-retry.prompt.md` | Retry логика |

---

## 🧠 Claude Code

### Основная конфигурация

**Файл**: `CLAUDE.md`

Claude автоматически читает этот файл при старте сессии.

### Структура файла

```markdown
# Project Name

## Project Overview
Краткое описание проекта

## Tech Stack
- Python 3.11+
- httpx, structlog, etc.

## Code Conventions
- Правила кодирования

## Rules for Claude
1. Никогда не делать X
2. Всегда делать Y

## Commands
- pytest tests/ -v
- ruff check src/
```

### Иерархия

Claude поддерживает иерархию правил:
1. `~/.claude/CLAUDE.md` - глобальные правила пользователя
2. `CLAUDE.md` в корне проекта - правила проекта
3. `CLAUDE.md` в поддиректории - локальные переопределения

---

## 🎯 Cursor AI

### Основная конфигурация

**Файл**: `.cursorrules`

Простой текстовый файл с правилами, применяемыми ко всему проекту.

### Модульные правила (рекомендуется)

Файлы в `.cursor/rules/*.mdc` с YAML frontmatter:

```markdown
---
description: "Описание правила"
globs: ["src/**/*.py"]
alwaysApply: true
---

# Правила

- Правило 1
- Правило 2
```

### Доступные модули

| Файл | globs | Описание |
|------|-------|----------|
| `python-source.mdc` | `src/**/*.py` | Python код |
| `testing.mdc` | `tests/**/*.py` | Тесты |
| `workflows.mdc` | `.github/workflows/**` | CI/CD |
| `api-integration.mdc` | `src/dmarket/**`, `src/waxpeer/**` | API |
| `telegram-handlers.mdc` | `src/telegram_bot/**` | Telegram |

---

## 📋 Сравнение подходов

| Функция | Copilot | Claude | Cursor |
|---------|---------|--------|--------|
| Глобальные правила | `.github/copilot-instructions.md` | `CLAUDE.md` | `.cursorrules` |
| По типу файлов | `applyTo` glob | Нет (но можно описать) | `globs` |
| Переиспользуемые промпты | `.github/prompts/` | Нет встроенного | Нет встроенного |
| Модульность | Отдельные `.instructions.md` | `@ref/` ссылки | `.cursor/rules/` |
| YAML frontmatter | Да | Нет | Да |
| Исключение агентов | `excludeAgent` | Нет | `excludeAgent` |

---

## 🚀 Быстрый старт

### Для GitHub Copilot

1. Убедитесь что `.github/copilot-instructions.md` в репозитории
2. Правила применяются автоматически в Copilot Chat
3. Используйте `/prompt <name>` для вызова промптов

### Для Claude Code

1. Файл `CLAUDE.md` должен быть в корне проекта
2. Claude прочитает его автоматически при старте
3. Используйте `/init` для генерации базового шаблона

### Для Cursor AI

1. Файл `.cursorrules` в корне проекта
2. Или модульные правила в `.cursor/rules/`
3. Правила применяются автоматически при редактировании

---

## 🔄 Синхронизация правил

При изменении правил обновляйте все три конфигурации для согласованности:

1. **Новый паттерн кодирования** → обновить все три
2. **Новый тип файлов** → добавить в `.github/instructions/` и `.cursor/rules/`
3. **Новый промпт** → только `.github/prompts/`

---

## 🔌 Context7 MCP - Актуальная документация для AI-ассистентов

### Что такое Context7?

[Context7](https://github.com/upstash/context7) - это Model Context Protocol (MCP) сервер, который предоставляет AI-моделям актуальную документацию по библиотекам и фреймворкам. Это решает проблему устаревших знаний LLM-моделей.

### Проблема без Context7

❌ LLM-модели обучены на старых данных и могут:
- Генерировать код с устаревшими методами
- Использовать несуществующие API (галлюцинации)
- Рекомендовать старые версии пакетов

### Решение с Context7

✅ Context7 MCP подтягивает актуальную документацию прямо в контекст LLM:
- Версионно-специфичные примеры кода
- Актуальные API и методы
- Правильный синтаксис для современных версий

### Установка

#### Для Cursor AI

```json
// ~/.cursor/mcp.json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

#### Для Claude Code

```bash
# Remote (рекомендуется)
claude mcp add --header "CONTEXT7_API_KEY: YOUR_API_KEY" --transport http context7 https://mcp.context7.com/mcp

# Local
claude mcp add context7 -- npx -y @upstash/context7-mcp --api-key YOUR_API_KEY
```

### Использование

Добавьте `use context7` в конец промпта:

```
Создай async HTTP клиент для DMarket API с retry логикой. use context7
```

Или укажите конкретную библиотеку:

```
Реализуй WebSocket подключение с использованием httpx. use library /encode/httpx for API and docs.
```

### Полный список библиотек проекта с Context7 ID

#### 🌐 HTTP и сетевые библиотеки

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| httpx | `/encode/httpx` | 0.28+ | Async HTTP клиент |
| aiohttp | `/aio-libs/aiohttp` | 3.13+ | Async HTTP клиент/сервер |
| requests | `/psf/requests` | 2.32+ | HTTP клиент (sync) |
| hishel | `/karpetrosyan/hishel` | 1.1+ | HTTP кэширование |

#### 🤖 Telegram Bot

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| python-telegram-bot | `/python-telegram-bot/python-telegram-bot` | 22.5+ | Telegram Bot API |

#### 🗄️ Базы данных и ORM

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| SQLAlchemy | `/sqlalchemy/sqlalchemy` | 2.0+ | ORM и SQL toolkit |
| alembic | `/sqlalchemy/alembic` | 1.18+ | Миграции БД |
| redis | `/redis/redis-py` | 7.1+ | Redis клиент |
| asyncpg | `/MagicStack/asyncpg` | 0.31+ | PostgreSQL async driver |
| aiosqlite | `/omnilib/aiosqlite` | 0.22+ | SQLite async driver |

#### 📊 Валидация и сериализация

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| Pydantic | `/pydantic/pydantic` | 2.12+ | Валидация данных |
| pydantic-settings | `/pydantic/pydantic-settings` | 2.12+ | Настройки из env |
| orjson | `/ijl/orjson` | 3.11+ | Быстрый JSON парсер |

#### 🧪 Тестирование

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| pytest | `/pytest-dev/pytest` | 9.0+ | Тестовый фреймворк |
| pytest-asyncio | `/pytest-dev/pytest-asyncio` | 1.3+ | Async тесты |
| pytest-cov | `/pytest-dev/pytest-cov` | 7.0+ | Покрытие кода |
| pytest-mock | `/pytest-dev/pytest-mock` | 3.15+ | Моки для pytest |
| hypothesis | `/HypothesisWorks/hypothesis` | 6.150+ | Property-based тестирование |
| vcrpy | `/kevin1024/vcrpy` | 8.1+ | Запись HTTP для тестов |
| factory-boy | `/FactoryBoy/factory_boy` | 3.3+ | Test fixtures |
| faker | `/joke2k/faker` | 40.1+ | Генерация фейковых данных |
| pact-python | `/pact-foundation/pact-python` | 3.2+ | Contract testing |

#### 📝 Логирование и мониторинг

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| structlog | `/hynek/structlog` | 25.5+ | Структурированное логирование |
| sentry-sdk | `/getsentry/sentry-python` | 2.49+ | Error tracking |
| prometheus-client | `/prometheus/client_python` | 0.24+ | Метрики Prometheus |

#### 🔐 Безопасность и криптография

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| cryptography | `/pyca/cryptography` | 46.0+ | Криптографические операции |
| PyJWT | `/jpadilla/pyjwt` | 2.10+ | JWT токены |
| bcrypt | `/pyca/bcrypt` | 5.0+ | Хеширование паролей |
| PyNaCl | `/pyca/pynacl` | 1.6+ | Crypto библиотека |

#### ⚡ Async утилиты

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| anyio | `/agronholm/anyio` | 4.12+ | Async compatibility |
| asyncer | `/tiangolo/asyncer` | 0.0.12 | Async утилиты |
| aiofiles | `/Tinche/aiofiles` | 25.1+ | Async файловые операции |
| aiocache | `/aio-libs/aiocache` | 0.12+ | Async кэширование |
| aiometer | `/florimondmanca/aiometer` | 1.0+ | Async rate limiting |

#### 📈 Data Science и ML

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| pandas | `/pandas-dev/pandas` | 2.3+ | DataFrames |
| numpy | `/numpy/numpy` | 2.4+ | Численные вычисления |
| scikit-learn | `/scikit-learn/scikit-learn` | 1.8+ | Machine Learning |
| matplotlib | `/matplotlib/matplotlib` | 3.10+ | Визуализация |
| seaborn | `/mwaskom/seaborn` | 0.13+ | Statistical plots |
| plotly | `/plotly/plotly.py` | 6.5+ | Интерактивные графики |

#### 🛠️ Утилиты

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| tenacity | `/jd/tenacity` | 9.1+ | Retry логика |
| circuitbreaker | `/fabfuel/circuitbreaker` | 2.1+ | Circuit breaker pattern |
| click | `/pallets/click` | 8.3+ | CLI интерфейсы |
| typer | `/tiangolo/typer` | 0.21+ | Modern CLI |
| rich | `/Textualize/rich` | 14.2+ | Rich text в терминале |
| schedule | `/dbader/schedule` | 1.2+ | Планировщик задач |
| apscheduler | `/agronholm/apscheduler` | 3.11+ | Advanced scheduler |
| python-dotenv | `/theskumar/python-dotenv` | 1.2+ | Загрузка .env |
| dependency-injector | `/ets-labs/python-dependency-injector` | 4.48+ | DI контейнер |

#### 🔍 Качество кода

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| ruff | `/astral-sh/ruff` | 0.14+ | Linter + Formatter |
| mypy | `/python/mypy` | 1.19+ | Static type checker |
| black | `/psf/black` | 26.1+ | Code formatter |
| bandit | `/PyCQA/bandit` | 1.9+ | Security linter |
| vulture | `/jendrikseipp/vulture` | 2.14 | Dead code finder |
| interrogate | `/econchick/interrogate` | 1.7+ | Docstring coverage |

#### 📚 Документация

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| mkdocs | `/mkdocs/mkdocs` | 1.6+ | Документация |
| mkdocs-material | `/squidfunk/mkdocs-material` | 9.7+ | Material theme |
| sphinx | `/sphinx-doc/sphinx` | 9.0+ | Python docs |

#### 🔗 MCP (Model Context Protocol)

| Библиотека | Context7 ID | Версия | Описание |
|------------|-------------|--------|----------|
| mcp | `/modelcontextprotocol/python-sdk` | 1.25+ | MCP SDK |

### Автоматический вызов

Добавьте правило в настройки IDE чтобы Context7 вызывался автоматически:

**Cursor**: `Settings > Rules`
**Claude Code**: `CLAUDE.md`

```
Always use Context7 MCP when I need library/API documentation, 
code generation, setup or configuration steps.
```

### Пример использования с библиотеками проекта

```bash
# Для httpx (async HTTP клиент)
"Создай async клиент для DMarket API с retry логикой. use library /encode/httpx for API and docs."

# Для python-telegram-bot
"Добавь inline keyboard с пагинацией. use library /python-telegram-bot/python-telegram-bot for API and docs."

# Для SQLAlchemy 2.0
"Создай async модель для хранения торговых данных. use library /sqlalchemy/sqlalchemy for API and docs."

# Для Pydantic v2
"Добавь валидацию для конфигурации бота. use library /pydantic/pydantic for API and docs."

# Для pytest + pytest-asyncio
"Напиши тесты для async API клиента. use library /pytest-dev/pytest for API and docs."

# Для structlog
"Добавь структурированное логирование с JSON форматом. use library /hynek/structlog for API and docs."
```

### Конфигурация MCP серверов для проекта

#### Полная конфигурация для Cursor

```json
// ~/.cursor/mcp.json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

#### Полная конфигурация для Claude Code

```json
// ~/.claude/claude_desktop_config.json или ~/.config/claude/config.json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {
        "CONTEXT7_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

Или через CLI:
```bash
claude mcp add --header "CONTEXT7_API_KEY: YOUR_API_KEY" --transport http context7 https://mcp.context7.com/mcp
```

### Когда использовать

✅ **Рекомендуется для:**
- Генерации кода с использованием библиотек
- Настройки и конфигурации пакетов
- Изучения новых API

❌ **НЕ нужен для:**
- Бизнес-логики проекта
- Рефакторинга существующего кода
- Простых изменений

---

## 📚 Ссылки

- [GitHub Copilot Custom Instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions)
- [Claude CLAUDE.md Guide](https://www.builder.io/blog/claude-md-guide)
- [Cursor Rules Documentation](https://cursor.com/docs/context/rules)
- [Context7 MCP GitHub](https://github.com/upstash/context7)
- [Context7 Documentation](https://context7.com/docs)
