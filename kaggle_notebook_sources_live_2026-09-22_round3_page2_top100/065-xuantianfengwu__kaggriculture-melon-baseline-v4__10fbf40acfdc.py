%pip install -q --upgrade kaggle-environments==1.32.7

from pathlib import Path
import importlib.util
import importlib.metadata
from kaggle_environments import make
print("kaggle-environments:", importlib.metadata.version("kaggle-environments"))

%%writefile submission_v3.py
"""Kaggriculture v3: diversified, staggered, market-aware baseline."""

import math

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS


BASE_PLAN = (
    [("MELON", 0)] * 16
    + [("TOMATO", 0)] * 9
)
EXTRA_PLAN = [("STRAWBERRY", 0)] * 5 + [("TOMATO", 0)] * 5
SELL_FLOORS = {
    "WHEAT": 18,
    "CARROT": 27,
    "TOMATO": 45,
    "STRAWBERRY": 90,
    "MELON": 180,
}
SELL_CAPS = {
    "WHEAT": 10,
    "CARROT": 8,
    "TOMATO": 8,
    "STRAWBERRY": 6,
    "MELON": 6,
}
SELL_ORDER = ("MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT")
LAND_COSTS = (1000, 2000, 4000)


def _pass(hand_count=0):
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in range(hand_count)],
        "market": [],
    }


def _quadrant(x, y, size):
    half = size // 2
    return ("S" if y >= half else "N") + ("E" if x >= half else "W")


def _ordered_tiles(farm, quadrant):
    size = len(farm.get("tiles", []))
    points = []
    for y, row in enumerate(farm.get("tiles", [])):
        for x, tile in enumerate(row):
            if tile != "LOCKED" and _quadrant(x, y, size) == quadrant:
                points.append((abs(x - 4) + abs(y - 4), y, x))
    points.sort()
    return [(x, y) for _, y, x in points]


def _crop_plan(farm):
    quadrants = list(farm.get("unlocked_quadrants", []) or ["NW"])
    plan = {}
    base = _ordered_tiles(farm, "NW")
    for pos, spec in zip(base, BASE_PLAN):
        plan[pos] = spec
    for quadrant in quadrants:
        if quadrant == "NW":
            continue
        for pos, spec in zip(_ordered_tiles(farm, quadrant), EXTRA_PLAN):
            plan[pos] = spec
    return plan


def _can_still_plant(crop, day):
    # Leave one full day after first maturity for harvesting and liquidation.
    return day + int(CROPS[crop]["first_yield_day"]) <= 28


def _task_list(obs, farm, private):
    day = int(obs.get("day", 0))
    seeds = dict(private.get("seeds", {}) or {})
    tasks = []
    for (x, y), (planned_crop, start_day) in _crop_plan(farm).items():
        tile = farm["tiles"][y][x]
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            actual_crop = tile.get("crop")
            crop_data = CROPS[actual_crop]
            age = day - int(tile.get("planted_day", day))
            harvest_age = (
                int(crop_data["first_yield_day"])
                if crop_data["ongoing"]
                else int(crop_data["max_yield_day"])
            )
            # One-time crops start with yield_units=1 before they are ripe.
            # Checking yield_units alone causes endless invalid HARVEST actions,
            # prevents watering, and turns the crop into a weed overnight.
            if age >= harvest_age and int(tile.get("yield_units", 0)) > 0:
                tasks.append((0, x, y, "HARVEST", None))
            elif not tile.get("watered_today", False):
                urgency = 1 if int(tile.get("consecutive_unwatered", 0)) else 2
                tasks.append((urgency, x, y, "WATER", None))
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            tasks.append((1, x, y, "DIG", None))
        elif tile is None and day >= start_day and _can_still_plant(planned_crop, day):
            if int(seeds.get(planned_crop, 0)) > 0:
                tasks.append((3, x, y, "PLANT", planned_crop))
    return tasks


def _move(x, y, tx, ty):
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]
    return ["PASS"]


