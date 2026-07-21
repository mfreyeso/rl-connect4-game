import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session

from connect4.api import app
from connect4.db.models import Player, Match
from connect4.db.repository import (
    get_or_create_player,
    get_player_by_username,
    record_match_result,
    sync_session_stats,
    get_top_players,
    get_player_rank,
    can_view_leaderboard,
)


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing repository functions."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_player_creation_and_stats(db_session: Session):
    player = get_or_create_player(db_session, "Alice")
    assert player.id is not None
    assert player.username == "Alice"
    assert player.victories == 0
    assert player.losses == 0
    assert player.draws == 0
    assert player.total_games == 0
    assert can_view_leaderboard(db_session, "Alice") is False


def test_record_match_result_and_visibility(db_session: Session):
    player = get_or_create_player(db_session, "Bob")
    assert player.id is not None
    assert can_view_leaderboard(db_session, "Bob") is False

    match = record_match_result(db_session, player.id, "human_win")
    assert match.id is not None
    assert match.result == "human_win"

    updated_player = get_player_by_username(db_session, "Bob")
    assert updated_player is not None
    assert updated_player.victories == 1
    assert updated_player.total_games == 1
    assert can_view_leaderboard(db_session, "Bob") is True


def test_leaderboard_ranking_and_rank_calc(db_session: Session):
    p1 = get_or_create_player(db_session, "Player1")
    p2 = get_or_create_player(db_session, "Player2")
    p3 = get_or_create_player(db_session, "Player3")
    assert p1.id is not None
    assert p2.id is not None
    assert p3.id is not None

    record_match_result(db_session, p1.id, "human_win")
    record_match_result(db_session, p1.id, "human_win")  # 2 wins

    record_match_result(db_session, p2.id, "human_win")  # 1 win

    top = get_top_players(db_session, limit=10)
    assert len(top) == 3
    assert top[0].username == "Player1"
    assert top[1].username == "Player2"

    assert get_player_rank(db_session, "Player1") == 1
    assert get_player_rank(db_session, "Player2") == 2
    assert get_player_rank(db_session, "Player3") is None  # 0 games played


def test_sync_session_stats(db_session: Session):
    player = get_or_create_player(db_session, "Charlie")
    assert player.id is not None
    sync_session_stats(db_session, player.id, wins=3, losses=1, draws=2)

    updated = get_player_by_username(db_session, "Charlie")
    assert updated is not None
    assert updated.victories == 3
    assert updated.losses == 1
    assert updated.draws == 2
    assert updated.total_games == 6
    assert can_view_leaderboard(db_session, "Charlie") is True


def test_api_endpoints():
    import uuid

    client = TestClient(app)
    user_name = f"TestUser_{uuid.uuid4().hex[:8]}"

    # 1. Get profile for new user
    res = client.get(f"/api/players/{user_name}")
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == user_name
    assert data["victories"] == 0
    assert data["can_view_leaderboard"] is False

    # 2. Leaderboard endpoint for new user -> HTTP 403 Forbidden
    lb_res = client.get(f"/api/leaderboard?username={user_name}")
    assert lb_res.status_code == 403
    assert "Leaderboard is locked" in lb_res.json()["detail"]

    # 3. Create a game session and play winning move
    game_res = client.post("/api/game/new", json={"nickname": user_name})
    assert game_res.status_code == 200
    sid = game_res.json()["session_id"]

    # Sync session or win game
    sync_res = client.post(
        f"/api/players/{user_name}/sync_session",
        json={"wins": 1, "losses": 0, "draws": 0},
    )
    assert sync_res.status_code == 200
    assert sync_res.json()["can_view_leaderboard"] is True

    # 4. Now leaderboard is accessible
    lb_unlocked = client.get(f"/api/leaderboard?username={user_name}")
    assert lb_unlocked.status_code == 200
    lb_data = lb_unlocked.json()
    assert len(lb_data["top_players"]) >= 1
    assert lb_data["user_rank"]["username"] == user_name
