from snake.logic import SnakeGame, Turn
from snake.visualiser import Visualiser

game = SnakeGame(width=10, height=10)

def controller():
    state = game.state
    snake = state.snake
    head = snake.body[0]
    dirs = [(0,-1),(1,0),(0,1),(-1,0)]  # up,right,down,left
    grid_w, grid_h = state.width, state.height

    # compute candidate turns
    candidates = [Turn.STRAIGHT, Turn.LEFT, Turn.RIGHT]
    valid = []
    for turn in candidates:
        if turn == Turn.STRAIGHT:
            new_dir = snake.direction
        elif turn == Turn.LEFT:
            new_dir = (snake.direction - 1) % 4
        else:
            new_dir = (snake.direction + 1) % 4

        dx, dy = dirs[new_dir]
        # NOTE: your SnakeGame does NOT wrap; don't modulo here or you'll pick OOB moves.
        next_pos = (head[0] + dx, head[1] + dy)

        # reject walls, body (except tail), and out-of-bounds to match game.move rules
        body_wo_tail = list(snake.body)[:-1]
        if (0 <= next_pos[0] < grid_w and 0 <= next_pos[1] < grid_h and
            next_pos not in state.walls and next_pos not in body_wo_tail):
            valid.append((turn, next_pos))

    # choose move
    if valid:
        if state.food:
            target = next(iter(state.food))
            best = min(valid, key=lambda m: abs(m[1][0]-target[0]) + abs(m[1][1]-target[1]))
            return best[0]
        return valid[0][0]
    return Turn.STRAIGHT

viz = Visualiser(game, logic_fps=5, render_fps=60, controller=controller)

while viz.is_running():
    viz.update()

viz.close()
