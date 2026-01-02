"""Automatic Arbitrage handler with mode selection.

This module handles the "Automatic Arbitrage" button functionality:
1. Mode selection (Boost, Standard, Medium, Advanced, Pro)
2. API health check before scanning
3. Integration with ScannerManager
4. Multi-game scanning
5. Results notification

Features:
- Interactive mode selection via inline keyboard
- Pre-scan API validation
- Utilizes ScannerManager for efficient scanning
- Supports all games simultaneously
- Progress updates during scanning
"""

import logging

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from src.dmarket.dmarket_api import DMarketAPI
from src.telegram_bot.keyboards.minimal_main import get_mode_selection_keyboard
from src.utils.sentry_breadcrumbs import add_command_breadcrumb

logger = structlog.get_logger(__name__)
std_logger = logging.getLogger(__name__)


# Mode to level mapping (corresponds to scanner levels)
MODE_LEVEL_MAP = {
    "boost": "boost",
    "standard": "standard",
    "medium": "medium",
    "advanced": "advanced",
    "pro": "pro",
}

# Mode descriptions for user
MODE_DESCRIPTIONS = {
    "boost": "🚀 Boost: $0.50-$3, quick turnover, 10%+ margin",
    "standard": "📊 Standard: $3-$10, balanced, 12%+ margin",
    "medium": "💎 Medium: $10-$30, good margins, 15%+ margin",
    "advanced": "⭐ Advanced: $30-$100, high value, 18%+ margin",
    "pro": "👑 Pro: $100+, premium items, 20%+ margin",
}


