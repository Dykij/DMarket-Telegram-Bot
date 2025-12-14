"""Тесты для feature_flags.py"""

import pytest

from src.utils.feature_flags import Feature, FeatureFlagsManager


class TestFeatureFlagsManager:
    """Тесты для FeatureFlagsManager."""

    @pytest.fixture()
    def manager(self, tmp_path):
        """Create test manager."""
        config_file = tmp_path / "test_flags.yaml"
        config_file.write_text("""
features:
  test_feature:
    enabled: true
    rollout_percent: 100
  rollout_feature:
    enabled: true
    rollout_percent: 50
  disabled_feature:
    enabled: false
""")
        return FeatureFlagsManager(config_path=str(config_file))

    @pytest.mark.asyncio()
    async def test_is_enabled_global(self, manager):
        """Тест глобально включенной фичи."""
        enabled = await manager.is_enabled("test_feature")
        assert enabled is True

    @pytest.mark.asyncio()
    async def test_is_enabled_disabled(self, manager):
        """Тест выключенной фичи."""
        enabled = await manager.is_enabled("disabled_feature")
        assert enabled is False

    @pytest.mark.asyncio()
    async def test_rollout_deterministic(self, manager):
        """Тест детерминированного rollout."""
        user_id = 12345

        # Несколько вызовов должны возвращать одинаковый результат
        result1 = await manager.is_enabled("rollout_feature", user_id)
        result2 = await manager.is_enabled("rollout_feature", user_id)
        result3 = await manager.is_enabled("rollout_feature", user_id)

        assert result1 == result2 == result3

    @pytest.mark.asyncio()
    async def test_whitelist(self, manager):
        """Тест whitelist."""
        user_id = 99999

        # Сначала выключено
        enabled = await manager.is_enabled("disabled_feature", user_id)
        assert enabled is False

        # Добавить в whitelist
        await manager.add_to_whitelist("disabled_feature", user_id)

        # Теперь должно быть включено
        enabled = await manager.is_enabled("disabled_feature", user_id)
        assert enabled is True

    @pytest.mark.asyncio()
    async def test_set_flag(self, manager):
        """Тест установки флага."""
        await manager.set_flag("new_feature", enabled=True, rollout_percent=100)

        enabled = await manager.is_enabled("new_feature")
        assert enabled is True

    @pytest.mark.asyncio()
    async def test_get_user_flags(self, manager):
        """Тест получения всех флагов пользователя."""
        user_id = 12345
        flags = await manager.get_user_flags(user_id)

        assert isinstance(flags, dict)
        assert len(flags) > 0

    def test_feature_enum(self):
        """Тест Feature enum."""
        assert Feature.PORTFOLIO_MANAGEMENT.value == "portfolio_management"
        assert Feature.AUTO_SELL.value == "auto_sell"
