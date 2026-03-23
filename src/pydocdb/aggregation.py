"""Aggregation pipeline for PyDocDB.

Imagine you have a huge collection of trading cards. You might want to:
1. First, pick out only the rare cards ($match)
2. Then, group them by type -- Fire, Water, Grass ($group)
3. Sort the groups by how many cards each has ($sort)
4. Only look at the top 3 groups ($limit)
5. Just count how many groups there are ($count)

That's an aggregation pipeline! It's a series of steps (called "stages")
that process your documents one step at a time. Each stage takes the
output of the previous stage and transforms it.
"""

from typing import Any

from pydocdb.document import Document, DocumentData
from pydocdb.errors import InvalidPipelineError
from pydocdb.projection import extract_field
from pydocdb.query import matches


def aggregate(
    documents: list[DocumentData],
    pipeline: list[dict[str, Any]],
) -> list[DocumentData]:
    """Run an aggregation pipeline on a list of documents.

    Process documents through a series of stages, where each stage
    transforms the data in some way.

    Args:
        documents: The input documents to process.
        pipeline: A list of stage dictionaries (e.g., [{"$match": {...}}, {"$sort": {...}}]).

    Returns:
        The resulting documents after all stages have been applied.

    Raises:
        InvalidPipelineError: If a stage is unknown or malformed.

    """
    current: list[DocumentData] = list(documents)

    for stage in pipeline:
        if len(stage) != 1:
            msg = "Each pipeline stage must have exactly one operator"
            raise InvalidPipelineError(msg)

        stage_name = next(iter(stage))
        stage_value = stage[stage_name]

        if stage_name == "$match":
            current = _stage_match(current, stage_value)
        elif stage_name == "$group":
            current = _stage_group(current, stage_value)
        elif stage_name == "$sort":
            current = _stage_sort(current, stage_value)
        elif stage_name == "$limit":
            current = _stage_limit(current, stage_value)
        elif stage_name == "$count":
            current = _stage_count(current, stage_value)
        else:
            msg = f"Unknown pipeline stage: {stage_name}"
            raise InvalidPipelineError(msg)

    return current


def _stage_match(
    documents: list[DocumentData],
    query: dict[str, Any],
) -> list[DocumentData]:
    """Filter documents that match a query -- like picking cards from a pile.

    Args:
        documents: Input documents.
        query: A query dictionary (same format as Collection.find).

    Returns:
        Only the documents that match the query.

    """
    return [doc for doc in documents if matches(Document(doc), query)]


def _stage_group(
    documents: list[DocumentData],
    group_spec: dict[str, Any],
) -> list[DocumentData]:
    """Group documents by a field and compute aggregations.

    Like sorting your cards into piles by type, then counting each pile.

    The ``_id`` field in the spec tells us what to group by.
    Other fields define accumulators:
    - ``$sum``: Add up values (use 1 to count)
    - ``$avg``: Calculate the average
    - ``$min``: Find the smallest value
    - ``$max``: Find the largest value

    Args:
        documents: Input documents.
        group_spec: A dict with ``_id`` (group key) and accumulator fields.

    Returns:
        One document per group with the computed values.

    Raises:
        InvalidPipelineError: If ``_id`` is missing from the spec.

    """
    if "_id" not in group_spec:
        msg = "$group stage requires an '_id' field"
        raise InvalidPipelineError(msg)

    group_key = group_spec["_id"]

    # Build groups
    groups: dict[Any, list[DocumentData]] = {}
    for doc in documents:
        if group_key is None:
            key: Any = None
        elif isinstance(group_key, str) and group_key.startswith("$"):
            key = extract_field(doc, group_key[1:])
        else:
            key = group_key

        # Make the key hashable
        hashable_key = _make_hashable_key(key)
        if hashable_key not in groups:
            groups[hashable_key] = []
        groups[hashable_key].append(doc)

    # Apply accumulators to each group
    results: list[DocumentData] = []
    for key_value, group_docs in groups.items():
        result: DocumentData = {"_id": key_value}

        for field, accumulator in group_spec.items():
            if field == "_id":
                continue
            if isinstance(accumulator, dict):
                acc_dict: dict[str, Any] = dict(accumulator)  # pyright: ignore[reportUnknownArgumentType]
                result[field] = _apply_accumulator(acc_dict, group_docs)

        results.append(result)

    return results


def _apply_accumulator(
    accumulator: dict[str, Any],
    group_docs: list[DocumentData],
) -> Any:
    """Apply a single accumulator to a group of documents.

    Args:
        accumulator: A dict like ``{"$sum": "$price"}`` or ``{"$sum": 1}``.
        group_docs: The documents in this group.

    Returns:
        The computed value.

    Raises:
        InvalidPipelineError: If the accumulator operator is unknown.

    """
    op = next(iter(accumulator))
    value_spec = accumulator[op]

    if op == "$sum":
        return _acc_sum(value_spec, group_docs)
    if op == "$avg":
        return _acc_avg(value_spec, group_docs)
    if op == "$min":
        return _acc_min(value_spec, group_docs)
    if op == "$max":
        return _acc_max(value_spec, group_docs)

    msg = f"Unknown accumulator: {op}"
    raise InvalidPipelineError(msg)


