import pygame

from connect4.constants import WIDTH, HEIGHT
from connect4.environment import Connect4Environment
from connect4.ui import BoardUI


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    board_ui = BoardUI()
    environment = Connect4Environment()

    while True:
        board_ui.show_board(environment, screen)
