# Task Breakdown: GCP Datastore Migration & Abstract Repository Pattern

## Phase 1: Domain Models & Dependencies
- [x] **Task 1.1**: Add `google-cloud-datastore` dependency to `pyproject.toml` and update virtual environment using `uv sync`.
- [x] **Task 1.2**: Create `connect4/db/domain.py` with pure Pydantic models (`PlayerDomain`, `MatchDomain`).
- [x] **Task 1.3**: Create `connect4/db/base.py` defining abstract `BasePlayerRepository` interface.

## Phase 2: Repository Backend Implementations
- [x] **Task 2.1**: Implement `connect4/db/inmemory_repo.py` (`InMemoryPlayerRepository`) for zero-dependency unit tests.
- [x] **Task 2.2**: Implement `connect4/db/sqlmodel_repo.py` (`SQLModelPlayerRepository`) refactoring legacy SQLModel logic.
- [x] **Task 2.3**: Implement `connect4/db/datastore_repo.py` (`DatastorePlayerRepository`) with Google Cloud Datastore transactions and entity keys.
- [x] **Task 2.4**: Create factory function `get_repository()` in `connect4/db/__init__.py` using `DB_BACKEND` environment variable (`datastore` | `postgres` | `sqlite` | `in_memory`).

## Phase 3: Web API Dependency Injection
- [x] **Task 3.1**: Refactor `connect4/api.py` endpoints to inject `repo: BasePlayerRepository = Depends(get_repository)`.
- [x] **Task 3.2**: Remove direct database session coupling in `new_game`, `make_move`, `get_player_profile`, `sync_player_session`, and `get_leaderboard`.

## Phase 4: Automated Testing & Multi-Backend Verification
- [x] **Task 4.1**: Update `tests/test_repository_and_leaderboard.py` to test abstract repository methods across `InMemoryPlayerRepository` and `SQLModelPlayerRepository`.
- [x] **Task 4.2**: Add `tests/test_datastore_repository.py` for Datastore emulator / mock verification.
- [x] **Task 4.3**: Run `pytest` across all backends to verify 100% test passing.
