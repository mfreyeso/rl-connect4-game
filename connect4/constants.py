from typing import Final

N_ROWS = 6
N_COLS = 7

SQUARE_SIZE = 100
WIDTH = N_COLS * SQUARE_SIZE
HEIGHT = (N_ROWS + 1) * SQUARE_SIZE

ACTION_BLOCK: Final[str] = "block"
ACTION_DROP: Final[str] = "drop"
ACTION_DROP_WIN: Final[str] = "drop_win"


def get_reward(action: str) -> int:
    rewards_map = {ACTION_BLOCK: 5, ACTION_DROP: 1, ACTION_DROP_WIN: 10}
    return rewards_map[action]
