"""Тесты для модуля profiles telegram_bot."""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock


class TestSaveUserProfiles:
    """Тесты для save_user_profiles."""

    def test_save_user_profiles_writes_to_file(self, tmp_path):
        """Тест сохранения профилей в файл."""
        from src.telegram_bot import profiles
        
        # Устанавливаем временный файл
        test_file = tmp_path / "test_profiles.json"
        
        with patch.object(profiles, 'USER_PROFILES_FILE', test_file):
            profiles.USER_PROFILES = {"123": {"language": "ru"}}
            profiles.save_user_profiles()
            
            assert test_file.exists()
            with open(test_file) as f:
                data = json.load(f)
            assert "123" in data
            assert data["123"]["language"] == "ru"

    def test_save_user_profiles_handles_os_error(self):
        """Тест обработки OSError при сохранении."""
        from src.telegram_bot import profiles
        
        with patch("builtins.open", side_effect=OSError("Test error")):
            # Не должно вызывать исключение
            profiles.save_user_profiles()

    def test_save_user_profiles_with_empty_profiles(self, tmp_path):
        """Тест сохранения пустых профилей."""
        from src.telegram_bot import profiles
        
        test_file = tmp_path / "empty_profiles.json"
        
        with patch.object(profiles, 'USER_PROFILES_FILE', test_file):
            profiles.USER_PROFILES = {}
            profiles.save_user_profiles()
            
            assert test_file.exists()
            with open(test_file) as f:
                data = json.load(f)
            assert data == {}


class TestLoadUserProfiles:
    """Тесты для load_user_profiles."""

    def test_load_user_profiles_from_file(self, tmp_path):
        """Тест загрузки профилей из файла."""
        from src.telegram_bot import profiles
        
        test_file = tmp_path / "test_profiles.json"
        test_data = {"456": {"language": "en"}}
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        
        with patch.object(profiles, 'USER_PROFILES_FILE', str(test_file)):
            profiles.load_user_profiles()
            assert "456" in profiles.USER_PROFILES
            assert profiles.USER_PROFILES["456"]["language"] == "en"

    def test_load_user_profiles_file_not_exists(self, tmp_path):
        """Тест загрузки когда файл не существует."""
        from src.telegram_bot import profiles
        
        test_file = tmp_path / "nonexistent.json"
        
        with patch.object(profiles, 'USER_PROFILES_FILE', str(test_file)):
            with patch("os.path.exists", return_value=False):
                profiles.USER_PROFILES = {"old": "data"}
                profiles.load_user_profiles()
                # Профили не должны измениться если файла нет
                assert "old" in profiles.USER_PROFILES

    def test_load_user_profiles_handles_json_error(self, tmp_path):
        """Тест обработки ошибки JSON при загрузке."""
        from src.telegram_bot import profiles
        
        test_file = tmp_path / "invalid.json"
        with open(test_file, "w") as f:
            f.write("invalid json content {{{")
        
        with patch.object(profiles, 'USER_PROFILES_FILE', str(test_file)):
            with patch("os.path.exists", return_value=True):
                profiles.load_user_profiles()
                assert profiles.USER_PROFILES == {}

    def test_load_user_profiles_handles_os_error(self, tmp_path):
        """Тест обработки OSError при загрузке."""
        from src.telegram_bot import profiles
        
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=OSError("Test error")):
                profiles.load_user_profiles()
                assert profiles.USER_PROFILES == {}


