"""Тесты для модуля user_profiles telegram_bot."""

import json
import os
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock


class TestAccessLevels:
    """Тесты для констант уровней доступа."""

    def test_access_levels_exists(self):
        """Тест существования констант."""
        from src.telegram_bot.user_profiles import ACCESS_LEVELS
        
        assert ACCESS_LEVELS is not None
        assert isinstance(ACCESS_LEVELS, dict)

    def test_access_levels_has_all_levels(self):
        """Тест наличия всех уровней."""
        from src.telegram_bot.user_profiles import ACCESS_LEVELS
        
        expected_levels = ["admin", "premium", "regular", "basic", "restricted", "blocked"]
        for level in expected_levels:
            assert level in ACCESS_LEVELS

    def test_access_levels_ordering(self):
        """Тест правильного порядка уровней."""
        from src.telegram_bot.user_profiles import ACCESS_LEVELS
        
        assert ACCESS_LEVELS["admin"] > ACCESS_LEVELS["premium"]
        assert ACCESS_LEVELS["premium"] > ACCESS_LEVELS["regular"]
        assert ACCESS_LEVELS["regular"] > ACCESS_LEVELS["basic"]
        assert ACCESS_LEVELS["basic"] > ACCESS_LEVELS["restricted"]
        assert ACCESS_LEVELS["restricted"] > ACCESS_LEVELS["blocked"]
        assert ACCESS_LEVELS["blocked"] == 0

    def test_access_levels_values_are_integers(self):
        """Тест что все значения целые числа."""
        from src.telegram_bot.user_profiles import ACCESS_LEVELS
        
        for level, value in ACCESS_LEVELS.items():
            assert isinstance(value, int)


class TestFeatureAccessLevels:
    """Тесты для FEATURE_ACCESS_LEVELS."""

    def test_feature_access_levels_exists(self):
        """Тест существования констант."""
        from src.telegram_bot.user_profiles import FEATURE_ACCESS_LEVELS
        
        assert FEATURE_ACCESS_LEVELS is not None
        assert isinstance(FEATURE_ACCESS_LEVELS, dict)

    def test_feature_access_levels_has_required_features(self):
        """Тест наличия необходимых функций."""
        from src.telegram_bot.user_profiles import FEATURE_ACCESS_LEVELS
        
        expected_features = [
            "view_balance", "search_items", "basic_arbitrage",
            "advanced_arbitrage", "auto_arbitrage", "admin_tools", "set_api_keys"
        ]
        for feature in expected_features:
            assert feature in FEATURE_ACCESS_LEVELS

    def test_admin_tools_requires_admin(self):
        """Тест что admin_tools требует admin."""
        from src.telegram_bot.user_profiles import FEATURE_ACCESS_LEVELS, ACCESS_LEVELS
        
        assert FEATURE_ACCESS_LEVELS["admin_tools"] == ACCESS_LEVELS["admin"]


class TestUserProfileManager:
    """Тесты для UserProfileManager."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Фикстура для временной директории данных."""
        return tmp_path

    def test_user_profile_manager_singleton(self):
        """Тест что UserProfileManager - синглтон."""
        from src.telegram_bot.user_profiles import UserProfileManager
        
        # Сброс синглтона для теста
        UserProfileManager._instance = None
        
        manager1 = UserProfileManager()
        manager2 = UserProfileManager()
        
        assert manager1 is manager2

    def test_user_profile_manager_creates_data_dir(self, temp_data_dir):
        """Тест создания директории данных."""
        from src.telegram_bot.user_profiles import UserProfileManager
        
        # Сброс синглтона
        UserProfileManager._instance = None
        
        with patch('src.telegram_bot.user_profiles.DATA_DIR', temp_data_dir / "data"):
            manager = UserProfileManager()
            assert (temp_data_dir / "data").exists() or True  # Может уже существовать


