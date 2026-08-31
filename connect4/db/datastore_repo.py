"""GCP Datastore repository implementation utilizing google-cloud-datastore SDK."""

from datetime import datetime, timezone
import os
from typing import Any

from connect4.db.base import BasePlayerRepository
from connect4.db.domain import PlayerDomain, MatchDomain, MatchResult


class DatastorePlayerRepository(BasePlayerRepository):
    """Google Cloud Datastore implementation of BasePlayerRepository."""

    def __init__(self, client: Any | None = None) -> None:
        if client is not None:
            self.client = client
        else:
            try:
                from google.cloud import datastore
            except ImportError as err:
                raise RuntimeError(
                    "google-cloud-datastore package is required for DatastorePlayerRepository."
                ) from err
            project = os.environ.get(
                "GCP_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT")
            )
            database = os.environ.get(
                "DATASTORE_DATABASE", os.environ.get("GCP_DATASTORE_DATABASE")
            )
            kwargs = {}
            if project:
                kwargs["project"] = project
            if database:
                kwargs["database"] = database
            self.client = datastore.Client(**kwargs)

    def _normalize_username(self, username: str) -> str:
        return username.strip()

    def _player_key(self, username: str) -> Any:
        clean_user = self._normalize_username(username)
        return self.client.key("Player", clean_user)

    def _entity_to_domain(self, entity: Any) -> PlayerDomain:
        created_at = entity.get("created_at")
        updated_at = entity.get("updated_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return PlayerDomain(
            username=entity["username"],
            victories=int(entity.get("victories", 0)),
            losses=int(entity.get("losses", 0)),
            draws=int(entity.get("draws", 0)),
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
        )

    def get_by_username(self, username: str) -> PlayerDomain | None:
        key = self._player_key(username)
        entity = self.client.get(key)
        if not entity:
            return None
        return self._entity_to_domain(entity)

    def create_player(self, username: str) -> PlayerDomain:
        clean_user = self._normalize_username(username)
        key = self._player_key(clean_user)

        with self.client.transaction():
            entity = self.client.get(key)
            if not entity:
                now = datetime.now(timezone.utc)
                entity = self._create_entity(key=key)
                entity.update(
                    {
                        "username": clean_user,
                        "victories": 0,
                        "losses": 0,
                        "draws": 0,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
                self.client.put(entity)

        return self._entity_to_domain(entity)

    def _create_entity(self, key: Any) -> Any:
        try:
            from google.cloud import datastore

            return datastore.Entity(key=key)
        except ImportError:
            # Fallback if self.client is a mock or custom object
            if hasattr(self.client, "entity"):
                return self.client.entity(key=key)

            # Dummy entity class for test mocks
            class Entity(dict):
                def __init__(self, key):
                    super().__init__()
                    self.key = key

            return Entity(key=key)

    def get_or_create(self, username: str) -> PlayerDomain:
        player = self.get_by_username(username)
        if not player:
            player = self.create_player(username)
        return player

    def record_match_result(self, username: str, result: str) -> MatchDomain:
        validated_result = MatchResult(result)
        clean_user = self._normalize_username(username)
        player_key = self._player_key(clean_user)
        match_key = self.client.key("Player", clean_user, "Match")
        now = datetime.now(timezone.utc)

        with self.client.transaction():
            player_entity = self.client.get(player_key)
            if not player_entity:
                player_entity = self._create_entity(key=player_key)
                player_entity.update(
                    {
                        "username": clean_user,
                        "victories": 0,
                        "losses": 0,
                        "draws": 0,
                        "created_at": now,
                        "updated_at": now,
                    }
                )

            if validated_result == MatchResult.HUMAN_WIN:
                player_entity["victories"] = int(player_entity.get("victories", 0)) + 1
            elif validated_result == MatchResult.MACHINE_WIN:
                player_entity["losses"] = int(player_entity.get("losses", 0)) + 1
            elif validated_result == MatchResult.DRAW:
                player_entity["draws"] = int(player_entity.get("draws", 0)) + 1
            player_entity["updated_at"] = now
            self.client.put(player_entity)

            match_entity = self._create_entity(key=match_key)
            match_entity.update(
                {
                    "result": validated_result.value,
                    "played_at": now,
                }
            )
            self.client.put(match_entity)

        match_id = getattr(getattr(match_entity, "key", None), "id_or_name", "match_1")
        return MatchDomain(
            id=str(match_id),
            player_username=clean_user,
            result=validated_result,
            played_at=now,
        )

    def sync_session_stats(
        self, username: str, wins: int, losses: int, draws: int
    ) -> PlayerDomain | None:
        if wins < 0 or losses < 0 or draws < 0:
            raise ValueError("wins, losses, and draws must be non-negative integers.")
        clean_user = self._normalize_username(username)
        player_key = self._player_key(clean_user)
        now = datetime.now(timezone.utc)

        with self.client.transaction():
            entity = self.client.get(player_key)
            if not entity:
                entity = self._create_entity(key=player_key)
                entity.update(
                    {
                        "username": clean_user,
                        "victories": 0,
                        "losses": 0,
                        "draws": 0,
                        "created_at": now,
                        "updated_at": now,
                    }
                )

            if wins > 0 or losses > 0 or draws > 0:
                entity["victories"] = int(entity.get("victories", 0)) + wins
                entity["losses"] = int(entity.get("losses", 0)) + losses
                entity["draws"] = int(entity.get("draws", 0)) + draws
                entity["updated_at"] = now
                self.client.put(entity)

        return self._entity_to_domain(entity)

    def get_top_players(self, limit: int = 10) -> list[PlayerDomain]:
        query = self.client.query(kind="Player")
        query.order = ["-victories"]
        results = list(query.fetch(limit=50))

        all_players = [self._entity_to_domain(e) for e in results]
        active_players = [p for p in all_players if p.total_games >= 1]
        active_players.sort(key=lambda p: (-p.victories, p.updated_at))
        return active_players[:limit]

    def get_player_rank(self, username: str) -> int | None:
        clean_user = self._normalize_username(username)
        target_player = self.get_by_username(clean_user)
        if not target_player or target_player.total_games == 0:
            return None

        # Reuse the same leaderboard logic with a generous limit for rank lookup
        ranked_players = self.get_top_players(limit=500)

        for idx, p in enumerate(ranked_players, start=1):
            if p.username == clean_user:
                return idx

        return None

    def can_view_leaderboard(self, username: str) -> bool:
        player = self.get_by_username(username)
        if not player:
            return False
        return player.total_games >= 1
