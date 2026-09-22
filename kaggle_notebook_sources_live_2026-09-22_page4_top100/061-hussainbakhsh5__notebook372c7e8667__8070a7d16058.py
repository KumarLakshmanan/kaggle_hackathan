# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python Docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

# Input data files are available in the read-only "../input/" directory
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# You can write up to 20GB to the current directory (/kaggle/working/) that gets preserved as output when you create a version using "Save & Run All" 
# You can also write temporary files to /kaggle/temp/, but they won't be saved outside of the current session

# Use the kagglehub client library to attach Kaggle resources like competitions, datasets, and models to your session
# Learn more about kagglehub: https://github.com/Kaggle/kagglehub/blob/main/README.md

import kagglehub
# kagglehub.dataset_download('<owner>/<dataset-slug>')

import numpy as np 
import pandas as pd
import os

base = "/kaggle/input"

for root, dirs, files in os.walk(base):
    for file in files:
        print(os.path.join(root, file))

from pathlib import Path

base = Path("/kaggle/input/competitions/kaggriculture")

print("=" * 80)
print("README.md")
print("=" * 80)
print((base / "README.md").read_text())

print("\n" + "=" * 80)
print("AGENTS.md")
print("=" * 80)
print((base / "AGENTS.md").read_text())

from kaggle_environments import make

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 100},
    debug=True
)

print("Environment created successfully!")

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 100},
    debug=True
)

env.run(["starter", "random"])

final = env.steps[-1]

for i, s in enumerate(final):
    print(
        f"Player {i}: "
        f"reward={s.reward}, "
        f"status={s.status}"
    )

obs = env.steps[0][0].observation

print(obs.keys())

print(obs)

def wheat_agent(obs):
    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    x, y = farm["farmer"]
    tile = farm["tiles"][y][x]

    market = []

    # -------------------------------------------------
    # Sell harvested wheat
    # -------------------------------------------------
    wheat = private["shed"].get("WHEAT", 0)

    if wheat > 0:
        market.append(["SELL", "WHEAT", wheat])

    # -------------------------------------------------
    # Buy wheat seed if we don't have one
    # -------------------------------------------------
    seeds = private["seeds"].get("WHEAT", 0)

    if seeds == 0 and farm["money"] >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])

    # -------------------------------------------------
    # Current tile is empty -> plant
    # -------------------------------------------------
    if tile is None and seeds > 0:
        return {
            "farmer": ["PLANT", "WHEAT"],
            "hands": [],
            "market": market
        }

    # -------------------------------------------------
    # Current tile contains a plant
    # -------------------------------------------------
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":

        crop = tile.get("crop")

        if crop == "WHEAT":

            age = obs["day"] - tile["planted_day"]

            # Harvest after first yield becomes available
            if age >= 2 and tile["yield_units"] > 0:
                return {
                    "farmer": ["HARVEST"],
                    "hands": [],
                    "market": market
                }

            # Water once per day
            if not tile["watered_today"]:
                return {
                    "farmer": ["WATER"],
                    "hands": [],
                    "market": market
                }

    # -------------------------------------------------
    # Nothing useful to do
    # -------------------------------------------------
    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }

from kaggle_environments import make

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 720
    },
    debug=True
)

env.run([wheat_agent, "random"])

final = env.steps[-1]

for i, s in enumerate(final):
    print(
        f"Player {i}: "
        f"reward={s.reward}, "
        f"status={s.status}"
    )

print("Our final money:", final[0].observation["farms"][0]["money"])
print("Opponent final money:", final[1].observation["farms"][1]["money"])

from kaggle_environments import make
import numpy as np

def run_match(agent1, agent2, n=5, steps=720):
    results = []

    for seed in range(n):
        env = make(
            "kaggriculture",
            configuration={
                "episodeSteps": steps,
                "seed": seed
            },
            debug=True
        )

        env.run([agent1, agent2])

        final = env.steps[-1]

        money1 = final[0].observation["farms"][0]["money"]
        money2 = final[1].observation["farms"][1]["money"]

        results.append((money1, money2))

        print(
            f"Game {seed + 1}: "
            f"Our={money1:.0f}, "
            f"Opponent={money2:.0f}"
        )

    our = [x[0] for x in results]
    opp = [x[1] for x in results]

    print("\n===== SUMMARY =====")
    print(f"Our average:      {np.mean(our):.2f}")
    print(f"Opponent average: {np.mean(opp):.2f}")
    print(f"Our best:         {np.max(our):.2f}")
    print(f"Our worst:        {np.min(our):.2f}")


