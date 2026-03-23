"""Tests for field projection."""

from pydocdb.projection import EXCLUDE, INCLUDE, apply_projection, extract_field


class TestInclusion:
    """Test inclusion projections (selecting specific fields)."""

    def test_include_specific_fields(self) -> None:
        """Verify only the listed fields are returned."""
        data = {"_id": "1", "name": "Alice", "age": 14, "email": "alice@example.com"}
        result = apply_projection(data, {"name": INCLUDE})
        assert "name" in result
        assert "_id" in result  # _id included by default
        assert "age" not in result
        assert "email" not in result

    def test_exclude_id(self) -> None:
        """Verify _id can be excluded in an inclusion projection."""
        data = {"_id": "1", "name": "Alice", "age": 14}
        result = apply_projection(data, {"name": INCLUDE, "_id": EXCLUDE})
        assert "_id" not in result
        assert "name" in result

    def test_include_multiple(self) -> None:
        """Verify including multiple fields."""
        data = {"_id": "1", "name": "Alice", "age": 14, "email": "a@b.com"}
        result = apply_projection(data, {"name": INCLUDE, "age": INCLUDE})
        assert "name" in result
        assert "age" in result
        assert "email" not in result


class TestExclusion:
    """Test exclusion projections (hiding specific fields)."""

    def test_exclude_specific_fields(self) -> None:
        """Verify the listed fields are removed."""
        data = {"_id": "1", "name": "Alice", "age": 14, "email": "alice@example.com"}
        result = apply_projection(data, {"email": EXCLUDE})
        assert "name" in result
        assert "age" in result
        assert "email" not in result

    def test_exclude_id(self) -> None:
        """Verify excluding only _id."""
        data = {"_id": "1", "name": "Alice"}
        result = apply_projection(data, {"_id": EXCLUDE})
        assert "_id" not in result
        assert "name" in result


class TestEmptyProjection:
    """Test behavior with no projection."""

    def test_empty_returns_all(self) -> None:
        """Verify an empty projection returns all fields."""
        data = {"_id": "1", "name": "Alice"}
        result = apply_projection(data, {})
        assert result == data

    def test_returns_copy(self) -> None:
        """Verify the returned data is a copy."""
        data = {"_id": "1", "name": "Alice"}
        result = apply_projection(data, {})
        result["name"] = "Bob"
        assert data["name"] == "Alice"


class TestExtractField:
    """Test dot-notation field extraction."""

    def test_top_level(self) -> None:
        """Verify extracting a top-level field."""
        assert extract_field({"name": "Alice"}, "name") == "Alice"

    def test_nested(self) -> None:
        """Verify extracting a nested field."""
        data = {"address": {"city": "Paris"}}
        assert extract_field(data, "address.city") == "Paris"

    def test_missing(self) -> None:
        """Verify extracting a missing field returns None."""
        assert extract_field({"name": "Alice"}, "age") is None

    def test_missing_nested(self) -> None:
        """Verify extracting a missing nested path returns None."""
        assert extract_field({"name": "Alice"}, "address.city") is None

    def test_non_dict_intermediate(self) -> None:
        """Verify a non-dict intermediate returns None."""
        data = {"name": "Alice"}
        assert extract_field(data, "name.first") is None