def _unit_actions(obs, farm, private):
    positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm.get("hands", []) or []]
    tasks = _task_list(obs, farm, private)
    actions = [["PASS"] for _ in positions]
    remaining = dict(private.get("seeds", {}) or {})
    free_units = set(range(len(positions)))

    while free_units and tasks:
        best = None
        for unit_i in free_units:
            ux, uy = positions[unit_i]
            for task_i, task in enumerate(tasks):
                priority, tx, ty, op, crop = task
                if op == "PLANT" and int(remaining.get(crop, 0)) <= 0:
                    continue
                key = (priority, abs(ux - tx) + abs(uy - ty), ty, tx, unit_i)
                if best is None or key < best[0]:
                    best = (key, unit_i, task_i)
        if best is None:
            break
        _, unit_i, task_i = best
        _, tx, ty, op, crop = tasks.pop(task_i)
        ux, uy = positions[unit_i]
        if (ux, uy) == (tx, ty):
            actions[unit_i] = [op] if crop is None else [op, crop]
            if op == "PLANT":
                remaining[crop] = int(remaining.get(crop, 0)) - 1
        else:
            actions[unit_i] = _move(ux, uy, tx, ty)
        free_units.remove(unit_i)
    return actions


def _planned_work(obs, farm):
    day = int(obs.get("day", 0))
    work = 0
    for (x, y), (crop, start_day) in _crop_plan(farm).items():
        tile = farm["tiles"][y][x]
        if isinstance(tile, dict) and tile.get("kind") in ("PLANT", "WEED"):
            work += 1
        elif tile is None and day >= start_day and _can_still_plant(crop, day):
            work += 1
    return work


def _rival_crop_count(obs, crop):
    farms = obs.get("farms", []) or []
    player = int(obs.get("player", 0))
    if len(farms) != 2:
        return 0
    count = 0
    for row in farms[1 - player].get("tiles", []) or []:
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == crop:
                count += 1
    return count


