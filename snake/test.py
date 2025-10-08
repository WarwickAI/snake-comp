from tqdm import tqdm

from snake.logic import SnakeGame
from snake.render import SnakeRenderer

from myAI import myAI
from examples.smartAI import smartAI as enemyAI


def run_no_viz(cfg):
    game = SnakeGame(
        width=cfg["width"],
        height=cfg["height"],
        num_enemies=cfg["num_enemies"],
        max_moves=cfg["max_moves"],
        num_food=cfg["num_food"],
    )

    while not game.game_over:
        for i in range(len(game.snakes)):
            if game.snakes[i].isAlive:
                state = game.getGameState(i)
                turn = myAI(state) if i == 0 else enemyAI(state)
                game.move_snake(i, turn)

    return game.snakes[0].score


def test(n, difficulty, DIFFICULTIES):
    scores = []
    with tqdm(total=n, desc=f"Testing {difficulty}", unit="game") as pbar:
        for i in range(n):
            score = run_no_viz(DIFFICULTIES[difficulty])
            scores.append(score)
            pbar.set_postfix({"last": score, "avg": f"{sum(scores)/len(scores):.1f}"})
            pbar.update(1)

    avg = sum(scores) / len(scores)
    print(f"\nResults:")
    print(f"  Games: {len(scores)}")
    print(f"  Average: {avg:.1f}")
    print(f"  Min/Max: {min(scores)}/{max(scores)}")
    return avg


def test_all(n, DIFFICULTIES):
    """Test all difficulty levels"""
    results = {}
    print(f"\nTesting all difficulties ({n} games each)")
    print("=" * 40)

    for diff in DIFFICULTIES:
        results[diff] = test(n, diff, DIFFICULTIES)
        print("")

    print("\n" + "=" * 40)
    print("SUMMARY:")
    for diff, avg in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"  {diff:<12} {avg:.1f}")

    final_score = (
        (results["easy"] + results["medium"] + results["hard"] + results["chaos"]) / 4
    )
    print("")
    print(f"  Average Score: {final_score:.1f}")
    print("=" * 40)

    return results
