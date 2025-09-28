from dataclasses import dataclass
from enum import Enum
from collections import deque
import random

class Turn(Enum):
    LEFT = -1
    STRAIGHT = 0
    RIGHT = 1

class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

class Snake:
    def __init__(self, x, y, direction_idx=1):
        self.body = deque([(x, y)])
        self.direction_idx = direction_idx

    @property
    def head(self):
        return self.body[0]

    @property
    def body_set(self):
        return set(self.body)

    def get_next_head(self, turn):
        new_dir_idx = (self.direction_idx + turn.value) % 4
        dx, dy = DIRECTIONS[new_dir_idx]
        return (self.head[0] + dx, self.head[1] + dy)

    def move(self, turn, grow=False):
        self.direction_idx = (self.direction_idx + turn.value) % 4
        dx, dy = DIRECTIONS[self.direction_idx]
        new_head = (self.head[0] + dx, self.head[1] + dy)

        self.body.appendleft(new_head)
        if not grow:
            self.body.pop()

@dataclass
class GameState:
    width: int
    height: int
    snake: Snake
    food: set
    walls: set
    score: int = 0
    game_over: bool = False

class SnakeGame:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.state = None
        self.reset()

    def reset(self):
        snake = Snake(self.width // 2, self.height // 2)
        self.state = GameState(
            width=self.width,
            height=self.height,
            snake=snake,
            food=set(),
            walls=set(),
        )
        self.spawn_food()

    def move(self, turn):
        if self.state.game_over:
            return False
    
        next_head = self.state.snake.get_next_head(turn)

        if next_head in self.state.walls:
            self.state.game_over = True
            return False

        if not (0 <= next_head[0] < self.width and 0 <= next_head[1] < self.height):
            self.state.game_over = True
            return False

        body_without_tail = list(self.state.snake.body)[:-1]
        if next_head in body_without_tail:
            self.state.game_over = True
            return False

        will_eat = next_head in self.state.food

        self.state.snake.move(turn, grow=will_eat)

        if will_eat:
            self.state.food.remove(next_head)
            self.state.score += 10
            self.spawn_food()

        return True

    def spawn_food(self):
        empty = self.get_empty_cells()
        if empty:
            self.state.food.add(random.choice(list(empty)))
    
    def spawn_wall(self, x, y):
        self.state.walls.add((x, y))
    
    def get_empty_cells(self):
        all_cells = {(x, y) for x in range(self.width) for y in range(self.height)}
        occupied = self.state.snake.body_set | self.state.walls | self.state.food
        return all_cells - occupied

if __name__ == "__main__":
    game = SnakeGame(15, 10)
    
    for i in range(5):
        game.spawn_wall(7, i)
    
    moves = [Turn.STRAIGHT] * 3 + [Turn.RIGHT] + [Turn.STRAIGHT] * 2
    
    for move in moves:
        game.render()
        if not game.move(move):
            break
    
    game.render()