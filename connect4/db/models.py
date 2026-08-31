"""SQLModel entities and Pydantic schemas for Connect 4 persistence."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Player(SQLModel, table=True):
    """Player entity storing historical game statistics."""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    victories: int = Field(default=0, nullable=False)
    losses: int = Field(default=0, nullable=False)
    draws: int = Field(default=0, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
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


class Match(SQLModel, table=True):
    """Match log entity for individual game completions."""

    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id", index=True, nullable=False)
    result: str = Field(nullable=False)  # "human_win", "machine_win", "draw"
    played_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


# --- API Data Transfer Schemas (pure Pydantic, not DB tables) ---


class PlayerRead(BaseModel):
    id: int
    username: str
    victories: int
    losses: int
    draws: int
    total_games: int
    win_rate: float
    rank: Optional[int] = None
    can_view_leaderboard: bool = False


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    victories: int
    losses: int
    draws: int
    total_games: int
    win_rate: float


class LeaderboardResponse(BaseModel):
    top_players: list[LeaderboardEntry]
    user_rank: Optional[LeaderboardEntry] = None
    can_view_leaderboard: bool = True
