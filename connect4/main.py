import pygame

from connect4.constants import WIDTH, HEIGHT, WINDOW_TITLE, BG_COLOR
from connect4.environment import Connect4Environment
from connect4.train import load_q_table
from connect4.ui import BoardUI, StartScreen, EndGameModal


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)

    board_ui = BoardUI()
    start_screen = StartScreen()
    end_modal = EndGameModal()
    q_table = load_q_table("q_table.pkl")

    state = "start"
    nickname = ""
    human_score = 0
    machine_score = 0

    while True:
        if state == "start":
            nickname = start_screen.show(screen)
            human_score = 0
            machine_score = 0
            state = "play"

        elif state == "play":
            env = Connect4Environment()
            result = board_ui.show_board(
                env, screen, q_table, nickname, human_score, machine_score
            )
            if result == "human_win":
                human_score += 1
            elif result == "machine_win":
                machine_score += 1
            state = "end"

        elif state == "end":
            play_again = end_modal.show(
                screen, result, nickname, human_score, machine_score
            )
            state = "play" if play_again else "start"
