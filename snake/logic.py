from dataclasses import dataclass
from enum import Enum
from collections import deque
import random


# the possible moves for a snake
class Turn(Enum):
    LEFT = -1
    STRAIGHT = 0
    RIGHT = 1


# the cardinal directions, indexes DIRECTIONS
class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


class Snake:
    def __init__(self, x, y, id, direction=1):
        self.score = 0
        self.isAlive = True
        self.body = deque([(x, y)])
        self.direction = direction
        self.id = id

    @property
    def head(self):
        return self.body[0]

    @property
    def body_set(self):
        return set(self.body)

    # gets the next position of the head if we took a given turn
    def get_next_head(self, turn):
        new_dir_idx = (self.direction + turn.value) % 4
        dx, dy = DIRECTIONS[new_dir_idx]
        return (self.head[0] + dx, self.head[1] + dy)

    # moves the snake, growing if needed
    def move(self, turn, grow=False):
        self.direction = (self.direction + turn.value) % 4
        dx, dy = DIRECTIONS[self.direction]
        new_head = (self.head[0] + dx, self.head[1] + dy)

        self.body.appendleft(new_head)
        if not grow:
            self.body.pop()


# the state passed to the user for their AI
@dataclass
class GameState:
    width: int
    height: int
    snake: Snake
    enemies: list[Snake]
    food: set
    walls: set
    score: int


class SnakeGame:
    def __init__(self, width=10, height=10, num_enemies=1, num_food=5, max_moves=1000):
        self.width = width
        self.height = height
        self.num_enemies = num_enemies
        self.num_food = num_food
        self.max_moves = max_moves
        self.moves = 0
        self.reset()  # in case people dont!

    # resets all snake game state
    def reset(self):
        self.game_over = False
        self.moves = 0
        self.snakes = []
        self.food = set()
        self.walls = set()

        for _ in range(self.num_food):
            self.spawn_food()

        for i in range(self.num_enemies + 1):
            pos = random.choice(list(self.get_empty_cells()))
            self.snakes.append(
                Snake(pos[0], pos[1], id=i, direction=random.randint(0, 3))
            )

        self.invalid_wall_cache = set()

    # checks if the game is over
    def isGameOver(self):
        return self.game_over

    # returns a game state from the perspective of a give snake
    def getGameState(self, snake_idx):
        return GameState(
            width=self.width,
            height=self.height,
            snake=self.snakes[snake_idx],
            enemies=[
                s for s in self.snakes if s != self.snakes[snake_idx] and s.isAlive
            ],
            food=self.food,
            walls=self.walls,
            score=self.snakes[snake_idx].score,
        )

    # moves a given snake
    def move_snake(self, snake_idx, turn):
        moved = self._move_snake(self.snakes[snake_idx], turn)
        self.snakes[snake_idx].isAlive = moved

        if snake_idx == 0:
            self.game_over = not moved

            self.moves += 1
            if self.moves >= self.max_moves:
                self.game_over = True

            return moved

        if not moved:
            for pos in list(self.snakes[snake_idx].body):
                self.food.add(pos)

        return moved

    # returns true if move successful, false if game over
    def _move_snake(self, snake: Snake, turn):
        next_head = snake.get_next_head(turn)

        if next_head in self.walls:
            return False

        if not (0 <= next_head[0] < self.width and 0 <= next_head[1] < self.height):
            return False

        # checks if we would collide with self
        # note that we disclude the tail as this will move
        body_without_tail = list(snake.body)[:-1]
        if next_head in body_without_tail:
            return False

        # checks collisions with all other snakes (both player and enemies)
        all_other_bodies = set()

        # adds player snake if we're not moving the player
        if snake is not self.snakes[0]:
            all_other_bodies |= self.snakes[0].body_set

        # adds all enemy snakes except the one we're moving
        for other_snake in self.snakes[1:]:
            if other_snake.isAlive:
                if other_snake is snake:
                    continue
                all_other_bodies |= other_snake.body_set

        if next_head in all_other_bodies:
            return False

        # checks if we're moving into an apple
        will_eat = next_head in self.food

        # moves the snake, telling it whether to grow or not
        snake.move(turn, grow=will_eat)

        # spawns a new food and wall
        if will_eat:
            self.food.remove(next_head)
            if len(self.food) < self.num_food:
                self.spawn_food()
            snake.score += 1

            self.spawn_wall()

        return True

    # spawns an apple at a random unoccupied cell
    def spawn_food(self):
        empty = self.get_empty_cells()
        if empty:
            self.food.add(random.choice(list(empty)))

    # spawns a wall at a random unoccupied cell
    # considers some simple rules to avoid blocking the grid
    def spawn_wall(self):
        if len(self.walls) >= self.width * self.height * 0.25:
            return

        candidates = self.get_empty_cells() - self.invalid_wall_cache
        if not candidates:
            return

        pos = random.choice(list(candidates))
        self.walls.add(pos)

        # helpers
        neighbors = lambda p: [(p[0] + d[0], p[1] + d[1]) for d in DIRECTIONS]
        in_bounds = lambda p: 0 <= p[0] < self.width and 0 <= p[1] < self.height

        # checks if any adjacent cell would have 3+ walls
        for n in neighbors(pos):
            if in_bounds(n) and n not in self.walls:
                wall_count = sum(
                    1 for nn in neighbors(n) if nn in self.walls or not in_bounds(nn)
                )
                if wall_count >= 3:
                    self.walls.remove(pos)
                    self.invalid_wall_cache.add(pos)
                    return

        # finds connected wall cluster
        cluster = {pos}
        queue = deque([pos])
        while queue:
            p = queue.popleft()
            for dx, dy in [
                (0, 1),
                (0, -1),
                (1, 0),
                (-1, 0),
                (1, 1),
                (1, -1),
                (-1, 1),
                (-1, -1),
            ]:
                np = (p[0] + dx, p[1] + dy)
                if np in self.walls and np not in cluster:
                    cluster.add(np)
                    queue.append(np)

        # checks border touches
        borders = set()
        for x, y in cluster:
            if x == 0:
                borders.add("L")
            if x == self.width - 1:
                borders.add("R")
            if y == 0:
                borders.add("T")
            if y == self.height - 1:
                borders.add("B")

        # invalid if touches 2+ borders
        if len(borders) >= 2:
            self.walls.remove(pos)
            self.invalid_wall_cache.add(pos)
            return

        # adds buffer zone around border-touching clusters
        if borders:
            for wx, wy in cluster:
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if abs(dx) + abs(dy) <= 2:
                            p = (wx + dx, wy + dy)
                            if in_bounds(p) and p not in self.walls:
                                self.invalid_wall_cache.add(p)

            # checks for nearby border walls not in cluster
            for wx, wy in cluster:
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if dx == dy == 0:
                            continue
                        p = (wx + dx, wy + dy)
                        if p in self.walls and p not in cluster:
                            if p[0] in [0, self.width - 1] or p[1] in [
                                0,
                                self.height - 1,
                            ]:
                                self.walls.remove(pos)
                                self.invalid_wall_cache.add(pos)
                                return

        # checks if wall has 3+ neighbors
        if len(self.walls) > 4:
            if sum(1 for n in neighbors(pos) if n in self.walls) >= 3:
                self.walls.remove(pos)
                self.invalid_wall_cache.add(pos)

    # gets all the empty cells in the grid
    def get_empty_cells(self):
        all_cells = {(x, y) for x in range(self.width) for y in range(self.height)}
        occupied = self.walls | self.food
        for s in self.snakes:
            if s.isAlive:
                occupied |= s.body_set
        return all_cells - occupied
