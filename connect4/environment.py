import random
import numpy as np

from connect4.constants import N_ROWS, N_COLS


class Connect4Environment:
    def __init__(self):
        self._board = np.zeros((N_ROWS, N_COLS))
        self.initial_turn = random.randint(0, 1)
        self._turn = self.initial_turn
        self._state = None
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

    @property
    def state(self) -> tuple[int, int]:
        return self._state

    @state.setter
    def state(self, value: tuple[int, int]):
        self._state = value

    def state_value(self, state: tuple[int, int]):
        return self._board[state[0]][state[1]]

    def get_reward(self, state: tuple[int, int], piece: int) -> int:
        # todo: our reward based on the state reached
        #  ~ analyze if we block or align one more pos to shape the 4.
        if self._board:
            return 0

    def get_possible_actions(self, state: tuple[int, int], piece: int) -> list[tuple[int, int]]:
        available_positions = []
        filled_positions = {}
        temp_filled_cols = []

        for row in range(N_ROWS):
            for col in range(N_COLS):
                if self._board[row][col] == 0:
                    available_positions.append((row, col))
                else:
                    filled_positions[(row, col)] = self.board[row][col]
                    temp_filled_cols.append(col)

            if len(temp_filled_cols) != N_COLS:
                break

        for col in temp_filled_cols:
            for row in range(N_ROWS):
                if self._board[row][col] != 0:
                    filled_positions[(row, col)] = self.board[row][col]
                else:
                    available_positions.append((row, col))
                    break

        # todo: we could sample the available options based on state and piece.

        return available_positions

    def is_terminal(self, player_1: int, player_2: int):
        return self.winning_move(player_1) or self.winning_move(player_2)

    def is_valid_location(self, col):
        return self._board[N_ROWS - 1][col] == 0

    def get_next_open_row(self, col):
        for r in range(N_ROWS):
            if self._board[r][col] == 0:
                return r

    def drop_piece(self, row, col, piece):
        # todo: replace later with drop_piece_reward
        self._board[row][col] = piece

    def drop_piece_reward(self, row, col, piece) -> tuple[tuple[int, int], int]:
        reached_stated = (row, col)

        self._board[row][col] = piece
        self.state = reached_stated

        return reached_stated, self.get_reward(reached_stated, piece)

    def winning_move(self, piece) -> bool:
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

        return False
