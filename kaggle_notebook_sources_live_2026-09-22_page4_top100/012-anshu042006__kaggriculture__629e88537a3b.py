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

from collections import deque





# ============================================================
# CONFIG
# ============================================================

CROP_INFO = {
    "WHEAT": {
        "seed_cost": 10,
        "harvest_day": 4,
        "max_yield": 4,
        "sell_threshold": 20,
    },
    "CARROT": {
        "seed_cost": 20,
        "harvest_day": 3,
        "max_yield": 3,
        "sell_threshold": 25,
    },
    "TOMATO": {
        "seed_cost": 50,
        "harvest_day": 8,
        "max_yield": 4,
        "sell_threshold": 45,
    },
    "STRAWBERRY": {
        "seed_cost": 100,
        "harvest_day": 10,
        "max_yield": 4,
        "sell_threshold": 100,
    },
    "MELON": {
        "seed_cost": 80,
        "harvest_day": 10,
        "max_yield": 6,
        "sell_threshold": 180,
    },
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def distance(a, b):
    """Manhattan distance."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_tiles(farm):
    """
    Return all useful tiles on the farm.
    """
    plants = []
    empty = []
    weeds = []
    structures = []

    tiles = farm["tiles"]

    for y in range(len(tiles)):
        for x in range(len(tiles[y])):

            tile = tiles[y][x]

            if tile == "LOCKED":
                continue

            pos = (x, y)

            if tile is None:
                empty.append(pos)

            elif isinstance(tile, dict):

                kind = tile.get("kind")

                if kind == "PLANT":
                    plants.append((pos, tile))

                elif kind == "WEED":
                    weeds.append(pos)

                else:
                    structures.append((pos, tile))

    return plants, empty, weeds, structures


def get_current_tile(farm, position):
    x, y = position
    return farm["tiles"][y][x]


# ============================================================
# MOVEMENT
# ============================================================

def move_towards(current, target):
    """
    Return one movement action that gets us closer
    to the target.
    """

    if current == target:
        return ["PASS"]

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

    return ["PASS"]


# ============================================================
# FIND BEST PLANT TO WORK ON
# ============================================================

def choose_plant(farm, farmer_position):
    plants, _, _, _ = find_tiles(farm)

    if not plants:
        return None

    best = None
    best_score = -10**9

    for pos, plant in plants:

        score = 0

        crop = plant.get("crop")
        age = 0

        # Prefer plants that need water
        if not plant.get("watered_today", False):
            score += 100

        # Prefer mature plants
        if crop in CROP_INFO:
            # planted_day is handled by caller when possible
            score += CROP_INFO[crop]["seed_cost"]

        # Prefer nearby plants
        score -= distance(farmer_position, pos)

        if score > best_score:
            best_score = score
            best = (pos, plant)

    return best


# ============================================================
# MARKET MANAGEMENT
# ============================================================

def market_actions(obs, farm, private):

    orders = []

    money = farm["money"]
    prices = obs["market"]["prices"]
    shed = private["shed"]
    seeds = private["seeds"]

    # --------------------------------------------------------
    # SELL HARVESTED PRODUCTS
    # --------------------------------------------------------

    for crop in CROP_INFO:

        amount = shed.get(crop, 0)

        if amount <= 0:
            continue

        price = prices.get(crop, 0)
        threshold = CROP_INFO[crop]["sell_threshold"]

        # Don't dump premium products at terrible prices.
        if price >= threshold:

            # Avoid unnecessarily huge market dumps.
            sell_amount = min(amount, 20)

            orders.append([
                "SELL",
                crop,
                sell_amount
            ])

    # --------------------------------------------------------
    # BUY SEEDS
    # --------------------------------------------------------

    # Early game: prioritize melon.
    melon_seeds = seeds.get("MELON", 0)

    if melon_seeds == 0 and money >= 80:
        orders.append([
            "BUY_SEED",
            "MELON",
            1
        ])

    # If we don't have melon and money is low,
    # buy cheap wheat as backup.
    elif melon_seeds == 0 and money >= 10:

        wheat_seeds = seeds.get("WHEAT", 0)

        if wheat_seeds == 0:
            orders.append([
                "BUY_SEED",
                "WHEAT",
                1
            ])

    return orders


# ============================================================
# FARMER LOGIC
# ============================================================

def farmer_action(obs):

    player = obs["player"]

    farm = obs["farms"][player]
    private = obs["private"]

    farmer_position = tuple(farm["farmer"])

    plants, empty, weeds, structures = find_tiles(farm)

    current_tile = get_current_tile(
        farm,
        farmer_position
    )

    # --------------------------------------------------------
    # 1. HANDLE CURRENT PLANT
    # --------------------------------------------------------

    if isinstance(current_tile, dict):

        if current_tile.get("kind") == "PLANT":

            crop = current_tile.get("crop")

            # Water first.
            if not current_tile.get("watered_today", False):
                return ["WATER"]

            # Harvest based on crop age.
            planted_day = current_tile.get(
                "planted_day",
                obs["day"]
            )

            age = obs["day"] - planted_day

            if crop == "MELON" and age >= 10:
                return ["HARVEST"]

            if crop == "WHEAT" and age >= 4:
                return ["HARVEST"]

            if crop == "CARROT" and age >= 3:
                return ["HARVEST"]

            if crop == "TOMATO" and age >= 11:
                return ["HARVEST"]

            if crop == "STRAWBERRY" and age >= 16:
                return ["HARVEST"]

            return ["PASS"]

        # ----------------------------------------------------
        # 2. REMOVE WEED
        # ----------------------------------------------------

        if current_tile.get("kind") == "WEED":
            return ["DIG"]

    # --------------------------------------------------------
    # 3. FIND PLANT THAT NEEDS WATER
    # --------------------------------------------------------

    nearest = None
    nearest_distance = 10**9

    for pos, plant in plants:

        if not plant.get("watered_today", False):

            d = distance(
                farmer_position,
                pos
            )

            if d < nearest_distance:
                nearest_distance = d
                nearest = pos

    if nearest is not None:

        if farmer_position != nearest:
            return move_towards(
                farmer_position,
                nearest
            )

    # --------------------------------------------------------
    # 4. FIND MATURE PLANT
    # --------------------------------------------------------

    nearest = None
    nearest_distance = 10**9

    for pos, plant in plants:

        crop = plant.get("crop")

        planted_day = plant.get(
            "planted_day",
            obs["day"]
        )

        age = obs["day"] - planted_day

        mature = False

        if crop == "MELON" and age >= 10:
            mature = True

        elif crop == "WHEAT" and age >= 4:
            mature = True

        elif crop == "CARROT" and age >= 3:
            mature = True

        elif crop == "TOMATO" and age >= 11:
            mature = True

        elif crop == "STRAWBERRY" and age >= 16:
            mature = True

        if mature:

            d = distance(
                farmer_position,
                pos
            )

            if d < nearest_distance:
                nearest_distance = d
                nearest = pos

    if nearest is not None:

        if farmer_position != nearest:
            return move_towards(
                farmer_position,
                nearest
            )

    # --------------------------------------------------------
    # 5. PLANT MELON ON EMPTY TILE
    # --------------------------------------------------------

    melon_seeds = private["seeds"].get(
        "MELON",
        0
    )

    if melon_seeds > 0:

        if current_tile is None:
            return ["PLANT", "MELON"]

        if empty:

            target = min(
                empty,
                key=lambda p: distance(
                    farmer_position,
                    p
                )
            )

            return move_towards(
                farmer_position,
                target
            )

    # --------------------------------------------------------
    # 6. REMOVE NEARBY WEED
    # --------------------------------------------------------

    if weeds:

        target = min(
            weeds,
            key=lambda p: distance(
                farmer_position,
                p
            )
        )

        if farmer_position != target:
            return move_towards(
                farmer_position,
                target
            )

    return ["PASS"]


# ============================================================
# MAIN AGENT
# ============================================================

def agent(obs):

    player = obs["player"]

    farm = obs["farms"][player]

    private = obs["private"]

    # Market decisions
    market = market_actions(
        obs,
        farm,
        private
    )

    # Main farmer
    farmer = farmer_action(obs)

    # V1 doesn't use hired hands yet.
    hands = []

    return {
        "farmer": farmer,
        "hands": hands,
        "market": market
    }

def agent(obs):

    # Get player
    player = obs["player"]

    # Get farm and private information
    farm = obs["farms"][player]
    private = obs["private"]

    # Decide farmer action
    farmer = farmer_action(obs)

    # Decide market actions
    market = market_actions(
        obs,
        farm,
        private
    )

    # No hired hands in V1
    hands = []

    return {
        "farmer": farmer,
        "hands": hands,
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

result = env.run([
    agent,
    "random"
])

print("Game completed!")
print(result[-1])

