from kaggle_environments import make
import json

"""Kaggriculture scaling baseline."""

MAX_PLANTS = 20
TARGET_HANDS = 4
HAND_COST_MULT = 10
RESERVE_MONEY = 200
DROP_POSITION = (4, 4)

CROP_DATA = {
    "WHEAT": {"seed_cost": 10, "first_yield_day": 2, "harvest_day": 4},
    "CARROT": {"seed_cost": 20, "first_yield_day": 2, "harvest_day": 3},
    "TOMATO": {"seed_cost": 50, "first_yield_day": 8, "harvest_day": 8},
    "STRAWBERRY": {"seed_cost": 100, "first_yield_day": 10, "harvest_day": 10},
    "MELON": {"seed_cost": 80, "first_yield_day": 10, "harvest_day": 12},
}

QUADRANT_RANGES = {
    "NW": (range(0, 5), range(0, 5)),
    "NE": (range(5, 10), range(0, 5)),
    "SW": (range(0, 5), range(5, 10)),
    "SE": (range(5, 10), range(5, 10)),
}

SELLABLE = {
    "WHEAT",
    "CARROT",
    "TOMATO",
    "STRAWBERRY",
    "MELON",
    "EGG",
    "MILK",
    "WOOL",
}

DROP_STATE = {}


def _tile_at(farm, position):
    x, y = position
    tiles = farm.get("tiles", [])
    if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
        return tiles[y][x]
    return None


def _unlocked_positions(farm):
    positions = []
    for quadrant in farm.get("unlocked_quadrants", ["NW"]):
        x_range, y_range = QUADRANT_RANGES.get(quadrant, (range(0), range(0)))
        positions.extend((x, y) for y in y_range for x in x_range)
    return positions


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _direction_towards(current, target):
    cx, cy = current
    tx, ty = target
    if cx < tx:
        return "EAST"
    if cx > tx:
        return "WEST"
    if cy < ty:
        return "SOUTH"
    if cy > ty:
        return "NORTH"
    return "PASS"


def _plant_count(farm):
    return sum(
        isinstance(_tile_at(farm, position), dict)
        and _tile_at(farm, position).get("kind") == "PLANT"
        for position in _unlocked_positions(farm)
    )


def _crop_counts(farm):
    counts = {crop: 0 for crop in CROP_DATA}
    for position in _unlocked_positions(farm):
        tile = _tile_at(farm, position)
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop = tile.get("crop")
            if crop in counts:
                counts[crop] += 1
    return counts


def _crop_targets(farm, day):
    unlocked = len(farm.get("unlocked_quadrants", []))
    expanding = unlocked == 1 and farm.get("money", 0) >= 1200
    total_cells = 50 if expanding or unlocked >= 2 else 25
    tomato = 4 if total_cells >= 50 else 2
    carrot = 6 if total_cells >= 50 else 3
    return {
        "WHEAT": total_cells - tomato - carrot,
        "CARROT": carrot,
        "TOMATO": tomato,
        "STRAWBERRY": 0,
        "MELON": 0,
    }


def _fib(index):
    a, b = 1, 1
    for _ in range(index):
        a, b = b, a + b
    return a


def _hire_cost(start_index, count):
    return HAND_COST_MULT * sum(_fib(start_index + i) for i in range(count))


