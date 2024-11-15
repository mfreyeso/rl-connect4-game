import random
import numpy as np

from connect4.constants import N_ROWS, N_COLS


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

    def is_valid_location(self, col):
        return self._board[N_ROWS - 1][col] == 0

    def get_next_open_row(self, col):
        for r in range(N_ROWS):
            if self._board[r][col] == 0:
                return r

    def drop_piece(self, row, col, piece):
        self._board[row][col] = piece

    def winning_move(self, piece):
        # revisando las posiciones horizontales
        for c in range(N_COLS - 3):
            for r in range(N_ROWS):
                if (
                    self._board[r][c] == piece
                    and self._board[r][c + 1] == piece
                    and self._board[r][c + 2] == piece
                    and self._board[r][c + 3] == piece
                ):
                    return True

        # verificando las posiciones verticales
        for c in range(N_COLS):
            for r in range(N_ROWS - 3):
                if (
                    self._board[r][c] == piece
                    and self._board[r + 1][c] == piece
                    and self._board[r + 2][c] == piece
                    and self._board[r + 3][c] == piece
                ):
                    return True

        # verificando diagonales positivas
        for c in range(N_COLS - 3):
            for r in range(N_ROWS - 3):
                if (
                    self._board[r][c] == piece
                    and self._board[r + 1][c + 1] == piece
                    and self._board[r + 2][c + 2] == piece
                    and self._board[r + 3][c + 3] == piece
                ):
                    return True

        # verificando diagonales negativas
        for c in range(N_COLS - 3):
            for r in range(3, N_ROWS):
                if (
                    self._board[r][c] == piece
                    and self._board[r - 1][c + 1] == piece
                    and self._board[r - 2][c + 2] == piece
                    and self._board[r - 3][c + 3] == piece
                ):
                    return True
