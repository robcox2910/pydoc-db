# Indexing

## The Book Index Analogy

Think about the index at the back of a textbook. If you want to find information about "photosynthesis," you have two choices:

1. **Without an index**: Flip through every single page looking for the word. Slow!
2. **With an index**: Look up "photosynthesis" in the index, which tells you it's on pages 42, 87, and 156. Fast!

Database indexes work the same way. Without an index, finding all students named "Alice" means checking every single document. With an index on the "name" field, we keep a lookup table that points directly to the right documents.

## Creating an Index

```python
students = Collection("students")
students.insert_many([
    {"name": "Alice", "age": 14},
    {"name": "Bob", "age": 13},
    {"name": "Alice", "age": 16},  # Another Alice!
])

# Create an index on the "name" field
students.create_index("name")
```

`create_index` also hands back a snapshot of the new index, so you can peek at
it. Like every card the collection hands out, it is a copy: changing it never
changes the collection's own index or what your searches find.

Calling `create_index` on a field that already has an index rebuilds it from
the current cards and returns a fresh snapshot.

## When to Use Indexes

- Use indexes on fields you search by frequently
- Indexes make reads faster but use extra memory
- You can index nested fields too: `students.create_index("address.city")`

## What Speeds Up (and What Doesn't)

`find()` and `find_one()` use an index only for **equality** lookups on an
indexed field, such as `students.find({"name": "Alice"})` or the equivalent
`{"name": {"$eq": "Alice"}}`. That's when we can jump straight to the matching
documents instead of scanning them all.

Range queries (`$gt`, `$lt`, ...), `$in`, `$exists`, and matches on
un-indexed fields still fall back to a full scan. Making those use an index too
is a great exercise to try yourself!

## Managing Indexes

```python
# List all indexes
students.list_indexes()  # ["name"]

# Remove an index
students.drop_index("name")
```
