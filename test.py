from snake.logic import SnakeGame

from myAI import myAI

game = SnakeGame(width=10, height=10)

n_runs = 100

for i in range(n_runs):
    game.reset()

    move = 0
    while not game.state.game_over:
        state = game.state
        turn = myAI(state)
        game.move(turn)
        move += 1

        if move >= 10000:
            break
    
    print(f"Run {i+1}: Score = {game.state.score}")