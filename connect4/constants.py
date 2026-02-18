from typing import Final

N_ROWS = 6
N_COLS = 7

SQUARE_SIZE = 100
WIDTH = N_COLS * SQUARE_SIZE
HEIGHT = (N_ROWS + 1) * SQUARE_SIZE

REWARD_WIN: Final[float] = 1.0
REWARD_LOSE: Final[float] = -1.0
REWARD_DRAW: Final[float] = 0.0
REWARD_STEP: Final[float] = 0.0
