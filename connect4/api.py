"""FastAPI web server for Connect 4."""

import os
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from connect4.environment import Connect4Environment
from connect4.train import load_q_table

# ---------------------------------------------------------------------------
# Load Q-table once at startup
# ---------------------------------------------------------------------------
_Q_TABLE_PATH = os.environ.get("Q_TABLE_PATH", "q_table.pkl")
try:
    _Q_TABLE: dict = load_q_table(_Q_TABLE_PATH)
except FileNotFoundError:
    _Q_TABLE = {}
    print(f"⚠️  Q-table not found at {_Q_TABLE_PATH} — agent will play randomly.")

# ---------------------------------------------------------------------------
# Session store (bounded OrderedDict for FIFO eviction)
# ---------------------------------------------------------------------------
MACHINE_PIECE = 1
HUMAN_PIECE = 2
MAX_SESSIONS = 200  # keep memory safe on 512 MB free tier


@dataclass
class GameSession:
    env: Connect4Environment = field(default_factory=Connect4Environment)
    nickname: str = "Player"
    human_score: int = 0
    machine_score: int = 0


_sessions: OrderedDict[str, GameSession] = OrderedDict()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class NewGameRequest(BaseModel):
    nickname: str = "Player"
    session_id: str | None = None  # reuse session to keep scores


class MoveRequest(BaseModel):
    column: int


class BoardState(BaseModel):
    board: list[list[int]]
    finished: bool
    result: str | None = None  # "human_win", "machine_win", "draw", or None
    human_score: int
    machine_score: int
    nickname: str
    human_goes_first: bool
    machine_move: int | None = None  # column the machine just played, if any
    winning_cells: list[list[int]] | None = None  # [[row, col], ...] for the 4-in-a-row


class NewGameResponse(BaseModel):
    session_id: str
    state: BoardState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _board_to_list(env: Connect4Environment) -> list[list[int]]:
    """Convert numpy board to JSON-friendly nested list (row 0 = bottom)."""
    return env.board.astype(int).tolist()


def _build_board_state(
    session: GameSession,
    result: str | None = None,
    machine_move: int | None = None,
    winning_cells: list[list[int]] | None = None,
) -> BoardState:
    return BoardState(
        board=_board_to_list(session.env),
        finished=session.env.finished,
        result=result,
        human_score=session.human_score,
        machine_score=session.machine_score,
        nickname=session.nickname,
        human_goes_first=session.env.initial_turn != 0,
        machine_move=machine_move,
        winning_cells=winning_cells,
    )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
_is_production = os.environ.get("ENV") == "production"

app = FastAPI(
    title="Connect 4",
    docs_url=None if _is_production else "/docs",
    redoc_url=None,
)

# --- Rate limiter ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please slow down."},
    )


# --- CORS ---
_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
# Add the Render production URL
_RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
if _RENDER_URL:
    _ALLOWED_ORIGINS.append(_RENDER_URL)

app.add_middleware(
    CORSMiddleware,  # ty: ignore[invalid-argument-type]
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------


@app.post("/api/game/new", response_model=NewGameResponse)
@limiter.limit("10/minute")
def new_game(request: Request, req: NewGameRequest):
    """Start a new game.  Optionally reuse a session to keep scores."""
    if req.session_id and req.session_id in _sessions:
        session = _sessions[req.session_id]
        session.env = Connect4Environment()
        session.nickname = req.nickname or session.nickname
        sid = req.session_id
        # Move to end so it's the most-recently-used
        _sessions.move_to_end(sid)
    else:
        sid = uuid.uuid4().hex
        session = GameSession(nickname=req.nickname)
        _sessions[sid] = session

        # Evict oldest session if we've exceeded the cap
        while len(_sessions) > MAX_SESSIONS:
            _sessions.popitem(last=False)

    machine_move: int | None = None

    # If machine goes first (turn == 0), play its opening move immediately.
    if session.env.turn == 0:
        col = session.env.choose_column(MACHINE_PIECE, _Q_TABLE)
        row = session.env.get_next_open_row(col)
        session.env.drop_piece(row, col, MACHINE_PIECE)
        session.env.turn = 1  # now human's turn
        machine_move = col

    return NewGameResponse(
        session_id=sid,
        state=_build_board_state(session, machine_move=machine_move),
    )


@app.post("/api/game/{session_id}/move", response_model=BoardState)
@limiter.limit("30/minute")
def make_move(request: Request, session_id: str, req: MoveRequest):
    """Human places a piece, then the machine responds."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    env = session.env
    if env.finished:
        raise HTTPException(status_code=400, detail="Game already finished.")

    col = req.column
    if col < 0 or col >= 7 or not env.is_valid_location(col):
        raise HTTPException(status_code=400, detail="Invalid column.")

    # --- Human move ---
    row = env.get_next_open_row(col)
    env.drop_piece(row, col, HUMAN_PIECE)

    if env.is_winning_move(HUMAN_PIECE):
        env.finished = True
        session.human_score += 1
        cells = env.winner_position(HUMAN_PIECE)
        wc = [list(c) for c in cells] if cells else None
        return _build_board_state(session, result="human_win", winning_cells=wc)

    if not env.get_valid_columns():
        env.finished = True
        return _build_board_state(session, result="draw")

    # --- Machine move ---
    best_col = env.choose_column(MACHINE_PIECE, _Q_TABLE)
    m_row = env.get_next_open_row(best_col)
    env.drop_piece(m_row, best_col, MACHINE_PIECE)

    if env.is_winning_move(MACHINE_PIECE):
        env.finished = True
        session.machine_score += 1
        cells = env.winner_position(MACHINE_PIECE)
        wc = [list(c) for c in cells] if cells else None
        return _build_board_state(
            session,
            result="machine_win",
            machine_move=best_col,
            winning_cells=wc,
        )

    if not env.get_valid_columns():
        env.finished = True
        return _build_board_state(session, result="draw", machine_move=best_col)

    return _build_board_state(session, machine_move=best_col)


@app.get("/api/game/{session_id}", response_model=BoardState)
@limiter.limit("30/minute")
def get_state(request: Request, session_id: str):
    """Return the current board state for a session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return _build_board_state(session)


# ---------------------------------------------------------------------------
# Static files & SPA fallback
# ---------------------------------------------------------------------------
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(_STATIC_DIR / "index.html"))
