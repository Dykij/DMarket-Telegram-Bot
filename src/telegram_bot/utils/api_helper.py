import logging
import os

from telegram.ext import ContextTypes

from src.dmarket.dmarket_api import DMarketAPI


logger = logging.getLogger(__name__)


def create_dmarket_api_client(
    context: ContextTypes.DEFAULT_TYPE | None = None,
) -> DMarketAPI:
    """Создает и возвращает экземпляр клиента DMarket API.

    Пытается получить ключи из:
    1. context.bot_data (если передан context)
    2. Переменных окружения

    Args:
        context: Контекст Telegram бота (опционально)

    Returns:
        Экземпляр DMarketAPI

    """
    public_key = None
    secret_key = None

    # 1. Пытаемся получить из bot_data
    if context and hasattr(context, "bot_data"):
        public_key = context.bot_data.get("DMARKET_PUBLIC_KEY")
        secret_key = context.bot_data.get("DMARKET_SECRET_KEY")

    # 2. Если нет в bot_data, берем из переменных окружения
    if not public_key:
        public_key = os.getenv("DMARKET_PUBLIC_KEY")

    if not secret_key:
        secret_key = os.getenv("DMARKET_SECRET_KEY")

    # Логируем (без секретов)
    if public_key:
        logger.debug(
            "Используется Public Key: %s...%s",
            public_key[:4],
            public_key[-4:],
        )
    else:
        logger.warning("DMARKET_PUBLIC_KEY не найден!")

    if not secret_key:
        logger.warning("DMARKET_SECRET_KEY не найден!")

    return DMarketAPI(public_key=public_key or "", secret_key=secret_key or "")
