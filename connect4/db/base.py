"""Abstract Base Class defining the Repository interface for player and match persistence."""

from abc import ABC, abstractmethod
from connect4.db.domain import PlayerDomain, MatchDomain, MatchResult


class BasePlayerRepository(ABC):
    """Abstract interface for player and match persistence repositories."""

    @abstractmethod
    def get_by_username(self, username: str) -> PlayerDomain | None:
        """Retrieve a player profile by unique username."""
        pass

    @abstractmethod
    def create_player(self, username: str) -> PlayerDomain:
        """Create and persist a new Player."""
        pass

    @abstractmethod
    def get_or_create(self, username: str) -> PlayerDomain:
        """Retrieve an existing player profile or create a new one if not found."""
        pass

    @abstractmethod
    def record_match_result(self, username: str, result: str) -> MatchDomain:
        """Record an individual completed match and update cumulative player statistics."""
        pass

    @abstractmethod
    def sync_session_stats(
        self, username: str, wins: int, losses: int, draws: int
    ) -> PlayerDomain | None:
        """Aggregate active game session wins/losses/draws into player history."""
        pass

    @abstractmethod
    def get_top_players(self, limit: int = 10) -> list[PlayerDomain]:
        """Return top N players ordered primarily by victories descending (played >= 1 match)."""
        pass

    @abstractmethod
    def get_player_rank(self, username: str) -> int | None:
        """Compute global 1-based leaderboard rank for a player based on victories."""
        pass

    @abstractmethod
    def can_view_leaderboard(self, username: str) -> bool:
        """Check if player is allowed to view the leaderboard (must have played >= 1 match)."""
        pass
