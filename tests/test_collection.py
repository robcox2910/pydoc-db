"""Tests for the Collection class."""

import pytest

from pydocdb.collection import Collection
from pydocdb.errors import DocumentNotFoundError, DuplicateKeyError

AGE_ALICE = 14
AGE_BOB = 13
AGE_CHARLIE = 15
AGE_THRESHOLD = 13
UPDATE_AGE = 15
EXPECTED_TWO = 2
EXPECTED_THREE = 3


class TestInsert:
    """Test inserting documents into a collection."""

    def test_insert_one(self) -> None:
        """Verify inserting a single document."""
        col = Collection("test")
        doc = col.insert_one({"name": "Alice", "age": AGE_ALICE})
        assert doc.get("name") == "Alice"
        assert len(col) == 1

    def test_insert_generates_id(self) -> None:
        """Verify inserted document gets an _id."""
        col = Collection("test")
        doc = col.insert_one({"name": "Alice"})
        assert doc.id is not None

    def test_insert_duplicate_id_raises(self) -> None:
        """Verify inserting a duplicate _id raises DuplicateKeyError."""
        col = Collection("test")
        col.insert_one({"_id": "same", "name": "Alice"})
        with pytest.raises(DuplicateKeyError, match="same"):
            col.insert_one({"_id": "same", "name": "Bob"})

    def test_insert_many(self) -> None:
        """Verify inserting multiple documents at once."""
        col = Collection("test")
        docs = col.insert_many(
            [
                {"name": "Alice"},
                {"name": "Bob"},
                {"name": "Charlie"},
            ]
        )
        assert len(docs) == EXPECTED_THREE
        assert len(col) == EXPECTED_THREE

    def test_insert_many_is_atomic_on_duplicate(self) -> None:
        """Verify a mid-batch duplicate _id inserts nothing (all-or-nothing)."""
        col = Collection("test")
        col.insert_one({"_id": "x", "name": "Existing"})
        with pytest.raises(DuplicateKeyError):
            col.insert_many(
                [
                    {"name": "Alice"},
                    {"_id": "x", "name": "Clash"},  # collides with existing
                    {"name": "Charlie"},
                ]
            )
        # Nothing from the batch was committed -- only the original doc remains.
        assert len(col) == 1
        assert col.find_by_id("x")["name"] == "Existing"

    def test_insert_many_rejects_duplicate_within_batch(self) -> None:
        """Verify two docs sharing an _id in one batch insert nothing."""
        col = Collection("test")
        with pytest.raises(DuplicateKeyError):
            col.insert_many(
                [
                    {"_id": "dup", "name": "Alice"},
                    {"_id": "dup", "name": "Bob"},
                ]
            )
        assert len(col) == 0


