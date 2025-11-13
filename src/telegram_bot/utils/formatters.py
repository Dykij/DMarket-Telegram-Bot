"""Модуль форматирования данных для сообщений Telegram бота.

Содержит функции для форматирования различных типов данных (предметы маркета,
возможности арбитража, баланс и т.д.) в читаемый текст для отправки в сообщениях Telegram.
"""

import logging
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)

# Максимальная длина сообщения в Telegram
MAX_MESSAGE_LENGTH = 4096


def format_balance(balance_data: dict[str, Any]) -> str:
    """Форматирует данные о балансе в читаемый текст.

    Args:
        balance_data: Словарь с данными о балансе

    Returns:
        str: Отформатированный текст с информацией о балансе

    """
    if balance_data.get("error"):
        return f"❌ *Ошибка при получении баланса*: {balance_data.get('error_message', 'Неизвестная ошибка')}"

    # Получаем значения баланса
    balance = balance_data.get("balance", 0)
    available_balance = balance_data.get("available_balance", balance)
    total_balance = balance_data.get("total_balance", balance)

    # Форматируем сообщение
    message = [
        "💰 *Баланс DMarket*",
        "",
        f"💵 *Доступно*: ${available_balance:.2f} USD",
    ]

    # Добавляем общий баланс, если он отличается от доступного
    if total_balance > available_balance:
        message.append(
            f"🔒 *Заблокировано*: ${total_balance - available_balance:.2f} USD",
        )

    message.append(f"📊 *Всего*: ${total_balance:.2f} USD")

    # Если баланс слишком мал для торговли
    if available_balance < 1.0:
        message.extend(
            [
                "",
                "⚠️ *Внимание*: Доступный баланс меньше $1. Некоторые операции могут быть недоступны.",
            ],
        )

    return "\n".join(message)


def format_market_item(item: dict[str, Any], show_details: bool = True) -> str:
    """Форматирует информацию о предмете маркета.

    Args:
        item: Словарь с данными о предмете
        show_details: Показывать ли детальную информацию

    Returns:
        str: Отформатированный текст с информацией о предмете

    """
    # Базовая информация
    title = item.get("title", "Неизвестный предмет")
    price_cents = item.get("price", {}).get("USD", 0)
    price_usd = price_cents / 100 if price_cents else 0

    message = [f"🏷️ *{title}*", f"💲 Цена: *${price_usd:.2f}*"]

    # Добавляем детали, если нужно
    if show_details:
        # Внешний вид (для CS:GO)
        if "extra" in item and "exteriorName" in item["extra"]:
            message.append(f"🔍 Состояние: _{item['extra']['exteriorName']}_")

        # Float (для CS:GO)
        if "extra" in item and "floatValue" in item["extra"]:
            message.append(f"📊 Float: `{item['extra']['floatValue']}`")

        # Наклейки (для CS:GO)
        if (
            "extra" in item
            and "stickers" in item["extra"]
            and item["extra"]["stickers"]
        ):
            stickers = item["extra"]["stickers"]
            message.append(f"🏵️ Наклейки: {len(stickers)}")

        # Ссылка на предмет
        item_id = item.get("itemId", "")
        if item_id:
            message.append(
                f"🔗 [Открыть на DMarket](https://dmarket.com/ingame-items/item-list/csgo-skins?userOfferId={item_id})",
            )

    return "\n".join(message)


def format_market_items(
    items: list[dict[str, Any]],
    page: int = 0,
    items_per_page: int = 5,
) -> str:
    """Форматирует список предметов с маркета с пагинацией.

    Args:
        items: Список предметов
        page: Номер страницы (начиная с 0)
        items_per_page: Количество предметов на странице

    Returns:
        str: Отформатированный текст со списком предметов

    """
    if not items:
        return "🔍 *Предметы не найдены*"

    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(items))

    page_items = items[start_idx:end_idx]

    message = [f"📋 *Найдено предметов: {len(items)}*"]
    message.append(
        f"📄 Страница {page + 1}/{(len(items) + items_per_page - 1) // items_per_page}",
    )
    message.append("")

    for i, item in enumerate(page_items, start=start_idx + 1):
        item_text = format_market_item(item, show_details=False)
        message.append(f"{i}. {item_text}")
        message.append("")  # Пустая строка между предметами

    return "\n".join(message)


