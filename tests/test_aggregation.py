"""Tests for the aggregation pipeline."""

import pytest

from pydocdb.aggregation import aggregate
from pydocdb.document import DocumentData
from pydocdb.errors import InvalidPipelineError

PRICE_TEN = 10
PRICE_TWENTY = 20
PRICE_THIRTY = 30
PRICE_FIFTEEN = 15
EXPECTED_TWO = 2
EXPECTED_THREE = 3
LIMIT_TWO = 2


def _sample_docs() -> list[DocumentData]:
    """Create sample product documents for testing."""
    return [
        {"_id": "1", "name": "Widget", "category": "A", "price": PRICE_TEN},
        {"_id": "2", "name": "Gadget", "category": "A", "price": PRICE_TWENTY},
        {"_id": "3", "name": "Doohickey", "category": "B", "price": PRICE_THIRTY},
        {"_id": "4", "name": "Thingamajig", "category": "B", "price": PRICE_FIFTEEN},
    ]


class TestMatchStage:
    """Test the $match pipeline stage."""

    def test_match_filters_documents(self) -> None:
        """Verify $match filters documents by query."""
        docs = _sample_docs()
        result = aggregate(docs, [{"$match": {"category": "A"}}])
        assert len(result) == EXPECTED_TWO

    def test_match_with_operator(self) -> None:
        """Verify $match works with comparison operators."""
        docs = _sample_docs()
        result = aggregate(docs, [{"$match": {"price": {"$gt": PRICE_FIFTEEN}}}])
        assert len(result) == EXPECTED_TWO


