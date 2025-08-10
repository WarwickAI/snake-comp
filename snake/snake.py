import argparse
import random
import yaml
import copy
from tqdm import tqdm
from snake.logic import SnakeGame, GameState
from snake.render import SnakeRenderer

from snake.run import run
from snake.test import test, test_all

# loads configurations
with open("snake/difficulties.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

# gets the difficulties, defaulting to medium
DIFFICULTIES = CONFIG["difficulties"]
DEFAULT = CONFIG.get("default_difficulty", "medium")


def list_modes():
    """List all available modes"""
    print("\nAvailable modes:")
    for name, cfg in DIFFICULTIES.items():
        print(
            f"  {name:<12} - {cfg['width']}x{cfg['height']} board, {cfg['num_enemies']} enemies"
        )


def main():
    parser = argparse.ArgumentParser(prog="snake")
    subparsers = parser.add_subparsers(dest="command")

    # snake run [difficulty]
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("difficulty", nargs="?", default=DEFAULT)
    run_parser.add_argument("--seed", type=int)

    # snake test <n> [difficulty]
    test_parser = subparsers.add_parser("test")
    test_parser.add_argument("n", type=int)
    test_parser.add_argument("difficulty", nargs="?", default=DEFAULT)
    test_parser.add_argument("--seed", type=int)

    # snake list
    subparsers.add_parser("list")

    # parses args
    args = parser.parse_args()

    # no args given so provide help
    if args.command is None:
        parser.print_help()
        return

    # Set seed if provided
    if hasattr(args, "seed") and args.seed:
        random.seed(args.seed)

    # user has asked to run a game
    if args.command == "run":
        if args.difficulty not in DIFFICULTIES:
            print(f"Unknown difficulty: {args.difficulty}")
            list_modes()
            return

        print("Controls: R=restart, ESC=quit")
        run(cfg=DIFFICULTIES[args.difficulty])

    # user has asked to test their AI
    elif args.command == "test":
        if args.difficulty == "all":
            test_all(args.n, DIFFICULTIES)

        elif args.difficulty not in DIFFICULTIES:
            print(f"Unknown difficulty: {args.difficulty}")
            list_modes()

        else:
            test(args.n, args.difficulty, DIFFICULTIES)

    # user has asked to list the difficulties
    elif args.command == "list":
        list_modes()


if __name__ == "__main__":
    main()