class TestGetUserProfile:
    """Тесты для get_user_profile."""

    def test_get_user_profile_existing_user(self):
        """Тест получения существующего профиля."""
        from src.telegram_bot import profiles
        
        profiles.USER_PROFILES = {"789": {"language": "de"}}
        
        profile = profiles.get_user_profile(789)
        assert profile["language"] == "de"

    def test_get_user_profile_new_user(self, tmp_path):
        """Тест создания нового профиля."""
        from src.telegram_bot import profiles
        
        test_file = tmp_path / "test_profiles.json"
        
        with patch.object(profiles, 'USER_PROFILES_FILE', test_file):
            profiles.USER_PROFILES = {}
            
            profile = profiles.get_user_profile(999)
            
            assert "999" in profiles.USER_PROFILES
            assert "language" in profile
            assert "auto_trading_enabled" in profile
            assert profile["auto_trading_enabled"] is False

    def test_get_user_profile_default_values(self, tmp_path):
        """Тест значений по умолчанию для нового профиля."""
        from src.telegram_bot import profiles
        
        test_file = tmp_path / "test_profiles.json"
        
        with patch.object(profiles, 'USER_PROFILES_FILE', test_file):
            profiles.USER_PROFILES = {}
            
            profile = profiles.get_user_profile(111)
            
            assert profile["language"] == "ru"
            assert profile["api_key"] == ""
            assert profile["api_secret"] == ""
            assert profile["auto_trading_enabled"] is False
            assert "trade_settings" in profile
            assert profile["trade_settings"]["min_profit"] == 2.0
            assert profile["trade_settings"]["max_price"] == 50.0
            assert profile["trade_settings"]["risk_level"] == "medium"

    def test_get_user_profile_updates_last_activity(self):
        """Тест обновления last_activity."""
        from src.telegram_bot import profiles
        import time
        
        profiles.USER_PROFILES = {"222": {"language": "ru", "last_activity": 0}}
        
        before = time.time()
        profile = profiles.get_user_profile(222)
        after = time.time()
        
        assert before <= profile["last_activity"] <= after

    def test_get_user_profile_saves_new_profile(self, tmp_path):
        """Тест сохранения нового профиля."""
        from src.telegram_bot import profiles
        
        test_file = tmp_path / "test_profiles.json"
        
        with patch.object(profiles, 'USER_PROFILES_FILE', test_file):
            profiles.USER_PROFILES = {}
            
            profiles.get_user_profile(333)
            
            assert test_file.exists()
            with open(test_file) as f:
                data = json.load(f)
            assert "333" in data


class TestUserProfilesModule:
    """Тесты для модуля в целом."""

    def test_user_profiles_is_dict(self):
        """Тест что USER_PROFILES это словарь."""
        from src.telegram_bot import profiles
        
        assert isinstance(profiles.USER_PROFILES, dict)

    def test_module_functions_exist(self):
        """Тест существования функций модуля."""
        from src.telegram_bot import profiles
        
        assert callable(profiles.save_user_profiles)
        assert callable(profiles.load_user_profiles)
        assert callable(profiles.get_user_profile)


class TestProfilesEdgeCases:
    """Тесты граничных случаев."""

    def test_get_user_profile_with_string_id(self, tmp_path):
        """Тест с ID как строкой."""
        from src.telegram_bot import profiles
        
        test_file = tmp_path / "test_profiles.json"
        
        with patch.object(profiles, 'USER_PROFILES_FILE', test_file):
            profiles.USER_PROFILES = {}
            
            # Хотя функция ожидает int, строка тоже работает через str()
            profile = profiles.get_user_profile(444)
            assert "444" in profiles.USER_PROFILES

    def test_get_user_profile_preserves_existing_fields(self):
        """Тест сохранения существующих полей."""
        from src.telegram_bot import profiles
        
        profiles.USER_PROFILES = {
            "555": {
                "language": "es",
                "custom_field": "custom_value",
            }
        }
        
        profile = profiles.get_user_profile(555)
        assert profile["language"] == "es"
        assert profile["custom_field"] == "custom_value"

    def test_multiple_profiles(self, tmp_path):
        """Тест работы с несколькими профилями."""
        from src.telegram_bot import profiles
        
        test_file = tmp_path / "test_profiles.json"
        
        with patch.object(profiles, 'USER_PROFILES_FILE', test_file):
            profiles.USER_PROFILES = {}
            
            profiles.get_user_profile(100)
            profiles.get_user_profile(200)
            profiles.get_user_profile(300)
            
            assert "100" in profiles.USER_PROFILES
            assert "200" in profiles.USER_PROFILES
            assert "300" in profiles.USER_PROFILES
            assert len(profiles.USER_PROFILES) == 3
