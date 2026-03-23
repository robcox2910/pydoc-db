"""Collection module -- a named group of documents.

Think of a collection like a folder in a filing cabinet. Each folder has a
label (like "Students" or "Products") and holds a bunch of index cards
(documents). You can add new cards, search through them, update existing
ones, or throw some away.

Unlike a relational database table where every row must have the same
columns, a collection is flexible -- each document can have completely
different fields! One student card might have a "nickname" field while
another doesn't.
"""

from typing import Any

from pydocdb.document import Document, DocumentData
from pydocdb.errors import DocumentNotFoundError, DuplicateKeyError
from pydocdb.indexing import Index
from pydocdb.projection import apply_projection
from pydocdb.query import matches


class Collection:
    """A named group of documents, like a folder in a filing cabinet.

    Supports full CRUD operations: Create (insert), Read (find),
    Update, and Delete.

    Attributes:
        name: The name of this collection.

    """

    def __init__(self, name: str) -> None:
        """Create a new empty collection.

        Args:
            name: The name for this collection (like a folder label).

        """
        self.name: str = name
        self._documents: dict[str, Document] = {}
        self._indexes: dict[str, Index] = {}

    def insert_one(self, data: DocumentData) -> Document:
        """Insert a single document into the collection.

        Like filing a new index card into the folder. The document gets an
        auto-generated ``_id`` if it doesn't already have one.

        Args:
            data: A dictionary of fields and values for the new document.

        Returns:
            The inserted Document (with its ``_id``).

        Raises:
            DuplicateKeyError: If a document with the same _id already exists.

        """
        doc = Document(data)
        if doc.id in self._documents:
            msg = f"Document with _id '{doc.id}' already exists"
            raise DuplicateKeyError(msg)

        self._documents[doc.id] = doc
        self._index_document(doc)
        return doc

    def insert_many(self, data_list: list[DocumentData]) -> list[Document]:
        """Insert multiple documents at once.

        Like filing a whole stack of index cards at once.

        Args:
            data_list: A list of dictionaries, each becoming a document.

        Returns:
            A list of the inserted Documents.

        """
        return [self.insert_one(data) for data in data_list]

    def find_one(
        self,
        query: dict[str, Any] | None = None,
        projection: dict[str, int] | None = None,
    ) -> DocumentData | None:
        """Find the first document that matches the query.

        Like asking the librarian: "Find me ONE book about science."

        Args:
            query: Conditions to match (empty or None means "any document").
            projection: Fields to include/exclude from the result.

        Returns:
            The matching document's data as a dict, or None if not found.

        """
        query = query or {}
        for doc in self._documents.values():
            if matches(doc, query):
                result = doc.to_dict()
                if projection:
                    return apply_projection(result, projection)
                return result
        return None

    def find(
        self,
        query: dict[str, Any] | None = None,
        projection: dict[str, int] | None = None,
    ) -> list[DocumentData]:
        """Find all documents matching the query.

        Like asking the librarian: "Find me ALL books about science."

        Args:
            query: Conditions to match (empty or None means "all documents").
            projection: Fields to include/exclude from results.

        Returns:
            A list of matching document data dicts.

        """
        query = query or {}
        results: list[DocumentData] = []
        for doc in self._documents.values():
            if matches(doc, query):
                result = doc.to_dict()
                if projection:
                    result = apply_projection(result, projection)
                results.append(result)
        return results

    def find_by_id(self, doc_id: str) -> DocumentData:
        """Find a document by its ``_id``.

        Like grabbing a specific index card by its number.

        Args:
            doc_id: The document's unique identifier.

        Returns:
            The document's data as a dictionary.

        Raises:
            DocumentNotFoundError: If no document has that _id.

        """
        doc = self._documents.get(doc_id)
        if doc is None:
            msg = f"No document found with _id '{doc_id}'"
            raise DocumentNotFoundError(msg)
        return doc.to_dict()

    def update_one(
        self,
        query: dict[str, Any],
        update: DocumentData,
    ) -> bool:
        """Update the first document matching the query.

        Like erasing part of an index card and writing new info.

        Args:
            query: Conditions to find the document to update.
            update: A dictionary of fields to change or add.

        Returns:
            True if a document was updated, False if none matched.

        """
        for doc in self._documents.values():
            if matches(doc, query):
                self._unindex_document(doc)
                doc.data.update(update)
                self._index_document(doc)
                return True
        return False

    def update_many(
        self,
        query: dict[str, Any],
        update: DocumentData,
    ) -> int:
        """Update all documents matching the query.

        Args:
            query: Conditions to find the documents to update.
            update: A dictionary of fields to change or add.

        Returns:
            The number of documents updated.

        """
        count = 0
        for doc in self._documents.values():
            if matches(doc, query):
                self._unindex_document(doc)
                doc.data.update(update)
                self._index_document(doc)
                count += 1
        return count

    def delete_one(self, query: dict[str, Any]) -> bool:
        """Delete the first document matching the query.

        Like pulling an index card out of the folder and shredding it.

        Args:
            query: Conditions to find the document to delete.

        Returns:
            True if a document was deleted, False if none matched.

        """
        for doc in list(self._documents.values()):
            if matches(doc, query):
                self._unindex_document(doc)
                del self._documents[doc.id]
                return True
        return False

    def delete_many(self, query: dict[str, Any]) -> int:
        """Delete all documents matching the query.

        Args:
            query: Conditions to find documents to delete.

        Returns:
            The number of documents deleted.

        """
        to_delete = [doc for doc in self._documents.values() if matches(doc, query)]
        for doc in to_delete:
            self._unindex_document(doc)
            del self._documents[doc.id]
        return len(to_delete)

    def count(self, query: dict[str, Any] | None = None) -> int:
        """Count documents matching the query.

        Args:
            query: Conditions to match (None means "count all").

        Returns:
            The number of matching documents.

        """
        if not query:
            return len(self._documents)
        return sum(1 for doc in self._documents.values() if matches(doc, query))

    def create_index(self, field: str) -> Index:
        """Create an index on a field for faster lookups.

        Like building an index at the back of a textbook so you can
        find topics quickly instead of reading every page.

        Args:
            field: The field to index (supports dot notation).

        Returns:
            The created Index object.

        """
        index = Index(field)
        for doc in self._documents.values():
            index.add(doc)
        self._indexes[field] = index
        return index

    def drop_index(self, field: str) -> bool:
        """Remove an index on a field.

        Args:
            field: The field whose index to remove.

        Returns:
            True if the index existed and was removed.

        """
        if field in self._indexes:
            del self._indexes[field]
            return True
        return False

    def list_indexes(self) -> list[str]:
        """List all indexed fields.

        Returns:
            A list of field names that have indexes.

        """
        return list(self._indexes.keys())

    def to_list(self) -> list[DocumentData]:
        """Export all documents as a list of dictionaries.

        Returns:
            A list of all document data dicts.

        """
        return [doc.to_dict() for doc in self._documents.values()]

    def clear(self) -> None:
        """Remove all documents and reset indexes."""
        self._documents.clear()
        for index in self._indexes.values():
            index.clear()

    def _index_document(self, doc: Document) -> None:
        """Add a document to all indexes.

        Args:
            doc: The document to index.

        """
        for index in self._indexes.values():
            index.add(doc)

    def _unindex_document(self, doc: Document) -> None:
        """Remove a document from all indexes.

        Args:
            doc: The document to un-index.

        """
        for index in self._indexes.values():
            index.remove(doc)

    def __len__(self) -> int:
        """Return the number of documents in the collection."""
        return len(self._documents)

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"Collection(name={self.name!r}, documents={len(self)})"
