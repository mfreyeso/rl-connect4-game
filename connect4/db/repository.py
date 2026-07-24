"""Repository pattern functions following Single Responsibility Principle (SRP)."""

from datetime import datetime, timezone
from sqlmodel import Session, select, col
from connect4.db.models import Player, Match


def get_player_by_username(session: Session, username: str) -> Player | None:
    """Retrieve player by unique username."""
    statement = select(Player).where(Player.username == username.strip())
    return session.exec(statement).first()


def create_player(session: Session, username: str) -> Player:
    """Create and persist a new Player."""
    player = Player(username=username.strip())
    session.add(player)
    session.commit()
    session.refresh(player)
    return player


def get_or_create_player(session: Session, username: str) -> Player:
    """Find existing player or initialize a new one."""
    player = get_player_by_username(session, username)
    if not player:
        player = create_player(session, username)
    return player


def record_match_result(session: Session, player_id: int, result: str) -> Match:
    """Record an individual completed match and update cumulative player stats."""
    match_entry = Match(player_id=player_id, result=result)
    session.add(match_entry)

    player = session.get(Player, player_id)
    if player:
        if result == "human_win":
            player.victories += 1
        elif result == "machine_win":
            player.losses += 1
        elif result == "draw":
            player.draws += 1
        player.updated_at = datetime.now(timezone.utc)
        session.add(player)

    session.commit()
    session.refresh(match_entry)
    return match_entry


def sync_session_stats(
    session: Session, player_id: int, wins: int, losses: int, draws: int
) -> Player | None:
    """Aggregate game session delta stats into persistent player history."""
    player = session.get(Player, player_id)
    if not player:
        return None

    if wins > 0 or losses > 0 or draws > 0:
        player.victories += wins
        player.losses += losses
        player.draws += draws
        player.updated_at = datetime.now(timezone.utc)
        session.add(player)
        session.commit()
        session.refresh(player)

    return player


def get_top_players(session: Session, limit: int = 10) -> list[Player]:
    """Return top N players ordered primarily by victories descending (played >= 1 match)."""
    statement = (
        select(Player)
        .where((col(Player.victories) + col(Player.losses) + col(Player.draws)) > 0)
        .order_by(col(Player.victories).desc(), col(Player.updated_at).asc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_player_rank(session: Session, username: str) -> int | None:
    """Compute global 1-based leaderboard rank for a player based on victories."""
    player = get_player_by_username(session, username)
    if not player or player.total_games == 0:
        return None

    # Count players with strictly more victories or same victories with earlier update
    all_players = list(
        session.exec(
            select(Player)
            .where((col(Player.victories) + col(Player.losses) + col(Player.draws)) > 0)
            .order_by(col(Player.victories).desc(), col(Player.updated_at).asc())
        ).all()
    )

    for idx, p in enumerate(all_players, start=1):
        if p.id == player.id:
            return idx

    return None


def can_view_leaderboard(session: Session, username: str) -> bool:
    """Check if player is allowed to view leaderboard (must have >= 1 match played)."""
    player = get_player_by_username(session, username)
    if not player:
        return False
    return player.total_games >= 1
