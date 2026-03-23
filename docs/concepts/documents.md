# Documents

## The Index Card Analogy

Think of a document like an **index card** in a library. Each card can have whatever information you want -- a person's name, their age, their favorite color, or even a list of their pets. Unlike a spreadsheet where every row must have the same columns, each index card can be totally different!

Every card gets a **unique barcode** stamped on it (the `_id` field), so you can always find that exact card again.

## Creating Documents

```python
from pydocdb import Document

# Create a document -- it automatically gets a unique _id
alice = Document({"name": "Alice", "age": 14})
print(alice.id)  # Something like "a1b2c3d4-..."

# You can also provide your own _id
bob = Document({"_id": "bob-001", "name": "Bob", "age": 13})
print(bob.id)  # "bob-001"
```

## Accessing Fields

```python
doc = Document({"name": "Alice", "age": 14, "address": {"city": "Paris"}})

# Get a field
doc.get("name")        # "Alice"
doc.get("missing")     # None
doc.get("missing", 0)  # 0 (custom default)

# Get nested fields with dot notation
doc.get_nested("address.city")  # "Paris"

# Get all data as a dictionary
doc.to_dict()  # {"_id": "...", "name": "Alice", "age": 14, "address": {"city": "Paris"}}
```

## Key Points

- Every document gets a unique `_id` automatically (unless you provide one)
- Documents can have any fields -- no fixed schema required
- Nested fields can be accessed using dot notation
- `to_dict()` returns a copy, so modifying it won't change the original