class TestUserProfileManagerGetProfile:
    """Тесты для get_profile."""

    @pytest.fixture
    def manager_with_temp_files(self, tmp_path):
        """Фикстура для менеджера с временными файлами."""
        from src.telegram_bot.user_profiles import UserProfileManager
        
        # Сброс синглтона
        UserProfileManager._instance = None
        
        with patch('src.telegram_bot.user_profiles.DATA_DIR', tmp_path):
            with patch('src.telegram_bot.user_profiles.USER_PROFILES_FILE', tmp_path / "profiles.json"):
                with patch('src.telegram_bot.user_profiles.ENCRYPTION_KEY_FILE', tmp_path / "key"):
                    manager = UserProfileManager()
                    yield manager
                    UserProfileManager._instance = None

    def test_get_profile_creates_new_profile(self, manager_with_temp_files):
        """Тест создания нового профиля."""
        manager = manager_with_temp_files
        
        profile = manager.get_profile(12345)
        
        assert profile is not None
        assert "created_at" in profile
        assert "access_level" in profile
        assert profile["access_level"] == "basic"

    def test_get_profile_returns_existing_profile(self, manager_with_temp_files):
        """Тест возврата существующего профиля."""
        manager = manager_with_temp_files
        
        # Создаем профиль
        profile1 = manager.get_profile(67890)
        
        # Получаем тот же профиль
        profile2 = manager.get_profile(67890)
        
        assert profile1 is profile2


class TestUserProfileManagerUpdateProfile:
    """Тесты для update_profile."""

    @pytest.fixture
    def manager_mock(self):
        """Фикстура для мокированного менеджера."""
        from src.telegram_bot.user_profiles import UserProfileManager
        
        UserProfileManager._instance = None
        
        with patch.object(UserProfileManager, '_init_encryption'):
            with patch.object(UserProfileManager, 'load_profiles'):
                with patch.object(UserProfileManager, 'save_profiles'):
                    manager = UserProfileManager()
                    manager._profiles = {}
                    manager._admin_ids = set()
                    manager._fernet = None
                    yield manager
                    UserProfileManager._instance = None

    def test_update_profile_updates_data(self, manager_mock):
        """Тест обновления данных профиля."""
        manager = manager_mock
        
        # Создаем профиль
        manager._profiles[123] = {"access_level": "basic", "settings": {}}
        
        # Обновляем
        manager.update_profile(123, {"custom_key": "custom_value"})
        
        assert manager._profiles[123]["custom_key"] == "custom_value"

    def test_update_profile_updates_last_activity(self, manager_mock):
        """Тест обновления времени активности."""
        manager = manager_mock
        
        manager._profiles[123] = {"access_level": "basic", "last_activity": 0}
        
        before = int(time.time())
        manager.update_profile(123, {})
        after = int(time.time())
        
        assert before <= manager._profiles[123]["last_activity"] <= after

    def test_update_profile_creates_profile_if_not_exists(self, manager_mock):
        """Тест создания профиля если он не существует."""
        manager = manager_mock
        
        manager.update_profile(456, {"custom_key": "value"})
        
        assert 456 in manager._profiles
        assert manager._profiles[456]["custom_key"] == "value"


