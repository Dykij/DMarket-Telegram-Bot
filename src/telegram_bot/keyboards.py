"""Модуль клавиатур для Telegram бота (Facade).

Данный модуль служит фасадом для обратной совместимости.
Все реализации перемещены в пакет keyboards/.

Для нового кода используйте:
    from src.telegram_bot.keyboards import ...

Deprecated: этот файл будет удалён в следующих версиях.
"""

import warnings

# Re-export everything from keyboards package
from src.telegram_bot.keyboards import (  # noqa: F401
    # Constants
    CB_BACK,
    CB_CANCEL,
    CB_GAME_PREFIX,
    CB_HELP,
    CB_NEXT_PAGE,
    CB_PREV_PAGE,
    CB_SETTINGS,
    GAMES,
    # Utils
    build_menu,
    # Arbitrage
    create_arbitrage_keyboard,
    # Settings
    create_confirm_keyboard,
    create_game_selection_keyboard,
    # Main
    create_main_keyboard,
    create_market_analysis_keyboard,
    create_pagination_keyboard,
    # Alerts
    create_price_alerts_keyboard,
    create_settings_keyboard,
    extract_callback_data,
    force_reply,
    get_alert_actions_keyboard,
    get_alert_keyboard,
    get_alert_type_keyboard,
    get_arbitrage_keyboard,
    get_auto_arbitrage_keyboard,
    get_back_to_arbitrage_keyboard,
    get_back_to_settings_keyboard,
    # WebApp
    get_combined_web_app_keyboard,
    # Filters
    get_confirm_cancel_keyboard,
    get_csgo_exterior_keyboard,
    get_csgo_weapon_type_keyboard,
    get_dmarket_webapp_keyboard,
    get_filter_keyboard,
    get_game_selection_keyboard,
    get_games_keyboard,
    get_language_keyboard,
    get_login_keyboard,
    get_main_menu_keyboard,
    get_marketplace_comparison_keyboard,
    get_modern_arbitrage_keyboard,
    get_pagination_keyboard,
    get_payment_keyboard,
    get_permanent_reply_keyboard,
    get_price_range_keyboard,
    get_rarity_keyboard,
    get_request_contact_keyboard,
    get_request_location_keyboard,
    get_risk_profile_keyboard,
    get_settings_keyboard,
    get_webapp_button,
    get_webapp_keyboard,
    remove_keyboard,
)


# Emit deprecation warning
warnings.warn(
    "Importing directly from keyboards.py is deprecated. "
    "Import from src.telegram_bot.keyboards package instead.",
    DeprecationWarning,
    stacklevel=2,
)
