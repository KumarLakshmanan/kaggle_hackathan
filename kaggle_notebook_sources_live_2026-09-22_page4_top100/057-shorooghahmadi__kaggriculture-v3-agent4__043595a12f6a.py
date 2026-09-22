import sys, subprocess
try:
    import kaggle_environments  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'kaggle-environments'], check=True)

import pandas as pd
import matplotlib.pyplot as plt
from kaggle_environments import make


AGENT_V1_SOURCE = r'''
"""Original Kaggriculture agent.

Strategy (own design, built from the public game rules only — no other
player's episode data is used anywhere in this file):

- The farm is split into role slots: the first 3 tiles of the NW quadrant
  are reserved for animal structures (goose coop, cow pasture, sheep
  pasture); every other unlocked tile is a crop slot cycling through a
  profitability-weighted rotation of wheat / carrot / melon / strawberry /
  tomato.
- The farmer is a dedicated "rancher": it builds structures, ferries wheat
  and fertilizer from the shed, feeds/cares/harvests the three animals, and
  drops what it's carrying back at the shed.
- Each hired hand owns one crop tile: plant -> water -> harvest, timed so
  one-time crops are harvested right when they hit peak yield (or
  immediately if they've entered decay) and ongoing crops are harvested
  the moment produce is ready.
- Market orders each turn (capped at 10): throttled sells (so a big shed
  balance doesn't crash a thin-inventory item like strawberry/melon/wool in
  one shot), opportunistic hiring while it's still cheap, land purchases
  once cash allows, and seed/animal restocking exactly when a slot needs it.
"""

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP"},
    "COW":   {"cost": 400, "structure": "PASTURE"},
    "SHEEP": {"cost": 500, "structure": "PASTURE"},
}

# T (24-day production capacity) per product, used only to size a sane
# per-turn sell throttle so we don't dump a whole shed into a thin market.
SELL_CAP = {
    "WHEAT": 40, "CARROT": 45, "TOMATO": 20, "STRAWBERRY": 10, "MELON": 30,
    "EGG": 33, "MILK": 12, "WOOL": 10,
}
SELL_ORDER = ["MELON", "STRAWBERRY", "WOOL", "MILK", "TOMATO", "EGG", "CARROT", "WHEAT"]

CROP_ROTATION = ["WHEAT", "MELON", "CARROT", "STRAWBERRY", "MELON", "TOMATO", "WHEAT", "CARROT"]
QUAD_ORDER = ["NW", "NE", "SW", "SE"]
LAND_PRICES = {"NE": 1000, "SW": 2000, "SE": 4000}
FERTILIZER_RESERVE = 6
MAX_ORDERS = 10
MAX_HANDS = 10
HIRE_MONEY_BUFFER = 60
HIRE_COST_CAP = 60
HIRE_BURST_CAP = 7
ANIMAL_MIN_CASH = 1200
ANIMAL_MIN_LEFTOVER = 400
SEASON_DAYS = 30
LAND_CUTOFF_DAY = 22          # no point unlocking land we can't put to work
ANIMAL_CUTOFF_DAY = 20        # animals need days to build+grow+pay back
FERTILIZER_LIQUIDATE_DAY = 26  # stop hoarding fertilizer near the end
LIQUIDATE_DAY = 28             # dump the whole shed, no throttling, near the end


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _step_toward(pos, target):
    x, y = pos
    tx, ty = target
    if x == tx and y == ty:
        return None
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    return ["NORTH"]


def _quadrant_tiles(half):
    return {
        "NW": [(x, y) for y in range(half) for x in range(half)],
        "NE": [(x, y) for y in range(half) for x in range(half, 2 * half)],
        "SW": [(x, y) for y in range(half, 2 * half) for x in range(half)],
        "SE": [(x, y) for y in range(half, 2 * half) for x in range(half, 2 * half)],
    }


def _home_tiles(unlocked, board_size):
    half = board_size // 2
    quads = _quadrant_tiles(half)
    tiles = []
    for q in QUAD_ORDER:
        if q in unlocked:
            tiles.extend(quads[q])
    return tiles


def _shed_tiles(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def _crop_action(pos, home_tile, crop, tiles, seeds, day):
    if pos != home_tile:
        return _step_toward(pos, home_tile) or ["PASS"]
    tx, ty = home_tile
    tile = tiles[ty][tx]
    if tile is None:
        if seeds.get(crop, 0) > 0:
            return ["PLANT", crop]
        return ["PASS"]
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return ["DIG"]
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        cd = CROPS.get(tile["crop"])
        if cd is None:
            return ["PASS"]
        age = day - tile["planted_day"]
        if cd["ongoing"]:
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            if not tile["watered_today"]:
                return ["WATER"]
            return ["PASS"]
        # one-time crop
        if age > cd["max_yield_day"]:
            # in decay: grab whatever is left immediately, or clear the tile
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            return ["DIG"]
        if age >= cd["max_yield_day"] and tile.get("yield_units", 0) > 0:
            return ["HARVEST"]
        if not tile["watered_today"]:
            return ["WATER"]
        return ["PASS"]
    return ["PASS"]


def _rancher_action(pos, inv, shed, tiles, animal_slots, board_size):
    shed_tiles = _shed_tiles(board_size)
    nearest_shed = min(shed_tiles, key=lambda t: _dist(pos, t))
    needs = []  # (priority, target_coord_or_None_for_shed, action)
    for coord, animal in animal_slots:
        tx, ty = coord
        tile = tiles[ty][tx]
        if tile is None:
            build_op = "BUILD_COOP" if animal == "GOOSE" else "BUILD_PASTURE"
            needs.append((0, coord, [build_op]))
            continue
        if not isinstance(tile, dict):
            continue
        if "animal" not in tile:
            if inv.get(animal, 0) > 0:
                needs.append((1, coord, ["PLACE", animal]))
            elif shed.get(animal, 0) > 0:
                needs.append((1, None, ["PICKUP", animal, 1]))
            continue
        if not tile["fed_today"]:
            if inv.get("WHEAT", 0) > 0:
                needs.append((2, coord, ["FEED"]))
            elif shed.get("WHEAT", 0) > 0:
                needs.append((2, None, ["PICKUP", "WHEAT", 6]))
        if tile.get("yield_units", 0) > 0:
            needs.append((3, coord, ["HARVEST"]))
        if tile.get("fertilizer_available"):
            needs.append((4, coord, ["COLLECT_FERTILIZER"]))
        if not tile.get("cared_today"):
            needs.append((5, coord, ["CARE"]))

    if not needs:
        if inv:
            if pos in shed_tiles:
                return ["DROP"]
            return _step_toward(pos, nearest_shed) or ["PASS"]
        return ["PASS"]

    needs.sort(key=lambda n: (n[0], _dist(pos, n[1] if n[1] is not None else nearest_shed)))
    _, target, action = needs[0]
    target_coord = nearest_shed if target is None else target
    if pos != target_coord:
        return _step_toward(pos, target_coord) or ["PASS"]
    return action


def agent(obs):
    player = obs["player"]
    day = obs["day"]
    hour = obs["hour"]
    farms = obs["farms"]
    me = farms[player]
    private = obs["private"]
    tiles = me["tiles"]
    board_size = len(tiles)
    shed = private["shed"]
    seeds = private["seeds"]
    inventories = private["inventories"]
    money = me["money"]

    home = _home_tiles(me["unlocked_quadrants"], board_size)
    animal_slots = list(zip(home[:3], ["GOOSE", "COW", "SHEEP"]))
    crop_tiles = home[3:]

    farmer_pos = tuple(me["farmer"])
    hand_positions = [tuple(h) for h in me["hands"]]

    orders = []

    def add(order):
        if len(orders) < MAX_ORDERS:
            orders.append(order)

    # --- sells (throttled per item so we don't crash thin markets; near the
    # end of the season we drop the throttle and liquidate everything) -----
    liquidating = day >= LIQUIDATE_DAY
    for item in SELL_ORDER:
        qty = shed.get(item, 0)
        if qty <= 0:
            continue
        cap = qty if liquidating else SELL_CAP.get(item, 20)
        add(["SELL", item, min(qty, cap)])
    fert_reserve = 0 if day >= FERTILIZER_LIQUIDATE_DAY else FERTILIZER_RESERVE
    if shed.get("FERTILIZER", 0) > fert_reserve:
        add(["SELL", "FERTILIZER", shed["FERTILIZER"] - fert_reserve])

    # --- hire: burst-hire right at the start of the day so hands get a
    # full day's work instead of trickling in one per turn -----------------
    wanted_hands = min(MAX_HANDS, max(1, len(crop_tiles)))
    if hour == 0:
        n = me["hires_today"]
        projected_money = money
        hired_this_turn = 0
        while (
            len(hand_positions) + hired_this_turn < wanted_hands
            and hired_this_turn < HIRE_BURST_CAP
            and len(orders) < MAX_ORDERS
        ):
            cost = _fib(n)
            if cost > HIRE_COST_CAP or projected_money - HIRE_MONEY_BUFFER < cost:
                break
            add(["HIRE"])
            projected_money -= cost
            n += 1
            hired_this_turn += 1

    # --- land purchase once cash is comfortably ahead (only while there's
    # enough season left to make use of the new tiles) ---------------------
    if day <= LAND_CUTOFF_DAY:
        for q in QUAD_ORDER[1:]:
            if q not in me["unlocked_quadrants"]:
                price = LAND_PRICES[q]
                if money >= price * 1.6:
                    add(["BUY_LAND"])
                break

    # --- seed restocking: only for tiles an actual hand is working --------
    needed_crops = set()
    active_tiles = min(len(crop_tiles), max(len(hand_positions), 1))
    for i, coord in enumerate(crop_tiles[:active_tiles]):
        cx, cy = coord
        if tiles[cy][cx] is None:
            crop = CROP_ROTATION[i % len(CROP_ROTATION)]
            if seeds.get(crop, 0) == 0:
                needed_crops.add(crop)
    for crop in needed_crops:
        cost = CROPS[crop]["seed"]
        if money >= cost * 1.2:
            add(["BUY_SEED", crop, 1])

    # --- animal restocking (skip once too little season remains to pay off
    # the purchase) ----------------------------------------------------
    if day <= ANIMAL_CUTOFF_DAY:
        for coord, animal in animal_slots:
            cx, cy = coord
            tile = tiles[cy][cx]
            has_structure = isinstance(tile, dict)
            has_animal = has_structure and "animal" in tile
            if has_structure and not has_animal and shed.get(animal, 0) == 0:
                cost = ANIMALS[animal]["cost"]
                if money >= max(ANIMAL_MIN_CASH, cost * 1.3) and money - cost >= ANIMAL_MIN_LEFTOVER:
                    add(["BUY_ANIMAL", animal, 1])
                    money -= cost  # reserve so we don't queue three buys in one turn

    # --- unit actions --------------------------------------------------
    farmer_inv = inventories[0] if inventories else {}
    farmer_action = _rancher_action(farmer_pos, farmer_inv, shed, tiles, animal_slots, board_size)

    hand_actions = []
    for i, pos in enumerate(hand_positions):
        if i < len(crop_tiles):
            coord = crop_tiles[i]
            crop = CROP_ROTATION[i % len(CROP_ROTATION)]
            hand_actions.append(_crop_action(pos, coord, crop, tiles, seeds, day))
        else:
            hand_actions.append(["PASS"])

    return {"farmer": farmer_action, "hands": hand_actions, "market": orders[:MAX_ORDERS]}
'''
AGENT_V2_SOURCE = r'''
"""Original Kaggriculture agent (v2).

Strategy (own design, built from the public game rules only — no other
player's episode data is used anywhere in this file):

- The farm is split into role slots: the first 3 tiles of the NW quadrant
  are reserved for animal structures (goose coop, cow pasture, sheep
  pasture); every other unlocked tile is a crop slot. Each empty crop slot
  picks whichever crop currently has the best $/day given the *live*
  market price (obs.market.prices) and how many of that crop are already
  growing elsewhere on the farm (so the farm doesn't dump every hand into
  one crop and crash its own market), instead of a fixed rotation.
- Wheat and carrot tiles get a one-shot FERTILIZE right at the start of
  their watering-bonus window: the engine doubles the per-watered-day
  yield bonus while a tile is fertilized, and for these two crops that
  bonus window is short enough that fertilizer measurably raises the cap
  (melon's window is already long enough to hit its cap unfertilized, so
  it's skipped — verified against the engine's yield formula, not
  guessed).
- Ongoing crops (tomato/strawberry) have a *finite* total production run
  in this engine — after enough days_since_first_yield they stop
  accumulating any new yield forever, even though the tile still looks
  like a healthy plant. Once a tile's ongoing crop is provably exhausted
  (no yield left to collect and no more coming), the hand digs it up and
  replants instead of tending a dead tile for the rest of the season.
- The farmer is a dedicated "rancher": it builds structures, ferries wheat
  and fertilizer from the shed, feeds/cares/harvests the three animals, and
  drops what it's carrying back at the shed.
- Market orders each turn (capped at 10): throttled sells (so a big shed
  balance doesn't crash a thin-inventory item like strawberry/melon/wool in
  one shot), opportunistic hiring while it's still cheap, land purchases
  once cash allows, and seed/fertilizer/animal restocking exactly when a
  slot needs it.
"""

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

# Crops whose watering-bonus window is short enough that a fertilizer
# (doubles the per-watered-day bonus for 3 days) actually raises the
# achievable yield above what plain watering alone reaches. Checked by hand
# against the engine's window formula: window = [(max_yield_day+1)//2 ..
# max_yield_day]; melon's window is long enough to hit its cap unfertilized,
# so fertilizing it is wasted fertilizer.
FERTILIZE_WORTHY = {"WHEAT", "CARROT"}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP"},
    "COW":   {"cost": 400, "structure": "PASTURE"},
    "SHEEP": {"cost": 500, "structure": "PASTURE"},
}

# T (24-day production capacity) per product, used only to size a sane
# per-turn sell throttle so we don't dump a whole shed into a thin market.
SELL_CAP = {
    "WHEAT": 40, "CARROT": 45, "TOMATO": 20, "STRAWBERRY": 10, "MELON": 30,
    "EGG": 33, "MILK": 12, "WOOL": 10,
}
SELL_ORDER = ["MELON", "STRAWBERRY", "WOOL", "MILK", "TOMATO", "EGG", "CARROT", "WHEAT"]

CROP_CANDIDATES = ["WHEAT", "CARROT", "MELON", "STRAWBERRY", "TOMATO"]
QUAD_ORDER = ["NW", "NE", "SW", "SE"]
LAND_PRICES = {"NE": 1000, "SW": 2000, "SE": 4000}
FERTILIZER_RESERVE = 6
MAX_ORDERS = 10
MAX_HANDS = 10
HIRE_MONEY_BUFFER = 60
HIRE_COST_CAP = 60
HIRE_BURST_CAP = 7
ANIMAL_MIN_CASH = 1200
ANIMAL_MIN_LEFTOVER = 400
SEASON_DAYS = 30
LAND_CUTOFF_DAY = 22          # no point unlocking land we can't put to work
ANIMAL_CUTOFF_DAY = 20        # animals need days to build+grow+pay back
FERTILIZER_LIQUIDATE_DAY = 26  # stop hoarding fertilizer near the end
LIQUIDATE_DAY = 28             # dump the whole shed, no throttling, near the end


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _step_toward(pos, target):
    x, y = pos
    tx, ty = target
    if x == tx and y == ty:
        return None
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    return ["NORTH"]


def _quadrant_tiles(half):
    return {
        "NW": [(x, y) for y in range(half) for x in range(half)],
        "NE": [(x, y) for y in range(half) for x in range(half, 2 * half)],
        "SW": [(x, y) for y in range(half, 2 * half) for x in range(half)],
        "SE": [(x, y) for y in range(half, 2 * half) for x in range(half, 2 * half)],
    }


def _home_tiles(unlocked, board_size):
    half = board_size // 2
    quads = _quadrant_tiles(half)
    tiles = []
    for q in QUAD_ORDER:
        if q in unlocked:
            tiles.extend(quads[q])
    return tiles


def _shed_tiles(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def _unfertilized_cap(cd):
    """Best yield reachable from plain watering alone (no fertilizer)."""
    window_start = (cd["max_yield_day"] + 1) // 2
    span = cd["max_yield_day"] - window_start + 1
    return min(cd["max_yield"], 1 + span)


def _ongoing_lifetime_days(cd):
    """Day offset (from planting) at which an ongoing crop's production
    permanently stops, per the engine's days_since_first % interval tick."""
    interval = max(cd["interval"], 1)
    return cd["first_yield_day"] + (cd["max_yield"] - 1) * interval


def _ongoing_exhausted(tile, cd, day):
    lifetime_end = tile["planted_day"] + _ongoing_lifetime_days(cd)
    return day > lifetime_end and tile.get("yield_units", 0) <= 0


def _crop_value_per_day(crop, prices):
    cd = CROPS[crop]
    price = prices.get(crop, cd["seed"])
    if cd["ongoing"]:
        lifetime = max(_ongoing_lifetime_days(cd), 1)
        revenue = price * cd["max_yield"]
        return (revenue - cd["seed"]) / lifetime
    yield_est = cd["max_yield"] if crop in FERTILIZE_WORTHY else _unfertilized_cap(cd)
    cycle = max(cd["max_yield_day"], 1)
    revenue = price * yield_est
    return (revenue - cd["seed"]) / cycle


def _choose_crop(prices, active_counts):
    best, best_score = CROP_CANDIDATES[0], float("-inf")
    for crop in CROP_CANDIDATES:
        score = _crop_value_per_day(crop, prices) / (1 + active_counts.get(crop, 0))
        if score > best_score:
            best, best_score = crop, score
    return best


def _crop_action(pos, home_tile, tiles, seeds, day, inv, shed, board_size, planned_crop):
    tx, ty = home_tile
    tile_at_home = tiles[ty][tx]

    # If our tile is a fertilize-worthy one-time crop approaching its bonus
    # window and we're not already carrying fertilizer, make a same-day
    # detour to the shed to grab one before the window opens.
    if (
        isinstance(tile_at_home, dict)
        and tile_at_home.get("kind") == "PLANT"
        and tile_at_home["crop"] in FERTILIZE_WORTHY
        and inv.get("FERTILIZER", 0) == 0
        and shed.get("FERTILIZER", 0) > 0
    ):
        cd = CROPS[tile_at_home["crop"]]
        window_start = (cd["max_yield_day"] + 1) // 2
        age = day - tile_at_home["planted_day"]
        if age <= window_start and tile_at_home["fertilized_until_day"] < day:
            shed_tiles = _shed_tiles(board_size)
            nearest = min(shed_tiles, key=lambda t: _dist(pos, t))
            if pos != nearest:
                return _step_toward(pos, nearest) or ["PASS"]
            return ["PICKUP", "FERTILIZER", 1]

    if pos != home_tile:
        return _step_toward(pos, home_tile) or ["PASS"]

    tile = tile_at_home
    if tile is None:
        crop = planned_crop
        if crop and seeds.get(crop, 0) > 0:
            return ["PLANT", crop]
        return ["PASS"]
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return ["DIG"]
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        cd = CROPS.get(tile["crop"])
        if cd is None:
            return ["PASS"]
        age = day - tile["planted_day"]
        if cd["ongoing"]:
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            if _ongoing_exhausted(tile, cd, day):
                return ["DIG"]
            if not tile["watered_today"]:
                return ["WATER"]
            return ["PASS"]
        # one-time crop
        if age > cd["max_yield_day"]:
            # in decay: grab whatever is left immediately, or clear the tile
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            return ["DIG"]
        if age >= cd["max_yield_day"] and tile.get("yield_units", 0) > 0:
            return ["HARVEST"]
        if (
            tile["crop"] in FERTILIZE_WORTHY
            and age == (cd["max_yield_day"] + 1) // 2
            and tile["fertilized_until_day"] < day
            and inv.get("FERTILIZER", 0) > 0
        ):
            return ["FERTILIZE"]
        if not tile["watered_today"]:
            return ["WATER"]
        return ["PASS"]
    return ["PASS"]


def _rancher_action(pos, inv, shed, tiles, animal_slots, board_size):
    shed_tiles = _shed_tiles(board_size)
    nearest_shed = min(shed_tiles, key=lambda t: _dist(pos, t))
    needs = []  # (priority, target_coord_or_None_for_shed, action)
    for coord, animal in animal_slots:
        tx, ty = coord
        tile = tiles[ty][tx]
        if tile is None:
            build_op = "BUILD_COOP" if animal == "GOOSE" else "BUILD_PASTURE"
            needs.append((0, coord, [build_op]))
            continue
        if not isinstance(tile, dict):
            continue
        if "animal" not in tile:
            if inv.get(animal, 0) > 0:
                needs.append((1, coord, ["PLACE", animal]))
            elif shed.get(animal, 0) > 0:
                needs.append((1, None, ["PICKUP", animal, 1]))
            continue
        if not tile["fed_today"]:
            if inv.get("WHEAT", 0) > 0:
                needs.append((2, coord, ["FEED"]))
            elif shed.get("WHEAT", 0) > 0:
                needs.append((2, None, ["PICKUP", "WHEAT", 6]))
        if tile.get("yield_units", 0) > 0:
            needs.append((3, coord, ["HARVEST"]))
        if tile.get("fertilizer_available"):
            needs.append((4, coord, ["COLLECT_FERTILIZER"]))
        if not tile.get("cared_today"):
            needs.append((5, coord, ["CARE"]))

    if not needs:
        if inv:
            if pos in shed_tiles:
                return ["DROP"]
            return _step_toward(pos, nearest_shed) or ["PASS"]
        return ["PASS"]

    needs.sort(key=lambda n: (n[0], _dist(pos, n[1] if n[1] is not None else nearest_shed)))
    _, target, action = needs[0]
    target_coord = nearest_shed if target is None else target
    if pos != target_coord:
        return _step_toward(pos, target_coord) or ["PASS"]
    return action


def agent(obs):
    player = obs["player"]
    day = obs["day"]
    hour = obs["hour"]
    farms = obs["farms"]
    me = farms[player]
    private = obs["private"]
    tiles = me["tiles"]
    board_size = len(tiles)
    shed = private["shed"]
    seeds = private["seeds"]
    inventories = private["inventories"]
    money = me["money"]

    market_prices = obs["market"]["prices"]

    home = _home_tiles(me["unlocked_quadrants"], board_size)
    animal_slots = list(zip(home[:3], ["GOOSE", "COW", "SHEEP"]))
    crop_tiles = home[3:]

    farmer_pos = tuple(me["farmer"])
    hand_positions = [tuple(h) for h in me["hands"]]

    # How many of each crop are already growing, for the anti-concentration
    # penalty in _choose_crop.
    active_counts = {}
    active_tiles = min(len(crop_tiles), max(len(hand_positions), 1))
    for coord in crop_tiles[:active_tiles]:
        cx, cy = coord
        t = tiles[cy][cx]
        if isinstance(t, dict) and t.get("kind") == "PLANT":
            active_counts[t["crop"]] = active_counts.get(t["crop"], 0) + 1

    # Plan a crop for every currently-empty assigned tile *once*, sharing one
    # incrementally-updated count so the anti-concentration scoring actually
    # spreads different tiles across different crops instead of every tile
    # independently landing on the same "best" crop and starving each other
    # for the one seed that gets bought.
    planned_crop = {}
    demand = {}
    planning_counts = dict(active_counts)
    for coord in crop_tiles[:active_tiles]:
        cx, cy = coord
        if tiles[cy][cx] is None:
            crop = _choose_crop(market_prices, planning_counts)
            planned_crop[coord] = crop
            planning_counts[crop] = planning_counts.get(crop, 0) + 1
            demand[crop] = demand.get(crop, 0) + 1

    orders = []

    def add(order):
        if len(orders) < MAX_ORDERS:
            orders.append(order)

    # --- sells (throttled per item so we don't crash thin markets; near the
    # end of the season we drop the throttle and liquidate everything) -----
    liquidating = day >= LIQUIDATE_DAY
    for item in SELL_ORDER:
        qty = shed.get(item, 0)
        if qty <= 0:
            continue
        cap = qty if liquidating else SELL_CAP.get(item, 20)
        add(["SELL", item, min(qty, cap)])
    fert_reserve = 0 if day >= FERTILIZER_LIQUIDATE_DAY else FERTILIZER_RESERVE
    if shed.get("FERTILIZER", 0) > fert_reserve:
        add(["SELL", "FERTILIZER", shed["FERTILIZER"] - fert_reserve])

    # --- hire: burst-hire right at the start of the day so hands get a
    # full day's work instead of trickling in one per turn -----------------
    wanted_hands = min(MAX_HANDS, max(1, len(crop_tiles)))
    if hour == 0:
        n = me["hires_today"]
        projected_money = money
        hired_this_turn = 0
        while (
            len(hand_positions) + hired_this_turn < wanted_hands
            and hired_this_turn < HIRE_BURST_CAP
            and len(orders) < MAX_ORDERS
        ):
            cost = _fib(n)
            if cost > HIRE_COST_CAP or projected_money - HIRE_MONEY_BUFFER < cost:
                break
            add(["HIRE"])
            projected_money -= cost
            n += 1
            hired_this_turn += 1

    # --- land purchase once cash is comfortably ahead (only while there's
    # enough season left to make use of the new tiles) ---------------------
    if day <= LAND_CUTOFF_DAY:
        for q in QUAD_ORDER[1:]:
            if q not in me["unlocked_quadrants"]:
                price = LAND_PRICES[q]
                if money >= price * 1.6:
                    add(["BUY_LAND"])
                break

    # --- seed restocking: buy exactly as many of each crop as the plan
    # above actually needs (not just "1 of whichever crop scored best"),
    # so every hand that was assigned a crop can actually plant it --------
    for crop, need in demand.items():
        have = seeds.get(crop, 0)
        to_buy = max(0, need - have)
        if to_buy == 0:
            continue
        cost = CROPS[crop]["seed"]
        affordable = int(money // (cost * 1.2)) if cost > 0 else to_buy
        to_buy = min(to_buy, affordable)
        if to_buy > 0:
            add(["BUY_SEED", crop, to_buy])
            money -= to_buy * cost

    # --- fertilizer restocking: only worth buying while a wheat/carrot tile
    # is actually growing (fertilizing melon/ongoing crops is wasted) ------
    has_fertilizable_growth = any(
        isinstance((t := tiles[cy][cx]), dict) and t.get("kind") == "PLANT" and t["crop"] in FERTILIZE_WORTHY
        for cx, cy in crop_tiles[:active_tiles]
    )
    if has_fertilizable_growth and shed.get("FERTILIZER", 0) < 2 and money >= 400:
        add(["BUY_PRODUCT", "FERTILIZER", 2])

    # --- animal restocking (skip once too little season remains to pay off
    # the purchase) ----------------------------------------------------
    if day <= ANIMAL_CUTOFF_DAY:
        for coord, animal in animal_slots:
            cx, cy = coord
            tile = tiles[cy][cx]
            has_structure = isinstance(tile, dict)
            has_animal = has_structure and "animal" in tile
            if has_structure and not has_animal and shed.get(animal, 0) == 0:
                cost = ANIMALS[animal]["cost"]
                if money >= max(ANIMAL_MIN_CASH, cost * 1.3) and money - cost >= ANIMAL_MIN_LEFTOVER:
                    add(["BUY_ANIMAL", animal, 1])
                    money -= cost  # reserve so we don't queue three buys in one turn

    # --- unit actions --------------------------------------------------
    farmer_inv = inventories[0] if inventories else {}
    farmer_action = _rancher_action(farmer_pos, farmer_inv, shed, tiles, animal_slots, board_size)

    hand_actions = []
    for i, pos in enumerate(hand_positions):
        if i < len(crop_tiles):
            coord = crop_tiles[i]
            hand_inv = inventories[i + 1] if i + 1 < len(inventories) else {}
            hand_actions.append(
                _crop_action(pos, coord, tiles, seeds, day, hand_inv, shed, board_size, planned_crop.get(coord))
            )
        else:
            hand_actions.append(["PASS"])

    return {"farmer": farmer_action, "hands": hand_actions, "market": orders[:MAX_ORDERS]}
'''

