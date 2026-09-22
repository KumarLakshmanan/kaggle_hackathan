from __future__ import annotations

import ast
import hashlib
import importlib.util
import tarfile
from pathlib import Path

import pandas as pd
from kaggle_environments import make

WORKING_DIR = Path.cwd()
AGENT_PATH = WORKING_DIR / "main.py"
ARCHIVE_PATH = WORKING_DIR / "submission.tar.gz"

print(f"Working directory: {WORKING_DIR}")
print("Environment import: OK")

AGENT_SOURCE = r'''
"""Kaggriculture baseline: deterministic multi-crop farm scheduler.

The submission contract requires a top-level ``agent(obs)`` function and no
non-standard dependencies.  The policy deliberately uses only the public
observation:

* reserve the initial 5x5 quadrant for a diversified crop mix;
* hire seven cheap hands each day;
* greedily route every unit to a unique farm task;
* water plants before they can be lost, harvest mature crops, clear weeds,
  and replant while there is enough season left;
* sell everything that has reached the shed.
"""

CROP_RULES = {
    "WHEAT": {
        "seed_cost": 10,
        "first_yield_day": 2,
        "harvest_day": 4,
        "last_plant_day": 24,
        "ongoing": False,
    },
    "CARROT": {
        "seed_cost": 20,
        "first_yield_day": 2,
        "harvest_day": 3,
        "last_plant_day": 25,
        "ongoing": False,
    },
    "TOMATO": {
        "seed_cost": 50,
        "first_yield_day": 8,
        "harvest_day": None,
        "last_plant_day": 20,
        "ongoing": True,
    },
    "STRAWBERRY": {
        "seed_cost": 100,
        "first_yield_day": 10,
        "harvest_day": None,
        "last_plant_day": 18,
        "ongoing": True,
    },
    "MELON": {
        "seed_cost": 80,
        "first_yield_day": 10,
        "harvest_day": 12,
        "last_plant_day": 16,
        "ongoing": False,
    },
}

SELL_ORDER = (
    "MELON",
    "STRAWBERRY",
    "TOMATO",
    "CARROT",
    "WHEAT",
    "EGG",
    "MILK",
    "WOOL",
)
TARGET_HANDS = 7
MAX_MARKET_ORDERS = 10


def _crop_plan(board_size):
    """Return a fixed crop assignment for the unlocked NW quadrant.

    Long-cycle melons are placed farthest from the shed.  Fast-cycle wheat and
    carrots are closer, reducing repeated travel over the season.
    """

    half = max(1, board_size // 2)
    shed_access = (half - 1, half - 1)
    cells = [(x, y) for y in range(half) for x in range(half)]
    cells.sort(
        key=lambda pos: (
            -(abs(pos[0] - shed_access[0]) + abs(pos[1] - shed_access[1])),
            pos[1],
            pos[0],
        )
    )

    n_cells = len(cells)
    # On the default 5x5 quadrant this is 15 melon, 3 carrot, 3 wheat,
    # 2 tomato, and 2 strawberry tiles.  The mix was selected by a small
    # round-robin rather than by maximizing only against the weak starter bot:
    # more melons earn a larger solo score but lose value quickly when both
    # players flood the shared market.
    counts = {
        "MELON": max(1, round(n_cells * 0.60)),
        "CARROT": max(1, round(n_cells * 0.12)),
        "WHEAT": max(1, round(n_cells * 0.12)),
        "TOMATO": max(1, round(n_cells * 0.08)),
    }
    counts["STRAWBERRY"] = max(0, n_cells - sum(counts.values()))

    crops = []
    for crop in ("MELON", "CARROT", "WHEAT", "TOMATO", "STRAWBERRY"):
        crops.extend([crop] * counts[crop])
    crops = crops[:n_cells]
    while len(crops) < n_cells:
        crops.append("WHEAT")
    return {cell: crop for cell, crop in zip(cells, crops)}


def _task_for_tile(tile, crop, day, hour, seeds):
    """Return ``(priority, action)`` for a tile, or ``None``.

    Lower priorities are scheduled first.  A one-time crop that is ready is
    harvested without spending another action on watering.  Ongoing crops are
    watered first, then harvested on a later turn.
    """

    rules = CROP_RULES[crop]

    if tile == "LOCKED":
        return None
    if tile is None:
        safe_to_plant = hour <= 21 and day <= rules["last_plant_day"]
        if safe_to_plant and seeds.get(crop, 0) > 0:
            return (3, ["PLANT", crop])
        return None
    if not isinstance(tile, dict):
        return None
    if tile.get("kind") == "WEED":
        return (2, ["DIG"])
    if tile.get("kind") != "PLANT":
        return None

    planted_crop = tile.get("crop")
    if planted_crop != crop:
        # The plan is stable, but recover gracefully from a hand-edited bot or
        # an old replay by tending the existing crop until it naturally clears.
        crop = planted_crop
        rules = CROP_RULES.get(crop, rules)

    age = day - tile.get("planted_day", day)
    yield_units = tile.get("yield_units", 0)

    if not rules["ongoing"]:
        ready = age >= rules["harvest_day"] and yield_units > 0
        if ready:
            return (0, ["HARVEST"])
        if not tile.get("watered_today", False):
            return (1, ["WATER"])
        return None

    if not tile.get("watered_today", False):
        return (1, ["WATER"])
    if yield_units > 0 and age >= rules["first_yield_day"]:
        return (0, ["HARVEST"])
    return None


def _move_toward(source, target):
    """Take one deterministic Manhattan step toward ``target``."""

    x, y = source
    tx, ty = target
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]
    return ["PASS"]


def _unit_actions(obs, farm, private, plan):
    """Greedily allocate unique task tiles to the farmer and every hand."""

    day = int(obs.get("day", 0))
    hour = int(obs.get("hour", 0))
    seeds = private.get("seeds", {}) or {}
    tiles = farm["tiles"]
    positions = [farm["farmer"], *farm.get("hands", [])]

    tasks = []
    for (x, y), crop in plan.items():
        task = _task_for_tile(tiles[y][x], crop, day, hour, seeds)
        if task is not None:
            priority, action = task
            tasks.append(
                {
                    "priority": priority,
                    "position": (x, y),
                    "action": action,
                    "crop": crop,
                }
            )

    reserved = set()
    seed_budget = dict(seeds)
    actions = []

    for position in positions:
        px, py = position
        candidates = []
        for task in tasks:
            target = task["position"]
            if target in reserved:
                continue
            distance = abs(px - target[0]) + abs(py - target[1])
            candidates.append(
                (
                    task["priority"] * 100 + distance,
                    distance,
                    target[1],
                    target[0],
                    task,
                )
            )

        if not candidates:
            actions.append(["PASS"])
            continue

        candidates.sort(key=lambda item: item[:-1])
        selected = None
        for candidate in candidates:
            task = candidate[-1]
            action = task["action"]
            if (
                candidate[1] == 0
                and action[0] == "PLANT"
                and seed_budget.get(action[1], 0) <= 0
            ):
                continue
            selected = task
            break

        if selected is None:
            actions.append(["PASS"])
            continue

        target = selected["position"]
        reserved.add(target)
        if (px, py) == target:
            action = selected["action"]
            if action[0] == "PLANT":
                seed_budget[action[1]] = seed_budget.get(action[1], 0) - 1
            actions.append(action)
        else:
            actions.append(_move_toward((px, py), target))

    return actions


def _market_actions(obs, farm, private, plan):
    """Sell shed contents, replenish immediately usable seeds, and hire hands."""

    day = int(obs.get("day", 0))
    hour = int(obs.get("hour", 0))
    shed = private.get("shed", {}) or {}
    seeds = private.get("seeds", {}) or {}
    tiles = farm["tiles"]
    orders = []

    # Product sales are ordered before purchases so their proceeds are
    # available to later market orders in the same turn.
    for item in SELL_ORDER:
        quantity = int(shed.get(item, 0))
        if quantity > 0 and len(orders) < MAX_MARKET_ORDERS:
            orders.append(["SELL", item, quantity])

    # Buy only for empty planned cells.  Seeds are uncapped and persist, but
    # avoiding large speculative inventories preserves cash for daily hands.
    empty_needs = {}
    for (x, y), crop in plan.items():
        if tiles[y][x] is None and day <= CROP_RULES[crop]["last_plant_day"]:
            empty_needs[crop] = empty_needs.get(crop, 0) + 1

    budget = float(farm.get("money", 0))
    for crop in ("MELON", "CARROT", "WHEAT", "TOMATO", "STRAWBERRY"):
        needed = max(0, empty_needs.get(crop, 0) - int(seeds.get(crop, 0)))
        if needed <= 0 or len(orders) >= MAX_MARKET_ORDERS:
            continue
        cost = CROP_RULES[crop]["seed_cost"]
        affordable = min(needed, int(budget // cost))
        if affordable > 0:
            orders.append(["BUY_SEED", crop, affordable])
            budget -= affordable * cost

    # Hires are useful only while farm work remains.  Missing hires are filled
    # during the first few turns of each day if sales/seed orders used the cap.
    if day < 29 and hour <= 3:
        missing_hands = max(0, TARGET_HANDS - len(farm.get("hands", [])))
        while missing_hands > 0 and len(orders) < MAX_MARKET_ORDERS:
            orders.append(["HIRE"])
            missing_hands -= 1

    return orders


def agent(obs):
    """Kaggle entry point."""

    farms = obs.get("farms", []) or []
    player = int(obs.get("player", 0))
    if player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    private = obs.get("private", {}) or {}
    board_size = len(farm.get("tiles", [])) or 10
    plan = _crop_plan(board_size)

    # Day 29 is a liquidation buffer: everything harvested by the end of day
    # 28 has reached the shed and can still be sold into banked reward.
    if int(obs.get("day", 0)) >= 29:
        hands = [["PASS"] for _ in farm.get("hands", [])]
        return {
            "farmer": ["PASS"],
            "hands": hands,
            "market": _market_actions(obs, farm, private, plan),
        }

    actions = _unit_actions(obs, farm, private, plan)
    farmer_action = actions[0] if actions else ["PASS"]
    hand_actions = actions[1:] if len(actions) > 1 else []
    return {
        "farmer": farmer_action,
        "hands": hand_actions,
        "market": _market_actions(obs, farm, private, plan),
    }
'''

