"""Tests for json_utils module.

This module tests JSON serialization/deserialization utilities
with support for both orjson and standard json fallback.
"""

import io
import math

import pytest

from src.utils import json_utils


class TestJsonDumps:
    """Tests for dumps function."""

    def test_dumps_simple_dict(self):
        """Test serializing simple dictionary."""
        data = {"name": "test", "value": 123}
        result = json_utils.dumps(data)

        assert isinstance(result, str)
        assert '"name"' in result
        assert '"test"' in result
        assert '"value"' in result
        assert "123" in result

    def test_dumps_list(self):
        """Test serializing list."""
        data = [1, 2, 3, "test"]
        result = json_utils.dumps(data)

        assert isinstance(result, str)
        assert "1" in result
        assert '"test"' in result

    def test_dumps_nested_dict(self):
        """Test serializing nested structures."""
        data = {
            "level1": {"level2": {"value": "deep"}},
            "list": [1, 2, {"nested": True}],
        }
        result = json_utils.dumps(data)

        assert '"deep"' in result
        assert '"nested"' in result

    def test_dumps_unicode(self):
        """Test serializing unicode characters."""
        data = {"name": "Тест", "emoji": "🎮"}
        result = json_utils.dumps(data)

        assert "Тест" in result
        assert "🎮" in result

    def test_dumps_numbers(self):
        """Test serializing different number types."""
        data = {
            "int": 42,
            "float": math.pi,
            "negative": -100,
            "zero": 0,
        }
        result = json_utils.dumps(data)

        assert "42" in result
        assert "3.14159" in result
        assert "-100" in result

    def test_dumps_boolean_and_none(self):
        """Test serializing boolean and None values."""
        data = {"true": True, "false": False, "null": None}
        result = json_utils.dumps(data)

        assert "true" in result.lower()
        assert "false" in result.lower()
        assert "null" in result.lower()


class TestJsonLoads:
    """Tests for loads function."""

    def test_loads_simple_dict(self):
        """Test deserializing simple dictionary."""
        json_str = '{"name": "test", "value": 123}'
        result = json_utils.loads(json_str)

        assert result["name"] == "test"
        assert result["value"] == 123

    def test_loads_from_bytes(self):
        """Test deserializing from bytes."""
        json_bytes = b'{"name": "test"}'
        result = json_utils.loads(json_bytes)

        assert result["name"] == "test"

    def test_loads_list(self):
        """Test deserializing list."""
        json_str = '[1, 2, 3, "test"]'
        result = json_utils.loads(json_str)

        assert result == [1, 2, 3, "test"]

    def test_loads_nested(self):
        """Test deserializing nested structures."""
        json_str = '{"outer": {"inner": {"value": 42}}}'
        result = json_utils.loads(json_str)

        assert result["outer"]["inner"]["value"] == 42

    def test_loads_unicode(self):
        """Test deserializing unicode."""
        json_str = '{"name": "Тест", "emoji": "🎮"}'
        result = json_utils.loads(json_str)

        assert result["name"] == "Тест"
        assert result["emoji"] == "🎮"


class TestJsonDump:
    """Tests for dump function (file writing)."""

    def test_dump_to_file_like_object(self):
        """Test dumping to file-like object."""
        data = {"name": "test", "value": 123}
        fp = io.BytesIO()

        json_utils.dump(data, fp)

        fp.seek(0)
        content = fp.read()
        assert b"name" in content
        assert b"test" in content

    def test_dump_complex_structure(self):
        """Test dumping complex structure."""
        data = {
            "items": [
                {"id": 1, "name": "item1"},
                {"id": 2, "name": "item2"},
            ]
        }
        fp = io.BytesIO()

        json_utils.dump(data, fp)

        fp.seek(0)
        content = fp.read()
        assert b"items" in content


class TestJsonLoad:
    """Tests for load function (file reading)."""

    def test_load_from_file_like_object(self):
        """Test loading from file-like object."""
        json_data = b'{"name": "test", "value": 123}'
        fp = io.BytesIO(json_data)

        result = json_utils.load(fp)

        assert result["name"] == "test"
        assert result["value"] == 123

    def test_load_complex_structure(self):
        """Test loading complex structure."""
        json_data = b'{"items": [{"id": 1}, {"id": 2}]}'
        fp = io.BytesIO(json_data)

        result = json_utils.load(fp)

        assert len(result["items"]) == 2
        assert result["items"][0]["id"] == 1


class TestJsonRoundTrip:
    """Tests for serialization/deserialization round trip."""

    def test_roundtrip_dict(self):
        """Test roundtrip for dictionary."""
        original = {"name": "test", "values": [1, 2, 3]}

        json_str = json_utils.dumps(original)
        restored = json_utils.loads(json_str)

        assert restored == original

    def test_roundtrip_list(self):
        """Test roundtrip for list."""
        original = [{"id": 1}, {"id": 2}, {"id": 3}]

        json_str = json_utils.dumps(original)
        restored = json_utils.loads(json_str)

        assert restored == original

    def test_roundtrip_unicode(self):
        """Test roundtrip for unicode content."""
        original = {"text": "Привет мир! 🌍"}

        json_str = json_utils.dumps(original)
        restored = json_utils.loads(json_str)

        assert restored == original


class TestJsonDecodeError:
    """Tests for JSONDecodeError handling."""

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises JSONDecodeError."""
        invalid_json = '{"name": invalid}'

        with pytest.raises(json_utils.JSONDecodeError):
            json_utils.loads(invalid_json)

    def test_empty_string_raises_error(self):
        """Test that empty string raises JSONDecodeError."""
        with pytest.raises(json_utils.JSONDecodeError):
            json_utils.loads("")


class TestOrjsonAvailability:
    """Tests for orjson availability check."""

    def test_orjson_available_flag_exists(self):
        """Test that ORJSON_AVAILABLE flag exists."""
        assert hasattr(json_utils, "ORJSON_AVAILABLE")
        assert isinstance(json_utils.ORJSON_AVAILABLE, bool)
