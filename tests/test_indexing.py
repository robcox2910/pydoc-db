"""Tests for the indexing module."""

from pydocdb.collection import Collection
from pydocdb.document import Document
from pydocdb.indexing import Index

EXPECTED_TWO = 2


class TestIndexOperations:
    """Test adding, removing, and querying an index."""

    def test_add_and_find(self) -> None:
        """Verify adding documents makes them findable by value."""
        index = Index("city")
        doc = Document({"_id": "1", "city": "Paris"})
        index.add(doc)
        result = index.find("Paris")
        assert "1" in result

    def test_find_no_match(self) -> None:
        """Verify finding a non-indexed value returns empty set."""
        index = Index("city")
        result = index.find("London")
        assert len(result) == 0

    def test_add_multiple_same_value(self) -> None:
        """Verify multiple documents with same value are all found."""
        index = Index("city")
        index.add(Document({"_id": "1", "city": "Paris"}))
        index.add(Document({"_id": "2", "city": "Paris"}))
        result = index.find("Paris")
        assert len(result) == EXPECTED_TWO

    def test_remove(self) -> None:
        """Verify removing a document from the index."""
        index = Index("city")
        doc = Document({"_id": "1", "city": "Paris"})
        index.add(doc)
        index.remove(doc)
        result = index.find("Paris")
        assert len(result) == 0

    def test_remove_nonexistent(self) -> None:
        """Verify removing a non-indexed document is safe."""
        index = Index("city")
        doc = Document({"_id": "1", "city": "Paris"})
        index.remove(doc)  # Should not raise

    def test_clear(self) -> None:
        """Verify clearing removes all entries."""
        index = Index("city")
        index.add(Document({"_id": "1", "city": "Paris"}))
        index.clear()
        assert len(index) == 0

    def test_none_value_not_indexed(self) -> None:
        """Verify documents without the indexed field are skipped."""
        index = Index("city")
        doc = Document({"_id": "1", "name": "Alice"})
        index.add(doc)
        assert len(index) == 0

    def test_nested_field(self) -> None:
        """Verify indexing nested fields with dot notation."""
        index = Index("address.city")
        doc = Document({"_id": "1", "address": {"city": "Paris"}})
        index.add(doc)
        result = index.find("Paris")
        assert "1" in result

    def test_len(self) -> None:
        """Verify __len__ returns unique value count."""
        index = Index("city")
        index.add(Document({"_id": "1", "city": "Paris"}))
        index.add(Document({"_id": "2", "city": "London"}))
        assert len(index) == EXPECTED_TWO

    def test_repr(self) -> None:
        """Verify repr includes useful info."""
        index = Index("city")
        index.add(Document({"_id": "1", "city": "Paris"}))
        result = repr(index)
        assert "city" in result


