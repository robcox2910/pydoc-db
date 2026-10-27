---
title: "Build your own document database in Python"
---

# PyDocDB: Build your own document database in Python

## The Filing Cabinet Analogy

Imagine a **filing cabinet** in a school office. It has folders labeled "Students," "Teachers," and "Classes." Each folder holds index cards with information about people or things.

Here's the key difference from a regular spreadsheet: **every index card can be different!**

- Alice's card might have: name, age, favorite_color
- Bob's card might have: name, age, hobby, pet_name
- Charlie's card might have: name, grade, allergies

In a spreadsheet (like a SQL database), every row MUST have the same columns. But in a document store, each "row" (document) can have whatever fields it wants. This flexibility is what makes document stores so powerful!

## What is PyDocDB?

PyDocDB is an **educational document store** -- a database that stores JSON-like documents without requiring a fixed schema. It's inspired by real-world databases like MongoDB.

## Core Concepts

1. **[Documents](concepts/documents.md)** -- Individual records (like index cards)
2. **[Collections](concepts/collections.md)** -- Named groups of documents (like folders)
3. **[Queries](concepts/queries.md)** -- Finding documents that match criteria
4. **[Nested Fields](concepts/nested.md)** -- Accessing data inside data with dot notation
5. **[Projection](concepts/projection.md)** -- Choosing which fields to see
6. **[Indexing](concepts/indexing.md)** -- Making searches faster
7. **[Persistence](concepts/persistence.md)** -- Saving data to disk
8. **[Aggregation](concepts/aggregation.md)** -- Grouping and summarizing data

## Install

```bash
pip install fromscratch-pydocdb
```

Or get the whole series at once with `pip install fromscratch-pystack`. To read the code or run the tests, clone it from [GitHub](https://github.com/robcox2910/pydoc-db).

## Quick Start

```python
from pydocdb import Collection

# Create a collection (like labeling a new folder)
students = Collection("students")

# Add some documents (like filing index cards)
students.insert_one({"name": "Alice", "age": 14, "grade": "9th"})
students.insert_one({"name": "Bob", "age": 13, "hobby": "chess"})

# Find documents (like searching through the folder)
teenagers = students.find({"age": {"$gte": 13}})
```
