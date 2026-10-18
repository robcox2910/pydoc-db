# Property Testing (Every Card Is Where the Index Says)

## The Filing Cabinet Inspector

Picture the filing cabinet in a school office. Every folder has a label,
every index card has a barcode, and a clerk files cards, finds them,
rewrites them and shreds them all day. PyDocDB is that cabinet, made of
Python.

How would you check the clerk does the job right? The usual way: file
Alice's card, ask for "everyone called Alice", and smile when her card
comes back. That's an **example test**. It's useful, but it only tells
you about the one card you thought of.

Now imagine an inspector. All day they hand the clerk thousands of
cards -- cards with no name, cards with a name that's an empty string,
cards whose "pet" is a list of lists, cards in Japanese -- and every time
they ask for something, they check one rule:

> Whatever cards are in the folder, asking for "name is X" gives back
> exactly the cards whose name is X.

That rule is a **property**. It doesn't say what any one card looks like.
It says something that must be true for *every* folder of cards.

When the inspector catches the clerk out, they don't just report
"something went wrong with that huge pile". They try again with fewer
cards, shorter names and simpler values, checking it still goes wrong
each time, until it's as small as it can be. That boiling-down is called
**shrinking**, and it's the best part: the smallest failing input usually
points straight at the bug.

In Python, the inspector is a library called
[Hypothesis](https://hypothesis.readthedocs.io/). PyDocDB's property tests
live in `tests/test_properties.py`, next to the ordinary example tests,
and the model check (more on that below) is in `tests/test_model.py`.

## A Property from PyDocDB

Here's the inspector's rule for [queries](concepts/queries.md) as a test:

```python
def field_names() -> st.SearchStrategy[str]:
    """Pick one of the few field names every test document draws from."""
    return st.sampled_from(FIELD_NAMES)


def document_fields() -> st.SearchStrategy[DocumentData]:
    """Make the fields of one index card: some of the shared names, each with any value."""
    return st.dictionaries(field_names(), any_values())


def folders_of_cards() -> st.SearchStrategy[list[DocumentData]]:
    """Make a short list of cards, each using some of the shared field names."""
    return st.lists(document_fields(), max_size=MOST_CARDS_PER_FOLDER)


def query_values() -> st.SearchStrategy[Any]:
    """Make a value to look for: a plain value, or a list of any values."""
    # Not a dict: in a query, a dict means "operators", like {"$gt": 13}
    # (see docs/concepts/queries.md and pydocdb.query._match_field).
    return st.one_of(plain_values(), st.lists(any_values()))


@given(cards=folders_of_cards(), field=field_names(), value=query_values())
def test_find_gives_what_a_plain_filter_gives(
    cards: list[DocumentData], field: str, value: Any
) -> None:
    """``find({field: value})`` returns exactly the cards whose field equals value, in order."""
    collection = folder_holding("cards", {str(n): card for n, card in enumerate(cards)})
    expected = [card for card in collection.to_list() if card.get(field) == value]
    assert collection.find({field: value}) == expected
```

Line by line:

- **`field_names()`, `document_fields()`, `folders_of_cards()` and
  `query_values()`** are **strategies**: recipes for making random
  inputs. Every card picks its fields from three shared names (`name`,
  `age`, `pet`), so searches really hit something; with fully random names
  they'd almost never match. `any_values()` (in `tests/strategies.py`,
  shared with the model check) makes text, numbers, `True`/`False`,
  `None`, and lists and dicts up to two deep. A folder holds at most five
  cards, which keeps the test quick; a failure shrinks to one or two
  cards anyway.
- **The comment in `query_values()`** says why the value is never a dict:
  `{"age": {"$gt": 13}}` means "age greater than 13", not "age equals
  this dict". A strategy should only make inputs the code promises to
  handle, and the comment says where that promise is written down.
- **`@given(...)`** tells Hypothesis to run the test many times (100 in a
  normal run), each time with fresh cards, a field and a value.
- **The docstring** says the rule in plain English. If you can't say the
  rule in one sentence, it probably isn't a good property yet.
- **`folder_holding(...)`** is a small helper that makes a `Collection`
  and files every card, giving each one the barcode `"0"`, `"1"`, ...
- **`expected = [...]`** is the answer worked out the dumbest way
  possible: a plain Python loop over every card. No query engine, no
  operators -- just `card.get(field) == value`. That's what makes it a
  trustworthy answer.
- **The `assert`** is the rule itself: PyDocDB's `find` must give exactly
  the same cards, in the same order.

Notice what the test *doesn't* say. It never says "find Alice and you get
Alice's card". It doesn't need to know any answers. It only needs a rule
that's always true.

The next property says an index must never change what `find` returns.
**That property alone is passed by a `find` that does nothing** -- one
that always hands back an empty list gives the same nothing with or
without an index -- so the plain-filter property sits beside it and fails
straight away if `find` never finds anything.

