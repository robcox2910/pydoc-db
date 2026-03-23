# PyDocDB

An educational document store (like MongoDB) built from scratch in Python. Part of the **PyLearn** platform for kids aged 12+.

PyDocDB stores JSON-like documents without requiring a fixed schema -- each document can have different fields, just like how every index card in a filing cabinet can have different information on it.

## Features

- **Documents** -- Dict-like objects with auto-generated unique IDs
- **Collections** -- Named groups of documents with full CRUD operations
- **Query Language** -- Filter with operators: `$eq`, `$gt`, `$lt`, `$gte`, `$lte`, `$ne`, `$in`, `$exists`, `$and`, `$or`, `$not`
- **Nested Field Access** -- Query nested fields with dot notation (e.g., `"address.city"`)
- **Projection** -- Return only specific fields from documents
- **Indexing** -- Create indexes on fields for faster lookups
- **Persistence** -- Save/load collections to JSON files on disk
- **Aggregation** -- Pipeline with `$match`, `$group`, `$sort`, `$limit`, `$count`

## Quick Start

```python
from pydocdb import Collection, save_collection, load_collection, aggregate

# Create a collection (like labeling a new folder in a filing cabinet)
students = Collection("students")

# Insert documents (like filing index cards)
students.insert_one({"name": "Alice", "age": 14, "grade": "9th"})
students.insert_one({"name": "Bob", "age": 13, "hobby": "chess"})
students.insert_one({"name": "Charlie", "age": 15, "grade": "10th"})

# Find documents with queries
teenagers = students.find({"age": {"$gte": 13}})
alice = students.find_one({"name": "Alice"})

# Update and delete
students.update_one({"name": "Alice"}, {"age": 15})
students.delete_one({"name": "Bob"})

# Use projection to get only specific fields
names = students.find({}, projection={"name": 1, "_id": 0})

# Aggregate data
result = aggregate(students.to_list(), [
    {"$group": {"_id": "$grade", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
])

# Save to disk and load later
save_collection(students, "students.json")
loaded = load_collection("students.json")
```

## Installation

```bash
uv add pydocdb
```

## Development

```bash
git clone https://github.com/robcox2910/pydoc-db.git
cd pydoc-db
uv sync --all-extras
uv run pytest
uv run ruff check src/ tests/
uv run pyright src tests
```

## Related Projects

| Project | Description |
|---------|-------------|
| [py-os](https://github.com/robcox2910/py-os) | Educational operating system concepts |
| [pebble-lang](https://github.com/robcox2910/pebble-lang) | Educational programming language |
| [pydb](https://github.com/robcox2910/pydb) | Educational relational database engine |
| [pyweb](https://github.com/robcox2910/pyweb) | Educational web framework |
| [pygit](https://github.com/robcox2910/pygit) | Educational version control system |
| [pycrypt](https://github.com/robcox2910/pycrypt) | Educational cryptography library |
| [pynet](https://github.com/robcox2910/pynet) | Educational networking library |
| [pysearch](https://github.com/robcox2910/pysearch) | Educational search engine |
| [pymq](https://github.com/robcox2910/pymq) | Educational message queue |
| [pykv](https://github.com/robcox2910/pykv) | Educational key-value store |
| [pystack](https://github.com/robcox2910/pystack) | Unified platform integrating all projects |
