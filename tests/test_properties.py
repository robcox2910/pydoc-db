"""Property-based tests -- rules that must hold for *every* input.

An ordinary test checks one example someone thought of: "save a folder
holding Alice's card, load it back, and Alice is still 14". A property test
states a rule instead, such as "whatever is in the folder, loading the save
file gives back exactly that", and lets Hypothesis invent hundreds of
folders to try to break it. If one breaks the rule, Hypothesis *shrinks* it
down to the smallest input that still fails, and shows you that.

Each test below says its rule in plain English in its docstring. The
strategies at the top are recipes for making random inputs; each one is
named for what it makes.

The step-by-step check of ``Collection`` against a plain list of dicts lives
in ``tests/test_model.py``. See ``docs/property-testing.md`` for the walk-through.
"""

import json
import tempfile
from pathlib import Path
from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from pydocdb.collection import Collection
from pydocdb.document import DocumentData
from pydocdb.errors import PersistenceError
from pydocdb.persistence import load_collection, save_collection
from tests.strategies import (
    MOST_CARDS_PER_FOLDER,
    any_values,
    document_fields,
    document_ids,
    field_names,
    plain_values,
)

# --- Strategies: recipes for random inputs -----------------------------------
# plain_values(), any_values(), field_names(), document_fields() and
# document_ids() live in tests/strategies.py, shared with the model check.


def collection_names() -> st.SearchStrategy[str]:
    """Make any folder label at all: empty, spaces, emoji, slashes, the lot."""
    return st.text()


def any_field_names() -> st.SearchStrategy[str]:
    """Make a field name: usually one of the shared few, sometimes any text at all."""
    return st.one_of(field_names(), st.text())


def any_cards() -> st.SearchStrategy[dict[str, DocumentData]]:
    """Make a folder's worth of cards: each ``_id`` (all different) with its fields."""
    return st.dictionaries(
        document_ids(),
        st.dictionaries(any_field_names(), any_values()),
        max_size=MOST_CARDS_PER_FOLDER,
    )


def folders_of_cards() -> st.SearchStrategy[list[DocumentData]]:
    """Make a short list of cards, each using some of the shared field names."""
    return st.lists(document_fields(), max_size=MOST_CARDS_PER_FOLDER)


@st.composite
def folders_with_repeats(draw: st.DrawFn) -> list[DocumentData]:
    """Make a short list of cards in which some cards are copies of others."""
    # Copies mean one search often matches several cards, which is where
    # an index could hand them back in the wrong order.
    kinds = draw(st.lists(document_fields(), min_size=1, max_size=3))
    return draw(st.lists(st.sampled_from(kinds), max_size=MOST_CARDS_PER_FOLDER))


def query_values() -> st.SearchStrategy[Any]:
    """Make a value to look for: a plain value, or a list of any values."""
    # Not a dict: in a query, a dict means "operators", like {"$gt": 13}
    # (see docs/concepts/queries.md and pydocdb.query._match_field).
    return st.one_of(plain_values(), st.lists(any_values()))


def any_bytes() -> st.SearchStrategy[bytes]:
    """Make any run of raw bytes, including the empty one and ones that aren't text."""
    return st.binary()


def any_json() -> st.SearchStrategy[object]:
    """Make any JSON value at all (NaN included), whether or not it looks like a saved collection."""
    return st.one_of(st.floats(), any_values())


def clashing_ids() -> st.SearchStrategy[object]:
    """Pick an ``_id`` from a tiny pool, so two cards in one file often share one."""
    # 1 and "1" are different values, but both are filed under the barcode "1".
    return st.sampled_from([1, "1", None])


def nearly_saved_cards() -> st.SearchStrategy[dict[str, object]]:
    """Make one card as it might sit in a save file: maybe an ``_id``, maybe a name, anything in them."""
    return st.fixed_dictionaries(
        {}, optional={"_id": st.one_of(clashing_ids(), any_json()), "name": any_json()}
    )


def nearly_saved_collections() -> st.SearchStrategy[dict[str, object]]:
    """Make JSON shaped just like a save file, with odd things in the details."""
    return st.fixed_dictionaries(
        {"name": collection_names(), "documents": st.lists(nearly_saved_cards())},
        optional={"indexes": st.lists(st.one_of(field_names(), any_json()))},
    )


# --- Helpers -----------------------------------------------------------------


def folder_holding(
    name: str, cards: dict[str, DocumentData], indexes: list[str] | None = None
) -> Collection:
    """Return a new Collection called ``name``, with every card filed and every index built."""
    collection = Collection(name)
    for doc_id, fields in cards.items():
        collection.insert_one({**fields, "_id": doc_id})
    for field in indexes or []:
        collection.create_index(field)
    return collection


def load_or_refuse(path: Path) -> None:
    """Load the collection at ``path``, accepting only a PersistenceError refusal.

    A PersistenceError is caught and ignored: refusing a bad file is fine. Any
    *other* exception escapes and fails the test, and that is the whole check.
    """
    try:
        load_collection(path)
    except PersistenceError:
        return


# --- Save and load: whatever you file away comes back ------------------------


@given(name=collection_names(), cards=any_cards(), indexes=st.lists(any_field_names()))
def test_save_then_load_gives_back_the_same_collection(
    name: str, cards: dict[str, DocumentData], indexes: list[str]
) -> None:
    """Loading a saved collection gives back the same name, cards (types and all) and indexes."""
    original = folder_holding(name, cards, indexes)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "saved.json"
        save_collection(original, path)
        loaded = load_collection(path)
    assert loaded.name == name
    assert loaded.to_list() == original.to_list()
    # ``==`` thinks True == 1 == 1.0, even inside lists and dicts, so a loader
    # that turned ``[True]`` into ``[1]`` would pass it. ``repr`` writes True
    # as ``True`` and 1.0 as ``1.0``, so it also checks every type, at every depth.
    assert repr(loaded.to_list()) == repr(original.to_list())
    assert loaded.list_indexes() == original.list_indexes()


# --- Finding: the answer a plain Python filter would give ---------------------


@given(cards=folders_of_cards(), field=field_names(), value=query_values())
def test_find_gives_what_a_plain_filter_gives(
    cards: list[DocumentData], field: str, value: Any
) -> None:
    """``find({field: value})`` returns exactly the cards whose field equals value, in order."""
    collection = folder_holding("cards", {str(n): card for n, card in enumerate(cards)})
    expected = [card for card in collection.to_list() if card.get(field) == value]
    assert collection.find({field: value}) == expected


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
    assert with_index == without_index


# --- Loading junk: a bad save file is refused, never a crash ------------------


@given(junk=any_bytes())
def test_any_bytes_on_disk_load_or_raise_persistence_error(junk: bytes) -> None:
    """Whatever bytes are in the file, loading gives a collection or a PersistenceError, never another error."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "saved.json"
        path.write_bytes(junk)
        load_or_refuse(path)


@given(document=st.one_of(any_json(), nearly_saved_collections()))
def test_any_json_on_disk_load_or_raise_persistence_error(document: object) -> None:
    """Whatever JSON is in the file, loading gives a collection or a PersistenceError, never another error."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "saved.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        load_or_refuse(path)
