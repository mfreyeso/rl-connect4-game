import math
import sys

import pygame

from connect4.constants import (
    N_COLS,
    N_ROWS,
    SQUARE_SIZE,
    HEADER_HEIGHT,
    HEIGHT,
    WIDTH,
    BG_COLOR,
    BOARD_COLOR,
    CELL_EMPTY,
    PLAYER_COLORS,
    PLAYER_1_COLOR,
    PLAYER_2_COLOR,
    WHITE,
    LIGHT_GRAY,
    ACCENT,
    ACCENT_HOVER,
    WIN_COLOR,
    LOSE_COLOR,
    DRAW_COLOR,
    RADIUS,
    WINDOW_TITLE,
)
from connect4.environment import Connect4Environment

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
pygame.font.init()

FONT_TITLE = pygame.font.SysFont("helvetica", 64, bold=True)
FONT_LABEL = pygame.font.SysFont("helvetica", 28)
FONT_INPUT = pygame.font.SysFont("helvetica", 30)
FONT_BUTTON = pygame.font.SysFont("helvetica", 30, bold=True)
FONT_SCORE = pygame.font.SysFont("helvetica", 24, bold=True)
FONT_SCORE_NUM = pygame.font.SysFont("helvetica", 36, bold=True)
FONT_RESULT = pygame.font.SysFont("helvetica", 44, bold=True)
FONT_MODAL_LABEL = pygame.font.SysFont("helvetica", 26)
FONT_MODAL_BTN = pygame.font.SysFont("helvetica", 28, bold=True)