run_match(wheat_agent, "random", n=5)

def move_towards(current, target):
    x, y = current
    tx, ty = target

    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]

    return None

def get_empty_tiles(farm):
    tiles = farm["tiles"]
    empty = []

    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile is None:
                empty.append((x, y))

    return empty


# Test
player = obs["player"]
farm = obs["farms"][player]

empty_tiles = get_empty_tiles(farm)

print("Number of empty tiles:", len(empty_tiles))
print("First 10:", empty_tiles[:10])

def move_towards(current, target):
    x, y = current
    tx, ty = target

    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]

    return None


def get_empty_tiles(farm):
    empty = []

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if tile is None:
                empty.append((x, y))

    return empty


def get_plant_tiles(farm):
    plants = []

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
            ):
                plants.append((x, y, tile))

    return plants


def wheat_agent_v2(obs):

    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    position = farm["farmer"]
    x, y = position

    tile = farm["tiles"][y][x]

    market = []

    # =====================================================
    # SELL WHEAT
    # =====================================================

    wheat = private["shed"].get("WHEAT", 0)

    if wheat > 0:
        market.append(["SELL", "WHEAT", wheat])

    # =====================================================
    # BUY WHEAT SEED
    # =====================================================

    seeds = private["seeds"].get("WHEAT", 0)

    if seeds == 0 and farm["money"] >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])

    # =====================================================
    # 1. HANDLE CURRENT PLANT
    # =====================================================

    if isinstance(tile, dict) and tile.get("kind") == "PLANT":

        if tile.get("crop") == "WHEAT":

            age = obs["day"] - tile["planted_day"]

            # Harvest when wheat has matured
            if age >= 2 and tile.get("yield_units", 0) > 0:
                return {
                    "farmer": ["HARVEST"],
                    "hands": [],
                    "market": market
                }

            # Water once per day
            if not tile.get("watered_today", False):
                return {
                    "farmer": ["WATER"],
                    "hands": [],
                    "market": market
                }

    # =====================================================
    # 2. FIND EMPTY TILE
    # =====================================================

    empty_tiles = get_empty_tiles(farm)

    # Prefer tiles close to farmer
    if empty_tiles:

        target = min(
            empty_tiles,
            key=lambda p: abs(p[0] - x) + abs(p[1] - y)
        )

        movement = move_towards(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

        # We reached empty tile
        if seeds > 0:
            return {
                "farmer": ["PLANT", "WHEAT"],
                "hands": [],
                "market": market
            }

    # =====================================================
    # 3. FIND PLANTS THAT NEED WATER
    # =====================================================

    plants = get_plant_tiles(farm)

    for px, py, plant in plants:

        if plant.get("crop") != "WHEAT":
            continue

        if not plant.get("watered_today", False):

            target = (px, py)

            movement = move_towards(position, target)

            if movement is not None:
                return {
                    "farmer": movement,
                    "hands": [],
                    "market": market
                }

            return {
                "farmer": ["WATER"],
                "hands": [],
                "market": market
            }

    # =====================================================
    # 4. NOTHING TO DO
    # =====================================================

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 120,
        "seed": 42
    },
    debug=True
)

env.run([wheat_agent_v2, "random"])

final = env.steps[-1]

for i, s in enumerate(final):
    print(
        f"Player {i}: "
        f"reward={s.reward}, "
        f"money={s.observation['farms'][i]['money']}, "
        f"status={s.status}"
    )

my_farm = final[0].observation["farms"][0]

plants = []

for yy, row in enumerate(my_farm["tiles"]):
    for xx, tile in enumerate(row):
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            plants.append(
                (xx, yy, tile.get("crop"), tile.get("yield_units"))
            )

print("Plants at end:")
print(plants)

def scan_farm(farm):
    empty = []
    plants = []
    weeds = []

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):

            if tile is None:
                empty.append((x, y))

            elif isinstance(tile, dict):

                if tile.get("kind") == "PLANT":
                    plants.append((x, y, tile))

                elif tile.get("kind") == "WEED":
                    weeds.append((x, y))

    return empty, plants, weeds


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def nearest(position, locations):

    if not locations:
        return None

    return min(
        locations,
        key=lambda p: distance(position, p)
    )


