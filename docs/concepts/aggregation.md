# Aggregation

## The "Sorting and Counting Your Card Collection" Analogy

Imagine you have a huge pile of trading cards. You might want to:

1. **Pick out** only the rare cards (`$match`)
2. **Group** them by type -- Fire, Water, Grass (`$group`)
3. **Sort** the groups by how many cards each has (`$sort`)
4. **Look at only** the top 3 groups (`$limit`)
5. **Count** how many groups there are (`$count`)

That's an aggregation pipeline! Each step transforms the data, and the output of one step becomes the input for the next.

## Pipeline Stages

### $match -- Filter Documents

```python
from pydocdb import Collection, aggregate

products = Collection("products")
products.insert_many([
    {"name": "Widget", "category": "A", "price": 10},
    {"name": "Gadget", "category": "A", "price": 20},
    {"name": "Doohickey", "category": "B", "price": 30},
])

# Get only category A products
result = aggregate(products.to_list(), [
    {"$match": {"category": "A"}}
])
```

### $group -- Group and Summarize

```python
# Group by category and sum prices
result = aggregate(products.to_list(), [
    {"$group": {
        "_id": "$category",
        "total_price": {"$sum": "$price"},
        "count": {"$sum": 1},
        "avg_price": {"$avg": "$price"},
    }}
])
```

Available accumulators: `$sum`, `$avg`, `$min`, `$max`

### $sort -- Order Results

```python
# Sort by price, highest first
result = aggregate(products.to_list(), [
    {"$sort": {"price": -1}}  # -1 = descending, 1 = ascending
])
```

### $limit -- Take Only N Results

```python
# Get the top 2 most expensive
result = aggregate(products.to_list(), [
    {"$sort": {"price": -1}},
    {"$limit": 2}
])
```

### $count -- Count Documents

```python
# Count how many products there are
result = aggregate(products.to_list(), [
    {"$count": "total_products"}
])
# [{"total_products": 3}]
```

## Multi-Stage Pipelines

The real power comes from chaining stages together:

```python
result = aggregate(products.to_list(), [
    {"$match": {"price": {"$gte": 15}}},     # Step 1: Filter expensive items
    {"$group": {"_id": "$category", "total": {"$sum": "$price"}}},  # Step 2: Group by category
    {"$sort": {"total": -1}},                  # Step 3: Sort by total, highest first
    {"$limit": 5},                             # Step 4: Only top 5
])
```