_ns_v1, _ns_v2 = {}, {}
exec(compile(AGENT_V1_SOURCE, 'agent_v1.py', 'exec'), _ns_v1)
exec(compile(AGENT_V2_SOURCE, 'main.py', 'exec'), _ns_v2)
agent_v1, agent = _ns_v1['agent'], _ns_v2['agent']
# 'agent' (v2) is what ships in main.py at the end; agent_v1 is kept only
# as the local comparison point for the table in §3.
print('v1:', len(AGENT_V1_SOURCE), 'bytes  |  v2:', len(AGENT_V2_SOURCE), 'bytes')


SEEDS = [1, 7, 42, 99, 2026]
OPPONENTS = ['random', 'starter']
AGENTS = {'v1 (fixed rotation)': agent_v1, 'v2 (price-aware + fertilizer + recycling)': agent}

rows = []
for label, fn in AGENTS.items():
    for seed in SEEDS:
        for opponent in OPPONENTS:
            for seat in (0, 1):
                env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed}, debug=False)
                agents = [fn, opponent] if seat == 0 else [opponent, fn]
                env.run(agents)
                final = env.steps[-1]
                rows.append({
                    'policy': label, 'seed': seed, 'opponent': opponent, 'seat': seat,
                    'money': final[seat].reward, 'opponent_money': final[1 - seat].reward,
                    'margin': final[seat].reward - final[1 - seat].reward,
                })

