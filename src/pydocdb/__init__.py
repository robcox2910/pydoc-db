"""PyDocDB -- an educational document store for kids aged 12+.

PyDocDB is a document database (like MongoDB) built from scratch in Python.
It stores JSON-like documents without requiring a fixed schema -- each
document can have different fields, just like how every index card in a
filing cabinet can have different information on it.

Quick start::

    from pydocdb import Collection

    students = Collection("students")
    students.insert_one({"name": "Alice", "age": 14, "grade": "9th"})
    students.insert_one({"name": "Bob", "age": 13, "hobby": "chess"})

    # Find students older than 13
    results = students.find({"age": {"$gt": 13}})
"""

from pydocdb.aggregation import aggregate
from pydocdb.collection import Collection
from pydocdb.document import Document, DocumentData
from pydocdb.errors import (
    CollectionExistsError,
    DocumentNotFoundError,
    DuplicateKeyError,
    InvalidFieldError,
    InvalidPipelineError,
    InvalidQueryError,
    PersistenceError,
    PyDocDBError,
)
from pydocdb.indexing import Index
from pydocdb.persistence import load_collection, save_collection

__all__: list[str] = [
    "Collection",
    "CollectionExistsError",
    "Document",
    "DocumentData",
    "DocumentNotFoundError",
    "DuplicateKeyError",
    "Index",
    "InvalidFieldError",
    "InvalidPipelineError",
    "InvalidQueryError",
    "PersistenceError",
    "PyDocDBError",
    "aggregate",
    "load_collection",
    "save_collection",
]