def format_opportunities(
    opportunities: list[dict[str, Any]],
    page: int = 0,
    items_per_page: int = 3,
) -> str:
    """Форматирует список арбитражных возможностей с пагинацией.

    Args:
        opportunities: Список возможностей для арбитража
        page: Номер страницы (начиная с 0)
        items_per_page: Количество возможностей на странице

    Returns:
        str: Отформатированный текст со списком возможностей

    """
    if not opportunities:
        return "🔍 <b>Арбитражные возможности не найдены</b>"

    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(opportunities))

    page_items = opportunities[start_idx:end_idx]

    message = [f"💰 <b>Найдено возможностей: {len(opportunities)}</b>"]
    message.append(
        f"📄 Страница {page + 1}/{(len(opportunities) + items_per_page - 1) // items_per_page}",
    )
    message.append("")

    for i, opportunity in enumerate(page_items, start=start_idx + 1):
        # Извлекаем данные
        item_name = opportunity.get("item_name", "Неизвестный предмет")
        buy_price = opportunity.get("buy_price", 0)
        sell_price = opportunity.get("sell_price", 0)
        profit = opportunity.get("profit", 0)
        profit_percent = opportunity.get("profit_percent", 0)

        # Форматируем
        message.append(f"{i}. <b>{item_name}</b>")
        message.append(
            f"💲 Покупка: <b>${buy_price:.2f}</b> ➡️ Продажа: <b>${sell_price:.2f}</b>",
        )
        message.append(f"📈 Прибыль: <b>${profit:.2f}</b> ({profit_percent:.2f}%)")

        # Добавляем ссылки если есть
        if "buy_link" in opportunity:
            message.append(
                f"🔗 <a href='{opportunity['buy_link']}'>Ссылка на покупку</a>",
            )

        message.append("")  # Пустая строка между возможностями

    # Добавляем время анализа
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message.append(f"🕒 <i>Время анализа: {current_time}</i>")

    return "\n".join(message)


def format_error_message(error: Exception, user_friendly: bool = True) -> str:
    """Форматирует сообщение об ошибке.

    Args:
        error: Объект исключения
        user_friendly: Если True, возвращает сообщение, понятное пользователю

    Returns:
        str: Отформатированное сообщение об ошибке

    """
    if user_friendly:
        return f"❌ *Произошла ошибка*\n\n{error!s}\n\nПожалуйста, попробуйте позже или обратитесь к команде /help для получения справки."

    # Техническое сообщение для отладки
    return f"❌ *Ошибка*: `{type(error).__name__}`\n\n```\n{error!s}\n```"


def format_sales_history(
    sales: list[dict[str, Any]],
    page: int = 0,
    items_per_page: int = 5,
) -> str:
    """Форматирует историю продаж.

    Args:
        sales: Список продаж
        page: Номер страницы (начиная с 0)
        items_per_page: Количество записей на странице

    Returns:
        str: Отформатированный текст с историей продаж

    """
    if not sales:
        return "📊 *История продаж пуста*"

    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(sales))

    page_items = sales[start_idx:end_idx]

    message = [f"📊 *История продаж (последние {len(sales)} записей)*"]
    message.append(
        f"📄 Страница {page + 1}/{(len(sales) + items_per_page - 1) // items_per_page}",
    )
    message.append("")

    for i, sale in enumerate(page_items, start=start_idx + 1):
        # Извлекаем данные
        item_name = sale.get("title", "Неизвестный предмет")
        price_cents = sale.get("price", {}).get("amount", 0)
        price_usd = price_cents / 100 if price_cents else 0

        date_str = sale.get("createdAt", "")
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_formatted = date.strftime("%d.%m.%Y %H:%M")
            except (ValueError, TypeError):
                date_formatted = date_str
        else:
            date_formatted = "Неизвестно"

        # Форматируем
        message.append(f"{i}. *{item_name}*")
        message.append(f"💰 Сумма: *${price_usd:.2f}*")
        message.append(f"🕒 Дата: _{date_formatted}_")
        message.append("")  # Пустая строка между продажами

    return "\n".join(message)


def format_sales_analysis(analysis: dict[str, Any], item_name: str) -> str:
    """Форматирует результаты анализа продаж предмета.

    Args:
        analysis: Словарь с данными анализа продаж
        item_name: Название предмета

    Returns:
        str: Отформатированный текст с анализом продаж

    """
    if not analysis.get("has_data"):
        return (
            f"⚠️ <b>Данные о продажах не найдены</b>\n\n"
            f"Предмет: <code>{item_name}</code>\n\n"
            f"Возможно, предмет редко продается или название указано неверно."
        )

    # Получаем эмодзи для тренда цены
    trend_emoji = {"up": "⬆️ Растет", "down": "⬇️ Падает", "stable": "➡️ Стабилен"}.get(
        analysis.get("price_trend", "stable"),
        "➡️ Стабилен",
    )

    message = [
        f"📊 <b>Анализ продаж:</b> <code>{item_name}</code>\n",
        f"💰 Средняя цена: <b>${analysis.get('avg_price', 0):.2f}</b>",
        f"⬆️ Максимальная цена: <b>${analysis.get('max_price', 0):.2f}</b>",
        f"⬇️ Минимальная цена: <b>${analysis.get('min_price', 0):.2f}</b>",
        f"📈 Тренд цены: {trend_emoji}",
        f"🔄 Продаж за период: <b>{analysis.get('sales_volume', 0)}</b>",
        f"📆 Продаж в день: <b>{analysis.get('sales_per_day', 0):.2f}</b>",
        f"⏱️ Период анализа: <b>{analysis.get('period_days', 0)} дней</b>\n",
    ]

    # Добавляем информацию о последних продажах
    recent_sales = analysis.get("recent_sales", [])
    if recent_sales:
        message.append("🕒 <b>Последние продажи:</b>")
        for sale in recent_sales[:5]:
            date = sale.get("date", "Неизвестно")
            price = sale.get("price", 0)
            currency = sale.get("currency", "USD")
            message.append(f"• {date} - <b>${price:.2f}</b> {currency}")

    return "\n".join(message)


