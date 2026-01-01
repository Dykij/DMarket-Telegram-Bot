"""Рефакторированный модуль для обработки фильтров игровых предметов.

Предоставляет обработчики для настройки и применения фильтров для разных игр:
- CS2/CSGO: качество, редкость, внешний вид, диапазоны float и цены
- Dota 2: герой, редкость, слот, качество
- Team Fortress 2: класс, качество, тип, эффект
- Rust: категория, тип, редкость

Рефакторинг Фазы 2:
- Применены early returns
- Разделение длинных функций на меньшие
- Вынесены константы и вспомогательные функции
"""

import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.dmarket.game_filters import FilterFactory


logger = logging.getLogger(__name__)

# Константы для фильтров

CS2_CATEGORIES = [
    "Pistol",
    "SMG",
    "Rifle",
    "Sniper Rifle",
    "Shotgun",
    "Machinegun",
    "Knife",
    "Gloves",
    "Sticker",
    "Agent",
    "Case",
]

CS2_RARITIES = [
    "Consumer Grade",
    "Industrial Grade",
    "Mil-Spec Grade",
    "Restricted",
    "Classified",
    "Covert",
    "Contraband",
]

CS2_EXTERIORS = [
    "Factory New",
    "Minimal Wear",
    "Field-Tested",
    "Well-Worn",
    "Battle-Scarred",
]

DOTA2_HEROES = [
    "Axe",
    "Anti-Mage",
    "Crystal Maiden",
    "Drow Ranger",
    "Juggernaut",
    "Pudge",
    "Lina",
    "Lion",
    "Sven",
    "Tiny",
    "Invoker",
    "Shadow Fiend",
]

DOTA2_RARITIES = [
    "Common",
    "Uncommon",
    "Rare",
    "Mythical",
    "Legendary",
    "Immortal",
    "Arcana",
]

DOTA2_SLOTS = [
    "Weapon",
    "Head",
    "Back",
    "Arms",
    "Shoulder",
    "Belt",
    "Misc",
    "Taunt",
    "Courier",
    "Ward",
]

TF2_CLASSES = [
    "Scout",
    "Soldier",
    "Pyro",
    "Demoman",
    "Heavy",
    "Engineer",
    "Medic",
    "Sniper",
    "Spy",
    "All Classes",
]

TF2_QUALITIES = [
    "Normal",
    "Unique",
    "Vintage",
    "Genuine",
    "Strange",
    "Unusual",
    "Haunted",
    "Collectors",
]

TF2_TYPES = [
    "Hat",
    "Weapon",
    "Cosmetic",
    "Action",
    "Tool",
    "Taunt",
    "Crate",
    "Key",
]

RUST_CATEGORIES = ["Weapon", "Clothing", "Tool", "Construction", "Misc"]

RUST_TYPES = [
    "Assault Rifle",
    "Pistol",
    "Shotgun",
    "SMG",
    "Jacket",
    "Pants",
    "Helmet",
    "Boots",
    "Gloves",
    "Door",
    "Box",
]

RUST_RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]

DEFAULT_FILTERS = {
    "csgo": {
        "min_price": 1.0,
        "max_price": 1000.0,
        "float_min": 0.0,
        "float_max": 1.0,
        "category": None,
        "rarity": None,
        "exterior": None,
        "stattrak": False,
        "souvenir": False,
    },
    "dota2": {
        "min_price": 1.0,
        "max_price": 1000.0,
        "hero": None,
        "rarity": None,
        "slot": None,
        "quality": None,
        "tradable": True,
    },
    "tf2": {
        "min_price": 1.0,
        "max_price": 1000.0,
        "class": None,
        "quality": None,
        "type": None,
        "effect": None,
        "killstreak": None,
        "australium": False,
    },
    "rust": {
        "min_price": 1.0,
        "max_price": 1000.0,
        "category": None,
        "type": None,
        "rarity": None,
    },
}

GAME_NAMES = {
    "csgo": "CS2 (CS:GO)",
    "dota2": "Dota 2",
    "tf2": "Team Fortress 2",
    "rust": "Rust",
}


# Вспомогательные функции для работы с фильтрами


