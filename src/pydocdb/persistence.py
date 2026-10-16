"""Persistence module -- save and load collections to disk.

Imagine you've spent hours organizing your trading card collection
into perfect piles on your desk. When you go to bed, you need to put
everything in a box so it's safe. The next morning, you take everything
back out and it's exactly how you left it.

That's what persistence does for PyDocDB! It saves your documents to
a JSON file on disk (putting cards in the box) and loads them back
later (taking them out again). Without persistence, all your data
would disappear when your program stops running.
"""

import json
from pathlib import Path
from typing import Any

from pydocdb.atomic import atomic_write_text
from pydocdb.collection import Collection
from pydocdb.document import DocumentData
from pydocdb.errors import PersistenceError


def save_collection(collection: Collection, file_path: str | Path) -> None:
    """Save a collection to a JSON file on disk.

    Like putting all your index cards into a labeled box and storing it
    on a shelf. The box (file) keeps everything safe even when the
    program isn't running.

    Note:
        JSON can only store text, numbers, lists, and dicts. Values it doesn't
        understand (like a ``datetime``) are written out as their text form, so
        after a save-and-load round trip they come back as strings, not their
        original type.

    Args:
        collection: The collection to save.
        file_path: Where to save the file (e.g., "students.json").

    Raises:
        PersistenceError: If the file cannot be written.

    """
    path = Path(file_path)
    data: dict[str, Any] = {
        "name": collection.name,
        "documents": collection.to_list(),
        "indexes": collection.list_indexes(),
    }

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, json.dumps(data, indent=2, default=str))
    except OSError as exc:
        msg = f"Failed to save collection to '{path}': {exc}"
        raise PersistenceError(msg) from exc


def load_collection(file_path: str | Path) -> Collection:
    """Load a collection from a JSON file on disk.

    Like taking a box of index cards off the shelf and laying them all
    out on your desk again, exactly as they were.

    Args:
        file_path: Path to the JSON file to load.

    Returns:
        A new Collection populated with the saved documents.

    Raises:
        PersistenceError: If the file cannot be read or is invalid.

    """
    path = Path(file_path)

    try:
        text = path.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"Failed to load collection from '{path}': {exc}"
        raise PersistenceError(msg) from exc

    name: str = data.get("name", "unnamed")
    documents: list[DocumentData] = data.get("documents", [])
    index_fields: list[str] = data.get("indexes", [])

    collection = Collection(str(name))
    for doc_data in documents:
        collection.insert_one(doc_data)

    for field in index_fields:
        collection.create_index(str(field))

    return collection