def format_liquidity_analysis(analysis: dict[str, Any], item_name: str) -> str:
    """Форматирует результаты анализа ликвидности предмета.

    Args:
        analysis: Словарь с данными анализа ликвидности
        item_name: Название предмета

    Returns:
        str: Отформатированный текст с анализом ликвидности

    """
    sales_analysis = analysis.get("sales_analysis", {})

    if not sales_analysis.get("has_data"):
        return (
            f"⚠️ <b>Данные о продажах не найдены</b>\n\n"
            f"Предмет: <code>{item_name}</code>\n\n"
            f"Возможно, предмет редко продается или название указано неверно."
        )

    # Получаем эмодзи для категории ликвидности
    liquidity_emoji = {
        "Очень высокая": "💧💧💧💧",
        "Высокая": "💧💧💧",
        "Средняя": "💧💧",
        "Низкая": "💧",
    }.get(analysis.get("liquidity_category", "Низкая"), "💧")

    # Получаем эмодзи для тренда цены
    trend_emoji = {"up": "⬆️ Растет", "down": "⬇️ Падает", "stable": "➡️ Стабилен"}.get(
        sales_analysis.get("price_trend", "stable"),
        "➡️ Стабилен",
    )

    message = [
        f"💧 <b>Анализ ликвидности:</b> <code>{item_name}</code>\n",
        f"{liquidity_emoji} Категория: <b>{analysis.get('liquidity_category', 'Неизвестно')}</b>",
        f"📊 Оценка: <b>{analysis.get('liquidity_score', 0)}/7</b>\n",
        f"📈 Тренд цены: {trend_emoji}",
        f"🔄 Продаж в день: <b>{sales_analysis.get('sales_per_day', 0):.2f}</b>",
        f"📆 Всего продаж: <b>{sales_analysis.get('sales_volume', 0)}</b>",
        f"💰 Средняя цена: <b>${sales_analysis.get('avg_price', 0):.2f}</b>\n",
    ]

    # Добавляем информацию о рынке
    market_data = analysis.get("market_data", {})
    if market_data:
        message.extend(
            [
                f"🛒 Предложений на рынке: <b>{market_data.get('offers_count', 0)}</b>",
                f"⬇️ Минимальная цена: <b>${market_data.get('lowest_price', 0):.2f}</b>",
                f"⬆️ Максимальная цена: <b>${market_data.get('highest_price', 0):.2f}</b>\n",
            ],
        )

    # Добавляем рекомендацию по арбитражу
    liquidity_cat = analysis.get("liquidity_category", "")
    if liquidity_cat in ["Очень высокая", "Высокая"]:
        message.append("✅ <b>Рекомендация:</b> Отлично подходит для арбитража!")
    elif liquidity_cat == "Средняя":
        message.append(
            "⚠️ <b>Рекомендация:</b> Может подойти для арбитража, но с осторожностью.",
        )
    else:
        message.append(
            "❌ <b>Рекомендация:</b> Не рекомендуется для арбитража из-за низкой ликвидности.",
        )

    return "\n".join(message)


def get_trend_emoji(trend: str) -> str:
    """Возвращает эмодзи для тренда цены.

    Args:
        trend: Тренд цены ("up", "down", "stable")

    Returns:
        str: Эмодзи с описанием тренда

    """
    return {"up": "⬆️ Растет", "down": "⬇️ Падает", "stable": "➡️ Стабилен"}.get(
        trend,
        "➡️ Стабилен",
    )


