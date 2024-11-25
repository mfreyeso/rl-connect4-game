import pickle

from environment import Connect4Environment
from qlearning import QLearning


def save_q_table(table):
    with open("q_table.pkl", "wb") as f:  # open a text file
        pickle.dump(table, f)


def load_q_table(file_reference: str) -> dict[tuple[int, str], float]:
    with open(file_reference, "rb") as f:
        table = pickle.load(f)

    return table


def train_agent():
    environment = Connect4Environment()
    q_train = QLearning(environment, 0.9, 1, 0.6)

    table = q_train.run(10000)
    save_q_table(table)


if __name__ == "__main__":
    train_agent()
