from snake.logic import SnakeGame, Turn
from snake.render import SnakeRenderer
import random

game = SnakeGame(width=10, height=10)
render = SnakeRenderer(moves_per_second=10)

while render.is_window_open():
    if not game.state.game_over:
        # ========= YOUR AI CODE HERE =========
        
        # state to use for your AI
        state = game.state
        
        turn = random.choice(list(Turn))
        
        # make a move
        game.move(turn)

        # ====================================
        
        # render the game (adds state to buffer and displays one frame)
        render.render(game.state)
    else:
        render.update()
        
        if render.should_restart():
            game.reset()
            render.clear_buffer()
        
        if render.should_quit():
            break

render.close()