def go_to(position, target):

    if target is None:
        return ["PASS"]

    x, y = position
    tx, ty = target

    if x < tx:
        return ["EAST"]

    if x > tx:
        return ["WEST"]

    if y < ty:
        return ["SOUTH"]

    if y > ty:
        return ["NORTH"]

    return None

def wheat_agent_v3(obs):

    player = obs["player"]

    farm = obs["farms"][player]
    private = obs["private"]

    position = tuple(farm["farmer"])

    empty, plants, weeds = scan_farm(farm)

    x, y = position
    current_tile = farm["tiles"][y][x]

    market = []

    # =====================================================
    # MARKET
    # =====================================================

    shed_wheat = private["shed"].get("WHEAT", 0)

    if shed_wheat > 0:
        market.append(
            ["SELL", "WHEAT", shed_wheat]
        )

    seeds = private["seeds"].get("WHEAT", 0)

    # Keep some cash available
    if seeds == 0 and farm["money"] >= 10:
        market.append(
            ["BUY_SEED", "WHEAT", 1]
        )

    # =====================================================
    # PRIORITY 1 — HARVEST
    # =====================================================

    harvest_targets = []

    for px, py, plant in plants:

        if plant.get("crop") != "WHEAT":
            continue

        age = obs["day"] - plant["planted_day"]

        if (
            age >= 2
            and plant.get("yield_units", 0) > 0
        ):
            harvest_targets.append((px, py))

    target = nearest(
        position,
        harvest_targets
    )

    if target is not None:

        movement = go_to(
            position,
            target
        )

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["HARVEST"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # PRIORITY 2 — WATER
    # =====================================================

    water_targets = []

    for px, py, plant in plants:

        if plant.get("crop") != "WHEAT":
            continue

        if not plant.get("watered_today", False):

            water_targets.append((px, py))

    target = nearest(
        position,
        water_targets
    )

    if target is not None:

        movement = go_to(
            position,
            target
        )

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["WATER"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # PRIORITY 3 — PLANT
    # =====================================================

    if current_tile is None and seeds > 0:

        return {
            "farmer": ["PLANT", "WHEAT"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # PRIORITY 4 — FIND EMPTY TILE
    # =====================================================

    if empty and seeds > 0:

        target = nearest(
            position,
            empty
        )

        movement = go_to(
            position,
            target
        )

        if movement is not None:

            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

    # =====================================================
    # NOTHING TO DO
    # =====================================================

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 120,
        "seed": 42
    },
    debug=True
)

env.run([wheat_agent_v3, "random"])

final = env.steps[-1]

for i, s in enumerate(final):
    print(
        f"Player {i}: "
        f"reward={s.reward}, "
        f"money={s.observation['farms'][i]['money']}, "
        f"status={s.status}"
    )

my_farm = final[0].observation["farms"][0]

plants = []

for yy, row in enumerate(my_farm["tiles"]):

    for xx, tile in enumerate(row):

        if (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
        ):
            plants.append({
                "x": xx,
                "y": yy,
                "crop": tile.get("crop"),
                "yield": tile.get("yield_units"),
                "watered": tile.get("watered_today")
            })

print("Number of plants:", len(plants))
print(plants)

harvest_targets = []

for px, py, plant in plants:
    ...

def wheat_agent_v4(obs):

    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    position = tuple(farm["farmer"])

    # =====================================================
    # SCAN FARM
    # =====================================================

    empty = []
    plants = []
    weeds = []

    for y, row in enumerate(farm["tiles"]):

        for x, tile in enumerate(row):

            if tile is None:
                empty.append((x, y))

            elif isinstance(tile, dict):

                if tile.get("kind") == "PLANT":
                    plants.append((x, y, tile))

                elif tile.get("kind") == "WEED":
                    weeds.append((x, y))

    x, y = position
    current_tile = farm["tiles"][y][x]

    market = []

    # =====================================================
    # SELL WHEAT
    # =====================================================

    wheat = private["shed"].get("WHEAT", 0)

    if wheat > 0:
        market.append(["SELL", "WHEAT", wheat])

    # =====================================================
    # BUY SEED
    # =====================================================

    seeds = private["seeds"].get("WHEAT", 0)

    if seeds == 0 and farm["money"] >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])

    # =====================================================
    # PRIORITY 1 — WATER WHEAT THAT NEEDS WATER
    # =====================================================

    water_targets = []

    for px, py, plant in plants:

        if plant.get("crop") != "WHEAT":
            continue

        if not plant.get("watered_today", False):
            water_targets.append((px, py))

    target = nearest(position, water_targets)

    if target is not None:

        movement = go_to(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["WATER"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # PRIORITY 2 — HARVEST MATURE WHEAT
    # =====================================================

    harvest_targets = []

    for px, py, plant in plants:

        if plant.get("crop") != "WHEAT":
            continue

        age = obs["day"] - plant["planted_day"]

        if (
            age >= 4
            and plant.get("yield_units", 0) > 0
            and plant.get("watered_today", False)
        ):
            harvest_targets.append((px, py))

    target = nearest(position, harvest_targets)

    if target is not None:

        movement = go_to(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["HARVEST"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # PRIORITY 3 — PLANT ON CURRENT EMPTY TILE
    # =====================================================

    if current_tile is None and seeds > 0:

        return {
            "farmer": ["PLANT", "WHEAT"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # PRIORITY 4 — MOVE TO EMPTY TILE
    # =====================================================

    if empty and seeds > 0:

        target = nearest(position, empty)

        movement = go_to(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

    # =====================================================
    # NOTHING TO DO
    # =====================================================

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 120,
        "seed": 42
    },
    debug=True
)

env.run([wheat_agent_v4, "random"])

final = env.steps[-1]

for i, s in enumerate(final):
    print(
        f"Player {i}: "
        f"reward={s.reward}, "
        f"money={s.observation['farms'][i]['money']}, "
        f"status={s.status}"
    )

def hire_test(obs):

    market = []

    # Hire 3 hands on day 0
    if obs["day"] == 0 and obs["hour"] == 0:
        market = [
            ["HIRE"],
            ["HIRE"],
            ["HIRE"],
        ]

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 48,
        "seed": 42
    },
    debug=True
)

env.run([hire_test, "pass"])

obs = env.steps[1][0].observation

print("Hands:", obs["farms"][0]["hands"])
print("Money:", obs["farms"][0]["money"])

def wheat_agent_v5(obs):

    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    market = []

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    farmer_pos = tuple(farm["farmer"])
    hands = farm.get("hands", [])

    positions = [farmer_pos] + [tuple(p) for p in hands]

    # =====================================================
    # SCAN FARM
    # =====================================================

    empty = []
    plants = []

    for y, row in enumerate(farm["tiles"]):

        for x, tile in enumerate(row):

            if tile is None:
                empty.append((x, y))

            elif isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    plants.append((x, y, tile))

    # =====================================================
    # MARKET — SELL WHEAT
    # =====================================================

    wheat = private["shed"].get("WHEAT", 0)

    if wheat > 0:
        market.append(["SELL", "WHEAT", wheat])

    # =====================================================
    # BUY WHEAT SEEDS
    # =====================================================

    seeds = private["seeds"].get("WHEAT", 0)

    if seeds == 0 and farm["money"] >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])

    # =====================================================
    # HIRE 3 HANDS
    # =====================================================

    if obs["hour"] == 0:

        hires_needed = 3 - len(hands)

        for _ in range(max(0, hires_needed)):
            market.append(["HIRE"])

    # =====================================================
    # FARMER ACTION
    # =====================================================

    fx, fy = farmer_pos
    current_tile = farm["tiles"][fy][fx]

    farmer_action = ["PASS"]

    # ---- Harvest first ----

    harvest_targets = []

    for px, py, plant in plants:

        if plant.get("crop") != "WHEAT":
            continue

        age = obs["day"] - plant["planted_day"]

        if (
            age >= 2
            and plant.get("yield_units", 0) > 0
        ):
            harvest_targets.append((px, py))

    target = nearest(
        farmer_pos,
        harvest_targets
    )

    if target is not None:

        movement = go_to(
            farmer_pos,
            target
        )

        if movement is not None:
            farmer_action = movement
        else:
            farmer_action = ["HARVEST"]

    # ---- Water ----

    else:

        water_targets = []

        for px, py, plant in plants:

            if plant.get("crop") != "WHEAT":
                continue

            if not plant.get("watered_today", False):
                water_targets.append((px, py))

        target = nearest(
            farmer_pos,
            water_targets
        )

        if target is not None:

            movement = go_to(
                farmer_pos,
                target
            )

            if movement is not None:
                farmer_action = movement
            else:
                farmer_action = ["WATER"]

        # ---- Plant ----

        elif current_tile is None and seeds > 0:

            farmer_action = ["PLANT", "WHEAT"]

        # ---- Move to empty ----

        elif empty and seeds > 0:

            target = nearest(
                farmer_pos,
                empty
            )

            movement = go_to(
                farmer_pos,
                target
            )

            if movement is not None:
                farmer_action = movement

    # =====================================================
    # HAND ACTIONS
    # =====================================================

    hand_actions = []

    # Assign each hand a watering target
    remaining_water = []

    for px, py, plant in plants:

        if plant.get("crop") == "WHEAT":

            if not plant.get("watered_today", False):
                remaining_water.append((px, py))

    for hand_pos in hands:

        hand_pos = tuple(hand_pos)

        if remaining_water:

            target = nearest(
                hand_pos,
                remaining_water
            )

            remaining_water.remove(target)

            movement = go_to(
                hand_pos,
                target
            )

            if movement is not None:
                hand_actions.append(movement)
            else:
                hand_actions.append(["WATER"])

        else:

            hand_actions.append(["PASS"])

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "farmer": farmer_action,
        "hands": hand_actions,
        "market": market
    }

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 120,
        "seed": 42
    },
    debug=True
)

