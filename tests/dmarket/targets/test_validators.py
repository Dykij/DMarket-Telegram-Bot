"""Tests for targets/validators.py module.

This module provides comprehensive tests for:
- validate_attributes function tests
- extract_attributes_from_title function tests
- GAME_IDS constant tests
"""

from __future__ import annotations

import pytest

from src.dmarket.targets.validators import (
    GAME_IDS,
    extract_attributes_from_title,
    validate_attributes,
)


# ============================================================================
# GAME_IDS Tests
# ============================================================================


class TestGameIDs:
    """Test GAME_IDS constant."""

    def test_csgo_game_id(self):
        """Test CS:GO game ID mapping."""
        assert GAME_IDS["csgo"] == "a8db"

    def test_dota2_game_id(self):
        """Test Dota 2 game ID mapping."""
        assert GAME_IDS["dota2"] == "9a92"

    def test_tf2_game_id(self):
        """Test TF2 game ID mapping."""
        assert GAME_IDS["tf2"] == "tf2"

    def test_rust_game_id(self):
        """Test Rust game ID mapping."""
        assert GAME_IDS["rust"] == "rust"

    def test_all_games_present(self):
        """Test all expected games are present."""
        expected_games = ["csgo", "dota2", "tf2", "rust"]
        assert set(expected_games) == set(GAME_IDS.keys())


# ============================================================================
# validate_attributes Tests
# ============================================================================


class TestValidateAttributes:
    """Test validate_attributes function."""

    def test_validate_none_attributes(self):
        """Test validation with None attributes."""
        # Should not raise
        validate_attributes("csgo", None)

    def test_validate_empty_attributes(self):
        """Test validation with empty attributes."""
        # Should not raise
        validate_attributes("csgo", {})

    def test_validate_valid_float_part_value(self):
        """Test validation with valid floatPartValue."""
        attrs = {"floatPartValue": "0.25"}
        validate_attributes("csgo", attrs)  # Should not raise

    def test_validate_float_part_value_zero(self):
        """Test validation with floatPartValue of 0."""
        attrs = {"floatPartValue": "0"}
        validate_attributes("csgo", attrs)  # Should not raise

    def test_validate_float_part_value_one(self):
        """Test validation with floatPartValue of 1."""
        attrs = {"floatPartValue": "1"}
        validate_attributes("csgo", attrs)  # Should not raise

    def test_validate_float_part_value_invalid_range_negative(self):
        """Test validation with floatPartValue below 0."""
        attrs = {"floatPartValue": "-0.1"}
        with pytest.raises(ValueError, match="floatPartValue должен быть от 0 до 1"):
            validate_attributes("csgo", attrs)

    def test_validate_float_part_value_invalid_range_above_one(self):
        """Test validation with floatPartValue above 1."""
        attrs = {"floatPartValue": "1.5"}
        with pytest.raises(ValueError, match="floatPartValue должен быть от 0 до 1"):
            validate_attributes("csgo", attrs)

    def test_validate_float_part_value_not_a_number(self):
        """Test validation with non-numeric floatPartValue."""
        attrs = {"floatPartValue": "not_a_number"}
        with pytest.raises(ValueError, match="floatPartValue должен быть числом"):
            validate_attributes("csgo", attrs)

    def test_validate_valid_paint_seed(self):
        """Test validation with valid paintSeed."""
        attrs = {"paintSeed": "123"}
        validate_attributes("csgo", attrs)  # Should not raise

    def test_validate_paint_seed_zero(self):
        """Test validation with paintSeed of 0."""
        attrs = {"paintSeed": "0"}
        validate_attributes("csgo", attrs)  # Should not raise

    def test_validate_paint_seed_negative(self):
        """Test validation with negative paintSeed."""
        attrs = {"paintSeed": "-1"}
        with pytest.raises(ValueError, match="paintSeed должен быть положительным"):
            validate_attributes("csgo", attrs)

    def test_validate_paint_seed_not_a_number(self):
        """Test validation with non-numeric paintSeed."""
        attrs = {"paintSeed": "not_a_number"}
        with pytest.raises(ValueError, match="paintSeed должен быть целым числом"):
            validate_attributes("csgo", attrs)

    def test_validate_both_attributes(self):
        """Test validation with both floatPartValue and paintSeed."""
        attrs = {"floatPartValue": "0.5", "paintSeed": "100"}
        validate_attributes("csgo", attrs)  # Should not raise

    def test_validate_csgo_alias_a8db(self):
        """Test validation with a8db game code."""
        attrs = {"floatPartValue": "0.5"}
        validate_attributes("a8db", attrs)  # Should not raise

    def test_validate_cs2_game(self):
        """Test validation with cs2 game code."""
        attrs = {"floatPartValue": "0.5"}
        validate_attributes("cs2", attrs)  # Should not raise

    def test_validate_non_csgo_game_ignores_attributes(self):
        """Test validation for non-CS:GO games ignores CS:GO-specific attrs."""
        # These attrs would be invalid for CS:GO but should be ignored for other games
        attrs = {"floatPartValue": "1.5", "paintSeed": "-1"}
        validate_attributes("dota2", attrs)  # Should not raise
        validate_attributes("rust", attrs)  # Should not raise

    def test_validate_unknown_attributes_ignored(self):
        """Test that unknown attributes are ignored."""
        attrs = {"unknown_attr": "value", "another": 123}
        validate_attributes("csgo", attrs)  # Should not raise


