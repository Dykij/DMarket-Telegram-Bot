# Migration script for refactored modules
$refactoredFiles = @(
    @{Src="src\dmarket\dmarket_api_refactored.py"; Dest="src\dmarket\dmarket_api.py"},
    @{Src="src\dmarket\arbitrage_scanner_refactored.py"; Dest="src\dmarket\arbitrage_scanner.py"},
    @{Src="src\dmarket\auto_trader_refactored.py"; Dest="src\dmarket\auto_trader.py"},
    @{Src="src\dmarket\market_analysis_refactored.py"; Dest="src\dmarket\market_analysis.py"},
    @{Src="src\dmarket\api\client_refactored.py"; Dest="src\dmarket\api\client.py"},
    @{Src="src\telegram_bot\handlers\scanner_handler_refactored.py"; Dest="src\telegram_bot\handlers\scanner_handler.py"},
    @{Src="src\telegram_bot\handlers\target_handler_refactored.py"; Dest="src\telegram_bot\handlers\target_handler.py"},
    @{Src="src\telegram_bot\handlers\market_analysis_handler_refactored.py"; Dest="src\telegram_bot\handlers\market_analysis_handler.py"},
    @{Src="src\telegram_bot\handlers\callbacks_refactored.py"; Dest="src\telegram_bot\handlers\callbacks.py"},
    @{Src="src\telegram_bot\handlers\notification_filters_handler_refactored.py"; Dest="src\telegram_bot\handlers\notification_filters_handler.py"},
    @{Src="src\telegram_bot\handlers\settings_handlers_refactored.py"; Dest="src\telegram_bot\handlers\settings_handlers.py"},
    @{Src="src\telegram_bot\handlers\game_filter_handlers_refactored.py"; Dest="src\telegram_bot\handlers\game_filter_handlers.py"},
    @{Src="src\telegram_bot\commands\balance_command_refactored.py"; Dest="src\telegram_bot\commands\balance_command.py"}
)

$backupDir = "backups\pre_migration_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

Write-Host "Created backup directory: $backupDir" -ForegroundColor Green

foreach ($file in $refactoredFiles) {
    if (Test-Path $file.Src) {
        # Backup original if exists
        if (Test-Path $file.Dest) {
            $backupPath = Join-Path $backupDir $file.Dest
            $backupParent = Split-Path $backupPath -Parent
            New-Item -ItemType Directory -Path $backupParent -Force | Out-Null
            Copy-Item $file.Dest $backupPath -Force
            Write-Host "Backed up: $($file.Dest)" -ForegroundColor Yellow
        }
        
        # Copy refactored to original location
        Copy-Item $file.Src $file.Dest -Force
        Write-Host "Migrated: $($file.Src) -> $($file.Dest)" -ForegroundColor Green
    }
}

Write-Host "`nMigration complete! Backup saved to: $backupDir" -ForegroundColor Cyan
