"""Query matching engine for PyDocDB.

Imagine you walk into a library and tell the librarian: "I want all books
that are about science AND have more than 100 pages." The librarian goes
through every book and checks each one against your criteria.

That's exactly what the query engine does! You give it a set of conditions
(called a "query"), and it checks each document to see if it matches.

Queries use a dictionary format inspired by MongoDB:

    {"age": {"$gt": 18}}           -- age greater than 18
    {"name": "Alice"}              -- name equals "Alice" (shorthand for $eq)
    {"$and": [{"a": 1}, {"b": 2}]} -- both conditions must be true
"""

from typing import Any

from pydocdb.document import Document
from pydocdb.errors import InvalidQueryError
from pydocdb.operators import OPERATORS


def matches(doc: Document, query: dict[str, Any]) -> bool:
    """Check if a document matches a query.

    This is the main entry point for the query engine. It takes a document
    and a query dictionary, and returns True if the document satisfies all
    the conditions in the query.

    Args:
        doc: The document to check.
        query: A dictionary of field conditions to match against.

    Returns:
        True if the document matches all conditions.

    Raises:
        InvalidQueryError: If the query contains an unknown operator.

    """
    for key, condition in query.items():
        if key == "$and":
            if not _match_and(doc, condition):
                return False
        elif key == "$or":
            if not _match_or(doc, condition):
                return False
        elif key == "$not":
            if not _match_not(doc, condition):
                return False
        elif not _match_field(doc, key, condition):
            return False
    return True


def _match_field(doc: Document, field: str, condition: Any) -> bool:
    """Check if a single field in the document matches its condition.

    If the condition is a plain value (not a dict with operators), it's
    treated as an equality check. If it's a dict, each key should be an
    operator like "$gt" or "$lt".

    Args:
        doc: The document to check.
        field: The field name (supports dot notation for nested fields).
        condition: The value or operator dict to match against.

    Returns:
        True if the field matches the condition.

    Raises:
        InvalidQueryError: If an unknown operator is used.

    """
    field_value = doc.get_nested(field)

    # Simple equality: {"name": "Alice"}
    if not isinstance(condition, dict):
        return field_value == condition  # type: ignore[no-any-return]

    # Operator-based: {"age": {"$gt": 18, "$lt": 65}}
    for op, value in condition.items():  # pyright: ignore[reportUnknownVariableType]
        if op not in OPERATORS:
            msg = f"Unknown query operator: {op}"
            raise InvalidQueryError(msg)
        operator_fn = OPERATORS[op]
        if not operator_fn(field_value, value):
            return False
    return True


def _match_and(doc: Document, conditions: Any) -> bool:
    """Match a $and condition -- ALL sub-conditions must be true.

    Like saying: "The book must be about science AND have more than 100 pages."
    Both conditions must be satisfied.

    Args:
        doc: The document to check.
        conditions: A list of query dictionaries.

    Returns:
        True if ALL conditions match.

    Raises:
        InvalidQueryError: If conditions is not a list.

    """
    if not isinstance(conditions, list):
        msg = "$and requires a list of conditions"
        raise InvalidQueryError(msg)
    return all(matches(doc, cond) for cond in conditions)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]


def _match_or(doc: Document, conditions: Any) -> bool:
    """Match a $or condition -- AT LEAST ONE sub-condition must be true.

    Like saying: "The book can be about science OR about math."
    At least one condition must be satisfied.

    Args:
        doc: The document to check.
        conditions: A list of query dictionaries.

    Returns:
        True if ANY condition matches.

    Raises:
        InvalidQueryError: If conditions is not a list.

    """
    if not isinstance(conditions, list):
        msg = "$or requires a list of conditions"
        raise InvalidQueryError(msg)
    return any(matches(doc, cond) for cond in conditions)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]


def _match_not(doc: Document, condition: Any) -> bool:
    """Match a $not condition -- the sub-condition must NOT be true.

    Like saying: "Find me books that are NOT about cooking."

    Args:
        doc: The document to check.
        condition: A query dictionary that must NOT match.

    Returns:
        True if the condition does NOT match.

    Raises:
        InvalidQueryError: If condition is not a dictionary.

    """
    if not isinstance(condition, dict):
        msg = "$not requires a dictionary condition"
        raise InvalidQueryError(msg)
    return not matches(doc, condition)  # pyright: ignore[reportUnknownArgumentType]
