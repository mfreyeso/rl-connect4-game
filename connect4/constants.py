from typing import Final

N_ROWS = 6
N_COLS = 7

SQUARE_SIZE = 100
HEADER_HEIGHT = 80
WIDTH = N_COLS * SQUARE_SIZE
HEIGHT = (N_ROWS + 1) * SQUARE_SIZE + HEADER_HEIGHT

WINDOW_TITLE = "Connect 4"

# --- Color palette ---
BG_COLOR = (20, 22, 36)  # dark navy background
BOARD_COLOR = (30, 60, 150)  # deep blue board
CELL_EMPTY = (15, 17, 30)  # empty cell (very dark)
PLAYER_1_COLOR = (230, 57, 70)  # red for machine (piece 1)
PLAYER_2_COLOR = (255, 200, 50)  # gold/yellow for human (piece 2)
WHITE = (255, 255, 255)
LIGHT_GRAY = (180, 180, 200)
ACCENT = (100, 140, 255)  # button / input accent
ACCENT_HOVER = (130, 165, 255)  # button hover
OVERLAY_COLOR = (0, 0, 0, 180)  # semi-transparent overlay for modal
WIN_COLOR = (50, 205, 100)  # green for win text
LOSE_COLOR = (230, 57, 70)  # red for lose text
DRAW_COLOR = (180, 180, 200)  # gray for draw text

PLAYER_COLORS = {1: PLAYER_1_COLOR, 2: PLAYER_2_COLOR}

RADIUS = int(SQUARE_SIZE / 2 - 5)

# --- Reward constants ---
REWARD_WIN: Final[float] = 1.0
REWARD_LOSE: Final[float] = -1.0
REWARD_DRAW: Final[float] = 0.0
REWARD_STEP: Final[float] = 0.0
