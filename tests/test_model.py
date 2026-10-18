"""Model check -- a Collection must behave exactly like a plain list of dicts.

A property test checks one rule for many inputs. A *model check* goes
further: Hypothesis invents a random *story* -- file this card, update
those, delete that one, build an index, search -- and plays it on two
things at once:

- the real ``Collection``;
- a **model**: a plain Python ``list`` of ``dict`` cards, which we already
  trust to be right.

After every step the two must agree. If they ever disagree, Hypothesis
shrinks the story to the shortest list of steps that still goes wrong.

The model is deliberately *not* a copy of ``Collection``'s code. It has no
``_id`` lookup table, no indexes and no query engine: every search is a
plain loop over the list, the simplest thing that is obviously correct.
So when the two disagree, the collection is the one to suspect.

See ``docs/property-testing.md`` for the walk-through.
"""

import copy
import unittest
from typing import Any, cast

import pytest
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, invariant, rule

from pydocdb.collection import Collection
from pydocdb.document import DocumentData
from pydocdb.errors import DocumentNotFoundError, DuplicateKeyError
from tests.strategies import (
    MOST_CARDS_PER_FOLDER,
    any_values,
    document_fields,
    document_ids,
    field_names,
    query_values,
)


def update_fields() -> st.SearchStrategy[DocumentData]:
    """Make the changes for an update: some shared fields, and sometimes a new ``_id`` too."""
    return st.dictionaries(st.one_of(field_names(), st.just("_id")), any_values())


def scribble_inside(card: DocumentData) -> None:
    """Add to every list and dict inside a card, the way careless code might."""
    for value in card.values():
        if isinstance(value, list):
            value.append("scribble")
        elif isinstance(value, dict):
            value["scribble"] = True


def without_id(changes: DocumentData) -> DocumentData:
    """Return a deep copy of the changes, minus ``_id``: an update never changes a barcode."""
    # Collection.update_one's docstring: "any ``_id`` in the update is ignored".
    return copy.deepcopy({key: value for key, value in changes.items() if key != "_id"})


# --- The machine: one story, played on the collection and on a list ----------


