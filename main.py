from snake.logic import SnakeGame, Turn
from snake.render import SnakeRenderer

from myAI import myAI

game = SnakeGame(width=10, height=10)
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
        turn = myAI(state)
        game.move(turn)
        
        # render the game
        render.render(game.state)
    else:
        render.update()

render.close()