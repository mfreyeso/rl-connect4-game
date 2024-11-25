import math
import random

import numpy as np
import pygame
import sys

from connect4.constants import N_COLS, N_ROWS, SQUARE_SIZE, HEIGHT, WIDTH
from connect4.environment import Connect4Environment

BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
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

        human = random.randint(0, 1)
        machine = int(not human)

        machine_pos = machine + 1
        human_pos = human + 1

        print(f"Human is Player {human_pos}")
        print(f"Machine is Player {machine_pos}")
        print(f"Starts Player {env.turn + 1}")

        while not env.finished:
            for event in pygame.event.get():
                # Configurando el cierre de la ventana para que el programa no cierre inesperadamente
                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEMOTION:
                    if env.turn != machine:
                        pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, SQUARE_SIZE))
                        posx = event.pos[0]
                        if env.turn == 0:
                            pygame.draw.circle(
                                screen, YELLOW, (posx, int(SQUARE_SIZE / 2)), RADIUS
                            )
                        else:
                            pygame.draw.circle(
                                screen, GREEN, (posx, int(SQUARE_SIZE / 2)), RADIUS
                            )

                pygame.display.update()

                if env.turn == machine:
                    row, col = env.get_next_agent_step(qtable)
                    print(row, col)
                    env.drop_piece(row, col, machine_pos)

                    if env.is_winning_move(machine_pos):
                        label = MY_FONT.render(
                            f"Player {machine_pos} wins!!!",
                            1,
                            PLAYER_COLORS[machine_pos],
                        )
                        screen.blit(label, (40, 10))
                        env.finished = True

                    turn += 1  # se incrementa en uno el turno
                    env.turn = turn % 2  # alternando entre cero y uno

                    print(np.flipud(env.board))
                    self.draw_board(env.board, screen)

                    pygame.display.update()

                    if env.finished:
                        pygame.time.wait(1500)

                    continue

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

                    turn += 1  # se incrementa en uno el turno
                    env.turn = turn % 2  # alternando entre cero y uno

                    print(np.flipud(env.board))
                    self.draw_board(env.board, screen)

                    pygame.display.update()

                    if env.finished:
                        pygame.time.wait(1500)
