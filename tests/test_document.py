"""Tests for the Document class."""

from pydocdb.document import Document


class TestDocumentCreation:
    """Test creating documents with various inputs."""

    def test_auto_generates_id(self) -> None:
        """Verify a document gets an auto-generated _id."""
        doc = Document({"name": "Alice"})
        assert doc.id is not None
        assert len(doc.id) > 0

    def test_preserves_custom_id(self) -> None:
        """Verify a custom _id is preserved."""
        custom_id = "my-custom-id"
        doc = Document({"_id": custom_id, "name": "Alice"})
        assert doc.id == custom_id

    def test_create_from_dict(self) -> None:
        """Verify creation from a dictionary."""
        doc = Document({"name": "Alice", "age": 14})
        assert doc.get("name") == "Alice"
        expected_age = 14
        assert doc.get("age") == expected_age

    def test_create_from_kwargs(self) -> None:
        """Verify creation from keyword arguments."""
        doc = Document(name="Bob", age=13)
        assert doc.get("name") == "Bob"

    def test_create_empty(self) -> None:
        """Verify creating an empty document still gets an _id."""
        doc = Document()
        assert doc.id is not None

    def test_unique_ids(self) -> None:
        """Verify two documents get different auto-generated IDs."""
        doc1 = Document({"name": "Alice"})
        doc2 = Document({"name": "Bob"})
        assert doc1.id != doc2.id

    def test_does_not_mutate_original_dict(self) -> None:
        """Verify the original dict is not modified."""
        original = {"name": "Alice"}
        Document(original)
        assert "_id" not in original


class TestDocumentAccess:
    """Test accessing document fields."""

    def test_get_existing_field(self) -> None:
        """Verify getting an existing field returns its value."""
        doc = Document({"name": "Alice"})
        assert doc.get("name") == "Alice"

    def test_get_missing_field_returns_default(self) -> None:
        """Verify getting a missing field returns the default."""
        doc = Document({"name": "Alice"})
        assert doc.get("age") is None
        expected_default = 0
        assert doc.get("age", expected_default) == expected_default

    def test_to_dict(self) -> None:
        """Verify to_dict returns a copy of the data."""
        doc = Document({"name": "Alice"})
        data = doc.to_dict()
        assert "name" in data
        assert "_id" in data
        # Modifying the copy should not affect the original
        data["name"] = "Bob"
        assert doc.get("name") == "Alice"


class TestDocumentNestedAccess:
    """Test dot-notation access for nested fields."""

    def test_nested_field(self) -> None:
        """Verify accessing a nested field with dot notation."""
        doc = Document({"address": {"city": "Paris", "country": "France"}})
        assert doc.get_nested("address.city") == "Paris"

    def test_deeply_nested_field(self) -> None:
        """Verify accessing a deeply nested field."""
        doc = Document({"a": {"b": {"c": "deep"}}})
        assert doc.get_nested("a.b.c") == "deep"

    def test_missing_nested_field(self) -> None:
        """Verify missing nested paths return None."""
        doc = Document({"name": "Alice"})
        assert doc.get_nested("address.city") is None

    def test_top_level_field(self) -> None:
        """Verify dot notation works for top-level fields too."""
        doc = Document({"name": "Alice"})
        assert doc.get_nested("name") == "Alice"


class TestDocumentComparison:
    """Test document equality and representation."""

    def test_equal_documents(self) -> None:
        """Verify two documents with the same data are equal."""
        data = {"_id": "123", "name": "Alice"}
        doc1 = Document(data)
        doc2 = Document(data)
        assert doc1 == doc2

    def test_unequal_documents(self) -> None:
        """Verify documents with different data are not equal."""
        doc1 = Document({"_id": "1", "name": "Alice"})
        doc2 = Document({"_id": "2", "name": "Bob"})
        assert doc1 != doc2

    def test_not_equal_to_non_document(self) -> None:
        """Verify a document is not equal to a non-Document object."""
        doc = Document({"name": "Alice"})
        assert doc != "not a document"

    def test_repr(self) -> None:
        """Verify the repr includes the data."""
        doc = Document({"_id": "123", "name": "Alice"})
        result = repr(doc)
        assert "Document(" in result
        assert "Alice" in result
