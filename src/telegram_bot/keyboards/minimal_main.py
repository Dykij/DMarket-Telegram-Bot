"""Minimal main keyboard for simplified UX.

This module provides a minimalistic main menu with only 4 essential buttons:
- Automatic Arbitrage (multi-game scanning)
- View Items (profit display)
- Detailed Settings (mode configuration)
- API Check (connectivity test)

Usage:
    from src.telegram_bot.keyboards.minimal_main import get_minimal_main_keyboard

    await update.message.reply_text(
        "Welcome!",
        reply_markup=get_minimal_main_keyboard()
    )
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def get_minimal_main_keyboard() -> ReplyKeyboardMarkup:
    """Create minimal reply keyboard with 4 essential buttons.

    Returns:
        ReplyKeyboardMarkup with simplified menu
    """
    keyboard = [
        ["🤖 Automatic Arbitrage"],
        ["📦 View Items"],
        ["⚙️ Detailed Settings"],
        ["🔌 API Check"],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_mode_selection_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for arbitrage mode selection.

    Modes correspond to scanner_manager levels:
    - Boost: Low-price items ($0.50 - $3), quick turnover
    - Standard: Mid-range items ($3 - $10), balanced
    - Medium: Higher value ($10 - $30), better margins
    - Advanced: Premium items ($30 - $100), high margins
    - Pro: Top-tier items ($100+), best margins

    Returns:
        InlineKeyboardMarkup with mode selection buttons
    """
    keyboard = [
        [InlineKeyboardButton("🚀 Boost (Разгон)", callback_data="mode_boost")],
        [InlineKeyboardButton("📊 Standard (Стандарт)", callback_data="mode_standard")],
        [InlineKeyboardButton("💎 Medium (Средний)", callback_data="mode_medium")],
        [InlineKeyboardButton("⭐ Advanced (Продвинутый)", callback_data="mode_advanced")],
        [InlineKeyboardButton("👑 Pro (Профессионал)", callback_data="mode_pro")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_mode_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for detailed settings - mode configuration.

    Allows users to adjust:
    - Price ranges for each mode
    - Minimum profit margins
    - Maximum items to scan

    Returns:
        InlineKeyboardMarkup with settings options
    """
    keyboard = [
        [InlineKeyboardButton("🚀 Edit Boost Settings", callback_data="edit_boost")],
        [InlineKeyboardButton("📊 Edit Standard Settings", callback_data="edit_standard")],
        [InlineKeyboardButton("💎 Edit Medium Settings", callback_data="edit_medium")],
        [InlineKeyboardButton("⭐ Edit Advanced Settings", callback_data="edit_advanced")],
        [InlineKeyboardButton("👑 Edit Pro Settings", callback_data="edit_pro")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_games_selection_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for selecting games to scan.

    Returns:
        InlineKeyboardMarkup with game selection buttons
    """
    keyboard = [
        [InlineKeyboardButton("🎮 CS:GO/CS2", callback_data="game_csgo")],
        [InlineKeyboardButton("🎯 Dota 2", callback_data="game_dota2")],
        [InlineKeyboardButton("🔧 TF2", callback_data="game_tf2")],
        [InlineKeyboardButton("🏝️ Rust", callback_data="game_rust")],
        [InlineKeyboardButton("✅ All Games", callback_data="game_all")],
    ]
    return InlineKeyboardMarkup(keyboard)
