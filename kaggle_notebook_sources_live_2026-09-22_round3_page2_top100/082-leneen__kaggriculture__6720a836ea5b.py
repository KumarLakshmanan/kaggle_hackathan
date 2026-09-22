%%writefile submission.py

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS


# ============================================================
# BALANCED FARMER v1
# ============================================================
#
# Strategy:
#   - Wheat = stable cash flow + future animal feed
#   - Melon = high-value cash crop
#   - Water all crops
#   - Harvest mature crops
#   - Sell wheat readily
#   - Sell melons only when price is attractive
#   - Buy seeds when needed
#   - Hire one farm hand once the farm becomes sufficiently busy
#   - Expand land when cash reserves are sufficiently large
#   - No animals or fertilizer in v1
#
# This is intended to be a simple BASELINE, not an optimized agent.
# ============================================================


# -----------------------------
# Crop constants
# -----------------------------

WHEAT_SEED_COST = CROPS["WHEAT"]["seed"]
MELON_SEED_COST = CROPS["MELON"]["seed"]

WHEAT_MAX_YIELD_DAY = CROPS["WHEAT"]["max_yield_day"]
MELON_MAX_YIELD_DAY = CROPS["MELON"]["max_yield_day"]


# -----------------------------
# Simple economic parameters
# -----------------------------

# Melon is valuable, but its price can crash when we sell too much.
MELON_SELL_THRESHOLD = 200

# Sell melons in batches rather than dumping the whole inventory.
MELON_SELL_BATCH = 5

# Wheat is primarily a cash-flow crop in this version.
WHEAT_SELL_THRESHOLD = 25

# Keep some cash available rather than spending everything.
MIN_CASH_RESERVE = 500

# Start hiring once enough crops exist that one farmer becomes inefficient.
HIRE_PLANT_THRESHOLD = 15

# Simple land-expansion thresholds.
LAND_BUY_THRESHOLDS = {
    "NE": 4000,
    "SW": 8000,
    "SE": 12000,
}


# ============================================================
# Utility functions
# ============================================================

def _step_toward(fx, fy, tx, ty):
    """
    Return one movement action that moves the farmer toward
    the target tile using Manhattan distance.
    """

    if fx > tx:
        return "WEST"

    if fx < tx:
        return "EAST"

    if fy > ty:
        return "NORTH"

    if fy < ty:
        return "SOUTH"

    return None


def _manhattan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def _count_plants(farm):
    """
    Count all active plants on the farm.
    """

    count = 0
    board_size = len(farm["tiles"])

    for y in range(board_size):
        for x in range(board_size):

            tile = farm["tiles"][y][x]

            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                count += 1

    return count


def _count_empty_tiles(farm):
    """
    Count unlocked empty tiles.
    """

    count = 0
    board_size = len(farm["tiles"])

    for y in range(board_size):
        for x in range(board_size):

            tile = farm["tiles"][y][x]

            if tile is None:
                count += 1

    return count