# ============================================================================
# extract_attributes_from_title Tests
# ============================================================================


class TestExtractAttributesFromTitle:
    """Test extract_attributes_from_title function."""

    def test_extract_phase_1(self):
        """Test extraction of Phase 1 from title."""
        title = "Karambit | Doppler (Factory New) Phase 1"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Phase 1"

    def test_extract_phase_2(self):
        """Test extraction of Phase 2 from title."""
        title = "Butterfly Knife | Doppler (Minimal Wear) Phase 2"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Phase 2"

    def test_extract_phase_3(self):
        """Test extraction of Phase 3 from title."""
        title = "M9 Bayonet | Doppler (Factory New) Phase 3"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Phase 3"

    def test_extract_phase_4(self):
        """Test extraction of Phase 4 from title."""
        title = "Bayonet | Doppler (Factory New) Phase 4"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Phase 4"

    def test_extract_ruby(self):
        """Test extraction of Ruby phase from title."""
        title = "Karambit | Doppler Ruby (Factory New)"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Ruby"

    def test_extract_sapphire(self):
        """Test extraction of Sapphire phase from title."""
        title = "Butterfly Knife | Doppler Sapphire (Factory New)"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Sapphire"

    def test_extract_black_pearl(self):
        """Test extraction of Black Pearl phase from title."""
        title = "M9 Bayonet | Doppler Black Pearl (Factory New)"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Black Pearl"

    def test_extract_emerald(self):
        """Test extraction of Emerald phase from title."""
        title = "Karambit | Gamma Doppler Emerald (Factory New)"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Emerald"

    def test_extract_no_phase(self):
        """Test extraction when no phase is present."""
        title = "AK-47 | Redline (Field-Tested)"
        attrs = extract_attributes_from_title("csgo", title)
        assert "phase" not in attrs

    def test_extract_case_insensitive_phase(self):
        """Test phase extraction is case insensitive."""
        title = "Karambit | Doppler (Factory New) PHASE 2"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Phase 2"

    def test_extract_csgo_alias_a8db(self):
        """Test extraction with a8db game code."""
        title = "Karambit | Doppler (Factory New) Phase 1"
        attrs = extract_attributes_from_title("a8db", title)
        assert attrs.get("phase") == "Phase 1"

    def test_extract_cs2_game(self):
        """Test extraction with cs2 game code."""
        title = "Karambit | Doppler (Factory New) Phase 1"
        attrs = extract_attributes_from_title("cs2", title)
        assert attrs.get("phase") == "Phase 1"

    def test_extract_non_csgo_game_returns_empty(self):
        """Test extraction for non-CS:GO games returns empty dict."""
        title = "Karambit | Doppler (Factory New) Phase 1"
        attrs = extract_attributes_from_title("dota2", title)
        assert attrs == {}

    def test_extract_empty_title(self):
        """Test extraction with empty title."""
        attrs = extract_attributes_from_title("csgo", "")
        assert attrs == {}

    def test_extract_ruby_takes_priority_over_phase(self):
        """Test Ruby phase takes priority over numbered phase."""
        # Edge case - shouldn't happen in real data
        title = "Karambit | Doppler Ruby Phase 2 (Factory New)"
        attrs = extract_attributes_from_title("csgo", title)
        # Ruby should override Phase 2 because it's checked after
        assert attrs.get("phase") == "Ruby"

    def test_extract_sapphire_takes_priority_over_phase(self):
        """Test Sapphire phase takes priority over numbered phase."""
        title = "Karambit | Doppler Sapphire Phase 2 (Factory New)"
        attrs = extract_attributes_from_title("csgo", title)
        assert attrs.get("phase") == "Sapphire"