| Rule | Test |
|---|---|
| Loading a saved collection gives back the same name, cards (types and all) and indexes | `test_save_then_load_gives_back_the_same_collection` |
| Building an index on a field changes how fast `find` is, never its answer or its order | `test_an_index_never_changes_what_find_returns` |
| Whatever bytes are in the file, loading gives a collection or a `PersistenceError`, never another error | `test_any_bytes_on_disk_load_or_raise_persistence_error` |
| Whatever JSON is in the file, loading gives a collection or a `PersistenceError`, never another error | `test_any_json_on_disk_load_or_raise_persistence_error` |

## Checking Against a Model

A property checks one action. But a collection is something you change
step by step: file, rewrite, shred, build an index, search. Bugs often
hide in the *order* of steps -- building an index *after* the cards are
filed, or rewriting a card that an index already points at.

So the inspector has a second trick. They keep a notebook: a plain list
of every card, copied out by hand. After every single step, they compare
the cabinet with the notebook. If the two ever disagree, the cabinet is
wrong.

That notebook is a **model**: something simple that we already trust.
For a `Collection`, the model is a plain Python `list` of `dict`s. Here's
part of the check in `tests/test_model.py`:

```python
class CollectionMachine(RuleBasedStateMachine):
    """Play random inserts, updates, deletes, searches and indexes on a Collection and a list."""

    ids = Bundle("ids")

    def __init__(self) -> None:
        """Start with an empty collection, an empty list and no indexes."""
        super().__init__()
        self.collection = Collection("cards")
        self.model: list[DocumentData] = []
        self.indexed_fields: list[str] = []

    @rule(target=ids, doc_id=st.one_of(ids, document_ids()), fields=document_fields())
    def insert_one(self, doc_id: str, fields: DocumentData) -> str:
        """File one card in both, or refuse it in both if its ``_id`` is taken."""
        card = {**fields, "_id": doc_id}
        if doc_id in self.ids_in_model():
            with pytest.raises(DuplicateKeyError):
                self.collection.insert_one(card)
        else:
            self.collection.insert_one(card)
            self.model.append(copy.deepcopy(card))
        return doc_id

    @rule(field=field_names(), value=search_values())
    def delete_one(self, field: str, value: Any) -> None:
        """Shred the first matching card in both; say True exactly when there was one."""
        expected = self.matching(field, value)
        if expected:
            self.model.remove(expected[0])
        assert self.collection.delete_one({field: value}) == bool(expected)

    @invariant()
    def same_cards_and_indexes(self) -> None:
        """After every step, the collection holds exactly the list's cards, in order."""
        assert self.collection.to_list() == self.model
        assert self.collection.list_indexes() == self.indexed_fields


TestCollectionModel = cast("type[unittest.TestCase]", CollectionMachine.TestCase)
```

Piece by piece:

- **`RuleBasedStateMachine`** is Hypothesis's tool for testing things
  that change step by step. Hypothesis makes up a random **story** of
  steps and plays it.
- **`self.collection` and `self.model`** are the cabinet and the
  notebook. Every story starts with both empty.
- **Each `@rule`** is one kind of step. It does the same thing to the
  collection and to the list. The real file has rules to insert one card
  or a stack of them, look a card up by `_id`, search, search for a value
  a real card holds, update one or many, delete one or many, build and
  drop indexes, scribble on found cards, and clear the folder.
- **`ids = Bundle("ids")`** is a bag of barcodes used earlier in the
  story. Two random strings almost never match, so without it the story
  would hardly ever try filing a card under a barcode that's taken.
  `insert_one` puts its barcode in the bag (`target=ids`), and picks
  either a barcode from the bag or a brand-new one, so it tries both
  sides: a taken barcode must raise `DuplicateKeyError` and change
  nothing.
- **`delete_one`** works out the answer from the notebook first, then
  checks what the collection *says*: `True` exactly when there was a card
  to shred.
- **The `@invariant()`** runs after every single step and compares the
  whole folder, card by card, in order, plus the list of indexes.
- **`TestCollectionModel = ...TestCase`** turns the machine into a test
  that pytest can find. One run plays 100 random stories, each up to 20
  steps long.

The list is a good model because it's obviously right and it's *not*
`Collection`'s code. It has no barcode lookup table, no indexes and no
query engine; every search is a plain loop. If we built the model by
copying `Collection`, any bug would be in both, and they'd agree
perfectly about the wrong answer.

## Try It Yourself

Let's break the [index](concepts/indexing.md) on purpose and watch the
inspector find it.

Open `src/pydocdb/indexing.py`, find `add`, and change the check that
skips missing values, as if "skip anything empty" sounded tidier:

```python
        if not value:  # was: if value is None:
```

Now the index quietly leaves out every card whose value is "empty":
`""`, `0`, `False`, `[]`. Run the property tests:

```bash
uv run pytest tests/test_properties.py tests/test_model.py --no-cov
```

Hypothesis reports this (trimmed to the interesting part):

