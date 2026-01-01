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
