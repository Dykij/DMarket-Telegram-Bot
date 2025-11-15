"""Тесты для проверки работы SQLite fallback.

Проверяет, что приложение корректно работает с SQLite
в качестве альтернативы PostgreSQL для разработки и тестирования.
"""

import os
import tempfile

import pytest
from sqlalchemy import inspect, text

from src.utils.database import (
    AnalyticsEvent,
    Base,
    CommandLog,
    DatabaseManager,
    MarketData,
    PriceAlert,
    User,
    UserSettings,
)


@pytest.fixture()
def sqlite_db_path():
    """Создает временный файл для SQLite БД."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture()
def sqlite_url(sqlite_db_path):
    """Возвращает SQLite connection URL."""
    return f"sqlite:///{sqlite_db_path}"


@pytest.fixture()
def db_manager(sqlite_url):
    """Создает DatabaseManager с SQLite."""
    manager = DatabaseManager(sqlite_url, echo=False)
    return manager


class TestSQLiteFallback:
    """Тесты для проверки SQLite fallback."""

    def test_sqlite_connection(self, db_manager):
        """Тест подключения к SQLite базе данных."""
        engine = db_manager.engine
        assert engine is not None

        # Проверяем, что это SQLite
        assert "sqlite" in str(engine.url)

        # Проверяем подключение
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_create_all_tables(self, db_manager):
        """Тест создания всех таблиц в SQLite."""
        engine = db_manager.engine

        # Создаем все таблицы
        Base.metadata.create_all(engine)

        # Проверяем, что таблицы созданы
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "users",
            "user_settings",
            "market_data",
            "price_alerts",
            "command_log",
            "events",
        ]

        for table in expected_tables:
            assert table in tables, f"Таблица {table} не создана"

    def test_user_model_sqlite(self, db_manager):
        """Тест работы с моделью User в SQLite."""
        engine = db_manager.engine
        Base.metadata.create_all(engine)

        session = db_manager.session_maker()

        try:
            # Создаем пользователя
            user = User(
                telegram_id=123456789,
                username="test_user",
                first_name="Test",
                last_name="User",
                language_code="ru",
            )

            session.add(user)
            session.commit()

            # Проверяем, что пользователь создан
            assert user.id is not None

            # Получаем пользователя из БД
            db_user = session.query(User).filter_by(telegram_id=123456789).first()

            assert db_user is not None
            assert db_user.username == "test_user"
            assert db_user.first_name == "Test"
            assert db_user.telegram_id == 123456789

        finally:
            session.close()

    def test_uuid_type_sqlite(self, db_manager):
        """Тест работы UUID типа в SQLite."""
        engine = db_manager.engine
        Base.metadata.create_all(engine)

        session = db_manager.session_maker()

        try:
            # Создаем пользователя (UUID генерируется автоматически)
            user = User(telegram_id=987654321, username="uuid_test")

            session.add(user)
            session.commit()

            user_id = user.id

            # Проверяем, что UUID сохранен как строка в SQLite
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id FROM users WHERE telegram_id = :tid"),
                    {"tid": 987654321},
                )
                row = result.fetchone()
                assert row is not None

                # В SQLite UUID хранится как строка
                stored_id = row[0]
                assert isinstance(stored_id, str)
                assert len(stored_id) == 36  # UUID формат

            # Проверяем, что при чтении UUID преобразуется обратно
            db_user = session.query(User).filter_by(telegram_id=987654321).first()
            assert db_user.id == user_id

        finally:
            session.close()

    def test_market_data_model_sqlite(self, db_manager):
        """Тест работы с моделью MarketData в SQLite."""
        engine = db_manager.engine
        Base.metadata.create_all(engine)

        session = db_manager.session_maker()

        try:
            # Создаем запись market data
            market_data = MarketData(
                item_id="item_123",
                game="csgo",
                item_name="AK-47 | Redline (Field-Tested)",
                price_usd=12.50,
                price_change_24h=0.5,
                volume_24h=150,
            )

            session.add(market_data)
            session.commit()

            # Проверяем сохранение
            db_data = session.query(MarketData).filter_by(item_id="item_123").first()

            assert db_data is not None
            assert db_data.item_name == "AK-47 | Redline (Field-Tested)"
            assert db_data.price_usd == 12.50
            assert db_data.game == "csgo"

        finally:
            session.close()

    def test_json_column_sqlite(self, db_manager):
        """Тест работы JSON колонок в SQLite."""
        engine = db_manager.engine
        Base.metadata.create_all(engine)

        session = db_manager.session_maker()

        try:
            # Создаем событие с JSON данными
            event = AnalyticsEvent(
                event_type="test_event",
                event_data={
                    "action": "scan",
                    "game": "csgo",
                    "items_found": 10,
                    "metadata": {"filter": "redline", "min_price": 5.0},
                },
            )

            session.add(event)
            session.commit()

            # Получаем событие из БД
            db_event = (
                session.query(AnalyticsEvent).filter_by(event_type="test_event").first()
            )

            assert db_event is not None
            assert db_event.event_data["action"] == "scan"
            assert db_event.event_data["game"] == "csgo"
            assert db_event.event_data["items_found"] == 10
            assert db_event.event_data["metadata"]["filter"] == "redline"

        finally:
            session.close()

    def test_indexes_created_sqlite(self, db_manager):
        """Тест создания индексов в SQLite."""
        engine = db_manager.engine
        Base.metadata.create_all(engine)

        inspector = inspect(engine)

        # Проверяем индексы на таблице users
        user_indexes = inspector.get_indexes("users")
        index_columns = [idx["column_names"] for idx in user_indexes]

        # Должен быть индекс на telegram_id
        assert any("telegram_id" in cols for cols in index_columns)

        # Проверяем индексы на таблице command_log
        log_indexes = inspector.get_indexes("command_log")
        log_index_columns = [idx["column_names"] for idx in log_indexes]

        # Должны быть индексы
        assert any("user_id" in cols for cols in log_index_columns)

    def test_foreign_key_constraints_sqlite(self, db_manager):
        """Тест работы с внешними ключами в SQLite (если есть)."""
        engine = db_manager.engine
        Base.metadata.create_all(engine)

        # SQLite по умолчанию не включает FK constraints
        # Проверяем, что таблицы связаны логически

        session = db_manager.session_maker()

        try:
            # Создаем пользователя
            user = User(telegram_id=111222333, username="fk_test")
            session.add(user)
            session.commit()

            # Создаем настройки для пользователя
            settings = UserSettings(user_id=user.id, language="ru", timezone="UTC")

            session.add(settings)
            session.commit()

            # Проверяем связь
            db_settings = session.query(UserSettings).filter_by(user_id=user.id).first()

            assert db_settings is not None
            assert db_settings.language == "ru"

        finally:
            session.close()

    def test_concurrent_writes_sqlite(self, db_manager):
        """Тест конкурентных записей в SQLite."""
        engine = db_manager.engine
        Base.metadata.create_all(engine)

        # SQLite имеет ограничения на конкурентные записи
        # Проверяем базовую функциональность

        session1 = db_manager.session_maker()
        session2 = db_manager.session_maker()

        try:
            # Записываем из разных сессий
            user1 = User(telegram_id=777888999, username="concurrent1")
            user2 = User(telegram_id=999888777, username="concurrent2")

            session1.add(user1)
            session2.add(user2)

            session1.commit()
            session2.commit()

            # Проверяем, что оба пользователя сохранены
            assert (
                session1.query(User).filter_by(telegram_id=777888999).first()
                is not None
            )
            assert (
                session2.query(User).filter_by(telegram_id=999888777).first()
                is not None
            )

        finally:
            session1.close()
            session2.close()


class TestDatabaseManagerSQLite:
    """Тесты для DatabaseManager с SQLite."""

    @pytest.mark.asyncio()
    async def test_init_database_sqlite(self, db_manager):
        """Тест инициализации БД через DatabaseManager."""
        await db_manager.init_database()

        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()

        assert len(tables) > 0
        assert "users" in tables

    @pytest.mark.asyncio()
    async def test_get_or_create_user_sqlite(self, db_manager):
        """Тест get_or_create_user с SQLite."""
        await db_manager.init_database()

        # Создаем пользователя
        user1 = await db_manager.get_or_create_user(
            telegram_id=123123123, username="get_or_create_test"
        )

        assert user1 is not None
        assert user1.telegram_id == 123123123

        # Получаем существующего пользователя
        user2 = await db_manager.get_or_create_user(telegram_id=123123123)

        assert user2.id == user1.id
        assert user2.username == "get_or_create_test"

    @pytest.mark.asyncio()
    async def test_log_command_sqlite(self, db_manager):
        """Тест логирования команд в SQLite."""
        await db_manager.init_database()

        # Создаем пользователя
        user = await db_manager.get_or_create_user(telegram_id=456456456)

        # Логируем команду
        await db_manager.log_command(
            user_id=user.id,
            command="/balance",
            parameters={"game": "csgo"},
            success=True,
            execution_time_ms=150,
        )

        # Проверяем лог
        session = db_manager.session_maker()
        try:
            log = session.query(CommandLog).filter_by(user_id=user.id).first()

            assert log is not None
            assert log.command == "/balance"
            assert log.parameters["game"] == "csgo"
            assert log.success is True
            assert log.execution_time_ms == 150

        finally:
            session.close()

    @pytest.mark.asyncio()
    async def test_save_market_data_sqlite(self, db_manager):
        """Тест сохранения market data в SQLite."""
        await db_manager.init_database()

        # Сохраняем данные
        await db_manager.save_market_data(
            item_id="test_item_789",
            game="dota2",
            item_name="Dragonclaw Hook",
            price_usd=500.0,
            volume_24h=50,
        )

        # Проверяем сохранение
        session = db_manager.session_maker()
        try:
            data = session.query(MarketData).filter_by(item_id="test_item_789").first()

            assert data is not None
            assert data.game == "dota2"
            assert data.price_usd == 500.0

        finally:
            session.close()


class TestSQLiteVsPostgreSQL:
    """Тесты сравнения поведения SQLite и PostgreSQL."""

    def test_url_detection(self):
        """Тест определения типа БД по URL."""
        sqlite_url = "sqlite:///test.db"
        postgres_url = "postgresql://user:pass@localhost/db"

        assert "sqlite" in sqlite_url
        assert "postgresql" in postgres_url

        # DatabaseManager должен работать с обоими
        sqlite_manager = DatabaseManager(sqlite_url)
        postgres_manager = DatabaseManager(postgres_url)

        assert "sqlite" in str(sqlite_manager.database_url)
        assert "postgresql" in str(postgres_manager.database_url)

    def test_sqlite_limitations_documented(self):
        """Документирует ограничения SQLite по сравнению с PostgreSQL.

        Ограничения SQLite:
        - Нет настоящего Boolean типа (использует INTEGER 0/1)
        - Ограниченная поддержка конкурентных записей
        - Нет некоторых расширенных типов данных
        - UUID хранится как TEXT
        - Ограниченная поддержка ALTER TABLE

        Преимущества SQLite:
        - Не требует отдельного сервера
        - Идеален для разработки и тестирования
        - Файл базы данных легко копировать/переносить
        - Отличная производительность для небольших нагрузок
        """
        # Этот тест просто документирует различия
        assert True


@pytest.mark.integration()
class TestSQLiteIntegration:
    """Интеграционные тесты для SQLite."""

    def test_full_user_workflow_sqlite(self, db_manager):
        """Тест полного workflow пользователя в SQLite."""
        db_manager.init_database()

        # 1. Создание пользователя
        user = db_manager.get_or_create_user(
            telegram_id=555666777, username="integration_test", first_name="Integration"
        )

        assert user is not None

        # 2. Логирование команды
        db_manager.log_command(
            user_id=user.id, command="/start", success=True, execution_time_ms=50
        )

        # 3. Сохранение market data
        db_manager.save_market_data(
            item_id="integration_item",
            game="csgo",
            item_name="Test Item",
            price_usd=10.0,
        )

        # 4. Создание алерта
        session = db_manager.session_maker()
        try:
            alert = PriceAlert(
                user_id=user.id,
                item_id="integration_item",
                target_price=9.0,
                condition="below",
            )
            session.add(alert)
            session.commit()

            # 5. Проверка всех данных
            db_user = session.query(User).filter_by(id=user.id).first()
            assert db_user.username == "integration_test"

            db_log = session.query(CommandLog).filter_by(user_id=user.id).first()
            assert db_log.command == "/start"

            db_market = (
                session.query(MarketData).filter_by(item_id="integration_item").first()
            )
            assert db_market.price_usd == 10.0

            db_alert = session.query(PriceAlert).filter_by(user_id=user.id).first()
            assert db_alert.target_price == 9.0

        finally:
            session.close()
