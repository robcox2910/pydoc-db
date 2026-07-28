"""Query operator implementations for PyDocDB.

Think of these operators like the different ways a librarian can search
for books. You might ask:
- "Find books that cost EXACTLY $10" ($eq)
- "Find books with MORE THAN 200 pages" ($gt)
- "Find books that are NOT science fiction" ($ne)
- "Find books that are EITHER fantasy OR mystery" ($in)

Each operator is a small function that answers a yes-or-no question:
"Does this value match the condition?"
"""

from typing import Any

from pydocdb.errors import InvalidQueryError


def op_eq(field_value: Any, query_value: Any) -> bool:
    """Check if a field equals the query value.

    Like asking: "Is this book's color exactly 'red'?"

    Args:
        field_value: The actual value from the document.
        query_value: The value to compare against.

    Returns:
        True if they are equal.

    """
    return field_value == query_value  # type: ignore[no-any-return]


def op_ne(field_value: Any, query_value: Any) -> bool:
    """Check if a field does NOT equal the query value.

    Like asking: "Is this book's color anything OTHER than 'red'?"

    Args:
        field_value: The actual value from the document.
        query_value: The value to compare against.

    Returns:
        True if they are not equal.

    """
    return field_value != query_value  # type: ignore[no-any-return]


def op_gt(field_value: Any, query_value: Any) -> bool:
    """Check if a field is greater than the query value.

    Like asking: "Does this book have MORE than 200 pages?"

    Args:
        field_value: The actual value from the document.
        query_value: The value to compare against.

    Returns:
        True if field_value > query_value.

    """
    if field_value is None:
        return False
    try:
        return field_value > query_value  # type: ignore[no-any-return]
    except TypeError:
        # Comparing apples to oranges (e.g. a number to a word) just
        # doesn't match -- like MongoDB, we skip it instead of crashing.
        return False


def op_gte(field_value: Any, query_value: Any) -> bool:
    """Check if a field is greater than or equal to the query value.

    Like asking: "Does this book have 200 pages or more?"

    Args:
        field_value: The actual value from the document.
        query_value: The value to compare against.

    Returns:
        True if field_value >= query_value.

    """
    if field_value is None:
        return False
    try:
        return field_value >= query_value  # type: ignore[no-any-return]
    except TypeError:
        return False


def op_lt(field_value: Any, query_value: Any) -> bool:
    """Check if a field is less than the query value.

    Like asking: "Does this book have FEWER than 200 pages?"

    Args:
        field_value: The actual value from the document.
        query_value: The value to compare against.

    Returns:
        True if field_value < query_value.

    """
    if field_value is None:
        return False
    try:
        return field_value < query_value  # type: ignore[no-any-return]
    except TypeError:
        return False


def op_lte(field_value: Any, query_value: Any) -> bool:
    """Check if a field is less than or equal to the query value.

    Like asking: "Does this book have 200 pages or fewer?"

    Args:
        field_value: The actual value from the document.
        query_value: The value to compare against.

    Returns:
        True if field_value <= query_value.

    """
    if field_value is None:
        return False
    try:
        return field_value <= query_value  # type: ignore[no-any-return]
    except TypeError:
        return False


def op_in(field_value: Any, query_value: Any) -> bool:
    """Check if a field's value is in a list of acceptable values.

    Like asking: "Is this book's genre one of: fantasy, mystery, or sci-fi?"

    Args:
        field_value: The actual value from the document.
        query_value: A list of acceptable values.

    Returns:
        True if field_value is found in the list.

    Raises:
        InvalidQueryError: If query_value is not a list.

    """
    if not isinstance(query_value, list):
        msg = "$in requires a list of values"
        raise InvalidQueryError(msg)
    return field_value in query_value


def op_exists(field_present: Any, query_value: Any) -> bool:
    """Check whether a field exists (or doesn't exist) in a document.

    Like asking: "Does this index card even HAVE a 'phone number' line on it?"
    A line that's been left blank still counts as being there -- what matters
    is whether the field is present, not what's written in it.

    Args:
        field_present: Whether the field is present in the document (True/False).
        query_value: True to check if the field exists, False to check if it doesn't.

    Returns:
        True if the existence check passes.

    """
    return bool(field_present) == bool(query_value)


# Registry mapping operator names to their functions
OPERATORS: dict[str, Any] = {
    "$eq": op_eq,
    "$ne": op_ne,
    "$gt": op_gt,
    "$gte": op_gte,
    "$lt": op_lt,
    "$lte": op_lte,
    "$in": op_in,
    "$exists": op_exists,
}
