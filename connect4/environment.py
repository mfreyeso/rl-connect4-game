import random
from typing import Any, Optional

import numpy as np

from connect4.constants import (
    N_ROWS,
    N_COLS,
    ACTION_DROP,
    ACTION_BLOCK,
    ACTION_DROP_WIN,
    get_reward,
)


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

    def state_value(self, state: tuple[int, int]) -> int:
        return int(self._board[state[0]][state[1]])

    def get_possible_positions(
        self,
    ) -> tuple[list[tuple[int, int]], dict[tuple[int, int], Any]]:
        available_positions = []
        filled_positions = {}
        temp_filled_cols = []

        current_row = 0
        for row in range(N_ROWS):
            for col in range(N_COLS):
                if self._board[row][col] == 0:
                    available_positions.append((row, col))
                else:
                    filled_positions[(row, col)] = self.board[row][col]
                    temp_filled_cols.append(col)

            if len(temp_filled_cols) != N_COLS:
                current_row = row
                break
            else:
                temp_filled_cols = []

        for col in temp_filled_cols:
            available_positions.append((current_row + 1, col))

        return available_positions, filled_positions

    def get_possible_actions(self, piece: int) -> list[str]:
        available_positions, filled_positions = self.get_possible_positions()

        # adversary filled positions
        con_filled_positions = {
            state: piece_i
            for state, piece_i in filled_positions.items()
            if piece_i != piece
        }

        if len([con_filled_positions]) < 3:
            # early steps in game, no required block yet
            actions = [ACTION_DROP]
        else:
            adv_piece = next(iter(con_filled_positions.values()))
            assert adv_piece != piece

            if self.is_winning_move(adv_piece):
                actions = [ACTION_BLOCK]
            else:
                actions = [ACTION_DROP]

        return actions

    def is_terminal(self, state: tuple[int, int]) -> bool:
        piece = self.state_value(state)
        return self.is_winning_move(piece)

    def is_valid_location(self, col):
        return self._board[N_ROWS - 1][col] == 0

    def get_next_open_row(self, col):
        for r in range(N_ROWS):
            if self._board[r][col] == 0:
                return r

    def do_action(self, action: str) -> tuple[tuple[int, int], int]:
        state = self.get_current_state()
        piece = self.state_value(state)

        available_positions, filled_positions = self.get_possible_positions()
        adv_piece = next(iter([p for p in filled_positions.values() if p != piece]))

        is_final = self.is_terminal(state)

        if action == ACTION_DROP:
            row, col = (
                self.winner_position(piece)
                if is_final
                else random.choice(available_positions)
            )
            action = ACTION_DROP_WIN
        else:
            row, col = self.winner_position(adv_piece)

        reached_stated = (row, col)

        self._board[row][col] = piece
        self.state = reached_stated

        return reached_stated, get_reward(action)

    def drop_piece(self, row, col, piece):
        self._board[row][col] = piece

    def is_winning_move(self, piece) -> bool:
        return bool(self.winner_position(piece))

    def winner_position(self, piece) -> Optional[tuple[int, int]]:
        # revisando las posiciones horizontales
        for c in range(N_COLS - 3):
            for r in range(N_ROWS):
                if (
                    self._board[r][c] == piece
                    and self._board[r][c + 1] == piece
                    and self._board[r][c + 2] == piece
                    and self._board[r][c + 3] == piece
                ):
                    return r, c

        # verificando las posiciones verticales
        for c in range(N_COLS):
            for r in range(N_ROWS - 3):
                if (
                    self._board[r][c] == piece
                    and self._board[r + 1][c] == piece
                    and self._board[r + 2][c] == piece
                    and self._board[r + 3][c] == piece
                ):
                    return r, c

        # verificando diagonales positivas
        for c in range(N_COLS - 3):
            for r in range(N_ROWS - 3):
                if (
                    self._board[r][c] == piece
                    and self._board[r + 1][c + 1] == piece
                    and self._board[r + 2][c + 2] == piece
                    and self._board[r + 3][c + 3] == piece
                ):
                    return r, c

        # verificando diagonales negativas
        for c in range(N_COLS - 3):
            for r in range(3, N_ROWS):
                if (
                    self._board[r][c] == piece
                    and self._board[r - 1][c + 1] == piece
                    and self._board[r - 2][c + 2] == piece
                    and self._board[r - 3][c + 3] == piece
                ):
                    return r, c

        return None

    def get_current_state(self):
        return self.state

    def reset(self):
        self._board = np.zeros((N_ROWS, N_COLS))
        self.initial_turn = random.randint(0, 1)
        self._turn = self.initial_turn
        self._state = None
        self._finished = False
