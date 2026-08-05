"""Kaggriculture submission agent.

The agent is deliberately self-contained: Kaggle submissions are loaded from a
single main.py and receive only the public observation plus the player's
private inventory.
"""

from math import sqrt, log


CROPS = {
    "WHEAT": {"seed": 10, "first": 2, "max_day": 4, "max_yield": 6, "ongoing": False},
    "CARROT": {"seed": 20, "first": 2, "max_day": 3, "max_yield": 4, "ongoing": False},
    "TOMATO": {"seed": 50, "first": 8, "max_day": 8, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_day": 10, "max_yield": 4, "ongoing": True},
    "MELON": {"seed": 80, "first": 10, "max_day": 12, "max_yield": 6, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP", "product": "EGG", "interval": 1, "first": 4, "max_held": 4},
    "COW": {"cost": 400, "structure": "PASTURE", "product": "MILK", "interval": 2, "first": 8, "max_held": 6},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "product": "WOOL", "interval": 3, "first": 6, "max_held": 6},
}

# The initial portfolio fits in the NW 5x5 quadrant.  It is intentionally
# diversified because premium resources crash very quickly when dumped.
BASE_CROP_TARGETS = {
    "WHEAT": 4,
    "CARROT": 3,
    "TOMATO": 0,
    "STRAWBERRY": 0,
    "MELON": 19,
}
BASE_ANIMAL_TARGETS = {"GOOSE": 0, "COW": 0, "SHEEP": 1}

# Tuned locally.  The initial quadrant has enough room for this portfolio, so
# expansion costs are not recovered before the season ends.
HAND_COUNT = 7
ENABLE_SCALE_UP = False
ENABLE_LAND_EXPANSION = False
FERTILIZE_MELON_ONLY = False
BUY_EXTRA_FERTILIZER = False

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

# Selling in small lots keeps the market from self-crashing.  At the end of
# the season the emergency path sells everything because unsold goods have no
# value in the final reward.
SELL_FLOORS = {
    "WHEAT": 30,
    "CARROT": 40,
    "TOMATO": 34,
    "STRAWBERRY": 72,
    "MELON": 262,
    "EGG": 30,
    "MILK": 92,
    "WOOL": 115,
    "FERTILIZER": 55,
}
SELL_BATCHES = {
    "WHEAT": 1,
    "CARROT": 1,
    "TOMATO": 1,
    "STRAWBERRY": 1,
    "MELON": 1,
    "EGG": 1,
    "MILK": 1,
    "WOOL": 1,
    "FERTILIZER": 1,
}
LATE_SELL_START = 26
LATE_SELL_BATCHES = {}

PRODUCTS = tuple(SELL_FLOORS)
STRUCTURE_SPOTS = ((4, 4), (4, 3), (3, 4), (3, 3), (4, 2), (2, 4), (3, 2), (2, 3), (2, 2))
SHED_SPOTS = ((4, 4), (5, 4), (4, 5), (5, 5))


def _tile(farm, pos):
    x, y = pos
    if 0 <= y < len(farm["tiles"]) and 0 <= x < len(farm["tiles"]):
        return farm["tiles"][y][x]
    return "LOCKED"


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _step_toward(pos, target):
    x, y = pos
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


def _is_shed_spot(pos):
    return tuple(pos) in SHED_SPOTS


def _unit_position(farm, idx):
    if idx == 0:
        return tuple(farm["farmer"])
    hands = farm.get("hands", [])
    if idx - 1 < len(hands):
        return tuple(hands[idx - 1])
    return None


def _unit_inventory(private, idx):
    inventories = private.get("inventories", []) or []
    if idx < len(inventories):
        return inventories[idx]
    return {}


def _all_tiles(farm):
    size = len(farm["tiles"])
    for y in range(size):
        for x in range(size):
            yield (x, y), farm["tiles"][y][x]


def _count_assets(farm):
    crops = {name: 0 for name in CROPS}
    animals = {name: 0 for name in ANIMALS}
    structures = {"COOP": [], "PASTURE": []}
    empty = []
    weeds = []
    plants = []
    for pos, tile in _all_tiles(farm):
        if tile is None:
            empty.append(pos)
        elif isinstance(tile, dict):
            kind = tile.get("kind")
            if kind == "PLANT":
                crops[tile.get("crop")] = crops.get(tile.get("crop"), 0) + 1
                plants.append((pos, tile))
            elif kind == "WEED":
                weeds.append(pos)
            elif kind in structures:
                structures[kind].append((pos, tile))
                if tile.get("animal") in animals:
                    animals[tile["animal"]] += 1
    return crops, animals, structures, empty, weeds, plants


def _targets(day, money, unlocked):
    crops = dict(BASE_CROP_TARGETS)
    animals = dict(BASE_ANIMAL_TARGETS)

    # Once the first short crops have paid back the opening investment, add a
    # small second production block.  Expansion is bought before using it.
    if ENABLE_SCALE_UP and len(unlocked) >= 2 and day >= 12 and money >= 6500:
        crops["WHEAT"] += 2
        crops["CARROT"] += 2
        crops["TOMATO"] += 1
        crops["MELON"] += 1
        animals["SHEEP"] += 1
    if ENABLE_SCALE_UP and len(unlocked) >= 3 and day >= 18 and money >= 10500:
        crops["WHEAT"] += 2
        crops["CARROT"] += 2
        crops["TOMATO"] += 1
        animals["GOOSE"] += 2
    return crops, animals


def _market_price(item, inventory):
    """Mirror the competition's default price curve for sell planning."""
    base = BASE_PRICES[item]
    i0 = 10000
    specs = {
        "WHEAT": (400, "sqrt", 0.80, "log", 0.20),
        "CARROT": (450, "log", 0.20, "sqrt", 0.70),
        "TOMATO": (200, "linear", 0.40, "sqrt", 0.60),
        "STRAWBERRY": (100, "sqrt", 0.70, "linear", 1.60),
        "MELON": (300, "log", 0.20, "sq", 3.60),
        "EGG": (332, "linear", 0.40, "log", 0.20),
        "MILK": (122, "sqrt", 0.60, "linear", 1.60),
        "WOOL": (105, "log", 0.20, "sq", 3.20),
        "FERTILIZER": (200, "linear", 0.40, "linear", 0.40),
    }
    t, below_func, below_target, above_func, above_target = specs[item]

    def shape(name, x):
        if name == "linear":
            return x
        if name == "sq":
            return x * x
        if name == "sqrt":
            return sqrt(x)
        if name == "log":
            return log(1 + x)
        return log(1 + x, 10)

    if inventory < i0:
        amp = below_target * base / shape(below_func, t)
        value = base + amp * shape(below_func, i0 - inventory)
    else:
        amp = above_target * base / shape(above_func, t)
        value = base - amp * shape(above_func, inventory - i0)
    return max(1, int(round(value)))


def _plant_records(farm):
    return [(pos, tile) for pos, tile in _all_tiles(farm)
            if isinstance(tile, dict) and tile.get("kind") == "PLANT"]


def _animal_records(farm):
    return [(pos, tile) for pos, tile in _all_tiles(farm)
            if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE")
            and tile.get("animal") in ANIMALS]


def _structure_records(farm):
    return [(pos, tile) for pos, tile in _all_tiles(farm)
            if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE")]


def _count_inventory(private, item):
    total = int((private.get("shed", {}) or {}).get(item, 0))
    for inv in private.get("inventories", []) or []:
        total += int((inv or {}).get(item, 0))
    return total


def _need_seed_orders(farm, private, day, targets):
    crops, _, _, _, _, _ = _count_assets(farm)
    orders = []
    for crop, wanted in targets.items():
        data = CROPS[crop]
        if day + data["max_day"] > 29 and not data["ongoing"]:
            continue
        owned = crops.get(crop, 0) + int((private.get("seeds", {}) or {}).get(crop, 0))
        need = max(0, wanted - owned)
        if need:
            orders.append(["BUY_SEED", crop, need])
    return orders


def _need_animal_orders(farm, private, targets):
    _, animals, _, _, _, _ = _count_assets(farm)
    orders = []
    for name, wanted in targets.items():
        owned = animals.get(name, 0) + _count_inventory(private, name)
        need = max(0, wanted - owned)
        if need:
            orders.append(["BUY_ANIMAL", name, need])
    return orders


def _sell_orders(obs, day):
    private = obs.get("private", {}) or {}
    shed = private.get("shed", {}) or {}
    market = obs.get("market", {}) or {}
    prices = market.get("prices", {}) or {}
    inventory = market.get("inventory", {}) or {}
    orders = []
    for item in PRODUCTS:
        amount = int(shed.get(item, 0))
        if amount <= 0:
            continue
        price = int(prices.get(item, _market_price(item, inventory.get(item, 10000))))
        if day >= 28 or price >= SELL_FLOORS[item]:
            if day >= 28:
                batch = amount
            elif day >= LATE_SELL_START and item in LATE_SELL_BATCHES:
                batch = min(amount, LATE_SELL_BATCHES[item])
            else:
                batch = min(amount, SELL_BATCHES[item])
            if batch > 0:
                orders.append(["SELL", item, batch])
    return orders


def _animal_task_candidates(farm, private, day, reserved):
    """Return high-priority tasks for animals and carried goods."""
    tasks = []
    shed = private.get("shed", {}) or {}
    inventories = private.get("inventories", []) or []
    animal_records = _animal_records(farm)
    structure_records = _structure_records(farm)

    for idx, inv in enumerate(inventories):
        inv = inv or {}
        for animal, data in ANIMALS.items():
            if inv.get(animal, 0) > 0:
                for pos, tile in structure_records:
                    if tile.get("kind") == data["structure"] and not tile.get("animal"):
                        if pos not in reserved:
                            tasks.append({"priority": 1, "pos": pos, "action": ["PLACE", animal], "reserve": pos})
                        break

    # Animals in the shed need a matching structure before they can be used.
    for animal, data in ANIMALS.items():
        shed_count = int(shed.get(animal, 0))
        if shed_count <= 0:
            continue
        structures = [pos for pos, tile in _all_tiles(farm)
                      if isinstance(tile, dict) and tile.get("kind") == data["structure"]
                      and not tile.get("animal")]
        missing = max(0, shed_count - len(structures))
        if missing:
            free = [pos for pos, tile in _all_tiles(farm)
                    if tile is None and pos not in reserved]
            free.sort(key=lambda pos: (pos not in STRUCTURE_SPOTS, _dist(pos, (4, 4)), pos[1], pos[0]))
            for pos in free[:missing]:
                tasks.append({"priority": 2, "pos": pos,
                              "action": ["BUILD_COOP" if data["structure"] == "COOP" else "BUILD_PASTURE"],
                              "reserve": pos})
        if structures:
            for shed_pos in SHED_SPOTS:
                if _tile(farm, shed_pos) != "LOCKED" and shed_pos not in reserved:
                    tasks.append({"priority": 3, "pos": shed_pos, "action": ["PICKUP", animal, 1],
                                  "reserve": shed_pos, "item": animal})
                    break

    # Carried wheat/fertilizer is routed to the next useful animal/plant.
    for idx, inv in enumerate(inventories):
        inv = inv or {}
        if inv.get("WHEAT", 0) > 0:
            for pos, tile in animal_records:
                if not tile.get("fed_today") and pos not in reserved:
                    tasks.append({"priority": 4, "pos": pos, "action": ["FEED"], "reserve": pos})
                    break
        if inv.get("FERTILIZER", 0) > 0:
            candidates = []
            for pos, tile in _plant_records(farm):
                crop = tile.get("crop")
                if crop in CROPS and tile.get("fertilized_until_day", -1) < day:
                    if FERTILIZE_MELON_ONLY and crop != "MELON":
                        continue
                    age = day - tile.get("planted_day", day)
                    if CROPS[crop]["ongoing"]:
                        # Ongoing crops only benefit on scheduled production
                        # days; apply just before their first production.
                        eligible = age >= CROPS[crop]["first"] - 1
                    else:
                        # One-time crops have a three-day bonus window.  Using
                        # fertilizer at its start covers that window exactly;
                        # applying it earlier expires before any bonus applies.
                        window_start = (CROPS[crop]["max_day"] + 1) // 2
                        eligible = age == window_start
                    if eligible and age <= CROPS[crop]["max_day"]:
                        candidates.append((pos, tile))
            if candidates:
                fert_priority = {"MELON": 0, "STRAWBERRY": 1, "TOMATO": 2, "CARROT": 3, "WHEAT": 4}
                pos, _ = min(candidates, key=lambda item: (
                    fert_priority.get(item[1].get("crop"), 9),
                    abs((day - item[1].get("planted_day", day)) - ((CROPS[item[1].get("crop")]["max_day"] + 1) // 2)),
                    _dist(item[0], (4, 4)),
                ))
                if pos not in reserved:
                    tasks.append({"priority": 7, "pos": pos, "action": ["FERTILIZE"], "reserve": pos})

    # If an animal still needs feed and this unit has no wheat, send it to the
    # shed.  The pickup amount is one because each unit can service one animal
    # without carrying a large load around the map.
    needs_feed = any(not tile.get("fed_today") for _, tile in animal_records)
    if needs_feed and shed.get("WHEAT", 0) > 0:
        for shed_pos in SHED_SPOTS:
            if _tile(farm, shed_pos) != "LOCKED" and shed_pos not in reserved:
                tasks.append({"priority": 5, "pos": shed_pos, "action": ["PICKUP", "WHEAT", 1],
                              "reserve": shed_pos, "item": "WHEAT"})
                break

    # Fertilizer collection is free income; it is lower priority than survival
    # and crop watering but normally gets serviced by spare hands.
    for pos, tile in animal_records:
        if tile.get("fertilizer_available") and pos not in reserved:
            tasks.append({"priority": 8, "pos": pos, "action": ["COLLECT_FERTILIZER"], "reserve": pos})
    return tasks


def _plant_task_candidates(farm, private, day, targets, reserved):
    tasks = []
    crops, _, structures, empty, weeds, plants = _count_assets(farm)
    seeds = private.get("seeds", {}) or {}
    need_structure = any(
        (private.get("shed", {}) or {}).get(animal, 0) > 0
        and not any(tile.get("animal") == animal for _, tile in _animal_records(farm))
        for animal in ANIMALS
    )

    # Water first; a plant that misses two consecutive end-of-day refreshes is
    # irrecoverably converted to a weed.
    for pos, tile in plants:
        if not tile.get("watered_today") and pos not in reserved:
            tasks.append({"priority": 6, "pos": pos, "action": ["WATER"], "reserve": pos})

    # Harvest mature one-time crops and all available ongoing output.  Harvest
    # before the yield cap is reached for animals/ongoing plants.
    for pos, tile in plants:
        crop = tile.get("crop")
        age = day - tile.get("planted_day", day)
        mature = age >= CROPS.get(crop, {}).get("max_day", 999)
        if crop in CROPS and ((not CROPS[crop]["ongoing"] and mature) or
                              (CROPS[crop]["ongoing"] and tile.get("yield_units", 0) > 0)):
            if pos not in reserved:
                tasks.append({"priority": 9, "pos": pos, "action": ["HARVEST"], "reserve": pos})

    # Clear weeds so a crop slot can be reused.  Keep central structure spots
    # available while purchased animals are still waiting in the shed.
    for pos in weeds:
        if pos not in reserved:
            tasks.append({"priority": 10, "pos": pos, "action": ["DIG"], "reserve": pos})

    # Plant in unlocked empty tiles.  The central positions are preferred for
    # animal structures until all purchased animals have been placed.
    free = [pos for pos in empty if pos not in reserved]
    if need_structure:
        free = [pos for pos in free if pos not in STRUCTURE_SPOTS] or free
    free.sort(key=lambda pos: (_dist(pos, (4, 4)), pos[1], pos[0]))
    for crop, wanted in targets.items():
        data = CROPS[crop]
        if day + data["max_day"] > 29 and not data["ongoing"]:
            continue
        available = int(seeds.get(crop, 0))
        for _ in range(min(available, max(0, wanted - crops.get(crop, 0)))):
            if not free:
                break
            pos = free.pop(0)
            tasks.append({"priority": 11, "pos": pos, "action": ["PLANT", crop], "reserve": pos})
    return tasks


def _task_action(farm, pos, task):
    if pos == task["pos"]:
        return task["action"]
    return _step_toward(pos, task["pos"])


def _unit_action(farm, private, idx, day, targets, reserved):
    pos = _unit_position(farm, idx)
    if pos is None:
        return ["PASS"]
    tile = _tile(farm, pos)
    inv = _unit_inventory(private, idx) or {}
    candidates = []

    # Immediate operation on the current tile is generally more valuable than
    # walking to another task, especially for feeding/watering.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop = tile.get("crop")
        age = day - tile.get("planted_day", day)
        if not tile.get("watered_today"):
            candidates.append({"priority": 0, "pos": pos, "action": ["WATER"], "reserve": pos})
        elif crop in CROPS and not CROPS[crop]["ongoing"] and age >= CROPS[crop]["max_day"] and tile.get("yield_units", 0) > 0:
            candidates.append({"priority": 0, "pos": pos, "action": ["HARVEST"], "reserve": pos})
    elif isinstance(tile, dict) and tile.get("animal") in ANIMALS:
        if inv.get("WHEAT", 0) > 0 and not tile.get("fed_today"):
            candidates.append({"priority": 0, "pos": pos, "action": ["FEED"], "reserve": pos})
        elif not tile.get("cared_today"):
            candidates.append({"priority": 1, "pos": pos, "action": ["CARE"], "reserve": pos})
        elif tile.get("yield_units", 0) > 0:
            candidates.append({"priority": 2, "pos": pos, "action": ["HARVEST"], "reserve": pos})
        elif tile.get("fertilizer_available"):
            candidates.append({"priority": 8, "pos": pos, "action": ["COLLECT_FERTILIZER"], "reserve": pos})

    candidates.extend(_animal_task_candidates(farm, private, day, reserved))
    candidates.extend(_plant_task_candidates(farm, private, day, targets, reserved))

    # If this unit is carrying something that must be dropped and has no useful
    # operation, return it to the shed instead of letting shed capacity overflow
    # at the end of the day.
    if inv and not any(item in ANIMALS or item in ("WHEAT", "FERTILIZER") for item in inv):
        for shed_pos in SHED_SPOTS:
            if _tile(farm, shed_pos) != "LOCKED" and shed_pos not in reserved:
                candidates.append({"priority": 12, "pos": shed_pos, "action": ["DROP"], "reserve": shed_pos})
                break

    if not candidates:
        return ["PASS"]
    candidates.sort(key=lambda item: (item["priority"], _dist(pos, item["pos"]), item["pos"][1], item["pos"][0]))
    chosen = candidates[0]
    reserved.add(chosen.get("reserve", chosen["pos"]))
    action = _task_action(farm, pos, chosen)
    return action or ["PASS"]


def _market_orders(obs, day, hour, targets, animal_targets):
    farm = obs["farms"][obs["player"]]
    private = obs.get("private", {}) or {}
    orders = []

    # Hire six hands daily.  Six costs 20 coins/day and leaves enough labor to
    # maintain the portfolio while the main farmer handles setup/transport.
    if hour == 0:
        orders.extend([["HIRE"] for _ in range(HAND_COUNT)])

    # Seed/animal purchases are spread across the first two hours so hiring
    # never crowds them out of the ten-order limit.
    if hour in (0, 1, 2):
        orders.extend(_need_seed_orders(farm, private, day, targets))
        orders.extend(_need_animal_orders(farm, private, animal_targets))

    # Keep enough wheat on hand for today's unfed animals plus one reserve day.
    animal_records = _animal_records(farm)
    fed = sum(1 for _, tile in animal_records if tile.get("fed_today"))
    feed_need = max(0, len(animal_records) - fed)
    available_wheat = _count_inventory(private, "WHEAT")
    if feed_need and available_wheat < feed_need + 2:
        orders.append(["BUY_PRODUCT", "WHEAT", max(4, feed_need + 4 - available_wheat)])

    if BUY_EXTRA_FERTILIZER and 3 <= day <= 9:
        plants = _plant_records(farm)
        melon_plants = [tile for _, tile in plants if tile.get("crop") == "MELON"]
        applied = sum(1 for tile in melon_plants if tile.get("fertilized_until_day", -1) >= day)
        available = _count_inventory(private, "FERTILIZER")
        need = max(0, len(melon_plants) - applied - available)
        fertilizer_price = int((obs.get("market", {}) or {}).get("prices", {}).get("FERTILIZER", 100))
        if need > 0 and farm.get("money", 0) >= fertilizer_price:
            orders.append(["BUY_PRODUCT", "FERTILIZER", 1])

    # Expand only after the current block has paid for itself.  The extra land
    # is useful because the second target block is not attempted otherwise.
    if ENABLE_LAND_EXPANSION and hour == 0 and len(farm.get("unlocked_quadrants", [])) < 2 and farm.get("money", 0) >= 6500:
        orders.append(["BUY_LAND"])
    elif ENABLE_LAND_EXPANSION and hour == 0 and len(farm.get("unlocked_quadrants", [])) < 3 and farm.get("money", 0) >= 10500:
        orders.append(["BUY_LAND"])

    orders.extend(_sell_orders(obs, day))
    return orders[:10]


def agent(obs):
    farms = obs.get("farms", []) or []
    player = int(obs.get("player", 0))
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    day = int(obs.get("day", 0))
    hour = int(obs.get("hour", 0))
    targets, animal_targets = _targets(day, float(farm.get("money", 0)), farm.get("unlocked_quadrants", []))
    market = _market_orders(obs, day, hour, targets, animal_targets)

    reserved = set()
    farmer_action = _unit_action(farm, obs.get("private", {}) or {}, 0, day, targets, reserved)
    hand_actions = []
    for idx in range(len(farm.get("hands", []) or [])):
        hand_actions.append(_unit_action(farm, obs.get("private", {}) or {}, idx + 1, day, targets, reserved))

    return {"farmer": farmer_action, "hands": hand_actions, "market": market}


# The competition loader accepts any callable named agent.  Keeping this alias
# also makes local smoke tests easy to read.
my_agent = agent
