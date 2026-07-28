"""Document module -- the building block of PyDocDB.

Imagine an index card in a filing cabinet. Each card can have whatever
information you want on it -- a person's name, their age, their favorite
color, or even a drawing of their pet. Unlike a spreadsheet where every
row must have the same columns, each index card can be totally different!

A Document is like one of those index cards. It holds key-value pairs
(like "name" -> "Alice") and automatically gets a unique ID stamped on it,
just like how every library book gets a unique barcode.
"""

import uuid
from typing import Any

# Type alias for document data -- a dictionary mapping string keys to any value
DocumentData = dict[str, Any]


def extract_field(data: Any, path: str) -> Any:
    """Extract a nested field value using dot notation.

    Like following directions: "Go to the address, then look for the city."
    The path "address.city" means: look inside "address", then get "city".

    Args:
        data: The data to search through (usually a dict).
        path: A dot-separated path like "address.city".

    Returns:
        The value at the path, or None if not found.

    """
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        else:
            return None
    return current  # pyright: ignore[reportUnknownVariableType]


class Document:
    """A single document in the store, like an index card with a unique ID.

    Each document is a dictionary of fields and values. When you create a
    document, it automatically gets a unique ``_id`` field -- like a barcode
    that no other document in the world will ever have.

    Attributes:
        data: The dictionary holding all the document's fields and values.

    """

    def __init__(self, data: DocumentData | None = None, **kwargs: Any) -> None:
        """Create a new document from a dictionary or keyword arguments.

        If no ``_id`` is provided, one is automatically generated using UUID4
        (a random unique identifier).

        Args:
            data: Optional dictionary of fields and values.
            **kwargs: Additional fields to include in the document.

        """
        self.data: DocumentData = dict(data) if data else {}
        self.data.update(kwargs)

        if "_id" not in self.data:
            self.data["_id"] = str(uuid.uuid4())

    @property
    def id(self) -> str:
        """Return the document's unique identifier.

        Like reading the barcode sticker on a library book -- no two documents
        ever share the same one.

        Returns:
            The ``_id`` field as a string.

        """
        return str(self.data["_id"])

    def get(self, key: str, default: Any = None) -> Any:
        """Get a field's value, returning a default if the field doesn't exist.

        Like reading one line off an index card, and just shrugging with a
        fallback answer if that line was never filled in.

        Args:
            key: The field name to look up.
            default: Value to return if the field isn't found.

        Returns:
            The field's value, or the default.

        """
        return self.data.get(key, default)

    def get_nested(self, path: str) -> Any:
        """Get a value from a nested field using dot notation.

        Think of it like an address on an envelope. "address.city" means
        "look inside the 'address' field, then find the 'city' inside that."

        Args:
            path: A dot-separated path like "address.city".

        Returns:
            The value at the path, or None if any part of the path is missing.

        """
        return extract_field(self.data, path)

    def to_dict(self) -> DocumentData:
        """Return a copy of the document's data as a plain dictionary.

        Like photocopying an index card so you can scribble on the copy without
        changing the original.

        Returns:
            A new dictionary with all the document's fields.

        """
        return dict(self.data)

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"Document({self.data!r})"

    def __eq__(self, other: object) -> bool:
        """Check if two documents are equal by comparing their data."""
        if not isinstance(other, Document):
            return NotImplemented
        return self.data == other.data

    def __hash__(self) -> int:
        """Return a hash based on the document's unique ID."""
        return hash(self.id)