async def handle_automatic_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Automatic Arbitrage button - initiate mode selection.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        None (sends mode selection keyboard)
    """
    user = update.effective_user
    if not user:
        return

    message = update.message or (update.callback_query.message if update.callback_query else None)
    if not message:
        return

    add_command_breadcrumb(
        command="automatic_arbitrage",
        user_id=user.id,
        username=user.username or "",
        chat_id=message.chat_id,
    )

    logger.info("automatic_arbitrage_started", user_id=user.id)

    # Send mode selection keyboard
    await message.reply_text(
        "🤖 <b>Automatic Arbitrage</b>\n\n"
        "Select your trading mode:\n\n"
        f"{MODE_DESCRIPTIONS['boost']}\n"
        f"{MODE_DESCRIPTIONS['standard']}\n"
        f"{MODE_DESCRIPTIONS['medium']}\n"
        f"{MODE_DESCRIPTIONS['advanced']}\n"
        f"{MODE_DESCRIPTIONS['pro']}\n\n"
        "Each mode scans all supported games simultaneously.",
        reply_markup=get_mode_selection_keyboard(),
        parse_mode="HTML",
    )


async def handle_mode_selection_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle mode selection callback and start scanning.

    Args:
        update: Telegram update with callback query
        context: Callback context

    Returns:
        None (starts arbitrage scan)
    """
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    user = update.effective_user
    if not user:
        return

    # Extract mode from callback data (e.g., "mode_boost" -> "boost")
    mode = query.data.replace("mode_", "")
    level = MODE_LEVEL_MAP.get(mode, "standard")

    logger.info("mode_selected", user_id=user.id, mode=mode, level=level)

    # Update message to show selection
    if query.message:
        await query.message.edit_text(
            f"✅ Selected mode: <b>{mode.capitalize()}</b>\n\n"
            f"{MODE_DESCRIPTIONS[mode]}\n\n"
            f"🔍 Performing API check...",
            parse_mode="HTML",
        )

    # Step 1: API Check
    api_client: DMarketAPI | None = context.bot_data.get("dmarket_api")
    if not api_client:
        if query.message:
            await query.message.edit_text(
                "❌ <b>Error</b>\n\n"
                "API client not initialized.\n"
                "Please restart the bot or contact administrator.",
                parse_mode="HTML",
            )
        logger.error("mode_scan_failed", reason="no_api_client", user_id=user.id)
        return

    # Quick API health check
    try:
        balance_result = await api_client.get_balance()
        if balance_result.get("error"):
            if query.message:
                await query.message.edit_text(
                    f"❌ <b>API Check Failed</b>\n\n"
                    f"Error: {balance_result.get('error_message', 'Unknown error')}\n\n"
                    f"Please check API configuration and try again.",
                    parse_mode="HTML",
                )
            logger.error(
                "mode_scan_api_check_failed",
                error=balance_result.get("error_message"),
                user_id=user.id,
            )
            return
    except Exception as e:
        if query.message:
            await query.message.edit_text(
                f"❌ <b>API Check Failed</b>\n\nError: {e!s}\n\nPlease verify API connectivity.",
                parse_mode="HTML",
            )
        logger.error(
            "mode_scan_api_exception",
            error=str(e),
            user_id=user.id,
            exc_info=True,
        )
        return

    # Step 2: Start scanning
    if query.message:
        await query.message.edit_text(
            f"✅ API Check passed!\n\n"
            f"🔍 <b>Starting {mode.capitalize()} scan...</b>\n\n"
            f"Scanning all supported games:\n"
            f"• CS:GO/CS2\n"
            f"• Dota 2\n"
            f"• TF2\n"
            f"• Rust\n\n"
            f"This may take 30-60 seconds...",
            parse_mode="HTML",
        )

    # Get ScannerManager from bot_data
    scanner_manager = context.bot_data.get("scanner_manager")

    if not scanner_manager:
        # Fallback: use direct API scanning if ScannerManager not available
        if query.message:
            await query.message.edit_text(
                "⚠️ <b>Scanner Manager not available</b>\n\n"
                "Using fallback scanning method...\n"
                "Note: This may be slower than parallel scanning.",
                parse_mode="HTML",
            )
        logger.warning("scanner_manager_not_available", user_id=user.id)

        # Direct scanning fallback (simplified)
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner(api_client=api_client)
        try:
            results = await scanner.scan_level(
                level=level,
                game="csgo",  # Fallback to single game
                max_results=10,
            )

            if results:
                results_text = f"✅ <b>Found {len(results)} opportunities!</b>\n\n"
                for i, opp in enumerate(results[:5], 1):
                    results_text += (
                        f"{i}. {opp.get('item_name', 'Unknown')}\n"
                        f"   💰 Price: ${opp.get('price', 0):.2f}\n"
                        f"   📈 Profit: {opp.get('profit_margin', 0):.1f}%\n\n"
                    )

                if len(results) > 5:
                    results_text += f"...and {len(results) - 5} more opportunities.\n"

                if query.message:
                    await query.message.edit_text(results_text, parse_mode="HTML")
            elif query.message:
                await query.message.edit_text(
                    f"ℹ️ <b>No opportunities found</b>\n\n"
                    f"Mode: {mode.capitalize()}\n"
                    f"Game: CS:GO\n\n"
                    f"Try a different mode or check back later.",
                    parse_mode="HTML",
                )

            logger.info(
                "fallback_scan_completed",
                user_id=user.id,
                mode=mode,
                opportunities_found=len(results),
            )

        except Exception as e:
            if query.message:
                await query.message.edit_text(
                    f"❌ <b>Scan Failed</b>\n\nError: {e!s}\n\nPlease try again later.",
                    parse_mode="HTML",
                )
            logger.error(
                "fallback_scan_failed",
                error=str(e),
                user_id=user.id,
                exc_info=True,
            )
        return

    # Use ScannerManager for parallel scanning
    try:
        games = ["csgo", "dota2", "rust", "tf2"]
        results = await scanner_manager.scan_multiple_games(
            games=games,
            level=level,
            max_items_per_game=10,
        )

        # Aggregate results
        total_opportunities = sum(len(v) for v in results.values())

        if total_opportunities > 0:
            results_text = (
                f"✅ <b>Scan Complete!</b>\n\n"
                f"Found <b>{total_opportunities}</b> opportunities across all games:\n\n"
            )

            for game, opps in results.items():
                if opps:
                    results_text += f"🎮 <b>{game.upper()}</b>: {len(opps)} items\n"

            results_text += f"\n📊 Mode: {mode.capitalize()}\n"
            results_text += "⏱️ Scan completed successfully!\n\n"
            results_text += (
                "Use /arbitrage command for detailed view\nor check specific game results."
            )

            if query.message:
                await query.message.edit_text(results_text, parse_mode="HTML")

            logger.info(
                "parallel_scan_success",
                user_id=user.id,
                mode=mode,
                total_opportunities=total_opportunities,
                games_scanned=len(games),
            )
        else:
            if query.message:
                await query.message.edit_text(
                    f"ℹ️ <b>No opportunities found</b>\n\n"
                    f"Mode: {mode.capitalize()}\n"
                    f"Games: All supported\n\n"
                    f"Market conditions may not be favorable right now.\n"
                    f"Try again in a few minutes or select a different mode.",
                    parse_mode="HTML",
                )

            logger.info(
                "parallel_scan_no_results",
                user_id=user.id,
                mode=mode,
                games_scanned=len(games),
            )

    except Exception as e:
        if query.message:
            await query.message.edit_text(
                f"❌ <b>Scan Failed</b>\n\n"
                f"Error: {e!s}\n\n"
                f"This may be due to:\n"
                f"• Temporary API issues\n"
                f"• Network connectivity problems\n"
                f"• Rate limiting\n\n"
                f"Please try again in a few minutes.",
                parse_mode="HTML",
            )

        logger.error(
            "parallel_scan_failed",
            error=str(e),
            user_id=user.id,
            mode=mode,
            exc_info=True,
        )
