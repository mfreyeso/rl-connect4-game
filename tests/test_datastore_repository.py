from unittest.mock import MagicMock
import pytest
from connect4.db.datastore_repo import DatastorePlayerRepository


class FakeEntity(dict):
    def __init__(self, key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key


class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_datastore_client():
    client = MagicMock()
    client.transaction.return_value = FakeTransaction()

    db_entities = {}

    def fake_key(*args):
        return ("Key",) + args

    def fake_get(key):
        return db_entities.get(key)

    def fake_put(entity):
        db_entities[entity.key] = entity

    def fake_query(kind):
        query = MagicMock()

        def fetch(limit=100):
            res = [e for e in db_entities.values() if e.key[1] == kind]
            return res[:limit]

        query.fetch.side_effect = fetch
        return query

    client.key.side_effect = fake_key
    client.get.side_effect = fake_get
    client.put.side_effect = fake_put
    client.query.side_effect = fake_query
    client.entity = lambda key: FakeEntity(key=key)

    return client


def test_datastore_create_and_get_player(mock_datastore_client):
    repo = DatastorePlayerRepository(client=mock_datastore_client)

    player = repo.create_player("Dave")
    assert player.username == "Dave"
    assert player.victories == 0

    fetched = repo.get_by_username("Dave")
    assert fetched is not None
    assert fetched.username == "Dave"


def test_datastore_record_match_result(mock_datastore_client):
    repo = DatastorePlayerRepository(client=mock_datastore_client)

    match = repo.record_match_result("Dave", "human_win")
    assert match.player_username == "Dave"
    assert match.result == "human_win"

    player = repo.get_by_username("Dave")
    assert player is not None
    assert player.victories == 1
    can_view = repo.can_view_leaderboard("Dave")
    assert can_view is True


def test_datastore_sync_session_stats(mock_datastore_client):
    repo = DatastorePlayerRepository(client=mock_datastore_client)

    player = repo.sync_session_stats("Dave", wins=2, losses=1, draws=0)
    assert player is not None
    assert player.victories == 2
    assert player.losses == 1
    assert player.total_games == 3