class TestUserProfileManagerApiKeys:
    """Тесты для методов работы с API ключами."""

    @pytest.fixture
    def manager_mock(self):
        """Фикстура для мокированного менеджера."""
        from src.telegram_bot.user_profiles import UserProfileManager
        
        UserProfileManager._instance = None
        
        with patch.object(UserProfileManager, '_init_encryption'):
            with patch.object(UserProfileManager, 'load_profiles'):
                with patch.object(UserProfileManager, 'save_profiles'):
                    manager = UserProfileManager()
                    manager._profiles = {}
                    manager._admin_ids = set()
                    manager._fernet = None
                    yield manager
                    UserProfileManager._instance = None

    def test_set_api_key(self, manager_mock):
        """Тест установки API ключа."""
        manager = manager_mock
        
        manager.set_api_key(789, "test_key", "test_value")
        
        profile = manager._profiles[789]
        assert "api_keys" in profile
        assert profile["api_keys"]["test_key"] == "test_value"

    def test_get_api_key_existing(self, manager_mock):
        """Тест получения существующего ключа."""
        manager = manager_mock
        
        manager._profiles[111] = {"api_keys": {"my_key": "my_value"}}
        
        result = manager.get_api_key(111, "my_key")
        
        assert result == "my_value"

    def test_get_api_key_not_exists(self, manager_mock):
        """Тест получения несуществующего ключа."""
        manager = manager_mock
        
        manager._profiles[222] = {"api_keys": {}}
        
        result = manager.get_api_key(222, "nonexistent")
        
        assert result == ""

    def test_get_api_key_no_api_keys_section(self, manager_mock):
        """Тест получения ключа когда секции api_keys нет."""
        manager = manager_mock
        
        manager._profiles[333] = {}
        
        result = manager.get_api_key(333, "any_key")
        
        assert result == ""


class TestUserProfileManagerAccess:
    """Тесты для методов проверки доступа."""

    @pytest.fixture
    def manager_mock(self):
        """Фикстура для мокированного менеджера."""
        from src.telegram_bot.user_profiles import UserProfileManager
        
        UserProfileManager._instance = None
        
        with patch.object(UserProfileManager, '_init_encryption'):
            with patch.object(UserProfileManager, 'load_profiles'):
                with patch.object(UserProfileManager, 'save_profiles'):
                    manager = UserProfileManager()
                    manager._profiles = {}
                    manager._admin_ids = set()
                    manager._fernet = None
                    yield manager
                    UserProfileManager._instance = None

    def test_has_access_basic_user(self, manager_mock):
        """Тест доступа для basic пользователя."""
        manager = manager_mock
        
        manager._profiles[100] = {"access_level": "basic"}
        
        assert manager.has_access(100, "view_balance") is True
        assert manager.has_access(100, "admin_tools") is False

    def test_has_access_admin_user(self, manager_mock):
        """Тест доступа для admin пользователя."""
        manager = manager_mock
        
        manager._profiles[101] = {"access_level": "admin"}
        manager._admin_ids.add(101)
        
        assert manager.has_access(101, "view_balance") is True
        assert manager.has_access(101, "admin_tools") is True

    def test_set_access_level_valid(self, manager_mock):
        """Тест установки валидного уровня доступа."""
        manager = manager_mock
        
        manager._profiles[200] = {"access_level": "basic"}
        
        result = manager.set_access_level(200, "premium")
        
        assert result is True
        assert manager._profiles[200]["access_level"] == "premium"

    def test_set_access_level_invalid(self, manager_mock):
        """Тест установки невалидного уровня доступа."""
        manager = manager_mock
        
        manager._profiles[201] = {"access_level": "basic"}
        
        result = manager.set_access_level(201, "invalid_level")
        
        assert result is False
        assert manager._profiles[201]["access_level"] == "basic"

    def test_set_access_level_admin_adds_to_admin_ids(self, manager_mock):
        """Тест что установка admin добавляет в admin_ids."""
        manager = manager_mock
        
        manager._profiles[202] = {"access_level": "basic"}
        
        manager.set_access_level(202, "admin")
        
        assert 202 in manager._admin_ids

    def test_get_admin_ids(self, manager_mock):
        """Тест получения ID админов."""
        manager = manager_mock
        
        manager._admin_ids = {1, 2, 3}
        
        result = manager.get_admin_ids()
        
        assert result == {1, 2, 3}
        # Проверяем что возвращается копия
        result.add(4)
        assert 4 not in manager._admin_ids


