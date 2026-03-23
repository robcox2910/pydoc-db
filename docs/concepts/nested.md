# Nested Field Access (Dot Notation)

## The Address Inside an Envelope Analogy

Imagine you receive a letter. The envelope has an address on it, but the address itself has parts: street, city, and country. To tell someone the city, you'd say: "Look at the address, then find the city part."

In PyDocDB, dot notation works the same way. If a document has nested data like:

```python
{
    "name": "Alice",
    "address": {
        "street": "123 Main St",
        "city": "Paris",
        "country": "France"
    }
}
```

You can access the city with `"address.city"` -- "look inside address, then get city."

## Using Dot Notation

### In Queries

```python
# Find everyone who lives in Paris
students.find({"address.city": "Paris"})

# Find everyone in France with age > 13
students.find({
    "address.country": "France",
    "age": {"$gt": 13}
})
```

### Deeply Nested Access

Dot notation works at any depth:

```python
doc = Document({
    "school": {
        "address": {
            "city": "London"
        }
    }
})

doc.get_nested("school.address.city")  # "London"
```

### Missing Fields

If any part of the path doesn't exist, you get `None` back (no errors!):

```python
doc = Document({"name": "Alice"})
doc.get_nested("address.city")  # None (address doesn't exist)
```