class TestCollectionIndex:
    """Test creating indexes via the Collection class."""

    def test_create_and_list(self) -> None:
        """Verify creating and listing indexes."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "age": 14})
        col.create_index("name")
        assert "name" in col.list_indexes()

    def test_drop_index(self) -> None:
        """Verify dropping an index."""
        col = Collection("test")
        col.create_index("name")
        assert col.drop_index("name") is True
        assert "name" not in col.list_indexes()

    def test_drop_nonexistent_index(self) -> None:
        """Verify dropping a non-existent index returns False."""
        col = Collection("test")
        assert col.drop_index("nonexistent") is False


class TestIndexBackedFind:
    """Test that find() actually uses an equality index for lookups."""

    def test_indexed_equality_find(self) -> None:
        """Verify an equality find on an indexed field returns the right docs."""
        col = Collection("test")
        col.insert_many(
            [
                {"name": "Alice", "city": "Paris"},
                {"name": "Bob", "city": "London"},
                {"name": "Carol", "city": "Paris"},
            ]
        )
        col.create_index("city")
        results = col.find({"city": "Paris"})
        assert {r["name"] for r in results} == {"Alice", "Carol"}

    def test_indexed_eq_operator_find(self) -> None:
        """Verify {"$eq": value} on an indexed field is index-backed and correct."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "city": "Paris"})
        col.insert_one({"name": "Bob", "city": "London"})
        col.create_index("city")
        results = col.find({"city": {"$eq": "London"}})
        assert len(results) == 1
        assert results[0]["name"] == "Bob"

    def test_index_find_reflects_updates(self) -> None:
        """Verify an index-backed find sees changes made after indexing."""
        col = Collection("test")
        col.insert_one({"_id": "1", "name": "Alice", "city": "Paris"})
        col.create_index("city")
        col.update_one({"_id": "1"}, {"city": "Rome"})
        assert col.find({"city": "Paris"}) == []
        assert col.find_one({"city": "Rome"})["name"] == "Alice"  # type: ignore[index]

    def test_indexed_field_range_query_falls_back(self) -> None:
        """Verify a non-equality operator on an indexed field still scans correctly."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "age": 14})
        col.insert_one({"name": "Bob", "age": 40})
        col.create_index("age")
        # $gt can't use the equality index, so it falls back to a full scan.
        results = col.find({"age": {"$gt": 18}})
        assert len(results) == 1
        assert results[0]["name"] == "Bob"

    def test_indexed_field_none_query_falls_back(self) -> None:
        """Verify querying an indexed field for None falls back to a full scan."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "city": None})
        col.insert_one({"name": "Bob", "city": "Paris"})
        col.create_index("city")
        # None isn't stored in the index, so this must not silently miss Alice.
        results = col.find({"city": None})
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    def test_index_candidates_never_lose_matches(self) -> None:
        """Verify a compound query with an indexed field still finds all matches."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "city": "Paris", "age": 14})
        col.insert_one({"name": "Bob", "city": "Paris", "age": 40})
        col.create_index("city")
        results = col.find({"city": "Paris", "age": {"$lt": 18}})
        assert len(results) == 1
        assert results[0]["name"] == "Alice"


class TestIndexNestedValues:
    """Lists inside lists, and lists inside dicts, can be indexed and searched.

    Regression: found by a property test, which shrank it to the value ``[[]]``.
    """

    def test_create_index_on_list_of_lists(self) -> None:
        """Verify an index can be built on a field holding a list of lists."""
        col = Collection("test")
        col.insert_one({"_id": "1", "name": [[]]})
        col.create_index("name")
        assert col.find({"name": [[]]}) == [{"_id": "1", "name": [[]]}]

    def test_create_index_on_dict_holding_a_list(self) -> None:
        """Verify an index can be built on a field holding a dict with a list inside."""
        col = Collection("test")
        col.insert_one({"_id": "1", "pet": {"": []}})
        col.create_index("pet")
        assert len(col.find({"pet": {"$eq": {"": []}}})) == 1

    def test_search_indexed_field_for_list_of_lists(self) -> None:
        """Verify searching an indexed field for a list of lists finds nothing, not a crash."""
        col = Collection("test")
        col.create_index("name")
        assert col.find({"name": [[]]}) == []

    def test_insert_into_indexed_collection_files_the_card_once(self) -> None:
        """Verify a nested value is filed and indexed, never half-inserted."""
        col = Collection("test")
        col.create_index("name")
        col.insert_one({"_id": "1", "name": [[1], {"a": [2]}]})
        assert col.find({"name": [[1], {"a": [2]}]}) == [{"_id": "1", "name": [[1], {"a": [2]}]}]


# Enough cards that a hash-ordered set of barcodes is very unlikely to come
# out in filing order by luck.
MANY_CARDS = 20


class TestIndexKeepsFilingOrder:
    """An index speeds up find, but the cards still come back in filing order.

    Regression: with an index, find used to return cards in hash order, and
    find_one's "first" match depended on PYTHONHASHSEED.
    """

    def test_indexed_find_returns_cards_in_filing_order(self) -> None:
        """Verify an index-backed find lists matches in the order they were filed."""
        col = Collection("test")
        ids = [f"card-{n}" for n in range(MANY_CARDS)]
        for doc_id in ids:
            col.insert_one({"_id": doc_id, "city": "Paris"})
        col.create_index("city")
        assert [doc["_id"] for doc in col.find({"city": "Paris"})] == ids

    def test_indexed_find_one_returns_the_earliest_filed_match(self) -> None:
        """Verify an index-backed find_one gives the first card filed, like a full scan."""
        col = Collection("test")
        for n in range(MANY_CARDS):
            col.insert_one({"_id": f"card-{n}", "city": "Paris"})
        col.create_index("city")
        found = col.find_one({"city": "Paris"})
        assert found is not None
        assert found["_id"] == "card-0"