def _find_nearest_target(farm, target_types, fx, fy):
    """
    Find the nearest tile whose (x, y, purpose) is one of
    the requested target types.

    target_types example:
        {"WATER", "HARVEST", "PLANT_WHEAT"}
    """

    board_size = len(farm["tiles"])
    candidates = []

    for y in range(board_size):
        for x in range(board_size):

            tile = farm["tiles"][y][x]

            # --------------------------------------------
            # Plants
            # --------------------------------------------

            if isinstance(tile, dict) and tile.get("kind") == "PLANT":

                crop = tile.get("crop")

                # Watering has high priority.
                if (
                    "WATER" in target_types
                    and not tile.get("watered_today", False)
                ):
                    candidates.append(
                        (
                            _manhattan_distance(fx, fy, x, y),
                            0,
                            x,
                            y,
                            "WATER",
                        )
                    )

                # Harvest wheat when mature.
                if (
                    "HARVEST_WHEAT" in target_types
                    and crop == "WHEAT"
                    and tile.get("yield_units", 0) > 0
                ):
                    candidates.append(
                        (
                            _manhattan_distance(fx, fy, x, y),
                            1,
                            x,
                            y,
                            "HARVEST",
                        )
                    )

                # Harvest melon when mature.
                if (
                    "HARVEST_MELON" in target_types
                    and crop == "MELON"
                    and tile.get("yield_units", 0) > 0
                ):
                    candidates.append(
                        (
                            _manhattan_distance(fx, fy, x, y),
                            1,
                            x,
                            y,
                            "HARVEST",
                        )
                    )

            # --------------------------------------------
            # Empty tile
            # --------------------------------------------

            elif tile is None:

                if "PLANT_WHEAT" in target_types:
                    candidates.append(
                        (
                            _manhattan_distance(fx, fy, x, y),
                            2,
                            x,
                            y,
                            "PLANT_WHEAT",
                        )
                    )

                if "PLANT_MELON" in target_types:
                    candidates.append(
                        (
                            _manhattan_distance(fx, fy, x, y),
                            2,
                            x,
                            y,
                            "PLANT_MELON",
                        )
                    )

    if not candidates:
        return None

    # First minimize distance, then action priority.
    candidates.sort(key=lambda z: (z[0], z[1]))

    return candidates[0]


def _find_best_farming_target(farm, seeds, fx, fy):
    """
    Decide what the farmer should work on next.

    Priority:
        1. Water plants
        2. Harvest mature crops
        3. Plant melon
        4. Plant wheat
    """

    # ----------------------------------------------------
    # 1. Water first.
    # ----------------------------------------------------

    target = _find_nearest_target(
        farm,
        {"WATER"},
        fx,
        fy,
    )

    if target:
        return target

    # ----------------------------------------------------
    # 2. Harvest mature wheat.
    # ----------------------------------------------------

    target = _find_nearest_target(
        farm,
        {"HARVEST_WHEAT"},
        fx,
        fy,
    )

    if target:
        return target

    # ----------------------------------------------------
    # 3. Harvest mature melon.
    # ----------------------------------------------------

    target = _find_nearest_target(
        farm,
        {"HARVEST_MELON"},
        fx,
        fy,
    )

    if target:
        return target

    # ----------------------------------------------------
    # 4. Plant melon.
    #
    # Melon gets preference because it is our high-value
    # cash crop.
    # ----------------------------------------------------

    if seeds.get("MELON", 0) > 0:

        target = _find_nearest_target(
            farm,
            {"PLANT_MELON"},
            fx,
            fy,
        )

        if target:
            return target

    # ----------------------------------------------------
    # 5. Plant wheat.
    # ----------------------------------------------------

    if seeds.get("WHEAT", 0) > 0:

        target = _find_nearest_target(
            farm,
            {"PLANT_WHEAT"},
            fx,
            fy,
        )

        if target:
            return target

    return None


# ============================================================
# Market management
# ============================================================

def _market_actions(obs, farm, private):
    """
    Decide what market orders to submit.

    Strategy:

    Wheat:
        Sell when the market is at or above its normal price.

    Melon:
        Sell only when price >= $200.
        Never dump the entire melon inventory at once.

    Seeds:
        Maintain a small supply of both wheat and melon.
    """

    market = []

    money = farm.get("money", 0)

    seeds = private.get("seeds", {})
    shed = private.get("shed", {})

    prices = (obs.get("market", {}) or {}).get("prices", {})

    wheat_price = prices.get("WHEAT", 0)
    melon_price = prices.get("MELON", 0)

    # --------------------------------------------------------
    # Sell wheat.
    #
    # Wheat is our stable cash-flow resource.
    # --------------------------------------------------------

    wheat_in_shed = shed.get("WHEAT", 0)

    if wheat_in_shed > 0 and wheat_price >= WHEAT_SELL_THRESHOLD:

        market.append(
            ["SELL", "WHEAT", wheat_in_shed]
        )

    # --------------------------------------------------------
    # Sell melon.
    #
    # Only sell a limited batch so that we don't intentionally
    # crash the market.
    # --------------------------------------------------------

    melon_in_shed = shed.get("MELON", 0)

    if melon_in_shed > 0 and melon_price >= MELON_SELL_THRESHOLD:

        sell_amount = min(
            melon_in_shed,
            MELON_SELL_BATCH,
        )

        market.append(
            ["SELL", "MELON", sell_amount]
        )

    # --------------------------------------------------------
    # Buy seeds.
    #
    # Maintain a small working supply rather than buying huge
    # quantities.
    # --------------------------------------------------------

    reserve_cash = MIN_CASH_RESERVE

    # Buy wheat seed when none are available.
    if (
        seeds.get("WHEAT", 0) == 0
        and money >= WHEAT_SEED_COST + reserve_cash
    ):
        market.append(
            ["BUY_SEED", "WHEAT", 1]
        )

    # Buy melon seed when none are available.
    if (
        seeds.get("MELON", 0) == 0
        and money >= MELON_SEED_COST + reserve_cash
    ):
        market.append(
            ["BUY_SEED", "MELON", 1]
        )

    return market


