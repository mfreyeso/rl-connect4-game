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
    rewards_map = {ACTION_BLOCK: 100, ACTION_DROP: 10, ACTION_DROP_WIN: 500}

    return rewards_map[action]
