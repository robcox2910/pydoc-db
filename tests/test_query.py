"""Tests for the query matching engine."""

import pytest

from pydocdb.document import Document
from pydocdb.errors import InvalidQueryError
from pydocdb.query import matches

AGE_FOURTEEN = 14
AGE_EIGHTEEN = 18
AGE_TEN = 10
AGE_TWENTY = 20


class TestSimpleQueries:
    """Test basic equality and operator queries."""

    def test_empty_query_matches_all(self) -> None:
        """Verify an empty query matches any document."""
        doc = Document({"name": "Alice"})
        assert matches(doc, {}) is True

    def test_equality_match(self) -> None:
        """Verify simple equality matching."""
        doc = Document({"name": "Alice", "age": AGE_FOURTEEN})
        assert matches(doc, {"name": "Alice"}) is True

    def test_equality_no_match(self) -> None:
        """Verify simple equality rejects non-matching values."""
        doc = Document({"name": "Alice"})
        assert matches(doc, {"name": "Bob"}) is False

    def test_operator_gt(self) -> None:
        """Verify $gt operator in a query."""
        doc = Document({"age": AGE_FOURTEEN})
        assert matches(doc, {"age": {"$gt": AGE_TEN}}) is True
        assert matches(doc, {"age": {"$gt": AGE_TWENTY}}) is False

    def test_multiple_conditions(self) -> None:
        """Verify multiple field conditions (implicit AND)."""
        doc = Document({"name": "Alice", "age": AGE_FOURTEEN})
        assert matches(doc, {"name": "Alice", "age": {"$gt": AGE_TEN}}) is True
        assert matches(doc, {"name": "Bob", "age": {"$gt": AGE_TEN}}) is False

    def test_unknown_operator_raises(self) -> None:
        """Verify unknown operators raise InvalidQueryError."""
        doc = Document({"age": AGE_FOURTEEN})
        with pytest.raises(InvalidQueryError, match="Unknown"):
            matches(doc, {"age": {"$badop": 5}})


class TestNestedFieldQueries:
    """Test queries on nested fields using dot notation."""

    def test_nested_equality(self) -> None:
        """Verify querying a nested field with dot notation."""
        doc = Document({"address": {"city": "Paris"}})
        assert matches(doc, {"address.city": "Paris"}) is True
        assert matches(doc, {"address.city": "London"}) is False

    def test_nested_operator(self) -> None:
        """Verify operators work on nested fields."""
        doc = Document({"stats": {"score": AGE_EIGHTEEN}})
        assert matches(doc, {"stats.score": {"$gte": AGE_EIGHTEEN}}) is True


class TestLogicalOperators:
    """Test $and, $or, and $not operators."""

    def test_and_all_match(self) -> None:
        """Verify $and passes when all conditions match."""
        doc = Document({"name": "Alice", "age": AGE_FOURTEEN})
        query = {"$and": [{"name": "Alice"}, {"age": AGE_FOURTEEN}]}
        assert matches(doc, query) is True

    def test_and_partial_match(self) -> None:
        """Verify $and fails when any condition doesn't match."""
        doc = Document({"name": "Alice", "age": AGE_FOURTEEN})
        query = {"$and": [{"name": "Alice"}, {"age": AGE_TWENTY}]}
        assert matches(doc, query) is False

    def test_and_requires_list(self) -> None:
        """Verify $and raises when given a non-list."""
        doc = Document({"name": "Alice"})
        with pytest.raises(InvalidQueryError, match="list"):
            matches(doc, {"$and": {"name": "Alice"}})

    def test_or_one_matches(self) -> None:
        """Verify $or passes when at least one condition matches."""
        doc = Document({"name": "Alice"})
        query = {"$or": [{"name": "Alice"}, {"name": "Bob"}]}
        assert matches(doc, query) is True

    def test_or_none_match(self) -> None:
        """Verify $or fails when no conditions match."""
        doc = Document({"name": "Charlie"})
        query = {"$or": [{"name": "Alice"}, {"name": "Bob"}]}
        assert matches(doc, query) is False

    def test_or_requires_list(self) -> None:
        """Verify $or raises when given a non-list."""
        doc = Document({"name": "Alice"})
        with pytest.raises(InvalidQueryError, match="list"):
            matches(doc, {"$or": {"name": "Alice"}})

    def test_not(self) -> None:
        """Verify $not negates the condition."""
        doc = Document({"name": "Alice"})
        assert matches(doc, {"$not": {"name": "Bob"}}) is True
        assert matches(doc, {"$not": {"name": "Alice"}}) is False

    def test_not_requires_dict(self) -> None:
        """Verify $not raises when given a non-dict."""
        doc = Document({"name": "Alice"})
        with pytest.raises(InvalidQueryError, match="dictionary"):
            matches(doc, {"$not": "invalid"})
