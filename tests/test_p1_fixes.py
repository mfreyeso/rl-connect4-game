"""Tests for P1 bug fixes from code review."""

import numpy as np
import pytest

from connect4.constants import ACTION_DROP, N_COLS, N_ROWS
from connect4.environment import Connect4Environment
from connect4.qlearning import QLearning


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_env_with_board(board: list[list[int]]) -> Connect4Environment:
    """Create an environment with a pre-set board (row 0 = bottom)."""
    env = Connect4Environment()
    env._board = np.array(board, dtype=float)
    return env


# ---------------------------------------------------------------------------
# P1-1: Q-table learns for both players (Bug 3 fix)
# ---------------------------------------------------------------------------


class TestUpdateValuesForBothPlayers:
    def test_update_values_learns_for_player_1(self):
        """Q-table should be updated when piece=1."""
        env = Connect4Environment()
        ql = QLearning(env, epsilon=1.0, gamma=0.9, alpha=0.5)

        state = (0, 0)
        action = ACTION_DROP
        next_state = (0, 1)

        ql.update_values(state, action, next_state, reward=5, piece=1)
        assert (state, action) in ql.qtable
        assert ql.qtable[(state, action)] > 0

    def test_update_values_learns_for_player_2(self):
        """Q-table should now also be updated when piece=2 (was skipped before fix)."""
        env = Connect4Environment()
        ql = QLearning(env, epsilon=1.0, gamma=0.9, alpha=0.5)

        state = (0, 0)
        action = ACTION_DROP
        next_state = (0, 1)

        ql.update_values(state, action, next_state, reward=5, piece=2)
        assert (state, action) in ql.qtable
        assert ql.qtable[(state, action)] > 0

    def test_q_value_formula_same_for_both_players(self):
        """The computed Q-value should be identical regardless of player identity."""
        env = Connect4Environment()

        ql1 = QLearning(env, epsilon=1.0, gamma=0.9, alpha=0.5)
        ql2 = QLearning(env, epsilon=1.0, gamma=0.9, alpha=0.5)

        state = (0, 0)
        action = ACTION_DROP
        next_state = (0, 1)
        reward = 5

        ql1.update_values(state, action, next_state, reward, piece=1)
        ql2.update_values(state, action, next_state, reward, piece=2)

        assert ql1.qtable[(state, action)] == pytest.approx(ql2.qtable[(state, action)])


# ---------------------------------------------------------------------------
# P1-2: Gravity-aware placement (Design Issue 1 fix)
# ---------------------------------------------------------------------------


class TestGravityAwarePlacement:
    def test_empty_board_only_row_zero(self):
        """On a fully empty board, only row-0 positions are gravity-valid."""
        env = Connect4Environment()  # all zeros
        all_positions = [(r, c) for r in range(N_ROWS) for c in range(N_COLS)]
        valid = env._gravity_valid_positions(all_positions)
        assert all(r == 0 for r, c in valid)
        assert len(valid) == N_COLS

    def test_supported_cells_included(self):
        """A cell above a filled cell IS gravity-valid."""
        env = make_env_with_board(
            [
                [1, 0, 0, 0, 0, 0, 0],  # row 0
                [0, 0, 0, 0, 0, 0, 0],  # row 1
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        # (1, 0) should be valid because (0, 0) is filled
        valid = env._gravity_valid_positions([(1, 0), (2, 0)])
        assert (1, 0) in valid
        assert (2, 0) not in valid  # (1, 0) is empty → (2, 0) hovers

    def test_mid_air_cells_excluded(self):
        """A cell with nothing below it is NOT gravity-valid (unless row 0)."""
        env = make_env_with_board(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        positions = [(3, 2), (5, 4)]  # both hovering in mid-air
        valid = env._gravity_valid_positions(positions)
        assert valid == []

    def test_full_column_not_in_positions(self):
        """A fully filled column has no empty cells, so no positions to offer."""
        env = make_env_with_board(
            [
                [1, 0, 0, 0, 0, 0, 0],
                [2, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0],
                [2, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0],
                [2, 0, 0, 0, 0, 0, 0],
            ]
        )
        # Column 0 is full — no empty cells there
        col0_positions = [(r, 0) for r in range(N_ROWS)]
        empty_col0 = [(r, c) for r, c in col0_positions if env._board[r][c] == 0]
        assert empty_col0 == []

    def test_do_action_respects_gravity(self):
        """When do_action drops a piece, it must land on a supported cell."""
        env = make_env_with_board(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        piece = 1
        for _ in range(10):
            env.reset()
            (r, c), _ = env.do_action(ACTION_DROP, piece)
            # It must be row 0 (bottom) since the board is empty
            assert r == 0, f"Piece placed at row {r} on empty board — violates gravity"
