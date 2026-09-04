import random

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from snake.logic import GameState, SnakeGame, Turn
from examples.smartAI import smartAI as enemyAI

"""
This is where your reinforcement learning snake lives.

What you are writing here is a Gymnasium environment - the standard
interface that every RL library speaks. Learn it here and it works
everywhere. Three methods do the work:

    observe()  - what does your snake SEE?
    step()     - take one action, say what happened and what it was worth
    reset()    - start a fresh game

and __init__ declares observation_space, which has to agree with whatever
observe() hands back.

Train it with `snake train easy`.

Leave the plumbing at the bottom of the file alone. It advances the game
exactly the way the competition scorer does, so the game you train
against and the game you are scored on stay identical.
"""


# the three moves, in the order the model sees them
# both training and myAI use this list, so the numbers can never drift apart
ACTIONS = [Turn.LEFT, Turn.STRAIGHT, Turn.RIGHT]


class SnakeEnv(gym.Env):
    """A game of snake, wrapped up so Stable Baselines 3 can learn from it."""

    metadata = {"render_modes": []}

    def __init__(self, cfg):
        super().__init__()

        self.build_game(cfg)

        # three actions: turn left, carry straight on, turn right
        self.action_space = spaces.Discrete(len(ACTIONS))

        # observation_space describes what observe() returns, and the two
        # have to agree - `snake train` checks before it starts.
        # We take the shape from observe() itself so that adding a feature
        # never means editing this line. The -1 to 1 bounds are the part
        # you have to keep to.
        shape = self.observe(self.game.getGameState(0)).shape
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=shape, dtype=np.float32
        )

    @staticmethod
    def observe(state: GameState) -> np.ndarray:
        """
        Turns a GameState into the list of numbers your snake gets to look at.

        Keep every number between -1 and 1. Models learn badly from features
        on wildly different scales, and `snake train` will refuse to start if
        anything falls outside that range.

        It is a @staticmethod because examples/rlAI.py calls it too, when your
        model actually plays - one function for both means they can't disagree.
        """

        snake = state.snake
        head_x, head_y = snake.head

        features = []

        # 1. would each of our three moves kill us? (1.0 = yes)
        for turn in ACTIONS:
            blocked = SnakeEnv.is_blocked(state, snake.get_next_head(turn))
            features.append(1.0 if blocked else 0.0)

        # 2. which way is the nearest food, relative to our head?
        if state.food:
            food_x, food_y = min(
                state.food, key=lambda f: abs(f[0] - head_x) + abs(f[1] - head_y)
            )
            features.append((food_x - head_x) / state.width)
            features.append((food_y - head_y) / state.height)
        else:
            features.extend([0.0, 0.0])

        # 3. which way are we currently facing?
        features.extend(1.0 if snake.direction == d else 0.0 for d in range(4))

        # Add your own features! Or change the above!
        #
        # Some ideas:
        #   - how far away is the nearest wall in each direction?
        #   - how much open space does each turn lead into? (try a flood fill)
        #   - where are the enemy heads, and how long are they?
        #   - how long is our own body, as a fraction of the board?
        #
        # The food offset above is in *board* coordinates. Try making it
        # egocentric instead (is the food to my left, right, or ahead?) - it
        # is usually much easier to learn from.

        return np.array(features, dtype=np.float32)

    @staticmethod
    def is_blocked(state: GameState, pos) -> bool:
        """Would moving into this cell kill us? Handy when writing observe()."""

        if not (0 <= pos[0] < state.width and 0 <= pos[1] < state.height):
            return True

        if pos in state.walls:
            return True

        if pos in state.snake.body_set:
            return True

        for enemy in state.enemies:
            if pos in enemy.body_set:
                return True

        return False

    def step(self, action):
        """
        Plays one move and reports back. Every Gymnasium environment returns
        these same five things, so this shape will look familiar forever.
        """

        # Grab anything you want to compare against after the move.
        # Copy out plain values like these two. If you hold on to a whole
        # GameState instead, it changes under you as the snakes move.
        prev_score = self.game.snakes[0].score
        prev_head = self.game.snakes[0].head

        self.play_turn(ACTIONS[int(action)])

        state = self.game.getGameState(0)

        # The game can end two different ways and RL cares which:
        # dying is your snake's own fault, running out of moves is not.
        # Getting these the wrong way round can quietly make learning worse.
        terminated = not self.game.snakes[0].isAlive
        truncated = self.game.game_over and not terminated

        # ======================================
        # =        Shape your reward!          =
        # ======================================

        reward = 0.0

        # ate some food
        if state.score > prev_score:
            reward += 1.0

        # died
        if terminated:
            reward -= 1.0

        # The two rules above already get you a long way.
        # Some other things to try:
        #   - a small penalty every step, so it stops going in circles
        #   - a small bonus for ending the move closer to food than it
        #     started (that is what prev_head is for)
        #   - a penalty for trapping itself in a small pocket of space
        #
        # Fair warning: reward shaping is fiddly and easy to get backwards;
        # reward a snake for surviving and it can learn to sit in a corner.

        return self.observe(state), reward, terminated, truncated, {}

    def reset(self, seed=None, options=None):
        """Starts a new game and hands back the first observation."""

        super().reset(seed=seed)
        self.new_game(seed)
        return self.observe(self.game.getGameState(0)), {}

    # ==========================================================
    # =                                                        =
    # =   The SnakeGame plumbing - please leave this alone.    =
    # =                                                        =
    # =   play_turn() moves every snake exactly the way        =
    # =   snake/test.py does. Change it and you will be        =
    # =   training against a different game to the one you     =
    # =   get scored on, with nothing to warn you.             =
    # =                                                        =
    # ==========================================================

    def build_game(self, cfg):
        self.game = SnakeGame(
            width=cfg["width"],
            height=cfg["height"],
            num_enemies=cfg["num_enemies"],
            max_moves=cfg["max_moves"],
            num_food=cfg["num_food"],
        )

    def new_game(self, seed=None):
        # SnakeGame spawns things with the global random module
        if seed is not None:
            random.seed(seed)
        self.game.reset()

    def play_turn(self, turn):
        # your snake moves first (index 0), then every enemy still alive
        for i in range(len(self.game.snakes)):
            if self.game.snakes[i].isAlive:
                state = self.game.getGameState(i)
                self.game.move_snake(i, turn if i == 0 else enemyAI(state))


# How your snake learns!
def make_model(env):
    """
    Builds the learning algorithm. PPO is a solid all-rounder and a good
    place to start - try tuning these numbers, or swap it for DQN or A2C.
    """

    from stable_baselines3 import PPO

    return PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=512,
        batch_size=256,
        gamma=0.99,
        # nudges the snake into trying new things instead of committing early
        ent_coef=0.01,
        verbose=1,
        # these models are tiny, a CPU beats a GPU for them
        device="cpu",
    )
