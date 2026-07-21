# Task Breakdown: Player Persistence, Stats & Leaderboard

## Phase 1: Dependencies & Database Foundation
- [ ] **Task 1.1**: Add `sqlmodel` and `psycopg2-binary` to `pyproject.toml` dependencies and sync virtual environment.
- [ ] **Task 1.2**: Create `connect4/db/__init__.py` and `connect4/db/models.py` defining `Player` and `Match` SQLModel tables and Pydantic schemas.
- [ ] **Task 1.3**: Create `connect4/db/engine.py` to establish database engines for PostgreSQL (with SQLite fallback for local dev/testing).

## Phase 2: SRP Repository Layer
- [ ] **Task 2.1**: Implement `connect4/db/repository.py` with Single Responsibility functions:
  - `get_player_by_username(session, username)`
  - `create_player(session, username)`
  - `record_match_result(session, player_id, result)`
  - `sync_session_stats(session, player_id, wins, losses, draws)`
  - `get_top_players(session, limit)`
  - `get_player_rank(session, username)`
  - `can_view_leaderboard(session, username)` ($\ge 1$ match requirement)

## Phase 3: Web API Integration
- [ ] **Task 3.1**: Update `connect4/api.py` endpoints:
  - `GET /api/players/{username}`: Return profile, stats, and `can_view_leaderboard` status.
  - `GET /api/leaderboard?username={username}`: Return Top 10 leaderboard + user rank (return HTTP 403 if user has 0 played matches).
  - `POST /api/players/{username}/sync_session`: Aggregate session stats.
  - Update `/api/game/{session_id}/move` to record match completion in DB.

## Phase 4: Desktop Interface (Pygame)
- [ ] **Task 4.1**: Update `StartScreen` in `connect4/ui.py`:
  - Show player's historical victories when typing username.
  - Show "Leaderboard" button ONLY if user is an existing player ($\ge 1$ match played) or unlocked.
- [ ] **Task 4.2**: Add `LeaderboardScreen` / Modal rendering Top 10 players and active user position.
- [ ] **Task 4.3**: Integrate session aggregation & match finish logic to record stats and unlock leaderboard for new players upon match completion.

## Phase 5: Automated Testing & Verification
- [ ] **Task 5.1**: Implement `tests/test_repository_and_leaderboard.py` covering repository functions, visibility rules, and API endpoints.
- [ ] **Task 5.2**: Run `uv run python -m pytest` and verify all tests pass.
