# VS Code Configuration Validator
# Проверяет корректность всех конфигурационных файлов VS Code

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           VS CODE CONFIGURATION VALIDATOR                     ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$errors = @()
$warnings = @()

# 1. Проверка существования файлов
Write-Host "📁 Проверка структуры .vscode/..." -ForegroundColor Yellow

$requiredFiles = @(
    ".vscode/settings.json",
    ".vscode/extensions.json",
    ".vscode/launch.json",
    ".vscode/tasks.json"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $file (опционально)" -ForegroundColor Yellow
        $warnings += "$file отсутствует"
    }
}

# 2. Проверка Python environment
Write-Host "`n🐍 Проверка Python окружения..." -ForegroundColor Yellow

if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "  ✅ Virtual environment найден" -ForegroundColor Green
    $pythonVersion = & ".venv\Scripts\python.exe" --version 2>&1
    Write-Host "     Версия: $pythonVersion" -ForegroundColor Gray
} else {
    Write-Host "  ❌ Virtual environment НЕ найден" -ForegroundColor Red
    $errors += "Запустите: python -m venv .venv"
}

# 3. Проверка путей в settings.json
Write-Host "`n⚙️  Проверка settings.json..." -ForegroundColor Yellow

try {
    # VS Code использует JSONC (JSON with Comments)
    $settingsContent = Get-Content ".vscode\settings.json" -Raw

    # Проверка критических настроек
    if ($settingsContent -match '"python.defaultInterpreterPath"') {
        Write-Host "  ✅ Python interpreter настроен" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Python interpreter не настроен" -ForegroundColor Yellow
        $warnings += "Добавьте python.defaultInterpreterPath"
    }

    if ($settingsContent -match '"python.languageServer":\s*"Pylance"') {
        Write-Host "  ✅ Pylance language server включен" -ForegroundColor Green
    } elseif ($settingsContent -match '"python.languageServer":\s*"None"') {
        Write-Host "  ⚠️  Language server выключен (None)" -ForegroundColor Yellow
        $warnings += "Рекомендуется: python.languageServer = Pylance"
    }

    if ($settingsContent -match 'config/mypy.ini') {
        Write-Host "  ❌ Неверный путь к mypy.ini" -ForegroundColor Red
        $errors += "Исправьте: --config-file=pyproject.toml"
    } else {
        Write-Host "  ✅ MyPy конфигурация корректна" -ForegroundColor Green
    }

    if ($settingsContent -match '"charliermarsh.ruff"') {
        Write-Host "  ✅ Ruff formatter настроен" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Ruff formatter не настроен" -ForegroundColor Yellow
        $warnings += "Добавьте Ruff как defaultFormatter"
    }

} catch {
    Write-Host "  ❌ Ошибка чтения settings.json" -ForegroundColor Red
    $errors += "Проверьте синтаксис settings.json"
}

# 4. Проверка установленных расширений
Write-Host "`n📦 Проверка расширений..." -ForegroundColor Yellow

$codeCommand = Get-Command code -ErrorAction SilentlyContinue

if ($codeCommand) {
    $installedExtensions = code --list-extensions 2>&1

    $requiredExtensions = @(
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff"
    )

    foreach ($ext in $requiredExtensions) {
        if ($installedExtensions -contains $ext) {
            Write-Host "  ✅ $ext" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $ext НЕ установлено" -ForegroundColor Red
            $errors += "Установите: code --install-extension $ext"
        }
    }
} else {
    Write-Host "  ℹ️  'code' CLI не установлена (опционально)" -ForegroundColor Cyan
    Write-Host "     Расширения можно установить через UI VS Code" -ForegroundColor Gray
    Write-Host "     Или запустите: .\scripts\install_code_cli.ps1" -ForegroundColor Gray
}

# 5. Проверка pyproject.toml
Write-Host "`n📋 Проверка pyproject.toml..." -ForegroundColor Yellow

if (Test-Path "pyproject.toml") {
    Write-Host "  ✅ pyproject.toml найден" -ForegroundColor Green

    $tomlContent = Get-Content "pyproject.toml" -Raw

    if ($tomlContent -match '\[tool\.mypy\]') {
        Write-Host "  ✅ MyPy конфигурация присутствует" -ForegroundColor Green
    }

    if ($tomlContent -match '\[tool\.ruff\]') {
        Write-Host "  ✅ Ruff конфигурация присутствует" -ForegroundColor Green
    }

    if ($tomlContent -match '\[tool\.pytest') {
        Write-Host "  ✅ pytest конфигурация присутствует" -ForegroundColor Green
    }
} else {
    Write-Host "  ❌ pyproject.toml НЕ найден" -ForegroundColor Red
    $errors += "pyproject.toml обязателен для проекта"
}

# 6. Итоговая статистика
Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                        РЕЗУЛЬТАТЫ                              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!" -ForegroundColor Green
    Write-Host "`n   Конфигурация VS Code оптимальна!" -ForegroundColor Green
    Write-Host "   Можете запускать VS Code без ошибок.`n" -ForegroundColor Green
    exit 0
} else {
    if ($errors.Count -gt 0) {
        Write-Host "❌ НАЙДЕНО ОШИБОК: $($errors.Count)" -ForegroundColor Red
        Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "  • $error" -ForegroundColor Red
        }
    }

    if ($warnings.Count -gt 0) {
        Write-Host "`n⚠️  НАЙДЕНО ПРЕДУПРЕЖДЕНИЙ: $($warnings.Count)" -ForegroundColor Yellow
        Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  • $warning" -ForegroundColor Yellow
        }
    }

    Write-Host "`n🔧 РЕКОМЕНДАЦИИ:" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

    if ($errors -like "*Virtual environment*") {
        Write-Host "  1. Создайте виртуальное окружение:" -ForegroundColor White
        Write-Host "     python -m venv .venv`n" -ForegroundColor Gray
    }

    if ($errors -like "*расширение*") {
        Write-Host "  2. Установите расширения VS Code:" -ForegroundColor White
        Write-Host "     .\scripts\install_vscode_extensions.ps1`n" -ForegroundColor Gray
    }

    if ($errors -like "*mypy.ini*") {
        Write-Host "  3. Исправлены автоматически! Перезапустите VS Code.`n" -ForegroundColor White
    }

    Write-Host "  После исправления запустите проверку снова:" -ForegroundColor White
    Write-Host "  .\scripts\validate_vscode_config.ps1`n" -ForegroundColor Gray

    if ($errors.Count -gt 0) {
        exit 1
    } else {
        exit 0
    }
}
