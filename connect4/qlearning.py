# Agente de Q-learning

import random
from typing import Optional

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

    def choose_action(self, state: tuple[int, int]) -> Optional[str]:
        p_actions = self.env.get_possible_actions(state)
        if p_actions:
            return (
                random.choice(p_actions)
                if random.random() < self.epsilon
                else self.best_action(state)
            )
        else:
            return None

    def update_values(
        self,
        state: tuple[int, int],
        action: str,
        next_state: tuple[int, int],
        reward: int,
    ) -> None:
        q_sa = self.get_value(state, action)
        max_q_next_state = max(
            [
                self.get_value(next_state, ac)
                for ac in self.env.get_possible_actions(next_state)
            ]
        )
        val_q_sa = ((1 - self.alpha) * q_sa) + self.alpha * (
            reward + (self.gamma * max_q_next_state)
        )
        self.qtable[(state, action)] = val_q_sa

    def best_action(self, state: tuple[int, int]) -> str:
        p_actions = {
            a: self.get_value(state, a) for a in self.env.get_possible_actions(state)
        }
        return max(p_actions, key=p_actions.get) if p_actions else ""

    def step(self, action: str) -> tuple[tuple[int, int], int, bool, str]:
        next_state, reward = self.env.do_action(action)
        terminal = self.env.is_terminal(next_state)
        des = f"{action} - {next_state}  - {reward}"

        return next_state, reward, terminal, des

    def run(self, episodes: int) -> dict[tuple[int, str], float]:
        for episode in range(1, episodes + 1):
            # print('episode', episode)
            self.env.reset()
            state = self.env.get_current_state()
            action = self.choose_action(state)
            done = False
            while not done:
                next_state, reward = self.env.do_action(action)
                next_action = self.choose_action(next_state)
                self.update_values(state, action, next_state, reward)
                state, action = next_state, next_action
                done = self.env.is_terminal(next_state)

            if episode % 100 == 0:
                if self.epsilon > 0.01:
                    self.epsilon -= self.epsilon * 0.1

        return self.qtable

    # def test_performance(self) -> tuple[dict, dict]:
    #     actions = {}
    #     values = {}
    #     for i in range(self.env.nrows):
    #         for j in range(self.env.ncols):
    #             if not self.env.is_terminal((i, j)):
    #                 action = self.best_action((i, j))
    #                 actions[(i, j)] = action
    #                 values[(i, j)] = self.get_value((i, j), action)
    #     return actions, values