def _acc_sum(value_spec: Any, docs: list[DocumentData]) -> int | float:
    """Compute sum for a group.

    Args:
        value_spec: Either a number (like 1 for counting) or a field reference like "$price".
        docs: The documents in the group.

    Returns:
        The sum.

    """
    if isinstance(value_spec, (int, float)):
        return value_spec * len(docs)

    if isinstance(value_spec, str) and value_spec.startswith("$"):
        field = value_spec[1:]
        total: int | float = 0
        for doc in docs:
            val = extract_field(doc, field)
            if isinstance(val, (int, float)):
                total += val
        return total

    return 0


def _acc_avg(value_spec: Any, docs: list[DocumentData]) -> float:
    """Compute average for a group.

    Args:
        value_spec: A field reference like "$price".
        docs: The documents in the group.

    Returns:
        The average, or 0.0 if no valid values.

    """
    if isinstance(value_spec, str) and value_spec.startswith("$"):
        field = value_spec[1:]
        values: list[float] = []
        for doc in docs:
            val = extract_field(doc, field)
            if isinstance(val, (int, float)):
                values.append(float(val))
        if values:
            return sum(values) / len(values)
    return 0.0


def _acc_min(value_spec: Any, docs: list[DocumentData]) -> Any:
    """Compute minimum for a group.

    Args:
        value_spec: A field reference like "$price".
        docs: The documents in the group.

    Returns:
        The minimum value, or None if no valid values.

    """
    if isinstance(value_spec, str) and value_spec.startswith("$"):
        field = value_spec[1:]
        values: list[Any] = []
        for doc in docs:
            val = extract_field(doc, field)
            if val is not None:
                values.append(val)
        if values:
            return min(values)
    return None


def _acc_max(value_spec: Any, docs: list[DocumentData]) -> Any:
    """Compute maximum for a group.

    Args:
        value_spec: A field reference like "$price".
        docs: The documents in the group.

    Returns:
        The maximum value, or None if no valid values.

    """
    if isinstance(value_spec, str) and value_spec.startswith("$"):
        field = value_spec[1:]
        values: list[Any] = []
        for doc in docs:
            val = extract_field(doc, field)
            if val is not None:
                values.append(val)
        if values:
            return max(values)
    return None


def _stage_sort(
    documents: list[DocumentData],
    sort_spec: dict[str, int],
) -> list[DocumentData]:
    """Sort documents by one or more fields.

    Like arranging your cards in order -- alphabetically by name,
    or by number from highest to lowest.

    Args:
        documents: Input documents.
        sort_spec: A dict mapping field names to 1 (ascending) or -1 (descending).

    Returns:
        The sorted list of documents.

    """
    result = list(documents)
    # Apply sorts in reverse order so first key is primary
    for field in reversed(sort_spec):
        direction = sort_spec[field]
        is_reverse = direction == -1
        result.sort(
            key=lambda doc, f=field: _sort_key(doc, f),  # type: ignore[misc]
            reverse=is_reverse,
        )
    return result


def _sort_key(doc: DocumentData, field: str) -> Any:
    """Get a sort-safe key for a document field.

    Args:
        doc: The document data.
        field: The field to sort by.

    Returns:
        The value to sort by, with None values sorted last.

    """
    val = extract_field(doc, field)
    if val is None:
        return (1, "")
    return (0, val)


def _stage_limit(
    documents: list[DocumentData],
    limit: Any,
) -> list[DocumentData]:
    """Limit the number of documents -- like looking at only the top N cards.

    Args:
        documents: Input documents.
        limit: Maximum number of documents to return.

    Returns:
        At most ``limit`` documents.

    Raises:
        InvalidPipelineError: If limit is not a positive integer.

    """
    if not isinstance(limit, int) or limit < 1:
        msg = "$limit requires a positive integer"
        raise InvalidPipelineError(msg)
    return documents[:limit]


def _stage_count(
    documents: list[DocumentData],
    field_name: Any,
) -> list[DocumentData]:
    """Count the number of documents and store the result in a named field.

    Like counting how many cards are in a pile and writing the number down.

    Args:
        documents: Input documents.
        field_name: The name of the field to store the count in.

    Returns:
        A single-element list with the count.

    Raises:
        InvalidPipelineError: If field_name is not a string.

    """
    if not isinstance(field_name, str):
        msg = "$count requires a string field name"
        raise InvalidPipelineError(msg)
    return [{field_name: len(documents)}]


def _make_hashable_key(value: Any) -> Any:
    """Convert a value to something hashable for use as a group key.

    Args:
        value: Any value.

    Returns:
        A hashable version of the value.

    """
    if isinstance(value, list):
        return tuple(value)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
    if isinstance(value, dict):
        return tuple(sorted(value.items()))  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
    return value
