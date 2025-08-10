import random
from collections import deque
from snake.logic import GameState, Turn


def smartAI(state: GameState) -> Turn:
    # Find safe moves
    safe = []

    enemy_bodies = set()
    for snake in state.enemies:
        enemy_bodies |= snake.body_set

    for turn in list(Turn):
        head = state.snake.get_next_head(turn)
        if (
            0 <= head[0] < state.width
            and 0 <= head[1] < state.height
            and head not in state.walls
            and head not in state.snake.body
            and head not in enemy_bodies
        ):
            safe.append(turn)

    # No safe moves. We're dead anyway.
    if not safe:
        return Turn.STRAIGHT

    # If food exists, try to move toward it
    if state.food:
        food = list(state.food)[0]
        current = state.snake.head

        # Pick first safe move that reduces distance on either axis
        for turn in safe:
            new = state.snake.get_next_head(turn)
            if abs(food[0] - new[0]) < abs(food[0] - current[0]) or abs(
                food[1] - new[1]
            ) < abs(food[1] - current[1]):
                return turn

    # No good move toward food, pick any safe move
    return safe[0]
