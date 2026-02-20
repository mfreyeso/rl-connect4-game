import random

from connect4.constants import REWARD_LOSE, REWARD_DRAW, REWARD_STEP
from connect4.environment import Connect4Environment


class QLearning:
    def __init__(self, env: Connect4Environment, epsilon=0.9, gamma=0.9, alpha=0.5):
        self.env = env
        self.epsilon = epsilon
        self.gamma = gamma
        self.alpha = alpha
        self.qtable = {}

    def get_value(self, state: tuple, action: int) -> float:
        return self.qtable.get((state, action), 0.0)

    def choose_action(self, state: tuple, valid_columns: list[int]) -> int:
        if random.random() < self.epsilon:
            return random.choice(valid_columns)
        return self.best_action(state, valid_columns)

    def best_action(self, state: tuple, valid_columns: list[int]) -> int:
        q_vals = {col: self.get_value(state, col) for col in valid_columns}
        return max(q_vals, key=lambda c: q_vals[c])

    def update_values(
        self,
        state: tuple,
        action: int,
        next_state: tuple,
        reward: float,
        next_valid_cols: list[int],
    ) -> None:
        q_sa = self.get_value(state, action)
        max_q_next = (
            max(self.get_value(next_state, c) for c in next_valid_cols)
            if next_valid_cols
            else 0.0
        )
        new_q = (1 - self.alpha) * q_sa + self.alpha * (
            reward + self.gamma * max_q_next
        )
        self.qtable[(state, action)] = new_q

    def run(self, episodes: int) -> dict:
        agent_piece = 1
        opponent_piece = 2

        for episode in range(1, episodes + 1):
            self.env.reset()

            # Randomly decide who goes first
            if random.random() < 0.5:
                opp_col = random.choice(self.env.get_valid_columns())
                self.env.step(opp_col, opponent_piece)

            state = self.env.get_state()
            done = False

            while not done:
                valid_cols = self.env.get_valid_columns()
                if not valid_cols:
                    break

                action = self.choose_action(state, valid_cols)
                next_state, reward, done = self.env.step(action, agent_piece)

                if done:
                    self.update_values(state, action, next_state, reward, [])
                    break

                # Opponent plays randomly
                opp_cols = self.env.get_valid_columns()
                if not opp_cols:
                    self.update_values(state, action, next_state, REWARD_DRAW, [])
                    break

                opp_col = random.choice(opp_cols)
                next_state_after_opp, _, done = self.env.step(opp_col, opponent_piece)

                if done:
                    self.update_values(
                        state, action, next_state_after_opp, REWARD_LOSE, []
                    )
                    break

                next_valid = self.env.get_valid_columns()
                self.update_values(
                    state, action, next_state_after_opp, REWARD_STEP, next_valid
                )
                state = next_state_after_opp

            # Decay epsilon
            if episode % 100 == 0 and self.epsilon > 0.05:
                self.epsilon *= 0.95

            if episode % 1000 == 0:
                print(f"Episode {episode} | epsilon={self.epsilon:.4f}")

        return self.qtable
