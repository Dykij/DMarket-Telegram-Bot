"""Unit tests for src/dmarket/targets/validators.py module.

Tests for target validation functions and attribute extraction.
"""

import pytest


class TestValidateAttributes:
    """Tests for validate_attributes function."""

    def test_validate_attributes_with_none_attrs(self):
        """Test validate_attributes returns None for None attrs."""
        from src.dmarket.targets.validators import validate_attributes

        # Should not raise - returns None
        result = validate_attributes("csgo", None)
        assert result is None

    def test_validate_attributes_with_empty_attrs(self):
        """Test validate_attributes returns None for empty attrs."""
        from src.dmarket.targets.validators import validate_attributes

        # Should not raise
        validate_attributes("csgo", {})

    def test_validate_attributes_valid_float_part_value(self):
        """Test validate_attributes accepts valid floatPartValue."""
        from src.dmarket.targets.validators import validate_attributes

        # Valid values
        validate_attributes("csgo", {"floatPartValue": 0.0})
        validate_attributes("csgo", {"floatPartValue": 0.5})
        validate_attributes("csgo", {"floatPartValue": 1.0})
        validate_attributes("csgo", {"floatPartValue": "0.5"})

    def test_validate_attributes_invalid_float_part_value_too_low(self):
        """Test validate_attributes rejects floatPartValue < 0."""
        from src.dmarket.targets.validators import validate_attributes

        with pytest.raises(ValueError, match="floatPartValue должен быть от 0 до 1"):
            validate_attributes("csgo", {"floatPartValue": -0.1})

    def test_validate_attributes_invalid_float_part_value_too_high(self):
        """Test validate_attributes rejects floatPartValue > 1."""
        from src.dmarket.targets.validators import validate_attributes

        with pytest.raises(ValueError, match="floatPartValue должен быть от 0 до 1"):
            validate_attributes("csgo", {"floatPartValue": 1.5})

    def test_validate_attributes_invalid_float_part_value_not_number(self):
        """Test validate_attributes rejects non-numeric floatPartValue."""
        from src.dmarket.targets.validators import validate_attributes

        with pytest.raises(ValueError, match="floatPartValue должен быть числом"):
            validate_attributes("csgo", {"floatPartValue": "invalid"})

    def test_validate_attributes_valid_paint_seed(self):
        """Test validate_attributes accepts valid paintSeed."""
        from src.dmarket.targets.validators import validate_attributes

        # Valid values
        validate_attributes("csgo", {"paintSeed": 0})
        validate_attributes("csgo", {"paintSeed": 100})
        validate_attributes("csgo", {"paintSeed": 999})
        validate_attributes("csgo", {"paintSeed": "500"})

    def test_validate_attributes_invalid_paint_seed_negative(self):
        """Test validate_attributes rejects negative paintSeed."""
        from src.dmarket.targets.validators import validate_attributes

        with pytest.raises(ValueError, match="paintSeed должен быть положительным"):
            validate_attributes("csgo", {"paintSeed": -1})

    def test_validate_attributes_invalid_paint_seed_not_integer(self):
        """Test validate_attributes rejects non-integer paintSeed."""
        from src.dmarket.targets.validators import validate_attributes

        with pytest.raises(ValueError, match="paintSeed должен быть целым числом"):
            validate_attributes("csgo", {"paintSeed": "invalid"})

    def test_validate_attributes_for_cs2_game(self):
        """Test validate_attributes works for cs2 game code."""
        from src.dmarket.targets.validators import validate_attributes

        # Should validate for cs2
        validate_attributes("cs2", {"floatPartValue": 0.5})
        validate_attributes("cs2", {"paintSeed": 100})

        with pytest.raises(ValueError):
            validate_attributes("cs2", {"floatPartValue": 2.0})

    def test_validate_attributes_for_a8db_game(self):
        """Test validate_attributes works for a8db game code."""
        from src.dmarket.targets.validators import validate_attributes

        # Should validate for a8db (CSGO internal ID)
        validate_attributes("a8db", {"floatPartValue": 0.5})
        validate_attributes("a8db", {"paintSeed": 100})

        with pytest.raises(ValueError):
            validate_attributes("a8db", {"floatPartValue": 2.0})

    def test_validate_attributes_for_non_csgo_game(self):
        """Test validate_attributes skips validation for non-CSGO games."""
        from src.dmarket.targets.validators import validate_attributes

        # For dota2, these attributes should not be validated
        validate_attributes("dota2", {"floatPartValue": 2.0})
        validate_attributes("dota2", {"paintSeed": -100})

    def test_validate_attributes_multiple_attributes(self):
        """Test validate_attributes validates multiple attributes."""
        from src.dmarket.targets.validators import validate_attributes

        # Both valid
        validate_attributes("csgo", {"floatPartValue": 0.5, "paintSeed": 100})

        # floatPartValue invalid
        with pytest.raises(ValueError):
            validate_attributes("csgo", {"floatPartValue": 2.0, "paintSeed": 100})

        # paintSeed invalid
        with pytest.raises(ValueError):
            validate_attributes("csgo", {"floatPartValue": 0.5, "paintSeed": -1})