results = pd.DataFrame(rows)
summary = results.groupby('policy').agg(
    games=('margin', 'size'),
    wins=('margin', lambda s: (s > 0).sum()),
    mean_money=('money', 'mean'),
    mean_margin=('margin', 'mean'),
).round(0)
summary['win rate'] = (summary['wins'] / summary['games']).round(3)
display(summary)


ax = summary['win rate'].plot.barh(figsize=(8.8, 2.6), color=['#94a3b8', '#0f766e'])
ax.axvline(0.5, color='#64748b', linestyle='--', linewidth=1)
ax.set(xlabel='win rate vs. random + starter, both seats, 5 seeds (live-run in this notebook)',
       ylabel='', xlim=(0, 1.05), title='v1 vs v2 — measured, not asserted')
ax.grid(axis='x', alpha=0.25)
plt.tight_layout()
plt.show()

assert (results.loc[results.policy.str.startswith('v2'), 'margin'] > 0).all(), 'v2 should win every game'
print('v2 won every one of its', (results.policy.str.startswith('v2')).sum(), 'test games.')


# Public market formula, independently derived from kaggriculture.py's own
# market_price()/MARKET_PARAMS - the same formula the agent above uses via
# obs.market.prices. Reproduced here only to chart it, not to plan around
# any specific opponent.
MARKET_PARAMS = {
    'WOOL':       (200, 105, 'sq',     3.20),
    'STRAWBERRY': (120, 100, 'linear', 1.60),
    'MILK':       (160, 122, 'linear', 1.60),
    'MELON':      (250, 300, 'sq',     3.60),
}