class CollectionMachine(RuleBasedStateMachine):
    """Play random inserts, updates, deletes, searches and indexes on a Collection and a list."""

    # ``_id``s we've used before. Brand-new random ids almost never repeat, so
    # rules also pick from here to insert a clashing card, or look up a card
    # that really is (or was) in the collection.
    ids = Bundle("ids")

    def __init__(self) -> None:
        """Start with an empty collection, an empty list and no indexes."""
        super().__init__()
        self.collection = Collection("cards")
        self.model: list[DocumentData] = []
        self.indexed_fields: list[str] = []

    def ids_in_model(self) -> set[str]:
        """Return every ``_id`` the list holds."""
        return {card["_id"] for card in self.model}

    def matching(self, field: str, value: Any) -> list[DocumentData]:
        """Return the cards in the list whose field equals value, in filing order."""
        return [card for card in self.model if card.get(field) == value]

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

    @rule(
        doc_ids=st.lists(st.one_of(ids, document_ids()), max_size=MOST_CARDS_PER_FOLDER),
        fields=document_fields(),
    )
    def insert_many(self, doc_ids: list[str], fields: DocumentData) -> None:
        """File a stack of cards: all of them, or none if any ``_id`` is taken or repeated."""
        cards = [{**fields, "_id": doc_id} for doc_id in doc_ids]
        clash = len(set(doc_ids)) < len(doc_ids) or bool(set(doc_ids) & self.ids_in_model())
        if clash:
            with pytest.raises(DuplicateKeyError):
                self.collection.insert_many(cards)
        else:
            self.collection.insert_many(cards)
            self.model.extend(copy.deepcopy(cards))

    @rule(doc_id=st.one_of(ids, document_ids()))
    def find_by_id(self, doc_id: str) -> None:
        """Look a card up by ``_id``: the list's card, or DocumentNotFoundError if it has none."""
        cards = [card for card in self.model if card["_id"] == doc_id]
        if cards:
            assert self.collection.find_by_id(doc_id) == cards[0]
        else:
            with pytest.raises(DocumentNotFoundError):
                self.collection.find_by_id(doc_id)

    @rule(field=field_names(), value=query_values())
    def find(self, field: str, value: Any) -> None:
        """Search on one field: the same cards, in the same order, as a plain loop over the list."""
        expected = self.matching(field, value)
        assert self.collection.find({field: value}) == expected
        assert self.collection.count({field: value}) == len(expected)
        assert self.collection.find_one({field: value}) == (expected[0] if expected else None)

    @rule(field=field_names(), which=st.integers(min_value=0))
    def find_a_value_some_card_has(self, field: str, which: int) -> None:
        """Search for a value one real card holds: the same cards as a plain loop."""
        if not self.model:
            return
        value = self.model[which % len(self.model)].get(field)
        # ``$eq`` spells out "equals", so even a dict value is looked for, not
        # read as operators (see docs/concepts/queries.md).
        query = {field: {"$eq": value}}
        expected = self.matching(field, value)
        assert self.collection.find(query) == expected

    @rule(field=field_names(), value=query_values(), changes=update_fields())
    def update_one(self, field: str, value: Any, changes: DocumentData) -> None:
        """Change the first matching card in both; say True exactly when there was one."""
        expected = self.matching(field, value)
        if expected:
            expected[0].update(without_id(changes))
        assert self.collection.update_one({field: value}, changes) == bool(expected)

    @rule(field=field_names(), value=query_values(), changes=update_fields())
    def update_many(self, field: str, value: Any, changes: DocumentData) -> None:
        """Change every matching card in both, and say how many."""
        expected = self.matching(field, value)
        for card in expected:
            card.update(without_id(changes))
        assert self.collection.update_many({field: value}, changes) == len(expected)

    @rule(field=field_names(), value=query_values())
    def delete_one(self, field: str, value: Any) -> None:
        """Shred the first matching card in both; say True exactly when there was one."""
        expected = self.matching(field, value)
        if expected:
            self.model.remove(expected[0])
        assert self.collection.delete_one({field: value}) == bool(expected)

    @rule(field=field_names(), value=query_values())
    def delete_many(self, field: str, value: Any) -> None:
        """Shred every matching card in both, and say how many."""
        expected = self.matching(field, value)
        self.model = [card for card in self.model if card not in expected]
        assert self.collection.delete_many({field: value}) == len(expected)

    @rule(field=field_names())
    def create_index(self, field: str) -> None:
        """Build an index on a field; the list just notes the field's name."""
        self.collection.create_index(field)
        if field not in self.indexed_fields:
            self.indexed_fields.append(field)

    @rule(field=field_names())
    def drop_index(self, field: str) -> None:
        """Remove an index; say True exactly when there was one."""
        was_there = field in self.indexed_fields
        if was_there:
            self.indexed_fields.remove(field)
        assert self.collection.drop_index(field) == was_there

    @rule()
    def scribble_on_found_cards(self) -> None:
        """Scribble inside every card ``find`` hands back; the filed cards must not change."""
        # Nothing changes in the list, so the invariant checks the folder is untouched.
        for card in self.collection.find():
            scribble_inside(card)

    @rule(doc_id=document_ids(), fields=document_fields())
    def scribble_on_an_inserted_card(self, doc_id: str, fields: DocumentData) -> None:
        """File a card, then scribble inside the Document handed back; the filed card must not change."""
        if doc_id in self.ids_in_model():
            return
        card = {**fields, "_id": doc_id}
        returned = self.collection.insert_one(card)
        self.model.append(copy.deepcopy(card))
        scribble_inside(returned.data)

    @rule()
    def clear(self) -> None:
        """Empty both. The indexes stay, empty, ready for new cards."""
        self.collection.clear()
        self.model.clear()

    @invariant()
    def same_cards_and_indexes(self) -> None:
        """After every step, the collection holds exactly the list's cards, in order."""
        assert len(self.collection) == len(self.model)
        assert self.collection.count() == len(self.model)
        assert self.collection.to_list() == self.model
        assert self.collection.find() == self.model
        assert self.collection.list_indexes() == self.indexed_fields


# why: 20 steps find the same bugs; 50 (the default) is most of the run time
CollectionMachine.TestCase.settings = settings(stateful_step_count=20)
# pytest runs this like any other test class: one run plays 100 random stories.
# (Hypothesis doesn't say what type ``TestCase`` is, so ``cast`` tells pyright.)
TestCollectionModel = cast("type[unittest.TestCase]", CollectionMachine.TestCase)
