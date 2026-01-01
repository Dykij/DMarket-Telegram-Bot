# VS Code Extensions Auto-Installer
# Автоматическая установка всех рекомендуемых расширений для проекта

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        VS Code Extensions Auto-Installer                      ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Проверка наличия code CLI
if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ОШИБКА: 'code' команда не найдена в PATH`n" -ForegroundColor Red
    Write-Host "Решение:" -ForegroundColor Yellow
    Write-Host "  1. Откройте VS Code" -ForegroundColor White
    Write-Host "  2. Нажмите Ctrl+Shift+P" -ForegroundColor White
    Write-Host "  3. Введите: Shell Command: Install 'code' command in PATH" -ForegroundColor White
    Write-Host "  4. Перезапустите PowerShell" -ForegroundColor White
    Write-Host "`nИли установите расширения вручную через VS Code UI (Ctrl+Shift+X)`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ VS Code CLI найден`n" -ForegroundColor Green

# Список обязательных расширений
$requiredExtensions = @(
    @{id="ms-python.python"; name="Python"},
    @{id="ms-python.vscode-pylance"; name="Pylance"},
    @{id="ms-python.debugpy"; name="Python Debugger"},
    @{id="charliermarsh.ruff"; name="Ruff"},
    @{id="ms-python.mypy-type-checker"; name="MyPy Type Checker"},
    @{id="github.copilot"; name="GitHub Copilot"},
    @{id="github.copilot-chat"; name="GitHub Copilot Chat"}
)

# Список рекомендуемых расширений
$recommendedExtensions = @(
    @{id="littlefoxteam.vscode-python-test-adapter"; name="Python Test Adapter"},
    @{id="hbenl.vscode-test-explorer"; name="Test Explorer UI"},
    @{id="eamodio.gitlens"; name="GitLens"},
    @{id="streetsidesoftware.code-spell-checker"; name="Code Spell Checker"},
    @{id="streetsidesoftware.code-spell-checker-russian"; name="Russian Spell Checker"},
    @{id="usernamehw.errorlens"; name="Error Lens"},
    @{id="nhoizey.gremlins"; name="Gremlins Tracker"},
    @{id="redhat.vscode-yaml"; name="YAML Support"},
    @{id="tamasfe.even-better-toml"; name="Better TOML"},
    @{id="yzhang.markdown-all-in-one"; name="Markdown All in One"},
    @{id="PKief.material-icon-theme"; name="Material Icon Theme"}
)

# Получаем список уже установленных расширений
Write-Host "📋 Проверка установленных расширений..." -ForegroundColor Yellow
$installedExtensions = code --list-extensions

function Install-Extension {
    param(
        [string]$ExtensionId,
        [string]$ExtensionName
    )
    
    if ($installedExtensions -contains $ExtensionId) {
        Write-Host "  ✓ $ExtensionName" -ForegroundColor Green -NoNewline
        Write-Host " (уже установлено)" -ForegroundColor Gray
        return $true
    } else {
        Write-Host "  ⏳ Установка $ExtensionName..." -ForegroundColor Yellow
        $output = code --install-extension $ExtensionId 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $ExtensionName установлено" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  ❌ Ошибка установки $ExtensionName" -ForegroundColor Red
            Write-Host "     $output" -ForegroundColor Gray
            return $false
        }
    }
}

# Установка обязательных расширений
Write-Host "`n🔧 Установка ОБЯЗАТЕЛЬНЫХ расширений:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

$requiredSuccess = 0
$requiredTotal = $requiredExtensions.Count

foreach ($ext in $requiredExtensions) {
    if (Install-Extension -ExtensionId $ext.id -ExtensionName $ext.name) {
        $requiredSuccess++
    }
}

# Установка рекомендуемых расширений
Write-Host "`n📦 Установка РЕКОМЕНДУЕМЫХ расширений:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

$recommendedSuccess = 0
$recommendedTotal = $recommendedExtensions.Count

foreach ($ext in $recommendedExtensions) {
    if (Install-Extension -ExtensionId $ext.id -ExtensionName $ext.name) {
        $recommendedSuccess++
    }
}

# Итоговая статистика
Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    УСТАНОВКА ЗАВЕРШЕНА                         ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📊 Статистика:" -ForegroundColor Cyan
Write-Host "  Обязательные: $requiredSuccess/$requiredTotal" -ForegroundColor $(if ($requiredSuccess -eq $requiredTotal) {"Green"} else {"Yellow"})
Write-Host "  Рекомендуемые: $recommendedSuccess/$recommendedTotal" -ForegroundColor $(if ($recommendedSuccess -eq $recommendedTotal) {"Green"} else {"Yellow"})
Write-Host "  Всего: $($requiredSuccess + $recommendedSuccess)/$($requiredTotal + $recommendedTotal)`n" -ForegroundColor Cyan

if ($requiredSuccess -eq $requiredTotal) {
    Write-Host "✅ Все обязательные расширения установлены!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Не все обязательные расширения установлены!" -ForegroundColor Yellow
    Write-Host "   Попробуйте установить их вручную через VS Code (Ctrl+Shift+X)`n" -ForegroundColor White
}

# Следующие шаги
Write-Host "🚀 Следующие шаги:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
Write-Host "  1. Перезапустите VS Code" -ForegroundColor Yellow
Write-Host "  2. Откройте проект: code ." -ForegroundColor Yellow
Write-Host "  3. Выберите Python interpreter: Ctrl+Shift+P → Python: Select Interpreter" -ForegroundColor Yellow
Write-Host "  4. Проверьте настройки: Ctrl+," -ForegroundColor Yellow
Write-Host "`n  Готово к работе! 🎉`n" -ForegroundColor Green

# Предложение открыть VS Code
$response = Read-Host "Хотите открыть проект в VS Code сейчас? (y/n)"
if ($response -eq "y" -or $response -eq "Y" -or $response -eq "д" -or $response -eq "Д") {
    Write-Host "`n🚀 Открываю VS Code..." -ForegroundColor Green
    code .
} else {
    Write-Host "`n👋 До встречи!" -ForegroundColor Cyan
}
