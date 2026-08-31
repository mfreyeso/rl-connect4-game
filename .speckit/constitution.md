# Project Constitution: RL Connect 4 Game

## 1. Core Mission & Vision
The **RL Connect 4 Game** is a hybrid desktop and web application combining Reinforcement Learning (Q-learning and Deep RL) with interactive Connect 4 gameplay.
The project evolves from a local single-player (Human vs. AI) experience into a robust, deployed full-stack multiplayer platform with player authentication, rating, match history persistence, and configurable game modes.

---

## 2. Technology Stack & Environment Standards
- **Language & Runtime**: Python >= 3.12.
- **Dependency & Package Manager**: `uv` (`pyproject.toml` with `uv.lock`).
- **Game Engine & Rendering**: `pygame` >= 2.6.1 for desktop UI; modular board & environment logic decoupled from rendering.
- **Web API & Server**: `fastapi` >= 0.115.0 with `uvicorn[standard]` >= 0.34.0, including `slowapi` for rate limiting.
- **Persistence & Database**: `GCP Datastore` (Google Cloud Datastore NoSQL) as primary cloud persistence backend; `SQLModel` (PostgreSQL/SQLite) and thread-safe `In-Memory` stores supported via Abstract Repository injection (`DB_BACKEND`).
- **Tooling & Code Quality**:
  - Formatter & Linter: `black` (24.x), `pre-commit`.
  - Type Checker: `ty` / `mypy`.
  - Testing Framework: `pytest` >= 9.0.2 with `httpx` for API testing.

---

## 3. System Architecture & Component Boundaries

### 3.1 Layered Architecture
1. **Game Engine (`connect4.environment`)**:
   - Holds core game state, move validation, win/draw detection, and board state encoding.
   - Must remain 100% UI-agnostic and network-agnostic.
2. **Reinforcement Learning (`connect4.qlearning` & AI module)**:
   - Houses Q-learning agent logic, state representation hash/serialization, action selection policies ($\epsilon$-greedy), and Q-table/model loading.
   - Scalable to deep neural network policy models.
3. **Persistence & Data Layer (`connect4.db`)**:
   - Abstract Repository interface (`BasePlayerRepository`) with dependency injection (`get_repository()`).
   - Implementations: GCP Datastore (`DatastorePlayerRepository`), SQLModel PostgreSQL/SQLite (`SQLModelPlayerRepository`), and fast testing (`InMemoryPlayerRepository`).
4. **Web & Real-Time API (`connect4.api`)**:
   - RESTful endpoints for authentication, player stats, and historical match retrieval.
   - WebSocket endpoints for real-time multiplayer move broadcasting and match synchronization.
5. **Desktop Interface (`connect4.ui`)**:
   - Pygame rendering, event loop handling, menu navigation, and API/local engine integration.

---

## 4. Feature Evolution & Roadmap

### Phase 1: Local & Base API (Current)
- Pygame GUI supporting Human vs. Human, Human vs. AI (Q-Table), AI vs. AI modes.
- Q-Learning training scripts and table serialization (`q_table.pkl`).
- Basic FastAPI wrapper for remote moves.

### Phase 2: Persistence & Player History
- Integration with PostgreSQL for storing user profiles, win/loss records, match replays/logs.
- API endpoints for leaderboards, player stats, and match history breakdown.

### Phase 3: Online Multiplayer & Advanced AI
- Real-time multiplayer matchmaking via WebSockets with server-side move verification.
- Neural network Q-value approximation (DQN / Deep RL) with configurable difficulty levels.

---

## 5. Development Guidelines & Code Standards
1. **Separation of Concerns**: Never embed game rule logic directly inside Pygame rendering loops or FastAPI endpoint handlers.
2. **Type Safety & Annotations**: Use strict Python typing for all function signatures and data models (`pydantic.BaseModel` / dataclasses).
3. **Database Transactions & Async**: Utilize async I/O (`asyncpg` / `SQLAlchemy` async sessions) in FastAPI routes to prevent thread blocking.
4. **Testing Strategy**:
   - Unit tests for board state changes, win condition evaluation, and Q-learning state updates.
   - API integration tests using `httpx.AsyncClient` + `pytest`.
   - Database model & migration verification.
5. **Documentation & Traceability**:
   - Maintain clear docstrings and preserve doc comments.
   - Every schema change must be accompanied by an Alembic migration script.