def _market_actions(farm, private, day):
    money = farm.get("money", 0)
    shed = private.get("shed", {})
    seeds = private.get("seeds", {})
    crop_counts = _crop_counts(farm)
    crop_targets = _crop_targets(farm, day)
    market = []

    buy_land = len(farm.get("unlocked_quadrants", [])) == 1 and money >= 1200
    land_cost = 1000 if buy_land else 0
    if buy_land:
        market.append(["BUY_LAND"])

    current_hands = len(farm.get("hands", []))
    hires_today = farm.get("hires_today", 0)
    missing_hands = max(0, TARGET_HANDS - current_hands - hires_today)

    seed_needs = {
        crop: max(0, crop_targets[crop] - crop_counts[crop] - seeds.get(crop, 0))
        for crop in CROP_DATA
    }
    available = money - land_cost - RESERVE_MONEY

    hires = 0
    while hires < missing_hands and available >= _hire_cost(hires_today + hires, 1):
        cost = _hire_cost(hires_today + hires, 1)
        available -= cost
        hires += 1

    market.extend([["HIRE"] for _ in range(hires)])

    for crop in ("WHEAT", "CARROT", "TOMATO", "MELON", "STRAWBERRY"):
        quantity = min(seed_needs[crop], int(max(0, available) // CROP_DATA[crop]["seed_cost"]))
        if quantity > 0:
            market.append(["BUY_SEED", crop, quantity])
            available -= quantity * CROP_DATA[crop]["seed_cost"]

    for product, quantity in shed.items():
        if product in SELLABLE and quantity > 0:
            market.append(["SELL", product, quantity])

    return market


def _current_action(tile, day):
    if not isinstance(tile, dict):
        return None
    if tile.get("kind") == "WEED":
        return "DIG"
    if tile.get("kind") == "PLANT":
        if not tile.get("watered_today", False):
            return "WATER"
        crop = tile.get("crop")
        crop_data = CROP_DATA.get(crop)
        age = day - tile.get("planted_day", 0)
        if crop_data and tile.get("yield_units", 0) > 0 and age >= crop_data["harvest_day"]:
            return "HARVEST"
    return None


def _build_targets(farm, day, zone):
    unwatered = []
    harvestable = []
    weeds = []
    empty = []

    for position in zone:
        tile = _tile_at(farm, position)
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            if not tile.get("watered_today", False):
                unwatered.append(position)
            crop = tile.get("crop")
            crop_data = CROP_DATA.get(crop)
            age = day - tile.get("planted_day", 0)
            if crop_data and tile.get("yield_units", 0) > 0 and age >= crop_data["harvest_day"]:
                harvestable.append(position)
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            weeds.append(position)
        elif tile is None:
            empty.append(position)

    return unwatered, harvestable, weeds, empty


def _claim_nearest(candidates, current, reserved):
    available = [position for position in candidates if position not in reserved]
    if not available:
        return None
    target = min(available, key=lambda pos: (_distance(current, pos), pos[1], pos[0]))
    reserved.add(target)
    return target


def _choose_plant_crop(farm, planting_budget, day):
    counts = _crop_counts(farm)
    targets = _crop_targets(farm, day)
    available = [crop for crop, quantity in planting_budget.items() if quantity > 0]
    if not available:
        return None
    if day < 4 and "TOMATO" in available and counts.get("TOMATO", 0) < targets.get("TOMATO", 0):
        return "TOMATO"
    deficits = {crop: targets.get(crop, 0) - counts.get(crop, 0) for crop in available}
    useful = [crop for crop in available if deficits[crop] > 0]
    if useful:
        return max(useful, key=lambda crop: (deficits[crop], -CROP_DATA[crop]["seed_cost"]))
    return min(available, key=lambda crop: CROP_DATA[crop]["harvest_day"])


def _unit_action(position, farm, targets, reserved, day, planting_budget):
    tile = _tile_at(farm, position)
    direct_action = _current_action(tile, day)
    if direct_action is not None:
        reserved.add(position)
        return [direct_action]

    unwatered, harvestable, weeds, empty = targets
    for candidates in (unwatered, harvestable, weeds):
        target = _claim_nearest(candidates, position, reserved)
        if target is not None:
            return [_direction_towards(position, target)]

    if any(quantity > 0 for quantity in planting_budget.values()):
        target = _claim_nearest(empty, position, reserved)
        if target is not None:
            if target == position:
                crop = _choose_plant_crop(farm, planting_budget, day)
                if crop is not None:
                    planting_budget[crop] -= 1
                    return ["PLANT", crop]
            return [_direction_towards(position, target)]

    return ["PASS"]


def _zones_for_units(farm):
    positions = sorted(_unlocked_positions(farm), key=lambda pos: (pos[0], pos[1]))
    unit_count = 1 + len(farm.get("hands", []))
    zone_size = (len(positions) + unit_count - 1) // unit_count
    return [positions[start:start + zone_size] for start in range(0, len(positions), zone_size)]


def _optional_drop(player, current, inventory):
    signature = tuple(sorted(inventory.items()))
    state = DROP_STATE.setdefault(player, {"signature": None, "attempted": False})
    if signature != state["signature"]:
        state["signature"] = signature
        state["attempted"] = False
    if inventory and current == DROP_POSITION and not state["attempted"]:
        state["attempted"] = True
        return ["DROP"]
    return None


def agent(obs):
    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]
    day = obs.get("day", 0)
    current = tuple(farm.get("farmer", [0, 0]))
    inventory = private.get("inventories", [{}])[0]

    market = _market_actions(farm, private, day)
    drop_action = _optional_drop(player, current, inventory)
    if drop_action is not None:
        return {"farmer": drop_action, "hands": [], "market": market}

    zones = _zones_for_units(farm)
    reserved = set()
    planting_budget = dict(private.get("seeds", {}))

    farmer_zone = zones[0] if zones else []
    farmer_targets = _build_targets(farm, day, farmer_zone)
    farmer_action = _unit_action(current, farm, farmer_targets, reserved, day, planting_budget)

    hand_actions = []
    for index, hand_position in enumerate(farm.get("hands", []), start=1):
        position = tuple(hand_position)
        zone = zones[index] if index < len(zones) else []
        targets = _build_targets(farm, day, zone)
        action = _unit_action(position, farm, targets, reserved, day, planting_budget)
        hand_actions.append(action)

    return {
        "farmer": farmer_action,
        "hands": hand_actions,
        "market": market,
    }


if __name__ == "__main__":
    print("Kaggriculture scaling agent loaded")


env = make('kaggriculture', configuration={'episodeSteps': 720}, debug=True)
env.run([agent, 'random'])
with open('/kaggle/working/result.json', 'w') as file:
    json.dump(env.toJSON(), file)

final = env.steps[-1]
for index, state in enumerate(final):
    print(f'Player {index}: reward={state.reward}, status={state.status}')
