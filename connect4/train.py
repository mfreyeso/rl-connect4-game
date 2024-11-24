import pickle

from connect4.environment import Connect4Environment
from connect4.qlearning import QLearning


def save_q_table(q_table):
    with open('q_table.pkl', 'wb') as f:  # open a text file
        pickle.dump(q_table, f)


def load_q_table(file_reference: str) -> dict[tuple[int, str], float]:
    with open(file_reference, "rb") as f:
        q_table = pickle.load(f)

    return q_table

def train_agent():
    environment = Connect4Environment()
    q_train = QLearning(environment, 0.9, 1, 0.6)
    q_table = q_train.run(1)

    save_q_table(q_table)
