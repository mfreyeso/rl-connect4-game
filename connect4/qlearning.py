# Agente de Q-learning

import random
from typing import Optional

import numpy as np

from environment import Connect4Environment


class QLearning:
    def __init__(self, env: Connect4Environment, epsilon=0.9, gamma=0.9, alpha=0.5):
        self.env = env
        self.epsilon = epsilon
        self.gamma = gamma
        self.alpha = alpha
        self.qtable = {}

    def get_value(self, state: tuple[int, int], action: str) -> float:
        return self.qtable[(state, action)] if (state, action) in self.qtable else 0

    def choose_action(self, state: tuple[int, int], piece: int) -> Optional[str]:
        p_actions = self.env.get_possible_actions(piece)
        if p_actions:
            return (
                random.choice(p_actions)
                if random.random() < self.epsilon
                else self.best_action(state, piece)
            )
        else:
            return None

    def update_values(
        self,
        state: tuple[int, int],
        action: str,
        next_state: tuple[int, int],
        reward: int,
        piece: int,
    ) -> None:
        if piece == 1:
            q_sa = self.get_value(state, action)
            max_q_next_state = max(
                [
                    self.get_value(next_state, ac)
                    for ac in self.env.get_possible_actions(piece)
                ]
            )
            val_q_sa = ((1 - self.alpha) * q_sa) + self.alpha * (
                reward + (self.gamma * max_q_next_state)
            )
            self.qtable[(state, action)] = val_q_sa

    def best_action(self, state: tuple[int, int], piece: int) -> str:
        p_actions = {
            a: self.get_value(state, a) for a in self.env.get_possible_actions(piece)
        }
        return max(p_actions, key=p_actions.get) if p_actions else ""

    def run(self, episodes: int) -> dict[tuple[int, str], float]:
        for episode in range(1, episodes + 1):
            print("episode", episode)
            print("epsilon", self.epsilon)

            self.env.reset()
            player = random.randint(1, 2)

            state = self.env.get_current_state()
            action = self.choose_action(state, player)

            done = False
            while not done:
                next_state, reward = self.env.do_action(action, player)

                player = 2 if player == 1 else 1

                next_action = self.choose_action(next_state, player)
                self.update_values(state, action, next_state, reward, player)

                state, action = next_state, next_action
                done = self.env.is_terminal(player)

            if episode % 100 == 0:
                if self.epsilon > 0.01:
                    self.epsilon -= self.epsilon * 0.1

            win = self.env.is_winning_move(player)

            if win:
                print(f"Player {player} Wins!")
            else:
                print(f"Draw!")

            # print(np.flipud(self.env.board))
            # breakpoint()

            # enable above two lines to track final table

        return self.qtable
