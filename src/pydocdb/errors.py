"""Custom exceptions for PyDocDB.

Think of these like warning signs in a library. When something goes wrong --
like trying to find a book that doesn't exist, or putting a book in the wrong
section -- the library puts up a sign telling you what happened. These
exceptions are PyDocDB's way of telling you exactly what went wrong so you
can fix it!
"""


class PyDocDBError(Exception):
    """Base exception for all PyDocDB errors.

    This is like the main "Something went wrong!" sign. All other, more
    specific signs are types of this one.
    """


class DocumentNotFoundError(PyDocDBError):
    """Raise when a document cannot be found by its _id.

    Like looking for a specific index card in a filing cabinet and
    discovering it's not there.
    """


class DuplicateKeyError(PyDocDBError):
    """Raise when inserting a document with an _id that already exists.

    Like trying to file two different index cards with the same number --
    every card needs its own unique number!
    """


class InvalidQueryError(PyDocDBError):
    """Raise when a query contains an unknown or malformed operator.

    Like asking a librarian to find books using a search method they
    don't understand -- "Find me all books that smell like chocolate"
    isn't a valid search!
    """


class InvalidPipelineError(PyDocDBError):
    """Raise when an aggregation pipeline stage is invalid.

    Like giving the librarian a set of instructions where one of the
    steps doesn't make sense -- "Step 3: Turn the books into frogs"
    isn't something they can do!
    """


class PersistenceError(PyDocDBError):
    """Raise when saving or loading data from disk fails.

    Like trying to save your work to a USB drive that's been unplugged,
    or opening a file that got corrupted.
    """