class TestExtractAttributesFromTitle:
    """Tests for extract_attributes_from_title function."""

    def test_extract_phase_from_doppler(self):
        """Test extract_attributes_from_title extracts phase from Doppler title."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "Karambit | Doppler (Factory New) Phase 2"
        )

        assert "phase" in result
        assert result["phase"] == "Phase 2"

    def test_extract_phase_1_from_title(self):
        """Test extract_attributes_from_title extracts Phase 1."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "Butterfly Knife | Doppler (Minimal Wear) Phase 1"
        )

        assert result["phase"] == "Phase 1"

    def test_extract_phase_3_from_title(self):
        """Test extract_attributes_from_title extracts Phase 3."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "M9 Bayonet | Doppler (Factory New) Phase 3"
        )

        assert result["phase"] == "Phase 3"

    def test_extract_phase_4_from_title(self):
        """Test extract_attributes_from_title extracts Phase 4."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "Bayonet | Doppler (Factory New) Phase 4"
        )

        assert result["phase"] == "Phase 4"

    def test_extract_ruby_from_title(self):
        """Test extract_attributes_from_title extracts Ruby phase."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "Karambit | Doppler Ruby (Factory New)"
        )

        assert result["phase"] == "Ruby"

    def test_extract_sapphire_from_title(self):
        """Test extract_attributes_from_title extracts Sapphire phase."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "Karambit | Doppler Sapphire (Factory New)"
        )

        assert result["phase"] == "Sapphire"

    def test_extract_black_pearl_from_title(self):
        """Test extract_attributes_from_title extracts Black Pearl phase."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "M9 Bayonet | Doppler Black Pearl (Factory New)"
        )

        assert result["phase"] == "Black Pearl"

    def test_extract_emerald_from_title(self):
        """Test extract_attributes_from_title extracts Emerald phase."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "Bayonet | Gamma Doppler Emerald (Factory New)"
        )

        assert result["phase"] == "Emerald"

    def test_extract_no_phase_from_regular_item(self):
        """Test extract_attributes_from_title returns empty dict for regular items."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "AK-47 | Redline (Field-Tested)"
        )

        assert result == {}

    def test_extract_attributes_for_non_csgo_game(self):
        """Test extract_attributes_from_title returns empty dict for non-CSGO."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "dota2",
            "Karambit | Doppler (Factory New) Phase 2"
        )

        assert result == {}

    def test_extract_attributes_for_cs2_game(self):
        """Test extract_attributes_from_title works for cs2 game code."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "cs2",
            "Karambit | Doppler (Factory New) Phase 2"
        )

        assert "phase" in result
        assert result["phase"] == "Phase 2"

    def test_extract_attributes_for_a8db_game(self):
        """Test extract_attributes_from_title works for a8db game code."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "a8db",
            "Karambit | Doppler (Factory New) Phase 2"
        )

        assert "phase" in result
        assert result["phase"] == "Phase 2"

    def test_extract_phase_case_insensitive(self):
        """Test extract_attributes_from_title is case insensitive for phase."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title(
            "csgo",
            "Karambit | Doppler (Factory New) PHASE 2"
        )

        assert "phase" in result
        assert result["phase"] == "Phase 2"

    def test_extract_attributes_with_empty_title(self):
        """Test extract_attributes_from_title with empty title."""
        from src.dmarket.targets.validators import extract_attributes_from_title

        result = extract_attributes_from_title("csgo", "")

        assert result == {}


class TestGameIDs:
    """Tests for GAME_IDS constant."""

    def test_game_ids_contains_csgo(self):
        """Test GAME_IDS contains csgo mapping."""
        from src.dmarket.targets.validators import GAME_IDS

        assert "csgo" in GAME_IDS
        assert GAME_IDS["csgo"] == "a8db"

    def test_game_ids_contains_dota2(self):
        """Test GAME_IDS contains dota2 mapping."""
        from src.dmarket.targets.validators import GAME_IDS

        assert "dota2" in GAME_IDS
        assert GAME_IDS["dota2"] == "9a92"

    def test_game_ids_contains_tf2(self):
        """Test GAME_IDS contains tf2 mapping."""
        from src.dmarket.targets.validators import GAME_IDS

        assert "tf2" in GAME_IDS
        assert GAME_IDS["tf2"] == "tf2"

    def test_game_ids_contains_rust(self):
        """Test GAME_IDS contains rust mapping."""
        from src.dmarket.targets.validators import GAME_IDS

        assert "rust" in GAME_IDS
        assert GAME_IDS["rust"] == "rust"


class TestModuleExports:
    """Tests for module exports."""

    def test_module_exports_validate_attributes(self):
        """Test module exports validate_attributes function."""
        from src.dmarket.targets import validators

        assert hasattr(validators, "validate_attributes")
        assert "validate_attributes" in validators.__all__

    def test_module_exports_extract_attributes_from_title(self):
        """Test module exports extract_attributes_from_title function."""
        from src.dmarket.targets import validators

        assert hasattr(validators, "extract_attributes_from_title")
        assert "extract_attributes_from_title" in validators.__all__

    def test_module_exports_game_ids(self):
        """Test module exports GAME_IDS constant."""
        from src.dmarket.targets import validators

        assert hasattr(validators, "GAME_IDS")
        assert "GAME_IDS" in validators.__all__
