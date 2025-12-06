# 🔄 CI/CD Pipeline Documentation

**Дата**: 23 ноября 2025 г.
**Версия**: 1.0

---

## 📋 Обзор

Проект использует GitHub Actions для автоматизации процессов тестирования, проверки качества кода и развертывания. Все workflows настроены для обеспечения высокого качества кода и надежности релизов.

## 🔧 Workflows

### 1. CI Pipeline (`ci.yml`)

**Триггеры:**

- Push в ветки `main`, `develop`
- Pull Request в `main`, `develop`
- Ручной запуск (workflow_dispatch)

**Основные этапы:**

#### Lint and Format Check

- ✅ Проверка кода с помощью Ruff
- ✅ Проверка форматирования Ruff
- ✅ Проверка типов с MyPy

#### Tests

- ✅ Запуск тестов на Python 3.10, 3.11, 3.12
- ✅ Генерация coverage отчетов
- ✅ Параллельное выполнение (pytest-xdist)
- ✅ Кэширование зависимостей

#### Security Scan

- ✅ Bandit security scan
- ✅ Safety check для зависимостей
- ✅ pip-audit для известных уязвимостей

**Минимальные требования для прохождения:**

- Все линтинг проверки должны пройти успешно
- Тесты должны пройти хотя бы на одной версии Python
- Security scan выполнен (предупреждения допустимы)

---

### 2. Code Quality (`quality.yml`)

**Триггеры:**

- Pull Request с изменениями в `.py` файлах
- Push в `main`, `develop` с изменениями в `.py` файлах

**Проверки:**

#### Ruff Linting

```yaml
ruff check src/ tests/ scripts/ --output-format=github
```

#### Ruff Format

```yaml
ruff format --check src/ tests/ scripts/
```

#### MyPy Type Checking

```yaml
mypy src/ --install-types --non-interactive
```

#### Complexity Analysis

- Cyclomatic complexity (radon)
- Maintainability index
- Threshold checks (Xenon)

**Комментарии на PR:**
Автоматически добавляет комментарий с результатами проверок.

---

### 3. Coverage Report (`coverage.yml`)

**Триггеры:**

- Push/PR с изменениями в `src/` или `tests/`

**Функции:**

#### Coverage Generation

- Генерация XML, HTML, JSON отчетов
- Загрузка в Codecov
- Проверка минимального порога (80%)

#### Coverage Badge

Автоматическая генерация badge с цветом:

- 90%+ → `brightgreen`
- 80-89% → `green`
- 70-79% → `yellow`
- 60-69% → `orange`
- <60% → `red`

#### Coverage Diff (для PR)

- Сравнение покрытия PR vs base branch
- Комментарий с изменениями покрытия

**Отчеты:**

- Файлы с низким покрытием (<70%)
- Топ-5 файлов с наименьшим покрытием
- Топ-5 файлов с наибольшим покрытием

---

### 4. Release Pipeline (`release.yml`)

**Триггеры:**

- Push тега `v*.*.*` (например, `v1.0.0`)
- Ручной запуск с указанием версии

**Этапы релиза:**

#### 1. Validation

- ✅ Проверка формата версии
- ✅ Определение типа релиза (stable/prerelease)

#### 2. Full Test Suite

- ✅ Запуск всех тестов
- ✅ Проверка минимального coverage (70%)

#### 3. Build Distribution

- ✅ Сборка Python packages
- ✅ Проверка с twine

#### 4. Build Docker Image

- ✅ Multi-platform build (amd64, arm64)
- ✅ Публикация в GitHub Container Registry
- ✅ Теги: `latest`, `X.Y.Z`, `X.Y`, `X`

#### 5. Create GitHub Release

- ✅ Генерация changelog
- ✅ Загрузка artifacts
- ✅ Draft/prerelease флаги

**Пример релиза:**

```bash
# Создать и запушить тег
git tag v1.0.0
git push origin v1.0.0

# Или использовать workflow_dispatch в GitHub UI
```

---

## 🎯 Использование

### Локальная проверка перед коммитом

