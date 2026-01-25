"""
Debug Suite для DMarket Telegram Bot.

Этот скрипт выполняет полный набор проверок перед деплоем:
1. Подключение к DMarket API + проверка баланса
2. Подключение к базе данных
3. Проверка/создание пользователя в БД
4. Тест получения цены и расчёта профита на реальных данных
5. Симуляция ордера в DRY-RUN режиме
6. Отправка тестового уведомления в Telegram

Запускайте этот скрипт перед каждым деплоем для проверки корректности настроек.
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
import sys

from sqlalchemy import text


# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.config import Config
from src.utils.database import DatabaseManager
from src.utils.logging_utils import get_logger


logger = get_logger(__name__)


class DebugSuite:
    """Debug Suite для полной проверки системы."""

    def __init__(self):
        """Инициализация Debug Suite."""
        self.config = Config.load()
        self.passed_tests = 0
        self.failed_tests = 0
        self.total_tests = 6

    async def run_all_tests(self) -> bool:
        """Запустить все тесты.

        Returns:
            True если все тесты прошли, False если хотя бы один провалился
        """
        print("\n" + "=" * 70)
        print("🧪 DMARKET BOT DEBUG SUITE")
        print("=" * 70)
        print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Режим: {'DRY-RUN ✅' if self.config.dry_run else 'LIVE ⚠️'}")
        print("=" * 70 + "\n")

        # Выполняем тесты последовательно
        await self._test_1_dmarket_connection()
        await self._test_2_database_connection()
        await self._test_3_user_management()
        await self._test_4_price_and_profit_calculation()
        await self._test_5_order_simulation()
        await self._test_6_telegram_notification()

        # Итоговый отчёт
        print("\n" + "=" * 70)
        print("📊 ИТОГОВЫЙ ОТЧЁТ")
        print("=" * 70)
        print(f"✅ Успешных тестов: {self.passed_tests}/{self.total_tests}")
        print(f"❌ Провалившихся тестов: {self.failed_tests}/{self.total_tests}")

        if self.failed_tests == 0:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            print("✅ Бот готов к запуску.")
        else:
            print(f"\n⚠️  {self.failed_tests} ТЕСТ(ОВ) НЕ ПРОШЛИ!")
            print("❌ Исправьте ошибки перед запуском бота.")

        print("=" * 70 + "\n")

        return self.failed_tests == 0

    async def _test_1_dmarket_connection(self) -> None:
        """Тест 1: Подключение к DMarket API + проверка баланса."""
        print("[1/6] 🌐 Подключение к DMarket API...")

        try:
            api = DMarketAPI(
                public_key=self.config.dmarket.public_key,
                secret_key=self.config.dmarket.secret_key,
            )

            # Получение баланса
            balance_data = await api.get_balance()

            # error=False означает, что ошибки НЕ было
            if balance_data.get("error", False) is True:
                raise ValueError(f"Ошибка получения баланса: {balance_data}")

            # Парсинг баланса (новый формат API - баланс напрямую в USD)
            usd = float(balance_data.get("balance", 0))
            usd_available = float(balance_data.get("available_balance", 0))

            print("   ✅ Подключение успешно")
            print(f"   💰 Баланс: ${usd:.2f}")
            print(f"   💵 Доступно для вывода: ${usd_available:.2f}")

            if usd < 1.0:
                print(f"   ⚠️  Предупреждение: Баланс менее $1.00 (текущий: ${usd:.2f})")

            self.passed_tests += 1

        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
            logger.exception("Test 1 DMarket API failed")
            self.failed_tests += 1

    async def _test_2_database_connection(self) -> None:
        """Тест 2: Подключение к базе данных."""
        print("\n[2/6] 🗄️  Подключение к базе данных...")

        try:
            db = DatabaseManager(self.config.database.url)
            await db.init_database()

            # Проверка подключения через простой запрос
            session = db.get_async_session()
            async with session.begin():
                result = await session.execute(text("SELECT 1"))
                result.scalar()

            print("   ✅ Подключение к БД успешно")
            print(f"   📊 URL: {self.config.database.url.split('@')[-1]}")  # Скрываем пароль

            self.passed_tests += 1

        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
            logger.exception("Test 2 failed")
            self.failed_tests += 1

    async def _test_3_user_management(self) -> None:
        """Тест 3: Проверка/создание пользователя в БД."""
        print("\n[3/6] 👤 Проверка работы с пользователями...")

        try:
            db = DatabaseManager(self.config.database.url)
            await db.init_database()

            # Тестовый пользователь
            test_telegram_id = 999999999  # Тестовый ID
            test_username = "debug_suite_test_user"

            # Получение или создание пользователя
            user = await db.get_or_create_user(
                telegram_id=test_telegram_id,
                username=test_username,
                first_name="Debug",
                last_name="Suite",
            )

            print("   ✅ Пользователь получен/создан")
            print(f"   🆔 User ID: {user.id}")
            print(f"   📱 Telegram ID: {user.telegram_id}")
            print(f"   👤 Username: @{user.username}")

            self.passed_tests += 1

        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
            logger.exception("Test 3 failed")
            self.failed_tests += 1

    async def _test_4_price_and_profit_calculation(self) -> None:
        """Тест 4: Получение цены и расчёт профита на реальных данных."""
        print("\n[4/6] 📊 Тест получения цены и расчёта профита...")

        try:
            api = DMarketAPI(
                public_key=self.config.dmarket.public_key,
                secret_key=self.config.dmarket.secret_key,
            )

            # Получение реальных предметов с рынка (CS2)
            items = await api.get_market_items(
                game="a8db",  # CS2/CSGO
                limit=5,
                price_from=100,  # От $1
                price_to=1000,  # До $10
            )

            if not items or "objects" not in items:
                raise ValueError("Не удалось получить предметы с рынка")

            # Берём первый предмет для теста
            item = items["objects"][0]
            item_title = item["title"]
            buy_price_cents = int(item["price"]["USD"])
            buy_price_usd = buy_price_cents / 100

            # Расчёт профита (предполагаем продажу на 10% выше)
            sell_price_usd = buy_price_usd * 1.10
            commission = 0.07  # 7% комиссия DMarket
            profit_usd = (sell_price_usd * (1 - commission)) - buy_price_usd
            profit_percent = (profit_usd / buy_price_usd) * 100

            print("   ✅ Предметы получены")
            print(f"   🎮 Тестовый предмет: {item_title}")
            print(f"   💵 Цена покупки: ${buy_price_usd:.2f}")
            print(f"   💰 Цена продажи: ${sell_price_usd:.2f}")
            print(f"   📈 Расчётный профит: ${profit_usd:.2f} ({profit_percent:.1f}%)")

            self.passed_tests += 1

        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
            logger.exception("Test 4 failed")
            self.failed_tests += 1

    async def _test_5_order_simulation(self) -> None:
        """Тест 5: Симуляция ордера в DRY-RUN режиме."""
        print("\n[5/6] 🛒 Симуляция ордера (DRY-RUN)...")

        try:
            if not self.config.dry_run:
                print("   ⚠️  ПРЕДУПРЕЖДЕНИЕ: DRY_RUN=False!")
                print("   ⚠️  Этот тест будет симулировать ордер без реальной покупки")

            api = DMarketAPI(
                public_key=self.config.dmarket.public_key,
                secret_key=self.config.dmarket.secret_key,
            )

            # Получаем предмет для симуляции
            items = await api.get_market_items(
                game="a8db",
                limit=1,
                price_from=100,
                price_to=500,
            )

            if not items or "objects" not in items or not items["objects"]:
                raise ValueError("Не удалось получить предметы для симуляции")

            item = items["objects"][0]
            item_id = item.get("itemId")
            item_title = item["title"]
            price_cents = int(item["price"]["USD"])
            price_usd = price_cents / 100

            # Симуляция покупки (логируем намерение)
            logger.info(
                "BUY_INTENT",
                extra={
                    "item": item_title,
                    "price_usd": price_usd,
                    "item_id": item_id,
                    "source": "debug_suite",
                    "dry_run": True,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

            print("   ✅ Симуляция успешна")
            print(f"   🎮 Предмет: {item_title}")
            print(f"   💵 Цена: ${price_usd:.2f}")
            print("   🔵 Режим: DRY-RUN (реальная покупка НЕ произведена)")
            print("   📝 INTENT залогирован в logs/")

            self.passed_tests += 1

        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
            logger.exception("Test 5 failed")
            self.failed_tests += 1

    async def _test_6_telegram_notification(self) -> None:
        """Тест 6: Отправка тестового уведомления в Telegram."""
        print("\n[6/6] 📱 Отправка тестового уведомления в Telegram...")

        try:
            from telegram import Bot

            bot = Bot(token=self.config.bot.token)

            # Получаем информацию о боте
            bot_info = await bot.get_me()

            print("   ✅ Подключение к Telegram успешно")
            print(f"   🤖 Бот: @{bot_info.username}")
            print(f"   📝 Имя: {bot_info.first_name}")

            # Попытка отправить тестовое сообщение (если есть chat_id в конфиге)
            if hasattr(self.config, "test_chat_id") and self.config.test_chat_id:
                message = (
                    "🧪 <b>Debug Suite Test</b>\n\n"
                    f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    "✅ Все системы работают нормально\n"
                    f"🔧 Режим: {'DRY-RUN' if self.config.dry_run else 'LIVE'}"
                )

                await bot.send_message(
                    chat_id=self.config.test_chat_id,
                    text=message,
                    parse_mode="HTML",
                )

                print(f"   📨 Тестовое сообщение отправлено в чат {self.config.test_chat_id}")
            else:
                print("   ℹ️  test_chat_id не настроен в конфиге, пропускаем отправку сообщения")

            self.passed_tests += 1

        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
            logger.exception("Test 6 Telegram notification failed")
            self.failed_tests += 1


async def main() -> None:
    """Главная функция."""
    suite = DebugSuite()

    try:
        success = await suite.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Debug Suite прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error(
            "debug_suite_critical_error",
            exc_info=True,
            extra={"error_message": str(e)},
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
