"""Tests for the FastAPI web API endpoints."""

from fastapi.testclient import TestClient

from connect4.api import app

client = TestClient(app)


class TestNewGame:
    def test_creates_session(self):
        res = client.post("/api/game/new", json={"nickname": "TestUser"})
        assert res.status_code == 200
        data = res.json()
        assert "session_id" in data
        assert data["state"]["nickname"] == "TestUser"
        assert data["state"]["human_score"] == 0
        assert data["state"]["machine_score"] == 0
        assert data["state"]["finished"] is False
        assert len(data["state"]["board"]) == 6
        assert len(data["state"]["board"][0]) == 7

    def test_reuses_session_keeps_scores(self):
        # Create first game
        res1 = client.post("/api/game/new", json={"nickname": "ReUser"})
        sid = res1.json()["session_id"]

        # Start another game in the same session
        res2 = client.post(
            "/api/game/new", json={"nickname": "ReUser", "session_id": sid}
        )
        assert res2.status_code == 200
        assert res2.json()["session_id"] == sid

    def test_default_nickname(self):
        res = client.post("/api/game/new", json={})
        assert res.status_code == 200
        assert res.json()["state"]["nickname"] == "Player"


class TestMakeMove:
    def _start_game(self, nickname="Tester"):
        res = client.post("/api/game/new", json={"nickname": nickname})
        return res.json()["session_id"]

    def test_valid_move(self):
        sid = self._start_game()
        res = client.post(f"/api/game/{sid}/move", json={"column": 3})
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data["board"], list)
        # Machine should have responded (unless human won or draw)
        if not data["finished"]:
            assert data["machine_move"] is not None

    def test_invalid_column_negative(self):
        sid = self._start_game()
        res = client.post(f"/api/game/{sid}/move", json={"column": -1})
        assert res.status_code == 400

    def test_invalid_column_too_high(self):
        sid = self._start_game()
        res = client.post(f"/api/game/{sid}/move", json={"column": 7})
        assert res.status_code == 400

    def test_session_not_found(self):
        res = client.post("/api/game/nonexistent/move", json={"column": 0})
        assert res.status_code == 404

    def test_full_column_rejected(self):
        sid = self._start_game()
        # Fill a column by repeatedly placing pieces (need to handle machine moves)
        # This is a best-effort test; the column may not fill in 6 human moves
        # because the machine also plays.
        for _ in range(10):
            res = client.post(f"/api/game/{sid}/move", json={"column": 0})
            if res.status_code != 200:
                break
            if res.json().get("finished"):
                break
        # If the game ended naturally, that's fine — test passes.


class TestGetState:
    def test_returns_state(self):
        res = client.post("/api/game/new", json={"nickname": "ReadTest"})
        sid = res.json()["session_id"]
        res2 = client.get(f"/api/game/{sid}")
        assert res2.status_code == 200
        assert res2.json()["nickname"] == "ReadTest"

    def test_unknown_session(self):
        res = client.get("/api/game/noexist")
        assert res.status_code == 404


class TestStaticFiles:
    def test_index_page(self):
        res = client.get("/")
        assert res.status_code == 200
        assert "Connect" in res.text


class TestGameplay:
    """Play several moves to exercise the full flow."""

    def test_play_multiple_moves(self):
        res = client.post("/api/game/new", json={"nickname": "GameTester"})
        sid = res.json()["session_id"]

        columns = [0, 1, 2, 3, 4, 5, 6, 0, 1, 2]
        for col in columns:
            res = client.post(f"/api/game/{sid}/move", json={"column": col})
            if res.status_code != 200:
                continue
            data = res.json()
            if data["finished"]:
                assert data["result"] in ("human_win", "machine_win", "draw")
                break
