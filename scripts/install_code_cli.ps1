# Install VS Code CLI
# Автоматическая установка 'code' команды в PATH

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║               VS CODE CLI INSTALLER                           ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Проверка текущего состояния
Write-Host "🔍 Проверка наличия code CLI..." -ForegroundColor Yellow

if (Get-Command code -ErrorAction SilentlyContinue) {
    Write-Host "✅ code CLI уже установлен и доступен в PATH!" -ForegroundColor Green
    Write-Host "`nВерсия:" -ForegroundColor Cyan
    code --version | Select-Object -First 3
    Write-Host "`nНичего делать не нужно! ✅`n" -ForegroundColor Green
    exit 0
}

Write-Host "⚠️  code CLI не найден в PATH" -ForegroundColor Yellow

# Поиск VS Code установки
Write-Host "`n📂 Поиск установки VS Code..." -ForegroundColor Cyan

$vscodePaths = @(
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin",
    "$env:ProgramFiles\Microsoft VS Code\bin",
    "${env:ProgramFiles(x86)}\Microsoft VS Code\bin"
)

$foundPath = $null

foreach ($path in $vscodePaths) {
    Write-Host "  Проверка: $path" -ForegroundColor Gray
    if (Test-Path "$path\code.cmd") {
        Write-Host "  ✅ Найден!" -ForegroundColor Green
        $foundPath = $path
        break
    }
}

if (-not $foundPath) {
    Write-Host "`n❌ VS Code не найден!" -ForegroundColor Red
    Write-Host "`nУстановите VS Code:" -ForegroundColor Yellow
    Write-Host "  1. Скачайте: https://code.visualstudio.com/" -ForegroundColor White
    Write-Host "  2. Установите" -ForegroundColor White
    Write-Host "  3. Запустите этот скрипт снова`n" -ForegroundColor White
    exit 1
}

# Метод 1: Добавление в PATH пользователя (рекомендуется)
Write-Host "`n🔧 Метод 1: Добавление в PATH пользователя" -ForegroundColor Cyan

try {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")

    if ($userPath -notlike "*$foundPath*") {
        Write-Host "  Добавление пути в User PATH..." -ForegroundColor Yellow
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$foundPath", "User")
        Write-Host "  ✅ Добавлено в User PATH!" -ForegroundColor Green

        # Обновляем текущую сессию
        $env:Path += ";$foundPath"

        Write-Host "`n✅ УСПЕШНО УСТАНОВЛЕНО!" -ForegroundColor Green
        Write-Host "`nПроверка установки:" -ForegroundColor Cyan
        code --version | Select-Object -First 3

        Write-Host "`n📝 ВАЖНО:" -ForegroundColor Yellow
        Write-Host "  • В текущей PowerShell сессии code уже работает ✅" -ForegroundColor Green
        Write-Host "  • Для других приложений требуется:" -ForegroundColor White
        Write-Host "    - Перезапустить терминалы" -ForegroundColor Gray
        Write-Host "    - Перезапустить приложения" -ForegroundColor Gray
        Write-Host "    - Или перезапустить VS Code" -ForegroundColor Gray

        Write-Host "`n🎉 Готово! code CLI установлен!" -ForegroundColor Green
        Write-Host "`nПопробуйте:" -ForegroundColor Cyan
        Write-Host "  code --version" -ForegroundColor White
        Write-Host "  code .  (открыть текущую папку)`n" -ForegroundColor White

        exit 0
    } else {
        Write-Host "  ✓ Путь уже есть в User PATH" -ForegroundColor Green
    }
} catch {
    Write-Host "  ❌ Ошибка при добавлении в PATH: $_" -ForegroundColor Red
}

# Метод 2: Через VS Code команду
Write-Host "`n🔧 Метод 2: Через VS Code (ручная установка)" -ForegroundColor Cyan
Write-Host "`nВыполните следующие шаги:" -ForegroundColor Yellow
Write-Host "  1. Откройте VS Code" -ForegroundColor White
Write-Host "  2. Нажмите: Ctrl+Shift+P" -ForegroundColor White
Write-Host "  3. Введите: Shell Command: Install 'code' command in PATH" -ForegroundColor White
Write-Host "  4. Нажмите Enter" -ForegroundColor White
Write-Host "  5. Перезапустите терминал`n" -ForegroundColor White

Write-Host "После выполнения проверьте:" -ForegroundColor Cyan
Write-Host "  code --version`n" -ForegroundColor White

# Метод 3: Создание символической ссылки (для текущей сессии)
Write-Host "`n🔧 Метод 3: Временное решение для текущей сессии" -ForegroundColor Cyan

$tempScript = "$env:TEMP\code_wrapper.ps1"
@"
# Wrapper for code CLI
& "$foundPath\code.cmd" `$args
"@ | Out-File -FilePath $tempScript -Encoding UTF8

Set-Alias -Name code -Value $tempScript -Scope Global

Write-Host "  ✅ Создан временный alias для текущей сессии" -ForegroundColor Green
Write-Host "  (работает только в текущем PowerShell окне)" -ForegroundColor Gray

Write-Host "`nТестирование..." -ForegroundColor Cyan
try {
    code --version | Select-Object -First 3
    Write-Host "`n✅ code работает в текущей сессии!" -ForegroundColor Green
} catch {
    Write-Host "`n❌ Не удалось запустить code" -ForegroundColor Red
}

Write-Host "`n📌 РЕКОМЕНДАЦИЯ:" -ForegroundColor Yellow
Write-Host "  Используйте Метод 1 (добавление в PATH) для постоянной установки`n" -ForegroundColor White