```
    @given(cards=folders_with_repeats(), field=field_names(), value=query_values())
    def test_an_index_never_changes_what_find_returns(
        cards: list[DocumentData], field: str, value: Any
    ) -> None:
        """Building an index on a field changes how fast ``find`` is, never its answer or its order."""
        collection = folder_holding("cards", {str(n): card for n, card in enumerate(cards)})
        # Search for a random value, and for every value a card really holds.
        # ``$eq`` spells out "equals", so even a dict value is looked for, not read
        # as operators (see docs/concepts/queries.md).
        queries = [{field: {"$eq": wanted}} for wanted in [value, *(c.get(field) for c in cards)]]
        without_index = [collection.find(query) for query in queries]
        collection.create_index(field)
        with_index = [collection.find(query) for query in queries]
>       assert with_index == without_index
E       AssertionError: assert [[], []] == [[], [{'name'... '_id': '0'}]]
E         At index 1 diff: [] != [{'name': '', '_id': '0'}]
E       Failing test case: test_an_index_never_changes_what_find_returns(
E           cards=[{'name': ''}],
E           field='name',
E           value=None,
E       )
```

Look at how small that is. One card, whose name is the empty string.
Searching for the random value, `None`, agreed either way. But
searching for the name the card really holds, `''`, found it without an
index and found nothing with one.

`test_an_index_never_changes_what_find_returns` caught it. The model
check happened to miss it this time: a model check is only as good as
the stories it tries. The other four
properties stayed green: without an index, `find` is still right. **The
example tests all still pass. Only the property notices.** The example
tests index cards with real-looking values like `"Paris"`, and nobody
thought to index a card with an empty name.

Put the line back to `if value is None:` and run the tests again. They
pass.

!!! tip "Older Hypothesis versions"
    Older versions of Hypothesis print `Falsifying example:` instead of
    `Failing test case:`. It means the same thing.

## A Bug We Found

Four, in fact. First, the model check failed on PyDocDB's real code:

```
TypeError: cannot use 'tuple' as a dict key (unhashable type: 'list')
Failing test case: <state machine>
state = CollectionMachine()
state.same_cards_and_indexes()
state.create_index(field='name')
state.same_cards_and_indexes()
state.find(field='name', value=[[]])
state.teardown()
```

Build an index on `name`, search for a list holding an empty list, and
PyDocDB crashed. An index is a dict from values to barcodes, and dict
keys must be *hashable* (unchangeable), which lists aren't. So
`make_hashable` turned a list into a tuple -- but only the outside one.
`[[]]` became `([],)`, a tuple with a list still inside it. Worse,
`insert_one` left the card half filed. The example tests only indexed text like
`"Paris"`; the inspector's `any_values()` makes lists of lists all the
time. The fix converts all the way down:

```python
        return tuple(make_hashable(item) for item in cast("list[Any]", value))  # was: return tuple(value)
```

The second was the loader. `test_any_bytes_on_disk_load_or_raise_persistence_error`
shrank a broken save file to one byte, `b'\x80'`, which isn't UTF-8 text,
so `load_collection` crashed with `UnicodeDecodeError` instead of
`PersistenceError`. The JSON property found a hand-edited file with two
cards sharing a barcode, `{'documents': [{'_id': 1}, {'_id': 1}]}`, which
escaped as `DuplicateKeyError`. Huge numbers and deep nesting got out too. Now
each is a `PersistenceError` naming the file:

```python
    except (OSError, UnicodeDecodeError) as exc:  # was: except (OSError, json.JSONDecodeError) as exc:
```

Third, an index changed the *order* of `find`'s answer: two cards named
`''` came back as `'1'`, `'0'` instead of the order they were filed, and
`find_one`'s "first" match changed from run to run. The collection now
remembers each card's place in the filing order and sorts the index's
answer by it.

Fourth, cards were copied only one level deep. Add `"blue"` to the
`tags` list of a card `find` gave you, and the filed card changed too.
The model check's `scribble_on_found_cards` rule caught it. Cards are now
copied all the way down (`copy.deepcopy`), coming in and going out.

Each shrunk input is now also an ordinary example test, in
`tests/test_indexing.py`, `tests/test_collection.py` and `tests/test_persistence.py`, so these bugs
can never sneak back in, even if someone deletes the properties.

## Run It Yourself

Run just the property tests and the model check (100 examples each, the
same every time):

```bash
uv run pytest tests/test_properties.py tests/test_model.py --no-cov
```

The `--no-cov` turns off the coverage check, which expects the *whole*
test suite to run and would fail on two files.

Run them the long way (2,000 random examples each, different every run)
to hunt for rarer bugs. It takes about 3 to 4 minutes:

```bash
uv run pytest tests/test_properties.py tests/test_model.py --no-cov --hypothesis-profile=thorough
```

The normal run uses a fixed seed, so it tries the same inputs every time
and a passing build means the same thing on every computer. The thorough
run is random, so each time you run it the inspector brings a brand-new
pile of cards. Both settings live in `conftest.py` at the top of the
project.

## Your Turn

Write one new property for PyDocDB. Think about `delete_many`. After
`delete_many({field: value})`, what should `count({field: value})` be,
whatever was in the folder? And what should `len` be, compared with
before? What's the strategy? What's the `assert`? Run it and watch it
pass. Then break `delete_many` on purpose and watch the inspector find it.
