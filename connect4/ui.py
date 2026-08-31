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
from connect4.db import get_repository

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
FONT_STATS = pygame.font.SysFont("helvetica", 22, bold=True)
FONT_TABLE_HDR = pygame.font.SysFont("helvetica", 22, bold=True)
FONT_TABLE_ROW = pygame.font.SysFont("helvetica", 20)


# ===================================================================
#  Leaderboard Modal
# ===================================================================
class LeaderboardModal:
    """Modal displaying top 10 leaderboard rankings and user position."""

    def show(self, screen: pygame.Surface, username: str | None = None):
        clock = pygame.time.Clock()

        repo = get_repository()
        top_players = repo.get_top_players(limit=10)
        user_rank = repo.get_player_rank(username) if username else None
        user_player = repo.get_by_username(username) if username else None

        modal_w, modal_h = 580, 480
        modal_x = (WIDTH - modal_w) // 2
        modal_y = (HEIGHT - modal_h) // 2

        btn_w, btn_h = 140, 42
        close_rect = pygame.Rect(
            WIDTH // 2 - btn_w // 2,
            modal_y + modal_h - btn_h - 20,
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
                    if close_rect.collidepoint(event.pos):
                        return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        return

            # Overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            # Modal Container
            modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
            pygame.draw.rect(screen, (28, 32, 52), modal_rect, border_radius=16)
            pygame.draw.rect(screen, ACCENT, modal_rect, 2, border_radius=16)

            # Title (Smooth White color)
            title_surf = FONT_RESULT.render("Top 10 Leaderboard", True, WHITE)
            screen.blit(
                title_surf, title_surf.get_rect(center=(WIDTH // 2, modal_y + 40))
            )

            # Table Header (Rank, Player, Matches, Win Rate)
            hdr_y = modal_y + 85
            col_x = [
                modal_x + 40,
                modal_x + 120,
                modal_x + 320,
                modal_x + 440,
            ]
            headers = ["Rank", "Player", "Matches", "Win Rate"]
            for x, text in zip(col_x, headers):
                h_surf = FONT_TABLE_HDR.render(text, True, LIGHT_GRAY)
                screen.blit(h_surf, (x, hdr_y))

            pygame.draw.line(
                screen,
                (60, 65, 90),
                (modal_x + 20, hdr_y + 28),
                (modal_x + modal_w - 20, hdr_y + 28),
                2,
            )

            # Table Rows
            row_y = hdr_y + 35
            for idx, p in enumerate(top_players, start=1):
                is_active_user = (
                    username and p.username.lower() == username.strip().lower()
                )
                row_color = ACCENT if is_active_user else WHITE

                rank_str = f"#{idx}"
                name_str = p.username[:18]
                matches_str = str(p.total_games)
                rate_str = f"{p.win_rate:.1f}%"

                screen.blit(
                    FONT_TABLE_ROW.render(rank_str, True, row_color), (col_x[0], row_y)
                )
                screen.blit(
                    FONT_TABLE_ROW.render(name_str, True, row_color), (col_x[1], row_y)
                )
                screen.blit(
                    FONT_TABLE_ROW.render(matches_str, True, row_color),
                    (col_x[2], row_y),
                )
                screen.blit(
                    FONT_TABLE_ROW.render(rate_str, True, row_color), (col_x[3], row_y)
                )
                row_y += 26

            # User Rank Footer (if user not in top 10)
            if username and user_player and user_rank and user_rank > 10:
                footer_y = modal_y + modal_h - 75
                u_str = f"Your Rank: #{user_rank}  |  {user_player.username} ({user_player.win_rate:.1f}% Win Rate)"
                u_surf = FONT_STATS.render(u_str, True, ACCENT)
                screen.blit(u_surf, u_surf.get_rect(center=(WIDTH // 2, footer_y)))

            # Close Button
            close_hover = close_rect.collidepoint(mouse_pos)
            pygame.draw.rect(
                screen,
                ACCENT_HOVER if close_hover else ACCENT,
                close_rect,
                border_radius=8,
            )
            close_text = FONT_MODAL_BTN.render("Close", True, WHITE)
            screen.blit(close_text, close_text.get_rect(center=close_rect.center))

            pygame.display.update()


# ===================================================================
#  Screen 1 — Start Screen
# ===================================================================
class StartScreen:
    """Title, nickname input, and Play/Leaderboard buttons."""

    def __init__(self):
        self._leaderboard_modal = LeaderboardModal()

    def show(self, screen: pygame.Surface) -> str:
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

            # Check if user is allowed to view leaderboard
            can_leaderboard = False
            if nickname.strip():
                repo = get_repository()
                player = repo.get_by_username(nickname.strip())
                can_leaderboard = player is not None and player.total_games >= 1

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
                    if (
                        can_leaderboard
                        and self._leaderboard_rect
                        and self._leaderboard_rect.collidepoint(event.pos)
                    ):
                        self._leaderboard_modal.show(screen, nickname.strip())

            self._draw(screen, nickname, cursor_visible, can_leaderboard)

    def _draw(
        self,
        screen: pygame.Surface,
        nickname: str,
        cursor_visible: bool,
        can_leaderboard: bool,
    ):
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
        btn_w, btn_h = 200, 48
        btn_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, HEIGHT // 2 + 60, btn_w, btn_h)
        self._play_rect = btn_rect

        mouse_pos = pygame.mouse.get_pos()
        is_hover = btn_rect.collidepoint(mouse_pos) and nickname.strip()
        btn_color = ACCENT_HOVER if is_hover else ACCENT
        if not nickname.strip():
            btn_color = (60, 65, 90)

        pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
        btn_text = FONT_BUTTON.render("Play", True, WHITE)
        screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

        # Leaderboard Button (shown for existing users with >= 1 match played)
        self._leaderboard_rect = None
        if can_leaderboard:
            lb_w, lb_h = 200, 48
            lb_rect = pygame.Rect(WIDTH // 2 - lb_w // 2, HEIGHT // 2 + 122, lb_w, lb_h)
            self._leaderboard_rect = lb_rect
            lb_hover = lb_rect.collidepoint(mouse_pos)

            # Elegant secondary style: Indigo/purple container matching main accent
            lb_bg = (60, 75, 125) if lb_hover else (40, 50, 90)
            pygame.draw.rect(screen, lb_bg, lb_rect, border_radius=10)
            pygame.draw.rect(screen, ACCENT, lb_rect, 2, border_radius=10)

            lb_text = FONT_BUTTON.render("Leaderboard", True, WHITE)
            screen.blit(lb_text, lb_text.get_rect(center=lb_rect.center))

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

        for r in range(N_ROWS):
            for c in range(N_COLS):
                rect = (
                    c * SQUARE_SIZE,
                    r * SQUARE_SIZE + y_offset,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                )
                pygame.draw.rect(screen, BOARD_COLOR, rect)

                center = (
                    int(c * SQUARE_SIZE + SQUARE_SIZE / 2),
                    int(r * SQUARE_SIZE + SQUARE_SIZE / 2 + y_offset),
                )
                cell_val = int(board[N_ROWS - 1 - r][c])
                color = CELL_EMPTY if cell_val == 0 else PLAYER_COLORS[cell_val]
                pygame.draw.circle(screen, color, center, RADIUS)

    def draw_winning_line(self, screen, winning_cells):
        """Draw a connecting line across the winning 4 cells."""
        if not winning_cells or len(winning_cells) < 4:
            return

        y_offset = HEADER_HEIGHT
        centers = []
        for r, c in winning_cells:
            cx = int(c * SQUARE_SIZE + SQUARE_SIZE / 2)
            cy = int((N_ROWS - 1 - r) * SQUARE_SIZE + SQUARE_SIZE / 2 + y_offset)
            centers.append((cx, cy))

        xs = [pt[0] for pt in centers]
        ys = [pt[1] for pt in centers]
        start_pt = (min(xs), min(ys))
        end_pt = (max(xs), max(ys))

        if min(xs) != max(xs) and min(ys) != max(ys):
            sorted_pts = sorted(centers, key=lambda p: p[0])
            if sorted_pts[0][1] < sorted_pts[-1][1]:
                start_pt = sorted_pts[0]
                end_pt = sorted_pts[-1]
            else:
                start_pt = sorted_pts[0]
                end_pt = sorted_pts[-1]

        pygame.draw.line(screen, WIN_COLOR, start_pt, end_pt, 8)

    def draw_dropping_piece(self, screen, col, y_pos, piece_color):
        """Animate a piece falling down column `col`."""
        x_center = int(col * SQUARE_SIZE + SQUARE_SIZE / 2)
        pygame.draw.circle(screen, piece_color, (x_center, int(y_pos)), RADIUS)

    def animate_drop(
        self,
        screen,
        board,
        row,
        col,
        piece_color,
        nickname,
        human_score,
        machine_score,
    ):
        """Smoothly animate dropping a piece into position."""
        target_y = (N_ROWS - 1 - row) * SQUARE_SIZE + SQUARE_SIZE / 2 + HEADER_HEIGHT
        y_pos = HEADER_HEIGHT + RADIUS
        speed = 0

        clock = pygame.time.Clock()
        while y_pos < target_y:
            clock.tick(60)
            speed += 2.5
            y_pos += speed
            if y_pos > target_y:
                y_pos = target_y

            screen.fill(BG_COLOR)
            self._score_header.draw(screen, nickname, human_score, machine_score)
            self.draw_board(board, screen)
            self.draw_dropping_piece(screen, col, y_pos, piece_color)
            pygame.display.update()

    def show_board(
        self, env, screen, q_table, nickname, human_score, machine_score
    ) -> str:
        """Main game loop for a single match."""
        HUMAN_PIECE = 2
        MACHINE_PIECE = 1

        clock = pygame.time.Clock()

        # Handle machine opening move if it goes first
        if env.turn == 0:
            col = env.choose_column(MACHINE_PIECE, q_table)
            row = env.get_next_open_row(col)
            self.animate_drop(
                screen,
                env.board,
                row,
                col,
                PLAYER_1_COLOR,
                nickname,
                human_score,
                machine_score,
            )
            env.drop_piece(row, col, MACHINE_PIECE)
            env.turn = 1

        while not env.finished:
            clock.tick(60)
            mouse_x = pygame.mouse.get_pos()[0]
            col_hover = math.floor(mouse_x / SQUARE_SIZE)
            col_hover = max(0, min(col_hover, N_COLS - 1))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    col = math.floor(event.pos[0] / SQUARE_SIZE)
                    col = max(0, min(col, N_COLS - 1))

                    if env.is_valid_location(col):
                        row = env.get_next_open_row(col)
                        self.animate_drop(
                            screen,
                            env.board,
                            row,
                            col,
                            PLAYER_2_COLOR,
                            nickname,
                            human_score,
                            machine_score,
                        )
                        env.drop_piece(row, col, HUMAN_PIECE)

                        if env.is_winning_move(HUMAN_PIECE):
                            env.finished = True
                            return "human_win"

                        if not env.get_valid_columns():
                            env.finished = True
                            return "draw"

                        # Machine turn
                        best_col = env.choose_column(MACHINE_PIECE, q_table)
                        m_row = env.get_next_open_row(best_col)
                        self.animate_drop(
                            screen,
                            env.board,
                            m_row,
                            best_col,
                            PLAYER_1_COLOR,
                            nickname,
                            human_score,
                            machine_score,
                        )
                        env.drop_piece(m_row, best_col, MACHINE_PIECE)

                        if env.is_winning_move(MACHINE_PIECE):
                            env.finished = True
                            return "machine_win"

                        if not env.get_valid_columns():
                            env.finished = True
                            return "draw"

            screen.fill(BG_COLOR)
            self._score_header.draw(screen, nickname, human_score, machine_score)
            self.draw_board(env.board, screen)

            # Hover piece indicator
            if env.is_valid_location(col_hover):
                h_x = int(col_hover * SQUARE_SIZE + SQUARE_SIZE / 2)
                h_y = HEADER_HEIGHT // 2
                pygame.draw.circle(screen, PLAYER_2_COLOR, (h_x, h_y), RADIUS)

            pygame.display.update()

        return "draw"


# ===================================================================
#  End-Game Modal
# ===================================================================
class EndGameModal:
    """Modal screen after game ends."""

    def show(
        self,
        screen: pygame.Surface,
        result: str,
        nickname: str,
        human_score: int,
        machine_score: int,
    ) -> bool:
        """Returns True if 'Yes' (play again), False if 'No' (main menu)."""
        clock = pygame.time.Clock()

        if result == "human_win":
            msg = "You Win! 🎉"
            msg_color = WIN_COLOR
        elif result == "machine_win":
            msg = "Machine Wins! 🤖"
            msg_color = LOSE_COLOR
        else:
            msg = "It's a Draw! 🤝"
            msg_color = DRAW_COLOR

        modal_w, modal_h = 440, 240
        modal_x = (WIDTH - modal_w) // 2
        modal_y = (HEIGHT - modal_h) // 2

        btn_w, btn_h = 130, 44
        yes_rect = pygame.Rect(
            modal_x + 40,
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

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
            pygame.draw.rect(screen, (30, 34, 55), modal_rect, border_radius=16)
            pygame.draw.rect(screen, ACCENT, modal_rect, 2, border_radius=16)

            result_surf = FONT_RESULT.render(msg, True, msg_color)
            screen.blit(
                result_surf,
                result_surf.get_rect(center=(WIDTH // 2, modal_y + 55)),
            )

            score_text = f"{nickname}: {human_score}  —  Machine: {machine_score}"
            score_surf = FONT_MODAL_LABEL.render(score_text, True, LIGHT_GRAY)
            screen.blit(
                score_surf,
                score_surf.get_rect(center=(WIDTH // 2, modal_y + 105)),
            )

            q_surf = FONT_MODAL_LABEL.render("Do you want to play again?", True, WHITE)
            screen.blit(q_surf, q_surf.get_rect(center=(WIDTH // 2, modal_y + 150)))

            yes_hover = yes_rect.collidepoint(mouse_pos)
            pygame.draw.rect(
                screen,
                WIN_COLOR if yes_hover else (40, 140, 70),
                yes_rect,
                border_radius=10,
            )
            yes_text = FONT_MODAL_BTN.render("Yes", True, WHITE)
            screen.blit(yes_text, yes_text.get_rect(center=yes_rect.center))

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
