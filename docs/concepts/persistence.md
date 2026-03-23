# Persistence

## Saving Your Work

Imagine you've spent hours organizing your trading card collection into perfect piles on your desk. When you go to bed, you need to put everything in a box so it's safe. The next morning, you take everything back out and it's exactly how you left it.

That's what persistence does! Without it, all your documents disappear when your program stops running.

## Saving a Collection

```python
from pydocdb import Collection, save_collection, load_collection

students = Collection("students")
students.insert_one({"name": "Alice", "age": 14})
students.insert_one({"name": "Bob", "age": 13})

# Save to a file
save_collection(students, "students.json")
```

## Loading a Collection

```python
# Load it back later
students = load_collection("students.json")
print(len(students))  # 2 -- all your data is back!
```

## What Gets Saved?

- The collection name
- All documents (with their data and _id fields)
- The list of indexed fields (indexes are recreated on load)

## File Format

Collections are saved as JSON files, which are human-readable. You can even open them in a text editor to see your data!
