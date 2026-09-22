"""Kaggriculture smoke agent: a deterministic carrot fleet.

The policy is intentionally small and original.  It uses the unlocked field,
hires a modest daily crew, keeps carrots watered, harvests at full yield, and
sells everything that reaches the shed.
"""

from collections import deque


CROP = "CARROT"
SEED_COST = 20
MAX_YIELD_DAY = 3
LAST_PLANT_DAY = 26
TARGET_HANDS = 6


def _move_toward(tiles, start, target):
    """Return one shortest legal movement action."""
    start = tuple(start)
    target = tuple(target)
    if start == target:
        return ["PASS"]

    size = len(tiles)
    queue = deque([start])
    parent = {start: None}
    arrival = {}
    directions = (
        (1, 0, "EAST"),
        (0, 1, "SOUTH"),
        (-1, 0, "WEST"),
        (0, -1, "NORTH"),
    )

    while queue:
        x, y = queue.popleft()
        if (x, y) == target:
            break
        for dx, dy, action in directions:
            nxt = (x + dx, y + dy)
            if not (0 <= nxt[0] < size and 0 <= nxt[1] < size):
                continue
            if nxt in parent or tiles[nxt[1]][nxt[0]] == "LOCKED":
                continue
            parent[nxt] = (x, y)
            arrival[nxt] = action
            queue.append(nxt)

    if target not in parent:
        return ["PASS"]

    cursor = target
    while parent[cursor] != start:
        cursor = parent[cursor]
        if cursor is None:
            return ["PASS"]
    return [arrival[cursor]]


def _jobs(obs, farm, private):
    day = int(obs.get("day", 0))
    seeds = int((private.get("seeds") or {}).get(CROP, 0))
    jobs = []

    for y, row in enumerate(farm.get("tiles") or []):
        for x, tile in enumerate(row):
            if tile == "LOCKED":
                continue
            if tile is None:
                if day <= LAST_PLANT_DAY and seeds > 0:
                    jobs.append((3, x, y, ["PLANT", CROP]))
                continue
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "WEED":
                jobs.append((0, x, y, ["DIG"]))
                continue
            if tile.get("kind") != "PLANT" or tile.get("crop") != CROP:
                continue

            age = day - int(tile.get("planted_day", day))
            if age >= MAX_YIELD_DAY and int(tile.get("yield_units", 0)) > 0:
                jobs.append((1, x, y, ["HARVEST"]))
            elif not tile.get("watered_today", False):
                urgent = int(tile.get("consecutive_unwatered", 0)) > 0
                jobs.append((0 if urgent else 2, x, y, ["WATER"]))

    return jobs


def _unit_actions(obs, farm, private):
    positions = [tuple(farm.get("farmer", [0, 0]))]
    positions.extend(tuple(pos) for pos in (farm.get("hands") or []))
    tasks = _jobs(obs, farm, private)
    tiles = farm.get("tiles") or []
    actions = [["PASS"] for _ in positions]
    free_tasks = set(range(len(tasks)))
    seeds_left = int((private.get("seeds") or {}).get(CROP, 0))

    for unit_index, position in enumerate(positions):
        choices = []
        for task_index in free_tasks:
            priority, x, y, task_action = tasks[task_index]
            distance = abs(position[0] - x) + abs(position[1] - y)
            choices.append((priority, distance, y, x, task_index, task_action))
        if not choices:
            continue

        _, _, y, x, task_index, task_action = min(choices)
        if position == (x, y):
            if task_action[0] == "PLANT":
                if seeds_left <= 0:
                    continue
                seeds_left -= 1
            actions[unit_index] = task_action
        else:
            actions[unit_index] = _move_toward(tiles, position, (x, y))
        free_tasks.remove(task_index)

    return actions


def _market_actions(obs, farm, private):
    day = int(obs.get("day", 0))
    hour = int(obs.get("hour", 0))
    shed = private.get("shed") or {}
    seeds = private.get("seeds") or {}
    orders = []
    money = float(farm.get("money", 0))

    carrots = int(shed.get(CROP, 0))
    if carrots > 0:
        orders.append(["SELL", CROP, carrots])

    if day <= LAST_PLANT_DAY:
        empty = sum(
            tile is None
            for row in (farm.get("tiles") or [])
            for tile in row
        )
        wanted = max(0, empty - int(seeds.get(CROP, 0)))
        affordable = max(0, int((money - 100) // SEED_COST))
        quantity = min(wanted, affordable)
        if quantity > 0:
            orders.append(["BUY_SEED", CROP, quantity])

    if hour == 0:
        missing = max(0, TARGET_HANDS - len(farm.get("hands") or []))
        orders.extend([["HIRE"] for _ in range(missing)])

    return orders[:10]


def _agent(obs):
    farms = obs.get("farms") or []
    player = int(obs.get("player", 0))
    if not farms or not (0 <= player < len(farms)):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    private = obs.get("private") or {}
    actions = _unit_actions(obs, farm, private)
    return {
        "farmer": actions[0] if actions else ["PASS"],
        "hands": actions[1:],
        "market": _market_actions(obs, farm, private),
    }


def agent(obs):
    """Kaggle entry point with a contract-safe fallback."""
    try:
        return _agent(obs)
    except Exception:
        try:
            farms = obs.get("farms") or []
            player = int(obs.get("player", 0))
            hand_count = len(farms[player].get("hands") or [])
        except Exception:
            hand_count = 0
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(hand_count)],
            "market": [],
        }