def _shape(name, x):
    return x if name == 'linear' else x * x

def _quote(item, surplus):
    base, scale, fn, target = MARKET_PARAMS[item]
    amp = target * base / _shape(fn, scale)
    return max(1, round(base - amp * _shape(fn, surplus)))

curve = pd.DataFrame(
    [[item, surplus, _quote(item, surplus)] for item in MARKET_PARAMS for surplus in range(0, 181)],
    columns=['product', 'surplus inventory', 'quote'],
)
ax = curve.pivot(index='surplus inventory', columns='product', values='quote').plot(figsize=(9, 4.2), linewidth=2)
ax.set(title='Public price-impact curve (above-equilibrium side)', ylabel='unit quote ($)')
ax.grid(alpha=0.25)
plt.tight_layout()
plt.show()


import io, contextlib

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 123}, debug=True)
    env.run([agent, agent])

log = buf.getvalue()
warnings = [line for line in log.splitlines() if 'WARNING' in line]
final = env.steps[-1]
p0, p1 = final[0].reward, final[1].reward
rel_diff = abs(p0 - p1) / max(p0, p1, 1)

print('seat 0:', p0, ' seat 1:', p1, f' relative diff: {rel_diff:.1%}', ' engine warnings:', len(warnings))
assert rel_diff < 0.15, 'mirror match should stay close (a large gap would suggest a real bug, not just weed RNG)'
assert not warnings, 'engine should not warn about illegal/invalid agent behaviour'
print('Mirror match stayed within tolerance, no engine warnings.')


