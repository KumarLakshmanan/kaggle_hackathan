"""Kaggriculture candidate v3: mixed melon/wheat portfolio."""

CROP_COST = {"MELON": 80, "WHEAT": 10}
MAX_AGE = {"MELON": 12, "WHEAT": 4}


def _owned_cells(farm):
    return [
        (x, y, tile)
        for y, row in enumerate(farm["tiles"])
        for x, tile in enumerate(row)
        if tile != "LOCKED"
    ]


def _plant_crop(x, y, day):
    if day > 25:
        return None
    if day > 17:
        return "WHEAT"
    # Three melon lanes finance the season; two wheat lanes create early cash
    # and diversify away from melon's aggressive shared-market price curve.
    return "MELON" if (x + 2 * y) % 5 < 3 else "WHEAT"


def _target_hands(fields):
    return 7 if fields == 1 else 12


def _step_toward(position, target, unit_index):
    x, y = position
    tx, ty = target
    if unit_index % 2 == 0 and x != tx:
        return ["EAST" if tx > x else "WEST"]
    if y != ty:
        return ["SOUTH" if ty > y else "NORTH"]
    if x != tx:
        return ["EAST" if tx > x else "WEST"]
    return ["PASS"]


def _tasks(farm, seed_stock, day):
    tasks = []
    for x, y, tile in _owned_cells(farm):
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop = tile.get("crop")
            age = day - int(tile.get("planted_day", day))
            mature = age >= MAX_AGE.get(crop, 999) and tile.get("yield_units", 0) > 0
            if mature:
                tasks.append((0, x, y, ["HARVEST"]))
            elif not tile.get("watered_today", False):
                tasks.append((0, x, y, ["WATER"]))
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            tasks.append((1, x, y, ["DIG"]))
        elif tile is None:
            crop = _plant_crop(x, y, day)
            if crop and seed_stock.get(crop, 0) > 0:
                tasks.append((2, x, y, ["PLANT", crop]))
    return tasks


def _unit_actions(farm, private, day):
    positions = [farm["farmer"]] + list(farm.get("hands", []))
    stock = {c: int(private.get("seeds", {}).get(c, 0)) for c in CROP_COST}
    remaining = _tasks(farm, stock, day)
    actions = []
    for unit_index, position in enumerate(positions):
        if not remaining:
            actions.append(["PASS"])
            continue
        px, py = position
        usable = [t for t in remaining if t[3][0] != "PLANT" or stock.get(t[3][1], 0) > 0]
        if not usable:
            actions.append(["PASS"])
            continue
        task = min(usable, key=lambda t: (t[0], abs(t[1]-px)+abs(t[2]-py), t[2], t[1]))
        remaining.remove(task)
        _, tx, ty, operation = task
        if (px, py) == (tx, ty):
            if operation[0] == "PLANT":
                stock[operation[1]] -= 1
            actions.append(operation)
        else:
            actions.append(_step_toward((px, py), (tx, ty), unit_index))
    return actions


def agent(obs):
    player = int(obs.get("player", 0))
    farms = obs.get("farms", [])
    if player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    private = obs.get("private", {}) or {}
    day = int(obs.get("day", 0))
    hour = int(obs.get("hour", 0))
    shed = private.get("shed", {}) or {}
    seeds = private.get("seeds", {}) or {}
    market = []

    for item, quantity in shed.items():
        if quantity > 0 and item not in ("GOOSE", "COW", "SHEEP", "FERTILIZER"):
            market.append(["SELL", item, int(quantity)])

    fields = len(farm.get("unlocked_quadrants", []))
    target_hands = _target_hands(fields)
    if hour == 0:
        market.extend([["HIRE"] for _ in range(max(0, target_hands-len(farm.get("hands", []))))])

    # Wheat's first harvest pays for a second 5x5 field without starving the
    # opening melon portfolio of seed capital.
    if day >= 8 and fields < 2 and farm["money"] >= 1800:
        market.append(["BUY_LAND"])

    empty = [(x, y) for x, y, tile in _owned_cells(farm) if tile is None]
    desired = {"MELON": 0, "WHEAT": 0}
    for x, y in empty:
        crop = _plant_crop(x, y, day)
        if crop:
            desired[crop] += 1

    reserve = 700 if fields == 1 else 1200
    cash = max(0, int(farm["money"] - reserve))
    # Buy the expensive crop first; wheat uses whatever small remainder is left.
    for crop in ("MELON", "WHEAT"):
        missing = max(0, desired[crop] - int(seeds.get(crop, 0)))
        amount = min(missing, cash // CROP_COST[crop])
        if amount > 0:
            market.append(["BUY_SEED", crop, amount])
            cash -= amount * CROP_COST[crop]

    actions = _unit_actions(farm, private, day)
    return {"farmer": actions[0] if actions else ["PASS"], "hands": actions[1:], "market": market[:10]}


if __name__ == "__main__":
    print("Kaggriculture Agent v3 mixed portfolio")