def get_current_filters(
    context: ContextTypes.DEFAULT_TYPE, game: str
) -> dict[str, Any]:
    """Получает текущие фильтры для игры из контекста пользователя."""
    user_data = context.user_data
    if not user_data:
        return DEFAULT_FILTERS.get(game, {}).copy()

    filters = user_data.get("filters", {})
    game_filters = filters.get(game, {})

    if not game_filters:
        return DEFAULT_FILTERS.get(game, {}).copy()

    return dict(game_filters)


def update_filters(
    context: ContextTypes.DEFAULT_TYPE,
    game: str,
    new_filters: dict[str, Any],
) -> None:
    """Обновляет фильтры для игры в контексте пользователя."""
    user_data = context.user_data
    if not user_data:
        user_data = {}
        context.user_data = user_data

    filters = user_data.get("filters", {})
    if not filters:
        filters = {}
        user_data["filters"] = filters

    filters[game] = new_filters


def get_filter_description(game: str, filters: dict[str, Any]) -> str:
    """Получает человекочитаемое описание фильтров."""
    game_filter = FilterFactory.get_filter(game)
    return game_filter.get_filter_description(filters)


def build_api_params_for_game(game: str, filters: dict[str, Any]) -> dict[str, Any]:
    """Строит параметры для DMarket API на основе фильтров."""
    game_filter = FilterFactory.get_filter(game)
    return game_filter.build_api_params(filters)


# Функции для создания клавиатур


def _create_common_filter_buttons(game: str) -> list[list[InlineKeyboardButton]]:
    """Создает общие кнопки фильтров для всех игр."""
    return [
        [InlineKeyboardButton("💰 Диапазон цен", callback_data=f"price_range:{game}")],
    ]


def _create_csgo_filter_buttons(game: str) -> list[list[InlineKeyboardButton]]:
    """Создает кнопки фильтров для CS:GO."""
    return [
        [
            InlineKeyboardButton(
                "🔢 Диапазон Float", callback_data=f"float_range:{game}"
            )
        ],
        [InlineKeyboardButton("🔫 Категория", callback_data=f"set_category:{game}")],
        [InlineKeyboardButton("⭐ Редкость", callback_data=f"set_rarity:{game}")],
        [InlineKeyboardButton("🧩 Внешний вид", callback_data=f"set_exterior:{game}")],
        [InlineKeyboardButton("🔢 StatTrak™", callback_data=f"filter:stattrak:{game}")],
        [InlineKeyboardButton("🏆 Сувенир", callback_data=f"filter:souvenir:{game}")],
    ]


def _create_dota2_filter_buttons(game: str) -> list[list[InlineKeyboardButton]]:
    """Создает кнопки фильтров для Dota 2."""
    return [
        [InlineKeyboardButton("🦸 Герой", callback_data=f"set_hero:{game}")],
        [InlineKeyboardButton("⭐ Редкость", callback_data=f"set_rarity:{game}")],
        [InlineKeyboardButton("🧩 Слот", callback_data=f"set_slot:{game}")],
        [InlineKeyboardButton("🏆 Качество", callback_data=f"filter:quality:{game}")],
        [
            InlineKeyboardButton(
                "🔄 Обмениваемость", callback_data=f"filter:tradable:{game}"
            )
        ],
    ]


def _create_tf2_filter_buttons(game: str) -> list[list[InlineKeyboardButton]]:
    """Создает кнопки фильтров для TF2."""
    return [
        [InlineKeyboardButton("👤 Класс", callback_data=f"set_class:{game}")],
        [InlineKeyboardButton("⭐ Качество", callback_data=f"filter:quality:{game}")],
        [InlineKeyboardButton("🔫 Тип", callback_data=f"set_type:{game}")],
        [InlineKeyboardButton("✨ Эффект", callback_data=f"filter:effect:{game}")],
        [
            InlineKeyboardButton(
                "🔢 Killstreak", callback_data=f"filter:killstreak:{game}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔶 Australium", callback_data=f"filter:australium:{game}"
            )
        ],
    ]


def _create_rust_filter_buttons(game: str) -> list[list[InlineKeyboardButton]]:
    """Создает кнопки фильтров для Rust."""
    return [
        [InlineKeyboardButton("🔫 Категория", callback_data=f"set_category:{game}")],
        [InlineKeyboardButton("🧩 Тип", callback_data=f"set_type:{game}")],
        [InlineKeyboardButton("⭐ Редкость", callback_data=f"set_rarity:{game}")],
    ]


