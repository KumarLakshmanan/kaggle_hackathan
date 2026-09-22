"""Kaggriculture adaptive market scheduler.

This is a standalone, standard-library-only competition agent.  It was
written after studying public Apache-2.0 Kaggle kernels, especially
``lucifer19/kaggriculture-night-harvest`` and
``prvsiyan/kaggriculture-frontier-the-soil-remembers-rain``.  The references
are credited in ``reference/ATTRIBUTION.md``; their code is not imported at
runtime.  This file is an independently modified implementation with a
defensive observation adapter, persistent worker ownership, demand-aware crop
selection, and staged liquidation.

The competition loader calls ``agent(observation)``.  No Kaggle package is
needed at runtime, which keeps the submission archive portable.
"""

import math


# The current Kaggriculture engine (1.32.7+) uses these defaults.  Keeping the
# table local also lets the policy estimate marginal sell damage without
# importing the simulator into the submitted file.
CROP_RULES = {
    "WHEAT": {
        "seed": 10,
        "base": 25,
        "first": 2,
        "peak": 4,
        "yield": 4,
        "fert_yield": 6,
        "ongoing": False,
    },
    "CARROT": {
        "seed": 20,
        "base": 35,
        "first": 2,
        "peak": 3,
        "yield": 3,
        "fert_yield": 4,
        "ongoing": False,
    },
    "TOMATO": {
        "seed": 50,
        "base": 60,
        "first": 8,
        "peak": 11,
        "yield": 4,
        "fert_yield": 4,
        "ongoing": True,
    },
    "STRAWBERRY": {
        "seed": 100,
        "base": 120,
        "first": 10,
        "peak": 16,
        "yield": 4,
        "fert_yield": 4,
        "ongoing": True,
    },
    "MELON": {
        "seed": 80,
        "base": 250,
        "first": 10,
        "peak": 10,
        "yield": 6,
        "fert_yield": 6,
        "ongoing": False,
    },
}

ANIMAL_RULES = {
    "GOOSE": {
        "cost": 300,
        "product": "EGG",
        "interval": 1,
        "first": 4,
        "max_held": 4,
        "structure": "COOP",
    },
    "COW": {
        "cost": 400,
        "product": "MILK",
        "interval": 2,
        "first": 8,
        "max_held": 6,
        "structure": "PASTURE",
    },
    "SHEEP": {
        "cost": 500,
        "product": "WOOL",
        "interval": 3,
        "first": 6,
        "max_held": 6,
        "structure": "PASTURE",
    },
}

BASE_PRICES = {
    "WHEAT": 25,
    "CARROT": 35,
    "TOMATO": 60,
    "STRAWBERRY": 120,
    "MELON": 250,
    "EGG": 50,
    "MILK": 160,
    "WOOL": 200,
    "FERTILIZER": 100,
}

# (anchor inventory, below-side shape, below-side target, above-side shape,
# above-side target, throughput anchor).  The table mirrors the public engine
# documentation and is used only for relative order ranking.
MARKET_PARAMS = {
    "WHEAT": (10_000, "sqrt", 0.80, "log", 0.20, 400),
    "CARROT": (10_000, "hinge", 1.00, "sqrt", 0.70, 450),
    "TOMATO": (10_000, "hinge", 0.40, "sqrt", 0.60, 200),
    "STRAWBERRY": (10_000, "sqrt", 0.70, "linear", 1.60, 100),
    "MELON": (10_000, "log", 0.20, "sq", 3.60, 300),
    "EGG": (10_000, "hinge", 0.40, "log", 0.20, 332),
    "MILK": (10_000, "sqrt", 0.60, "linear", 1.60, 122),
    "WOOL": (10_000, "log", 0.20, "sq", 3.20, 105),
    "FERTILIZER": (10_000, "linear", 0.40, "linear", 0.40, 200),
}

SHOP_RECIPES = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL", "WOOL"),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT", "CARROT"),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

LAND_COSTS = (1000, 2000, 4000)
TURN_HOURS = 24
BOARD_SIZE = 10
MAX_MARKET_ORDERS = 10
SHED_CAPACITY = 100

# Episode-local memory.  The engine reuses the Python process for all turns,
# so this is where route ownership survives between calls.  It is deliberately
# state based: there is no opponent identity or hidden episode identifier.
_LAST_STEP = -1
_ASSIGNMENTS = {}
_CROP_PLAN = {}


def _reset_episode_state():
    """Forget route state when the simulator starts a fresh episode."""

    global _LAST_STEP, _ASSIGNMENTS, _CROP_PLAN
    _LAST_STEP = -1
    _ASSIGNMENTS = {}
    _CROP_PLAN = {}


def _number(value, default=0.0):
    try:
        if isinstance(value, bool):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _integer(value, default=0):
    return int(_number(value, default))


def _position(value, default=(0, 0)):
    """Read both the public ``[x, y]`` form and tolerant mock forms."""

    if isinstance(value, dict):
        value = value.get("position", value.get("pos", default))
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return (_integer(value[0]), _integer(value[1]))
    return (int(default[0]), int(default[1]))