class TestGroupStage:
    """Test the $group pipeline stage."""

    def test_group_by_field(self) -> None:
        """Verify grouping documents by a field."""
        docs = _sample_docs()
        result = aggregate(
            docs,
            [
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            ],
        )
        assert len(result) == EXPECTED_TWO

    def test_group_sum(self) -> None:
        """Verify $sum accumulator adds values."""
        docs = _sample_docs()
        result = aggregate(
            docs,
            [
                {"$group": {"_id": "$category", "total": {"$sum": "$price"}}},
            ],
        )
        # Find category A group
        cat_a = next(r for r in result if r["_id"] == "A")
        expected_total = PRICE_TEN + PRICE_TWENTY
        assert cat_a["total"] == expected_total

    def test_group_avg(self) -> None:
        """Verify $avg accumulator computes average."""
        docs = _sample_docs()
        result = aggregate(
            docs,
            [
                {"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}},
            ],
        )
        cat_a = next(r for r in result if r["_id"] == "A")
        expected_avg = (PRICE_TEN + PRICE_TWENTY) / EXPECTED_TWO
        assert cat_a["avg_price"] == pytest.approx(expected_avg)

    def test_group_min_max(self) -> None:
        """Verify $min and $max accumulators."""
        docs = _sample_docs()
        result = aggregate(
            docs,
            [
                {
                    "$group": {
                        "_id": "$category",
                        "min_price": {"$min": "$price"},
                        "max_price": {"$max": "$price"},
                    }
                },
            ],
        )
        cat_b = next(r for r in result if r["_id"] == "B")
        assert cat_b["min_price"] == PRICE_FIFTEEN
        assert cat_b["max_price"] == PRICE_THIRTY

    def test_group_null_id(self) -> None:
        """Verify grouping all docs together with _id: null."""
        docs = _sample_docs()
        result = aggregate(
            docs,
            [
                {"$group": {"_id": None, "total": {"$sum": "$price"}}},
            ],
        )
        assert len(result) == 1
        expected_total = PRICE_TEN + PRICE_TWENTY + PRICE_THIRTY + PRICE_FIFTEEN
        assert result[0]["total"] == expected_total

    def test_group_missing_id_raises(self) -> None:
        """Verify $group without _id raises InvalidPipelineError."""
        with pytest.raises(InvalidPipelineError, match="_id"):
            aggregate([], [{"$group": {"total": {"$sum": 1}}}])

    def test_unknown_accumulator_raises(self) -> None:
        """Verify unknown accumulator raises InvalidPipelineError."""
        docs = _sample_docs()
        with pytest.raises(InvalidPipelineError, match="Unknown accumulator"):
            aggregate(
                docs,
                [
                    {"$group": {"_id": "$category", "x": {"$badacc": "$price"}}},
                ],
            )


class TestSortStage:
    """Test the $sort pipeline stage."""

    def test_sort_ascending(self) -> None:
        """Verify sorting in ascending order."""
        docs = _sample_docs()
        result = aggregate(docs, [{"$sort": {"price": 1}}])
        assert result[0]["price"] == PRICE_TEN
        assert result[-1]["price"] == PRICE_THIRTY

    def test_sort_descending(self) -> None:
        """Verify sorting in descending order."""
        docs = _sample_docs()
        result = aggregate(docs, [{"$sort": {"price": -1}}])
        assert result[0]["price"] == PRICE_THIRTY
        assert result[-1]["price"] == PRICE_TEN


class TestLimitStage:
    """Test the $limit pipeline stage."""

    def test_limit(self) -> None:
        """Verify limiting the number of results."""
        docs = _sample_docs()
        result = aggregate(docs, [{"$limit": LIMIT_TWO}])
        assert len(result) == EXPECTED_TWO

    def test_limit_invalid_raises(self) -> None:
        """Verify invalid limit raises InvalidPipelineError."""
        with pytest.raises(InvalidPipelineError, match="positive integer"):
            aggregate([], [{"$limit": -1}])

    def test_limit_non_int_raises(self) -> None:
        """Verify non-integer limit raises InvalidPipelineError."""
        with pytest.raises(InvalidPipelineError, match="positive integer"):
            aggregate([], [{"$limit": "two"}])


class TestCountStage:
    """Test the $count pipeline stage."""

    def test_count(self) -> None:
        """Verify counting documents in the pipeline."""
        docs = _sample_docs()
        result = aggregate(docs, [{"$count": "total"}])
        assert len(result) == 1
        expected_count = 4
        assert result[0]["total"] == expected_count

    def test_count_after_match(self) -> None:
        """Verify count after filtering with $match."""
        docs = _sample_docs()
        result = aggregate(
            docs,
            [
                {"$match": {"category": "A"}},
                {"$count": "num_a"},
            ],
        )
        assert result[0]["num_a"] == EXPECTED_TWO

    def test_count_invalid_raises(self) -> None:
        """Verify non-string count field raises InvalidPipelineError."""
        with pytest.raises(InvalidPipelineError, match="string"):
            aggregate([], [{"$count": 123}])


class TestPipelineErrors:
    """Test pipeline validation errors."""

    def test_unknown_stage_raises(self) -> None:
        """Verify unknown stage raises InvalidPipelineError."""
        with pytest.raises(InvalidPipelineError, match="Unknown pipeline stage"):
            aggregate([], [{"$unknown": {}}])

    def test_multi_operator_stage_raises(self) -> None:
        """Verify a stage with multiple operators raises InvalidPipelineError."""
        with pytest.raises(InvalidPipelineError, match="exactly one"):
            aggregate([], [{"$match": {}, "$sort": {}}])


class TestMultiStagePipeline:
    """Test combining multiple pipeline stages."""

    def test_match_group_sort(self) -> None:
        """Verify a multi-stage pipeline: match, group, sort."""
        docs = _sample_docs()
        result = aggregate(
            docs,
            [
                {"$match": {"price": {"$gte": PRICE_FIFTEEN}}},
                {"$group": {"_id": "$category", "total": {"$sum": "$price"}}},
                {"$sort": {"total": -1}},
            ],
        )
        assert len(result) == EXPECTED_TWO
        # B category (30+15=45) should be first
        assert result[0]["_id"] == "B"