env.run([wheat_agent_v5, "random"])

final = env.steps[-1]

for i, s in enumerate(final):
    print(
        f"Player {i}: "
        f"reward={s.reward}, "
        f"money={s.observation['farms'][i]['money']}, "
        f"status={s.status}"
    )

obs = final[0].observation

print("Our hands:", obs["farms"][0]["hands"])
print("Our money:", obs["farms"][0]["money"])

def melon_agent(obs):

    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    position = tuple(farm["farmer"])

    market = []

    # Sell harvested melons
    melon = private["shed"].get("MELON", 0)

    if melon > 0:
        market.append(["SELL", "MELON", melon])

    # Buy melon seed
    seeds = private["seeds"].get("MELON", 0)

    if seeds == 0 and farm["money"] >= 80:
        market.append(["BUY_SEED", "MELON", 1])

    # Scan farm
    empty = []
    plants = []

    for y, row in enumerate(farm["tiles"]):

        for x, tile in enumerate(row):

            if tile is None:
                empty.append((x, y))

            elif isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    plants.append((x, y, tile))

    x, y = position
    tile = farm["tiles"][y][x]

    # =====================================================
    # HARVEST
    # =====================================================

    harvest_targets = []

    for px, py, plant in plants:

        if plant.get("crop") != "MELON":
            continue

        age = obs["day"] - plant["planted_day"]

        if age >= 10 and plant.get("yield_units", 0) > 0:
            harvest_targets.append((px, py))

    target = nearest(position, harvest_targets)

    if target is not None:

        movement = go_to(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["HARVEST"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # WATER
    # =====================================================

    water_targets = []

    for px, py, plant in plants:

        if plant.get("crop") == "MELON":

            if not plant.get("watered_today", False):
                water_targets.append((px, py))

    target = nearest(position, water_targets)

    if target is not None:

        movement = go_to(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["WATER"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # PLANT
    # =====================================================

    if tile is None and seeds > 0:

        return {
            "farmer": ["PLANT", "MELON"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # MOVE TO EMPTY
    # =====================================================

    if empty and seeds > 0:

        target = nearest(position, empty)

        movement = go_to(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 120,
        "seed": 42
    },
    debug=True
)

env.run([melon_agent, "random"])

final = env.steps[-1]

for i, s in enumerate(final):
    print(
        f"Player {i}: "
        f"reward={s.reward}, "
        f"money={s.observation['farms'][i]['money']}, "
        f"status={s.status}"
    )

def carrot_agent(obs):

    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    position = tuple(farm["farmer"])

    market = []

    # Sell carrots
    carrots = private["shed"].get("CARROT", 0)

    if carrots > 0:
        market.append(["SELL", "CARROT", carrots])

    # Buy seed
    seeds = private["seeds"].get("CARROT", 0)

    if seeds == 0 and farm["money"] >= 20:
        market.append(["BUY_SEED", "CARROT", 1])

    # Scan farm
    empty = []
    plants = []

    for y, row in enumerate(farm["tiles"]):

        for x, tile in enumerate(row):

            if tile is None:
                empty.append((x, y))

            elif isinstance(tile, dict):

                if tile.get("kind") == "PLANT":
                    plants.append((x, y, tile))

    x, y = position
    current_tile = farm["tiles"][y][x]

    # =====================================================
    # HARVEST
    # =====================================================

    harvest_targets = []

    for px, py, plant in plants:

        if plant.get("crop") != "CARROT":
            continue

        age = obs["day"] - plant["planted_day"]

        if age >= 2 and plant.get("yield_units", 0) > 0:
            harvest_targets.append((px, py))

    target = nearest(position, harvest_targets)

    if target is not None:

        movement = go_to(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["HARVEST"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # WATER
    # =====================================================

    water_targets = []

    for px, py, plant in plants:

        if plant.get("crop") == "CARROT":

            if not plant.get("watered_today", False):
                water_targets.append((px, py))

    target = nearest(position, water_targets)

    if target is not None:

        movement = go_to(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["WATER"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # PLANT
    # =====================================================

    if current_tile is None and seeds > 0:

        return {
            "farmer": ["PLANT", "CARROT"],
            "hands": [],
            "market": market
        }

    # =====================================================
    # MOVE TO EMPTY
    # =====================================================

    if empty and seeds > 0:

        target = nearest(position, empty)

        movement = go_to(position, target)

        if movement is not None:
            return {
                "farmer": movement,
                "hands": [],
                "market": market
            }

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 120,
        "seed": 42
    },
    debug=True
)

env.run([carrot_agent, "random"])

final = env.steps[-1]

for i, s in enumerate(final):
    print(
        f"Player {i}: "
        f"reward={s.reward}, "
        f"money={s.observation['farms'][i]['money']}, "
        f"status={s.status}"
    )

{'x': 0, 'y': 0, 'crop': 'WHEAT', 'yield': 1, 'watered': True}

[(0, 0, "WHEAT", 1), ...]

plants = []

for y, row in enumerate(farm["tiles"]):
    for x, tile in enumerate(row):

        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            plants.append((x, y, tile))

print("Number of plants:", len(plants))
print("First 3 plants:")

for item in plants[:3]:
    print(item)

obs = env.steps[-1][0].observation

player = obs["player"]
farm = obs["farms"][player]

print("Player:", player)
print("Day:", obs["day"])
print("Hour:", obs["hour"])
print("Money:", farm["money"])

plants = []

for y, row in enumerate(farm["tiles"]):
    for x, tile in enumerate(row):

        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            plants.append((x, y, tile))

print("Number of plants:", len(plants))

for x, y, plant in plants:
    print(
        x,
        y,
        plant.get("crop"),
        "yield =", plant.get("yield_units"),
        "watered =", plant.get("watered_today"),
        "planted_day =", plant.get("planted_day")
    )

obs = env.steps[-1][0].observation

farm = obs["farms"][0]

(x, y, plant)

for step in range(len(env.steps)):

    obs = env.steps[step][0].observation

    day = obs["day"]
    hour = obs["hour"]

    farm = obs["farms"][0]

    plants = []

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):

            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                plants.append(
                    (
                        x,
                        y,
                        tile.get("crop"),
                        tile.get("planted_day")
                    )
                )

    if plants:
        print(
            f"step={step:3d} "
            f"day={day} "
            f"hour={hour} "
            f"plants={plants}"
        )

for step in range(len(env.steps)):
    obs = env.steps[step][0].observation

    day = obs["day"]
    hour = obs["hour"]
    farm = obs["farms"][0]

    plants = []

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                plants.append(
                    (x, y, tile.get("crop"), tile.get("planted_day"))
                )

    if plants:
        print(
            f"step={step:3d} "
            f"day={day} "
            f"hour={hour} "
            f"plants={plants}"
        )