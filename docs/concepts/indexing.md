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

## When to Use Indexes

- Use indexes on fields you search by frequently
- Indexes make reads faster but use extra memory
- You can index nested fields too: `students.create_index("address.city")`

## Managing Indexes

```python
# List all indexes
students.list_indexes()  # ["name"]

# Remove an index
students.drop_index("name")
```