def _default_tiles(size=BOARD_SIZE):
    return [
        [None if x < size // 2 and y < size // 2 else "LOCKED" for x in range(size)]
        for y in range(size)
    ]


def _safe_mapping(value):
    return value if isinstance(value, dict) else {}


def _farm_from_observation(observation, player_id):
    """Find the local farm across official and lightweight test schemas."""

    raw_player = observation.get("player", 0)
    if isinstance(raw_player, dict):
        nested = raw_player.get("farm")
        if isinstance(nested, dict):
            return nested, _integer(raw_player.get("id", player_id), player_id)

    farms = observation.get("farms")
    if isinstance(farms, (list, tuple)) and farms:
        index = max(0, min(player_id, len(farms) - 1))
        if isinstance(farms[index], dict):
            return farms[index], player_id

    for key in ("farm", "local_farm"):
        if isinstance(observation.get(key), dict):
            return observation[key], player_id
    return {}, player_id


def _normalise_hands(raw_hands):
    if not isinstance(raw_hands, (list, tuple)):
        return []
    return [_position(item) for item in raw_hands]


def _normalize_observation(observation):
    """Convert the public observation into a stable internal view.

    Kaggle's official format is intentionally small and predictable, but a
    malformed observation should never terminate a submitted agent.  Missing
    private/market sections become empty dictionaries and a missing board gets
    a conservative initial board.
    """

    if not isinstance(observation, dict):
        return {
            "valid": False,
            "player": 0,
            "day": 0,
            "hour": 0,
            "step": 0,
            "farm": {},
            "tiles": _default_tiles(),
            "farmer": (0, 0),
            "hands": [],
            "money": 0.0,
            "hires_today": 0,
            "unlocked_quadrants": ["NW"],
            "opponent_farm": {},
            "private": {},
            "market": {},
            "town": {},
        }

    raw_player = observation.get("player", 0)
    player_id = 0
    if isinstance(raw_player, dict):
        player_id = _integer(raw_player.get("id", 0), 0)
    else:
        player_id = _integer(raw_player, 0)
    player_id = 1 if player_id == 1 else 0

    farm, player_id = _farm_from_observation(observation, player_id)
    raw_tiles = farm.get("tiles") if isinstance(farm, dict) else None
    if isinstance(raw_tiles, list) and raw_tiles:
        tiles = []
        for row in raw_tiles:
            if isinstance(row, list):
                tiles.append(list(row))
        if not tiles:
            tiles = _default_tiles()
    else:
        tiles = _default_tiles()

    size_y = len(tiles)
    size_x = max((len(row) for row in tiles), default=BOARD_SIZE)
    if size_x <= 0 or size_y <= 0:
        tiles = _default_tiles()
        size_y = len(tiles)
        size_x = len(tiles[0])

    raw_farmer = farm.get("farmer", (0, 0)) if isinstance(farm, dict) else (0, 0)
    farmer = _position(raw_farmer, (size_x // 2 - 1, size_y // 2 - 1))
    hands = _normalise_hands(farm.get("hands", []) if isinstance(farm, dict) else [])

    raw_farms = observation.get("farms")
    opponent_farm = {}
    if isinstance(raw_farms, (list, tuple)) and len(raw_farms) > 1:
        other = 1 - player_id
        if isinstance(raw_farms[other], dict):
            opponent_farm = raw_farms[other]
    elif isinstance(observation.get("opponent"), dict):
        opponent_farm = observation["opponent"].get("farm", observation["opponent"])

    raw_market = _safe_mapping(observation.get("market"))
    raw_town = _safe_mapping(observation.get("town"))
    if not raw_town:
        raw_town = _safe_mapping(raw_market.get("town"))

    raw_private = _safe_mapping(observation.get("private"))
    day = max(0, _integer(observation.get("day", 0), 0))
    hour = max(0, _integer(observation.get("hour", 0), 0))
    supplied_step = observation.get("step")
    if isinstance(supplied_step, (int, float)) and not isinstance(supplied_step, bool):
        step = max(0, int(supplied_step))
    else:
        step = day * TURN_HOURS + hour

    unlocked = farm.get("unlocked_quadrants", ["NW"]) if isinstance(farm, dict) else ["NW"]
    if not isinstance(unlocked, list):
        unlocked = ["NW"]

    return {
        "valid": bool(farm),
        "player": player_id,
        "day": day,
        "hour": hour,
        "step": step,
        "farm": farm,
        "tiles": tiles,
        "width": size_x,
        "height": size_y,
        "farmer": farmer,
        "hands": hands,
        "money": max(0.0, _number(farm.get("money", 0), 0.0)),
        "hires_today": max(0, _integer(farm.get("hires_today", 0), 0)),
        "unlocked_quadrants": [str(item).upper() for item in unlocked],
        "opponent_farm": opponent_farm if isinstance(opponent_farm, dict) else {},
        "private": raw_private,
        "market": raw_market,
        "town": raw_town,
    }


def _phase(day):
    """Season phases used by both economics and the worker route."""

    day = _integer(day, 0)
    if day <= 7:
        return "BOOTSTRAP"
    if day <= 20:
        return "COMPOUND"
    if day <= 27:
        return "HARVEST"
    return "LIQUIDATE"


def _tile(view, position):
    x, y = position
    tiles = view.get("tiles", [])
    if y < 0 or x < 0 or y >= len(tiles) or x >= len(tiles[y]):
        return "LOCKED"
    return tiles[y][x]


def _tile_kind(tile):
    if isinstance(tile, str):
        return tile.upper()
    if not isinstance(tile, dict):
        return "EMPTY"
    kind = tile.get("kind", tile.get("structure", ""))
    kind = str(kind).upper()
    if kind == "PLANT" or tile.get("crop"):
        return "PLANT"
    if kind in {"COOP", "PASTURE"}:
        return kind
    if kind == "WEED":
        return "WEED"
    return kind or "EMPTY"


def _is_empty_unlocked(view, position):
    return _tile(view, position) is None


def _all_positions(view):
    for y, row in enumerate(view.get("tiles", [])):
        for x in range(len(row)):
            yield (x, y)


def _plants(view):
    for position in _all_positions(view):
        tile = _tile(view, position)
        if _tile_kind(tile) == "PLANT":
            yield position, tile


def _structures(view):
    for position in _all_positions(view):
        tile = _tile(view, position)
        kind = _tile_kind(tile)
        if kind in {"COOP", "PASTURE"}:
            yield position, tile


def _crop_at(tile):
    if isinstance(tile, dict):
        crop = tile.get("crop", tile.get("product"))
        if crop:
            return str(crop).upper()
    return ""


def _animal_at(tile):
    if isinstance(tile, dict):
        animal = tile.get("animal")
        if animal:
            return str(animal).upper()
    return ""


def _shed(view):
    private = _safe_mapping(view.get("private"))
    return _safe_mapping(private.get("shed"))


def _inventory(view, unit_index):
    private = _safe_mapping(view.get("private"))
    inventories = private.get("inventories", [])
    if isinstance(inventories, list) and 0 <= unit_index < len(inventories):
        return _safe_mapping(inventories[unit_index])
    return {}


def _inventory_load(inventory):
    return sum(max(0, _integer(value, 0)) for value in _safe_mapping(inventory).values())


def _shed_load(view):
    return sum(max(0, _integer(value, 0)) for value in _shed(view).values())


def _public_count(view, product, opponent=False):
    source = view.get("opponent_farm", {}) if opponent else view
    tiles = source.get("tiles", []) if isinstance(source, dict) else []
    count = 0
    if opponent:
        for row in tiles if isinstance(tiles, list) else []:
            for tile in row if isinstance(row, list) else []:
                if _crop_at(tile) == product:
                    count += 1
                if _animal_at(tile) and ANIMAL_RULES.get(_animal_at(tile), {}).get("product") == product:
                    count += 1
    else:
        for _, tile in _plants(source):
            if _crop_at(tile) == product:
                count += 1
        for _, tile in _structures(source):
            animal = _animal_at(tile)
            if ANIMAL_RULES.get(animal, {}).get("product") == product:
                count += 1
    return count


def _town_pull(view):
    """Count per-instance shop inputs, retaining duplicate shop unlocks."""

    town = _safe_mapping(view.get("town"))
    shops = town.get("unlocked_shops", [])
    if not isinstance(shops, list):
        shops = []
    pull = {product: 0 for product in BASE_PRICES}
    for raw_shop in shops:
        shop = str(raw_shop).upper().strip().replace(" ", "_")
        for product in SHOP_RECIPES.get(shop, ()):
            pull[product] = pull.get(product, 0) + 1
    return pull


def _market_inventory(view, product):
    market = _safe_mapping(view.get("market"))
    inventory = _safe_mapping(market.get("inventory"))
    return max(0, _integer(inventory.get(product, 10_000), 10_000))


def _market_price(view, product):
    market = _safe_mapping(view.get("market"))
    prices = _safe_mapping(market.get("prices"))
    return max(1.0, _number(prices.get(product, BASE_PRICES.get(product, 1)), BASE_PRICES.get(product, 1)))


def _shape_value(shape, distance, throughput):
    if throughput <= 0:
        return 0.0
    ratio = max(0.0, distance) / float(throughput)
    if shape == "linear":
        return ratio
    if shape == "sq":
        return ratio * ratio
    if shape == "sqrt":
        return math.sqrt(ratio)
    if shape == "log":
        return math.log1p(ratio)
    if shape == "log10":
        return math.log10(1.0 + ratio)
    if shape == "hinge":
        return ratio + 8.0 * max(0.0, ratio - 1.0) ** 2
    return ratio


def _quote(product, inventory):
    """Approximate the official rounded quote at a market inventory."""

    base = float(BASE_PRICES.get(product, 1))
    params = MARKET_PARAMS.get(product)
    if not params:
        return max(1, int(base + 0.5))
    anchor, below_shape, below_target, above_shape, above_target, throughput = params
    inventory = _number(inventory, anchor)
    if inventory == anchor:
        return max(1, int(base + 0.5))
    distance = abs(inventory - anchor)
    if inventory < anchor:
        shape = below_shape
        target = below_target
        sign = 1.0
    else:
        shape = above_shape
        target = above_target
        sign = -1.0
    normalizer = _shape_value(shape, throughput, throughput)
    amplitude = target * base / normalizer if normalizer else 0.0
    raw = base + sign * amplitude * _shape_value(shape, distance, throughput)
    return max(1, int(math.floor(raw + 0.5)))


def _sell_value(product, inventory, quantity):
    quantity = max(0, _integer(quantity, 0))
    return sum(_quote(product, inventory + offset) for offset in range(quantity))


def _sell_loss(product, inventory, quantity):
    quantity = max(0, _integer(quantity, 0))
    if quantity <= 0:
        return 0.0
    before = quantity * _quote(product, inventory)
    return before - _sell_value(product, inventory, quantity)


def _fib(index):
    """Fibonacci hire price with the engine's 1, 1, 2, 3... sequence."""

    index = max(0, _integer(index, 0))
    a, b = 1, 1
    for _ in range(index):
        a, b = b, a + b
    return a


def _daily_workforce_target(day):
    """Return the number of units worth funding on this calendar day.

    Hands are reset at midnight by the official engine.  The target therefore
    describes the next day's temporary workforce, not a persistent headcount.
    Early labor compounds crop coverage; once the animal loop starts, a
    smaller crew leaves enough cash and market slots for livestock and feed.
    """

    day = max(0, _integer(day, 0))
    if day <= 3:
        return 3 + 2 * day
    if day <= 7:
        return 9
    if day <= 20:
        return 6
    if day < 28:
        return 5
    return 0


def _animal_targets(view):
    """Choose a conservative milk/wool mix after crops are established."""

    day = view.get("day", 0)
    if day < 8 or day >= 28:
        return {}

    if day < 12:
        total = 3
    elif day < 18:
        total = 6
    else:
        total = 9

    pull = _town_pull(view)
    milk_signal = _market_price(view, "MILK") / BASE_PRICES["MILK"] + 0.035 * pull.get("MILK", 0)
    wool_signal = _market_price(view, "WOOL") / BASE_PRICES["WOOL"] + 0.035 * pull.get("WOOL", 0)
    rival_milk = _public_count(view, "MILK", opponent=True)
    rival_wool = _public_count(view, "WOOL", opponent=True)
    milk_signal -= 0.025 * rival_milk
    wool_signal -= 0.025 * rival_wool

    if milk_signal >= wool_signal:
        cows = max(1, int(round(total * 0.58)))
        sheep = max(1, total - cows)
    else:
        sheep = max(1, int(round(total * 0.58)))
        cows = max(1, total - sheep)
    return {"COW": cows, "SHEEP": sheep}


def _animal_slot_positions(view):
    """Stable central pasture/coop positions, excluding shed standing tiles."""

    width = max(1, _integer(view.get("width", BOARD_SIZE), BOARD_SIZE))
    height = max(1, _integer(view.get("height", BOARD_SIZE), BOARD_SIZE))
    cx, cy = width // 2, height // 2
    shed_access = set(_shed_access(view))
    candidates = []
    for position in _all_positions(view):
        if position in shed_access:
            continue
        tile = _tile(view, position)
        if tile == "LOCKED":
            # Locked squares become useful after expansion, but do not reserve
            # them ahead of time while the initial farm is small.
            continue
        x, y = position
        distance = abs(x - (cx - 1)) + abs(y - (cy - 1))
        candidates.append((distance, y, x, position))
    candidates.sort()
    return [item[-1] for item in candidates[:10]]


def _crop_score(view, crop, count_hint=0):
    rule = CROP_RULES[crop]
    day = view.get("day", 0)
    remaining = max(0, 30 - day)
    if remaining < rule["first"]:
        return -1e9
    if rule["ongoing"]:
        # Four scheduled yields are possible only if the first production and
        # its cadence fit in the season.  Strawberry's every-other-day cadence
        # is approximated by the wider occupancy divisor.
        usable = min(rule["yield"], 1 + max(0, remaining - rule["first"]) // (2 if crop == "STRAWBERRY" else 1))
        occupancy = max(1, rule["first"] + (6 if crop == "STRAWBERRY" else 3))
    else:
        usable = rule["yield"]
        occupancy = max(1, rule["peak"])
    price = _market_price(view, crop)
    pull = _town_pull(view).get(crop, 0)
    rival = _public_count(view, crop, opponent=True)
    crowd = max(0, count_hint + rival)
    demand_factor = 1.0 + min(0.45, pull * 0.045)
    # Premium products need a hard crowd brake because their above-equilibrium
    # curves reach the floor quickly.  The brake is gradual so a scarcity price
    # can still justify planting.
    crowd_factor = 1.0
    if crop in {"MELON", "STRAWBERRY"}:
        crowd_factor = max(0.30, 1.0 - 0.035 * max(0, crowd - 4))
    elif crop in {"TOMATO", "CARROT"}:
        crowd_factor = max(0.65, 1.0 - 0.012 * max(0, crowd - 8))
    gross = usable * price * demand_factor * crowd_factor
    return (gross - rule["seed"]) / float(occupancy)


def _cleanup_crop_plan(view):
    global _CROP_PLAN
    cleaned = {}
    for position, crop in _CROP_PLAN.items():
        if not isinstance(position, tuple) or len(position) != 2:
            continue
        if not _is_empty_unlocked(view, position):
            continue
        if crop in CROP_RULES:
            cleaned[position] = crop
    _CROP_PLAN = cleaned


def _ensure_crop_plan(view):
    """Allocate future empty tiles without planting into the animal lane."""

    global _CROP_PLAN
    _cleanup_crop_plan(view)
    if _phase(view.get("day", 0)) == "LIQUIDATE":
        return

    animal_slots = set(_animal_slot_positions(view))
    candidates = []
    planned_positions = set(_CROP_PLAN)
    for position in _all_positions(view):
        if (
            position in animal_slots
            or position in planned_positions
            or not _is_empty_unlocked(view, position)
        ):
            continue
        x, y = position
        # The main farmer begins in the northwest shed lane.  A stable row
        # ordering keeps the route cache from thrashing on equal scores.
        candidates.append((abs(x - 1) + abs(y - 1), y, x, position))
    candidates.sort()

    unlocked_count = max(1, len(view.get("unlocked_quadrants", [])))
    day = view.get("day", 0)
    if day <= 3:
        target_total = 16
    elif day <= 7:
        target_total = 20
    elif day <= 14:
        target_total = 12 + 8 * unlocked_count
    elif day <= 20:
        target_total = 16 + 10 * unlocked_count
    else:
        target_total = 20 + 12 * unlocked_count

    existing_counts = {crop: 0 for crop in CROP_RULES}
    for _, tile in _plants(view):
        crop = _crop_at(tile)
        if crop in existing_counts:
            existing_counts[crop] += 1
    for crop in _CROP_PLAN.values():
        existing_counts[crop] += 1

    if day <= 7:
        allowed = ("MELON", "CARROT", "WHEAT", "STRAWBERRY", "TOMATO")
    elif day <= 20:
        allowed = ("STRAWBERRY", "MELON", "CARROT", "WHEAT", "TOMATO")
    else:
        allowed = ("CARROT", "WHEAT", "TOMATO", "STRAWBERRY")

    for _, _, _, position in candidates:
        if len(_CROP_PLAN) + sum(1 for _ in _plants(view)) >= target_total:
            break
        scored = []
        for crop in allowed:
            # Avoid a single premium crop consuming a whole initial quadrant.
            if crop == "MELON" and existing_counts[crop] >= max(4, 3 * unlocked_count):
                continue
            if crop == "STRAWBERRY" and existing_counts[crop] >= max(6, 8 * unlocked_count):
                continue
            if crop == "TOMATO" and existing_counts[crop] >= max(4, 6 * unlocked_count):
                continue
            score = _crop_score(view, crop, existing_counts[crop])
            scored.append((score, -list(allowed).index(crop), crop))
        if not scored:
            break
        scored.sort(reverse=True)
        crop = scored[0][-1]
        _CROP_PLAN[position] = crop
        existing_counts[crop] += 1


def _shed_access(view):
    width = max(2, _integer(view.get("width", BOARD_SIZE), BOARD_SIZE))
    height = max(2, _integer(view.get("height", BOARD_SIZE), BOARD_SIZE))
    hx, hy = width // 2, height // 2
    points = [
        (hx - 1, hy - 1),
        (hx, hy - 1),
        (hx - 1, hy),
        (hx, hy),
    ]
    return [
        (x, y)
        for x, y in points
        if 0 <= x < width and 0 <= y < height
    ]


def _distance(start, target):
    return abs(start[0] - target[0]) + abs(start[1] - target[1])


def _nearest_shed(position, view):
    access = _shed_access(view)
    if not access:
        return (0, 0)
    return min(access, key=lambda item: (_distance(position, item), item[1], item[0]))


def _movement_action(current, target, view):
    """Return one legal cardinal move on the passable board."""

    current = _position(current)
    target = _position(target)
    if current == target:
        return ["PASS"]
    width = max(1, _integer(view.get("width", BOARD_SIZE), BOARD_SIZE))
    height = max(1, _integer(view.get("height", BOARD_SIZE), BOARD_SIZE))
    x, y = current
    tx, ty = target
    # Locked cells are passable, so Manhattan routing is both safe and stable.
    if y > ty and y - 1 >= 0:
        return ["NORTH"]
    if x > tx and x - 1 >= 0:
        return ["WEST"]
    if y < ty and y + 1 < height:
        return ["SOUTH"]
    if x < tx and x + 1 < width:
        return ["EAST"]
    return ["PASS"]


def _task_signature(task):
    if not isinstance(task, dict):
        return None
    return (
        task.get("kind", ""),
        tuple(task.get("pos", ())),
        task.get("crop", ""),
        task.get("item", ""),
        task.get("owner"),
    )


def _unit_positions(view):
    return [view.get("farmer", (0, 0)), *view.get("hands", [])]


def _assign_tasks(view, tasks):
    """Assign distinct tasks, preserving a worker's target when still valid."""

    units = _unit_positions(view)
    remaining = [task for task in tasks if isinstance(task, dict)]
    assignments = []
    next_memory = {}

    def eligible(task, unit_index):
        owner = task.get("owner")
        if owner is None:
            return True
        return _integer(owner, -1) == unit_index

    for index, position in enumerate(units):
        previous = _ASSIGNMENTS.get(index)
        chosen_index = None
        if previous is not None:
            for candidate_index, task in enumerate(remaining):
                if _task_signature(task) == previous and eligible(task, index):
                    previous_priority = _integer(task.get("priority", 99), 99)
                    best_priority = min(
                        _integer(candidate.get("priority", 99), 99)
                        for candidate in remaining
                    )
                    # A persistent route is useful only while it is not
                    # blocking a newly surfaced survival-critical task.
                    if previous_priority <= best_priority:
                        chosen_index = candidate_index
                    break
        if chosen_index is None and remaining:
            eligible_indices = [
                candidate_index
                for candidate_index, task in enumerate(remaining)
                if eligible(task, index)
            ]
        else:
            eligible_indices = []
        if chosen_index is None and eligible_indices:
            chosen_index = min(
                eligible_indices,
                key=lambda candidate_index: (
                    _integer(remaining[candidate_index].get("priority", 99), 99),
                    _distance(position, _position(remaining[candidate_index].get("pos", position))),
                    str(_task_signature(remaining[candidate_index]) or ()),
                ),
            )
        if chosen_index is None:
            assignments.append(None)
            continue
        chosen = remaining.pop(chosen_index)
        assignments.append(chosen)
        next_memory[index] = _task_signature(chosen)

    _ASSIGNMENTS.clear()
    _ASSIGNMENTS.update(next_memory)
    return assignments


def _existing_animal_counts(view):
    counts = {animal: 0 for animal in ANIMAL_RULES}
    structures = {"COOP": 0, "PASTURE": 0}
    for _, tile in _structures(view):
        kind = _tile_kind(tile)
        structures[kind] = structures.get(kind, 0) + 1
        animal = _animal_at(tile)
        if animal in counts:
            counts[animal] += 1
    shed = _shed(view)
    for animal in counts:
        counts[animal] += max(0, _integer(shed.get(animal, 0), 0))
    for index in range(len(view.get("hands", [])) + 1):
        for item, amount in _inventory(view, index).items():
            item = str(item).upper()
            if item in counts:
                counts[item] += max(0, _integer(amount, 0))
    return counts, structures


def _build_tasks(view):
    """Create urgent care work first and economic work second."""

    _ensure_crop_plan(view)
    tasks = []
    day = view.get("day", 0)
    phase = _phase(day)

    # Basic needs and harvests.  Both WATER and HARVEST can exist for one tile;
    # enough hands then complete them in parallel, while priority protects the
    # no-two-missed-days rule when the farm is larger than the workforce.
    for position, tile in _plants(view):
        crop = _crop_at(tile)
        if crop not in CROP_RULES:
            continue
        watered = bool(tile.get("watered_today", tile.get("watered", False))) if isinstance(tile, dict) else False
        yield_units = max(0, _integer(tile.get("yield_units", 0), 0)) if isinstance(tile, dict) else 0
        planted_day = _integer(tile.get("planted_day", day), day) if isinstance(tile, dict) else day
        age = max(0, day - planted_day)
        rule = CROP_RULES[crop]
        if not watered:
            tasks.append({"kind": "WATER", "pos": position, "priority": 0, "crop": crop})
        if yield_units > 0:
            harvest_priority = 1 if age >= rule["first"] else 3
            if age > rule["peak"]:
                harvest_priority = 0
            tasks.append({"kind": "HARVEST", "pos": position, "priority": harvest_priority, "crop": crop})

    unfed_animals = []
    for position, tile in _structures(view):
        animal = _animal_at(tile)
        if animal not in ANIMAL_RULES:
            continue
        fed_today = bool(tile.get("fed_today", False)) if isinstance(tile, dict) else False
        if not fed_today:
            unfed_animals.append((position, animal))
        yield_units = max(0, _integer(tile.get("yield_units", 0), 0)) if isinstance(tile, dict) else 0
        if yield_units > 0:
            tasks.append({"kind": "HARVEST", "pos": position, "priority": 1, "item": animal})
        if isinstance(tile, dict) and bool(tile.get("fertilizer_available", False)):
            tasks.append({"kind": "COLLECT_FERTILIZER", "pos": position, "priority": 2, "item": "FERTILIZER"})
        if isinstance(tile, dict) and not bool(tile.get("cared_today", False)):
            tasks.append({"kind": "CARE", "pos": position, "priority": 4, "item": animal})

    # FEED consumes wheat from the active unit inventory.  First account for
    # wheat already carried by workers; then create shed pickups for the
    # remainder.  A worker can carry several feed units, so pickup batches keep
    # the route practical without sacrificing the one-action-per-turn contract.
    wheat_carriers = [
        index
        for index in range(len(view.get("hands", [])) + 1)
        if _integer(_inventory(view, index).get("WHEAT", 0), 0) > 0
    ]
    feedable = min(len(unfed_animals), len(wheat_carriers))
    for (position, animal), owner in zip(unfed_animals[:feedable], wheat_carriers):
        # One active unit can execute one FEED action per turn; bind the task
        # to a worker that currently carries wheat so it cannot be stolen by a
        # nearby but empty-handed worker during persistent assignment.
        tasks.append({
            "kind": "FEED",
            "pos": position,
            "priority": -3,
            "item": animal,
            "owner": owner,
        })
    missing_feed = len(unfed_animals) - feedable
    wheat_in_shed = max(0, _integer(_shed(view).get("WHEAT", 0), 0))
    if missing_feed > 0 and wheat_in_shed > 0:
        pickup_count = min(missing_feed, wheat_in_shed)
        pickup_access = _shed_access(view)
        while pickup_count > 0:
            batch = min(3, pickup_count)
            tasks.append({
                "kind": "PICKUP",
                "pos": pickup_access[0] if pickup_access else (0, 0),
                "priority": -2,
                "item": "WHEAT",
                "quantity": batch,
            })
            pickup_count -= batch

    # Weeds block future crops.  Clearing them is especially useful after the
    # first expansion, but is below animal survival and watering.
    for position in _all_positions(view):
        if _tile_kind(_tile(view, position)) == "WEED":
            tasks.append({"kind": "DIG", "pos": position, "priority": 3})

    target_animals = _animal_targets(view)
    existing_animals, structure_counts = _existing_animal_counts(view)
    empty_slots = [
        position
        for position in _animal_slot_positions(view)
        if _is_empty_unlocked(view, position)
    ]
    # Build just enough structures for the selected herd.  COW and SHEEP both
    # consume one shared PASTURE slot, so their targets must be added before
    # comparing against the structure count.  Existing empty structures count,
    # so an order cannot snowball across turns.
    required_structures = {
        "COOP": target_animals.get("GOOSE", 0),
        "PASTURE": target_animals.get("COW", 0) + target_animals.get("SHEEP", 0),
    }
    build_labels = {
        "COOP": ["GOOSE"],
        "PASTURE": ["COW", "SHEEP"],
    }
    for structure in ("COOP", "PASTURE"):
        needed = max(0, required_structures[structure] - structure_counts.get(structure, 0))
        labels = build_labels[structure]
        for build_index in range(min(needed, len(empty_slots))):
            position = empty_slots.pop(0)
            tasks.append({
                "kind": "BUILD_COOP" if structure == "COOP" else "BUILD_PASTURE",
                "pos": position,
                "priority": 5,
                "item": labels[build_index % len(labels)],
            })
            structure_counts[structure] = structure_counts.get(structure, 0) + 1

    # Carrying an animal gets a sticky placement task.  It is evaluated before
    # shed pickup so a worker never abandons an animal in transit.
    empty_structures = []
    for position, tile in _structures(view):
        if not _animal_at(tile):
            empty_structures.append((position, _tile_kind(tile)))
    for unit_index in range(len(view.get("hands", [])) + 1):
        inventory = _inventory(view, unit_index)
        for animal in ("COW", "SHEEP", "GOOSE"):
            if _integer(inventory.get(animal, 0), 0) <= 0:
                continue
            matching = [
                item for item in empty_structures
                if item[1] == ANIMAL_RULES[animal]["structure"]
            ]
            if matching:
                position = matching[0][0]
                tasks.append({
                    "kind": "PLACE",
                    "pos": position,
                    "priority": -1,
                    "item": animal,
                    "owner": unit_index,
                })
                empty_structures.remove(matching[0])
                break

    # If purchased animals are waiting in the shed, assign one pickup per
    # available empty matching structure.  PICKUP is valid from all four
    # standing tiles around the central shed, including locked quadrants.
    shed = _shed(view)
    pickup_access = _shed_access(view)
    for animal in ("COW", "SHEEP", "GOOSE"):
        count = max(0, _integer(shed.get(animal, 0), 0))
        matching = [
            item for item in empty_structures
            if item[1] == ANIMAL_RULES[animal]["structure"]
        ]
        for index in range(min(count, len(matching))):
            tasks.append({
                "kind": "PICKUP",
                "pos": pickup_access[0] if pickup_access else (0, 0),
                "priority": 3,
                "item": animal,
                "quantity": 1,
            })

    # Products should be dropped before a large shed becomes lossy.  At the
    # end of the season this task becomes more urgent so all worker inventory
    # reaches the market-side shed before final liquidation.
    drop_priority = 6 if phase != "LIQUIDATE" else 2
    for unit_index, position in enumerate(_unit_positions(view)):
        inventory = _inventory(view, unit_index)
        carrying_animal = any(
            _integer(inventory.get(animal, 0), 0) > 0
            for animal in ANIMAL_RULES
        )
        if _inventory_load(inventory) > 0 and not carrying_animal:
            if _shed_load(view) + _inventory_load(inventory) >= 70 or phase == "LIQUIDATE":
                tasks.append({
                    "kind": "DROP",
                    "pos": _nearest_shed(position, view),
                    "priority": drop_priority,
                    "owner": unit_index,
                })

    # Plant only when a seed is already present.  Market orders execute after
    # unit actions, so a newly purchased seed becomes plantable next turn.
    seeds = _safe_mapping(_safe_mapping(view.get("private")).get("seeds"))
    for position, crop in sorted(_CROP_PLAN.items(), key=lambda item: (item[0][1], item[0][0])):
        if _is_empty_unlocked(view, position) and _integer(seeds.get(crop, 0), 0) > 0:
            tasks.append({"kind": "PLANT", "pos": position, "priority": 7, "crop": crop})

    tasks.sort(
        key=lambda task: (
            _integer(task.get("priority", 99), 99),
            _position(task.get("pos", (0, 0)))[1],
            _position(task.get("pos", (0, 0)))[0],
            task.get("kind", ""),
        )
    )
    return tasks


def _task_action(view, position, task):
    if not isinstance(task, dict):
        return ["PASS"]
    target = _position(task.get("pos", position), position)
    if _position(position) != target:
        return _movement_action(position, target, view)

    kind = str(task.get("kind", "PASS")).upper()
    if kind == "PLANT":
        crop = str(task.get("crop", "WHEAT")).upper()
        return ["PLANT", crop]
    if kind == "PICKUP":
        return ["PICKUP", str(task.get("item", "WHEAT")).upper(), max(1, _integer(task.get("quantity", 1), 1))]
    if kind == "PLACE":
        return ["PLACE", str(task.get("item", "COW")).upper()]
    if kind == "BUILD_COOP":
        return ["BUILD_COOP"]
    if kind == "BUILD_PASTURE":
        return ["BUILD_PASTURE"]
    if kind in {
        "WATER",
        "HARVEST",
        "FEED",
        "CARE",
        "COLLECT_FERTILIZER",
        "DROP",
        "DIG",
        "FERTILIZE",
    }:
        return [kind]
    return ["PASS"]


def _safe_action(hand_count=0):
    hand_count = max(0, _integer(hand_count, 0))
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in range(hand_count)],
        "market": [],
    }


def _order_cost(product, quantity):
    if product in CROP_RULES:
        return CROP_RULES[product]["seed"] * quantity
    if product in ANIMAL_RULES:
        return ANIMAL_RULES[product]["cost"] * quantity
    if product == "WHEAT":
        return _market_price({}, "WHEAT") * quantity
    return 0.0


def _market_orders(view):
    """Build at most ten ordered market actions with a cash shadow balance."""

    if not view.get("valid", False):
        return []
    _ensure_crop_plan(view)
    orders = []
    shadow_money = max(0.0, _number(view.get("money", 0), 0))
    day = view.get("day", 0)
    phase = _phase(day)
    shed = _shed(view)
    pull = _town_pull(view)

    # Sell in small batches while prices are healthy.  Premium resources get a
    # tighter cap because their glut side is much steeper; final-day orders
    # deliberately clear every remaining product.
    active_animals = sum(1 for _, tile in _structures(view) if _animal_at(tile))
    wheat_reserve = max(4, active_animals * 3 + 4)
    products = [
        "FERTILIZER",
        "MILK",
        "WOOL",
        "STRAWBERRY",
        "MELON",
        "TOMATO",
        "CARROT",
        "EGG",
        "WHEAT",
    ]

    def sell_rank(product):
        price = _market_price(view, product)
        base = BASE_PRICES.get(product, 1)
        demand_bonus = 0.025 * pull.get(product, 0)
        return (price / base + demand_bonus, -_sell_loss(product, _market_inventory(view, product), 1))

    products.sort(key=sell_rank, reverse=True)
    sell_budget = 10 if phase == "LIQUIDATE" else (7 if phase == "HARVEST" else 5)
    for product in products:
        if len(orders) >= sell_budget or len(orders) >= MAX_MARKET_ORDERS:
            break
        amount = max(0, _integer(shed.get(product, 0), 0))
        if product == "WHEAT":
            amount = max(0, amount - wheat_reserve)
        if amount <= 0:
            continue
        current_price = _market_price(view, product)
        base = BASE_PRICES.get(product, 1)
        if phase != "LIQUIDATE" and current_price <= max(1, base * 0.35):
            continue
        if phase == "LIQUIDATE":
            quantity = amount
        elif product in {"MELON", "STRAWBERRY", "MILK", "WOOL"}:
            quantity = min(amount, 6 if current_price < base * 1.1 else 10)
        else:
            quantity = min(amount, 12)
        if quantity <= 0:
            continue
        orders.append(["SELL", product, int(quantity)])
        shadow_money += 0.82 * _sell_value(product, _market_inventory(view, product), quantity)

    # Wheat is purchased as feed, not as seed.  A small multi-day buffer avoids
    # a farm-wide starvation cascade when a market queue is temporarily full.
    if len(orders) < MAX_MARKET_ORDERS and active_animals:
        available_wheat = max(0, _integer(shed.get("WHEAT", 0), 0))
        desired_wheat = active_animals * 3 + 6
        needed = max(0, desired_wheat - available_wheat)
        wheat_price = _market_price(view, "WHEAT")
        affordable = int(max(0.0, shadow_money - 200) // max(1.0, wheat_price))
        quantity = min(needed, affordable, 20)
        if quantity > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", quantity])
            shadow_money -= wheat_price * quantity

    # Hire early and at the start of every day.  The engine resets hands at
    # midnight, so this target is deliberately day-specific.
    desired_units = 0
    if view.get("hour", 0) <= 8:
        desired_units = _daily_workforce_target(day)
    current_units = 1 + len(view.get("hands", []))
    remaining_hires = max(0, desired_units - current_units)

    # Estimate the first herd before deciding whether expansion is affordable.
    # The target is computed once so the land gate and the purchase queue use
    # the same demand signal.
    target_animals = _animal_targets(view)
    existing_animals, _ = _existing_animal_counts(view)
    animal_budget = sum(
        max(0, target_animals.get(animal, 0) - existing_animals.get(animal, 0))
        * ANIMAL_RULES[animal]["cost"]
        for animal in ANIMAL_RULES
    )

    # Land is a high-leverage purchase; buy at most one segment per turn and
    # preserve a cash floor for seed/feed and the first animal pipeline.  The
    # first expansion waits until the initial herd has had a chance to start;
    # otherwise its 1000 cost can strand the farm just below animal prices.
    unlocked_count = len(view.get("unlocked_quadrants", []))
    if (
        len(orders) < MAX_MARKET_ORDERS
        and 12 <= day <= 18
        and 0 < unlocked_count < len(LAND_COSTS)
    ):
        land_cost = LAND_COSTS[unlocked_count - 1]
        cash_floor = 900 if day < 12 else 500
        herd_reserve = animal_budget if day >= 8 else 0
        if shadow_money >= land_cost + cash_floor + herd_reserve:
            orders.append(["BUY_LAND"])
            shadow_money -= land_cost

    # Buy the selected herd before discretionary labor.  This keeps a full
    # daily HIRE queue from starving the animal pipeline once the workforce
    # target has intentionally stepped down.
    for animal in ("COW", "SHEEP"):
        if len(orders) >= MAX_MARKET_ORDERS:
            break
        need = max(0, target_animals.get(animal, 0) - existing_animals.get(animal, 0))
        if need <= 0:
            continue
        cost = ANIMAL_RULES[animal]["cost"]
        affordable = int(max(0.0, shadow_money - 400) // cost)
        quantity = min(need, affordable, 5)
        if quantity > 0:
            orders.append(["BUY_ANIMAL", animal, quantity])
            shadow_money -= cost * quantity

    hires_already_queued = _integer(view.get("hires_today", 0), 0)
    while remaining_hires and len(orders) < MAX_MARKET_ORDERS:
        cost = _fib(hires_already_queued)
        if shadow_money < cost + 30:
            break
        orders.append(["HIRE"])
        shadow_money -= cost
        hires_already_queued += 1
        remaining_hires -= 1

    # Seeds are grouped by crop, which leaves order slots for hires and land.
    seeds = _safe_mapping(_safe_mapping(view.get("private")).get("seeds"))
    seed_need = {crop: 0 for crop in CROP_RULES}
    for position, crop in _CROP_PLAN.items():
        if _is_empty_unlocked(view, position):
            seed_need[crop] += 1
    for crop in ("MELON", "STRAWBERRY", "CARROT", "WHEAT", "TOMATO"):
        if len(orders) >= MAX_MARKET_ORDERS:
            break
        quantity = max(0, seed_need[crop] - _integer(seeds.get(crop, 0), 0))
        if quantity <= 0:
            continue
        unit_cost = CROP_RULES[crop]["seed"]
        affordable = int(max(0.0, shadow_money - 200) // unit_cost)
        quantity = min(quantity, affordable, 30)
        if quantity > 0:
            orders.append(["BUY_SEED", crop, quantity])
            shadow_money -= unit_cost * quantity

    return orders[:MAX_MARKET_ORDERS]


def _action_for_unit(view, unit_index, task):
    positions = _unit_positions(view)
    position = positions[unit_index] if unit_index < len(positions) else (0, 0)
    return _task_action(view, position, task)


def agent(observation):
    """Return a complete, validator-safe action for the current turn."""

    global _LAST_STEP
    view = _normalize_observation(observation)
    hand_count = len(view.get("hands", []))
    if not view.get("valid", False):
        return _safe_action(hand_count)

    try:
        step = max(0, _integer(view.get("step", 0), 0))
        if _LAST_STEP >= 0 and step < _LAST_STEP:
            _reset_episode_state()
        _LAST_STEP = step

        tasks = _build_tasks(view)
        assignments = _assign_tasks(view, tasks)
        unit_actions = [
            _action_for_unit(view, index, assignments[index] if index < len(assignments) else None)
            for index in range(hand_count + 1)
        ]
        result = {
            "farmer": unit_actions[0] if unit_actions else ["PASS"],
            "hands": unit_actions[1:],
            "market": _market_orders(view)[:MAX_MARKET_ORDERS],
        }

        # Last-mile contract guard: a malformed internal value degrades to a
        # no-op action while retaining the exact hand count expected by the
        # engine.
        if not isinstance(result["farmer"], list) or not result["farmer"]:
            result["farmer"] = ["PASS"]
        if len(result["hands"]) != hand_count:
            result["hands"] = [["PASS"] for _ in range(hand_count)]
        if not isinstance(result["market"], list):
            result["market"] = []
        return result
    except Exception:
        # Competition agents must never throw because a private field is
        # absent or an engine patch changes a harmless representation.
        return _safe_action(hand_count)


__all__ = [
    "agent",
    "_normalize_observation",
    "_phase",
    "_town_pull",
    "_movement_action",
    "_market_orders",
    "_assign_tasks",
    "_reset_episode_state",
]