# ============================================================================
# Integration Tests
# ============================================================================


class TestValidatorIntegration:
    """Integration tests for validators module."""

    def test_validate_extracted_attributes(self):
        """Test validating attributes extracted from title."""
        title = "Karambit | Doppler (Factory New) Phase 2"
        attrs = extract_attributes_from_title("csgo", title)
        # Should not raise
        validate_attributes("csgo", attrs)

    def test_validate_manual_attributes_with_extraction(self):
        """Test combining manual attributes with extracted."""
        title = "Karambit | Doppler (Factory New) Phase 2"
        extracted = extract_attributes_from_title("csgo", title)
        manual = {"floatPartValue": "0.01", "paintSeed": "500"}
        combined = {**extracted, **manual}

        # Should not raise
        validate_attributes("csgo", combined)
        assert combined["phase"] == "Phase 2"
        assert combined["floatPartValue"] == "0.01"
        assert combined["paintSeed"] == "500"

    def test_game_id_lookup_with_validation(self):
        """Test game ID lookup integrates with validation."""
        game = "csgo"
        game_id = GAME_IDS.get(game.lower(), game)
        assert game_id == "a8db"

        # Both original and mapped should work for validation
        attrs = {"floatPartValue": "0.5"}
        validate_attributes(game, attrs)
        validate_attributes(game_id, attrs)


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases for validators."""

    def test_float_part_value_boundary_just_below_zero(self):
        """Test floatPartValue just below 0."""
        attrs = {"floatPartValue": "-0.0001"}
        with pytest.raises(ValueError):
            validate_attributes("csgo", attrs)

    def test_float_part_value_boundary_just_above_one(self):
        """Test floatPartValue just above 1."""
        attrs = {"floatPartValue": "1.0001"}
        with pytest.raises(ValueError):
            validate_attributes("csgo", attrs)

    def test_float_part_value_as_integer(self):
        """Test floatPartValue as integer."""
        attrs = {"floatPartValue": 0.5}
        validate_attributes("csgo", attrs)  # Should accept float type

    def test_paint_seed_as_integer_type(self):
        """Test paintSeed as integer type."""
        attrs = {"paintSeed": 100}
        validate_attributes("csgo", attrs)  # Should accept int type

    def test_phase_extraction_with_extra_whitespace(self):
        """Test phase extraction with extra whitespace."""
        title = "Karambit | Doppler (Factory New) Phase    2"
        attrs = extract_attributes_from_title("csgo", title)
        # Regex uses \s+ so this should work
        assert "phase" in attrs

    def test_none_value_in_attributes(self):
        """Test handling of None values in attributes."""
        attrs = {"floatPartValue": None}
        with pytest.raises((ValueError, TypeError)):
            validate_attributes("csgo", attrs)
