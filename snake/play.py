import sys
import time
from collections import deque
from pathlib import Path

from snake.logic import SnakeGame, Snake, Turn
from snake.render import SnakeRenderer

# the examples import each other by bare module name, so make that work
_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
if str(_EXAMPLES_DIR) not in sys.path:
    sys.path.append(str(_EXAMPLES_DIR))


# AIs that can drive the enemy snakes, keyed by the name used on the CLI.
# Imported lazily so one broken/heavy example does not stop the others.
ENEMY_AIS = {
    "demo": ("examples.demoAI", "demoAI"),
    "my": ("myAI", "myAI"),
    "smart": ("examples.smartAI", "smartAI"),
    "dumb": ("examples.dumbAI", "dumbAI"),
    "simulation": ("examples.simulationAI", "simulationAI"),
    "winner": ("examples.winnerAI", "winnerAI"),
    "rl": ("examples.rlAI", "rlAI"),
}


def load_enemy_ai(name):
    """Import and return the AI function registered under `name`"""
    module_name, func_name = ENEMY_AIS[name]
    try:
        module = __import__(module_name, fromlist=[func_name])
    except ImportError as e:
        raise SystemExit(
            f"Could not load the '{name}' enemy AI ({e}). "
            "If it needs extra packages, install them with `pip install -e .` "
            "after enabling them in pyproject.toml."
        )
    return getattr(module, func_name)


def turn_towards(snake: Snake, direction):
    """Convert an absolute direction (0=up,1=right,2=down,3=left) into a Turn.

    Reversing into yourself is not a legal move, so an opposite direction
    is treated as going straight.
    """
    if direction is None or direction == snake.direction:
        return Turn.STRAIGHT
    if direction == (snake.direction + 1) % 4:
        return Turn.RIGHT
    if direction == (snake.direction - 1) % 4:
        return Turn.LEFT
    return Turn.STRAIGHT


# a human-friendly pace; the AI difficulties run at 10 moves per second
DEFAULT_SPEED = 5

# how fast the AI-only demo runs while waiting for someone to press space
ATTRACT_SPEED = 7.5

# which AI drives the blue snake during the demo (the strongest example)
DEMO_AI = "demo"

# how long the demo lingers on a finished game before starting another (seconds)
ATTRACT_RESTART_DELAY = 1.0

# a demo game is cut off and restarted after this long, so it never runs forever
ATTRACT_TIMEOUT = 60.0

# coyote time: how long a fatal move waits for a saving key press (seconds)
COYOTE_SECONDS = 0.08

# how many key presses can be queued up; each one is played on its own move
INPUT_QUEUE_SIZE = 3

ATTRACT, PLAYER = "attract", "player"


def queue_direction(queue, snake: Snake, direction):
    """Add a key press to the input queue unless it would do nothing.

    A press is measured against where the snake will be heading once the
    queued moves have played, so UP then RIGHT tapped quickly turns twice.
    Repeats and reversals are dropped rather than wasting a move.
    """
    heading = queue[-1] if queue else snake.direction
    if direction == heading or direction == (heading + 2) % 4:
        return
    if len(queue) < INPUT_QUEUE_SIZE:
        queue.append(direction)


def play(cfg, enemy="demo", speed=None, fullscreen=True):
    """Arcade-style loop: AIs play a fast demo until space is pressed, then the
    player takes the blue snake with the arrow keys. Space after losing goes
    back to the demo."""
    demoAI = load_enemy_ai(DEMO_AI)
    enemyAI = load_enemy_ai(enemy)
    player_speed = speed or DEFAULT_SPEED

    game = SnakeGame(
        width=cfg["width"],
        height=cfg["height"],
        num_enemies=cfg["num_enemies"],
        max_moves=cfg["max_moves"],
        num_food=cfg["num_food"],
    )
    render = SnakeRenderer(moves_per_second=ATTRACT_SPEED, fullscreen=fullscreen)
    render.game_over_hint = "R to retry  -  SPACE to watch the AIs"

    mode = ATTRACT
    queue = deque()  # queued player directions
    started = False  # has the player pressed their first key this round
    grace_until = None  # coyote-time deadline, if a fatal move is pending
    attract_restart_at = None  # when the demo should start a fresh game
    attract_started_at = 0.0  # when the current demo game began

    def start_attract():
        nonlocal mode, attract_restart_at, attract_started_at
        mode = ATTRACT
        attract_restart_at = None
        attract_started_at = time.monotonic()
        game.reset()
        render.reset()
        render.set_speed(ATTRACT_SPEED)
        render.show_game_over = False
        render.set_message("AI demo  -  press SPACE to play", corner=True)
        render.push(game.getGameState(0))

    def start_player():
        nonlocal mode, queue, started, grace_until
        mode = PLAYER
        queue = deque()
        started = False
        grace_until = None
        game.reset()
        render.reset()
        render.set_speed(player_speed)
        render.show_game_over = True
        render.set_message("Press an arrow key to start")
        render.push(game.getGameState(0))

    def move_everyone(player_turn=None):
        """Advance the game one move; the blue snake uses player_turn if given"""
        for i in range(len(game.snakes)):
            if not game.snakes[i].isAlive:
                continue
            state = game.getGameState(i)
            if i == 0:
                turn = player_turn if player_turn is not None else demoAI(state)
            else:
                turn = enemyAI(state)
            game.move_snake(i, turn)
        render.push(game.getGameState(0))

    start_attract()

    while render.is_window_open():
        # R restarts the current mode, SPACE switches between them
        if render.should_restart():
            start_player() if mode == PLAYER else start_attract()

        if render.poll_space():
            if mode == ATTRACT:
                start_player()
            elif game.game_over:
                start_attract()

        if mode == ATTRACT:
            now = time.monotonic()
            if now - attract_started_at >= ATTRACT_TIMEOUT:
                start_attract()
                continue
            if game.game_over:
                if attract_restart_at is None:
                    attract_restart_at = now + ATTRACT_RESTART_DELAY
                elif now >= attract_restart_at:
                    start_attract()
                    continue
                render.update()
            elif render.is_idle():
                move_everyone()
            else:
                render.update()
            continue

        # ---- player mode ----

        # queue up key presses so quick taps play out one move at a time
        direction = render.poll_direction()
        if direction is not None:
            if not started:
                started = True
                render.set_message(None)
                # a one-cell snake can head any way, so honour the first key exactly
                game.snakes[0].direction = direction
            else:
                queue_direction(queue, game.snakes[0], direction)

        # step the game once the renderer has finished showing the last move
        if started and not game.game_over and render.is_idle():
            turn = turn_towards(game.snakes[0], queue.popleft() if queue else None)

            # coyote time: if this move would kill the player, hang on the
            # current cell for a moment so a slightly late key press still counts.
            # the fatal press has been dropped, so the next one is tried instead
            if not game.is_safe_move(0, turn):
                now = time.monotonic()
                if grace_until is None:
                    grace_until = now + COYOTE_SECONDS
                if now < grace_until:
                    render.update()
                    continue
            grace_until = None

            move_everyone(player_turn=turn)

            if game.game_over and game.snakes[0].isAlive:
                render.set_message("Out of moves!  R to retry  -  SPACE for AI demo")
        else:
            render.update()

    print(f"Final score: {game.snakes[0].score}")
