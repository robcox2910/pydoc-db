# Projection

## The "Reading Only the Headline" Analogy

When you open a newspaper, you don't always read every word of every article. Sometimes you just scan the **headlines** to find what interests you. Projection works the same way -- it lets you choose which fields to see and which to skip.

## Include Mode

Tell PyDocDB exactly which fields you want:

```python
# Only get name and age (plus _id, which is always included)
students.find({"age": {"$gt": 13}}, projection={"name": 1, "age": 1})
# Returns: [{"_id": "...", "name": "Alice", "age": 14}]
```

## Exclude Mode

Tell PyDocDB which fields to hide:

```python
# Get everything EXCEPT the password
users.find({}, projection={"password": 0})
```

## The _id Field

The `_id` field is special -- it's always included unless you explicitly exclude it:

```python
# Exclude _id too
students.find({}, projection={"name": 1, "_id": 0})
# Returns: [{"name": "Alice"}, {"name": "Bob"}]
```

## Rules

1. You can either include fields (value = 1) or exclude fields (value = 0), but not both in the same projection (except for `_id`)
2. An empty projection `{}` returns all fields
3. `_id` is included by default in inclusion mode
