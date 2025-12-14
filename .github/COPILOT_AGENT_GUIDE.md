# 🤖 GitHub Copilot Coding Agent - Руководство для DMarket-Telegram-Bot

> **Полное руководство по использованию GitHub Copilot Background Agent в проекте**

---

## 📋 Содержание

1. [Быстрый старт](#-быстрый-старт)
2. [Конфигурация](#-конфигурация)
3. [Автоматизация](#-автоматизация)
4. [Специализированные агенты](#-специализированные-агенты)
5. [Лучшие практики](#-лучшие-практики)
6. [Troubleshooting](#-troubleshooting)

---

## 🚀 Быстрый старт

### 1. Активация агента

**Через веб-интерфейс GitHub:**
```
Settings → Code and automation → Copilot → Enable Copilot coding agent
```

**Через GitHub CLI:**
```bash
gh copilot agent enable
```

### 2. Первое задание

**Создать issue и назначить на @copilot:**

```markdown
Title: Improve test coverage in arbitrage_scanner.py

@copilot Please analyze test coverage for src/dmarket/arbitrage_scanner.py
and add missing unit tests for edge cases. Target: 85%+ coverage.

Context:
- Use AAA pattern (Arrange-Act-Assert)
- Follow naming: test_<function>_<condition>_<result>
- Mock external API calls with pytest-mock
- Run `pytest --cov=src/dmarket/arbitrage_scanner.py` to verify
```

**Через комментарий в PR:**
```markdown
@copilot Fix mypy errors in src/telegram_bot/handlers/scanner_handler.py
- Add missing type annotations
- Ensure strict mode compliance
- Run `mypy src/telegram_bot/handlers/scanner_handler.py` to verify
```

---

## ⚙️ Конфигурация

### Файлы конфигурации

```
.github/
├── workflows/
│   ├── copilot-coding-agent-setup.yaml    # Основная настройка среды
│   ├── copilot-scheduled-tasks.yaml       # Автоматические задачи
│   └── copilot-security-audit.yaml        # Аудит безопасности
├── copilot-instructions.md                # Общие инструкции (основные)
└── copilot-agent-instructions.md          # Специфичные для агента
```

### Workflow: copilot-coding-agent-setup.yaml

**Что делает:**
- ✅ Устанавливает Python 3.12
- ✅ Кэширует зависимости (pip, mypy, ruff)
- ✅ Настраивает async окружение
- ✅ Проверяет ключевые библиотеки (httpx, telegram)

**Время выполнения:** ~2-3 минуты (с кэшем ~30 секунд)

**Кастомизация:**

```yaml
# Добавить специфичные инструменты
- name: Install additional tools
  run: |
    pip install pre-commit hypothesis pact-python
```

### Инструкции: copilot-agent-instructions.md

**Ключевые секции:**
1. **Приоритеты проекта** - async, типизация, тесты
2. **Архитектурные правила** - запрещенные импорты
3. **Стиль кода** - примеры правильного/неправильного кода
4. **Тестирование** - AAA паттерн, именование
5. **Специфичные задачи** - пошаговые гайды

**Обновление инструкций:**

```bash
# При изменении архитектуры или правил
git add .github/copilot-agent-instructions.md
git commit -m "docs(copilot): update agent instructions for new module structure"
```

---

## 🔄 Автоматизация

### Scheduled Tasks (copilot-scheduled-tasks.yaml)

| Задача                       | Расписание          | Описание                                            |
| ---------------------------- | ------------------- | --------------------------------------------------- |
| **daily-code-quality**       | Ежедневно 02:00 UTC | Ruff + MyPy + pytest (критичные тесты)              |
| **weekly-dependency-update** | Понедельник 02:00   | Safety check + обновление уязвимостей               |
| **weekly-test-coverage**     | Среда 02:00         | Анализ покрытия, добавление тестов для <80% модулей |
| **weekly-documentation**     | Пятница 02:00       | Обновление docs/, проверка docstrings               |
| **performance-monitoring**   | Ежедневно           | Профилирование arbitrage_scanner, оптимизация       |

**Ручной запуск:**

```bash
# Запустить конкретную задачу
gh workflow run copilot-scheduled-tasks.yaml \
  -f task=daily-code-quality

# Посмотреть статус
gh run list --workflow=copilot-scheduled-tasks.yaml
```

### Security Audit (copilot-security-audit.yaml)

**Что проверяет:**
- 🔒 **Bandit** - SQL injection, hardcoded passwords, insecure crypto
- 🛡️ **Safety** - известные уязвимости в зависимостях
- 🔍 **Ruff** - небезопасные паттерны кода

**Триггеры:**
- Ежедневно в 03:00 UTC
- При push в `main`/`develop`
- Вручную через Actions

**Реакция агента:**
- CRITICAL/HIGH → автоматический PR с фиксами
- MEDIUM → issue с описанием
- LOW → комментарий в commit

---

## 🎨 Специализированные агенты

### 1. Тестовый агент (Test Coverage Agent)

**Назначение:** Повышение покрытия тестами

**Создание:**
```markdown
Title: @copilot-test Improve coverage for dmarket_api.py

Context:
- Target file: src/dmarket/dmarket_api.py
- Current coverage: 72%
- Target: 85%+
- Focus on edge cases: rate limiting, timeouts, auth failures

Tasks:
1. Analyze existing tests in tests/unit/dmarket/test_dmarket_api.py
2. Identify untested code paths with `pytest --cov --cov-report=term-missing`
3. Add missing tests using AAA pattern
4. Parametrize similar test cases with @pytest.mark.parametrize
5. Verify coverage: `pytest --cov=src/dmarket/dmarket_api.py --cov-fail-under=85`
```

### 2. Рефакторинг агент (Refactoring Agent)

**Назначение:** Улучшение читаемости и производительности

**Создание:**
```markdown
Title: @copilot-refactor Optimize arbitrage_scanner.py performance

Context:
- Current issue: Scanning 5 levels takes >15s
- Target: <10s
- Module: src/dmarket/arbitrage_scanner.py

Constraints:
- Preserve existing API
- Maintain 85%+ test coverage
- Use asyncio.gather() for parallel requests
- Add caching with @cached decorator

Tasks:
1. Profile current performance with cProfile
2. Identify bottlenecks (hint: sequential API calls)
3. Refactor to parallel execution
4. Add Redis caching for frequently accessed data
5. Run performance tests: `pytest tests/performance/ -v`
6. Verify no regression: `pytest tests/unit/dmarket/test_arbitrage_scanner.py`
```

### 3. Документация агент (Docs Agent)

**Назначение:** Поддержка актуальной документации

**Создание:**
```markdown
Title: @copilot-docs Update API reference for new endpoints

Context:
- New methods added in src/dmarket/dmarket_api.py:
  - get_sales_history()
  - get_offers()
- Documentation: docs/api_reference.md

Tasks:
1. Extract method signatures with type hints
2. Generate Google-style docstrings if missing
3. Add examples from tests (tests/unit/dmarket/test_dmarket_api.py)
4. Update docs/api_reference.md with new endpoints
5. Cross-reference related docs (ARCHITECTURE.md, ARBITRAGE.md)
6. Verify links work: `mkdocs serve`
```

### 4. Безопасность агент (Security Agent)

**Назначение:** Аудит и исправление уязвимостей

**Автоматически запускается через:**
- `copilot-security-audit.yaml` workflow
- Security alerts в GitHub

**Ручное назначение:**
```markdown
Title: @copilot-security Fix security issues in authentication

Context:
- Bandit HIGH: src/utils/encryption.py:45 - Insecure hash function (SHA1)
- Safety CRITICAL: cryptography 41.0.0 has CVE-2024-XXXX

Tasks:
1. Replace SHA1 with SHA256 in src/utils/encryption.py
2. Update cryptography to latest version in requirements.txt
3. Run security checks: `bandit -r src/` and `safety check`
4. Update tests to reflect new hash function
5. Verify no API breaking changes
```

---

## ✅ Лучшие практики

### Формулирование задач

**✅ Хорошая задача:**
```markdown
@copilot Add input validation for create_target() method

Context:
- File: src/dmarket/targets.py
- Method: create_target(game: str, item_title: str, price: float)

Requirements:
1. Validate `game` is in SupportedGame enum
2. Validate `item_title` is not empty string
3. Validate `price` is positive and < $10,000
4. Raise ValidationError with descriptive message on failure
5. Add tests in tests/unit/dmarket/test_targets.py:
   - test_create_target_with_invalid_game_raises_error
   - test_create_target_with_empty_title_raises_error
   - test_create_target_with_negative_price_raises_error

Success criteria:
- MyPy passes (no type errors)
- Ruff passes (no lint errors)
- Tests pass: `pytest tests/unit/dmarket/test_targets.py -v`
```

**❌ Плохая задача:**
```markdown
@copilot Fix the targets

(Нет контекста, не указан конкретный файл, нет критериев успеха)
```

### Предоставление контекста

**Важные детали:**
1. **Файлы:** Полные пути (`src/dmarket/dmarket_api.py`)
2. **Модули:** Зависимости (`httpx`, `tenacity`)
3. **Правила:** Ссылки на инструкции (`.github/copilot-agent-instructions.md`)
4. **Примеры:** Существующий код или тесты
5. **Критерии:** Как проверить успех (`pytest -v`, `ruff check`)

**Структура комментария:**

```markdown
@copilot <Краткое описание задачи>

Context:
- File: <путь к файлу>
- Current state: <что сейчас>
- Goal: <что должно быть>

Requirements:
1. <требование 1>
2. <требование 2>
...

Constraints:
- <ограничение 1>
- <ограничение 2>

Success criteria:
- <критерий 1>
- <критерий 2>

References:
- Docs: docs/<файл>.md
- Similar code: src/<модуль>/<файл>.py
```

### Ревью PR от Copilot

**Чеклист при ревью:**

- [ ] **Стиль кода:** Соответствует `.github/copilot-instructions.md`
- [ ] **Типизация:** MyPy strict mode, без `Any`
- [ ] **Тесты:** AAA паттерн, покрытие ≥80%
- [ ] **Производительность:** Нет регрессий (profile если нужно)
- [ ] **Безопасность:** Нет секретов, bandit чист
- [ ] **Документация:** Docstrings обновлены
- [ ] **Коммиты:** Conventional Commits формат

**Запрос изменений:**

```markdown
@copilot Please address the following issues:

1. Missing type annotation on line 45: `async def process_item(item)`
   Should be: `async def process_item(item: MarketItem) -> ProcessResult:`

2. Test `test_process_item` doesn't follow AAA pattern.
   Please refactor with explicit Arrange/Act/Assert comments.

3. MyPy error: `src/dmarket/processor.py:67: error: Argument 1 to "process" has incompatible type "str"; expected "int"`

Run checks before updating:
- `mypy src/`
- `pytest tests/unit/dmarket/test_processor.py -v`
```

---

## 🐛 Troubleshooting

### Агент не отвечает на @copilot

**Причины:**
1. Copilot не активирован для репозитория
2. У пользователя нет write permissions
3. Синтаксическая ошибка в задаче

**Решение:**
```bash
# Проверить статус
gh copilot agent status

# Проверить права
gh api repos/:owner/:repo/collaborators/:username/permission

# Попробовать через CLI
gh copilot agent start --task "Test task"
```

### Workflow copilot-coding-agent-setup.yaml падает

**Частые ошибки:**

**1. Timeout при установке зависимостей**
```yaml
# Решение: увеличить timeout
jobs:
  setup:
    timeout-minutes: 15  # было 10
```

**2. MyPy cache conflict**
```bash
# Очистить кэш
rm -rf .mypy_cache
git add .mypy_cache -f
```

**3. Ruff version mismatch**
```yaml
# Зафиксировать версию
- name: Install dependencies
  run: |
    pip install ruff==0.14.8  # точная версия
```

### Агент создает неправильный код

**Причины:**
1. Недостаточный контекст в задаче
2. Устаревшие инструкции
3. Конфликт с существующим кодом

**Решение:**

**Обновить инструкции:**
```bash
# Добавить примеры правильного кода
edit .github/copilot-agent-instructions.md
```

**Предоставить больше контекста:**
```markdown
@copilot Fix this, but follow the pattern from src/dmarket/dmarket_api.py:

```python
# Example from dmarket_api.py (lines 45-60)
async def _request(self, method: str, endpoint: str) -> dict[str, Any]:
    headers = self._generate_auth_headers()
    async with self.rate_limiter:
        response = await self.client.request(method, endpoint, headers=headers)
        return response.json()
```

Apply same pattern to src/telegram_bot/api_wrapper.py
```

### Scheduled tasks не запускаются

**Проверить:**

1. **Actions включены:**
   ```
   Settings → Actions → General → Allow all actions
   ```

2. **Права workflow:**
   ```yaml
   permissions:
     contents: write      # Для создания коммитов
     pull-requests: write # Для создания PR
   ```

3. **Cron выражение корректно:**
   ```yaml
   # Тестовый запуск каждые 5 минут
   schedule:
     - cron: '*/5 * * * *'
   ```

4. **Логи:**
   ```bash
   gh run list --workflow=copilot-scheduled-tasks.yaml
   gh run view <run-id> --log
   ```

---

## 📊 Метрики и мониторинг

### Отслеживание использования

**GitHub Actions:**
```bash
# Просмотр всех запусков
gh run list --workflow=copilot-coding-agent-setup.yaml --limit 50

# Средняя длительность
gh run list --json conclusion,name,startedAt,updatedAt \
  --jq '[.[] | select(.name=="Copilot Coding Agent Setup") | (.updatedAt | fromdateiso8601) - (.startedAt | fromdateiso8601)] | add / length'
```

**Copilot API лимиты:**
- **Pro:** 50 премиум-запросов/месяц
- **Business:** Без лимита
- **Enterprise:** Без лимита

**Проверка лимитов:**
```bash
gh copilot limits
```

### Статистика PR от Copilot

**SQL для анализа (GitHub Insights):**
```sql
SELECT
  COUNT(*) as total_prs,
  AVG(additions) as avg_additions,
  AVG(deletions) as avg_deletions,
  SUM(CASE WHEN merged THEN 1 ELSE 0 END) as merged_count
FROM pull_requests
WHERE author = 'copilot[bot]'
  AND created_at > DATE_SUB(NOW(), INTERVAL 30 DAY);
```

---

## 🎓 Дополнительные ресурсы

### Документация проекта

- [**AGENTS.md**](./AGENTS.md) - Общие инструкции для Copilot
- [**docs/ARCHITECTURE.md**](../docs/ARCHITECTURE.md) - Архитектура проекта
- [**docs/testing_guide.md**](../docs/testing_guide.md) - Руководство по тестированию
- [**docs/CI_CD_GUIDE.md**](../docs/CI_CD_GUIDE.md) - CI/CD pipelines

### GitHub Copilot

- [Официальная документация](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-code-review)
- [Best practices](https://github.blog/developer-skills/github/how-to-use-github-copilot-in-your-ide-tips-tricks-and-best-practices/)
- [Model Context Protocol (MCP)](https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)

---

**Версия**: 1.0
**Дата обновления**: 14 декабря 2025
**Авторы**: DMarket Bot Team
**Лицензия**: MIT
