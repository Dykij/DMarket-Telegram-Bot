# 📝 CHANGELOG Automation Guide

## Обзор

Проект использует автоматическую генерацию CHANGELOG из git commits в формате [Conventional Commits](https://www.conventionalcommits.org/).

## 🎯 Формат коммитов

### Структура

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Типы коммитов

| Тип | Категория CHANGELOG | Описание |
|-----|---------------------|----------|
| `feat` | **Added** | Новая функциональность |
| `fix` | **Fixed** | Исправление бага |
| `docs` | **Documentation** | Изменения документации |
| `style` | **Style** | Форматирование кода |
| `refactor` | **Changed** | Рефакторинг |
| `perf` | **Performance** | Улучшение производительности |
| `test` | **Tests** | Добавление тестов |
| `build` | **Build** | Изменения сборки |
| `ci` | **CI/CD** | Изменения CI/CD |
| `chore` | **Chores** | Рутинные задачи |
| `revert` | **Reverted** | Откат изменений |

### Примеры

```bash
# Новая фича
git commit -m "feat(api): add portfolio endpoint"

# Исправление бага
git commit -m "fix(scanner): handle null prices correctly"

# Документация
git commit -m "docs(readme): update installation steps"

# Рефакторинг
git commit -m "refactor(targets): split into multiple modules"

# Breaking change
git commit -m "feat(api)!: change response format

BREAKING CHANGE: API now returns ISO dates instead of timestamps"
```

## 🚀 Использование

### Автоматическая генерация

CHANGELOG автоматически обновляется в CI/CD:

- **Push в main**: коммит с обновлением CHANGELOG
- **Pull Request**: комментарий с preview изменений

### Ручная генерация

```bash
# Генерация с последнего тега
python scripts/generate_changelog.py

# Генерация с определённого ref
python scripts/generate_changelog.py --since v1.0.0

# Генерация с указанием выходного файла
python scripts/generate_changelog.py --output HISTORY.md

# Dry-run (вывод в stdout)
python scripts/generate_changelog.py --dry-run
```

## 📋 Workflow

### 1. Разработка

```bash
# Создаём feature branch
git checkout -b feat/portfolio-management

# Коммитим изменения
git commit -m "feat(portfolio): add portfolio tracker"
git commit -m "test(portfolio): add unit tests"
git commit -m "docs(portfolio): add usage guide"
```

### 2. Pull Request

При создании PR:
- ✅ GitHub Actions генерирует CHANGELOG preview
- ✅ Комментарий показывает изменения
- ✅ Reviewer видит что попадёт в CHANGELOG

### 3. Merge в main

После мерджа:
- ✅ CHANGELOG автоматически обновляется
- ✅ Коммит с пометкой `[skip ci]`
- ✅ История изменений актуальна

## 🏷️ Релизы

### Создание релиза

```bash
# 1. Обновить версию
# Edit: src/__init__.py, pyproject.toml

# 2. Сгенерировать финальный CHANGELOG
python scripts/generate_changelog.py --since v1.0.0

# 3. Создать тег
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# 4. GitHub Release создаётся автоматически
```

### Формат версий (Semantic Versioning)

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): Новая функциональность (обратно совместимая)
- **PATCH** (0.0.1): Исправления багов

## 📊 Структура CHANGELOG.md

```markdown
# Changelog

## [Unreleased]

### Added
- feat(api): new portfolio endpoint
- feat(ui): add dark mode

### Fixed
- fix(scanner): handle null prices
- fix(auth): token expiration

### Changed
- refactor(targets): split into modules

## [1.1.0] - 2025-12-14

### Added
- Portfolio management system
- Backtesting framework

### Fixed
- Critical bug in price calculation

[Unreleased]: https://github.com/.../compare/v1.1.0...HEAD
[1.1.0]: https://github.com/.../releases/tag/v1.1.0
```

## ⚙️ Настройка

### .github/workflows/changelog.yml

Автоматический workflow включает:
- ✅ Триггер на push в main
- ✅ Триггер на PR
- ✅ Автоматический коммит
- ✅ PR комментарий с preview

### scripts/generate_changelog.py

Скрипт поддерживает:
- ✅ Парсинг Conventional Commits
- ✅ Категоризация по типам
- ✅ Генерация Markdown
- ✅ Интеграция с существующим файлом
- ✅ Ссылки на коммиты

## 🧪 Тестирование

```bash
# Запуск тестов
pytest tests/scripts/test_generate_changelog.py -v

# Тест dry-run генерации
python scripts/generate_changelog.py --dry-run
```

## 🔧 Troubleshooting

### CHANGELOG не обновляется автоматически

**Проблема**: Коммиты не попадают в CHANGELOG

**Решение**:
1. Проверь формат коммита (должен быть Conventional Commits)
2. Убедись что GitHub Actions имеют права `contents: write`
3. Проверь логи workflow

### Дублирование записей

**Проблема**: Одни и те же изменения дублируются

**Решение**:
1. Используй флаг `--since` с последним тегом
2. Убедись что теги созданы правильно
3. Перегенерируй CHANGELOG с нужным ref

### Неправильная категория

**Проблема**: Коммит попал не в ту категорию

**Решение**:
1. Используй правильный тип в коммите
2. Отредактируй CHANGELOG.md вручную
3. Добавь маппинг в `generate_changelog.py`

## 📚 Ресурсы

- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)

## ✅ Best Practices

1. **Пиши понятные коммиты**: Описывай ЧТО и ЗАЧЕМ
2. **Используй scope**: Помогает быстро понять область изменений
3. **Breaking changes**: Всегда отмечай в footer
4. **Группируй логически**: Несколько коммитов для одной фичи - нормально
5. **Squash при необходимости**: Убирай WIP и fix commits перед мерджем

## 🎓 Примеры из проекта

```bash
# ✅ Хорошие примеры
feat(portfolio): implement portfolio management system (P1-23)
fix(api): resolve rate limiting issues
docs(architecture): update component diagrams
refactor(scanner): split arbitrage_scanner.py into modules

# ❌ Плохие примеры
Update files                    # Нет типа и контекста
Fix bug                        # Нет scope и детализации
WIP                           # Не информативно
[COPILOT] Changes from AI     # Не следует формату
```

---

**Версия**: 1.0.0  
**Последнее обновление**: 14 декабря 2025 г.
