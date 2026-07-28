"""Simple indexing for PyDocDB.

Think about the index at the back of a textbook. Instead of flipping
through every single page to find "photosynthesis," you look it up in
the index and it tells you exactly which pages to go to. Much faster!

A database index works the same way. Without an index, finding all
documents where city="Paris" means checking EVERY document (called a
"full scan"). With an index on the "city" field, we keep a lookup table
that maps each city to the documents that have it, so we can jump
straight to the right ones.
"""

from typing import Any

from pydocdb.document import Document, extract_field


class Index:
    """An index on a single field for fast lookups.

    Like a book's index, it maps values to document IDs so you can find
    documents without scanning through all of them.

    Attributes:
        field: The field name this index covers.

    """

    def __init__(self, field: str) -> None:
        """Create a new index for the given field.

        Args:
            field: The field to index (supports dot notation for nested fields).

        """
        self.field: str = field
        # Maps field values to sets of document IDs
        self._entries: dict[Any, set[str]] = {}

    def add(self, doc: Document) -> None:
        """Add a document to this index.

        Extract the indexed field's value from the document and record
        which document ID has that value.

        Args:
            doc: The document to index.

        """
        value = extract_field(doc.data, self.field)
        if value is None:
            return

        # Convert unhashable types to something hashable
        key = make_hashable(value)
        if key not in self._entries:
            self._entries[key] = set()
        self._entries[key].add(doc.id)

    def remove(self, doc: Document) -> None:
        """Remove a document from this index.

        Args:
            doc: The document to remove.

        """
        value = extract_field(doc.data, self.field)
        if value is None:
            return

        key = make_hashable(value)
        if key in self._entries:
            self._entries[key].discard(doc.id)
            if not self._entries[key]:
                del self._entries[key]

    def find(self, value: Any) -> set[str]:
        """Find all document IDs that have the given value for this field.

        Args:
            value: The value to look up.

        Returns:
            A set of document IDs that match.

        """
        key = make_hashable(value)
        if key in self._entries:
            return set(self._entries[key])
        return set()

    def clear(self) -> None:
        """Remove all entries from the index."""
        self._entries.clear()

    def __len__(self) -> int:
        """Return the number of unique values in the index."""
        return len(self._entries)

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        count = sum(len(ids) for ids in self._entries.values())
        return f"Index(field={self.field!r}, unique_values={len(self)}, documents={count})"


def make_hashable(value: Any) -> Any:
    """Convert a value to something that can be used as a dict key.

    Lists and dicts aren't hashable in Python, so we convert them
    to tuples and frozensets.

    Args:
        value: Any value to make hashable.

    Returns:
        A hashable version of the value.

    """
    if isinstance(value, list):
        return tuple(value)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
    if isinstance(value, dict):
        return tuple(sorted(value.items()))  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
    return value