import hashlib, importlib.util, tarfile
from pathlib import Path

WORK = Path('/kaggle/working')
if not WORK.exists():
    WORK = Path.cwd()
MAIN_PATH = WORK / 'main.py'
ARCHIVE_PATH = WORK / 'submission.tar.gz'

MAIN_PATH.write_text(AGENT_V2_SOURCE, encoding='utf-8')
main_bytes = MAIN_PATH.read_bytes()
main_sha256 = hashlib.sha256(main_bytes).hexdigest()

with tarfile.open(ARCHIVE_PATH, 'w:gz') as archive:
    archive.add(MAIN_PATH, arcname='main.py')
with tarfile.open(ARCHIVE_PATH, 'r:gz') as archive:
    assert archive.getnames() == ['main.py']

spec = importlib.util.spec_from_file_location('submitted_agent', MAIN_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 220807}, debug=False)
schema_smoke = []
for seat, state in enumerate(env.reset(2)):
    action = module.agent(state.observation)
    assert set(action) == {'farmer', 'hands', 'market'}
    assert isinstance(action['farmer'], list)
    assert isinstance(action['hands'], list)
    assert isinstance(action['market'], list) and len(action['market']) <= 10
    schema_smoke.append({'seat': seat, 'farmer': action['farmer'], 'market_orders': len(action['market'])})

print({
    'main_py': str(MAIN_PATH),
    'main_bytes': len(main_bytes),
    'main_sha256': main_sha256,
    'submission': str(ARCHIVE_PATH),
    'archive_members': ['main.py'],
    'schema_smoke': schema_smoke,
    'ready': True,
})
