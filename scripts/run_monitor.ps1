# Скрипт для запуска GitHub Actions Monitor с правильной кодировкой
# Использование: .\scripts\run_monitor.ps1

Write-Host "`n🔧 Настройка окружения..." -ForegroundColor Cyan

# Установка UTF-8 кодировки для корректного отображения эмодзи
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Путь к Python в виртуальном окружении
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = "$projectRoot\.venv\Scripts\python.exe"
$scriptPath = "$PSScriptRoot\github_actions_monitor.py"

# Проверка наличия виртуального окружения
if (-not (Test-Path $pythonPath)) {
    Write-Host "❌ Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "   Создайте его командой: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Окружение настроено`n" -ForegroundColor Green

# Запуск скрипта
try {
    & $pythonPath $scriptPath
}
catch {
    Write-Host "`n❌ Ошибка при выполнении скрипта: $_" -ForegroundColor Red
    exit 1
}

# Сохранение кода завершения
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n✅ Мониторинг завершен успешно`n" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Мониторинг завершен с кодом: $exitCode`n" -ForegroundColor Yellow
}

exit $exitCode
