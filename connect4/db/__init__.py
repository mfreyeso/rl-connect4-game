"""Database package for Connect 4 providing abstract repository injection."""

import os
import threading
from connect4.db.base import BasePlayerRepository
from connect4.db.inmemory_repo import InMemoryPlayerRepository
from connect4.db.sqlmodel_repo import SQLModelPlayerRepository

_repository_instance: BasePlayerRepository | None = None
_init_lock = threading.Lock()


def get_repository() -> BasePlayerRepository:
    """Provide active repository instance based on DB_BACKEND environment variable."""
    global _repository_instance
    if _repository_instance is not None:
        return _repository_instance

    with _init_lock:
        # Double-checked locking: re-check after acquiring the lock
        if _repository_instance is not None:
            return _repository_instance

        backend = os.environ.get("DB_BACKEND")
        if not backend:
            import sys

            is_testing = "pytest" in sys.modules or os.environ.get("ENV") == "testing"
            if is_testing:
                backend = "in_memory"
            elif "DATABASE_URL" in os.environ:
                backend = "postgres"
            else:
                backend = "datastore"
        else:
            backend = backend.lower()

        if backend == "datastore":
            from connect4.db.datastore_repo import DatastorePlayerRepository

            _repository_instance = DatastorePlayerRepository()
        elif backend in ("postgres", "postgresql", "sqlite"):
            _repository_instance = SQLModelPlayerRepository()
        elif backend == "in_memory":
            _repository_instance = InMemoryPlayerRepository()
        else:
            _repository_instance = InMemoryPlayerRepository()

        return _repository_instance


def set_repository(repo: BasePlayerRepository | None) -> None:
    """Override repository instance (useful for testing)."""
    global _repository_instance
    _repository_instance = repo


__all__ = [
    "BasePlayerRepository",
    "InMemoryPlayerRepository",
    "SQLModelPlayerRepository",
    "get_repository",
    "set_repository",
]
