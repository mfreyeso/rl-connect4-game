import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine

from connect4.api import app
from connect4.db import set_repository
from connect4.db.base import BasePlayerRepository
from connect4.db.inmemory_repo import InMemoryPlayerRepository
from connect4.db.sqlmodel_repo import SQLModelPlayerRepository


@pytest.fixture(params=["in_memory", "sqlmodel"])
def repository(request) -> Generator[BasePlayerRepository, None, None]:
    """Parametrized fixture yielding both InMemory and SQLModel repository backends."""
    if request.param == "in_memory":
        repo = InMemoryPlayerRepository()
        set_repository(repo)
        yield repo
        set_repository(None)
    else:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        SQLModel.metadata.create_all(engine)
        repo = SQLModelPlayerRepository(engine=engine)
        set_repository(repo)
        yield repo
        set_repository(None)


def test_player_creation_and_stats(repository: BasePlayerRepository):
    player = repository.get_or_create("Alice")
    assert player.username == "Alice"
    assert player.victories == 0
    assert player.losses == 0
    assert player.draws == 0
    assert player.total_games == 0
    assert repository.can_view_leaderboard("Alice") is False


def test_record_match_result_and_visibility(repository: BasePlayerRepository):
    player = repository.get_or_create("Bob")
    assert repository.can_view_leaderboard("Bob") is False

    match = repository.record_match_result("Bob", "human_win")
    assert match.id is not None
    assert match.result == "human_win"

    updated_player = repository.get_by_username("Bob")
    assert updated_player is not None
    assert updated_player.victories == 1
    assert updated_player.total_games == 1
    assert repository.can_view_leaderboard("Bob") is True


def test_leaderboard_ranking_and_rank_calc(repository: BasePlayerRepository):
    repository.get_or_create("Player1")
    repository.get_or_create("Player2")
    repository.get_or_create("Player3")

    repository.record_match_result("Player1", "human_win")
    repository.record_match_result("Player1", "human_win")  # 2 wins

    repository.record_match_result("Player2", "human_win")  # 1 win

    top = repository.get_top_players(limit=10)
    assert len(top) == 2  # Player3 has 0 games played and is excluded
    assert top[0].username == "Player1"
    assert top[1].username == "Player2"

    assert repository.get_player_rank("Player1") == 1
    assert repository.get_player_rank("Player2") == 2
    assert repository.get_player_rank("Player3") is None  # 0 games played


def test_sync_session_stats(repository: BasePlayerRepository):
    repository.get_or_create("Charlie")
    repository.sync_session_stats("Charlie", wins=3, losses=1, draws=2)

    updated = repository.get_by_username("Charlie")
    assert updated is not None
    assert updated.victories == 3
    assert updated.losses == 1
    assert updated.draws == 2
    assert updated.total_games == 6
    assert repository.can_view_leaderboard("Charlie") is True


def test_api_endpoints():
    import uuid

    # Use in-memory repo for API integration test
    repo = InMemoryPlayerRepository()
    set_repository(repo)

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

    # 3. Create a game session and play move
    game_res = client.post("/api/game/new", json={"nickname": user_name})
    assert game_res.status_code == 200

    # Sync session
    sync_res = client.post(
        f"/api/players/{user_name}/sync_session",
        json={"wins": 1, "losses": 0, "draws": 0},
    )
    assert sync_res.status_code == 200
    assert sync_res.json()["can_view_leaderboard"] is True

    # 4. Leaderboard is unlocked now
    lb_unlocked = client.get(f"/api/leaderboard?username={user_name}")
    assert lb_unlocked.status_code == 200
    lb_data = lb_unlocked.json()
    assert len(lb_data["top_players"]) >= 1
    assert lb_data["user_rank"]["username"] == user_name

    set_repository(None)


def test_get_player_profile_does_not_create_db_record():
    import uuid

    repo = InMemoryPlayerRepository()
    set_repository(repo)

    client = TestClient(app)
    unplayed_user = f"Unplayed_{uuid.uuid4().hex[:8]}"

    res = client.get(f"/api/players/{unplayed_user}")
    assert res.status_code == 200
    assert res.json()["username"] == unplayed_user
    assert res.json()["can_view_leaderboard"] is False

    assert repo.get_by_username(unplayed_user) is None
    set_repository(None)
