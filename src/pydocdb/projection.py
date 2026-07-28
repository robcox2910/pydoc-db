"""Field projection for PyDocDB.

Imagine you're reading a newspaper. Sometimes you only want to see the
headlines without reading the entire article. Projection works the same
way -- it lets you pick which fields you want to see from a document,
so you don't have to deal with all the extra information.

You can either:
- **Include** only the fields you want (like "show me just the name and age")
- **Exclude** specific fields (like "show me everything except the password")

The ``_id`` field is always included by default (unless you explicitly exclude it).
"""

from pydocdb.document import DocumentData, extract_field

__all__ = ["EXCLUDE", "INCLUDE", "apply_projection", "extract_field"]

# Projection values: 1 means include, 0 means exclude
INCLUDE: int = 1
EXCLUDE: int = 0


def apply_projection(
    doc_data: DocumentData,
    projection: dict[str, int],
) -> DocumentData:
    """Apply a field projection to a document's data.

    Like choosing which columns to show in a spreadsheet -- you can pick
    specific columns to display or hide columns you don't need.

    Args:
        doc_data: The full document data dictionary.
        projection: A dict mapping field names to 1 (include) or 0 (exclude).

    Returns:
        A new dictionary with only the requested fields.

    """
    if not projection:
        return dict(doc_data)

    # Determine if this is an inclusion or exclusion projection
    projection_values = {v for k, v in projection.items() if k != "_id"}

    if INCLUDE in projection_values:
        return _apply_inclusion(doc_data, projection)
    return _apply_exclusion(doc_data, projection)


def _apply_inclusion(
    doc_data: DocumentData,
    projection: dict[str, int],
) -> DocumentData:
    """Apply an inclusion projection -- only keep listed fields.

    Args:
        doc_data: The full document data.
        projection: Fields to include (value=1).

    Returns:
        A dict with only the included fields.

    """
    result: DocumentData = {}

    # _id is included by default unless explicitly excluded
    if projection.get("_id", INCLUDE) != EXCLUDE and "_id" in doc_data:
        result["_id"] = doc_data["_id"]

    for field, value in projection.items():
        if field == "_id":
            continue
        if value == INCLUDE and field in doc_data:
            result[field] = doc_data[field]

    return result


def _apply_exclusion(
    doc_data: DocumentData,
    projection: dict[str, int],
) -> DocumentData:
    """Apply an exclusion projection -- remove listed fields.

    Args:
        doc_data: The full document data.
        projection: Fields to exclude (value=0).

    Returns:
        A dict with the excluded fields removed.

    """
    result: DocumentData = dict(doc_data)

    for field, value in projection.items():
        if value == EXCLUDE and field in result:
            del result[field]

    return result
