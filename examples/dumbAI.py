import random
from collections import deque
from snake.logic import GameState, Turn


def dumbAI(state: GameState) -> Turn:
    return random.choice(list(Turn))