# ============================================================
# Land expansion
# ============================================================

def _land_actions(farm):
    """
    Buy land when the farm has accumulated enough cash.

    We only buy one quadrant at a time.
    """

    money = farm.get("money", 0)

    unlocked = set(
        farm.get("unlocked_quadrants", [])
    )

    orders = []

    # --------------------------------------------------------
    # NE
    # --------------------------------------------------------

    if (
        "NE" not in unlocked
        and money >= LAND_BUY_THRESHOLDS["NE"]
    ):
        orders.append(
            ["BUY_LAND", "NE"]
        )

    # --------------------------------------------------------
    # SW
    # --------------------------------------------------------

    elif (
        "SW" not in unlocked
        and money >= LAND_BUY_THRESHOLDS["SW"]
    ):
        orders.append(
            ["BUY_LAND", "SW"]
        )

    # --------------------------------------------------------
    # SE
    # --------------------------------------------------------

    elif (
        "SE" not in unlocked
        and money >= LAND_BUY_THRESHOLDS["SE"]
    ):
        orders.append(
            ["BUY_LAND", "SE"]
        )

    return orders


# ============================================================
# Farm-hand management
# ============================================================

def _should_hire(farm):
    """
    Hire one farm hand once the farm becomes sufficiently busy.

    We deliberately limit the baseline to ONE hand.
    """

    plants = _count_plants(farm)

    hires_today = farm.get("hires_today", 0)

    if hires_today >= 1:
        return False

    if plants >= HIRE_PLANT_THRESHOLD:
        return True

    return False


# ============================================================
# Farm-hand behavior
# ============================================================

def _hand_action(obs, farm, private, hand_index):
    """
    Simple farm-hand behavior.

    The hand primarily maintains plants.

    The baseline does not attempt sophisticated multi-agent
    task allocation.
    """

    hands = farm.get("hands", [])

    if hand_index >= len(hands):
        return ["PASS"]

    hx, hy = hands[hand_index]

    target = _find_nearest_target(
        farm,
        {"WATER", "HARVEST_WHEAT", "HARVEST_MELON"},
        hx,
        hy,
    )

    if not target:
        return ["PASS"]

    _, _, tx, ty, purpose = target

    # Already standing on target.
    if hx == tx and hy == ty:

        if purpose == "WATER":
            return ["WATER"]

        if purpose == "HARVEST":
            return ["HARVEST"]

    # Move toward target.
    step = _step_toward(
        hx,
        hy,
        tx,
        ty,
    )

    if step:
        return [step]

    return ["PASS"]


# ============================================================
# Main agent
# ============================================================