class TestFind:
    """Test finding documents in a collection."""

    def _make_collection(self) -> Collection:
        """Create a collection with test data."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "age": AGE_ALICE})
        col.insert_one({"name": "Bob", "age": AGE_BOB})
        col.insert_one({"name": "Charlie", "age": AGE_CHARLIE})
        return col

    def test_find_all(self) -> None:
        """Verify finding all documents with no query."""
        col = self._make_collection()
        results = col.find()
        assert len(results) == EXPECTED_THREE

    def test_find_with_query(self) -> None:
        """Verify finding documents that match a query."""
        col = self._make_collection()
        results = col.find({"name": "Alice"})
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    def test_find_with_operator(self) -> None:
        """Verify finding with comparison operators."""
        col = self._make_collection()
        results = col.find({"age": {"$gt": AGE_THRESHOLD}})
        assert len(results) == EXPECTED_TWO

    def test_find_one(self) -> None:
        """Verify find_one returns first match."""
        col = self._make_collection()
        result = col.find_one({"name": "Bob"})
        assert result is not None
        assert result["name"] == "Bob"

    def test_find_one_no_match(self) -> None:
        """Verify find_one returns None when no match."""
        col = self._make_collection()
        assert col.find_one({"name": "Nobody"}) is None

    def test_find_by_id(self) -> None:
        """Verify finding a document by its _id."""
        col = Collection("test")
        doc = col.insert_one({"name": "Alice"})
        result = col.find_by_id(doc.id)
        assert result["name"] == "Alice"

    def test_find_by_id_not_found(self) -> None:
        """Verify find_by_id raises when document doesn't exist."""
        col = Collection("test")
        with pytest.raises(DocumentNotFoundError):
            col.find_by_id("nonexistent")

    def test_find_with_projection(self) -> None:
        """Verify find applies projection to results."""
        col = self._make_collection()
        results = col.find({"name": "Alice"}, projection={"name": 1})
        assert "name" in results[0]
        assert "age" not in results[0]

    def test_find_one_with_projection(self) -> None:
        """Verify find_one applies projection."""
        col = self._make_collection()
        result = col.find_one({"name": "Alice"}, projection={"name": 1})
        assert result is not None
        assert "name" in result
        assert "age" not in result

    def test_find_mixed_types_does_not_abort(self) -> None:
        """Verify a range query survives documents with incomparable field types."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "age": AGE_ALICE})
        col.insert_one({"name": "Bob", "age": "teenager"})  # incomparable type
        col.insert_one({"name": "Charlie", "age": AGE_CHARLIE})
        # Without the TypeError guard this whole find would crash.
        results = col.find({"age": {"$gt": AGE_THRESHOLD}})
        names = {r["name"] for r in results}
        assert names == {"Alice", "Charlie"}

    def test_find_exists_matches_present_null(self) -> None:
        """Verify $exists: True matches a field explicitly set to None."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "nickname": None})
        col.insert_one({"name": "Bob"})
        results = col.find({"nickname": {"$exists": True}})
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    def test_find_not_exists_skips_present_null(self) -> None:
        """Verify $exists: False does not match a field that is present but None."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "nickname": None})
        col.insert_one({"name": "Bob"})
        results = col.find({"nickname": {"$exists": False}})
        assert len(results) == 1
        assert results[0]["name"] == "Bob"


class TestUpdate:
    """Test updating documents."""

    def test_update_one(self) -> None:
        """Verify updating a single document."""
        col = Collection("test")
        col.insert_one({"name": "Alice", "age": AGE_ALICE})
        updated = col.update_one({"name": "Alice"}, {"age": UPDATE_AGE})
        assert updated is True
        result = col.find_one({"name": "Alice"})
        assert result is not None
        assert result["age"] == UPDATE_AGE

    def test_update_one_no_match(self) -> None:
        """Verify update_one returns False when no match."""
        col = Collection("test")
        assert col.update_one({"name": "Nobody"}, {"age": UPDATE_AGE}) is False

    def test_update_many(self) -> None:
        """Verify updating multiple documents."""
        col = Collection("test")
        col.insert_one({"team": "A", "score": 0})
        col.insert_one({"team": "A", "score": 0})
        col.insert_one({"team": "B", "score": 0})
        count = col.update_many({"team": "A"}, {"score": 1})
        assert count == EXPECTED_TWO

    def test_update_one_ignores_id_change(self) -> None:
        """Verify update_one refuses to change _id, keeping the document findable."""
        col = Collection("test")
        doc = col.insert_one({"_id": "orig", "name": "Alice"})
        col.update_one({"name": "Alice"}, {"_id": "hacked", "age": UPDATE_AGE})
        # _id is unchanged and the document is still findable by its real id.
        assert doc.id == "orig"
        result = col.find_by_id("orig")
        assert result["age"] == UPDATE_AGE
        with pytest.raises(DocumentNotFoundError):
            col.find_by_id("hacked")

    def test_update_many_ignores_id_change(self) -> None:
        """Verify update_many does not desync documents by rewriting _id."""
        col = Collection("test")
        col.insert_one({"_id": "a", "team": "A"})
        col.insert_one({"_id": "b", "team": "A"})
        col.update_many({"team": "A"}, {"_id": "clash", "score": 1})
        # Both documents keep their original ids (no collision, no lost cards).
        assert len(col) == EXPECTED_TWO
        assert col.find_by_id("a")["score"] == 1
        assert col.find_by_id("b")["score"] == 1


class TestDelete:
    """Test deleting documents."""

    def test_delete_one(self) -> None:
        """Verify deleting a single document."""
        col = Collection("test")
        col.insert_one({"name": "Alice"})
        col.insert_one({"name": "Bob"})
        deleted = col.delete_one({"name": "Alice"})
        assert deleted is True
        assert len(col) == 1

    def test_delete_one_no_match(self) -> None:
        """Verify delete_one returns False when no match."""
        col = Collection("test")
        assert col.delete_one({"name": "Nobody"}) is False

    def test_delete_many(self) -> None:
        """Verify deleting multiple documents."""
        col = Collection("test")
        col.insert_one({"team": "A"})
        col.insert_one({"team": "A"})
        col.insert_one({"team": "B"})
        count = col.delete_many({"team": "A"})
        assert count == EXPECTED_TWO
        assert len(col) == 1


class TestCount:
    """Test counting documents."""

    def test_count_all(self) -> None:
        """Verify counting all documents."""
        col = Collection("test")
        col.insert_one({"name": "Alice"})
        col.insert_one({"name": "Bob"})
        assert col.count() == EXPECTED_TWO

    def test_count_with_query(self) -> None:
        """Verify counting documents matching a query."""
        col = Collection("test")
        col.insert_one({"team": "A"})
        col.insert_one({"team": "A"})
        col.insert_one({"team": "B"})
        assert col.count({"team": "A"}) == EXPECTED_TWO


class TestCollectionMisc:
    """Test other collection operations."""

    def test_clear(self) -> None:
        """Verify clearing removes all documents."""
        col = Collection("test")
        col.insert_one({"name": "Alice"})
        col.clear()
        assert len(col) == 0

    def test_to_list(self) -> None:
        """Verify to_list exports all documents."""
        col = Collection("test")
        col.insert_one({"name": "Alice"})
        col.insert_one({"name": "Bob"})
        data = col.to_list()
        assert len(data) == EXPECTED_TWO

    def test_repr(self) -> None:
        """Verify repr includes name and count."""
        col = Collection("students")
        assert "students" in repr(col)


class TestCardsAreCopiedAllTheWayDown:
    """Scribbling on a copy, even on a list inside it, never changes the filed card.

    Regression: cards used to be copied only one level deep, so a list inside
    a card was shared between the caller and the collection.
    """

    def test_changing_a_found_card_leaves_the_filed_card_alone(self) -> None:
        """Verify changing a nested list in a find() result doesn't change the stored card."""
        col = Collection("test")
        col.insert_one({"_id": "1", "tags": ["red"]})
        found = col.find()[0]
        found["tags"].append("blue")
        assert col.find_by_id("1") == {"_id": "1", "tags": ["red"]}

    def test_changing_the_inserted_dict_leaves_the_filed_card_alone(self) -> None:
        """Verify changing a nested list in the dict passed to insert_one doesn't change the card."""
        col = Collection("test")
        tags = ["red"]
        col.insert_one({"_id": "1", "tags": tags})
        tags.append("blue")
        assert col.find_by_id("1") == {"_id": "1", "tags": ["red"]}

    def test_changing_the_update_dict_leaves_the_filed_card_alone(self) -> None:
        """Verify changing a nested list in an update payload after update_one doesn't change the card."""
        col = Collection("test")
        col.insert_one({"_id": "1"})
        changes = {"tags": ["red"]}
        col.update_one({"_id": "1"}, changes)
        changes["tags"].append("blue")
        assert col.find_by_id("1") == {"_id": "1", "tags": ["red"]}

    def test_changing_what_insert_one_returns_leaves_the_filed_card_alone(self) -> None:
        """Verify changing a nested list in the Document insert_one returns doesn't change the card."""
        col = Collection("test")
        returned = col.insert_one({"_id": "1", "tags": ["red"]})
        returned.data["tags"].append("blue")
        assert col.find_by_id("1") == {"_id": "1", "tags": ["red"]}

    def test_changing_what_insert_many_returns_leaves_the_filed_cards_alone(self) -> None:
        """Verify changing a nested list in a Document insert_many returns doesn't change the card."""
        col = Collection("test")
        returned = col.insert_many([{"_id": "1", "tags": ["red"]}])
        returned[0].data["tags"].append("blue")
        assert col.find_by_id("1") == {"_id": "1", "tags": ["red"]}

    def test_cards_changed_by_one_update_many_do_not_share_a_list(self) -> None:
        """Verify each card update_many changes gets its own copy of a nested value."""
        col = Collection("test")
        col.insert_many([{"_id": "1", "team": "A"}, {"_id": "2", "team": "A"}])
        col.update_many({"team": "A"}, {"tags": ["red"]})
        # Reach the stored card the way a buggy caller could: through a returned Document.
        col._documents["1"].data["tags"].append("blue")
        assert col.find_by_id("2") == {"_id": "2", "team": "A", "tags": ["red"]}
