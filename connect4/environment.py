import random


import numpy as np

from connect4.constants import (
    N_ROWS,
    N_COLS,
    REWARD_WIN,
    REWARD_DRAW,
    REWARD_STEP,
)


class Connect4Environment:
    def __init__(self):
        self._board = np.zeros((N_ROWS, N_COLS))
        self.initial_turn = random.randint(0, 1)
        self._turn = self.initial_turn
        self._finished = False

    @property
    def board(self):
        return self._board

    @property
    def turn(self):
        return self._turn

    @turn.setter
    def turn(self, value):
        self._turn = value

    @property
    def finished(self):
        return self._finished

    @finished.setter
    def finished(self, value):
        self._finished = value

    # State & action interface for Q-learning

    def get_state(self) -> tuple:
        """Return the board as a hashable tuple for Q-table keys."""
        return tuple(self._board.flatten().astype(int))

    def get_valid_columns(self) -> list[int]:
        """Return column indices that still have room."""
        return [c for c in range(N_COLS) if self._board[N_ROWS - 1][c] == 0]

    def step(self, col: int, piece: int) -> tuple[tuple, float, bool]:
        """Place piece in column. Returns (next_state, reward, done)."""
        row = self.get_next_open_row(col)
        self.drop_piece(row, col, piece)

        if self.is_winning_move(piece):
            return self.get_state(), REWARD_WIN, True

        if not self.get_valid_columns():
            return self.get_state(), REWARD_DRAW, True

        return self.get_state(), REWARD_STEP, False

    # Board helpers

    def is_valid_location(self, col):
        return self._board[N_ROWS - 1][col] == 0

    def get_next_open_row(self, col):
        for r in range(N_ROWS):
            if self._board[r][col] == 0:
                return r

    def drop_piece(self, row, col, piece):
        self._board[row][col] = piece

    # Win / threat detection

    def is_winning_move(self, piece) -> bool:
        return bool(self.winner_position(piece))

    def winner_position(self, piece) -> list[tuple[int, int]] | None:
        # Horizontal
        for c in range(N_COLS - 3):
            for r in range(N_ROWS):
                if (
                    self._board[r][c] == piece
                    and self._board[r][c + 1] == piece
                    and self._board[r][c + 2] == piece
                    and self._board[r][c + 3] == piece
                ):
                    return [(r, c + i) for i in range(4)]

        # Vertical
        for c in range(N_COLS):
            for r in range(N_ROWS - 3):
                if (
                    self._board[r][c] == piece
                    and self._board[r + 1][c] == piece
                    and self._board[r + 2][c] == piece
                    and self._board[r + 3][c] == piece
                ):
                    return [(r + i, c) for i in range(4)]

        # Positive diagonal
        for c in range(N_COLS - 3):
            for r in range(N_ROWS - 3):
                if (
                    self._board[r][c] == piece
                    and self._board[r + 1][c + 1] == piece
                    and self._board[r + 2][c + 2] == piece
                    and self._board[r + 3][c + 3] == piece
                ):
                    return [(r + i, c + i) for i in range(4)]

        # Negative diagonal
        for c in range(N_COLS - 3):
            for r in range(3, N_ROWS):
                if (
                    self._board[r][c] == piece
                    and self._board[r - 1][c + 1] == piece
                    and self._board[r - 2][c + 2] == piece
                    and self._board[r - 3][c + 3] == piece
                ):
                    return [(r - i, c + i) for i in range(4)]

        return None

    def threatening_position(self, piece) -> tuple[int, int] | None:
        """Find a gravity-valid empty cell that completes a 3-in-a-row threat."""

        def is_gravity_valid(r: int, c: int) -> bool:
            return r == 0 or self._board[r - 1][c] != 0

        def check_window(cells: list[tuple[int, int]]) -> tuple[int, int] | None:
            values = [self._board[r][c] for r, c in cells]
            if values.count(piece) == 3 and values.count(0) == 1:
                empty_idx = values.index(0)
                er, ec = cells[empty_idx]
                if is_gravity_valid(er, ec):
                    return (er, ec)
            return None

        for c in range(N_COLS - 3):
            for r in range(N_ROWS):
                result = check_window([(r, c + i) for i in range(4)])
                if result:
                    return result

        for c in range(N_COLS):
            for r in range(N_ROWS - 3):
                result = check_window([(r + i, c) for i in range(4)])
                if result:
                    return result

        for c in range(N_COLS - 3):
            for r in range(N_ROWS - 3):
                result = check_window([(r + i, c + i) for i in range(4)])
                if result:
                    return result

        for c in range(N_COLS - 3):
            for r in range(3, N_ROWS):
                result = check_window([(r - i, c + i) for i in range(4)])
                if result:
                    return result

        return None

    def is_threatening_move(self, piece) -> bool:
        """Return True if the given piece has a 3-in-a-row threat with a playable open cell."""
        return self.threatening_position(piece) is not None

    # Agent column selection with heuristic priority

    def choose_column(self, piece: int, qtable: dict) -> int:
        """Pick a column using heuristic win/block priority, then Q-table fallback."""
        valid_cols = self.get_valid_columns()
        opp = 2 if piece == 1 else 1

        for c in valid_cols:
            r = self.get_next_open_row(c)
            self._board[r][c] = piece
            win = self.is_winning_move(piece)
            self._board[r][c] = 0
            if win:
                return c

        for c in valid_cols:
            r = self.get_next_open_row(c)
            self._board[r][c] = opp
            win = self.is_winning_move(opp)
            self._board[r][c] = 0
            if win:
                return c

        state = self.get_state()
        q_vals = {c: qtable.get((state, c), 0.0) for c in valid_cols}
        return max(q_vals, key=lambda c: q_vals[c])

    # Lifecycle

    def reset(self):
        self._board = np.zeros((N_ROWS, N_COLS))
        self.initial_turn = random.randint(0, 1)
        self._turn = self.initial_turn
        self._finished = False
