"""Tests for persistence (save/load)."""

import os
from pathlib import Path

import pytest

from pydocdb.collection import Collection
from pydocdb.errors import PersistenceError
from pydocdb.persistence import load_collection, save_collection

AGE_ALICE = 14
AGE_BOB = 13
EXPECTED_TWO = 2


class TestSaveAndLoad:
    """Test saving and loading collections to disk."""

    def test_save_and_load(self, tmp_path: Path) -> None:
        """Verify a collection survives a save/load round-trip."""
        col = Collection("students")
        col.insert_one({"_id": "1", "name": "Alice", "age": AGE_ALICE})
        col.insert_one({"_id": "2", "name": "Bob", "age": AGE_BOB})

        file_path = tmp_path / "students.json"
        save_collection(col, file_path)

        loaded = load_collection(file_path)
        assert loaded.name == "students"
        assert len(loaded) == EXPECTED_TWO

    def test_preserves_data(self, tmp_path: Path) -> None:
        """Verify document data is preserved after save/load."""
        col = Collection("test")
        col.insert_one({"_id": "1", "name": "Alice", "age": AGE_ALICE})

        file_path = tmp_path / "test.json"
        save_collection(col, file_path)

        loaded = load_collection(file_path)
        doc = loaded.find_one({"name": "Alice"})
        assert doc is not None
        assert doc["age"] == AGE_ALICE

    def test_preserves_indexes(self, tmp_path: Path) -> None:
        """Verify indexes are recreated after loading."""
        col = Collection("test")
        col.insert_one({"name": "Alice"})
        col.create_index("name")

        file_path = tmp_path / "test.json"
        save_collection(col, file_path)

        loaded = load_collection(file_path)
        assert "name" in loaded.list_indexes()

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Verify save creates parent directories if needed."""
        col = Collection("test")
        col.insert_one({"name": "Alice"})

        file_path = tmp_path / "subdir" / "deep" / "test.json"
        save_collection(col, file_path)
        assert file_path.exists()

    def test_load_nonexistent_raises(self) -> None:
        """Verify loading a non-existent file raises PersistenceError."""
        with pytest.raises(PersistenceError, match="Failed to load"):
            load_collection("/nonexistent/path/file.json")

    def test_load_invalid_json_raises(self, tmp_path: Path) -> None:
        """Verify loading invalid JSON raises PersistenceError."""
        file_path = tmp_path / "bad.json"
        file_path.write_text("not valid json {{{", encoding="utf-8")
        with pytest.raises(PersistenceError, match="Failed to load"):
            load_collection(file_path)


class _SimulatedCrashError(OSError):
    """Stands in for the power going out part-way through a save."""


def test_interrupted_save_keeps_the_previous_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: a crash mid-save used to leave a truncated, unloadable file."""
    col = Collection("c")
    col.insert_one({"_id": "1", "v": "old"})
    path = tmp_path / "data.json"
    save_collection(col, path)
    before = path.read_bytes()
    col.insert_one({"_id": "2", "v": "new"})

    def write_half_then_crash(self: Path, data: str, *_args: object, **_kwargs: object) -> int:
        with self.open("w", encoding="utf-8") as handle:
            handle.write(data[: len(data) // 2])
        raise _SimulatedCrashError

    def crash(*_args: object) -> None:
        raise _SimulatedCrashError

    monkeypatch.setattr(Path, "write_text", write_half_then_crash)
    monkeypatch.setattr(os, "replace", crash)
    with pytest.raises((OSError, PersistenceError)):
        save_collection(col, path)
    monkeypatch.undo()
    assert path.read_bytes() == before
    load_collection(path)
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


WRONG_SHAPES = [
    "{}",
    "[]",
    '{"name": "pets", "documents": "nope"}',
    '{"name": "pets", "documents": [1]}',
]


class TestWrongShapeFiles:
    """Valid JSON that isn't a saved collection is refused, never loaded as empty."""

    @pytest.mark.parametrize("content", WRONG_SHAPES)
    def test_wrong_shape_raises_persistence_error_naming_the_file(
        self, tmp_path: Path, content: str
    ) -> None:
        """Loading it raises PersistenceError with the file name, so it can't be overwritten."""
        path = tmp_path / "saved.json"
        path.write_text(content, encoding="utf-8")
        with pytest.raises(PersistenceError, match=r"saved\.json"):
            load_collection(path)
