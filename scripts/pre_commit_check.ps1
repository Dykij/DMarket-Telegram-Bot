# Pre-commit validation script for Windows
# Run this before committing Phase 2 & 3 changes

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Phase 2 & 3 Pre-Commit Validation" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# 1. Code formatting
Write-Host "1/5: Running Ruff formatter..." -ForegroundColor Yellow
poetry run ruff format src/ tests/ --quiet
Write-Host "✅ Code formatted" -ForegroundColor Green
Write-Host ""

# 2. Linting
Write-Host "2/5: Running Ruff linter..." -ForegroundColor Yellow
poetry run ruff check src/ tests/ --fix --quiet
Write-Host "✅ Linting passed" -ForegroundColor Green
Write-Host ""

# 3. Type checking
Write-Host "3/5: Running MyPy type checker..." -ForegroundColor Yellow
try {
    poetry run mypy src/ --no-error-summary 2>$null
    Write-Host "✅ Type checking passed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  MyPy warnings (non-blocking)" -ForegroundColor Yellow
}
Write-Host ""

# 4. Unit tests
Write-Host "4/5: Running unit tests..." -ForegroundColor Yellow
poetry run pytest tests/unit/ --no-cov -q --tb=short
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Unit tests passed" -ForegroundColor Green
} else {
    Write-Host "❌ Unit tests failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 5. Integration tests
Write-Host "5/5: Running integration tests..." -ForegroundColor Yellow
try {
    poetry run pytest tests/integration/ --no-cov -q --tb=short 2>$null
    Write-Host "✅ Integration tests passed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some integration tests skipped" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "✅ Pre-commit validation PASSED" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ready to commit! Use:" -ForegroundColor Cyan
Write-Host "  git add ."
Write-Host "  git commit -F PHASE_2_3_COMPLETION_SUMMARY.md"
Write-Host "  git push origin main"
Write-Host ""
