!pip install -q -U kaggle-environments

import json
from kaggle_environments import make

import kaggle_environments
print("kaggle_environments version:", kaggle_environments.__version__)

def load_replay(path):
    """
    Reconstruct a finished kaggle_environments Environment from a saved
    episode JSON, instead of running live agents.

    A JSON produced by `json.dump(env.toJSON(), f)` (or downloaded from a
    competition's Episodes page) already contains everything
    `kaggle_environments.make()` needs to rebuild the environment: the
    game name, its configuration, the episode `info` (team names, seed,
    etc.), and the full per-turn `steps` history. Passing `steps=` makes
    `make()` skip running any agent entirely -- the environment comes
    back already DONE, exactly as recorded.
    """
    with open(path) as f:
        data = json.load(f)

    env = make(
        data["name"],
        configuration=data.get("configuration"),
        info=data.get("info"),
        steps=data["steps"],
    )
    return env, data

REPLAY_JSON_PATH = "/kaggle/input/datasets/kaggle/kaggriculture-episodes-2026-07-30/89006909.json"   # <-- edit me

env, replay_data = load_replay(REPLAY_JSON_PATH)

names = replay_data.get("info", {}).get("TeamNames", ["Seat 0", "Seat 1"])

final = env.steps[-1]
money_a = final[0].observation.farms[0]["money"]
money_b = final[0].observation.farms[1]["money"]

print(f"{names[0]} (seat 0) final bank: {money_a:,.0f}  -- status: {final[0].status}")
print(f"{names[1]} (seat 1) final bank: {money_b:,.0f}  -- status: {final[1].status}")
print("Winner:", names[0] if money_a > money_b else names[1] if money_b > money_a else "Tie")

from IPython.display import IFrame, display

player_html = env.render(mode="html", width=800, height=800)
with open("replay.html", "w") as f:
    f.write(player_html)

display(IFrame(src="./replay.html", width=800, height=800))

