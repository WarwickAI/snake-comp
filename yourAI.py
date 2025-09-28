"""

TODO:

Software Improvements:
- implement random wall spawning on eating food

User Side:
- Readme with instructions
- example bot 
- comments and docstrings?


"""

from snake.logic import SnakeGame, Turn
from snake.visualiser import Visualiser

game = SnakeGame(width=20, height=15)
viz = Visualiser(game, fps=5)

while viz.is_running():
    if game.state.game_over:
        viz.update()
        continue

    state = game.state

    # ai code innit

    game.move(Turn.STRAIGHT)
    viz.update()

viz.close()
