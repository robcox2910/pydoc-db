"""Tests for query operators."""

import pytest

from pydocdb.errors import InvalidQueryError
from pydocdb.operators import op_eq, op_exists, op_gt, op_gte, op_in, op_lt, op_lte, op_ne

# Named constants for test values
VALUE_TEN = 10
VALUE_TWENTY = 20
VALUE_THIRTY = 30


class TestEqualityOperators:
    """Test $eq and $ne operators."""

    def test_eq_matches(self) -> None:
        """Verify $eq returns True for equal values."""
        assert op_eq(VALUE_TEN, VALUE_TEN) is True

    def test_eq_no_match(self) -> None:
        """Verify $eq returns False for different values."""
        assert op_eq(VALUE_TEN, VALUE_TWENTY) is False

    def test_eq_string(self) -> None:
        """Verify $eq works with strings."""
        assert op_eq("hello", "hello") is True

    def test_ne_matches(self) -> None:
        """Verify $ne returns True for different values."""
        assert op_ne(VALUE_TEN, VALUE_TWENTY) is True

    def test_ne_no_match(self) -> None:
        """Verify $ne returns False for equal values."""
        assert op_ne(VALUE_TEN, VALUE_TEN) is False


class TestComparisonOperators:
    """Test $gt, $gte, $lt, $lte operators."""

    def test_gt_greater(self) -> None:
        """Verify $gt returns True when value is greater."""
        assert op_gt(VALUE_TWENTY, VALUE_TEN) is True

    def test_gt_equal(self) -> None:
        """Verify $gt returns False when values are equal."""
        assert op_gt(VALUE_TEN, VALUE_TEN) is False

    def test_gt_less(self) -> None:
        """Verify $gt returns False when value is less."""
        assert op_gt(VALUE_TEN, VALUE_TWENTY) is False

    def test_gt_none(self) -> None:
        """Verify $gt returns False for None values."""
        assert op_gt(None, VALUE_TEN) is False

    def test_gte_greater(self) -> None:
        """Verify $gte returns True when value is greater."""
        assert op_gte(VALUE_TWENTY, VALUE_TEN) is True

    def test_gte_equal(self) -> None:
        """Verify $gte returns True when values are equal."""
        assert op_gte(VALUE_TEN, VALUE_TEN) is True

    def test_gte_less(self) -> None:
        """Verify $gte returns False when value is less."""
        assert op_gte(VALUE_TEN, VALUE_TWENTY) is False

    def test_gte_none(self) -> None:
        """Verify $gte returns False for None values."""
        assert op_gte(None, VALUE_TEN) is False

    def test_lt_less(self) -> None:
        """Verify $lt returns True when value is less."""
        assert op_lt(VALUE_TEN, VALUE_TWENTY) is True

    def test_lt_equal(self) -> None:
        """Verify $lt returns False when values are equal."""
        assert op_lt(VALUE_TEN, VALUE_TEN) is False

    def test_lt_greater(self) -> None:
        """Verify $lt returns False when value is greater."""
        assert op_lt(VALUE_TWENTY, VALUE_TEN) is False

    def test_lt_none(self) -> None:
        """Verify $lt returns False for None values."""
        assert op_lt(None, VALUE_TEN) is False

    def test_lte_less(self) -> None:
        """Verify $lte returns True when value is less."""
        assert op_lte(VALUE_TEN, VALUE_TWENTY) is True

    def test_lte_equal(self) -> None:
        """Verify $lte returns True when values are equal."""
        assert op_lte(VALUE_TEN, VALUE_TEN) is True

    def test_lte_greater(self) -> None:
        """Verify $lte returns False when value is greater."""
        assert op_lte(VALUE_TWENTY, VALUE_TEN) is False

    def test_lte_none(self) -> None:
        """Verify $lte returns False for None values."""
        assert op_lte(None, VALUE_TEN) is False


class TestInOperator:
    """Test $in operator."""

    def test_in_found(self) -> None:
        """Verify $in returns True when value is in the list."""
        assert op_in("a", ["a", "b", "c"]) is True

    def test_in_not_found(self) -> None:
        """Verify $in returns False when value is not in the list."""
        assert op_in("d", ["a", "b", "c"]) is False

    def test_in_requires_list(self) -> None:
        """Verify $in raises InvalidQueryError if not given a list."""
        with pytest.raises(InvalidQueryError, match="list"):
            op_in("a", "not-a-list")


class TestExistsOperator:
    """Test $exists operator."""

    def test_exists_true_field_present(self) -> None:
        """Verify $exists: True matches when field has a value."""
        assert op_exists("something", True) is True

    def test_exists_true_field_missing(self) -> None:
        """Verify $exists: True does not match when field is None."""
        assert op_exists(None, True) is False

    def test_exists_false_field_present(self) -> None:
        """Verify $exists: False does not match when field has a value."""
        assert op_exists("something", False) is False

    def test_exists_false_field_missing(self) -> None:
        """Verify $exists: False matches when field is None."""
        assert op_exists(None, False) is True
