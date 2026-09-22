"""Kaggriculture baseline 1: long-horizon melon monoculture."""

CROPS = {
    "WHEAT": {"first": 2, "max_day": 4, "yield": 6, "seed": 10},
    "CARROT": {"first": 2, "max_day": 3, "yield": 4, "seed": 20},
    "TOMATO": {"first": 8, "max_day": 8, "yield": 4, "seed": 50},
    "STRAWBERRY": {"first": 10, "max_day": 10, "yield": 4, "seed": 100},
    "MELON": {"first": 10, "max_day": 12, "yield": 6, "seed": 80},
}

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
TARGET_CROP = "MELON"
TARGET_TILES = 25
HANDS_PER_DAY = 8
LAST_PLANT_DAY = 16


def _move_toward(position, target, step, unit_index):
    x, y = position
    tx, ty = target
    horizontal_first = (step + unit_index) % 2 == 0
    if horizontal_first and x != tx:
        return ["EAST" if tx > x else "WEST"]
    if y != ty:
        return ["SOUTH" if ty > y else "NORTH"]
    if x != tx:
        return ["EAST" if tx > x else "WEST"]
    return ["PASS"]


def _field_cells(farm):
    cells = []
    for y, row in enumerate(farm["tiles"]):
        xs = range(len(row)) if y % 2 == 0 else range(len(row) - 1, -1, -1)
        for x in xs:
            if row[x] != "LOCKED":
                cells.append((x, y))
    return cells[:TARGET_TILES]


def _build_tasks(obs, farm, private):
    day = int(obs.get("day", 0))
    seeds_left = int(private.get("seeds", {}).get(TARGET_CROP, 0))
    tasks = []
    for x, y in _field_cells(farm):
        tile = farm["tiles"][y][x]
        if tile is None:
            if day <= LAST_PLANT_DAY and seeds_left > 0:
                tasks.append((3, (x, y), ["PLANT", TARGET_CROP]))
                seeds_left -= 1
            continue
        if not isinstance(tile, dict):
            continue
        if tile.get("kind") == "WEED":
            tasks.append((2, (x, y), ["DIG"]))
            continue
        if tile.get("kind") != "PLANT":
            continue
        crop = tile.get("crop")
        crop_info = CROPS.get(crop, CROPS[TARGET_CROP])
        age = day - int(tile.get("planted_day", day))
        available = int(tile.get("yield_units", 0))
        should_harvest = age >= crop_info["max_day"]
        if day >= 28 and age >= crop_info["first"] and available > 0:
            should_harvest = True
        if should_harvest and available > 0:
            tasks.append((0, (x, y), ["HARVEST"]))
        elif not tile.get("watered_today", False):
            tasks.append((1, (x, y), ["WATER"]))
    return tasks


def _assign_tasks(obs, farm, private):
    step = int(obs.get("step", 0))
    positions = [farm["farmer"]] + list(farm.get("hands", []))
    inventories = list(private.get("inventories", []))
    actions = [["PASS"] for _ in positions]
    available_units = []

    # Bank harvests quickly instead of waiting for the end-of-day auto-drop.
    for idx, position in enumerate(positions):
        inventory = inventories[idx] if idx < len(inventories) else {}
        if sum(int(v) for v in inventory.values()) > 0:
            if tuple(position) == (4, 4):
                actions[idx] = ["DROP"]
            else:
                actions[idx] = _move_toward(position, (4, 4), step, idx)
        else:
            available_units.append(idx)

    tasks = _build_tasks(obs, farm, private)
    for priority in (0, 1, 2, 3):
        pending = [task for task in tasks if task[0] == priority]
        while pending and available_units:
            best = None
            for task_index, task in enumerate(pending):
                tx, ty = task[1]
                for unit_index in available_units:
                    ux, uy = positions[unit_index]
                    candidate = (abs(ux - tx) + abs(uy - ty), task_index, unit_index)
                    if best is None or candidate < best:
                        best = candidate
            _, task_index, unit_index = best
            _, target, operation = pending.pop(task_index)
            available_units.remove(unit_index)
            if tuple(positions[unit_index]) == target:
                actions[unit_index] = operation
            else:
                actions[unit_index] = _move_toward(positions[unit_index], target, step, unit_index)
    return actions


def _market_orders(obs, farm, private):
    day = int(obs.get("day", 0))
    hour = int(obs.get("hour", 0))
    shed = private.get("shed", {})
    seeds = private.get("seeds", {})
    orders = []

    for product in PRODUCTS:
        amount = int(shed.get(product, 0))
        if amount > 0:
            orders.append(["SELL", product, amount])

    if hour == 0:
        orders.extend([["HIRE"] for _ in range(HANDS_PER_DAY)])

    if day <= LAST_PLANT_DAY:
        planted = 0
        for x, y in _field_cells(farm):
            tile = farm["tiles"][y][x]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == TARGET_CROP:
                planted += 1
        need = max(0, TARGET_TILES - planted - int(seeds.get(TARGET_CROP, 0)))
        affordable = max(0, int(farm["money"]) // CROPS[TARGET_CROP]["seed"])
        if need > 0 and affordable > 0:
            orders.append(["BUY_SEED", TARGET_CROP, min(need, affordable)])
    return orders[:10]


def agent(obs):
    player = int(obs.get("player", 0))
    farms = obs.get("farms", [])
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    private = obs.get("private", {}) or {}
    actions = _assign_tasks(obs, farm, private)
    return {
        "farmer": actions[0] if actions else ["PASS"],
        "hands": actions[1:],
        "market": _market_orders(obs, farm, private),
    }
