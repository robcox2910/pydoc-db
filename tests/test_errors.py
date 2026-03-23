"""Tests for custom exceptions."""

import pytest

from pydocdb.errors import (
    CollectionExistsError,
    DocumentNotFoundError,
    DuplicateKeyError,
    InvalidFieldError,
    InvalidPipelineError,
    InvalidQueryError,
    PersistenceError,
    PyDocDBError,
)


class TestExceptionHierarchy:
    """Test that all exceptions inherit from PyDocDBError."""

    @pytest.mark.parametrize(
        "exc_class",
        [
            DocumentNotFoundError,
            DuplicateKeyError,
            InvalidQueryError,
            InvalidFieldError,
            CollectionExistsError,
            InvalidPipelineError,
            PersistenceError,
        ],
    )
    def test_inherits_from_base(self, exc_class: type[PyDocDBError]) -> None:
        """Verify each exception is a subclass of PyDocDBError."""
        assert issubclass(exc_class, PyDocDBError)

    @pytest.mark.parametrize(
        "exc_class",
        [
            DocumentNotFoundError,
            DuplicateKeyError,
            InvalidQueryError,
            InvalidFieldError,
            CollectionExistsError,
            InvalidPipelineError,
            PersistenceError,
        ],
    )
    def test_can_be_raised_and_caught(self, exc_class: type[PyDocDBError]) -> None:
        """Verify each exception can be raised and caught."""
        msg = "test message"
        with pytest.raises(PyDocDBError):
            raise exc_class(msg)
