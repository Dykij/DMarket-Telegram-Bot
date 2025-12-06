# 📋 GitHub Actions Workflows Overview

**Дата**: 23 ноября 2025 г.

Полный список всех GitHub Actions workflows в проекте.

---

## 📁 Список Workflows

### 1. CI Pipeline (`ci.yml`)

**Путь**: `.github/workflows/ci.yml`

**Триггеры**:
- Push в `main`, `develop`
- Pull Request в `main`, `develop`
- Ручной запуск (workflow_dispatch)

**Что делает**:
- Проверка кода (Ruff linting & format)
- Проверка типов (MyPy)
- Запуск тестов на Python 3.10, 3.11, 3.12
- Security scan (Bandit, Safety, pip-audit)
- Build Docker image

**Статус**: ![CI](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/ci.yml/badge.svg)

---

### 2. Code Quality (`quality.yml`)

**Путь**: `.github/workflows/quality.yml`

**Триггеры**:
- Pull Request с изменениями в `.py` файлах
- Push в `main`, `develop`

**Что делает**:
- Детальная проверка Ruff
- MyPy с генерацией отчетов
- Анализ сложности кода (Radon, Xenon)
- Автоматические комментарии на PR

**Статус**: ![Quality](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/quality.yml/badge.svg)

---

### 3. Coverage Report (`coverage.yml`)

**Путь**: `.github/workflows/coverage.yml`

**Триггеры**:
- Push/PR с изменениями в `src/` или `tests/`

**Что делает**:
- Генерация coverage отчетов (XML, HTML, JSON)
- Загрузка в Codecov
- Coverage badge
- Coverage diff для PR
- Комментарии с отчетом на PR

**Статус**: ![Coverage](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/coverage.yml/badge.svg)

---

### 4. Release (`release.yml`)

**Путь**: `.github/workflows/release.yml`

**Триггеры**:
- Push тега `v*.*.*`
- Ручной запуск с указанием версии

**Что делает**:
- Валидация версии
- Полный набор тестов
- Сборка Python packages
- Сборка Docker образов (multi-platform)
- Публикация в GitHub Container Registry
- Создание GitHub Release
- Генерация changelog

**Как использовать**:
```bash
git tag v1.0.0
git push origin v1.0.0
```

**Статус**: ![Release](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/release.yml/badge.svg)

---

### 5. Dependency Update (`dependencies.yml`)

**Путь**: `.github/workflows/dependencies.yml`

**Триггеры**:
- Расписание (каждый понедельник в 00:00 UTC)
- Ручной запуск

**Что делает**:
- Обновление Python зависимостей
- Обновление GitHub Actions versions
- Проверка устаревших пакетов
- Создание PR с обновлениями
- Создание issue для outdated packages

**Статус**: ![Dependencies](https://github.com/Dykij/DMarket-Telegram-Bot/actions/workflows/dependencies.yml/badge.svg)

---

## 📊 Workflow Matrix

| Workflow     | Запуск      | Время   | Критичность     |
| ------------ | ----------- | ------- | --------------- |
| CI           | Push/PR     | ~5 мин  | 🔴 Обязательно   |
| Quality      | PR          | ~3 мин  | 🟡 Рекомендуется |
| Coverage     | Push/PR     | ~4 мин  | 🟡 Рекомендуется |
| Release      | Tag         | ~10 мин | 🟢 По требованию |
| Dependencies | Еженедельно | ~2 мин  | 🟢 Автоматически |

---

## 🎯 Когда запускается что

### При Push в main/develop

1. ✅ CI Pipeline
2. ✅ Coverage Report (если изменены `.py` файлы)

### При создании Pull Request

1. ✅ CI Pipeline
2. ✅ Code Quality (если изменены `.py` файлы)
3. ✅ Coverage Report (если изменены `.py` файлы)
   - С coverage diff комментарием

### При создании Release (тег)

1. ✅ Release Pipeline
   - Все тесты
   - Docker build
   - GitHub Release

### Еженедельно (понедельник)

1. ✅ Dependency Update
   - Проверка обновлений
   - Создание PR при наличии обновлений

---

## 🔧 Конфигурация Workflows

### Общие переменные

Все workflows используют:

```yaml
env:
  PYTHON_VERSION: "3.11"  # Основная версия Python
```

### Matrix Testing

CI запускает тесты на:
- Python 3.10
- Python 3.11 (с coverage)
- Python 3.12

### Кэширование

Все workflows используют кэширование:
- pip dependencies
- Ruff cache
- MyPy cache
- Docker layers

---

## 📝 Artifacts

### CI Pipeline

- `test-results-*` - результаты тестов
- `security-reports` - отчеты безопасности

### Coverage

- `coverage-report-*` - HTML отчеты покрытия
- `coverage.xml` - XML для Codecov

### Quality

- `mypy-report` - HTML отчеты MyPy

### Release

- `python-packages` - wheel и source distributions
- Docker images в ghcr.io

---

## 🎮 Ручное управление

### Запуск через GitHub UI

1. Перейдите в **Actions**
2. Выберите нужный workflow
3. Нажмите **Run workflow**
4. Заполните параметры (если есть)
5. Нажмите **Run workflow**

### Запуск через GitHub CLI

```bash
# Запустить CI вручную
gh workflow run ci.yml

# Запустить Release с версией
gh workflow run release.yml -f version=1.0.0

# Посмотреть статус
gh run list

# Посмотреть логи
gh run view <run-id>
```

---

## 🚨 Troubleshooting

### Workflow не запускается

1. Проверьте, что workflow включен:
   - Actions → выберите workflow → Enable workflow

2. Проверьте триггеры в `.yml` файле

3. Проверьте branch protection rules

### Workflow падает

1. Откройте детальные логи в GitHub Actions
2. Проверьте секреты (если используются)
3. Запустите проверки локально:
   ```bash
   ruff check .
   mypy src/
   pytest tests/
   ```

### Coverage не обновляется

1. Проверьте `CODECOV_TOKEN` в secrets
2. Убедитесь, что `coverage.yml` запустился
3. Проверьте на codecov.io

---

## 📚 Связанные документы

- 📖 [CI/CD Guide](CI_CD_GUIDE.md) - Полная документация
- 🚀 [CI/CD Quick Start](CI_CD_QUICKSTART.md) - Быстрый старт
- 🔧 [Code Quality Tools](code_quality_tools_guide.md) - Инструменты качества
- 🧪 [Testing Guide](testing_guide.md) - Тестирование

---

## 📞 Поддержка

Если workflow работает неправильно:

1. Проверьте [GitHub Actions Status](https://www.githubstatus.com/)
2. Создайте [Issue](https://github.com/Dykij/DMarket-Telegram-Bot/issues)
3. Обратитесь к документации GitHub Actions

---

**Последнее обновление**: 23 ноября 2025 г.
