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

## Saving Safely

The simple way to save -- wipe the file, then write it out again -- has a
nasty problem: if the computer crashes halfway through, you're left with half
a file, and your data is gone.

So saving works like a careful student copying out their homework:

1. Write the new version on a **fresh sheet** -- a temporary file right next
   to the real one.
2. Make sure the **ink is dry** -- `fsync` pushes the bytes out of the
   computer's memory and onto the disk.
3. **Swap** the fresh sheet in for the old one in a single instant step.

At every moment there's a complete file: the old one or the new one, never
half of each. Real databases like SQLite and PostgreSQL use the same trick.
The code lives in `atomic.py`.