```bash
# Проверка качества кода
ruff check src/ tests/ --fix
ruff format src/ tests/

# Проверка типов
mypy src/

# Запуск тестов
pytest tests/ --cov=src

# Полная проверка (как в CI)
make qa
```

### Pre-commit Hook

Установите pre-commit для автоматических проверок:

```bash
pip install pre-commit
pre-commit install
```

Создайте `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Проверка PR локально

```bash
# Запустить те же проверки, что и CI
pytest tests/ --cov=src --cov-report=term

# Проверить complexity
radon cc src/ -a -s
radon mi src/ -s
```

---

## 📊 Badges в README

Актуальные badges:

```markdown
[![CI](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/ci.yml)
[![Code Quality](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/quality.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/quality.yml)
[![Coverage](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/coverage.yml/badge.svg)](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/coverage.yml)
[![codecov](https://codecov.io/gh/Dykij/DMarket-Telegram-Bot/branch/main/graph/badge.svg)](https://codecov.io/gh/Dykij/DMarket-Telegram-Bot)
[![Release](https://img.shields.io/github/v/release/Dykij/DMarket-Telegram-Bot)](https://github.com/Dykij/DMarket-Telegram-Bot/releases)
```

---

## 🔐 Секреты

Необходимые GitHub Secrets:

| Секрет          | Описание                | Обязательный        |
| --------------- | ----------------------- | ------------------- |
| `CODECOV_TOKEN` | Токен для Codecov       | Нет (рекомендуется) |
| `GITHUB_TOKEN`  | Автоматически создается | Да                  |

### Настройка Codecov

1. Зарегистрируйтесь на [codecov.io](https://codecov.io)
2. Подключите репозиторий
3. Скопируйте токен
4. Добавьте в GitHub Secrets:
   - Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `CODECOV_TOKEN`
   - Value: ваш токен

---

## 🚀 Деплой

### Docker Image

После релиза образ доступен в GitHub Container Registry:

```bash
# Pull образа
docker pull ghcr.io/dykij/dmarket-telegram-bot:latest

# Или конкретной версии
docker pull ghcr.io/dykij/dmarket-telegram-bot:1.0.0

# Запуск
docker run -d \
  --name dmarket-bot \
  --env-file .env \
  ghcr.io/dykij/dmarket-telegram-bot:latest
```

### Python Package

```bash
# Установка из GitHub Release
pip install https://github.com/Dykij/DMarket-Telegram-Bot/releases/download/v1.0.0/dmarket_telegram_bot-1.0.0-py3-none-any.whl
```

---

## 📈 Метрики

### Coverage Trends

Следите за трендами покрытия на:

- [Codecov Dashboard](https://codecov.io/gh/Dykij/DMarket-Telegram-Bot)
- GitHub Actions artifacts

### Целевые показатели

| Метрика               | Текущая цель | Идеальная цель |
| --------------------- | ------------ | -------------- |
| Coverage              | 80%          | 90%+           |
| Maintainability       | B+           | A              |
| Cyclomatic Complexity | ≤15          | ≤10            |
| Test Success Rate     | 95%          | 100%           |

---

## 🛠️ Troubleshooting

### CI Failed: Linting Errors

```bash
# Исправить локально
ruff check . --fix
ruff format .

# Коммит и push
git add .
git commit -m "fix: resolve linting errors"
git push
```

### CI Failed: Tests

```bash
# Запустить тесты локально
pytest tests/ -v

# С подробным выводом ошибок
pytest tests/ -v --tb=long

# Запустить конкретный тест
pytest tests/test_specific.py::test_function -v
```

### CI Failed: Coverage Too Low

```bash
# Проверить покрытие
pytest tests/ --cov=src --cov-report=html

# Открыть отчет
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows

# Найти непокрытые строки
coverage report --show-missing
```

### Release Failed: Version Conflict

```bash
# Удалить локальный тег
git tag -d v1.0.0

# Удалить remote тег
git push --delete origin v1.0.0

# Создать правильный тег
git tag v1.0.1
git push origin v1.0.1
```

---

## 📚 Дополнительные ресурсы

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)

---

**Версия документа**: 1.0
**Последнее обновление**: 23 ноября 2025 г.
