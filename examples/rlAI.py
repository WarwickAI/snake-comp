"""
Plays using a model trained with `snake train`.

The observation comes from SnakeEnv.observe - the same method training
used, so the two can never disagree about what the snake is looking at.
"""

from pathlib import Path

from snake.logic import GameState, Turn
from myEnv import ACTIONS, SnakeEnv

MODEL_PATH = Path(__file__).resolve().parent.parent / "model.zip"

_model = None


def rlAI(state: GameState) -> Turn:
    global _model

    # loads the model once and hangs onto it - `snake test` calls this
    # hundreds of thousands of times, so reloading every move would crawl
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"No trained model found at {MODEL_PATH}.\n"
                "Train one first with:  snake train easy"
            )

        from stable_baselines3 import PPO

        _model = PPO.load(MODEL_PATH, device="cpu")

        # catches the easy mistake of changing observe() and forgetting to
        # retrain - otherwise this surfaces as a wall of Stable Baselines 3
        # traceback several layers down
        trained_on = _model.observation_space.shape[0]
        returns_now = SnakeEnv.observe(state).shape[0]
        if trained_on != returns_now:
            raise ValueError(
                f"Your model was trained on {trained_on} observations, but "
                f"observe() now returns {returns_now}.\n"
                "Looks like you changed observe() without retraining - "
                "run `snake train easy` again."
            )

    action, _ = _model.predict(SnakeEnv.observe(state), deterministic=True)
    return ACTIONS[int(action)]
