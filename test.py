import argparse
from snake.logic import SnakeGame
from snake.render import SnakeRenderer
from myAI import myAI


def run_with_viz():
    game = SnakeGame(width=10, height=10)
    render = SnakeRenderer(moves_per_second=10)
    
    while render.is_window_open():
        if render.should_restart():
            game.reset()
            render.clear_buffer()
        if render.should_quit():
            break
        
        if not game.state.game_over:
            turn = myAI(game.state)
            game.move(turn)
            render.render(game.state)
        else:
            render.update()
    
    render.close()
    print(f"Final score: {game.state.score}")


def run_no_viz():
    game = SnakeGame(width=10, height=10)

    moves = 0

    while not game.state.game_over:
        turn = myAI(game.state)
        game.move(turn)
        moves += 1
        if moves > 1000:
            break

    return game.state.score


def test(n):
    print(f"Running {n} games...")
    scores = []
    
    for i in range(n):
        score = run_no_viz()
        scores.append(score)
        print(f"  Game {i+1}/{n}: {score}")
    
    print(f"\n{'='*40}")
    print(f"Games:   {len(scores)}")
    print(f"Average: {sum(scores)/len(scores):.1f}")
    print(f"Min:     {min(scores)}")
    print(f"Max:     {max(scores)}")
    print(f"{'='*40}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Snake AI Runner')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    subparsers.add_parser('run', help='Run game with visualization')
    
    test_parser = subparsers.add_parser('test', help='Test AI without visualization')
    test_parser.add_argument('n', type=int, help='Number of games to run')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        print("Controls: R=restart, Q=quit")
        run_with_viz()
    elif args.command == 'test':
        test(args.n)
    else:
        parser.print_help()