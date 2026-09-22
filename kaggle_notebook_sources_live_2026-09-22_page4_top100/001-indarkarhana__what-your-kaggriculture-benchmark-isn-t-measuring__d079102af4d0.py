import subprocess
import sys
from importlib.metadata import version

SERVER_VERSION = "1.32.5"
try:
    installed = version("kaggle-environments")
except Exception:  # pragma: no cover - metadata missing
    installed = "unknown"
if installed != SERVER_VERSION:
    print(f"image ships {installed}; installing {SERVER_VERSION} to match the server")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", f"kaggle-environments=={SERVER_VERSION}"],
        check=False,
    )

import json

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture.kaggriculture import MARKET_PARAMS, market_price

# Behavioural check, not a version string: these are the numbers that decide the
# game, so verify them directly rather than trusting package metadata.
ON_SERVER_RULES = MARKET_PARAMS["STRAWBERRY"]["above_target"] == 1.6
print("engine loaded | strawberry above_target =",
      MARKET_PARAMS["STRAWBERRY"]["above_target"],
      "| matches server rules:", ON_SERVER_RULES)

def reference_agent(obs, config=None):
    """Wheat/strawberry loop: hire, claim a tile each, water, harvest, sell.

    Each unit owns one tile (assigned by index) and walks to it, so the farm
    fills instead of the units crowding one square. Nothing clever â€” it just has
    to produce enough volume that market saturation is visible.
    """
    seat = int(obs.get("player", 0) or 0)
    farm = obs["farms"][seat]
    private = obs["private"]
    tiles = farm["tiles"]
    seeds = dict(private.get("seeds", {}))
    shed = private.get("shed", {})
    money = farm["money"]
    day = int(obs.get("day", 0) or 0)

    # The starting quadrant is NW: x, y in 0..4 on the default 10x10 board.
    workable = [(x, y) for y in range(5) for x in range(5)]

    market = []
    if farm.get("hires_today", 0) < 8 and money > 150:
        market.append(["HIRE"])
    # Strawberry is an ongoing crop and pays far better; wheat is the cheap filler.
    if money > 1200 and seeds.get("STRAWBERRY", 0) < 2 and day < 18:
        market.append(["BUY_SEED", "STRAWBERRY", 2])
    elif money > 120 and seeds.get("WHEAT", 0) < 3 and day < 27:
        market.append(["BUY_SEED", "WHEAT", 3])
    for product, quantity in sorted(shed.items()):
        if quantity > 0:
            market.append(["SELL", product, int(quantity)])

    planned = {"WHEAT": 0, "STRAWBERRY": 0}

    def step_toward(px, py, tx, ty):
        if px < tx:
            return ["EAST"]
        if px > tx:
            return ["WEST"]
        if py < ty:
            return ["SOUTH"]
        if py > ty:
            return ["NORTH"]
        return ["PASS"]

    def unit_action(position, index):
        px, py = int(position[0]), int(position[1])
        here = tiles[py][px]
        if isinstance(here, dict) and here.get("kind") == "PLANT":
            if here.get("yield_units", 0) > 0:
                return ["HARVEST"]
            if not here.get("watered_today"):
                return ["WATER"]
        if isinstance(here, dict) and here.get("kind") == "WEED":
            return ["DIG"]
        if here is None:
            # PLANT is dropped entirely if more units request a crop than we
            # hold seed for, so each unit reserves against the same budget.
            for crop in ("STRAWBERRY", "WHEAT"):
                if seeds.get(crop, 0) - planned[crop] > 0:
                    planned[crop] += 1
                    return ["PLANT", crop]
        target = workable[index % len(workable)]
        if (px, py) == target:
            return ["PASS"]
        return step_toward(px, py, target[0], target[1])

    hands = [unit_action(position, index + 1)
             for index, position in enumerate(farm.get("hands") or [])]
    return {"farmer": unit_action(farm["farmer"], 0), "hands": hands, "market": market[:10]}


def run_match(player_a, player_b, seed, steps=720):
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed}, debug=False)
    env.run([player_a, player_b])
    final = env.steps[-1]
    return env, [final[s]["observation"]["farms"][s]["money"] for s in (0, 1)]


env, money = run_match(reference_agent, "starter", 101)
print(f"reference agent {money[0]:,.0f}   starter {money[1]:,.0f}")

PASS = {"farmer": ["PASS"], "hands": [], "market": []}


def extract_tape(replay_steps, seat, shift):
    """Rebuild a seat's action sequence. shift=1 is correct, shift=0 is the bug."""
    tape = []
    for t in range(len(replay_steps)):
        source = t + shift
        if source < len(replay_steps) and seat < len(replay_steps[source]):
            tape.append(replay_steps[source][seat].get("action") or dict(PASS))
        else:
            tape.append(dict(PASS))
    return tape


def tape_agent(tape):
    def agent(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        action = tape[step] if step < len(tape) else PASS
        return dict(action) if isinstance(action, dict) else dict(PASS)
    return agent


SEED = 4242
source_env, recorded = run_match(reference_agent, "starter", SEED)
replay = json.loads(json.dumps(source_env.toJSON()))["steps"]
print(f"recorded episode: {recorded[0]:,.0f} vs {recorded[1]:,.0f}")

for shift, label in ((0, "steps[t]  (the common bug)"), (1, "steps[t+1] (correct)")):
    tapes = [extract_tape(replay, s, shift) for s in (0, 1)]
    _, replayed = run_match(tape_agent(tapes[0]), tape_agent(tapes[1]), SEED)
    exact = all(abs(replayed[s] - recorded[s]) < 1e-9 for s in (0, 1))
    print(f"  {label}: {replayed[0]:>10,.0f} vs {replayed[1]:>10,.0f}   "
          f"{'EXACT' if exact else 'DOES NOT REPRODUCE'}")

# `above_target` and the resulting price at a full anchor-throughput glut, on the
# engine the notebook image ships versus the engine the ladder runs. The 1.29.3
# column is recorded here because the cell at the top of this notebook has
# already upgraded the session â€” run this notebook with that cell removed and the
# live column becomes the 1.29.3 one.
IMAGE_1_29_3 = {  # what a default Kaggle notebook gives you
    "STRAWBERRY": (0.40, 72), "MILK": (0.40, 96), "MELON": (0.90, 25), "WOOL": (0.80, 40),
}

print(f"{'resource':12s} | {'image 1.29.3':>22s} | {'server 1.32.5 (live)':>22s}")
print(f"{'':12s} | {'above_tgt':>10s} {'P(I0+T)':>11s} | {'above_tgt':>10s} {'P(I0+T)':>11s}")
for name, (old_target, old_price) in IMAGE_1_29_3.items():
    live_target = MARKET_PARAMS[name]["above_target"]
    live_price = market_price(name, MARKET_PARAMS[name]["I0"] + MARKET_PARAMS[name]["T"])
    print(f"{name:12s} | {old_target:10.2f} {old_price:11d} | {live_target:10.2f} {live_price:11d}")

print(f"\nthis session is running server rules: {ON_SERVER_RULES}")

print(f"{'resource':12s} {'base':>5s} {'above_func':>11s} {'above_target':>13s} {'P(I0+T)':>8s} {'P(I0+2T)':>9s}")
for name, params in MARKET_PARAMS.items():
    i0, throughput = params["I0"], params["T"]
    print(f"{name:12s} {params['base']:5d} {params['above_func']:>11s} "
          f"{params['above_target']:13.2f} "
          f"{market_price(name, i0 + throughput):8d} {market_price(name, i0 + 2 * throughput):9d}")