def _create_reset_and_back_buttons(game: str) -> list[list[InlineKeyboardButton]]:
    """Создает кнопки сброса и возврата."""
    return [
        [
            InlineKeyboardButton(
                "🔄 Сбросить фильтры", callback_data=f"filter:reset:{game}"
            )
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_filters:main")],
    ]


def get_game_filter_keyboard(game: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора фильтров игры."""
    keyboard = _create_common_filter_buttons(game)

    if game == "csgo":
        keyboard.extend(_create_csgo_filter_buttons(game))
    elif game == "dota2":
        keyboard.extend(_create_dota2_filter_buttons(game))
    elif game == "tf2":
        keyboard.extend(_create_tf2_filter_buttons(game))
    elif game == "rust":
        keyboard.extend(_create_rust_filter_buttons(game))

    keyboard.extend(_create_reset_and_back_buttons(game))
    return InlineKeyboardMarkup(keyboard)


def _create_button_rows(
    items: list[str],
    callback_prefix: str,
    game: str,
    items_per_row: int = 2,
) -> list[list[InlineKeyboardButton]]:
    """Создает ряды кнопок из списка элементов."""
    keyboard = []
    row = []

    for i, item in enumerate(items):
        row.append(
            InlineKeyboardButton(item, callback_data=f"{callback_prefix}:{item}:{game}")
        )

        if len(row) == items_per_row or i == len(items) - 1:
            keyboard.append(row.copy())
            row = []

    return keyboard


# Обработчики команд


async def handle_game_filters(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработчик команды /filters - показывает выбор игры для фильтрации."""
    if not update.message:
        return

    keyboard = [
        [
            InlineKeyboardButton("🎮 CS2", callback_data="select_game_filter:csgo"),
            InlineKeyboardButton("🎮 Dota 2", callback_data="select_game_filter:dota2"),
        ],
        [
            InlineKeyboardButton("🎮 TF2", callback_data="select_game_filter:tf2"),
            InlineKeyboardButton("🎮 Rust", callback_data="select_game_filter:rust"),
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="arbitrage")],
    ]

    await update.message.reply_text(
        "Выберите игру для настройки фильтров:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_select_game_filter_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик выбора игры для фильтрации."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")
    game = data[1] if len(data) > 1 else "csgo"

    filters = get_current_filters(context, game)
    description = get_filter_description(game, filters)
    reply_markup = get_game_filter_keyboard(game)

    game_name = GAME_NAMES.get(game, game)
    message_text = f"🎮 Настройка фильтров для {game_name}:\n\n"

    if description:
        message_text += f"📋 Текущие фильтры:\n{description}\n"
    else:
        message_text += "📋 Текущие фильтры: не настроены\n"

    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )


async def handle_price_range_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик выбора диапазона цен."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")
    game = data[1] if len(data) > 1 else "csgo"
    filters = get_current_filters(context, game)

    keyboard = [
        [
            InlineKeyboardButton(
                "$1-10", callback_data=f"filter:price_range:1:10:{game}"
            ),
            InlineKeyboardButton(
                "$10-50", callback_data=f"filter:price_range:10:50:{game}"
            ),
        ],
        [
            InlineKeyboardButton(
                "$50-100", callback_data=f"filter:price_range:50:100:{game}"
            ),
            InlineKeyboardButton(
                "$100-500", callback_data=f"filter:price_range:100:500:{game}"
            ),
        ],
        [
            InlineKeyboardButton(
                "$500+", callback_data=f"filter:price_range:500:10000:{game}"
            ),
            InlineKeyboardButton(
                "Сбросить", callback_data=f"filter:price_range:reset:{game}"
            ),
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"select_game_filter:{game}")],
    ]

    min_price = filters.get("min_price", DEFAULT_FILTERS[game]["min_price"])
    max_price = filters.get("max_price", DEFAULT_FILTERS[game]["max_price"])

    await query.edit_message_text(
        text=f"💰 Настройка диапазона цен:\n\nТекущий диапазон: ${min_price:.2f} - ${max_price:.2f}\n\nВыберите новый диапазон цен:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_float_range_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик выбора диапазона Float (для CS2)."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")
    game = data[1] if len(data) > 1 else "csgo"

    if game != "csgo":
        await query.edit_message_text(
            text="Диапазон Float доступен только для CS2.",
            reply_markup=get_game_filter_keyboard(game),
        )
        return

    filters = get_current_filters(context, game)

    keyboard = [
        [
            InlineKeyboardButton(
                "Factory New (0.00-0.07)",
                callback_data=f"filter:float_range:0.00:0.07:{game}",
            ),
            InlineKeyboardButton(
                "Minimal Wear (0.07-0.15)",
                callback_data=f"filter:float_range:0.07:0.15:{game}",
            ),
        ],
        [
            InlineKeyboardButton(
                "Field-Tested (0.15-0.38)",
                callback_data=f"filter:float_range:0.15:0.38:{game}",
            ),
            InlineKeyboardButton(
                "Well-Worn (0.38-0.45)",
                callback_data=f"filter:float_range:0.38:0.45:{game}",
            ),
        ],
        [
            InlineKeyboardButton(
                "Battle-Scarred (0.45-1.00)",
                callback_data=f"filter:float_range:0.45:1.00:{game}",
            ),
            InlineKeyboardButton(
                "Сбросить", callback_data=f"filter:float_range:reset:{game}"
            ),
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"select_game_filter:{game}")],
    ]

    float_min = filters.get("float_min", DEFAULT_FILTERS[game]["float_min"])
    float_max = filters.get("float_max", DEFAULT_FILTERS[game]["float_max"])

    await query.edit_message_text(
        text=f"🔢 Настройка диапазона Float:\n\nТекущий диапазон: {float_min:.2f} - {float_max:.2f}\n\nВыберите новый диапазон Float:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_set_category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик выбора категории (для CS2 и Rust)."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")
    game = data[1] if len(data) > 1 else "csgo"
    filters = get_current_filters(context, game)

    categories = CS2_CATEGORIES if game == "csgo" else RUST_CATEGORIES
    keyboard = _create_button_rows(categories, "filter:category", game)

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "Сбросить", callback_data=f"filter:category:reset:{game}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Назад", callback_data=f"select_game_filter:{game}"
                )
            ],
        ]
    )

    current_category = filters.get("category", "Не выбрано")

    await query.edit_message_text(
        text=f"🔫 Выбор категории:\n\nТекущая категория: {current_category}\n\nВыберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_set_rarity_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик выбора редкости."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")
    game = data[1] if len(data) > 1 else "csgo"
    filters = get_current_filters(context, game)

    rarities = {
        "csgo": CS2_RARITIES,
        "dota2": DOTA2_RARITIES,
        "rust": RUST_RARITIES,
    }.get(game, [])

    keyboard = _create_button_rows(rarities, "filter:rarity", game)
    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "Сбросить", callback_data=f"filter:rarity:reset:{game}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Назад", callback_data=f"select_game_filter:{game}"
                )
            ],
        ]
    )

    current_rarity = filters.get("rarity", "Не выбрано")

    await query.edit_message_text(
        text=f"⭐ Выбор редкости:\n\nТекущая редкость: {current_rarity}\n\nВыберите редкость:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_set_exterior_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик выбора внешнего вида (для CS2)."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")
    game = data[1] if len(data) > 1 else "csgo"

    if game != "csgo":
        await query.edit_message_text(
            text="Выбор внешнего вида доступен только для CS2.",
            reply_markup=get_game_filter_keyboard(game),
        )
        return

    filters = get_current_filters(context, game)
    keyboard = [
        [InlineKeyboardButton(ext, callback_data=f"filter:exterior:{ext}:{game}")]
        for ext in CS2_EXTERIORS
    ]

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "Сбросить", callback_data=f"filter:exterior:reset:{game}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Назад", callback_data=f"select_game_filter:{game}"
                )
            ],
        ]
    )

    current_exterior = filters.get("exterior", "Не выбрано")

    await query.edit_message_text(
        text=f"🧩 Выбор внешнего вида:\n\nТекущий внешний вид: {current_exterior}\n\nВыберите внешний вид:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_set_hero_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик выбора героя (для Dota 2)."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")
    game = data[1] if len(data) > 1 else "dota2"

    if game != "dota2":
        await query.edit_message_text(
            text="Выбор героя доступен только для Dota 2.",
            reply_markup=get_game_filter_keyboard(game),
        )
        return

    filters = get_current_filters(context, game)
    keyboard = _create_button_rows(DOTA2_HEROES, "filter:hero", game)

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "Сбросить", callback_data=f"filter:hero:reset:{game}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Назад", callback_data=f"select_game_filter:{game}"
                )
            ],
        ]
    )

    current_hero = filters.get("hero", "Не выбрано")

    await query.edit_message_text(
        text=f"🦸 Выбор героя:\n\nТекущий герой: {current_hero}\n\nВыберите героя:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_set_class_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик выбора класса (для TF2)."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")
    game = data[1] if len(data) > 1 else "tf2"

    if game != "tf2":
        await query.edit_message_text(
            text="Выбор класса доступен только для Team Fortress 2.",
            reply_markup=get_game_filter_keyboard(game),
        )
        return

    filters = get_current_filters(context, game)
    keyboard = [
        [InlineKeyboardButton(cls, callback_data=f"filter:class:{cls}:{game}")]
        for cls in TF2_CLASSES
    ]

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "Сбросить", callback_data=f"filter:class:reset:{game}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Назад", callback_data=f"select_game_filter:{game}"
                )
            ],
        ]
    )

    current_class = filters.get("class", "Не выбрано")

    await query.edit_message_text(
        text=f"👤 Выбор класса:\n\nТекущий класс: {current_class}\n\nВыберите класс:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# Обработка изменения фильтров


def _handle_price_range_filter(filters: dict[str, Any], data: list[str]) -> str:
    """Обрабатывает изменение фильтра диапазона цен."""
    filter_value = data[2]
    game = data[4] if len(data) > 4 else "csgo"

    if filter_value == "reset":
        filters.pop("min_price", None)
        filters.pop("max_price", None)
    else:
        filters["min_price"] = float(filter_value)
        filters["max_price"] = float(data[3])

    return game


def _handle_float_range_filter(filters: dict[str, Any], data: list[str]) -> str:
    """Обрабатывает изменение фильтра диапазона Float."""
    filter_value = data[2]
    game = data[4] if len(data) > 4 else "csgo"

    if filter_value == "reset":
        filters.pop("float_min", None)
        filters.pop("float_max", None)
    else:
        filters["float_min"] = float(filter_value)
        filters["float_max"] = float(data[3])

    return game


def _handle_simple_filter(
    filters: dict[str, Any],
    filter_type: str,
    filter_value: str,
) -> None:
    """Обрабатывает изменение простого фильтра."""
    if filter_value == "reset":
        filters.pop(filter_type, None)
    else:
        filters[filter_type] = filter_value


def _handle_boolean_filter(filters: dict[str, Any], filter_type: str) -> None:
    """Обрабатывает изменение булева фильтра."""
    filters[filter_type] = not filters.get(filter_type)


async def handle_filter_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик для всех фильтров."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")

    if len(data) < 3:
        await query.edit_message_text(
            text="Неверный формат данных фильтра.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data="arbitrage")]]
            ),
        )
        return

    filter_type = data[1]
    filter_value = data[2]
    game = data[3] if len(data) > 3 else "csgo"

    filters = get_current_filters(context, game)

    if filter_type == "price_range":
        game = _handle_price_range_filter(filters, data)
    elif filter_type == "float_range":
        game = _handle_float_range_filter(filters, data)
    elif filter_type in {"category", "rarity", "exterior", "hero", "class"}:
        _handle_simple_filter(filters, filter_type, filter_value)
    elif filter_type in {"stattrak", "souvenir", "tradable", "australium"}:
        _handle_boolean_filter(filters, filter_type)
    elif filter_type == "reset":
        filters = DEFAULT_FILTERS.get(game, {}).copy()

    update_filters(context, game, filters)
    await handle_select_game_filter_callback(update, context)


async def handle_back_to_filters_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик кнопки 'Назад' в фильтрах."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()

    data = query.data.split(":")

    if len(data) < 2:
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад к арбитражу", callback_data="arbitrage")]
        ]
        await query.edit_message_text(
            text="Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    back_type = data[1]

    if back_type == "main":
        await handle_game_filters(update, context)
    else:
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад к арбитражу", callback_data="arbitrage")]
        ]
        await query.edit_message_text(
            text="Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