AGENT_PATH.write_text(AGENT_SOURCE, encoding="utf-8")
print(f"Wrote {AGENT_PATH.name}: {AGENT_PATH.stat().st_size:,} bytes")

tree = ast.parse(AGENT_SOURCE)
top_level_functions = {
    node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
assert "agent" in top_level_functions, "Submission must expose agent(obs)"
compile(AGENT_SOURCE, str(AGENT_PATH), "exec")

spec = importlib.util.spec_from_file_location("kaggriculture_baseline_agent", AGENT_PATH)
agent_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(agent_module)

assert callable(agent_module.agent)
print("AST, compilation, import, and callable checks: OK")

def run_match(seed: int, baseline_side: int, opponent: str = "starter") -> dict:
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    if opponent == "self":
        agents = [agent_module.agent, agent_module.agent]
    elif baseline_side == 0:
        agents = [agent_module.agent, opponent]
    else:
        agents = [opponent, agent_module.agent]

    env.run(agents)
    final = env.steps[-1]
    rewards = [float(state.reward) for state in final]
    statuses = [state.status for state in final]

    return {
        "opponent": opponent,
        "seed": seed,
        "baseline_side": baseline_side,
        "baseline_reward": rewards[baseline_side],
        "opponent_reward": rewards[1 - baseline_side],
        "baseline_status": statuses[baseline_side],
        "opponent_status": statuses[1 - baseline_side],
        "win": rewards[baseline_side] > rewards[1 - baseline_side],
    }


results = []
for match_seed in (7, 19, 41):
    results.append(run_match(match_seed, baseline_side=0, opponent="starter"))
    results.append(run_match(match_seed, baseline_side=1, opponent="starter"))

for match_seed in (11, 29):
    results.append(run_match(match_seed, baseline_side=0, opponent="self"))

results_df = pd.DataFrame(results)
results_df

assert (results_df["baseline_status"] == "DONE").all()
assert (results_df["opponent_status"] == "DONE").all()

starter_rows = results_df[results_df["opponent"] == "starter"]
self_rows = results_df[results_df["opponent"] == "self"]
assert starter_rows["win"].all(), "Baseline should beat starter in every smoke-test match"

summary = pd.DataFrame(
    [
        {
            "matchup": "baseline vs starter",
            "games": len(starter_rows),
            "wins": int(starter_rows["win"].sum()),
            "mean_baseline_reward": round(starter_rows["baseline_reward"].mean(), 1),
            "mean_opponent_reward": round(starter_rows["opponent_reward"].mean(), 1),
        },
        {
            "matchup": "mirror self-play",
            "games": len(self_rows),
            "wins": int(self_rows["win"].sum()),
            "mean_baseline_reward": round(self_rows["baseline_reward"].mean(), 1),
            "mean_opponent_reward": round(self_rows["opponent_reward"].mean(), 1),
        },
    ]
)
summary

with tarfile.open(ARCHIVE_PATH, "w:gz") as archive:
    archive.add(AGENT_PATH, arcname="main.py")

with tarfile.open(ARCHIVE_PATH, "r:gz") as archive:
    members = archive.getnames()

assert members == ["main.py"], f"Unexpected archive members: {members}"
archive_sha256 = hashlib.sha256(ARCHIVE_PATH.read_bytes()).hexdigest()

package_info = {
    "archive": ARCHIVE_PATH.name,
    "size_bytes": ARCHIVE_PATH.stat().st_size,
    "members": members,
    "sha256": archive_sha256,
}
package_info