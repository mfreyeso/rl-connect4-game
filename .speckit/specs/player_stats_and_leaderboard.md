# Feature Specification: Player Stats, Persistence & Leaderboard

## 1. Overview
This specification defines the persistence of player match results, historical stats aggregation, and global leaderboard rankings for Connect 4. When a player inputs a unique username, the application fetches their past victories and stats, aggregates newly completed game sessions, and displays both the top 10 leaderboard and the player's overall rank.

---

## 2. Technical Architecture & UX Requirements

1. **ORM & Data Layer**:
   - Built using **SQLModel** (combining Pydantic and SQLAlchemy ORM capabilities).
   - Uses the **Repository Pattern** (`PlayerRepository`, `MatchRepository`) with Single Responsibility Principle (SRP) functions to decouple DB engines (PostgreSQL adapter vs SQLite fallback adapter) from business logic.

2. **User Identification**:
   - Passwordless / simple unique nickname entry matching existing Pygame UI behavior.
   - Entering a unique username loads the existing player profile (`victories`, `losses`, `draws`, `total_games`).
   - If the username does not exist, a new profile is initialized (`total_games = 0`).

3. **Leaderboard Visibility Rules**:
   - **Existing Users** (players with $\ge 1$ recorded match): Can view the Top 10 leaderboard and their rank immediately (e.g. from the main menu / start screen).
   - **New Users** (players with 0 matches): Leaderboard access is unlocked ONLY after completing their first match.

4. **Session Aggregation & Persistence**:
   - Scores aggregate dynamically during an active gameplay session.
   - Match outcomes and aggregated session stats are committed to persistence upon match completion or returning to the main menu.

5. **Leaderboard Ranking Logic**:
   - Top 10 leaderboard ranked primarily by **Total Victories** (wins) descending. Ties broken by total games played and update timestamp.
   - System computes and displays the user's exact global rank (e.g., `#4 of 120 players`).

---

## 3. SQLModel Data Definitions

### Class `Player` (table=True)
- `id`: Optional[int] (Primary Key)
- `username`: str (Unique, Indexed)
- `victories`: int = 0
- `losses`: int = 0
- `draws`: int = 0
- `created_at`: datetime
- `updated_at`: datetime

### Class `Match` (table=True)
- `id`: Optional[int] (Primary Key)
- `player_id`: int (Foreign Key -> `player.id`)
- `result`: str (`"human_win"`, `"machine_win"`, `"draw"`)
- `played_at`: datetime

---

## 4. Repository & SRP Architecture

```
connect4/db/
├── models.py         # SQLModel entity definitions (Player, Match, schemas)
├── repository.py     # Abstract / SRP repository functions (PlayerRepository)
└── engine.py         # Database engine setup (PostgreSQL URL / SQLite fallback)
```

### SRP Repository Functions:
- `get_player_by_username(session, username: str) -> Player | None`
- `create_player(session, username: str) -> Player`
- `record_match(session, player_id: int, result: str) -> Match`
- `update_player_stats(session, player_id: int, wins: int, losses: int, draws: int) -> Player`
- `get_top_players(session, limit: int = 10) -> list[Player]`
- `get_player_rank(session, username: str) -> int | None`

---

## 5. API Endpoints

- `GET /api/players/{username}`
  - Returns player profile + `has_played` flag (`total_games >= 1`).
- `GET /api/leaderboard?username={username}`
  - Returns Top 10 leaderboard and `user_rank`. If `username` is a new user (`has_played == False`), returns a `403 Leaderboard Locked` response until 1 match is finished.
- `POST /api/players/{username}/sync_session`
  - Aggregates session wins/losses/draws to player profile.
