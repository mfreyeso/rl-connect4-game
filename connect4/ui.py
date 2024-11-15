import math

import numpy as np
import pygame
import sys

from connect4.constants import N_COLS, N_ROWS, SQUARE_SIZE, HEIGHT, WIDTH

BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

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

    def show_board(self, env, screen):
        self.draw_board(env.board, screen)
        turn = env.turn

        while not env.finished:
            for event in pygame.event.get():
                # Configurando el cierre de la ventana para que el programa no cierre inesperadamente
                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEMOTION:
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

                # solicitando la movida al jugador 1
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, SQUARE_SIZE))
                    # print(event.pos)
                    if env.turn == 0:
                        posx = event.pos[0]
                        col = int(math.floor(posx / SQUARE_SIZE))
                        # col = int(input("Jugador 1 haz tu movida (0,6):"))

                        if env.is_valid_location(col):
                            row = env.get_next_open_row(col)
                            env.drop_piece(row, col, 1)

                            if env.winning_move(1):
                                # print("Player 1 wins!!!")
                                label = MY_FONT.render("Player 1 wins!!!", 1, YELLOW)
                                screen.blit(label, (40, 10))
                                env.finished = True

                    # solicitando la movida al jugador 2
                    else:
                        posx = event.pos[0]
                        col = int(math.floor(posx / SQUARE_SIZE))
                        # col = int(input("Jugador 2 haz tu movida(0,6):"))

                        if env.is_valid_location(col):
                            row = env.get_next_open_row(col)
                            env.drop_piece(row, col, 2)

                            if env.winning_move(2):
                                # print("Player 2 wins!!!")
                                label = MY_FONT.render("Player 2 wins!!!", 1, GREEN)
                                screen.blit(label, (40, 10))
                                env.finished = True

                    print(np.flipud(env.board))
                    self.draw_board(env.board, screen)

                    turn += 1  # se incrementa en uno el turno
                    env.turn = turn % 2  # alternando entre cero y uno

                    if env.finished:
                        pygame.time.wait(1500)
