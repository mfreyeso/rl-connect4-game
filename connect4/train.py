import argparse
import pickle

from connect4.environment import Connect4Environment
from connect4.qlearning import QLearning


def save_q_table(table):
    with open("q_table.pkl", "wb") as f:
        pickle.dump(table, f)


def load_q_table(file_reference: str) -> dict:
    with open(file_reference, "rb") as f:
        table = pickle.load(f)

    return table


def train_agent(episodes: int):
    environment = Connect4Environment()
    q_train = QLearning(environment, epsilon=1.0, gamma=0.95, alpha=0.1)

    table = q_train.run(episodes)
    save_q_table(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=50000)
    args = parser.parse_args()

    train_agent(args.episodes)
