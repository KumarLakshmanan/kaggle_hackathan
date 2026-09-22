!pip install -q -U kaggle-environments

import json
from kaggle_environments import make
from kaggle_environments.agent import build_agent

import kaggle_environments
print("kaggle_environments version:", kaggle_environments.__version__)

TURNS_PER_DAY = 24  # matches the env's default configuration


def load_agent(path_or_source):
    """
    Load a Kaggle-submission-style agent (a .py file path, or its raw
    source as a string) and wrap it so obs["step"] is always correct.

    kaggle_environments/core.py only stamps "step" onto seat 0's
    observation; kaggriculture.py's interpreter propagates day/hour/farms/
    market/town to every other seat each turn, but never step. Any agent
    reading obs["step"] therefore sees None (-> 0 via .get("step", 0))
    forever whenever it's placed in seat 1. day/hour ARE synced correctly
    for every seat, so we recompute step from those instead of trusting
    whatever kaggle_environments already put there.
    """
    raw_fn, _ = build_agent(path_or_source, {}, "kaggriculture")

    def patched(obs, config=None):
        obs["step"] = obs.get("day", 0) * TURNS_PER_DAY + obs.get("hour", 0)
        return raw_fn(obs, config if config is not None else {})

    return patched

AGENT_A_PATH = "/kaggle/input/datasets/raykkretzschmar/kaggriculture-reference-agents/rotation_rosa.py"   # <-- edit me
AGENT_B_PATH = "/kaggle/input/datasets/raykkretzschmar/kaggriculture-reference-agents/melon_mateo.py"   # <-- edit me

EPISODE_STEPS = 720   # full season; lower this for a quick smoke test
SEED = None           # set an int for a reproducible matchup

agent_a = load_agent(AGENT_A_PATH)
agent_b = load_agent(AGENT_B_PATH)

config = {"episodeSteps": EPISODE_STEPS}
if SEED is not None:
    config["seed"] = SEED

env = make("kaggriculture", configuration=config, debug=True)
env.run([agent_a, agent_b])

final = env.steps[-1]
money_a = final[0].observation.farms[0]["money"]
money_b = final[0].observation.farms[1]["money"]
print(f"Agent A (seat 0) final bank: {money_a:,.0f}  -- status: {final[0].status}")
print(f"Agent B (seat 1) final bank: {money_b:,.0f}  -- status: {final[1].status}")
print("Winner:", "Agent A" if money_a > money_b else "Agent B" if money_b > money_a else "Tie")

from IPython.display import IFrame, display

player_html = env.render(mode="html", width=800, height=800)
with open("replay.html", "w") as f:
    f.write(player_html)

display(IFrame(src="./replay.html", width=800, height=800))

def run_match(seat0_path, seat1_path, seed=SEED, episode_steps=EPISODE_STEPS):
    a = load_agent(seat0_path)
    b = load_agent(seat1_path)
    cfg = {"episodeSteps": episode_steps}
    if seed is not None:
        cfg["seed"] = seed
    e = make("kaggriculture", configuration=cfg)
    e.run([a, b])
    f = e.steps[-1]
    return f[0].observation.farms[0]["money"], f[0].observation.farms[1]["money"]


a_first_a, a_first_b = run_match(AGENT_A_PATH, AGENT_B_PATH)
b_first_b, b_first_a = run_match(AGENT_B_PATH, AGENT_A_PATH)

print(f"A in seat 0 vs B in seat 1:  A={a_first_a:,.0f}  B={a_first_b:,.0f}")
print(f"B in seat 0 vs A in seat 1:  A={b_first_a:,.0f}  B={b_first_b:,.0f}")
print(f"Agent A bank changed by seat: {abs(a_first_a - b_first_a):,.0f}")
print(f"Agent B bank changed by seat: {abs(a_first_b - b_first_b):,.0f}")

with open("replay.json", "w") as f:
    json.dump(env.toJSON(), f)
print("Saved replay.json")