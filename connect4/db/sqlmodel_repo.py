"""Relational SQLModel database repository implementation (PostgreSQL / SQLite)."""

from datetime import datetime, timezone
from sqlalchemy.engine import Engine
from sqlmodel import Session, select, col

from connect4.db.base import BasePlayerRepository
from connect4.db.domain import PlayerDomain, MatchDomain, MatchResult
from connect4.db.models import Player, Match
from connect4.db.engine import engine as default_engine


class SQLModelPlayerRepository(BasePlayerRepository):
    """SQLModel backed repository for PostgreSQL / SQLite databases."""

    def __init__(self, engine: Engine | None = None) -> None:
        self.engine = engine or default_engine

    def _to_player_domain(self, player: Player) -> PlayerDomain:
        return PlayerDomain(
            username=player.username,
            victories=player.victories,
            losses=player.losses,
            draws=player.draws,
            created_at=player.created_at,
            updated_at=player.updated_at,
        )

    def _to_match_domain(self, match: Match, username: str) -> MatchDomain:
        return MatchDomain(
            id=match.id,
            player_username=username,
            result=MatchResult(match.result),
            played_at=match.played_at,
        )

    def get_by_username(self, username: str) -> PlayerDomain | None:
        clean_user = username.strip()
        with Session(self.engine) as session:
            statement = select(Player).where(Player.username == clean_user)
            player = session.exec(statement).first()
            if not player:
                return None
            return self._to_player_domain(player)

    def create_player(self, username: str) -> PlayerDomain:
        clean_user = username.strip()
        with Session(self.engine) as session:
            existing = session.exec(
                select(Player).where(Player.username == clean_user)
            ).first()
            if existing:
                return self._to_player_domain(existing)
            player = Player(username=clean_user)
            session.add(player)
            session.commit()
            session.refresh(player)
            return self._to_player_domain(player)

    def get_or_create(self, username: str) -> PlayerDomain:
        clean_user = username.strip()
        with Session(self.engine) as session:
            player = session.exec(
                select(Player).where(Player.username == clean_user)
            ).first()
            if not player:
                player = Player(username=clean_user)
                session.add(player)
                session.commit()
                session.refresh(player)
            return self._to_player_domain(player)

    def record_match_result(self, username: str, result: str) -> MatchDomain:
        validated_result = MatchResult(result)
        clean_user = username.strip()
        with Session(self.engine) as session:
            statement = select(Player).where(Player.username == clean_user)
            player = session.exec(statement).first()
            if not player:
                player = Player(username=clean_user)
                session.add(player)
                session.commit()
                session.refresh(player)

            assert player.id is not None
            match_entry = Match(player_id=player.id, result=validated_result.value)
            session.add(match_entry)

            if validated_result == MatchResult.HUMAN_WIN:
                player.victories += 1
            elif validated_result == MatchResult.MACHINE_WIN:
                player.losses += 1
            elif validated_result == MatchResult.DRAW:
                player.draws += 1
            player.updated_at = datetime.now(timezone.utc)
            session.add(player)

            session.commit()
            session.refresh(match_entry)
            return self._to_match_domain(match_entry, clean_user)

    def sync_session_stats(
        self, username: str, wins: int, losses: int, draws: int
    ) -> PlayerDomain | None:
        if wins < 0 or losses < 0 or draws < 0:
            raise ValueError("wins, losses, and draws must be non-negative integers.")
        clean_user = username.strip()
        with Session(self.engine) as session:
            statement = select(Player).where(Player.username == clean_user)
            player = session.exec(statement).first()
            if not player:
                player = Player(username=clean_user)
                session.add(player)
                session.commit()
                session.refresh(player)

            if wins > 0 or losses > 0 or draws > 0:
                player.victories += wins
                player.losses += losses
                player.draws += draws
                player.updated_at = datetime.now(timezone.utc)
                session.add(player)
                session.commit()
                session.refresh(player)

            return self._to_player_domain(player)

    def get_top_players(self, limit: int = 10) -> list[PlayerDomain]:
        with Session(self.engine) as session:
            statement = (
                select(Player)
                .where(
                    (col(Player.victories) + col(Player.losses) + col(Player.draws)) > 0
                )
                .order_by(col(Player.victories).desc(), col(Player.updated_at).asc())
                .limit(limit)
            )
            players = session.exec(statement).all()
            return [self._to_player_domain(p) for p in players]

    def get_player_rank(self, username: str) -> int | None:
        clean_user = username.strip()
        with Session(self.engine) as session:
            statement = select(Player).where(Player.username == clean_user)
            player = session.exec(statement).first()
            if not player or player.total_games == 0:
                return None

            # Count players ranked strictly above this player:
            # more victories, OR same victories but earlier updated_at
            from sqlalchemy import func, or_, and_

            rank_query = (
                select(func.count())
                .select_from(Player)
                .where(
                    (col(Player.victories) + col(Player.losses) + col(Player.draws))
                    > 0,
                    or_(
                        col(Player.victories) > player.victories,
                        and_(
                            col(Player.victories) == player.victories,
                            col(Player.updated_at) < player.updated_at,
                        ),
                    ),
                )
            )
            players_above = session.exec(rank_query).one()
            return players_above + 1

    def can_view_leaderboard(self, username: str) -> bool:
        player = self.get_by_username(username)
        if not player:
            return False
        return player.total_games >= 1
