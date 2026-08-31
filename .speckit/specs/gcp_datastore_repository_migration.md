# Feature Specification: GCP Datastore Migration & Abstract Repository Pattern

## 1. Overview
This specification details the migration of the Connect 4 data layer from a PostgreSQL-only / SQLite dependency to a decoupled **Abstract Repository Pattern** supporting **Google Cloud Datastore (GCP Datastore)** as a primary NoSQL persistence engine, alongside existing SQLModel (PostgreSQL/SQLite) and fast In-Memory implementations.

By decoupling FastAPI endpoints and UI modules from database-specific ORMs, the application can seamlessly switch storage engines at runtime via environment configuration (`DB_BACKEND`), ensuring high scalability, serverless compatibility on GCP (App Engine / Cloud Run / Cloud Functions), and lightweight testing without mandatory external databases.

---

## 2. Technical Architecture & Design Requirements

1. **Domain Model Isolation**:
   - Replace direct SQLModel usage in API endpoints with pure **Pydantic Domain Models** (`PlayerDomain`, `MatchDomain`).
   - Repositories accept and return domain models, encapsulating database-specific entity/table transformations internally.

2. **Polymorphic Repository Pattern**:
   - Abstract Base Class `BasePlayerRepository` defining strict CRUD and query contracts.
   - Three concrete implementations:
     - `DatastorePlayerRepository`: GCP Datastore backend utilizing `google-cloud-datastore`.
     - `SQLModelPlayerRepository`: Relational backend (PostgreSQL / SQLite) via `sqlmodel.Session`.
     - `InMemoryPlayerRepository`: Thread-safe Python `dict`-backed store for ultra-fast local unit tests.

3. **Dependency Injection**:
   - FastAPI endpoints inject repository instances via `get_repository` dependency (`Depends(get_repository)`).
   - Selection controlled by environment variable: `DB_BACKEND` (`datastore` | `postgres` | `sqlite` | `in_memory`).

4. **GCP Datastore Key & Ancestor Design**:
   - **Player Entity**: Keyed deterministically by `username` (Kind: `Player`).
   - **Match Entity**: Auto-generated integer/string ID (Kind: `Match`) with ancestor key set to the associated `Player` entity key `datastore_client.key("Player", username)`.
   - Atomic transactions (`datastore_client.transaction()`) for recording match results and session statistic aggregation.

5. **Leaderboard & Ranking Logic**:
   - Top 10 query: Fetch players ordered by `victories` descending (filtered for `victories + losses + draws > 0`).
   - User Rank computation: Efficient index calculation based on victory count and update timestamp.

---

## 3. Domain Data Definitions

```python
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class PlayerDomain(BaseModel):
    """Pure domain entity for a player."""

    username: str
    victories: int = 0
    losses: int = 0
    draws: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def total_games(self) -> int:
        return self.victories + self.losses + self.draws

    @property
    def win_rate(self) -> float:
        total = self.total_games
        if total == 0:
            return 0.0
        return round((self.victories / total) * 100, 2)


class MatchDomain(BaseModel):
    """Pure domain entity for a completed match log."""

    id: str | int | None = None
    player_username: str
    result: str  # "human_win", "machine_win", "draw"
    played_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
```

---

## 4. Repository Interface & Concrete Classes

```
connect4/db/
├── __init__.py           # Export factory get_repository
├── domain.py             # Pure Pydantic domain models (PlayerDomain, MatchDomain)
├── base.py               # Abstract base class (BasePlayerRepository)
├── datastore_repo.py     # DatastorePlayerRepository implementation
├── sqlmodel_repo.py      # SQLModelPlayerRepository (Postgres / SQLite)
├── inmemory_repo.py      # InMemoryPlayerRepository (Unit testing)
└── engine.py             # DB engine / Datastore client initializers
```

### Abstract Base Interface (`BasePlayerRepository`)
- `get_by_username(username: str) -> PlayerDomain | None`
- `create_player(username: str) -> PlayerDomain`
- `get_or_create(username: str) -> PlayerDomain`
- `record_match_result(username: str, result: str) -> MatchDomain`
- `sync_session_stats(username: str, wins: int, losses: int, draws: int) -> PlayerDomain | None`
- `get_top_players(limit: int = 10) -> list[PlayerDomain]`
- `get_player_rank(username: str) -> int | None`
- `can_view_leaderboard(username: str) -> bool`

---

## 5. Dependency Injection Configuration

```python
# connect4/db/__init__.py
import os
from connect4.db.base import BasePlayerRepository
from connect4.db.datastore_repo import DatastorePlayerRepository
from connect4.db.sqlmodel_repo import SQLModelPlayerRepository
from connect4.db.inmemory_repo import InMemoryPlayerRepository

_repository_instance: BasePlayerRepository | None = None


def get_repository() -> BasePlayerRepository:
    """FastAPI dependency for injecting the configured repository backend."""
    global _repository_instance
    if _repository_instance is not None:
        return _repository_instance

    backend = os.environ.get("DB_BACKEND", "datastore").lower()

    if backend == "datastore":
        _repository_instance = DatastorePlayerRepository()
    elif backend in ("postgres", "postgresql", "sqlite"):
        _repository_instance = SQLModelPlayerRepository()
    elif backend == "in_memory":
        _repository_instance = InMemoryPlayerRepository()
    else:
        raise ValueError(f"Unsupported DB_BACKEND: {backend}")

    return _repository_instance
```

---

## 6. GCP Datastore Entity Structure & Query Strategy

### Entity Schemas
1. **Kind**: `Player`
   - Key: `Key('Player', username)`
   - Properties:
     - `username` (string, indexed)
     - `victories` (integer, indexed)
     - `losses` (integer)
     - `draws` (integer)
     - `created_at` (timestamp)
     - `updated_at` (timestamp, indexed)

2. **Kind**: `Match`
   - Key: `Key('Player', username, 'Match', auto_id)` (Ancestor: Player)
   - Properties:
     - `result` (string)
     - `played_at` (timestamp)

### Transactional Operations
- `record_match_result`: Executes within a Datastore `transaction()`. Reads `Player` entity key, increments outcome counter (`victories`/`losses`/`draws`), updates `updated_at`, creates a `Match` child entity, and commits atomically.
- `sync_session_stats`: Similar transaction block for bulk session deltas.

---

## 7. Testing & Emulator Setup

- **Fast Unit Tests**: Pytest defaults to `DB_BACKEND=in_memory` via fixture, executing without network overhead or database setup.
- **Datastore Integration Tests**: Run with `DB_BACKEND=datastore` connected to Google Cloud Datastore Emulator via `DATASTORE_EMULATOR_HOST=localhost:8081`.
- **Relational Tests**: Run with `DB_BACKEND=sqlite` for SQLModel regression checks.

---

## 8. Migration Plan
1. Add `google-cloud-datastore>=2.19.0` to `pyproject.toml`.
2. Implement domain models (`domain.py`) and abstract repo (`base.py`).
3. Implement `DatastorePlayerRepository`, `SQLModelPlayerRepository`, and `InMemoryPlayerRepository`.
4. Refactor `connect4/api.py` to use `Depends(get_repository)` dependency injection.
5. Update tests to verify repository contracts across all three backends.
