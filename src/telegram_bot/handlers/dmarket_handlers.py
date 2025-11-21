"""Обработчики команд для работы с DMarket.

Этот модуль содержит команды для взаимодействия с API DMarket.
"""

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.dmarket.dmarket_api import DMarketAPI


logger = logging.getLogger(__name__)


class DMarketHandler:
    """Обработчик команд для работы с DMarket."""

    def __init__(self, public_key: str, secret_key: str, api_url: str) -> None:
        """Инициализирует обработчик команд DMarket.

        Args:
            public_key: Публичный ключ для доступа к API.
            secret_key: Секретный ключ для доступа к API.
            api_url: URL API DMarket.

        """
        self.public_key = public_key
        self.secret_key = secret_key
        self.api_url = api_url
        self.api = None

        if public_key and secret_key:
            self.initialize_api()

    def initialize_api(self) -> None:
        """Инициализирует API клиент."""
        try:
            self.api = DMarketAPI(
                public_key=self.public_key,
                secret_key=self.secret_key,
                api_url=self.api_url,
            )
            logger.info("DMarket API клиент инициализирован успешно")
        except Exception as e:
            logger.error(
                f"Не удалось инициализировать DMarket API клиент: {e}",
                exc_info=True,
            )

    async def status_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Проверяет статус настройки API ключей DMarket."""
        logger.info(
            f"Пользователь {update.effective_user.id} использовал команду /dmarket",
        )

        if update.message:
            if self.public_key and self.secret_key:
                await update.message.reply_text(
                    f"API ключи DMarket настроены.\nAPI endpoint: {self.api_url}",
                )
            else:
                await update.message.reply_text(
                    "API ключи DMarket не настроены.\nПожалуйста, добавьте их в .env файл.",
                )

    async def balance_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Проверяет баланс на DMarket."""
        logger.info(
            f"Пользователь {update.effective_user.id} использовал команду /balance",
        )

        if not self.api:
            if update.message:
                await update.message.reply_text(
                    "API DMarket не инициализирован.\nПожалуйста, проверьте настройки API ключей.",
                )
            return

        try:
            balance_data = await self.api.get_balance()

            if not balance_data:
                await update.message.reply_text(
                    "Не удалось получить информацию о балансе.\nПожалуйста, попробуйте позже.",
                )
                return

            if balance_data.get("error"):
                error_msg = balance_data.get(
                    "error_message",
                    "Неизвестная ошибка",
                )
                if update.message:
                    await update.message.reply_text(
                        f"Ошибка при получении баланса: {error_msg}",
                    )
                return

            # Получаем значения в центах (строки)
            usd_cents = int(balance_data.get("usd", 0))
            usd_available_cents = int(balance_data.get("usdAvailableToWithdraw", 0))

            # Конвертируем в доллары
            total_balance = usd_cents / 100.0
            available_balance = usd_available_cents / 100.0
            blocked_balance = total_balance - available_balance

            if update.message:
                await update.message.reply_text(
                    f"Баланс на DMarket:\n"
                    f"Общий баланс: ${total_balance:.2f}\n"
                    f"Заблокировано: ${blocked_balance:.2f}\n"
                    f"Доступно: ${available_balance:.2f}",
                )
        except Exception as e:
            logger.error("Ошибка при получении баланса: %s", e, exc_info=True)
            if update.message:
                await update.message.reply_text(
                    "Не удалось получить информацию о балансе.\nПожалуйста, попробуйте позже.",
                )


def register_dmarket_handlers(
    app: Application,
    public_key: str,
    secret_key: str,
    api_url: str,
) -> None:
    """Регистрирует обработчики команд DMarket в приложении Telegram.

    Args:
        app: Экземпляр приложения Telegram.
        public_key: Публичный ключ для доступа к API DMarket.
        secret_key: Секретный ключ для доступа к API DMarket.
        api_url: URL API DMarket.

    """
    logger.info("Регистрация обработчиков команд DMarket")

    handler = DMarketHandler(public_key, secret_key, api_url)

    app.add_handler(CommandHandler("dmarket", handler.status_command))
    app.add_handler(CommandHandler("balance", handler.balance_command))
