"""Tests for P0 bug fixes from code review."""

import numpy as np
import pytest

from connect4.constants import ACTION_BLOCK, ACTION_DROP, N_COLS, N_ROWS
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
# P0-1: len() wrapping fix — ACTION_BLOCK should be reachable
# ---------------------------------------------------------------------------


class TestLenFix:
    def test_early_game_returns_drop(self):
        """With < 3 opponent pieces, only ACTION_DROP is offered."""
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
        # Place only 2 opponent (piece=2) pieces on the bottom row
        env._board[0][0] = 2
        env._board[0][1] = 2

        actions = env.get_possible_actions(piece=1)
        assert actions == [ACTION_DROP]

    def test_block_action_reachable_with_threat(self):
        """With ≥ 3 opponent pieces forming a threat, ACTION_BLOCK is returned."""
        env = make_env_with_board(
            [
                [2, 2, 2, 0, 0, 0, 0],  # row 0 (bottom): 3 opponent pieces in a row
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        actions = env.get_possible_actions(piece=1)
        assert actions == [ACTION_BLOCK]

    def test_many_opponent_pieces_no_threat(self):
        """With ≥ 3 opponent pieces but no 3-in-a-row threat → ACTION_DROP."""
        env = make_env_with_board(
            [
                [2, 0, 2, 0, 2, 0, 0],  # scattered, no 3-in-a-row
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        actions = env.get_possible_actions(piece=1)
        assert actions == [ACTION_DROP]


# ---------------------------------------------------------------------------
# P0-2: Threat detection — is_threatening_move / threatening_position
# ---------------------------------------------------------------------------


class TestThreatDetection:
    def test_horizontal_threat(self):
        """3 horizontal pieces + open gravity-valid cell → threat detected."""
        env = make_env_with_board(
            [
                [2, 2, 2, 0, 0, 0, 0],  # bottom row: threat at (0, 3)
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert env.is_threatening_move(2) is True
        pos = env.threatening_position(2)
        assert pos == (0, 3)

    def test_vertical_threat(self):
        """3 vertical pieces + open cell on top → threat detected."""
        env = make_env_with_board(
            [
                [2, 0, 0, 0, 0, 0, 0],  # row 0
                [2, 0, 0, 0, 0, 0, 0],  # row 1
                [2, 0, 0, 0, 0, 0, 0],  # row 2
                [0, 0, 0, 0, 0, 0, 0],  # row 3 — empty, gravity-valid (row 2 is filled)
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert env.is_threatening_move(2) is True
        pos = env.threatening_position(2)
        assert pos == (3, 0)

    def test_positive_diagonal_threat(self):
        """3 pieces on positive diagonal + open cell → threat detected."""
        env = make_env_with_board(
            [
                [2, 1, 1, 0, 0, 0, 0],  # row 0
                [1, 2, 0, 0, 0, 0, 0],  # row 1
                [0, 0, 2, 0, 0, 0, 0],  # row 2
                [0, 0, 0, 0, 0, 0, 0],  # row 3 — (3,3) needs gravity support
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        # (3, 3) is NOT gravity-valid (nothing at (2, 3)), so no threat
        assert env.is_threatening_move(2) is False

        # Add support below (2, 3) so (3, 3) becomes gravity-valid
        env._board[2][3] = 1  # support piece
        env._board[3][3] = 0  # the open cell — now gravity-valid since (2,3) is filled
        # Still not valid — (3,3) needs something at (2,3) which we just set
        assert env.is_threatening_move(2) is True
        assert env.threatening_position(2) == (3, 3)

    def test_negative_diagonal_threat(self):
        """3 pieces on negative diagonal + open cell → threat detected."""
        env = make_env_with_board(
            [
                [0, 0, 0, 2, 0, 0, 0],  # row 0
                [0, 0, 2, 1, 0, 0, 0],  # row 1
                [0, 2, 1, 1, 0, 0, 0],  # row 2
                [0, 1, 1, 1, 0, 0, 0],  # row 3 — (3, 0) is the open cell
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        # (3, 0) is NOT gravity-valid — nothing at (2, 0)
        assert env.is_threatening_move(2) is False

        # Add support at (2, 0) to make (3, 0) gravity-valid
        env._board[0][0] = 1
        env._board[1][0] = 1
        env._board[2][0] = 1
        assert env.is_threatening_move(2) is True
        assert env.threatening_position(2) == (3, 0)

    def test_no_threat_scattered_pieces(self):
        """Scattered pieces with no 3-in-a-row → no threat."""
        env = make_env_with_board(
            [
                [2, 0, 0, 0, 0, 0, 2],
                [0, 0, 2, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert env.is_threatening_move(2) is False
        assert env.threatening_position(2) is None

    def test_gravity_invalid_cell_rejected(self):
        """A 3-in-a-row with an open cell hovering in mid-air is NOT a threat."""
        env = make_env_with_board(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [2, 2, 2, 0, 0, 0, 0],  # row 1: 3-in-a-row but (1, 3) not gravity-valid
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        # (1, 3) has nothing below at (0, 3) → not gravity-valid
        assert env.is_threatening_move(2) is False

    def test_threatening_position_returns_correct_cell(self):
        """The returned position is the empty playable cell, not one of the pieces."""
        env = make_env_with_board(
            [
                [
                    0,
                    2,
                    2,
                    2,
                    0,
                    0,
                    0,
                ],  # the empty cell is (0, 0), gravity-valid (bottom)
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        pos = env.threatening_position(2)
        # The window [0,1,2,3] has empty at index 0 → (0, 0)
        assert pos is not None
        r, c = pos
        assert env._board[r][c] == 0  # it's the empty cell


# ---------------------------------------------------------------------------
# P0-3: Player attribution — Q-table updated for the acting player
# ---------------------------------------------------------------------------


class TestPlayerAttribution:
    def test_update_values_uses_acting_player(self):
        """Q-table update should be keyed to the player who performed the action."""
        env = Connect4Environment()
        ql = QLearning(env, epsilon=1.0, gamma=0.9, alpha=0.5)

        state = (0, 0)
        action = ACTION_DROP
        next_state = (0, 1)
        reward = 1

        # Update as player 1
        ql.update_values(state, action, next_state, reward, piece=1)
        assert (state, action) in ql.qtable
        val_p1 = ql.qtable[(state, action)]
        assert val_p1 > 0  # should have learned something

    def test_both_players_update_qtable(self):
        """Both players should update the Q-table (Bug 3 / P1 fix removed piece==1 guard)."""
        env = Connect4Environment()

        state = (0, 0)
        action = ACTION_DROP
        next_state = (0, 1)

        # Player 1 updates
        ql1 = QLearning(env, epsilon=1.0, gamma=0.9, alpha=0.5)
        ql1.update_values(state, action, next_state, reward=5, piece=1)
        assert (state, action) in ql1.qtable
        assert ql1.qtable[(state, action)] > 0

        # Player 2 also updates (was blocked before P1 fix)
        ql2 = QLearning(env, epsilon=1.0, gamma=0.9, alpha=0.5)
        ql2.update_values(state, action, next_state, reward=5, piece=2)
        assert (state, action) in ql2.qtable
        assert ql2.qtable[(state, action)] > 0
