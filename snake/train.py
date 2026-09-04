import os

RL_DEPS_MISSING = """
Reinforcement learning needs a couple of extra packages that aren't
installed by default.

Open pyproject.toml, uncomment these two lines:

    # "gymnasium>=1.0",
    # "stable-baselines3>=2.4",

then reinstall:

    pip install -e .

(Uncommenting them also means your trained snake will work when you push
it - the competition scorer installs whatever is in your pyproject.toml.)
"""


def train(name, cfg, steps, n_envs, seed, resume, model_path="model.zip"):
    # checked on its own so a mistake in your own myEnv.py still shows you
    # a real error instead of this message
    try:
        import stable_baselines3  # noqa: F401
    except ImportError:
        print(RL_DEPS_MISSING)
        return

    from stable_baselines3 import PPO
    from stable_baselines3.common.env_checker import check_env
    from stable_baselines3.common.env_util import make_vec_env

    from myEnv import SnakeEnv, make_model

    print(f"Training on {name} for {steps} steps\n")

    # catches a broken observe() now, with a readable message, rather
    # than partway through training
    print("Checking your environment...")
    try:
        check_env(SnakeEnv(cfg))
    except AssertionError as e:
        print("\nSomething is wrong with your observe():\n")
        print(f"  {e}\n")
        print("Every feature you return needs to sit between -1 and 1.")
        print("Divide positions by state.width / state.height to scale them down.")
        return
    print("Looks good!\n")

    env = make_vec_env(SnakeEnv, n_envs=n_envs, env_kwargs={"cfg": cfg}, seed=seed)

    if resume and os.path.exists(model_path):
        print(f"Resuming training from {model_path}\n")
        model = PPO.load(model_path, env=env, device="cpu")
    else:
        model = make_model(env)

    # watch ep_rew_mean in the table below - that is your snake getting better
    # log_interval keeps that table readable instead of a scrolling blur
    model.learn(total_timesteps=steps, log_interval=10)

    model.save(model_path)

    print(f"\nSaved your model to {model_path}")
    print("Next:")
    print("  1. uncomment the two rlAI lines in myAI.py")
    print("  2. snake run easy        (watch it play)")
    print("  3. snake test 100 easy   (score it)")

    return model
