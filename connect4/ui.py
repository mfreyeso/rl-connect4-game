import math
import sys

import numpy as np
import pygame

from connect4.constants import N_COLS, N_ROWS, SQUARE_SIZE, HEIGHT, WIDTH
from connect4.environment import Connect4Environment

BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

PLAYER_COLORS = {1: YELLOW, 2: GREEN}

RADIUS = int(SQUARE_SIZE / 2 - 5)

pygame.font.init()
MY_FONT = pygame.font.SysFont("monospace", 75)


class BoardUI:
    @staticmethod
    def draw_board(board, screen):
        for c in range(N_COLS):
            for r in range(N_ROWS):
                pygame.draw.rect(
                    screen,
                    BLUE,
                    (
                        c * SQUARE_SIZE,
                        r * SQUARE_SIZE + SQUARE_SIZE,
                        SQUARE_SIZE,
                        SQUARE_SIZE,
                    ),
                )
                pygame.draw.circle(
                    screen,
                    BLACK,
                    (
                        int(c * SQUARE_SIZE + SQUARE_SIZE / 2),
                        int(r * SQUARE_SIZE + SQUARE_SIZE + SQUARE_SIZE / 2),
                    ),
                    RADIUS,
                )

        for c in range(N_COLS):
            for r in range(N_ROWS):
                if board[r][c] == 1:
                    pygame.draw.circle(
                        screen,
                        YELLOW,
                        (
                            int(c * SQUARE_SIZE + SQUARE_SIZE / 2),
                            (HEIGHT + SQUARE_SIZE)
                            - int(r * SQUARE_SIZE + SQUARE_SIZE + SQUARE_SIZE / 2),
                        ),
                        RADIUS,
                    )
                elif board[r][c] == 2:
                    pygame.draw.circle(
                        screen,
                        GREEN,
                        (
                            int(c * SQUARE_SIZE + SQUARE_SIZE / 2),
                            (HEIGHT + SQUARE_SIZE)
                            - int(r * SQUARE_SIZE + SQUARE_SIZE + SQUARE_SIZE / 2),
                        ),
                        RADIUS,
                    )

        pygame.display.update()

    def show_board(self, env: Connect4Environment, screen, qtable):
        self.draw_board(env.board, screen)
        turn = env.turn

        # Agent always trained as piece 1
        machine_pos = 1
        human_pos = 2

        print(f"Human is Player {human_pos}")
        print(f"Machine is Player {machine_pos}")
        print(f"Starts Player {env.turn + 1}")

        while not env.finished:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEMOTION:
                    if env.turn != 0:  # human is turn 1
                        pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, SQUARE_SIZE))
                        posx = event.pos[0]
                        pygame.draw.circle(
                            screen,
                            PLAYER_COLORS[human_pos],
                            (posx, int(SQUARE_SIZE / 2)),
                            RADIUS,
                        )

                pygame.display.update()

                # Machine turn (turn == 0, piece 1)
                if env.turn == 0:
                    valid_cols = env.get_valid_columns()

                    if not valid_cols:
                        label = MY_FONT.render("Draw!", 1, WHITE)
                        screen.blit(label, (40, 10))
                        env.finished = True
                        continue

                    best_col = env.choose_column(machine_pos, qtable)

                    row = env.get_next_open_row(best_col)
                    env.drop_piece(row, best_col, machine_pos)

                    if env.is_winning_move(machine_pos):
                        label = MY_FONT.render(
                            f"Player {machine_pos} wins!!!",
                            1,
                            PLAYER_COLORS[machine_pos],
                        )
                        screen.blit(label, (40, 10))
                        env.finished = True

                    if not env.get_valid_columns() and not env.finished:
                        label = MY_FONT.render("Draw!", 1, WHITE)
                        screen.blit(label, (40, 10))
                        env.finished = True

                    turn += 1
                    env.turn = turn % 2

                    print(np.flipud(env.board))
                    self.draw_board(env.board, screen)
                    pygame.display.update()

                    if env.finished:
                        pygame.time.wait(1500)

                    continue

                # Human turn (turn == 1, piece 2)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, SQUARE_SIZE))
                    posx = event.pos[0]
                    col = int(math.floor(posx / SQUARE_SIZE))

                    if env.is_valid_location(col):
                        row = env.get_next_open_row(col)
                        env.drop_piece(row, col, human_pos)

                        if env.is_winning_move(human_pos):
                            label = MY_FONT.render(
                                f"Player {human_pos} wins!!!",
                                1,
                                PLAYER_COLORS[human_pos],
                            )
                            screen.blit(label, (40, 10))
                            env.finished = True

                        if not env.get_valid_columns() and not env.finished:
                            label = MY_FONT.render("Draw!", 1, WHITE)
                            screen.blit(label, (40, 10))
                            env.finished = True

                    turn += 1
                    env.turn = turn % 2

                    print(np.flipud(env.board))
                    self.draw_board(env.board, screen)
                    pygame.display.update()

                    if env.finished:
                        pygame.time.wait(1500)
