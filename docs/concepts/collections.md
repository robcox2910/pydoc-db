# Collections

## The Folder in a Filing Cabinet Analogy

A collection is like a **labeled folder** in a filing cabinet. The folder called "Students" holds all the student index cards. The folder called "Products" holds all the product cards. Each folder is independent -- adding a card to "Students" doesn't affect "Products."

## CRUD Operations

CRUD stands for **C**reate, **R**ead, **U**pdate, **D**elete -- the four basic things you can do with data.

### Create (Insert)

```python
from pydocdb import Collection

students = Collection("students")

# Insert one document
alice = students.insert_one({"name": "Alice", "age": 14})

# Insert many at once
students.insert_many([
    {"name": "Bob", "age": 13},
    {"name": "Charlie", "age": 15},
])
```

### Read (Find)

```python
# Find all documents
all_students = students.find()

# Find with a query
teens = students.find({"age": {"$gte": 13}})

# Find just one
alice = students.find_one({"name": "Alice"})

# Find by ID
doc = students.find_by_id("some-id-here")
```

### Update

```python
# Update one document
students.update_one({"name": "Alice"}, {"age": 15})

# Update many documents
students.update_many({"grade": "9th"}, {"year": 2024})
```

### Delete

```python
# Delete one document
students.delete_one({"name": "Alice"})

# Delete many documents
students.delete_many({"graduated": True})
```