def _seed_needs(obs, farm, private):
    day = int(obs.get("day", 0))
    needs = {crop: 0 for crop in CROPS}
    for (x, y), (crop, start_day) in _crop_plan(farm).items():
        if farm["tiles"][y][x] is None and day >= start_day and _can_still_plant(crop, day):
            needs[crop] += 1
    seeds = private.get("seeds", {}) or {}
    return {crop: max(0, n - int(seeds.get(crop, 0))) for crop, n in needs.items()}


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _market_actions(obs, farm, private):
    day, hour = int(obs.get("day", 0)), int(obs.get("hour", 0))
    shed = private.get("shed", {}) or {}
    prices = ((obs.get("market", {}) or {}).get("prices", {}) or {})
    orders = []
    budget = float(farm.get("money", 0))

    # Sell on a six-times-per-day cadence so town demand can replenish prices.
    if hour % 4 == 0 or day >= 29:
        for item in SELL_ORDER:
            amount = int(shed.get(item, 0))
            if amount <= 0:
                continue
            price = int(prices.get(item, 0))
            floor = SELL_FLOORS[item]
            rival_wave = _rival_crop_count(obs, item) >= 8
            if rival_wave:
                floor = int(floor * 0.85)  # pre-empt an obvious rival harvest wave
            if day >= 28 or price >= floor:
                # If the rival visibly has a large crop wave, small throttled
                # sales lose: their bulk order crashes the shared price first.
                quantity = amount if day >= 29 or rival_wave else min(amount, SELL_CAPS[item])
                orders.append(["SELL", item, quantity])
                budget += quantity * max(1, price)

    quadrants = list(farm.get("unlocked_quadrants", []) or ["NW"])
    extra = max(0, len(quadrants) - 1)
    # One controlled expansion only, after the base farm has generated cash.
    if extra == 0 and 5 <= day <= 12 and budget >= 6000 and len(orders) < 10:
        orders.append(["BUY_LAND"])
        budget -= LAND_COSTS[0]

    for crop, need in _seed_needs(obs, farm, private).items():
        if need <= 0 or len(orders) >= 10:
            continue
        cost = int(CROPS[crop]["seed"])
        buy = min(need, max(0, int((budget - 250) // cost)))
        if buy > 0:
            orders.append(["BUY_SEED", crop, buy])
            budget -= buy * cost

    if hour <= 1:
        work = _planned_work(obs, farm)
        # Roughly ten useful tile operations per unit/day after travel overhead.
        desired_units = max(1, min(5, int(math.ceil(work / 10.0))))
        existing = 1 + len(farm.get("hands", []) or [])
        hire_index = int(farm.get("hires_today", 0))
        while existing < desired_units and len(orders) < 10:
            cost = _fib(hire_index)
            if budget < cost + 200:
                break
            orders.append(["HIRE"])
            budget -= cost
            hire_index += 1
            existing += 1
    return orders[:10]


def agent(obs):
    try:
        farms = obs.get("farms", []) or []
        player = int(obs.get("player", 0))
        if player < 0 or player >= len(farms):
            return _pass()
        farm = farms[player]
        private = obs.get("private", {}) or {}
        actions = _unit_actions(obs, farm, private)
        return {
            "farmer": actions[0] if actions else ["PASS"],
            "hands": actions[1:] if len(actions) > 1 else [],
            "market": _market_actions(obs, farm, private),
        }
    except Exception:
        try:
            farms = obs.get("farms", []) or []
            farm = farms[int(obs.get("player", 0))]
            return _pass(len(farm.get("hands", []) or []))
        except Exception:
            return _pass()


%%writefile submission.py
"""Kaggriculture v3: diversified, staggered, market-aware baseline."""

import math

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS


BASE_PLAN = (
    [("MELON", 0)] * 16
    + [("TOMATO", 0)] * 9
)
EXTRA_PLAN = [("STRAWBERRY", 0)] * 5 + [("TOMATO", 0)] * 5
SELL_FLOORS = {
    "WHEAT": 18,
    "CARROT": 27,
    "TOMATO": 45,
    "STRAWBERRY": 90,
    "MELON": 180,
}
SELL_CAPS = {
    "WHEAT": 10,
    "CARROT": 8,
    "TOMATO": 8,
    "STRAWBERRY": 6,
    "MELON": 6,
}
SELL_ORDER = ("MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT")
LAND_COSTS = (1000, 2000, 4000)


def _pass(hand_count=0):
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in range(hand_count)],
        "market": [],
    }


def _quadrant(x, y, size):
    half = size // 2
    return ("S" if y >= half else "N") + ("E" if x >= half else "W")


def _ordered_tiles(farm, quadrant):
    size = len(farm.get("tiles", []))
    points = []
    for y, row in enumerate(farm.get("tiles", [])):
        for x, tile in enumerate(row):
            if tile != "LOCKED" and _quadrant(x, y, size) == quadrant:
                points.append((abs(x - 4) + abs(y - 4), y, x))
    points.sort()
    return [(x, y) for _, y, x in points]


def _crop_plan(farm):
    quadrants = list(farm.get("unlocked_quadrants", []) or ["NW"])
    plan = {}
    base = _ordered_tiles(farm, "NW")
    for pos, spec in zip(base, BASE_PLAN):
        plan[pos] = spec
    for quadrant in quadrants:
        if quadrant == "NW":
            continue
        for pos, spec in zip(_ordered_tiles(farm, quadrant), EXTRA_PLAN):
            plan[pos] = spec
    return plan


def _can_still_plant(crop, day):
    # Leave one full day after first maturity for harvesting and liquidation.
    return day + int(CROPS[crop]["first_yield_day"]) <= 28


def _task_list(obs, farm, private):
    day = int(obs.get("day", 0))
    seeds = dict(private.get("seeds", {}) or {})
    tasks = []
    for (x, y), (planned_crop, start_day) in _crop_plan(farm).items():
        tile = farm["tiles"][y][x]
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            actual_crop = tile.get("crop")
            crop_data = CROPS[actual_crop]
            age = day - int(tile.get("planted_day", day))
            harvest_age = (
                int(crop_data["first_yield_day"])
                if crop_data["ongoing"]
                else int(crop_data["max_yield_day"])
            )
            # One-time crops start with yield_units=1 before they are ripe.
            # Checking yield_units alone causes endless invalid HARVEST actions,
            # prevents watering, and turns the crop into a weed overnight.
            if age >= harvest_age and int(tile.get("yield_units", 0)) > 0:
                tasks.append((0, x, y, "HARVEST", None))
            elif not tile.get("watered_today", False):
                urgency = 1 if int(tile.get("consecutive_unwatered", 0)) else 2
                tasks.append((urgency, x, y, "WATER", None))
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            tasks.append((1, x, y, "DIG", None))
        elif tile is None and day >= start_day and _can_still_plant(planned_crop, day):
            if int(seeds.get(planned_crop, 0)) > 0:
                tasks.append((3, x, y, "PLANT", planned_crop))
    return tasks


def _move(x, y, tx, ty):
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]
    return ["PASS"]