def format_sales_volume_stats(stats: dict[str, Any], game: str) -> str:
    """Форматирует статистику объема продаж.

    Args:
        stats: Словарь со статистикой объема продаж
        game: Код игры

    Returns:
        str: Отформатированный текст со статистикой

    """
    game_display = {
        "csgo": "CS2",
        "dota2": "Dota 2",
        "tf2": "Team Fortress 2",
        "rust": "Rust",
    }.get(game, game.upper())

    items = stats.get("items", [])
    if not items:
        return f"⚠️ <b>Статистика объема продаж не найдена для {game_display}</b>"

    summary = stats.get("summary", {})

    message = [
        f"📊 <b>Статистика объема продаж для {game_display}</b>\n",
        f"🔎 Проанализировано предметов: <b>{stats.get('count', 0)}</b>",
        f"⬆️ Предметов с растущей ценой: <b>{summary.get('up_trend_count', 0)}</b>",
        f"⬇️ Предметов с падающей ценой: <b>{summary.get('down_trend_count', 0)}</b>",
        f"➡️ Предметов со стабильной ценой: <b>{summary.get('stable_trend_count', 0)}</b>\n",
        "📈 <b>Топ-5 предметов по объему продаж:</b>\n",
    ]

    # Добавляем информацию о предметах с наибольшим объемом продаж
    for i, item in enumerate(items[:5], 1):
        item_name = item.get("item_name", "Неизвестный предмет")
        sales_per_day = item.get("sales_per_day", 0)
        avg_price = item.get("avg_price", 0)
        price_trend = item.get("price_trend", "stable")

        message.extend(
            [
                f"{i}. <code>{item_name}</code>",
                f"   🔄 Продаж в день: <b>{sales_per_day:.2f}</b>",
                f"   💰 Средняя цена: <b>${avg_price:.2f}</b>",
                f"   📈 Тренд: {get_trend_emoji(price_trend)}\n",
            ],
        )

    return "\n".join(message)


def format_arbitrage_with_sales(results: dict[str, Any], game: str) -> str:
    """Форматирует арбитражные возможности с учетом истории продаж.

    Args:
        results: Словарь с результатами поиска арбитража
        game: Код игры

    Returns:
        str: Отформатированный текст с результатами

    """
    game_display = {
        "csgo": "CS2",
        "dota2": "Dota 2",
        "tf2": "Team Fortress 2",
        "rust": "Rust",
    }.get(game, game.upper())

    opportunities = results.get("opportunities", [])
    if not opportunities:
        return (
            f"⚠️ <b>Арбитражные возможности не найдены</b>\n\n"
            f"Игра: <b>{game_display}</b>\n\n"
            f"Попробуйте изменить параметры фильтрации или выбрать другую игру."
        )

    filters = results.get("filters", {})
    time_period = filters.get("time_period_days", 7)

    message = [
        f"📊 <b>Арбитражные возможности с учетом продаж для {game_display}</b>\n",
        f"🔎 Найдено предметов: <b>{len(opportunities)}</b>",
        f"📆 Период анализа: <b>{time_period} дней</b>\n",
    ]

    # Добавляем информацию о найденных предметах
    for i, item in enumerate(opportunities[:5], 1):
        item_name = item.get("market_hash_name", "Неизвестный предмет")
        profit = item.get("profit", 0)
        profit_percent = item.get("profit_percent", 0)
        buy_price = item.get("buy_price", 0)
        sell_price = item.get("sell_price", 0)

        sales_analysis = item.get("sales_analysis", {})
        price_trend = sales_analysis.get("price_trend", "stable")
        sales_per_day = sales_analysis.get("sales_per_day", 0)

        message.extend(
            [
                f"🏆 {i}. <code>{item_name}</code>",
                f"💰 Прибыль: <b>${profit:.2f}</b> ({profit_percent:.1f}%)",
                f"🛒 Цена покупки: <b>${buy_price:.2f}</b>",
                f"💵 Цена продажи: <b>${sell_price:.2f}</b>",
                f"📈 Тренд: {get_trend_emoji(price_trend)}",
                f"🔄 Продаж в день: <b>{sales_per_day:.2f}</b>\n",
            ],
        )

    # Если найдено больше 5 предметов, добавляем сообщение о показе только части
    if len(opportunities) > 5:
        message.append(
            f"<i>Показаны 5 из {len(opportunities)} найденных возможностей.</i>",
        )

    return "\n".join(message)


def split_long_message(message: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Разбивает длинное сообщение на части, подходящие для отправки в Telegram.

    Args:
        message: Исходное сообщение
        max_length: Максимальная длина части

    Returns:
        List[str]: Список частей сообщения

    """
    if len(message) <= max_length:
        return [message]

    parts = []
    lines = message.split("\n")
    current_part = ""

    for line in lines:
        # Если добавление этой строки превысит максимальную длину,
        # сохраняем текущую часть и начинаем новую
        if len(current_part) + len(line) + 1 > max_length:
            parts.append(current_part)
            current_part = line + "\n"
        else:
            current_part += line + "\n"

    # Добавляем последнюю часть, если она не пуста
    if current_part:
        parts.append(current_part)

    return parts
