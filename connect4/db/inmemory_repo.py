"""Thread-safe In-Memory repository implementation for testing and development.

NOTE: This implementation intentionally mutates PlayerDomain instances stored in
``_players`` in-place for simplicity. Read operations return ``model_copy()`` to
ensure callers never hold a reference to internal state.
"""

from datetime import datetime, timezone
import threading
import uuid
from connect4.db.base import BasePlayerRepository
from connect4.db.domain import PlayerDomain, MatchDomain, MatchResult


class InMemoryPlayerRepository(BasePlayerRepository):
    """In-memory dictionary store implementing BasePlayerRepository."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._players: dict[str, PlayerDomain] = {}

    def _normalize_key(self, username: str) -> str:
        return username.strip()

    def get_by_username(self, username: str) -> PlayerDomain | None:
        key = self._normalize_key(username)
        with self._lock:
            player = self._players.get(key)
            if player:
                return player.model_copy()
            return None

    def create_player(self, username: str) -> PlayerDomain:
        key = self._normalize_key(username)
        with self._lock:
            if key in self._players:
                return self._players[key].model_copy()
            now = datetime.now(timezone.utc)
            player = PlayerDomain(
                username=key,
                victories=0,
                losses=0,
                draws=0,
                created_at=now,
                updated_at=now,
            )
            self._players[key] = player
            return player.model_copy()

    def get_or_create(self, username: str) -> PlayerDomain:
        key = self._normalize_key(username)
        with self._lock:
            if key not in self._players:
                now = datetime.now(timezone.utc)
                self._players[key] = PlayerDomain(
                    username=key,
                    victories=0,
                    losses=0,
                    draws=0,
                    created_at=now,
                    updated_at=now,
                )
            return self._players[key].model_copy()

    def record_match_result(self, username: str, result: str) -> MatchDomain:
        validated_result = MatchResult(result)
        key = self._normalize_key(username)
        with self._lock:
            if key not in self._players:
                now = datetime.now(timezone.utc)
                self._players[key] = PlayerDomain(
                    username=key,
                    created_at=now,
                    updated_at=now,
                )
            player = self._players[key]
            if validated_result == MatchResult.HUMAN_WIN:
                player.victories += 1
            elif validated_result == MatchResult.MACHINE_WIN:
                player.losses += 1
            elif validated_result == MatchResult.DRAW:
                player.draws += 1
            player.updated_at = datetime.now(timezone.utc)

            match_entry = MatchDomain(
                id=uuid.uuid4().hex,
                player_username=key,
                result=validated_result,
                played_at=datetime.now(timezone.utc),
            )
            return match_entry.model_copy()

    def sync_session_stats(
        self, username: str, wins: int, losses: int, draws: int
    ) -> PlayerDomain | None:
        if wins < 0 or losses < 0 or draws < 0:
            raise ValueError("wins, losses, and draws must be non-negative integers.")
        key = self._normalize_key(username)
        with self._lock:
            if key not in self._players:
                now = datetime.now(timezone.utc)
                self._players[key] = PlayerDomain(
                    username=key, created_at=now, updated_at=now
                )
            player = self._players[key]
            if wins > 0 or losses > 0 or draws > 0:
                player.victories += wins
                player.losses += losses
                player.draws += draws
                player.updated_at = datetime.now(timezone.utc)
            return player.model_copy()

    def get_top_players(self, limit: int = 10) -> list[PlayerDomain]:
        with self._lock:
            active_players = [
                p.model_copy() for p in self._players.values() if p.total_games >= 1
            ]
            active_players.sort(key=lambda p: (-p.victories, p.updated_at))
            return active_players[:limit]

    def get_player_rank(self, username: str) -> int | None:
        key = self._normalize_key(username)
        with self._lock:
            player = self._players.get(key)
            if not player or player.total_games == 0:
                return None

            active_players = [p for p in self._players.values() if p.total_games >= 1]
            active_players.sort(key=lambda p: (-p.victories, p.updated_at))

            for idx, p in enumerate(active_players, start=1):
                if p.username == key:
                    return idx

            return None

    def can_view_leaderboard(self, username: str) -> bool:
        key = self._normalize_key(username)
        with self._lock:
            player = self._players.get(key)
            if not player:
                return False
            return player.total_games >= 1
