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

## Releasing

Other projects in the series ([PyStack](https://github.com/robcox2910/pystack)) use a pinned release of this one,
not whatever is on `main`. To publish a change for them:

1. Merge the change to `main`.
2. Tag it: `git tag -a vX.Y.Z -m vX.Y.Z && git push origin vX.Y.Z`.
   A change to the public API bumps the minor version (`v0.1.0` → `v0.2.0`);
   anything else bumps the patch (`v0.1.0` → `v0.1.1`).
3. In each project that uses it, edit the tag in `[tool.uv.sources]`, run
   `uv lock --upgrade-package <name>`, and open a pull request so CI checks
   the pair together.

<!-- series:start -->
## Related Projects

This project is one of a series that builds real systems "from scratch in Python" to teach how they work. See the [series home](https://robcox2910.github.io/) for the full story.

| Project | What it teaches | Repository | Docs |
| --- | --- | --- | --- |
| PyOS | Operating systems | [py-os](https://github.com/robcox2910/py-os) | [Docs](https://robcox2910.github.io/py-os/) |
| Pebble | Compilers and programming languages | [pebble-lang](https://github.com/robcox2910/pebble-lang) | [Docs](https://robcox2910.github.io/pebble-lang/) |
| PyDB | Relational databases | [pydb](https://github.com/robcox2910/pydb) | [Docs](https://robcox2910.github.io/pydb/) |
| PyKV | Key-value stores | [pykv](https://github.com/robcox2910/pykv) | [Docs](https://robcox2910.github.io/pykv/) |
| **PyDocDB** | **Document databases** | [pydoc-db](https://github.com/robcox2910/pydoc-db) | [Docs](https://robcox2910.github.io/pydoc-db/) |
| PyGraphDB | Graph databases | [pygraphdb](https://github.com/robcox2910/pygraphdb) | [Docs](https://robcox2910.github.io/pygraphdb/) |
| PyTSDB | Time-series databases | [pytsdb](https://github.com/robcox2910/pytsdb) | [Docs](https://robcox2910.github.io/pytsdb/) |
| PyVecDB | Vector databases | [pyvecdb](https://github.com/robcox2910/pyvecdb) | [Docs](https://robcox2910.github.io/pyvecdb/) |
| PyColDB | Column-family databases | [pycoldb](https://github.com/robcox2910/pycoldb) | [Docs](https://robcox2910.github.io/pycoldb/) |
| PyCrypt | Cryptography | [pycrypt](https://github.com/robcox2910/pycrypt) | [Docs](https://robcox2910.github.io/pycrypt/) |
| PyNet | Computer networking | [pynet](https://github.com/robcox2910/pynet) | [Docs](https://robcox2910.github.io/pynet/) |
| PyWeb | HTTP web servers | [pyweb](https://github.com/robcox2910/pyweb) | [Docs](https://robcox2910.github.io/pyweb/) |
| PyGit | Version control | [pygit](https://github.com/robcox2910/pygit) | [Docs](https://robcox2910.github.io/pygit/) |
| PySearch | Search engines | [pysearch](https://github.com/robcox2910/pysearch) | [Docs](https://robcox2910.github.io/pysearch/) |
| PyMQ | Message queues | [pymq](https://github.com/robcox2910/pymq) | [Docs](https://robcox2910.github.io/pymq/) |
| PyLLM | Language models (the brain) | [pyllm](https://github.com/robcox2910/pyllm) | [Docs](https://robcox2910.github.io/pyllm/) |
| PyScheduler | Job scheduling | [pyscheduler](https://github.com/robcox2910/pyscheduler) | [Docs](https://robcox2910.github.io/pyscheduler/) |
| PyStack | Full-stack integration | [pystack](https://github.com/robcox2910/pystack) | [Docs](https://robcox2910.github.io/pystack/) |
<!-- series:end -->

<!-- docs:start -->
## Documentation

Full docs (with kid-friendly explanations of every idea): https://robcox2910.github.io/pydoc-db/
<!-- docs:end -->