def _unit_actions(obs, farm, private):
    positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm.get("hands", []) or []]
    tasks = _task_list(obs, farm, private)
    actions = [["PASS"] for _ in positions]
    remaining = dict(private.get("seeds", {}) or {})
    free_units = set(range(len(positions)))

    while free_units and tasks:
        best = None
        for unit_i in free_units:
            ux, uy = positions[unit_i]
            for task_i, task in enumerate(tasks):
                priority, tx, ty, op, crop = task
                if op == "PLANT" and int(remaining.get(crop, 0)) <= 0:
                    continue
                key = (priority, abs(ux - tx) + abs(uy - ty), ty, tx, unit_i)
                if best is None or key < best[0]:
                    best = (key, unit_i, task_i)
        if best is None:
            break
        _, unit_i, task_i = best
        _, tx, ty, op, crop = tasks.pop(task_i)
        ux, uy = positions[unit_i]
        if (ux, uy) == (tx, ty):
            actions[unit_i] = [op] if crop is None else [op, crop]
            if op == "PLANT":
                remaining[crop] = int(remaining.get(crop, 0)) - 1
        else:
            actions[unit_i] = _move(ux, uy, tx, ty)
        free_units.remove(unit_i)
    return actions


def _planned_work(obs, farm):
    day = int(obs.get("day", 0))
    work = 0
    for (x, y), (crop, start_day) in _crop_plan(farm).items():
        tile = farm["tiles"][y][x]
        if isinstance(tile, dict) and tile.get("kind") in ("PLANT", "WEED"):
            work += 1
        elif tile is None and day >= start_day and _can_still_plant(crop, day):
            work += 1
    return work


def _rival_crop_count(obs, crop):
    farms = obs.get("farms", []) or []
    player = int(obs.get("player", 0))
    if len(farms) != 2:
        return 0
    count = 0
    for row in farms[1 - player].get("tiles", []) or []:
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == crop:
                count += 1
    return count


