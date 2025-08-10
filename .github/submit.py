import yaml

from snake.snake import test_all

with open("snake/difficulties.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

DIFFICULTIES = CONFIG["difficulties"]

results = test_all(1000, DIFFICULTIES)

avg = (results["easy"] + results["medium"] + results["hard"] + results["chaos"]) / 4

with open("score.txt", "w") as f:
    f.write(f"score={avg}")
