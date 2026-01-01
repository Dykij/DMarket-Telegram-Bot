# Repository Cleanup Script
# Очистка репозитория от временных и cache файлов

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              REPOSITORY CLEANUP SCRIPT                        ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$totalSize = 0
$totalFiles = 0

function Remove-Directory {
    param([string]$Path, [string]$Name)

    if (Test-Path $Path) {
        $size = (Get-ChildItem $Path -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
        $files = (Get-ChildItem $Path -Recurse -File | Measure-Object).Count

        Write-Host "  🗑️  Удаление $Name..." -ForegroundColor Yellow
        Write-Host "     Файлов: $files, Размер: $([math]::Round($size, 2)) MB" -ForegroundColor Gray

        Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue

        $script:totalSize += $size
        $script:totalFiles += $files

        Write-Host "  ✅ Удалено!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  ✓ $Name не найдено" -ForegroundColor Gray
        return $false
    }
}

function Remove-Files {
    param([string]$Pattern, [string]$Name)

    $files = Get-ChildItem -Recurse -Filter $Pattern -ErrorAction SilentlyContinue

    if ($files.Count -gt 0) {
        $size = ($files | Measure-Object -Property Length -Sum).Sum / 1MB

        Write-Host "  🗑️  Удаление $Name..." -ForegroundColor Yellow
        Write-Host "     Файлов: $($files.Count), Размер: $([math]::Round($size, 2)) MB" -ForegroundColor Gray

        $files | Remove-Item -Force -ErrorAction SilentlyContinue

        $script:totalSize += $size
        $script:totalFiles += $files.Count

        Write-Host "  ✅ Удалено!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  ✓ $Name не найдено" -ForegroundColor Gray
        return $false
    }
}

Write-Host "📦 Очистка Python cache..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

# Python cache
$pycacheDirs = Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
if ($pycacheDirs.Count -gt 0) {
    Write-Host "  🗑️  Удаление __pycache__ директорий..." -ForegroundColor Yellow
    Write-Host "     Найдено: $($pycacheDirs.Count) директорий" -ForegroundColor Gray
    $pycacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ Удалено!" -ForegroundColor Green
}

Remove-Files "*.pyc" ".pyc файлы"
Remove-Files "*.pyo" ".pyo файлы"
Remove-Files "*.pyd" ".pyd файлы"

Write-Host "`n🧪 Очистка test cache..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

Remove-Directory ".pytest_cache" "pytest cache"
Remove-Directory ".hypothesis" "hypothesis cache"
Remove-Directory ".tox" "tox cache"

Write-Host "`n🔍 Очистка linter/type-checker cache..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

Remove-Directory ".mypy_cache" "mypy cache"
Remove-Directory ".ruff_cache" "ruff cache"
Remove-Files ".dmypy.json" "dmypy файлы"

Write-Host "`n📊 Очистка coverage..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

Remove-Directory "htmlcov" "HTML coverage"
Remove-Files ".coverage" "coverage database"
Remove-Files "coverage.xml" "coverage XML"
Remove-Files "coverage.json" "coverage JSON"

Write-Host "`n🏗️  Очистка build artifacts..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

Remove-Directory "build" "build директория"
Remove-Directory "dist" "dist директория"
Get-ChildItem -Recurse -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
}

Write-Host "`n🗄️  Очистка временных файлов..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

Remove-Files "*.tmp" "временные файлы"
Remove-Files "*.temp" "temp файлы"
Remove-Files "*.log" "log файлы (кроме критичных)"
Remove-Files "*.bak" "backup файлы"
Remove-Files "*.backup" "backup файлы"
Remove-Files "*~" "editor backup файлы"

Write-Host "`n📁 Очистка пустых директорий..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

$emptyDirs = Get-ChildItem -Recurse -Directory -ErrorAction SilentlyContinue |
    Where-Object { -not (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue) } |
    Where-Object { $_.FullName -notmatch "\.venv|node_modules|\.git" }

if ($emptyDirs.Count -gt 0) {
    Write-Host "  🗑️  Найдено пустых директорий: $($emptyDirs.Count)" -ForegroundColor Yellow
    $emptyDirs | ForEach-Object {
        Write-Host "     • $($_.Name)" -ForegroundColor Gray
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  ✅ Удалено!" -ForegroundColor Green
} else {
    Write-Host "  ✓ Пустых директорий не найдено" -ForegroundColor Gray
}

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                     ОЧИСТКА ЗАВЕРШЕНА                          ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📊 Статистика:" -ForegroundColor Cyan
Write-Host "  • Удалено файлов: $totalFiles" -ForegroundColor White
Write-Host "  • Освобождено места: $([math]::Round($totalSize, 2)) MB`n" -ForegroundColor White

Write-Host "✅ Репозиторий очищен!" -ForegroundColor Green
Write-Host "🎯 Рекомендуется запустить: git status`n" -ForegroundColor Yellow
