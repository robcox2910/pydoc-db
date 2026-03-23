# Query Language

## The Librarian Search Analogy

Imagine telling a librarian what kind of book you want. You might say:

- "I want a book that costs EXACTLY $10" -- that's `$eq`
- "I want a book with MORE THAN 200 pages" -- that's `$gt`
- "I want a book that is NOT science fiction" -- that's `$ne`

PyDocDB's query language lets you express these kinds of searches using special operators.

## Comparison Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `$eq` | Equals | `{"age": {"$eq": 14}}` |
| `$ne` | Not equals | `{"name": {"$ne": "Bob"}}` |
| `$gt` | Greater than | `{"age": {"$gt": 13}}` |
| `$gte` | Greater than or equal | `{"age": {"$gte": 13}}` |
| `$lt` | Less than | `{"price": {"$lt": 100}}` |
| `$lte` | Less than or equal | `{"price": {"$lte": 100}}` |
| `$in` | In a list | `{"color": {"$in": ["red", "blue"]}}` |
| `$exists` | Field exists | `{"email": {"$exists": True}}` |

## Shorthand Equality

Writing `{"name": "Alice"}` is the same as `{"name": {"$eq": "Alice"}}`.

## Logical Operators

```python
# AND -- all conditions must be true
{"$and": [{"age": {"$gte": 13}}, {"age": {"$lte": 19}}]}

# OR -- at least one condition must be true
{"$or": [{"name": "Alice"}, {"name": "Bob"}]}

# NOT -- the condition must NOT be true
{"$not": {"name": "Charlie"}}
```

## Combining Operators

You can combine multiple operators on the same field:

```python
# Age between 13 and 19
{"age": {"$gte": 13, "$lte": 19}}
```
