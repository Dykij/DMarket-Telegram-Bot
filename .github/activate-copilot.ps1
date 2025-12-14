# GitHub Copilot Agent - Automated Activation Script
# Version: 1.0
# Date: 2025-12-14

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Copilot Agent Activation Helper" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$repo = "Dykij/DMarket-Telegram-Bot"
$baseUrl = "https://github.com/$repo"

# Check if GitHub CLI is installed
$ghInstalled = Get-Command gh -ErrorAction SilentlyContinue

if (-not $ghInstalled) {
    Write-Host "⚠️  GitHub CLI (gh) not found" -ForegroundColor Yellow
    Write-Host "`nOptions to install:" -ForegroundColor White
    Write-Host "  1. winget install --id GitHub.cli" -ForegroundColor Gray
    Write-Host "  2. choco install gh" -ForegroundColor Gray
    Write-Host "  3. scoop install gh`n" -ForegroundColor Gray

    $install = Read-Host "Do you want to install via winget now? (y/n)"

    if ($install -eq 'y') {
        Write-Host "`nInstalling GitHub CLI..." -ForegroundColor Cyan
        winget install --id GitHub.cli --silent

        Write-Host "`n✅ GitHub CLI installed!" -ForegroundColor Green
        Write-Host "⚠️  Please restart PowerShell and run this script again.`n" -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "`n⚠️  Skipping automated steps. Opening web browser for manual setup...`n" -ForegroundColor Yellow
        Start-Sleep -Seconds 2

        # Open necessary URLs
        Write-Host "Opening browser tabs..." -ForegroundColor Cyan
        Start-Process "$baseUrl/labels"
        Start-Sleep -Seconds 1
        Start-Process "$baseUrl/settings"
        Start-Sleep -Seconds 1
        Start-Process "$baseUrl/settings/actions"

        Write-Host "`n📋 Manual steps:" -ForegroundColor Yellow
        Write-Host "1. Create 6 labels in first tab" -ForegroundColor White
        Write-Host "2. Enable Copilot Agent in second tab (Settings → Copilot)" -ForegroundColor White
        Write-Host "3. Set Actions permissions in third tab" -ForegroundColor White
        Write-Host "`nSee .github/ACTIVATION_GUIDE.md for details`n" -ForegroundColor Gray
        exit 0
    }
}

Write-Host "✅ GitHub CLI found`n" -ForegroundColor Green

# Check authentication
Write-Host "Checking GitHub authentication..." -ForegroundColor Cyan
$authStatus = gh auth status 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Not authenticated with GitHub" -ForegroundColor Yellow
    Write-Host "`nStarting authentication...`n" -ForegroundColor White
    gh auth login

    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ Authentication failed. Exiting.`n" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Authenticated with GitHub`n" -ForegroundColor Green

# Create labels
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating Labels" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$labels = @(
    @{Name="copilot-task"; Color="0E8A16"; Description="Task for GitHub Copilot Coding Agent"},
    @{Name="copilot-test"; Color="1D76DB"; Description="Test coverage improvement task"},
    @{Name="copilot-refactor"; Color="FBCA04"; Description="Code refactoring task"},
    @{Name="copilot-docs"; Color="5319E7"; Description="Documentation update task"},
    @{Name="copilot-security"; Color="D93F0B"; Description="Security fix task"},
    @{Name="copilot-bugfix"; Color="EE0701"; Description="Bug fix task"}
)

$labelsCreated = 0
foreach ($label in $labels) {
    Write-Host "Creating label: $($label.Name)..." -NoNewline

    $result = gh label create $label.Name `
        --color $label.Color `
        --description $label.Description `
        --repo $repo 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅" -ForegroundColor Green
        $labelsCreated++
    } elseif ($result -like "*already exists*") {
        Write-Host " ⚠️  Already exists" -ForegroundColor Yellow
    } else {
        Write-Host " ❌ Failed" -ForegroundColor Red
        Write-Host "   Error: $result" -ForegroundColor Red
    }
}

Write-Host "`n✅ Labels: $labelsCreated/6 created`n" -ForegroundColor Green

# Check workflows
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Checking Workflows" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Fetching workflow list..." -ForegroundColor White
$workflows = gh workflow list --repo $repo 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nCopilot workflows:" -ForegroundColor Cyan
    $workflows | Select-String "copilot" -CaseSensitive | ForEach-Object {
        Write-Host "  ✅ $_" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  Could not fetch workflows" -ForegroundColor Yellow
}

# Manual steps reminder
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Manual Steps Required" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "⚠️  The following require web browser:`n" -ForegroundColor Yellow

Write-Host "1. Enable Copilot Agent:" -ForegroundColor White
Write-Host "   $baseUrl/settings" -ForegroundColor Gray
Write-Host "   → Code and automation → Copilot" -ForegroundColor Gray
Write-Host "   → Enable 'Copilot coding agent'`n" -ForegroundColor Gray

Write-Host "2. Configure Actions permissions:" -ForegroundColor White
Write-Host "   $baseUrl/settings/actions" -ForegroundColor Gray
Write-Host "   → Workflow permissions: 'Read and write'" -ForegroundColor Gray
Write-Host "   → Allow GitHub Actions to create PRs`n" -ForegroundColor Gray

Write-Host "3. Create test issue:" -ForegroundColor White
Write-Host "   $baseUrl/issues/new/choose" -ForegroundColor Gray
Write-Host "   → Select 'Copilot Task' template`n" -ForegroundColor Gray

$openBrowser = Read-Host "`nOpen these pages in browser now? (y/n)"

if ($openBrowser -eq 'y') {
    Write-Host "`nOpening browser tabs..." -ForegroundColor Cyan
    Start-Process "$baseUrl/settings"
    Start-Sleep -Seconds 1
    Start-Process "$baseUrl/settings/actions"
    Start-Sleep -Seconds 1
    Start-Process "$baseUrl/issues/new/choose"
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Automated Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "✅ Labels created: $labelsCreated/6" -ForegroundColor Green
Write-Host "⏳ Manual steps: 3 remaining (~10 minutes)`n" -ForegroundColor Yellow

Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   .github/ACTIVATION_GUIDE.md" -ForegroundColor White
Write-Host "   .github/COPILOT_AGENT_GUIDE.md`n" -ForegroundColor White

Write-Host "Next: Complete manual steps in browser`n" -ForegroundColor Yellow

# Create completion marker
$completionFile = ".github/.copilot-setup-status.json"
$status = @{
    labels_created = $labelsCreated -eq 6
    automated_setup_completed = $true
    timestamp = (Get-Date).ToString("o")
    manual_steps_remaining = 3
} | ConvertTo-Json

Set-Content -Path $completionFile -Value $status
Write-Host "✅ Status saved to $completionFile`n" -ForegroundColor Green
