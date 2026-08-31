"""Pure Pydantic domain models for Connect 4 entities."""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, Field


class MatchResult(StrEnum):
    """Valid match outcome values."""

    HUMAN_WIN = "human_win"
    MACHINE_WIN = "machine_win"
    DRAW = "draw"


class PlayerDomain(BaseModel):
    """Pure domain entity representing a player's statistics."""

    username: str
    victories: int = 0
    losses: int = 0
    draws: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    """Pure domain entity representing a completed match."""

    id: Optional[str | int] = None
    player_username: str
    result: MatchResult
    played_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
