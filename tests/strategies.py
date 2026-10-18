"""Strategies -- recipes for random documents, shared by the property tests.

A strategy tells Hypothesis how to invent one kind of input. Each one here
is a named function, named for what it makes, with a one-line docstring.
``tests/test_properties.py`` and ``tests/test_model.py`` both use them.
"""

from typing import Any

from hypothesis import strategies as st

from pydocdb.document import DocumentData

# Every document in a test collection uses some of these field names. With a
# few names shared by every card, queries, updates and indexes really hit
# something; with fully random names they would almost never match. None has
# a dot in it: in a query, "pet.name" means "look inside pet" (see
# docs/concepts/nested.md), so a field *called* "pet.name" is a different thing.
FIELD_NAMES = ("name", "age", "pet")

# A test folder holds at most this many cards. Hypothesis would otherwise
# invent dozens, each full of nested values, which is slow; a bug that needs
# a crowd is rare, and a failure shrinks to one or two cards anyway.
MOST_CARDS_PER_FOLDER = 5


def plain_values() -> st.SearchStrategy[Any]:
    """Make one simple JSON value: text, a whole number, a decimal, True/False or None."""
    return st.one_of(
        st.text(),
        st.integers(),
        # NaN ("not a number") is never equal to itself, not even to a copy
        # of itself, so ``==`` could never confirm it came back. That's a
        # rule of floats, not of PyDocDB, so it's left out; infinity stays in.
        st.floats(allow_nan=False),
        st.booleans(),
        st.none(),
    )


def lists_and_dicts_of(children: st.SearchStrategy[Any]) -> st.SearchStrategy[Any]:
    """Make a list, or a dict with text keys, holding values made by ``children``."""
    return st.one_of(st.lists(children), st.dictionaries(st.text(), children))


def any_values() -> st.SearchStrategy[Any]:
    """Make any value a document can hold: a plain value, or lists and dicts up to two deep."""
    # save_collection's docstring: JSON stores text, numbers, lists and dicts.
    # Two levels (like [[1], {"a": None}]) find the same bugs as twenty, and
    # Hypothesis invents them several times faster than ``st.recursive`` does.
    one_deep = lists_and_dicts_of(plain_values())
    return st.one_of(plain_values(), lists_and_dicts_of(st.one_of(plain_values(), one_deep)))


def field_names() -> st.SearchStrategy[str]:
    """Pick one of the few field names every test document draws from."""
    return st.sampled_from(FIELD_NAMES)


def document_fields() -> st.SearchStrategy[DocumentData]:
    """Make the fields of one index card: some of the shared names, each with any value."""
    return st.dictionaries(field_names(), any_values())


def document_ids() -> st.SearchStrategy[str]:
    """Make an ``_id`` for a document: any text at all, even the empty string."""
    return st.text()
