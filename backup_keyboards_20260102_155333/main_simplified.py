def get_permanent_reply_keyboard() -> ReplyKeyboardMarkup:
    """Создать упрощенную постоянную reply клавиатуру."""
    keyboard = [
        [
            KeyboardButton(text="🔍 Арбитраж"),
            KeyboardButton(text="🎯 Таргеты"),
        ],
        [
            KeyboardButton(text="💰 Баланс"),
            KeyboardButton(text="📈 Статистика"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )
