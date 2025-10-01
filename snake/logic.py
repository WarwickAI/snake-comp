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
    def __init__(self, x, y, direction=1):
        self.body = deque([(x, y)])
        self.direction = direction

    @property
    def head(self):
        return self.body[0]

    @property
    def body_set(self):
        return set(self.body)

    def get_next_head(self, turn):
        new_dir_idx = (self.direction + turn.value) % 4
        dx, dy = DIRECTIONS[new_dir_idx]
        return (self.head[0] + dx, self.head[1] + dy)

    def move(self, turn, grow=False):
        self.direction = (self.direction + turn.value) % 4
        dx, dy = DIRECTIONS[self.direction]
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
        self.reset() # in case people dont!

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
            self.spawn_food()
            self.state.score += 1
            
            self.spawn_wall()

        return True

    def spawn_food(self):
        empty = self.get_empty_cells()
        if empty:
            self.state.food.add(random.choice(list(empty)))
    
    def spawn_wall(self):
        empty = self.get_empty_cells()
        if empty:
            self.state.walls.add(random.choice(list(empty)))
    
    def get_empty_cells(self):
        all_cells = {(x, y) for x in range(self.width) for y in range(self.height)}
        occupied = self.state.snake.body_set | self.state.walls | self.state.food
        return all_cells - occupied
    
    def render(self):
        grid = [['.' for _ in range(self.width)] for _ in range(self.height)]
        for (x, y) in self.state.walls:
            grid[y][x] = '#'
        for (x, y) in self.state.food:
            grid[y][x] = '*'
        for i, (x, y) in enumerate(self.state.snake.body):
            grid[y][x] = 'O' if i == 0 else 'o'
        
        top_border = '┌' + '─' * self.width + '┐'
        bottom_border = '└' + '─' * self.width + '┘'
        rows = [top_border]
        rows.extend('│' + ''.join(row) + '│' for row in grid)
        rows.append(bottom_border)
        
        print('\n'.join(rows))