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
