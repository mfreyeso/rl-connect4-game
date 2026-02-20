"""Tests for the redesigned Connect 4 Q-learning architecture."""

import numpy as np

from connect4.constants import N_COLS, N_ROWS, REWARD_WIN, REWARD_STEP
from connect4.environment import Connect4Environment
from connect4.qlearning import QLearning


def make_env_with_board(board: list[list[int]]) -> Connect4Environment:
    """Create an environment with a pre-set board (row 0 = bottom)."""
    env = Connect4Environment()
    env._board = np.array(board, dtype=float)
    return env


# Environment — State encoding


class TestGetState:
    def test_returns_tuple_of_correct_length(self):
        env = Connect4Environment()
        state = env.get_state()
        assert isinstance(state, tuple)
        assert len(state) == N_ROWS * N_COLS

    def test_is_hashable(self):
        env = Connect4Environment()
        state = env.get_state()
        d = {state: 1}
        assert d[state] == 1

    def test_different_boards_different_states(self):
        env = Connect4Environment()
        s1 = env.get_state()
        env.drop_piece(0, 0, 1)
        s2 = env.get_state()
        assert s1 != s2


# Environment — Valid columns


class TestGetValidColumns:
    def test_empty_board_all_columns(self):
        env = Connect4Environment()
        assert env.get_valid_columns() == list(range(N_COLS))

    def test_full_column_excluded(self):
        env = Connect4Environment()
        for r in range(N_ROWS):
            env._board[r][3] = 1
        valid = env.get_valid_columns()
        assert 3 not in valid
        assert len(valid) == N_COLS - 1


# Environment — Step function


class TestStep:
    def test_applies_gravity(self):
        env = Connect4Environment()
        env.step(3, 1)
        assert env._board[0][3] == 1  # bottom row
        env.step(3, 2)
        assert env._board[1][3] == 2  # stacks on top

    def test_win_reward(self):
        env = make_env_with_board(
            [
                [1, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        _, reward, done = env.step(3, 1)
        assert reward == REWARD_WIN
        assert done is True

    def test_draw_detection(self):
        """Board with only one cell left → step fills it → draw."""
        env = Connect4Environment()
        env._board = np.ones((N_ROWS, N_COLS))
        env._board[N_ROWS - 1][0] = 0  # one cell left
        _, reward, done = env.step(0, 1)
        assert done is True

    def test_normal_step(self):
        env = Connect4Environment()
        _, reward, done = env.step(0, 1)
        assert reward == REWARD_STEP
        assert done is False


# Environment — Threat detection


class TestThreatDetection:
    def test_horizontal_threat(self):
        env = make_env_with_board(
            [
                [2, 2, 2, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert env.is_threatening_move(2) is True
        assert env.threatening_position(2) == (0, 3)

    def test_vertical_threat(self):
        env = make_env_with_board(
            [
                [2, 0, 0, 0, 0, 0, 0],
                [2, 0, 0, 0, 0, 0, 0],
                [2, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert env.is_threatening_move(2) is True
        assert env.threatening_position(2) == (3, 0)

    def test_no_threat_scattered(self):
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

    def test_gravity_invalid_rejected(self):
        env = make_env_with_board(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [2, 2, 2, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert env.is_threatening_move(2) is False


# Q-Learning — Action selection


class TestQLearningActions:
    def test_explore_picks_random(self):
        env = Connect4Environment()
        ql = QLearning(env, epsilon=1.0)
        cols = env.get_valid_columns()
        action = ql.choose_action(env.get_state(), cols)
        assert action in cols

    def test_exploit_picks_best(self):
        env = Connect4Environment()
        ql = QLearning(env, epsilon=0.0)
        state = env.get_state()
        ql.qtable[(state, 3)] = 10.0  # column 3 is best
        action = ql.choose_action(state, env.get_valid_columns())
        assert action == 3


# Q-Learning — Update values


class TestQLearningUpdate:
    def test_win_increases_q_value(self):
        env = Connect4Environment()
        ql = QLearning(env, epsilon=0.0, alpha=0.5, gamma=0.95)
        state = env.get_state()
        next_state = (0,) * 42  # dummy

        ql.update_values(state, 3, next_state, REWARD_WIN, [])
        assert ql.qtable[(state, 3)] > 0

    def test_lose_decreases_q_value(self):
        env = Connect4Environment()
        ql = QLearning(env, epsilon=0.0, alpha=0.5, gamma=0.95)
        state = env.get_state()
        next_state = (0,) * 42

        from connect4.constants import REWARD_LOSE

        ql.update_values(state, 3, next_state, REWARD_LOSE, [])
        assert ql.qtable[(state, 3)] < 0

    def test_training_short_run(self):
        """100 episodes should complete without errors."""
        env = Connect4Environment()
        ql = QLearning(env, epsilon=1.0, gamma=0.95, alpha=0.1)
        table = ql.run(100)
        assert isinstance(table, dict)
        assert len(table) > 0


# Agent column selection heuristic


class TestChooseColumn:
    def test_takes_winning_move(self):
        """Agent should pick the column that wins immediately."""
        env = make_env_with_board(
            [
                [1, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        col = env.choose_column(1, {})
        assert col == 3

    def test_blocks_opponent_win(self):
        """Agent should block the opponent's winning column."""
        env = make_env_with_board(
            [
                [2, 2, 2, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        col = env.choose_column(1, {})
        assert col == 3

    def test_falls_back_to_qtable(self):
        """When no win/block, pick the column with highest Q-value."""
        env = Connect4Environment()
        state = env.get_state()
        qtable = {(state, 4): 5.0}
        col = env.choose_column(1, qtable)
        assert col == 4
