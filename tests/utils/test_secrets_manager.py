"""Tests for secrets_manager module.

This module tests the SecretsManager class for secure
handling of API keys and sensitive data.
"""

import pytest
from unittest.mock import MagicMock, patch
import os

from src.utils.secrets_manager import SecretsManager


class TestSecretsManager:
    """Tests for SecretsManager class."""

    @pytest.fixture
    def manager(self):
        """Create SecretsManager instance."""
        return SecretsManager()

    def test_init(self, manager):
        """Test initialization."""
        assert manager is not None

    def test_init_with_key_file(self):
        """Test initialization with key file."""
        manager = SecretsManager(key_file="/tmp/test_key")
        assert manager.key_file == "/tmp/test_key"

    def test_get_secret_from_env(self, manager):
        """Test getting secret from environment."""
        with patch.dict(os.environ, {"TEST_SECRET": "secret_value"}):
            value = manager.get_secret("TEST_SECRET")
            assert value == "secret_value"

    def test_get_secret_default(self, manager):
        """Test getting secret with default value."""
        value = manager.get_secret("NONEXISTENT_SECRET", default="default_value")
        assert value == "default_value"

    def test_get_secret_not_found(self, manager):
        """Test getting nonexistent secret without default."""
        value = manager.get_secret("NONEXISTENT_SECRET_12345")
        assert value is None

    def test_set_secret(self, manager):
        """Test setting secret."""
        manager.set_secret("TEST_KEY", "test_value")

        value = manager.get_secret("TEST_KEY")
        assert value == "test_value"

    def test_delete_secret(self, manager):
        """Test deleting secret."""
        manager.set_secret("DELETE_KEY", "value")
        manager.delete_secret("DELETE_KEY")

        value = manager.get_secret("DELETE_KEY")
        assert value is None

    def test_encrypt_value(self, manager):
        """Test encrypting value."""
        encrypted = manager.encrypt("sensitive_data")

        assert encrypted != "sensitive_data"
        assert len(encrypted) > 0

    def test_decrypt_value(self, manager):
        """Test decrypting value."""
        original = "sensitive_data"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_decrypt_roundtrip(self, manager):
        """Test encrypt-decrypt roundtrip."""
        values = [
            "simple_string",
            "string with spaces",
            "unicode: тест 测试",
            "special: !@#$%^&*()",
            "",
        ]

        for original in values:
            encrypted = manager.encrypt(original)
            decrypted = manager.decrypt(encrypted)
            assert decrypted == original, f"Failed for: {original}"

    def test_is_encrypted(self, manager):
        """Test checking if value is encrypted."""
        encrypted = manager.encrypt("test")
        plain = "test"

        assert manager.is_encrypted(encrypted) is True
        assert manager.is_encrypted(plain) is False

    def test_store_api_key(self, manager):
        """Test storing API key."""
        manager.store_api_key(
            service="dmarket",
            public_key="pub_key",
            secret_key="sec_key",
        )

        keys = manager.get_api_keys("dmarket")
        assert keys["public_key"] == "pub_key"
        assert keys["secret_key"] == "sec_key"

    def test_get_nonexistent_api_keys(self, manager):
        """Test getting nonexistent API keys."""
        keys = manager.get_api_keys("nonexistent_service")
        assert keys is None or keys == {}

    def test_list_services(self, manager):
        """Test listing services with stored keys."""
        manager.store_api_key("service1", "pub1", "sec1")
        manager.store_api_key("service2", "pub2", "sec2")

        services = manager.list_services()

        assert "service1" in services
        assert "service2" in services

    def test_validate_api_keys(self, manager):
        """Test validating API keys."""
        # Valid keys
        is_valid = manager.validate_api_keys(
            public_key="valid_public_key",
            secret_key="valid_secret_key",
        )
        assert is_valid is True

        # Invalid keys
        is_valid = manager.validate_api_keys(
            public_key="",
            secret_key="secret",
        )
        assert is_valid is False

    def test_clear_all_secrets(self, manager):
        """Test clearing all secrets."""
        manager.set_secret("KEY1", "value1")
        manager.set_secret("KEY2", "value2")

        manager.clear_all()

        assert manager.get_secret("KEY1") is None
        assert manager.get_secret("KEY2") is None

    def test_export_secrets(self, manager):
        """Test exporting secrets (masked)."""
        manager.set_secret("EXPORT_KEY", "secret_value")

        exported = manager.export_secrets()

        assert isinstance(exported, dict)
        # Values should be masked
        assert "secret_value" not in str(exported)

    def test_generate_encryption_key(self, manager):
        """Test generating new encryption key."""
        key = manager.generate_encryption_key()

        assert len(key) > 0
        assert isinstance(key, (str, bytes))