# ===================================================================
#  Screen 1 — Start Screen
# ===================================================================
class StartScreen:
    """Title, nickname input, and Play button."""

    def show(self, screen: pygame.Surface) -> str:
        """Block until the user types a nickname and clicks Play. Returns the nickname."""
        clock = pygame.time.Clock()
        nickname = ""
        cursor_visible = True
        cursor_timer = 0

        while True:
            dt = clock.tick(60)
            cursor_timer += dt
            if cursor_timer >= 500:
                cursor_visible = not cursor_visible
                cursor_timer = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and nickname.strip():
                        return nickname.strip()
                    elif event.key == pygame.K_BACKSPACE:
                        nickname = nickname[:-1]
                    elif (
                        len(nickname) < 16
                        and event.unicode.isprintable()
                        and event.unicode != ""
                    ):
                        nickname += event.unicode

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if (
                        self._play_rect
                        and self._play_rect.collidepoint(event.pos)
                        and nickname.strip()
                    ):
                        return nickname.strip()

            self._draw(screen, nickname, cursor_visible)

    # ---- drawing helpers ----
    def _draw(self, screen: pygame.Surface, nickname: str, cursor_visible: bool):
        screen.fill(BG_COLOR)

        # Title
        title_surf = FONT_TITLE.render(WINDOW_TITLE, True, WHITE)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 140))
        screen.blit(title_surf, title_rect)

        # Subtitle decoration
        line_y = title_rect.bottom + 12
        pygame.draw.line(
            screen, ACCENT, (WIDTH // 2 - 100, line_y), (WIDTH // 2 + 100, line_y), 3
        )

        # Label
        label_surf = FONT_LABEL.render("Type your nickname", True, LIGHT_GRAY)
        label_rect = label_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(label_surf, label_rect)

        # Input box
        input_w, input_h = 320, 48
        input_rect = pygame.Rect(
            WIDTH // 2 - input_w // 2, HEIGHT // 2 - 10, input_w, input_h
        )
        pygame.draw.rect(screen, (40, 44, 65), input_rect, border_radius=8)
        pygame.draw.rect(screen, ACCENT, input_rect, 2, border_radius=8)

        text_surf = FONT_INPUT.render(nickname, True, WHITE)
        screen.blit(text_surf, (input_rect.x + 12, input_rect.y + 9))

        if cursor_visible:
            cursor_x = input_rect.x + 12 + text_surf.get_width() + 2
            pygame.draw.line(
                screen,
                WHITE,
                (cursor_x, input_rect.y + 8),
                (cursor_x, input_rect.y + input_h - 8),
                2,
            )

        # Play button
        btn_w, btn_h = 180, 50
        btn_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, HEIGHT // 2 + 60, btn_w, btn_h)
        self._play_rect = btn_rect

        mouse_pos = pygame.mouse.get_pos()
        is_hover = btn_rect.collidepoint(mouse_pos) and nickname.strip()
        btn_color = ACCENT_HOVER if is_hover else ACCENT
        if not nickname.strip():
            btn_color = (60, 65, 90)  # muted when disabled

        pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
        btn_text = FONT_BUTTON.render("Play", True, WHITE)
        screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

        pygame.display.update()


# ===================================================================
#  Score Header (drawn at the top of the game screen)
# ===================================================================
class ScoreHeader:
    """Renders the scoreboard bar above the board."""

    def draw(
        self,
        screen: pygame.Surface,
        nickname: str,
        human_score: int,
        machine_score: int,
    ):
        header_rect = pygame.Rect(0, 0, WIDTH, HEADER_HEIGHT)
        pygame.draw.rect(screen, (25, 28, 48), header_rect)
        pygame.draw.line(
            screen, ACCENT, (0, HEADER_HEIGHT - 1), (WIDTH, HEADER_HEIGHT - 1), 2
        )

        # Human (left side)
        human_name = FONT_SCORE.render(nickname, True, PLAYER_2_COLOR)
        human_num = FONT_SCORE_NUM.render(str(human_score), True, WHITE)
        screen.blit(human_name, (20, 12))
        screen.blit(human_num, (20, 42))

        # Machine (right side)
        machine_name = FONT_SCORE.render("Machine", True, PLAYER_1_COLOR)
        machine_num = FONT_SCORE_NUM.render(str(machine_score), True, WHITE)
        screen.blit(machine_name, (WIDTH - machine_name.get_width() - 20, 12))
        screen.blit(machine_num, (WIDTH - machine_num.get_width() - 20, 42))

        # Center label
        vs_text = FONT_SCORE.render("vs", True, LIGHT_GRAY)
        screen.blit(vs_text, vs_text.get_rect(center=(WIDTH // 2, HEADER_HEIGHT // 2)))


# ===================================================================
#  Board UI (adjusted for header offset)
# ===================================================================
class BoardUI:
    def __init__(self):
        self._score_header = ScoreHeader()

    @staticmethod
    def draw_board(board, screen):
        """Draw the board grid and pieces below the header."""
        y_offset = HEADER_HEIGHT

        for c in range(N_COLS):
            for r in range(N_ROWS):
                pygame.draw.rect(
                    screen,
                    BOARD_COLOR,
                    (
                        c * SQUARE_SIZE,
                        r * SQUARE_SIZE + SQUARE_SIZE + y_offset,
                        SQUARE_SIZE,
                        SQUARE_SIZE,
                    ),
                )
                pygame.draw.circle(
                    screen,
                    CELL_EMPTY,
                    (
                        int(c * SQUARE_SIZE + SQUARE_SIZE / 2),
                        int(r * SQUARE_SIZE + SQUARE_SIZE + SQUARE_SIZE / 2) + y_offset,
                    ),
                    RADIUS,
                )

        for c in range(N_COLS):
            for r in range(N_ROWS):
                if board[r][c] != 0:
                    color = PLAYER_1_COLOR if board[r][c] == 1 else PLAYER_2_COLOR
                    # Board row 0 = bottom → screen row (N_ROWS - 1)
                    screen_r = N_ROWS - 1 - r
                    pygame.draw.circle(
                        screen,
                        color,
                        (
                            int(c * SQUARE_SIZE + SQUARE_SIZE / 2),
                            int(screen_r * SQUARE_SIZE + SQUARE_SIZE + SQUARE_SIZE / 2)
                            + y_offset,
                        ),
                        RADIUS,
                    )

        pygame.display.update()

    def show_board(
        self,
        env: Connect4Environment,
        screen,
        qtable,
        nickname: str = "Player",
        human_score: int = 0,
        machine_score: int = 0,
    ) -> str:
        """Run the game loop. Returns 'human_win', 'machine_win', or 'draw'."""
        y_offset = HEADER_HEIGHT
        hover_y = y_offset  # top area just above the board, below header

        # Redraw everything
        screen.fill(BG_COLOR)
        self._score_header.draw(screen, nickname, human_score, machine_score)
        self.draw_board(env.board, screen)

        turn = env.turn
        machine_pos = 1
        human_pos = 2

        result = "draw"

        while not env.finished:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEMOTION:
                    if env.turn != 0:  # human's turn
                        # Clear hover row
                        pygame.draw.rect(
                            screen, BG_COLOR, (0, y_offset, WIDTH, SQUARE_SIZE)
                        )
                        posx = event.pos[0]
                        pygame.draw.circle(
                            screen,
                            PLAYER_COLORS[human_pos],
                            (posx, hover_y + int(SQUARE_SIZE / 2)),
                            RADIUS,
                        )

                pygame.display.update()

                # Machine turn (turn == 0, piece 1)
                if env.turn == 0:
                    valid_cols = env.get_valid_columns()
                    if not valid_cols:
                        result = "draw"
                        env.finished = True
                        continue

                    best_col = env.choose_column(machine_pos, qtable)
                    row = env.get_next_open_row(best_col)
                    env.drop_piece(row, best_col, machine_pos)

                    if env.is_winning_move(machine_pos):
                        result = "machine_win"
                        env.finished = True

                    if not env.get_valid_columns() and not env.finished:
                        result = "draw"
                        env.finished = True

                    turn += 1
                    env.turn = turn % 2

                    screen.fill(BG_COLOR)
                    self._score_header.draw(
                        screen, nickname, human_score, machine_score
                    )
                    self.draw_board(env.board, screen)
                    pygame.display.update()

                    if env.finished:
                        pygame.time.wait(600)

                    continue

                # Human turn (turn == 1, piece 2)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pygame.draw.rect(
                        screen, BG_COLOR, (0, y_offset, WIDTH, SQUARE_SIZE)
                    )
                    posx = event.pos[0]
                    col = int(math.floor(posx / SQUARE_SIZE))

                    if 0 <= col < N_COLS and env.is_valid_location(col):
                        row = env.get_next_open_row(col)
                        env.drop_piece(row, col, human_pos)

                        if env.is_winning_move(human_pos):
                            result = "human_win"
                            env.finished = True

                        if not env.get_valid_columns() and not env.finished:
                            result = "draw"
                            env.finished = True

                    turn += 1
                    env.turn = turn % 2

                    screen.fill(BG_COLOR)
                    self._score_header.draw(
                        screen, nickname, human_score, machine_score
                    )
                    self.draw_board(env.board, screen)
                    pygame.display.update()

                    if env.finished:
                        pygame.time.wait(600)

        return result


# ===================================================================
#  Screen 3 — End-Game Modal
# ===================================================================
class EndGameModal:
    """Shows the game result and Yes/No buttons for play-again."""

    def show(
        self,
        screen: pygame.Surface,
        result: str,
        nickname: str,
        human_score: int,
        machine_score: int,
    ) -> bool:
        """Display modal over the current screen. Returns True to play again, False to quit."""
        clock = pygame.time.Clock()

        # Build result message
        if result == "human_win":
            msg = f"{nickname} wins!"
            msg_color = WIN_COLOR
        elif result == "machine_win":
            msg = "Machine wins!"
            msg_color = LOSE_COLOR
        else:
            msg = "It's a draw!"
            msg_color = DRAW_COLOR

        # Modal dimensions
        modal_w, modal_h = 420, 260
        modal_x = WIDTH // 2 - modal_w // 2
        modal_y = HEIGHT // 2 - modal_h // 2

        # Button rects
        btn_w, btn_h = 120, 46
        yes_rect = pygame.Rect(
            modal_x + modal_w // 2 - btn_w - 20,
            modal_y + modal_h - btn_h - 30,
            btn_w,
            btn_h,
        )
        no_rect = pygame.Rect(
            modal_x + modal_w // 2 + 20,
            modal_y + modal_h - btn_h - 30,
            btn_w,
            btn_h,
        )

        while True:
            clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if yes_rect.collidepoint(event.pos):
                        return True
                    if no_rect.collidepoint(event.pos):
                        return False

            # Draw overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            # Modal background
            modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
            pygame.draw.rect(screen, (30, 34, 55), modal_rect, border_radius=16)
            pygame.draw.rect(screen, ACCENT, modal_rect, 2, border_radius=16)

            # Result text
            result_surf = FONT_RESULT.render(msg, True, msg_color)
            screen.blit(
                result_surf,
                result_surf.get_rect(center=(WIDTH // 2, modal_y + 55)),
            )

            # Score line
            score_text = f"{nickname}: {human_score}  —  Machine: {machine_score}"
            score_surf = FONT_MODAL_LABEL.render(score_text, True, LIGHT_GRAY)
            screen.blit(
                score_surf,
                score_surf.get_rect(center=(WIDTH // 2, modal_y + 105)),
            )

            # Question
            q_surf = FONT_MODAL_LABEL.render("Do you want to play again?", True, WHITE)
            screen.blit(q_surf, q_surf.get_rect(center=(WIDTH // 2, modal_y + 150)))

            # Yes button
            yes_hover = yes_rect.collidepoint(mouse_pos)
            pygame.draw.rect(
                screen,
                WIN_COLOR if yes_hover else (40, 140, 70),
                yes_rect,
                border_radius=10,
            )
            yes_text = FONT_MODAL_BTN.render("Yes", True, WHITE)
            screen.blit(yes_text, yes_text.get_rect(center=yes_rect.center))

            # No button
            no_hover = no_rect.collidepoint(mouse_pos)
            pygame.draw.rect(
                screen,
                LOSE_COLOR if no_hover else (160, 40, 50),
                no_rect,
                border_radius=10,
            )
            no_text = FONT_MODAL_BTN.render("No", True, WHITE)
            screen.blit(no_text, no_text.get_rect(center=no_rect.center))

            pygame.display.update()
