from snake.logic import SnakeGame, Turn
from snake.render import SnakeRenderer
import random

game = SnakeGame(width=10, height=10)
render = SnakeRenderer(moves_per_second=10)

def simple_ai(state):
    """
    Simple AI that:
    1. Avoids immediate death (walls, body, boundaries)
    2. Moves towards the closest food
    """
    snake = state.snake
    
    # Get all possible moves and check which are safe
    safe_moves = []
    for turn in [Turn.LEFT, Turn.STRAIGHT, Turn.RIGHT]:
        next_head = snake.get_next_head(turn)
        x, y = next_head
        
        # Check if move is safe
        if (0 <= x < state.width and 
            0 <= y < state.height and
            next_head not in state.walls and
            next_head not in list(snake.body)[:-1]):  # Exclude tail (it will move)
            safe_moves.append(turn)
    
    # If no safe moves, just go straight (we're dead anyway)
    if not safe_moves:
        return Turn.STRAIGHT
    
    # If only one safe move, take it
    if len(safe_moves) == 1:
        return safe_moves[0]
    
    # Multiple safe moves - pick the one closest to food
    if state.food:
        food_pos = list(state.food)[0]  # Get closest food
        best_move = safe_moves[0]
        best_distance = float('inf')
        
        for turn in safe_moves:
            next_head = snake.get_next_head(turn)
            # Manhattan distance to food
            distance = abs(next_head[0] - food_pos[0]) + abs(next_head[1] - food_pos[1])
            if distance < best_distance:
                best_distance = distance
                best_move = turn
        
        return best_move
    
    # No food? Just pick a random safe move
    return random.choice(safe_moves)

from snake.logic import SnakeGame, Turn
from snake.render import SnakeRenderer
import random

game = SnakeGame(width=10, height=10)
# moves_per_second controls game speed (independent of render FPS)
render = SnakeRenderer(moves_per_second=10)

while render.is_window_open():
    if render.should_restart():
        game.reset()
        render.clear_buffer()
    
    if render.should_quit():
        break
    
    if not game.state.game_over:        
        # state to use for your AI
        state = game.state
        
        # make a move
        turn = simple_ai(state)
        game.move(turn)
        
        # render the game
        render.render(game.state)
    else:
        render.update()

render.close()