from snake.logic import SnakeGame
from snake.render import SnakeRenderer

from myAI import myAI
from examples.smartAI import smartAI as enemyAI


def run(cfg):
    # creates a new snake game
    game = SnakeGame(
        width=cfg["width"],
        height=cfg["height"],
        num_enemies=cfg["num_enemies"],
        max_moves=cfg["max_moves"],
        num_food=cfg["num_food"],
    )

    # creates a new snake renderer
    render = SnakeRenderer(moves_per_second=cfg["moves_per_second"])

    # main loop runs whilst the main window is open
    while render.is_window_open():

        # handles reset input
        if render.should_restart():
            game.reset()
            render.reset()

        # if the game is not over
        if not game.game_over:

            # moves all the snakes one by one
            # note that the player's snake is at index 0
            for i in range(len(game.snakes)):
                if game.snakes[i].isAlive:
                    state = game.getGameState(i)
                    turn = myAI(state) if i == 0 else enemyAI(state)
                    game.move_snake(i, turn)

            # gives the processed frame to the renered
            render.push(game.getGameState(0))

        # updates the renderer
        render.update()

    print(f"Final score: {game.snakes[0].score}")