def balanced_farmer(obs):
    """
    Balanced Farmer v1.

    This is the baseline agent.
    """

    farms = obs.get("farms", [])

    player = obs.get("player", 0)

    private = obs.get("private", {}) or {}

    # --------------------------------------------------------
    # Safety check.
    # --------------------------------------------------------

    if not farms or player >= len(farms):

        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [],
        }

    farm = farms[player]

    board_size = len(
        farm.get("tiles", [])
    )

    if board_size == 0:

        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [],
        }

    # --------------------------------------------------------
    # Current farmer position.
    # --------------------------------------------------------

    fx, fy = farm.get(
        "farmer",
        [0, 0],
    )

    tile = farm["tiles"][fy][fx]

    seeds = private.get(
        "seeds",
        {},
    )

    day = obs.get(
        "day",
        0,
    )

    # --------------------------------------------------------
    # Market orders.
    # --------------------------------------------------------

    market = _market_actions(
        obs,
        farm,
        private,
    )

    # --------------------------------------------------------
    # Land expansion.
    # --------------------------------------------------------

    market.extend(
        _land_actions(farm)
    )

    # --------------------------------------------------------
    # Hire one farm hand when the farm is sufficiently busy.
    # --------------------------------------------------------

    if _should_hire(farm):

        market.append(
            ["HIRE"]
        )

    # --------------------------------------------------------
    # Farmer action.
    # --------------------------------------------------------

    farmer = ["PASS"]

    # ========================================================
    # If standing on a plant
    # ========================================================

    if (
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
    ):

        crop = tile.get("crop")

        planted_day = tile.get(
            "planted_day",
            day,
        )

        age = day - planted_day

        # ----------------------------------------------------
        # Water immediately if needed.
        # ----------------------------------------------------

        if not tile.get(
            "watered_today",
            False,
        ):

            farmer = ["WATER"]

        # ----------------------------------------------------
        # Harvest wheat when mature.
        # ----------------------------------------------------

        elif (
            crop == "WHEAT"
            and age >= WHEAT_MAX_YIELD_DAY
            and tile.get("yield_units", 0) > 0
        ):

            farmer = ["HARVEST"]

        # ----------------------------------------------------
        # Harvest melon when mature.
        # ----------------------------------------------------

        elif (
            crop == "MELON"
            and age >= MELON_MAX_YIELD_DAY
            and tile.get("yield_units", 0) > 0
        ):

            farmer = ["HARVEST"]

        # ----------------------------------------------------
        # Otherwise move toward another useful tile.
        # ----------------------------------------------------

        else:

            target = _find_best_farming_target(
                farm,
                seeds,
                fx,
                fy,
            )

            if target:

                _, _, tx, ty, purpose = target

                step = _step_toward(
                    fx,
                    fy,
                    tx,
                    ty,
                )

                if step:
                    farmer = [step]

    # ========================================================
    # If standing on an empty tile
    # ========================================================

    elif tile is None:

        # Prefer melon when a melon seed is available.
        if seeds.get("MELON", 0) > 0:

            farmer = [
                "PLANT",
                "MELON",
            ]

        elif seeds.get("WHEAT", 0) > 0:

            farmer = [
                "PLANT",
                "WHEAT",
            ]

        else:

            target = _find_best_farming_target(
                farm,
                seeds,
                fx,
                fy,
            )

            if target:

                _, _, tx, ty, purpose = target

                step = _step_toward(
                    fx,
                    fy,
                    tx,
                    ty,
                )

                if step:
                    farmer = [step]

    # ========================================================
    # If standing on a weed or structure
    # ========================================================

    else:

        target = _find_best_farming_target(
            farm,
            seeds,
            fx,
            fy,
        )

        if target:

            _, _, tx, ty, purpose = target

            step = _step_toward(
                fx,
                fy,
                tx,
                ty,
            )

            if step:
                farmer = [step]

    # --------------------------------------------------------
    # Farm hands.
    # --------------------------------------------------------

    hands = []

    active_hands = farm.get(
        "hands",
        [],
    )

    for i in range(len(active_hands)):

        action = _hand_action(
            obs,
            farm,
            private,
            i,
        )

        hands.append(action)

    # --------------------------------------------------------
    # Return complete action.
    # --------------------------------------------------------

    return {
        "farmer": farmer,
        "hands": hands,
        "market": market,
    }


# ============================================================
# Kaggle entry point
# ============================================================

def agent(obs):
    return balanced_farmer(obs)