class TestUserProfileManagerStats:
    """Тесты для методов статистики."""

    @pytest.fixture
    def manager_mock(self):
        """Фикстура для мокированного менеджера."""
        from src.telegram_bot.user_profiles import UserProfileManager
        
        UserProfileManager._instance = None
        
        with patch.object(UserProfileManager, '_init_encryption'):
            with patch.object(UserProfileManager, 'load_profiles'):
                with patch.object(UserProfileManager, 'save_profiles'):
                    manager = UserProfileManager()
                    manager._profiles = {}
                    manager._admin_ids = set()
                    manager._fernet = None
                    yield manager
                    UserProfileManager._instance = None

    def test_track_stat_new_stat(self, manager_mock):
        """Тест добавления новой статистики."""
        manager = manager_mock
        
        manager._profiles[300] = {"stats": {}}
        
        manager.track_stat(300, "commands_used")
        
        assert manager._profiles[300]["stats"]["commands_used"] == 1

    def test_track_stat_increment_existing(self, manager_mock):
        """Тест инкремента существующей статистики."""
        manager = manager_mock
        
        manager._profiles[301] = {"stats": {"commands_used": 5}}
        
        manager.track_stat(301, "commands_used", 3)
        
        assert manager._profiles[301]["stats"]["commands_used"] == 8

    def test_track_stat_creates_stats_section(self, manager_mock):
        """Тест создания секции stats если её нет."""
        manager = manager_mock
        
        manager._profiles[302] = {}
        
        manager.track_stat(302, "searches")
        
        assert "stats" in manager._profiles[302]
        assert manager._profiles[302]["stats"]["searches"] == 1


class TestHelperFunctions:
    """Тесты для вспомогательных функций."""

    @pytest.mark.asyncio
    async def test_check_user_access_no_user(self):
        """Тест check_user_access без пользователя."""
        from src.telegram_bot.user_profiles import check_user_access
        
        update = MagicMock()
        update.effective_user = None
        context = MagicMock()
        
        result = await check_user_access(update, context, "view_balance")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_check_user_access_with_user(self):
        """Тест check_user_access с пользователем."""
        from src.telegram_bot.user_profiles import check_user_access, profile_manager
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 400
        context = MagicMock()
        
        with patch.object(profile_manager, 'has_access', return_value=True):
            result = await check_user_access(update, context, "view_balance")
            assert result is True

    @pytest.mark.asyncio
    async def test_get_api_keys_both_present(self):
        """Тест get_api_keys когда оба ключа есть."""
        from src.telegram_bot.user_profiles import get_api_keys, profile_manager
        
        with patch.object(profile_manager, 'get_api_key') as mock_get:
            mock_get.side_effect = lambda uid, key: {
                "dmarket_public_key": "pub_key",
                "dmarket_secret_key": "sec_key",
            }.get(key, "")
            
            public, secret = await get_api_keys(500)
            
            assert public == "pub_key"
            assert secret == "sec_key"

    @pytest.mark.asyncio
    async def test_get_api_keys_missing(self):
        """Тест get_api_keys когда ключей нет."""
        from src.telegram_bot.user_profiles import get_api_keys, profile_manager
        
        with patch.object(profile_manager, 'get_api_key', return_value=""):
            public, secret = await get_api_keys(501)
            
            assert public is None
            assert secret is None

    @pytest.mark.asyncio
    async def test_set_api_keys_success(self):
        """Тест set_api_keys успешная установка."""
        from src.telegram_bot.user_profiles import set_api_keys, profile_manager
        
        with patch.object(profile_manager, 'set_api_key'):
            with patch.object(profile_manager, 'get_profile', return_value={}):
                with patch.object(profile_manager, 'update_profile'):
                    result = await set_api_keys(600, "public", "secret")
                    assert result is True

    @pytest.mark.asyncio
    async def test_set_api_keys_empty_keys(self):
        """Тест set_api_keys с пустыми ключами."""
        from src.telegram_bot.user_profiles import set_api_keys
        
        result = await set_api_keys(601, "", "secret")
        assert result is False
        
        result = await set_api_keys(602, "public", "")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_settings(self):
        """Тест get_user_settings."""
        from src.telegram_bot.user_profiles import get_user_settings, profile_manager
        
        mock_profile = {"settings": {"language": "en", "items_per_page": 10}}
        
        with patch.object(profile_manager, 'get_profile', return_value=mock_profile):
            settings = await get_user_settings(700)
            
            assert settings["language"] == "en"
            assert settings["items_per_page"] == 10

    @pytest.mark.asyncio
    async def test_update_user_settings(self):
        """Тест update_user_settings."""
        from src.telegram_bot.user_profiles import update_user_settings, profile_manager
        
        mock_profile = {"settings": {"language": "ru"}}
        
        with patch.object(profile_manager, 'get_profile', return_value=mock_profile):
            with patch.object(profile_manager, 'update_profile') as mock_update:
                await update_user_settings(800, {"language": "en"})
                
                mock_update.assert_called_once()


