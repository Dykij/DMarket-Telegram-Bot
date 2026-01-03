"""
Тесты для Steam Database Handler.

Проверяет все функции работы с базой данных:
- Создание таблиц
- Кэширование цен Steam
- Логирование арбитража
- Настройки пользователя
- Blacklist
"""

import os
import pathlib
from datetime import datetime, timedelta

import pytest

from src.utils.steam_db_handler import SteamDatabaseHandler


@pytest.fixture()
def db():
    """Фикстура для тестовой БД."""
    test_db_path = "data/test_steam_cache.db"

    # Удаляем старую тестовую БД если существует
    if os.path.exists(test_db_path):
        pathlib.Path(test_db_path).unlink()

    # Создаем новую
    db = SteamDatabaseHandler(test_db_path)

    yield db

    # Очистка после тестов
    db.close()
    if os.path.exists(test_db_path):
        pathlib.Path(test_db_path).unlink()


class TestSteamCacheOperations:
    """Тесты кэширования Steam цен."""

    def test_update_and_get_steam_price(self, db):
        """Тест сохранения и получения цены."""
        # Arrange
        item_name = "AK-47 | Slate (Field-Tested)"
        price = 2.15
        volume = 145

        # Act
        db.update_steam_price(item_name, price, volume)
        result = db.get_steam_data(item_name)

        # Assert
        assert result is not None
        assert result["price"] == price
        assert result["volume"] == volume
        assert isinstance(result["last_updated"], datetime)

    def test_cache_actualness_check(self, db):
        """Тест проверки актуальности кэша."""
        # Arrange
        item_name = "Test Item"
        db.update_steam_price(item_name, 10.0, 50)
        data = db.get_steam_data(item_name)

        # Act & Assert
        assert db.is_cache_actual(data["last_updated"], hours=6) is True

        # Старые данные
        old_time = datetime.now() - timedelta(hours=7)
        assert db.is_cache_actual(old_time, hours=6) is False

    def test_cache_stats(self, db):
        """Тест статистики кэша."""
        # Arrange
        db.update_steam_price("Item 1", 5.0, 100)
        db.update_steam_price("Item 2", 10.0, 200)
        db.update_steam_price("Item 3", 15.0, 300)

        # Act
        stats = db.get_cache_stats()

        # Assert
        assert stats["total"] == 3
        assert stats["actual"] == 3

    def test_clear_stale_cache(self, db):
        """Тест очистки устаревшего кэша."""
        # Arrange
        db.update_steam_price("Fresh Item", 5.0, 100)

        # Вставляем старую запись напрямую в БД (используем ISO формат)
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        with db.conn:
            db.conn.execute(
                """
                INSERT INTO steam_cache
                (market_hash_name, lowest_price, volume, last_updated)
                VALUES (?, ?, ?, ?)
                """,
                ("Stale Item", 10.0, 50, old_time),
            )

        # Act
        deleted = db.clear_stale_cache(hours=24)

        # Assert
        assert deleted == 1
        assert db.get_steam_data("Fresh Item") is not None
        assert db.get_steam_data("Stale Item") is None


class TestArbitrageLogs:
    """Тесты логирования арбитража."""

    def test_log_opportunity(self, db):
        """Тест записи находки."""
        # Act
        db.log_opportunity(
            name="Test Item",
            dmarket_price=2.0,
            steam_price=2.5,
            profit=15.7,
            volume=100,
            liquidity_status="🔥 Высокая",
        )

        # Assert
        stats = db.get_daily_stats()
        assert stats["count"] == 1
        assert stats["max_profit"] == 15.7

    def test_daily_stats(self, db):
        """Тест статистики за день."""
        # Arrange
        db.log_opportunity("Item 1", 2.0, 2.5, 10.0, 100)
        db.log_opportunity("Item 2", 3.0, 4.0, 20.0, 150)
        db.log_opportunity("Item 3", 1.0, 1.2, 5.0, 50)

        # Act
        stats = db.get_daily_stats()

        # Assert
        assert stats["count"] == 3
        assert stats["avg_profit"] == 11.67  # (10 + 20 + 5) / 3
        assert stats["max_profit"] == 20.0
        assert stats["min_profit"] == 5.0

    def test_top_items_today(self, db):
        """Тест топ-предметов дня."""
        # Arrange
        db.log_opportunity("Item A", 2.0, 3.0, 25.0, 100)
        db.log_opportunity("Item B", 2.0, 2.5, 15.0, 100)
        db.log_opportunity("Item C", 2.0, 2.8, 20.0, 100)

        # Act
        top_items = db.get_top_items_today(limit=2)

        # Assert
        assert len(top_items) == 2
        assert top_items[0]["item_name"] == "Item A"  # 25%
        assert top_items[1]["item_name"] == "Item C"  # 20%


class TestSettings:
    """Тесты настроек пользователя."""

    def test_default_settings(self, db):
        """Тест настроек по умолчанию."""
        # Act
        settings = db.get_settings()

        # Assert
        assert settings["min_profit"] == 10.0
        assert settings["min_volume"] == 50
        assert settings["is_paused"] is False

    def test_update_settings(self, db):
        """Тест обновления настроек."""
        # Act
        db.update_settings(min_profit=15.0, min_volume=100, is_paused=True)
        settings = db.get_settings()

        # Assert
        assert settings["min_profit"] == 15.0
        assert settings["min_volume"] == 100
        assert settings["is_paused"] is True

    def test_partial_update_settings(self, db):
        """Тест частичного обновления настроек."""
        # Act
        db.update_settings(min_profit=20.0)
        settings = db.get_settings()

        # Assert
        assert settings["min_profit"] == 20.0
        assert settings["min_volume"] == 50  # Не изменилось
        assert settings["is_paused"] is False  # Не изменилось


class TestBlacklist:
    """Тесты черного списка."""

    def test_add_to_blacklist(self, db):
        """Тест добавления в blacklist."""
        # Act
        db.add_to_blacklist("Scam Item", reason="Too expensive")

        # Assert
        assert db.is_blacklisted("Scam Item") is True
        assert db.is_blacklisted("Normal Item") is False

    def test_remove_from_blacklist(self, db):
        """Тест удаления из blacklist."""
        # Arrange
        db.add_to_blacklist("Test Item")

        # Act
        removed = db.remove_from_blacklist("Test Item")

        # Assert
        assert removed is True
        assert db.is_blacklisted("Test Item") is False

    def test_get_blacklist(self, db):
        """Тест получения всего blacklist."""
        # Arrange
        db.add_to_blacklist("Item 1", "Reason 1")
        db.add_to_blacklist("Item 2", "Reason 2")

        # Act
        blacklist = db.get_blacklist()

        # Assert
        assert len(blacklist) == 2

    def test_clear_blacklist(self, db):
        """Тест очистки blacklist."""
        # Arrange
        db.add_to_blacklist("Item 1")
        db.add_to_blacklist("Item 2")
        db.add_to_blacklist("Item 3")

        # Act
        cleared = db.clear_blacklist()

        # Assert
        assert cleared == 3
        assert len(db.get_blacklist()) == 0


class TestContextManager:
    """Тест context manager."""

    def test_context_manager(self):
        """Тест использования with statement."""
        test_db_path = "data/test_context.db"

        # Act
        with SteamDatabaseHandler(test_db_path) as db:
            db.update_steam_price("Test", 5.0, 100)
            result = db.get_steam_data("Test")

        # Assert
        assert result is not None

        # Cleanup
        if os.path.exists(test_db_path):
            pathlib.Path(test_db_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
