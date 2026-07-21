# Agent Rules: RL Connect 4 Game

## Project Principles & Tech Standards
- **Python Version**: Python >= 3.12 managed via `uv`.
- **Frameworks**: Pygame (Desktop UI), FastAPI + Uvicorn (Web API & Deployment), PostgreSQL (Persistence).
- **Architecture**:
  - Keep game engine rules (`connect4/environment.py`), AI policies (`connect4/qlearning.py`), database interactions (`connect4/db`), and UI (`connect4/ui.py`) decoupled.
  - Web API endpoints must use async FastAPI handlers with typed Pydantic models.
- **Testing & Quality**:
  - Run `pytest` to verify game logic, API contracts, and database repositories.
  - Enforce code formatting via `black` and type safety with Python standard type annotations.