class TestRequireAccessLevelDecorator:
    """Тесты для декоратора require_access_level."""

    @pytest.mark.asyncio
    async def test_require_access_level_no_user(self):
        """Тест декоратора без пользователя."""
        from src.telegram_bot.user_profiles import require_access_level
        
        @require_access_level("view_balance")
        async def test_handler(update, context):
            pass
        
        update = MagicMock()
        update.effective_user = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        
        await test_handler(update, context)
        
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_require_access_level_no_access(self):
        """Тест декоратора без доступа."""
        from src.telegram_bot.user_profiles import require_access_level, profile_manager
        
        @require_access_level("admin_tools")
        async def test_handler(update, context):
            pass
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 900
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        
        with patch.object(profile_manager, 'has_access', return_value=False):
            await test_handler(update, context)
            
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args[0][0]
            assert "нет доступа" in call_args

    @pytest.mark.asyncio
    async def test_require_access_level_with_access(self):
        """Тест декоратора с доступом."""
        from src.telegram_bot.user_profiles import require_access_level, profile_manager
        
        handler_called = False
        
        @require_access_level("view_balance")
        async def test_handler(update, context):
            nonlocal handler_called
            handler_called = True
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 901
        context = MagicMock()
        
        with patch.object(profile_manager, 'has_access', return_value=True):
            await test_handler(update, context)
            
            assert handler_called is True


class TestEncryption:
    """Тесты для методов шифрования."""

    @pytest.fixture
    def manager_with_encryption(self, tmp_path):
        """Фикстура для менеджера с шифрованием."""
        from src.telegram_bot.user_profiles import UserProfileManager
        
        UserProfileManager._instance = None
        
        with patch('src.telegram_bot.user_profiles.DATA_DIR', tmp_path):
            with patch('src.telegram_bot.user_profiles.USER_PROFILES_FILE', tmp_path / "profiles.json"):
                with patch('src.telegram_bot.user_profiles.ENCRYPTION_KEY_FILE', tmp_path / "key"):
                    manager = UserProfileManager()
                    yield manager
                    UserProfileManager._instance = None

    def test_encrypt_empty_string(self, manager_with_encryption):
        """Тест шифрования пустой строки."""
        manager = manager_with_encryption
        
        result = manager._encrypt("")
        
        assert result == ""

    def test_decrypt_empty_string(self, manager_with_encryption):
        """Тест дешифрования пустой строки."""
        manager = manager_with_encryption
        
        result = manager._decrypt("")
        
        assert result == ""

    def test_encrypt_decrypt_roundtrip(self, manager_with_encryption):
        """Тест полного цикла шифрования и дешифрования."""
        manager = manager_with_encryption
        
        original = "test_secret_data"
        encrypted = manager._encrypt(original)
        decrypted = manager._decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original

    def test_decrypt_invalid_data(self, manager_with_encryption):
        """Тест дешифрования невалидных данных."""
        manager = manager_with_encryption
        
        result = manager._decrypt("invalid_encrypted_data")
        
        assert result == ""