def _seed_needs(obs, farm, private):
    day = int(obs.get("day", 0))
    needs = {crop: 0 for crop in CROPS}
    for (x, y), (crop, start_day) in _crop_plan(farm).items():
        if farm["tiles"][y][x] is None and day >= start_day and _can_still_plant(crop, day):
            needs[crop] += 1
    seeds = private.get("seeds", {}) or {}
    return {crop: max(0, n - int(seeds.get(crop, 0))) for crop, n in needs.items()}


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _market_actions(obs, farm, private):
    day, hour = int(obs.get("day", 0)), int(obs.get("hour", 0))
    shed = private.get("shed", {}) or {}
    prices = ((obs.get("market", {}) or {}).get("prices", {}) or {})
    orders = []
    budget = float(farm.get("money", 0))

    # Sell on a six-times-per-day cadence so town demand can replenish prices.
    if hour % 4 == 0 or day >= 29:
        for item in SELL_ORDER:
            amount = int(shed.get(item, 0))
            if amount <= 0:
                continue
            price = int(prices.get(item, 0))
            floor = SELL_FLOORS[item]
            rival_wave = _rival_crop_count(obs, item) >= 8
            if rival_wave:
                floor = int(floor * 0.85)  # pre-empt an obvious rival harvest wave
            if day >= 28 or price >= floor:
                # If the rival visibly has a large crop wave, small throttled
                # sales lose: their bulk order crashes the shared price first.
                quantity = amount if day >= 29 or rival_wave else min(amount, SELL_CAPS[item])
                orders.append(["SELL", item, quantity])
                budget += quantity * max(1, price)

    quadrants = list(farm.get("unlocked_quadrants", []) or ["NW"])
    extra = max(0, len(quadrants) - 1)
    # One controlled expansion only, after the base farm has generated cash.
    if extra == 0 and 5 <= day <= 12 and budget >= 6000 and len(orders) < 10:
        orders.append(["BUY_LAND"])
        budget -= LAND_COSTS[0]

    for crop, need in _seed_needs(obs, farm, private).items():
        if need <= 0 or len(orders) >= 10:
            continue
        cost = int(CROPS[crop]["seed"])
        buy = min(need, max(0, int((budget - 250) // cost)))
        if buy > 0:
            orders.append(["BUY_SEED", crop, buy])
            budget -= buy * cost

    if hour <= 1:
        work = _planned_work(obs, farm)
        # Roughly ten useful tile operations per unit/day after travel overhead.
        desired_units = max(1, min(5, int(math.ceil(work / 10.0))))
        existing = 1 + len(farm.get("hands", []) or [])
        hire_index = int(farm.get("hires_today", 0))
        while existing < desired_units and len(orders) < 10:
            cost = _fib(hire_index)
            if budget < cost + 200:
                break
            orders.append(["HIRE"])
            budget -= cost
            hire_index += 1
            existing += 1
    return orders[:10]


def agent(obs):
    try:
        farms = obs.get("farms", []) or []
        player = int(obs.get("player", 0))
        if player < 0 or player >= len(farms):
            return _pass()
        farm = farms[player]
        private = obs.get("private", {}) or {}
        actions = _unit_actions(obs, farm, private)
        return {
            "farmer": actions[0] if actions else ["PASS"],
            "hands": actions[1:] if len(actions) > 1 else [],
            "market": _market_actions(obs, farm, private),
        }
    except Exception:
        try:
            farms = obs.get("farms", []) or []
            farm = farms[int(obs.get("player", 0))]
            return _pass(len(farm.get("hands", []) or []))
        except Exception:
            return _pass()
"""Overrides appended to melon_v3_agent.py to form the self-contained v4 agent."""

# A unit keeps its target coordinate until that tile no longer has work.
_V4_TARGETS = {}
_V4_LAST_STEP = -1
SAFE_PLANT_LAST_HOUR = 20
V4_BASE_PLAN = (
    [("MELON", 0)] * 13
    + [("MELON", 7)] * 3
    + [("TOMATO", 0)] * 8
    + [("TOMATO", 1)]
)


def _crop_plan(farm):
    quadrants = list(farm.get("unlocked_quadrants", []) or ["NW"])
    plan = {}
    for pos, spec in zip(_ordered_tiles(farm, "NW"), V4_BASE_PLAN):
        plan[pos] = spec
    for quadrant in quadrants:
        if quadrant == "NW":
            continue
        for pos, spec in zip(_ordered_tiles(farm, quadrant), EXTRA_PLAN):
            plan[pos] = spec
    return plan


def _can_still_plant(crop, day):
    crop_data = CROPS[crop]
    maturity = (
        int(crop_data["first_yield_day"])
        if crop_data["ongoing"]
        else int(crop_data["max_yield_day"])
    )
    # Mature by Day 27, leaving Days 28-29 for harvest and liquidation.
    return day + maturity <= 27


def _task_list(obs, farm, private):
    day, hour = int(obs.get("day", 0)), int(obs.get("hour", 0))
    seeds = dict(private.get("seeds", {}) or {})
    tasks = []
    for (x, y), (planned_crop, start_day) in _crop_plan(farm).items():
        tile = farm["tiles"][y][x]
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            actual_crop = tile.get("crop")
            crop_data = CROPS[actual_crop]
            age = day - int(tile.get("planted_day", day))
            harvest_age = (
                int(crop_data["first_yield_day"])
                if crop_data["ongoing"]
                else int(crop_data["max_yield_day"])
            )
            if age >= harvest_age and int(tile.get("yield_units", 0)) > 0:
                tasks.append((0, x, y, "HARVEST", None))
            elif not tile.get("watered_today", False):
                urgency = 1 if int(tile.get("consecutive_unwatered", 0)) else 2
                tasks.append((urgency, x, y, "WATER", None))
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            tasks.append((1, x, y, "DIG", None))
        elif (
            tile is None
            and hour <= SAFE_PLANT_LAST_HOUR
            and day >= start_day
            and _can_still_plant(planned_crop, day)
            and int(seeds.get(planned_crop, 0)) > 0
        ):
            tasks.append((3, x, y, "PLANT", planned_crop))
    return tasks


def _unit_actions(obs, farm, private):
    global _V4_TARGETS, _V4_LAST_STEP
    day, hour = int(obs.get("day", 0)), int(obs.get("hour", 0))
    step = day * 24 + hour
    if step == 0 or step < _V4_LAST_STEP:
        _V4_TARGETS = {}
    _V4_LAST_STEP = step

    positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm.get("hands", []) or []]
    tasks = _task_list(obs, farm, private)
    by_pos = {(t[1], t[2]): t for t in tasks}
    actions = [["PASS"] for _ in positions]
    remaining = dict(private.get("seeds", {}) or {})
    reserved = set()

    # Keep valid targets. This prevents workers swapping destinations each Turn.
    for unit_i in range(len(positions)):
        target = _V4_TARGETS.get(unit_i)
        if target not in by_pos or target in reserved:
            _V4_TARGETS.pop(unit_i, None)
        else:
            reserved.add(target)

    for unit_i, (ux, uy) in enumerate(positions):
        target = _V4_TARGETS.get(unit_i)
        if target is None:
            candidates = [t for t in tasks if (t[1], t[2]) not in reserved]
            if not candidates:
                continue
            task = min(candidates, key=lambda t: (t[0], abs(ux-t[1]) + abs(uy-t[2]), t[2], t[1]))
            target = (task[1], task[2])
            _V4_TARGETS[unit_i] = target
            reserved.add(target)

        task = by_pos[target]
        _, tx, ty, op, crop = task
        if (ux, uy) != (tx, ty):
            actions[unit_i] = _move(ux, uy, tx, ty)
            continue
        if op == "PLANT":
            if int(remaining.get(crop, 0)) <= 0:
                _V4_TARGETS.pop(unit_i, None)
                continue
            remaining[crop] = int(remaining.get(crop, 0)) - 1
            actions[unit_i] = ["PLANT", crop]
        else:
            actions[unit_i] = [op]
        # The coordinate remains locked. On the next observation PLANT may turn
        # into urgent WATER and HARVEST may turn into WATER, both desirable.
    return actions


def _planned_work(obs, farm):
    day, hour = int(obs.get("day", 0)), int(obs.get("hour", 0))
    operations = 0
    active_tiles = 0
    for (x, y), (crop, start_day) in _crop_plan(farm).items():
        tile = farm["tiles"][y][x]
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            active_tiles += 1
            operations += 1  # daily water
            data = CROPS[tile.get("crop")]
            age = day - int(tile.get("planted_day", day))
            maturity = int(data["first_yield_day"] if data["ongoing"] else data["max_yield_day"])
            if age >= maturity and int(tile.get("yield_units", 0)) > 0:
                operations += 1  # harvest as well as water/replant work
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            active_tiles += 1
            operations += 3  # dig, plant, water
        elif tile is None and hour <= SAFE_PLANT_LAST_HOUR and day >= start_day and _can_still_plant(crop, day):
            active_tiles += 1
            operations += 2  # plant and water

    # Approximate one move between neighboring jobs. Twenty of 24 turns are
    # treated as safely usable so a late spawn or awkward route has slack.
    return operations + active_tiles


def _market_actions(obs, farm, private):
    # Reuse v3 market logic, but `_planned_work`, `_seed_needs`, and
    # `_can_still_plant` resolve to the v4 overrides in this combined module.
    day, hour = int(obs.get("day", 0)), int(obs.get("hour", 0))
    shed = private.get("shed", {}) or {}
    prices = ((obs.get("market", {}) or {}).get("prices", {}) or {})
    orders, budget = [], float(farm.get("money", 0))

    if hour % 4 == 0 or day >= 29:
        for item in SELL_ORDER:
            amount = int(shed.get(item, 0))
            if amount <= 0:
                continue
            price, floor = int(prices.get(item, 0)), SELL_FLOORS[item]
            if day >= 28 or price >= floor:
                # A visible crop count is not a reliable harvest forecast. Sell
                # the available batch while its observed quote clears the floor.
                quantity = amount
                orders.append(["SELL", item, quantity])
                budget += quantity * max(1, price)

    quadrants = list(farm.get("unlocked_quadrants", []) or ["NW"])
    if len(quadrants) == 1 and 5 <= day <= 12 and budget >= 6000 and len(orders) < 10:
        orders.append(["BUY_LAND"])
        budget -= LAND_COSTS[0]

    for crop, need in _seed_needs(obs, farm, private).items():
        if need <= 0 or len(orders) >= 10:
            continue
        cost = int(CROPS[crop]["seed"])
        buy = min(need, max(0, int((budget - 250) // cost)))
        if buy > 0:
            orders.append(["BUY_SEED", crop, buy])
            budget -= buy * cost

    if hour <= 1:
        estimated_turns = _planned_work(obs, farm)
        desired_units = max(1, min(6, int(math.ceil(estimated_turns / 20.0))))
        existing = 1 + len(farm.get("hands", []) or [])
        hire_index = int(farm.get("hires_today", 0))
        while existing < desired_units and len(orders) < 10:
            cost = _fib(hire_index)
            if budget < cost + 200:
                break
            orders.append(["HIRE"])
            budget -= cost
            hire_index += 1
            existing += 1
    return orders[:10]


def load_agent(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent
v3_agent=load_agent("submission_v3.py","v3")
v4_agent=load_agent("submission.py","v4")

for seat in (0,1):
    players=[v4_agent,"starter"] if seat==0 else ["starter",v4_agent]
    env=make("kaggriculture",configuration={"episodeSteps":720,"seed":42},debug=True)
    env.run(players)
    print("v4 seat",seat,[(s.reward,s.status) for s in env.steps[-1]])

results=[]
for seed in (1,2,3,42,101,20260910):
    for seat in (0,1):
        players=[v4_agent,v3_agent] if seat==0 else [v3_agent,v4_agent]
        env=make("kaggriculture",configuration={"episodeSteps":720,"seed":seed})
        env.run(players)
        final=env.steps[-1]
        mine,other=(final[0],final[1]) if seat==0 else (final[1],final[0])
        results.append({"seed":seed,"seat":seat,"v4":mine.reward,"v3":other.reward,"win":mine.reward>other.reward,"status":mine.status})
results

wins=sum(r["win"] for r in results)
print("v4 wins:",wins,"/",len(results))
print("v4 average:",sum(r["v4"] for r in results)/len(results))
print("v3 average:",sum(r["v3"] for r in results)/len(results))

assert Path("submission.py").exists()
assert all(r["status"]=="DONE" for r in results)
assert wins>=7, "v4 未稳定战胜 v3，先不要提交"
print("Pre-submit checks passed")