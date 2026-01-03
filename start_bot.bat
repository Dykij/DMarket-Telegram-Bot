@echo off
title DMarket Trading Bot
color 0A

echo ============================================================
echo           DMarket Telegram Bot - Auto-Restart Script
echo ============================================================
echo.

:loop
echo [%date% %time%] Starting DMarket Bot...
echo.

:: Change to script directory
cd /d "%~dp0"

:: Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found at .venv\Scripts\activate.bat
    echo Please create venv first: python -m venv .venv
    pause
    exit /b 1
)

:: Run the bot
python -m src.main

:: Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [%date% %time%] Bot stopped gracefully.
    echo Press any key to restart, or Ctrl+C to exit...
    pause >nul
) else (
    echo.
    echo [%date% %time%] Bot crashed with exit code: %ERRORLEVEL%
    echo Restarting in 10 seconds... (Press Ctrl+C to cancel)
    timeout /t 10
)

echo.
echo ============================================================
goto loop
