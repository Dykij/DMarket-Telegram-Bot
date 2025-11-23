"""Balance command handler."""

from datetime import datetime
import logging
import traceback

from telegram import CallbackQuery, Message, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from src.telegram_bot.config_data import ARBITRAGE_MODES
from src.telegram_bot.keyboards import get_back_to_arbitrage_keyboard
from src.telegram_bot.utils.api_helper import create_dmarket_api_client
from src.utils.exceptions import APIError, handle_api_error


logger = logging.getLogger(__name__)


async def check_balance_command(
    message: CallbackQuery | Update | Message,
    context: CallbackContext,
) -> None:
    """Check DMarket balance and API connection, show account stats.

    Args:
        message: Source message, callback query or Update object
        context: Callback context

    """
    # Determine message type
    is_callback = isinstance(message, CallbackQuery)
    is_message = isinstance(message, Message)
    is_update = isinstance(message, Update) and (not is_callback and not is_message)

    if is_callback:
        # For callback, send temporary checking message
        await message.edit_message_text(
            text="🔄 <b>Проверка подключения к DMarket API...</b>",
            parse_mode=ParseMode.HTML,
        )
        processing_message = None
    elif is_message:
        # For normal message, send temporary checking message
        processing_message = await message.reply_text(
            text="🔄 <b>Проверка подключения к DMarket API...</b>",
            parse_mode=ParseMode.HTML,
        )
    elif is_update and hasattr(message, "message") and message.message:
        # For Update object
        processing_message = await message.message.reply_text(
            text="🔄 <b>Проверка подключения к DMarket API...</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        logger.error(
            "Failed to get message object for response. Type: %s",
            type(message),
        )
        return

    try:
        # Create API client
        api_client = create_dmarket_api_client(context)

        if not api_client:
            error_text = (
                "❌ <b>Ошибка подключения:</b>\n\n"
                "Не удалось создать клиент DMarket API. "
                "Проверьте, что ключи API настроены правильно."
            )

            if is_callback:
                await message.edit_message_text(
                    text=error_text,
                    reply_markup=get_back_to_arbitrage_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
            elif processing_message:
                await processing_message.edit_text(
                    text=error_text,
                    parse_mode=ParseMode.HTML,
                )
            return

        # Update status
        status_text = "🔄 <b>Проверка баланса DMarket...</b>"
        if is_callback:
            await message.edit_message_text(
                text=status_text,
                parse_mode=ParseMode.HTML,
            )
        elif processing_message:
            await processing_message.edit_text(
                text=status_text,
                parse_mode=ParseMode.HTML,
            )

        # Check balance
        try:
            # Try new balance endpoint first
            balance_result = await api_client.get_user_balance()

            # Check for API error in response
            if balance_result.get("error", False):
                error_msg = balance_result.get(
                    "error_message",
                    "Неизвестная ошибка API",
                )
                error_code = balance_result.get("status_code", "неизвестный код")

                # Special handling for 404 error
                if (
                    error_code == 404
                    or "404" in str(error_msg)
                    or "not found" in str(error_msg).lower()
                ):
                    error_text = (
                        "⚠️ <b>Trading API недоступен (404)</b>\n\n"
                        "Ваши API ключи работают, но не имеют доступа к "
                        "приватным функциям DMarket (баланс, инвентарь, "
                        "торговля).\n\n"
                        "<b>Это ограничение DMarket API, а не ошибка бота!</b>"
                        "\n\n"
                        "📋 <b>Что работает:</b>\n"
                        "✅ Поиск предметов на маркете\n"
                        "✅ Просмотр цен\n"
                        "✅ Анализ рынка\n"
                        "✅ Поиск арбитражных возможностей\n\n"
                        "🔒 <b>Для доступа к балансу и торговле:</b>\n"
                        "1. Войдите на dmarket.com\n"
                        "2. Настройки → API Keys\n"
                        "3. Активируйте <b>Trading API</b>\n"
                        "4. Создайте новые ключи с полными правами\n"
                        "5. Обновите ключи в боте командой /setup\n\n"
                        "📖 Подробнее: НАСТРОЙКА_API_КЛЮЧЕЙ.md"
                    )
                elif (
                    error_code == 401
                    or "401" in str(error_msg)
                    or "unauthorized" in str(error_msg).lower()
                ):
                    error_text = (
                        "🔑 <b>Ошибка аутентификации (401)</b>\n\n"
                        "API ключи недействительны или истекли.\n\n"
                        "<b>Решение:</b>\n"
                        "1. Проверьте правильность ключей\n"
                        "2. Создайте новые ключи на dmarket.com\n"
                        "3. Убедитесь, что ключи скопированы полностью\n"
                        "4. Обновите ключи командой /setup"
                    )
                else:
                    error_text = (
                        f"❌ <b>Ошибка при получении баланса:</b>\n\n"
                        f"Код: {error_code}\n"
                        f"Сообщение: {error_msg}\n\n"
                        f"Проверьте настройки API ключей и попробуйте снова."
                    )

                if is_callback:
                    await message.edit_message_text(
                        text=error_text,
                        reply_markup=get_back_to_arbitrage_keyboard(),
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await processing_message.edit_text(
                        text=error_text,
                        parse_mode=ParseMode.HTML,
                    )
                return

            # Extract balance data
            available_balance = balance_result.get("available_balance", 0)
            total_balance = balance_result.get("total_balance", 0)
            has_funds = balance_result.get("has_funds", False)

            # Get account info
            account_info = await api_client.get_account_details()
            username = account_info.get("username", "Неизвестный")

            # Get active offers stats
            offers_info = await api_client.get_active_offers(limit=1)
            total_offers = offers_info.get("total", 0)

            # Check if balance is enough for arbitrage
            min_required_balance = ARBITRAGE_MODES["boost_low"]["min_price"]

            if available_balance < min_required_balance:
                warning_text = (
                    f"⚠️ <b>Предупреждение:</b> Баланс меньше минимального "
                    f"рекомендуемого значения (${min_required_balance:.2f}) "
                    f"для арбитража."
                )
            else:
                warning_text = ""

            # Determine balance status
            if has_funds and available_balance >= 5.0:
                balance_status = "✅ <b>Достаточно для арбитража</b>"
            elif has_funds:
                balance_status = "⚠️ <b>Низкий, но можно использовать</b>"
            else:
                balance_status = "❌ <b>Недостаточно для арбитража</b>"

            # Format response
            response_text = (
                f"📊 <b>Информация о DMarket аккаунте</b>\n\n"
                f"👤 <b>Пользователь:</b> {username}\n"
                f"💰 <b>Доступный баланс:</b> ${available_balance:.2f}\n"
                f"💵 <b>Общий баланс:</b> ${total_balance:.2f}\n"
                f"📦 <b>Активные предложения:</b> {total_offers}\n"
                f"🔋 <b>Статус баланса:</b> {balance_status}\n\n"
            )

            if warning_text:
                response_text += f"{warning_text}\n\n"

            current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            response_text += f"⏱️ <b>Обновлено:</b> {current_time}"

            # Log debug info
            logger.info(
                "DMarket Balance: $%.2f available, $%.2f total. User: %s. Active offers: %d.",
                available_balance,
                total_balance,
                username,
                total_offers,
            )

            # Send result
            if is_callback:
                reply_markup = get_back_to_arbitrage_keyboard()
            else:
                reply_markup = None

            if is_callback:
                await message.edit_message_text(
                    text=response_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await processing_message.edit_text(
                    text=response_text,
                    parse_mode=ParseMode.HTML,
                )

        except APIError as e:
            error_message = await handle_api_error(e)
            error_text = (
                f"❌ <b>Ошибка при проверке баланса:</b>\n\n{error_message}\n\n"
                f"Возможно, проблема с подключением к DMarket API. "
                f"Проверьте настройки API ключей и повторите попытку."
            )

            if is_callback:
                await message.edit_message_text(
                    text=error_text,
                    reply_markup=get_back_to_arbitrage_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
            else:
                await processing_message.edit_text(
                    text=error_text,
                    parse_mode=ParseMode.HTML,
                )

    except Exception as e:
        # Handle generic error
        logger.exception("Error checking balance: %s", e)
        logger.debug(traceback.format_exc())

        error_message = str(e)

        # Check specific errors
        if "404" in error_message or "not found" in error_message.lower():
            error_text = (
                "⚠️ <b>Trading API недоступен</b>\n\n"
                "Ваши API ключи действительны, но не имеют доступа к "
                "приватным функциям DMarket (баланс, инвентарь, торговля)."
                "\n\n"
                "<b>Это НЕ ошибка бота!</b> Это ограничение DMarket.\n\n"
                "📋 <b>Что работает:</b>\n"
                "✅ Поиск предметов на маркете\n"
                "✅ Просмотр цен\n"
                "✅ Анализ рынка\n"
                "✅ Поиск арбитражных возможностей\n\n"
                "🔒 <b>Для доступа к балансу:</b>\n"
                "1. Войдите на dmarket.com\n"
                "2. Настройки → API Keys → Trading API\n"
                "3. Активируйте Trading API\n"
                "4. Создайте новые ключи с полными правами\n"
                "5. Обновите ключи в настройках бота\n\n"
                "📖 Подробнее: см. файл НАСТРОЙКА_API_КЛЮЧЕЙ.md"
            )
        elif "401" in error_message or "unauthorized" in error_message.lower():
            error_text = (
                "🔑 <b>Ошибка аутентификации</b>\n\n"
                "API ключи недействительны или истекли.\n\n"
                "<b>Решение:</b>\n"
                "1. Проверьте правильность ключей в настройках\n"
                "2. Создайте новые ключи на dmarket.com\n"
                "3. Убедитесь, что ключи скопированы полностью\n"
                "4. Обновите ключи и перезапустите бота"
            )
        else:
            error_text = (
                f"❌ <b>Ошибка при проверке баланса:</b>\n\n"
                f"Тип ошибки: {type(e).__name__}\n"
                f"Сообщение: {error_message[:200]}\n\n"
                f"Пожалуйста, попробуйте позже или обратитесь к "
                f"администратору."
            )

        if is_callback:
            await message.edit_message_text(
                text=error_text,
                reply_markup=get_back_to_arbitrage_keyboard(),
                parse_mode=ParseMode.HTML,
            )
        else:
            await processing_message.edit_text(
                text=error_text,
                parse_mode=ParseMode.HTML,
            )
