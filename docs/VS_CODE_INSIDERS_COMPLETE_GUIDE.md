# 🚀 VS Code Insiders Complete Guide

Полное руководство по настройке VS Code Insiders с GitHub Copilot для проекта DMarket Telegram Bot.

---

## 📖 Содержание

1. [Что это такое](#что-это-такое)
2. [Быстрый старт](#быстрый-старт)
3. [Топ-10 функций](#топ-10-экспериментальных-функций)
4. [Полный список настроек](#полный-список-настроек)
5. [Примеры использования](#примеры-использования)
6. [Troubleshooting](#troubleshooting)

---

## 📖 Что это такое?

Этот документ объединяет:
- **Экспериментальные настройки VS Code Insiders** (100+ настроек)
- **Краткую справку** (Top-10 функций)
- **Полный индекс настроек** (все параметры с описанием)

Улучшает работу с:
- ✨ **GitHub Copilot** (AI-ассистент)
- ⚡ **VS Code Insiders** (производительность)
- 🤖 **Вашим репозиторием** (контекстные подсказки)

---

## 🚀 Быстрый старт

### Шаг 1: Установка

```bash
# Windows
winget install Microsoft.VisualStudioCode.Insiders

# macOS
brew install --cask visual-studio-code-insiders

# Linux
wget https://code.visualstudio.com/sha/download?build=insider&os=linux-deb-x64
```

### Шаг 2: Расширения

```bash
code-insiders --install-extension GitHub.copilot
code-insiders --install-extension GitHub.copilot-chat
code-insiders --install-extension ms-python.python
code-insiders --install-extension charliermarsh.ruff
```

### Шаг 3: Открыть проект

```bash
code-insiders .
```

Настройки из `.vscode/settings.insiders.json` применятся автоматически!

---

## ⚡ Top-10 Экспериментальных функций

### 1. 🤖 Code Review (Auto)
```json
"github.copilot.chat.experimental.codeReview.enabled": true
```
**Использование**: `Ctrl+Shift+P` → `Copilot: Review Code`

**Проверяет**:
- ✅ async/await для I/O
- ✅ Type hints
- ✅ Error handling
- ✅ Code smells

### 2. 📝 Multi-file Editing
```json
"github.copilot.chat.experimental.multiFileEdits": true
```
**Использование**: В Chat: "Add feature X"

**Результат**: Изменения в нескольких файлах одновременно

### 3. 🔍 Semantic Search
```json
"search.experimental.semanticSearch": true
```
**Использование**: `Ctrl+Shift+F` → поиск по смыслу

**Пример**: "code that handles errors" → находит все try/except

### 4. 🧪 Test Generation Enhanced
```json
"github.copilot.chat.experimental.testGeneration": "enhanced"
```
**Использование**: Правый клик → `Generate Tests`

**Результат**: Тесты с edge cases, AAA pattern

### 5. 🛡️ Security Scanning
```json
"github.copilot.chat.experimental.security.enabled": true
```
**Находит**:
- Hardcoded secrets
- SQL injection
- Path traversal
- Небезопасные dependencies

### 6. 💬 Explain Error (Auto)
```json
"github.copilot.chat.experimental.explainError": true
```
**Работает автоматически** при ошибках в терминале

### 7. 🌳 Tree-sitter (10x Faster)
```json
"editor.experimental.treeSitter": true
```
**Результат**: 10x быстрее syntax highlighting

### 8. 🎯 Workspace Context
```json
"github.copilot.experimental.repositoryAnalysis": true
```
**Результат**: Copilot понимает структуру всего проекта

### 9. 🗣️ Voice Coding
```json
"accessibility.experimental.voice.enabled": true
```
**Использование**: `Ctrl+Shift+P` → `Voice: Start Dictation`

### 10. 📊 Test Coverage Inline
```json
"testing.experimental.coverage.showInline": true
```
**Результат**: Coverage у каждой строки (зелёный/красный)

---

## 🎯 Горячие клавиши

| Действие            | Комбинация                              |
| ------------------- | --------------------------------------- |
| Copilot Chat        | `Ctrl+Shift+P` → `Copilot: Open Chat`   |
| Code Review         | `Ctrl+Shift+P` → `Copilot: Review Code` |
| Generate Tests      | Правый клик → `Generate Tests`          |
| Accept Suggestion   | `Tab`                                   |
| Next Suggestion     | `Alt+]`                                 |
| Previous Suggestion | `Alt+[`                                 |
| Dismiss Suggestion  | `Esc`                                   |

---

## 📋 Полный список настроек

### 🤖 GitHub Copilot

| Настройка                                             | Описание                   |
| ----------------------------------------------------- | -------------------------- |
| `github.copilot.chat.experimental.codeReview.enabled` | Автоматический code review |
| `github.copilot.chat.experimental.workspaceContext`   | Понимание workspace        |
| `github.copilot.chat.experimental.multiFileEdits`     | Multi-file редактирование  |
| `github.copilot.chat.experimental.smellDetection`     | Детект code smells         |
| `github.copilot.chat.experimental.security.enabled`   | Security scanning          |
| `github.copilot.chat.experimental.explainError`       | Объяснение ошибок          |
| `github.copilot.chat.experimental.testGeneration`     | Enhanced test generation   |
| `github.copilot.experimental.repositoryAnalysis`      | Анализ репозитория         |
| `github.copilot.experimental.contextHints`            | Context hints              |

### ✨ Editor

| Настройка                                       | Описание                 |
| ----------------------------------------------- | ------------------------ |
| `editor.experimental.inlineCompletions.enabled` | Inline AI completions    |
| `editor.experimental.semanticSearch`            | Семантический поиск      |
| `editor.experimental.smartRename`               | Умное переименование     |
| `editor.experimental.treeSitter`                | Tree-sitter (10x faster) |
| `editor.experimental.asyncTokenization`         | Async парсинг            |

### 🔍 Search

| Настройка                            | Описание        |
| ------------------------------------ | --------------- |
| `search.experimental.semanticSearch` | Поиск по смыслу |
| `search.experimental.aiRanking`      | AI ранжирование |

### 🧪 Testing

| Настройка                                   | Описание          |
| ------------------------------------------- | ----------------- |
| `testing.experimental.coverage.enabled`     | Test coverage     |
| `testing.experimental.coverage.showInline`  | Inline coverage   |
| `testing.experimental.coverage.showGutters` | Gutter indicators |

### 🔄 Git

| Настройка                             | Описание           |
| ------------------------------------- | ------------------ |
| `git.experimental.commitMessageAI`    | AI commit messages |
| `git.experimental.timeline.showGraph` | Git graph          |

### 🐍 Python

| Настройка                                       | Описание             |
| ----------------------------------------------- | -------------------- |
| `python.analysis.experimental.languageServer`   | Enhanced Pylance     |
| `python.analysis.experimental.typeCheckingMode` | Strict type checking |

### 💻 Terminal

| Настройка                                        | Описание            |
| ------------------------------------------------ | ------------------- |
| `terminal.integrated.experimental.aiSuggestions` | AI подсказки команд |

### ♿ Accessibility

| Настройка                                  | Описание       |
| ------------------------------------------ | -------------- |
| `accessibility.experimental.voice.enabled` | Голосовой ввод |

**Полный список** (100+ настроек): см. `.vscode/settings.insiders.json`

---

## 🎨 Проектные паттерны (DMarket Bot)

### API Call Pattern
```python
from tenacity import retry, stop_after_attempt
import httpx
import structlog

logger = structlog.get_logger(__name__)

@retry(stop=stop_after_attempt(3))
async def api_call(url: str) -> dict:
    """Template for all API calls."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("api_error", url=url, status=e.response.status_code)
            raise
```

### Test Pattern (AAA)
```python
@pytest.mark.asyncio
async def test_function_condition_expected_result():
    # Arrange
    mock = AsyncMock(return_value={"key": "value"})

    # Act
    result = await function(mock)

    # Assert
    assert result["key"] == "value"
    mock.assert_called_once()
```

### Telegram Handler Pattern
```python
async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info("command_received", user_id=user_id)

    try:
        result = await process_command(user_id)
        await update.message.reply_text(f"✅ {result}")
    except Exception as e:
        logger.error("command_failed", user_id=user_id, error=str(e))
        await update.message.reply_text("❌ Error")
```

---

## 💡 Примеры использования

### Пример 1: Создание API метода

**Вы пишете**:
```python
async def get_user_balance(user_id: int):
```

**Copilot предлагает** (с workspace context):
```python
async def get_user_balance(user_id: int) -> dict[str, float]:
    """Get user balance from DMarket API.

    Args:
        user_id: Telegram user ID

    Returns:
        Balance dict with USD and DMC amounts
    """
    logger.info("fetching_balance", user_id=user_id)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{config.dmarket.api_url}/balance")
        data = response.json()

        # Convert cents to dollars (DMarket API specific!)
        return {
            "usd": cents_to_dollars(data["usd"]),
            "dmc": cents_to_dollars(data["dmc"])
        }
```

**Почему хорошо?**:
- ✅ async/await
- ✅ Type hints
- ✅ Docstring
- ✅ Logging
- ✅ Конвертация центов в доллары (знает специфику DMarket!)

### Пример 2: Генерация тестов

**В Chat**:
```
@workspace /tests Generate tests for get_user_balance
```

**Copilot создаст**:
- Тесты успешных случаев
- Edge cases (zero balance, большие суммы)
- Error cases (HTTP errors, timeouts)
- AAA pattern структура

---

## ✅ Checklist проверки работы

- [ ] VS Code Insiders установлен
- [ ] GitHub Copilot активирован (`Ctrl+Shift+P` → `Copilot: Check Status`)
- [ ] Файл `.vscode/settings.insiders.json` существует
- [ ] Файл `.github/copilot-workspace.md` существует
- [ ] В Chat: `@workspace what is this project?` - Copilot понимает контекст

**Ожидаемый ответ**:
```
This is a DMarket Telegram Bot project in Python 3.11+.
Uses async/await, httpx, python-telegram-bot.
2348+ tests, 85%+ coverage.
DMarket API prices in CENTS (not dollars!).
```

---

## 🐛 Troubleshooting

### Copilot не работает
```bash
# Проверить статус
Ctrl+Shift+P → Copilot: Check Status

# Переподключиться
Ctrl+Shift+P → Copilot: Sign Out
Ctrl+Shift+P → Copilot: Sign In
```

### Медленная работа
```json
// Отключить semantic highlighting
"editor.experimental.semanticHighlighting.enabled": false

// Включить Tree-sitter
"editor.experimental.treeSitter": true
```

### Workspace не индексируется
```json
// Уменьшить глубину анализа
"github.copilot.experimental.repositoryAnalysis.depth": "shallow"
```

---

## 🎯 Специфика для DMarket Bot

### Copilot знает:
- ✅ DMarket API цены в **центах** (не долларах!)
- ✅ async/await обязателен для всех I/O
- ✅ Type hints везде (MyPy strict mode)
- ✅ Structured logging (structlog) с контекстом
- ✅ AAA pattern для тестов
- ✅ DRY_RUN режим безопасности

### Code Review чеклист:
- [ ] async/await для всех I/O операций
- [ ] Type hints на всех функциях
- [ ] Error handling (no bare except)
- [ ] Structured logging с контекстом
- [ ] Нет hardcoded secrets
- [ ] Rate limiting учтён
- [ ] Цены DMarket правильно конвертируются

---

## 💡 Pro Tips

1. **@workspace** для контекстных вопросов:
   ```
   @workspace How to add new arbitrage level?
   ```

2. **Multi-file tasks**:
   ```
   @workspace Add user authentication with tests
   ```

3. **Code Review** перед commit:
   ```
   Ctrl+Shift+P → Copilot: Review Code
   ```

4. **Test generation**:
   ```
   Правый клик → Generate Tests
   ```

5. **Semantic search**:
   ```
   Ctrl+Shift+F → "code that validates prices"
   ```

---

## 📚 Дополнительные ресурсы

### Файлы проекта:
- **Настройки**: `.vscode/settings.insiders.json`
- **Workspace контекст**: `.github/copilot-workspace.md`
- **Copilot инструкции**: `.github/copilot-instructions.md`

### Документация проекта:
- **README**: `README.md`
- **Архитектура**: `docs/ARCHITECTURE.md`
- **Арбитраж**: `docs/ARBITRAGE.md`
- **Тестирование**: `docs/testing_guide.md`
- **Безопасность**: `docs/SECURITY.md`

### Внешние ресурсы:
- **VS Code Insiders**: https://code.visualstudio.com/insiders/
- **GitHub Copilot**: https://docs.github.com/copilot
- **Copilot Best Practices**: https://github.blog/tag/copilot/

---

## 📊 Статистика настроек

- **Всего настроек**: 100+
- **Только для Insiders**: ~70
- **AI/Copilot**: ~50
- **Performance**: ~15
- **Accessibility**: ~5
- **Testing**: ~10
- **Git**: ~5

---

## 🎉 Итоги

С этими настройками вы получаете:

✅ **Умный Copilot** - понимает контекст проекта
✅ **Автоматический Code Review** - находит ошибки до запуска
✅ **Multi-file редактирование** - изменения в нескольких файлах
✅ **Enhanced Test Generation** - тесты с edge cases
✅ **Semantic Search** - поиск по смыслу
✅ **Voice Coding** - голосовой ввод
✅ **10x Faster Performance** - Tree-sitter и async tokenization

**Начните прямо сейчас**: откройте проект в VS Code Insiders! 🚀

---

**Версия**: 2.0 (Объединённая)
**Дата**: Январь 2026
**Для**: VS Code Insiders 1.96+ с GitHub Copilot
**Проект**: DMarket Telegram Bot


---

# 🔧 VS Code Setup Troubleshooting

Дополнительные инструкции по настройке VS Code и решению частых проблем.

# VS Code Setup Guide - Настройка VS Code

> **Дата создания**: 01 января 2026
> **Статус**: Актуально для VS Code 1.85+

Это руководство поможет правильно настроить VS Code для работы с проектом DMarket Telegram Bot.

---

## 🔧 Решение проблемы "ms-python.python:system"

Если вы видите сообщение:

```
Вы хотите установить расширение ms-python.python, чтобы включить поддержку ms-python.python:system
```

### ✅ Способ 1: Через VS Code UI (Рекомендуется)

1. **Нажмите кнопку "Установить"** в уведомлении VS Code
2. **Или откройте Extensions** (`Ctrl+Shift+X`)
3. **Найдите**: `ms-python.python`
4. **Нажмите "Install"**
5. **Перезагрузите VS Code** если требуется

### ✅ Способ 2: Через Command Palette

1. Откройте Command Palette: `Ctrl+Shift+P` (Windows) или `Cmd+Shift+P` (Mac)
2. Введите: `Extensions: Install Extensions`
3. Найдите: `Python` (от Microsoft)
4. Установите `ms-python.python`

### ✅ Способ 3: Через командную строку (с code CLI)

Если у вас установлен `code` CLI:

```bash
# Windows PowerShell
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension ms-python.mypy-type-checker
code --install-extension github.copilot
```

### ✅ Способ 4: Автоматическая установка всех рекомендуемых расширений

VS Code автоматически предложит установить рекомендуемые расширения при открытии проекта.

**Как включить**:

1. Откройте проект в VS Code
2. В правом нижнем углу появится уведомление: "Do you want to install the recommended extensions?"
3. Нажмите **"Install All"**

---

## 📦 Обязательные расширения (REQUIRED)

Эти расширения необходимы для полноценной работы:

| Расширение     | ID                            | Назначение                 |
| -------------- | ----------------------------- | -------------------------- |
| Python         | `ms-python.python`            | Основная поддержка Python  |
| Pylance        | `ms-python.vscode-pylance`    | IntelliSense для Python    |
| Debugpy        | `ms-python.debugpy`           | Отладчик Python            |
| Ruff           | `charliermarsh.ruff`          | Быстрый линтер и форматтер |
| MyPy           | `ms-python.mypy-type-checker` | Проверка типов             |
| GitHub Copilot | `github.copilot`              | AI-ассистент               |

---

## 🚀 Быстрая установка всех расширений

### Через PowerShell

```powershell
# Проверка наличия code CLI
if (Get-Command code -ErrorAction SilentlyContinue) {
    Write-Host "Installing VS Code extensions..." -ForegroundColor Green

    # Python Development
    code --install-extension ms-python.python
    code --install-extension ms-python.vscode-pylance
    code --install-extension ms-python.debugpy
    code --install-extension charliermarsh.ruff
    code --install-extension ms-python.mypy-type-checker

    # Testing
    code --install-extension littlefoxteam.vscode-python-test-adapter
    code --install-extension hbenl.vscode-test-explorer

    # Git & GitHub
    code --install-extension eamodio.gitlens
    code --install-extension github.copilot
    code --install-extension github.copilot-chat

    # Code Quality
    code --install-extension streetsidesoftware.code-spell-checker
    code --install-extension usernamehw.errorlens
    code --install-extension nhoizey.gremlins

    # YAML/JSON/TOML
    code --install-extension redhat.vscode-yaml
    code --install-extension tamasfe.even-better-toml

    Write-Host "✅ All extensions installed!" -ForegroundColor Green
    Write-Host "Please restart VS Code" -ForegroundColor Yellow
} else {
    Write-Host "❌ 'code' command not found in PATH" -ForegroundColor Red
    Write-Host "Please install extensions manually through VS Code UI" -ForegroundColor Yellow
}
```

### Через Bash (Linux/Mac)

```bash
#!/bin/bash

# Проверка наличия code CLI
if command -v code &> /dev/null; then
    echo "Installing VS Code extensions..."

    # Python Development
    code --install-extension ms-python.python
    code --install-extension ms-python.vscode-pylance
    code --install-extension ms-python.debugpy
    code --install-extension charliermarsh.ruff
    code --install-extension ms-python.mypy-type-checker

    # Testing
    code --install-extension littlefoxteam.vscode-python-test-adapter
    code --install-extension hbenl.vscode-test-explorer

    # Git & GitHub
    code --install-extension eamodio.gitlens
    code --install-extension github.copilot
    code --install-extension github.copilot-chat

    # Code Quality
    code --install-extension streetsidesoftware.code-spell-checker
    code --install-extension usernamehw.errorlens
    code --install-extension nhoizey.gremlins

    # YAML/JSON/TOML
    code --install-extension redhat.vscode-yaml
    code --install-extension tamasfe.even-better-toml

    echo "✅ All extensions installed!"
    echo "Please restart VS Code"
else
    echo "❌ 'code' command not found in PATH"
    echo "Please install extensions manually through VS Code UI"
fi
```

---

## 🔍 Проверка установленных расширений

### Через VS Code

1. Откройте Extensions: `Ctrl+Shift+X`
2. Проверьте, что все расширения из списка установлены

### Через командную строку

```bash
# Список всех установленных расширений
code --list-extensions

# Проверка конкретных расширений
code --list-extensions | grep "ms-python.python"
code --list-extensions | grep "charliermarsh.ruff"
code --list-extensions | grep "github.copilot"
```

---

## ⚙️ Настройка после установки

После установки расширений, VS Code автоматически применит настройки из `.vscode/settings.json`.

### Проверьте настройки

1. **Python Interpreter**:
   - Откройте Command Palette: `Ctrl+Shift+P`
   - Выберите: `Python: Select Interpreter`
   - Выберите интерпретатор из `.venv` или системный Python 3.11+

2. **Ruff Configuration**:
   - Автоматически используется `pyproject.toml`
   - Проверьте: `Ctrl+Shift+P` → `Ruff: Show Output`

3. **MyPy Configuration**:
   - Автоматически использует настройки из `pyproject.toml`
   - Проверьте: `Ctrl+Shift+P` → `MyPy: Run Type Check`

---

## 🐛 Troubleshooting

### Проблема: "code command not found"

**Решение**:

1. Откройте VS Code
2. Command Palette (`Ctrl+Shift+P`)
3. Введите: `Shell Command: Install 'code' command in PATH`
4. Перезапустите терминал

### Проблема: Расширения не работают

**Решение**:

1. Перезагрузите VS Code: `Ctrl+Shift+P` → `Developer: Reload Window`
2. Проверьте Output: `View` → `Output` → выберите расширение
3. Переустановите расширение: ПКМ на расширении → `Uninstall` → `Install`

### Проблема: Pylance не находит модули

**Решение**:

1. Убедитесь, что выбран правильный Python interpreter
2. Проверьте `.vscode/settings.json`:

   ```json
   {
       "python.analysis.extraPaths": ["${workspaceFolder}/src"]
   }
   ```

3. Перезагрузите window: `Ctrl+Shift+P` → `Developer: Reload Window`

### Проблема: Ruff не форматирует код

**Решение**:

1. Проверьте, что Ruff установлен: `pip list | grep ruff`
2. Установите если нужно: `pip install ruff`
3. Проверьте настройки в `.vscode/settings.json`:

   ```json
   {
       "[python]": {
           "editor.defaultFormatter": "charliermarsh.ruff",
           "editor.formatOnSave": true
       }
   }
   ```

---

## 📚 Полезные команды VS Code

| Команда         | Описание             |
| --------------- | -------------------- |
| `Ctrl+Shift+P`  | Command Palette      |
| `Ctrl+Shift+X`  | Extensions           |
| `Ctrl+Shift+E`  | Explorer             |
| `Ctrl+Shift+F`  | Search               |
| `Ctrl+Shift+G`  | Source Control (Git) |
| `Ctrl+Shift+D`  | Debug                |
| `Ctrl+Shift+U`  | Output               |
| `Ctrl+``        | Terminal             |
| `Ctrl+K Ctrl+S` | Keyboard Shortcuts   |
| `F5`            | Start Debugging      |
| `Shift+F5`      | Stop Debugging       |
| `Ctrl+Shift+B`  | Run Build Task       |

---

## 🎨 Рекомендуемые темы

- **Dark+** (Default Dark) - встроенная тема
- **Material Theme** - популярная тема (install: `Equinox Defect.vsc-material-theme`)
- **One Dark Pro** - тема Atom для VS Code (install: `zhuangtongfa.Material-theme`)

---

## 🔗 Полезные ссылки

- [VS Code Python Documentation](https://code.visualstudio.com/docs/languages/python)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pylance Features](https://github.com/microsoft/pylance-release)
- [GitHub Copilot Docs](https://docs.github.com/en/copilot)

---

## ✅ Checklist - Проверка установки

После установки всех расширений, убедитесь что:

- [ ] Python расширение установлено и активно
- [ ] Pylance показывает подсказки при наведении на код
- [ ] Ruff подчёркивает ошибки в коде
- [ ] MyPy проверяет типы (можно запустить: `Ctrl+Shift+P` → `MyPy: Run`)
- [ ] GitHub Copilot предлагает автодополнения
- [ ] Test Explorer показывает тесты (View → Testing)
- [ ] GitLens показывает git blame в редакторе
- [ ] Terminal открывается внутри VS Code
- [ ] Python interpreter выбран (смотрите статус бар)

---

## 🚀 Готово

После выполнения всех шагов, VS Code будет полностью настроен для разработки.

**Следующий шаг**: Откройте проект и начните разработку! 🎉

Если возникли проблемы - см. раздел [Troubleshooting](#-troubleshooting) выше.


---

**Обновлено**: Январь 2026 - добавлен Troubleshooting Setup
