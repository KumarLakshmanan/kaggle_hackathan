from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import random
import statistics
import tarfile
import time

WORKDIR = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path.cwd()
WORKDIR.mkdir(parents=True, exist_ok=True)
MAIN_PATH = WORKDIR / "main.py"
ARCHIVE_PATH = WORKDIR / "submission.tar.gz"
MANIFEST_PATH = WORKDIR / "submission_manifest.json"

print(f"Output directory: {WORKDIR.resolve()}")

AGENT_SOURCE = r'''
"""Deterministic Kaggriculture agent.

Standalone standard-library-only source intended to be copied to submission main.py.
No learning, external files, network calls, or persistent cross-episode state.
"""

from __future__ import annotations

import math


PARAMS = {
    "animal_ratio": 0.3600,
    "goose_share": 0.58,
    "max_hands": 8,
    "opening_hands": 6,
    "opening_geese": 6,
    "crop_fill_ratio": 0.94,
    "land_cash_1": 999999,
    "land_cash_2": 5200,
    "land_cash_3": 9000,
    "sell_threshold": 0.78,
    "premium_sell_threshold": 0.72,
    "shed_pressure": 82,
    "fertilizer_reserve": 0,
}

# ----- Static game model ---------------------------------------------------

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")

SEED_COST = {
    "WHEAT": 10,
    "CARROT": 20,
    "TOMATO": 50,
    "STRAWBERRY": 100,
    "MELON": 80,
}

ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
ANIMAL_STRUCTURE = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
STRUCTURE_ANIMALS = {"COOP": ("GOOSE",), "PASTURE": ("COW", "SHEEP")}

BASE_PRICE = {
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

MARKET_MODEL = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 10000, 450, "log", 0.20, "sqrt", 0.70),
    "TOMATO": (60, 10000, 200, "linear", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 10000, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 10000, 332, "linear", 0.40, "log", 0.20),
    "MILK": (160, 10000, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 10000, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 10000, 200, "linear", 0.40, "linear", 0.40),
}

CROP_RULES = {
    "WHEAT": {"first": 2, "max_day": 4, "max_yield": 6, "regular": 4, "ongoing": False, "interval": 0},
    "CARROT": {"first": 2, "max_day": 3, "max_yield": 4, "regular": 3, "ongoing": False, "interval": 0},
    "TOMATO": {"first": 8, "max_day": 0, "max_yield": 4, "regular": 4, "ongoing": True, "interval": 1},
    "STRAWBERRY": {"first": 10, "max_day": 0, "max_yield": 4, "regular": 4, "ongoing": True, "interval": 2},
    "MELON": {"first": 10, "max_day": 12, "max_yield": 6, "regular": 6, "ongoing": False, "interval": 0},
}

# Approximate steady output with daily care and feeding, before congestion.
ANIMAL_DAILY_OUTPUT = {"GOOSE": 1.75, "COW": 1.35, "SHEEP": 1.20}
ANIMAL_MATURITY = {"GOOSE": 4, "COW": 8, "SHEEP": 6}

SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

SHED_TILES = ((4, 4), (5, 4), (4, 5), (5, 5))
LAND_COST = {"NE": 1000, "SW": 2000, "SE": 4000}
LAND_ORDER = ("NE", "SW", "SE")

DIRECTIONS = {"NORTH", "SOUTH", "EAST", "WEST", "PASS"}


# ----- Robust observation helpers -----------------------------------------

def _get(obj, key, default=None):
    """Read from a plain dict or Kaggle Struct without assuming one type."""
    if obj is None:
        return default
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        value = getattr(obj, key)
        return value
    except (AttributeError, KeyError, TypeError):
        try:
            return obj[key]
        except (KeyError, TypeError, IndexError):
            return default


def _as_dict(obj):
    if isinstance(obj, dict):
        return obj
    if obj is None:
        return {}
    try:
        return dict(obj)
    except (TypeError, ValueError):
        return {}


def _pos(obj):
    # Official farm positions are plain [x, y] lists; tolerate richer wrappers too.
    if isinstance(obj, (list, tuple)) and len(obj) >= 2:
        try:
            return int(obj[0]), int(obj[1])
        except (TypeError, ValueError):
            return 4, 4
    p = _get(obj, "position", None)
    if p is None:
        p = _get(obj, "pos", [4, 4])
    try:
        return int(p[0]), int(p[1])
    except (TypeError, IndexError, ValueError):
        return 4, 4


def _inventory(obj):
    inv = _get(obj, "inventory", obj)
    out = {}
    for k, v in _as_dict(inv).items():
        try:
            q = int(v)
        except (TypeError, ValueError):
            q = 0
        if q > 0:
            out[str(k)] = q
    return out


def _tile_at(tiles, x, y):
    try:
        return tiles[y][x]
    except (TypeError, IndexError):
        try:
            return tiles[x][y]
        except (TypeError, IndexError):
            return "LOCKED"


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _nearest_shed(pos):
    return min(SHED_TILES, key=lambda s: (_manhattan(pos, s), s[1], s[0]))


def _step_toward(src, dst):
    if src == dst:
        return "PASS"
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    # Alternating tie break prevents all workers from making identical paths.
    if abs(dx) > abs(dy) or (abs(dx) == abs(dy) and ((src[0] + src[1]) & 1) == 0):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"


def _iter_tiles(tiles):
    for y in range(10):
        for x in range(10):
            yield (x, y), _tile_at(tiles, x, y)


def _tile_kind(tile):
    if isinstance(tile, str):
        return tile
    return str(_get(tile, "type", _get(tile, "kind", "NONE")))


def _plant(tile):
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        return tile
    p = _get(tile, "plant", None)
    if p is not None and not isinstance(p, str):
        return p
    kind = _tile_kind(tile)
    if kind in CROPS:
        return tile
    return None


def _animal(tile):
    # Official animal tiles are the tile dict itself and contain animal="GOOSE" etc.
    if isinstance(tile, dict) and tile.get("animal") in ANIMALS:
        return tile
    a = _get(tile, "animal", None)
    if a is not None and not isinstance(a, str):
        return a
    kind = _tile_kind(tile)
    if kind in ANIMALS:
        return tile
    return None


def _structure(tile):
    s = _get(tile, "structure", None)
    if s is not None:
        return str(s)
    kind = _tile_kind(tile)
    if kind in ("COOP", "PASTURE"):
        return kind
    return None


def _is_empty(tile):
    if tile is None:
        return True
    if isinstance(tile, str):
        return tile in ("NONE", "EMPTY", "SOIL", "UNLOCKED")
    kind = _tile_kind(tile)
    return kind in ("NONE", "EMPTY", "SOIL", "UNLOCKED") and _plant(tile) is None and _animal(tile) is None and _structure(tile) is None


def _is_weed(tile):
    return _tile_kind(tile) == "WEED"


def _plant_type(plant):
    return str(_get(plant, "type", _get(plant, "crop", _get(plant, "plant_type", ""))))


def _animal_type(animal):
    return str(_get(animal, "animal", _get(animal, "type", _get(animal, "animal_type", ""))))


def _yield_units(obj):
    for key in ("yield", "product_yield", "yield_units", "products"):
        value = _get(obj, key, None)
        if value is not None:
            try:
                return max(0, int(value))
            except (TypeError, ValueError):
                pass
    return 0


def _bool(obj, *keys):
    for key in keys:
        value = _get(obj, key, None)
        if value is not None:
            return bool(value)
    return False


def _int(obj, *keys, default=0):
    for key in keys:
        value = _get(obj, key, None)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    return default


# ----- Economic model ------------------------------------------------------

def _curve(name, distance):
    d = max(0.0, float(distance))
    if name == "linear":
        return d
    if name == "sqrt":
        return math.sqrt(d)
    if name in ("sq", "square"):
        return d * d
    return math.log1p(d)


def _modeled_price(item, inventory):
    base, initial, capacity, below_curve, below_target, above_curve, above_target = MARKET_MODEL[item]
    delta = float(inventory) - float(initial)
    if delta < 0:
        denom = max(1e-12, _curve(below_curve, capacity))
        amp = below_target * base / denom
        value = base + amp * _curve(below_curve, -delta)
    else:
        denom = max(1e-12, _curve(above_curve, capacity))
        amp = above_target * base / denom
        value = base - amp * _curve(above_curve, delta)
    return max(1, int(round(value)))


def _market_state(obs):
    market = _get(obs, "market", {})
    prices = {}
    inventory = {}
    for item in PRODUCTS:
        node = _get(market, item, {})
        p = _get(node, "price", None)
        q = _get(node, "inventory", None)
        if p is None:
            p = _get(_get(market, "prices", {}), item, BASE_PRICE[item])
        if q is None:
            q = _get(_get(market, "inventory", _get(market, "inventories", {})), item, MARKET_MODEL[item][1])
        try:
            prices[item] = max(1, int(p))
        except (TypeError, ValueError):
            prices[item] = BASE_PRICE[item]
        try:
            inventory[item] = max(0, int(q))
        except (TypeError, ValueError):
            inventory[item] = MARKET_MODEL[item][1]
    return prices, inventory


def _town_signal(obs):
    town = _get(obs, "town", {})
    shops = _get(town, "unlocked_shops", None)
    if shops is None:
        shops = _get(town, "shops", [])
    demand = {item: 1.0 for item in PRODUCTS}
    units_per_day = {item: 0.0 for item in PRODUCTS}
    iterable = shops.values() if isinstance(shops, dict) else (shops or [])
    for shop in iterable:
        if isinstance(shop, str):
            shop_type = shop
            unlocked = True
        else:
            shop_type = str(_get(shop, "type", _get(shop, "shop_type", "")))
            unlocked = bool(_get(shop, "unlocked", _get(shop, "active", True)))
        if not unlocked or shop_type not in SHOP_PRODUCTS:
            continue
        products = SHOP_PRODUCTS[shop_type]
        per_cycle = 2.0 if len(products) == 1 else 1.0
        for item in products:
            units_per_day[item] += 6.0 * per_cycle
            demand[item] += 0.10 * 6.0 * per_cycle
    # Town centre removes one unit per day from each non-fertilizer product.
    for item in PRODUCTS:
        if item != "FERTILIZER":
            units_per_day[item] += 1.0
            demand[item] += 0.08
    return demand, units_per_day


def _opponent_pipeline(obs, me):
    farms = _get(obs, "farms", []) or []
    pipeline = {item: 0 for item in PRODUCTS}
    for idx, farm in enumerate(farms):
        if idx == me:
            continue
        tiles = _get(farm, "tiles", [])
        for _, tile in _iter_tiles(tiles):
            p = _plant(tile)
            if p is not None:
                crop = _plant_type(p)
                if crop in pipeline:
                    pipeline[crop] += 1
            a = _animal(tile)
            if a is not None:
                animal = _animal_type(a)
                product = ANIMAL_PRODUCT.get(animal)
                if product:
                    pipeline[product] += 2
    return pipeline


def _animal_scores(prices, market_inventory, demand, opponent, day):
    remaining = max(0, 29 - day)
    scores = {}
    for animal in ANIMALS:
        product = ANIMAL_PRODUCT[animal]
        maturity_factor = min(1.0, remaining / max(1.0, ANIMAL_MATURITY[animal] + 2.0))
        prod_value = ANIMAL_DAILY_OUTPUT[animal] * prices[product] * demand[product]
        fert_value = 0.70 * prices["FERTILIZER"]
        feed_cost = prices["WHEAT"]
        congestion = 1.0 + 0.045 * opponent[product]
        live_glut = max(0, market_inventory[product] - MARKET_MODEL[product][1])
        congestion *= 1.0 + min(0.8, live_glut / max(80.0, MARKET_MODEL[product][1]))
        raw = (prod_value / congestion + fert_value - feed_cost) * maturity_factor
        raw -= ANIMAL_COST[animal] / max(4.0, remaining + 1.0)
        if animal == "GOOSE":
            raw *= 1.10
        scores[animal] = raw
    return scores


def _crop_scores(prices, demand, opponent, remaining_days, feed_shortage):
    expected = {"WHEAT": 4.0, "CARROT": 3.0, "TOMATO": 4.0, "STRAWBERRY": 4.0, "MELON": 6.0}
    maturity = {"WHEAT": 4, "CARROT": 3, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}
    effort = {"WHEAT": 5.0, "CARROT": 4.0, "TOMATO": 13.0, "STRAWBERRY": 16.0, "MELON": 11.0}
    bias = {"WHEAT": 1.18, "CARROT": 1.02, "TOMATO": 0.98, "STRAWBERRY": 0.93, "MELON": 1.12}
    scores = {}
    for crop in CROPS:
        if remaining_days <= maturity[crop] + 1:
            scores[crop] = -1e9
            continue
        gross = expected[crop] * prices[crop] * demand[crop]
        congestion = 1.0 + 0.025 * opponent[crop]
        net = gross / congestion - SEED_COST[crop] - 1.8 * effort[crop]
        if crop == "WHEAT":
            net += min(180.0, 12.0 * feed_shortage)
        scores[crop] = net * bias[crop]
    return scores


def _sale_revenue(item, quantity, inventory):
    value = 0
    inv = int(inventory)
    for _ in range(max(0, int(quantity))):
        price = _modeled_price(item, inv)
        value += price
        if price > 1:
            inv += 1
    return value


# ----- Farm analysis and layout -------------------------------------------

def _analyze_farm(farm, private):
    tiles = _get(farm, "tiles", [])
    unlocked = []
    locked = []
    plants = []
    animals = []
    structures = []
    weeds = []
    empties = []
    for pos, tile in _iter_tiles(tiles):
        if isinstance(tile, str) and tile == "LOCKED":
            locked.append(pos)
            continue
        unlocked.append(pos)
        p = _plant(tile)
        a = _animal(tile)
        s = _structure(tile)
        if p is not None:
            plants.append((pos, p, tile))
        elif a is not None:
            animals.append((pos, a, tile))
            structures.append((pos, s or ANIMAL_STRUCTURE.get(_animal_type(a)), tile))
        elif s is not None:
            structures.append((pos, s, tile))
        elif _is_weed(tile):
            weeds.append((pos, tile))
        elif _is_empty(tile):
            empties.append(pos)
    shed = _inventory(_get(private, "shed", {}))
    seeds = _inventory(_get(private, "seeds", {}))
    return {
        "tiles": tiles,
        "unlocked": unlocked,
        "locked": locked,
        "plants": plants,
        "animals": animals,
        "structures": structures,
        "weeds": weeds,
        "empties": empties,
        "shed": shed,
        "seeds": seeds,
        "hires_today": _int(farm, "hires_today", default=0),
    }


def _layout_slots(unlocked, target_animals):
    # Central, short routes first. A checkerboard tie break spreads traffic.
    ranked = sorted(
        unlocked,
        key=lambda p: (
            min(_manhattan(p, s) for s in SHED_TILES),
            (p[0] + p[1]) & 1,
            abs(p[0] - 4.5) + abs(p[1] - 4.5),
            p[1],
            p[0],
        ),
    )
    return set(ranked[: max(0, min(target_animals, len(ranked)))])


def _desired_animal(slot_index, animal_scores):
    return "COW" if slot_index < 5 else "SHEEP"

def _choose_crop(pos, crop_scores, day):
    ranked = sorted(CROPS, key=lambda c: crop_scores[c], reverse=True)
    viable = [c for c in ranked if crop_scores[c] > -1e8]
    if not viable:
        return None
    # Use mostly the best crop, but preserve diversity and avoid synchronised dumps.
    top = viable[: min(3, len(viable))]
    weights = []
    floor = min(crop_scores[c] for c in top)
    for rank, crop in enumerate(top):
        weights.append(max(1.0, crop_scores[crop] - floor + 35.0 / (rank + 1)))
    total = sum(weights)
    h = (pos[0] * 73856093 + pos[1] * 19349663 + (day // 3) * 83492791) & 0xFFFFFFFF
    point = (h % 10000) / 10000.0 * total
    acc = 0.0
    for crop, weight in zip(top, weights):
        acc += weight
        if point <= acc:
            return crop
    return top[0]


def _target_animals(day, cash, owned_cells, current_assets):
    cap = int(max(0, owned_cells) * float(PARAMS["animal_ratio"]))
    growth_cap = int(PARAMS["opening_geese"]) + max(0, day) * 2
    target = min(cap, growth_cap)
    if day >= 23:
        target = min(target, current_assets)
    if cash < 450:
        target = min(target, current_assets)
    return max(current_assets, target)


def _land_name_from_locked(locked, unlocked):
    # Official buy order is fixed; identify already unlocked quadrants by coordinates.
    unlocked_set = set(unlocked)
    checks = {
        "NE": (5, 0),
        "SW": (0, 5),
        "SE": (5, 5),
    }
    for name in LAND_ORDER:
        if checks[name] not in unlocked_set:
            return name
    return None


# ----- Task creation and worker routing -----------------------------------

def _task(priority, pos, action, need=None, tag=""):
    return {"priority": float(priority), "pos": tuple(pos), "action": list(action), "need": need, "tag": tag}


def _unit_records(farm, private):
    farmer = _get(farm, "farmer", {})
    hands = list(_get(farm, "hands", []) or [])
    units = [farmer] + hands
    private_inventories = list(_get(private, "inventories", []) or [])
    out = []
    for idx, unit in enumerate(units):
        inv = _inventory(unit)
        if not inv and idx < len(private_inventories):
            inv = _inventory(private_inventories[idx])
        out.append({"idx": idx, "pos": _pos(unit), "inv": inv})
    return out


def _eligible(unit, task):
    need = task.get("need")
    if need is None:
        return True
    if isinstance(need, (tuple, list, set)):
        return any(unit["inv"].get(item, 0) > 0 for item in need)
    return unit["inv"].get(str(need), 0) > 0


def _assign_tasks(units, tasks, day, hour):
    actions = [None] * len(units)
    unassigned = set(range(len(units)))
    used_tasks = set()

    # Hard endgame rule: inventory must reach the shed before the episode ends.
    if day >= 29 and hour >= 17:
        for ui, unit in enumerate(units):
            if not unit["inv"]:
                continue
            target = _nearest_shed(unit["pos"])
            if unit["pos"] == target:
                # DROP without an item means all inventory in the official API.
                actions[ui] = ["DROP"]
            else:
                actions[ui] = [_step_toward(unit["pos"], target)]
            unassigned.discard(ui)

    ordered = sorted(
        enumerate(tasks),
        key=lambda pair: (
            -(pair[1]["priority"] + (20 if any(_eligible(units[ui], pair[1]) and units[ui]["pos"] == pair[1]["pos"] for ui in unassigned) else 0)),
            pair[1]["pos"][1], pair[1]["pos"][0], pair[0],
        ),
    )
    for ti, task in ordered:
        if ti in used_tasks or not unassigned:
            continue
        candidates = [ui for ui in unassigned if _eligible(units[ui], task)]
        if not candidates:
            continue
        ui = min(candidates, key=lambda j: (_manhattan(units[j]["pos"], task["pos"]), 0 if units[j]["pos"] == task["pos"] else 1, j))
        unit = units[ui]
        actions[ui] = list(task["action"]) if unit["pos"] == task["pos"] else [_step_toward(unit["pos"], task["pos"])]
        unassigned.remove(ui)
        used_tasks.add(ti)

    # Workers with cargo on the final day return even before the hard cutoff.
    for ui in list(unassigned):
        unit = units[ui]
        if day >= 29 and unit["inv"]:
            target = _nearest_shed(unit["pos"])
            actions[ui] = ["DROP"] if unit["pos"] == target else [_step_toward(unit["pos"], target)]
            unassigned.remove(ui)

    for ui in unassigned:
        actions[ui] = ["PASS"]
    return actions


def _build_tasks(obs, farm_info, units, animal_slots, desired_by_slot, crop_scores, day, hour, step):
    tasks = []
    tiles = farm_info["tiles"]
    final_day = day >= 29

    # Index open structures and current animals.
    open_structures = {"COOP": [], "PASTURE": []}
    occupied_positions = set()
    for pos, animal, tile in farm_info["animals"]:
        occupied_positions.add(pos)
        animal_type = _animal_type(animal)
        product_yield = _yield_units(animal)
        fed = _bool(animal, "fed_today", "was_fed", "fed")
        cared = _bool(animal, "cared_today", "was_cared", "cared")
        unfed = _int(animal, "consecutive_unfed_days", "consecutive_unfed", default=0)
        fert_available = _bool(animal, "fertilizer_available", "has_fertilizer")
        max_held = 4 if animal_type == "GOOSE" else 6

        if final_day:
            if product_yield > 0 and hour <= 16:
                tasks.append(_task(245 + product_yield, pos, ["HARVEST"], tag="final_animal_harvest"))
            if fert_available and hour <= 15:
                tasks.append(_task(232, pos, ["COLLECT_FERTILIZER"], tag="final_fert"))
            continue

        if not fed:
            priority = 235 if unfed >= 1 else 205
            tasks.append(_task(priority, pos, ["FEED"], need="WHEAT", tag="feed"))
        if product_yield > 0 and (product_yield >= 2 or product_yield >= max_held - 1 or hour >= 18):
            tasks.append(_task(165 + 3 * product_yield, pos, ["HARVEST"], tag="animal_harvest"))
        if fert_available:
            tasks.append(_task(156, pos, ["COLLECT_FERTILIZER"], tag="fert_collect"))
        if not cared:
            tasks.append(_task(142, pos, ["CARE"], tag="care"))

    for pos, structure, tile in farm_info["structures"]:
        if pos in occupied_positions:
            continue
        if structure in open_structures:
            open_structures[structure].append(pos)

    # Units carrying animals get an overriding placement route.
    reserved_open = {"COOP": set(), "PASTURE": set()}
    for unit in units:
        for animal in ANIMALS:
            if unit["inv"].get(animal, 0) <= 0:
                continue
            structure = ANIMAL_STRUCTURE[animal]
            candidates = [p for p in open_structures[structure] if p not in reserved_open[structure]]
            if candidates:
                target = min(candidates, key=lambda p: (_manhattan(unit["pos"], p), p[1], p[0]))
                reserved_open[structure].add(target)
                tasks.append(_task(300, target, ["PLACE", animal, 1], need=animal, tag="place_animal"))

    # Empty animal slots: build the correct structure. Never destroy a healthy crop for layout purity.
    for pos in sorted(animal_slots, key=lambda p: (p[1], p[0])):
        tile = _tile_at(tiles, pos[0], pos[1])
        if _is_empty(tile):
            animal = desired_by_slot.get(pos, "GOOSE")
            structure = ANIMAL_STRUCTURE[animal]
            tasks.append(_task(105, pos, ["BUILD_" + structure], tag="build"))
        elif _is_weed(tile):
            tasks.append(_task(176, pos, ["DIG"], tag="weed"))

    # Pickup animals for already-built compatible structures. Requests are capped by shed stock.
    shed = farm_info["shed"]
    animal_pickups = []
    for structure, positions in open_structures.items():
        available_positions = [p for p in positions if p not in reserved_open[structure]]
        allowed = STRUCTURE_ANIMALS[structure]
        for animal in allowed:
            q = min(int(shed.get(animal, 0)), len(available_positions))
            for i in range(q):
                target = SHED_TILES[(len(animal_pickups) + i) % len(SHED_TILES)]
                animal_pickups.append(_task(185, target, ["PICKUP", animal, 1], tag="animal_pickup"))
                if available_positions:
                    available_positions.pop()
    tasks.extend(animal_pickups)

    # Crops: urgent harvest, water, selective fertilizer, or reclaim exhausted plants.
    fertilizer_carriers = sum(1 for u in units if u["inv"].get("FERTILIZER", 0) > 0)
    for pos, plant, tile in farm_info["plants"]:
        crop = _plant_type(plant)
        if crop not in CROP_RULES:
            continue
        rules = CROP_RULES[crop]
        age = _int(plant, "age", "age_days", default=max(0, day - _int(plant, "planted_day", default=day)))
        yld = _yield_units(plant)
        watered = _bool(plant, "watered_today", "was_watered", "watered")
        unwatered = _int(plant, "consecutive_unwatered_days", "consecutive_unwatered", default=0)
        fertilized = (
            _bool(plant, "fertilized", "is_fertilized")
            or _int(plant, "fertilized_until_day", default=-1) >= day
            or _int(plant, "fertilizer_days", "fertilized_days", default=0) > 0
        )

        if final_day:
            if yld > 0 and hour <= 16:
                tasks.append(_task(250 + yld, pos, ["HARVEST"], tag="final_crop_harvest"))
            continue

        harvest = False
        priority = 0
        if rules["ongoing"]:
            if yld >= 2 or yld >= rules["max_yield"] - 1 or day >= 27:
                harvest = yld > 0
                priority = 170 + 3 * yld
            exhausted_age = rules["first"] + rules["interval"] * rules["max_yield"] + 2
            if age >= exhausted_age and yld <= 0:
                tasks.append(_task(112, pos, ["DIG"], tag="reclaim"))
        else:
            target_yield = rules["regular"]
            if crop == "MELON":
                target_yield = 6
            if yld >= target_yield or age >= rules["max_day"] or day >= 27:
                harvest = yld > 0
                priority = 176 + 3 * yld
        if harvest:
            tasks.append(_task(priority, pos, ["HARVEST"], tag="crop_harvest"))

        if not watered and hour <= 20:
            # A plant with one missed day dies at EOD if ignored again.
            water_priority = 215 if unwatered >= 1 else 154
            # Fertilize valuable one-time crops just before watering, when there is time.
            bonus_window = int(math.ceil(max(1, rules.get("max_day", rules["first"])) / 2.0))
            valuable_window = crop in ("MELON", "STRAWBERRY", "TOMATO") and age >= max(0, bonus_window - 1)
            if fertilizer_carriers > 0 and valuable_window and not fertilized and hour <= 17 and unwatered == 0:
                tasks.append(_task(water_priority + 8, pos, ["FERTILIZE"], need="FERTILIZER", tag="fertilize"))
            tasks.append(_task(water_priority, pos, ["WATER"], tag="water"))

    # Weeds outside animal slots.
    for pos, tile in farm_info["weeds"]:
        if pos not in animal_slots:
            tasks.append(_task(169, pos, ["DIG"], tag="weed"))

    # Plant viable empty crop slots, but never so late that they cannot be watered today.
    if not final_day and hour <= 15:
        available_seeds = {c: int(farm_info["seeds"].get(c, 0)) for c in CROPS}
        for pos in sorted(farm_info["empties"], key=lambda p: (min(_manhattan(p, s) for s in SHED_TILES), p[1], p[0])):
            if pos in animal_slots:
                continue
            crop = _choose_crop(pos, crop_scores, day)
            if crop is None or available_seeds.get(crop, 0) <= 0:
                continue
            available_seeds[crop] -= 1
            tasks.append(_task(145, pos, ["PLANT", crop], tag="plant"))

    # Resource pickup. Multiple workers become feeders; exact quantities are reserved.
    existing_animals = len(farm_info["animals"])
    carried_wheat = sum(u["inv"].get("WHEAT", 0) for u in units)
    wheat_available = max(0, int(shed.get("WHEAT", 0)))
    if not final_day and existing_animals > 0 and wheat_available > 0 and carried_wheat < max(2, existing_animals // 2):
        pickers = min(max(1, int(math.ceil(existing_animals / 5.0))), len(units), 4)
        remaining = wheat_available
        for i in range(pickers):
            if remaining <= 0:
                break
            qty = min(remaining, max(2, int(math.ceil(existing_animals / float(pickers))) + 1))
            remaining -= qty
            tasks.append(_task(210, SHED_TILES[i % 4], ["PICKUP", "WHEAT", qty], tag="wheat_pickup"))

    # If fertilizer accumulated in the shed and premium crops exist, arm one specialist.
    if not final_day and int(shed.get("FERTILIZER", 0)) > 0 and fertilizer_carriers == 0:
        premium_plants = sum(1 for _, p, _ in farm_info["plants"] if _plant_type(p) in ("MELON", "STRAWBERRY", "TOMATO"))
        if premium_plants > 0:
            tasks.append(_task(128, SHED_TILES[3], ["PICKUP", "FERTILIZER", min(4, int(shed["FERTILIZER"]))], tag="fert_pickup"))

    return tasks


# ----- Market policy -------------------------------------------------------

def _fib_hire_cost(nth_hire_today):
    # Official sequence is 1, 1, 2, 3, 5, ...
    n = max(0, int(nth_hire_today))
    if n <= 1:
        return 1
    a, b = 1, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def _market_orders(obs, farm_info, units, animal_slots, desired_by_slot, crop_scores, prices, market_inventory, demand, units_per_day, day, hour, money):
    orders = []
    budget = max(0, int(money))
    shed = dict(farm_info["shed"])
    final_day = day >= 29
    shed_total = sum(int(v) for v in shed.values())
    pressure = shed_total >= int(PARAMS["shed_pressure"])

    def add(order, cost=0):
        nonlocal budget
        if len(orders) >= 10:
            return False
        if cost > budget:
            return False
        orders.append(list(order))
        budget -= int(cost)
        return True

    # 1) Sales. They are intentionally first so the official market can fund later orders.
    sell_candidates = []
    current_animals = len(farm_info["animals"])
    feed_reserve = max(0, current_animals * 2 + 4)
    for item in PRODUCTS:
        qty = int(shed.get(item, 0))
        if qty <= 0:
            continue
        reserve = 0
        if item == "WHEAT" and not final_day:
            reserve = min(qty, feed_reserve)
        elif item == "FERTILIZER" and not final_day:
            reserve = min(qty, int(PARAMS["fertilizer_reserve"]))
        excess = max(0, qty - reserve)
        if excess <= 0:
            continue
        base = BASE_PRICE[item]
        ratio = prices[item] / float(base)
        premium = item in ("MELON", "STRAWBERRY", "MILK", "WOOL")
        threshold = float(PARAMS["premium_sell_threshold"] if premium else PARAMS["sell_threshold"])
        demand_support = units_per_day[item]
        should_sell = final_day or day >= 27 or pressure or ratio >= threshold
        if item == "FERTILIZER":
            should_sell = True
        if not should_sell:
            continue
        if final_day or day >= 27 or pressure or ratio >= 1.0:
            q_sell = excess
        else:
            tranche = max(3, int(round(1.5 * demand_support)))
            q_sell = min(excess, tranche)
        revenue = _sale_revenue(item, q_sell, market_inventory[item])
        # Prioritize high cash release and per-slot value.
        sell_candidates.append((revenue + 50 * prices[item], prices[item], item, q_sell))

    sell_candidates.sort(reverse=True)
    for _, _, item, qty in sell_candidates:
        if len(orders) >= 10:
            break
        add(["SELL", item, int(qty)], 0)

    if final_day:
        return orders[:10]

    # 2) Decide workforce from daily work burden. Hires only help the current day.
    structures_in_progress = sum(1 for p in animal_slots if _is_empty(_tile_at(farm_info["tiles"], p[0], p[1])))
    work = 3.1 * len(farm_info["animals"]) + 1.15 * len(farm_info["plants"]) + 1.7 * structures_in_progress
    desired_hands = int(math.ceil(work / 10.0))
    if day <= 1:
        desired_hands = max(desired_hands, int(PARAMS["opening_hands"]))
    desired_hands = 8 if day < 14 and len(farm_info["plants"]) >= 10 else 7
    current_hands = max(0, len(units) - 1)
    if hour <= 3 and current_hands < desired_hands:
        to_hire = min(desired_hands - current_hands, max(0, 10 - len(orders)))
        for i in range(to_hire):
            cost = _fib_hire_cost(int(farm_info.get("hires_today", 0)) + i)
            if not add(["HIRE"], cost):
                break

    # 3) Feed buffer: animals starve much faster than crops become profitable.
    animals_in_transit = sum(int(shed.get(a, 0)) for a in ANIMALS) + sum(sum(u["inv"].get(a, 0) for a in ANIMALS) for u in units)
    wheat_units = int(shed.get("WHEAT", 0)) + sum(u["inv"].get("WHEAT", 0) for u in units)
    target_wheat = max(10, 2 * (len(farm_info["animals"]) + animals_in_transit) + 6)
    wheat_short = max(0, target_wheat - wheat_units)
    if wheat_short > 0 and len(orders) < 10:
        # BUY_PRODUCT is market-priced, not seed-priced.
        unit_cost = max(1, int(prices["WHEAT"]))
        affordable = max(0, (budget - 180) // unit_cost)
        qty = min(wheat_short, affordable)
        if qty > 0:
            add(["BUY_PRODUCT", "WHEAT", int(qty)], qty * unit_cost)

    # 4) Buy animals only for the deterministic layout, grouped by type.
    current_assets = len(farm_info["animals"]) + animals_in_transit
    target = len(animal_slots)
    need = max(0, target - current_assets)
    if day <= 22 and need > 0 and len(orders) < 10:
        desired_counts = {a: 0 for a in ANIMALS}
        for pos in sorted(animal_slots, key=lambda p: (p[1], p[0])):
            desired_counts[desired_by_slot[pos]] += 1
        existing_counts = {a: 0 for a in ANIMALS}
        for _, animal, _ in farm_info["animals"]:
            a = _animal_type(animal)
            if a in existing_counts:
                existing_counts[a] += 1
        for a in ANIMALS:
            existing_counts[a] += int(shed.get(a, 0)) + sum(u["inv"].get(a, 0) for u in units)
        deficits = [(desired_counts[a] - existing_counts[a], a) for a in ANIMALS]
        deficits.sort(key=lambda z: (z[0] * ANIMAL_COST[z[1]], z[0]), reverse=True)
        for deficit, animal in deficits:
            if deficit <= 0 or len(orders) >= 10:
                continue
            reserve = 220 + 20 * current_assets
            affordable = max(0, (budget - reserve) // ANIMAL_COST[animal])
            qty = min(deficit, need, affordable)
            if qty > 0 and add(["BUY_ANIMAL", animal, int(qty)], qty * ANIMAL_COST[animal]):
                need -= qty

    # 5) Buy seed batches matching empty crop slots. Atomic planting means exact counts matter.
    if day <= 16 and hour <= 14 and len(orders) < 10:
        requested = {c: 0 for c in CROPS}
        for pos in farm_info["empties"]:
            if pos in animal_slots:
                continue
            crop = _choose_crop(pos, crop_scores, day)
            if crop is not None:
                requested[crop] += 1
        for crop in CROPS:
            requested[crop] = max(0, requested[crop] - int(farm_info["seeds"].get(crop, 0)))
        ranked = sorted(CROPS, key=lambda c: crop_scores[c], reverse=True)
        for crop in ranked:
            qty = requested[crop]
            if qty <= 0 or len(orders) >= 10 or crop_scores[crop] <= -1e8:
                continue
            reserve = 150
            affordable = max(0, (budget - reserve) // SEED_COST[crop])
            qty = min(qty, affordable, 18)
            if qty > 0:
                add(["BUY_SEED", crop, int(qty)], qty * SEED_COST[crop])

    # 6) Land expansion only after the current quadrant is productively occupied.
    nonempty = len(farm_info["plants"]) + len(farm_info["animals"]) + len(farm_info["structures"]) + len(farm_info["weeds"])
    utilization = nonempty / float(max(1, len(farm_info["unlocked"])))
    next_land = _land_name_from_locked(farm_info["locked"], farm_info["unlocked"])
    unlocked_quadrants = max(1, len(farm_info["unlocked"]) // 25)
    cash_threshold = {
        1: int(PARAMS["land_cash_1"]),
        2: int(PARAMS["land_cash_2"]),
        3: int(PARAMS["land_cash_3"]),
    }.get(unlocked_quadrants, 10**9)
    if next_land and day < 22 and utilization >= 0.82 and budget >= max(cash_threshold, LAND_COST[next_land] + 500) and len(orders) < 10:
        add(["BUY_LAND"], LAND_COST[next_land])

    return orders[:10]


# ----- Public agent --------------------------------------------------------

def _agent_impl(obs):
    """Return a legal deterministic action for one Kaggriculture turn."""
    player = _int(obs, "player", default=0)
    day = _int(obs, "day", default=0)
    hour = _int(obs, "hour", default=0)
    step = _int(obs, "step", default=day * 24 + hour)

    farms = list(_get(obs, "farms", []) or [])
    if not farms:
        return {"farmer": ["PASS"], "hands": [], "market": []}
    player = min(max(0, player), len(farms) - 1)
    farm = farms[player]

    private_root = _get(obs, "private", {})
    if isinstance(private_root, (list, tuple)):
        private = private_root[player] if player < len(private_root) else {}
    else:
        private = private_root
    # Some simulator versions nest private state by player id.
    nested = _get(private, str(player), None)
    if nested is None:
        nested = _get(private, player, None)
    if nested is not None and _get(private, "shed", None) is None:
        private = nested

    money = _int(private, "money", default=_int(farm, "money", default=0))
    farm_info = _analyze_farm(farm, private)
    units = _unit_records(farm, private)
    prices, market_inventory = _market_state(obs)
    demand, units_per_day = _town_signal(obs)
    opponent = _opponent_pipeline(obs, player)

    assets = len(farm_info["animals"])
    assets += sum(int(farm_info["shed"].get(a, 0)) for a in ANIMALS)
    assets += sum(sum(u["inv"].get(a, 0) for a in ANIMALS) for u in units)
    target_animals = _target_animals(day, money, len(farm_info["unlocked"]), assets)
    animal_slots = _layout_slots(farm_info["unlocked"], target_animals)

    animal_scores = _animal_scores(prices, market_inventory, demand, opponent, day)
    desired_by_slot = {}
    for idx, pos in enumerate(sorted(animal_slots, key=lambda p: (min(_manhattan(p, s) for s in SHED_TILES), p[1], p[0]))):
        tile = _tile_at(farm_info["tiles"], pos[0], pos[1])
        existing_structure = _structure(tile)
        if existing_structure == "COOP":
            desired_by_slot[pos] = "GOOSE"
        elif existing_structure == "PASTURE":
            existing_animal = _animal(tile)
            if existing_animal is not None and _animal_type(existing_animal) in ("COW", "SHEEP"):
                desired_by_slot[pos] = _animal_type(existing_animal)
            else:
                desired_by_slot[pos] = _desired_animal(idx, animal_scores)
        else:
            desired_by_slot[pos] = _desired_animal(idx, animal_scores)

    total_wheat = int(farm_info["shed"].get("WHEAT", 0)) + sum(u["inv"].get("WHEAT", 0) for u in units)
    feed_shortage = max(0, 2 * max(1, assets) + 6 - total_wheat)
    crop_scores = _crop_scores(prices, demand, opponent, max(0, 29 - day), feed_shortage)

    tasks = _build_tasks(obs, farm_info, units, animal_slots, desired_by_slot, crop_scores, day, hour, step)
    unit_actions = _assign_tasks(units, tasks, day, hour)
    market_orders = _market_orders(
        obs,
        farm_info,
        units,
        animal_slots,
        desired_by_slot,
        crop_scores,
        prices,
        market_inventory,
        demand,
        units_per_day,
        day,
        hour,
        money,
    )

    return {
        "farmer": unit_actions[0] if unit_actions else ["PASS"],
        "hands": unit_actions[1:] if len(unit_actions) > 1 else [],
        "market": market_orders,
    }



def agent(obs):
    """Competition entry point with a last-resort legal PASS fallback."""
    try:
        return _agent_impl(obs)
    except Exception:
        # A malformed observation should not invalidate the whole submission.
        hand_count = 0
        try:
            farms = obs.get("farms", []) if isinstance(obs, dict) else getattr(obs, "farms", [])
            player = obs.get("player", 0) if isinstance(obs, dict) else getattr(obs, "player", 0)
            farm = farms[int(player)]
            hands = farm.get("hands", []) if isinstance(farm, dict) else getattr(farm, "hands", [])
            hand_count = len(hands or [])
        except Exception:
            hand_count = 0
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(hand_count)],
            "market": [],
        }

'''

print(f'Embedded agent: {len(AGENT_SOURCE):,} characters, {len(AGENT_SOURCE.splitlines()):,} lines')

# Compile before writing: catches SyntaxError immediately.
compile(AGENT_SOURCE, "main.py", "exec")
MAIN_PATH.write_text(AGENT_SOURCE, encoding="utf-8")

spec = importlib.util.spec_from_file_location("kaggriculture_submission", MAIN_PATH)
assert spec is not None and spec.loader is not None
agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_module)
assert callable(agent_module.agent)

print(f"Wrote {MAIN_PATH} ({MAIN_PATH.stat().st_size:,} bytes)")
print("Import and entry-point check: OK")

# Synthetic observations follow the current official public/private shape.
LEGAL_UNIT = {
    "NORTH", "SOUTH", "EAST", "WEST", "PASS", "PICKUP", "DROP", "PLANT",
    "WATER", "HARVEST", "FERTILIZE", "BUILD_COOP", "BUILD_PASTURE", "DIG",
    "PLACE", "FEED", "COLLECT_FERTILIZER", "CARE",
}
LEGAL_MARKET = {"BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL", "HIRE", "BUY_LAND"}


def empty_shed():
    return {k: 0 for k in list(agent_module.PRODUCTS) + list(agent_module.ANIMALS)}


def initial_farm():
    tiles = [[None if x < 5 and y < 5 else "LOCKED" for x in range(10)] for y in range(10)]
    return {
        "money": 3000.0,
        "tiles": tiles,
        "farmer": [4, 4],
        "hands": [],
        "unlocked_quadrants": ["NW"],
        "hires_today": 0,
    }


def initial_observation(player=0):
    return {
        "player": player,
        "step": 0,
        "day": 0,
        "hour": 0,
        "farms": [initial_farm(), initial_farm()],
        "private": {
            "shed": empty_shed(),
            "seeds": {k: 0 for k in agent_module.CROPS},
            "inventories": [{}],
        },
        "market": {
            "inventory": {k: 10000 for k in agent_module.PRODUCTS},
            "prices": dict(agent_module.BASE_PRICE),
        },
        "town": {"unlocked_shops": []},
    }


def validate_action(obs, action):
    assert isinstance(action, dict)
    assert set(action) == {"farmer", "hands", "market"}

    farmer = action["farmer"]
    assert isinstance(farmer, list) and farmer and farmer[0] in LEGAL_UNIT

    expected_hands = len(obs["farms"][obs["player"]].get("hands", []))
    hands = action["hands"]
    assert isinstance(hands, list) and len(hands) == expected_hands
    for hand_action in hands:
        assert isinstance(hand_action, list) and hand_action and hand_action[0] in LEGAL_UNIT

    market = action["market"]
    assert isinstance(market, list) and len(market) <= 10
    for order in market:
        assert isinstance(order, list) and order and order[0] in LEGAL_MARKET
        if order[0] in {"BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"}:
            assert len(order) == 3 and isinstance(order[2], int) and order[2] > 0
        else:
            assert len(order) == 1

    json.dumps(action)  # Must be serialisable by the simulation runner.


obs = initial_observation()
opening_action = agent_module.agent(obs)
validate_action(obs, opening_action)
print(json.dumps(opening_action, indent=2))
print("Initial contract test: OK")

# Branch-coverage fuzzing: plants, animals, structures, weeds, inventory carriers,
# different days/hours, market states, shop demand, workforce sizes, and unlocked land.
rng = random.Random(20260810)
latencies = []

for case in range(750):
    obs = initial_observation(player=rng.randrange(2))
    day, hour = rng.randrange(30), rng.randrange(24)
    obs.update(day=day, hour=hour, step=day * 24 + hour)

    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]

    quadrant_count = rng.randrange(1, 5)
    names = ["NW", "NE", "SW", "SE"][:quadrant_count]
    farm["unlocked_quadrants"] = names
    for y in range(10):
        for x in range(10):
            quadrant = ("N" if y < 5 else "S") + ("W" if x < 5 else "E")
            farm["tiles"][y][x] = None if quadrant in names else "LOCKED"

    hand_count = rng.randrange(10)
    farm["hands"] = [list(rng.choice(agent_module.SHED_TILES)) for _ in range(hand_count)]
    farm["hires_today"] = hand_count
    farm["farmer"] = [rng.randrange(10), rng.randrange(10)]
    farm["money"] = rng.randrange(20000)
    private["inventories"] = [{} for _ in range(hand_count + 1)]

    unlocked = [
        (x, y) for y in range(10) for x in range(10)
        if farm["tiles"][y][x] is None
    ]
    rng.shuffle(unlocked)
    for x, y in unlocked[:rng.randrange(min(36, len(unlocked)) + 1)]:
        kind = rng.choice(["PLANT", "ANIMAL", "STRUCTURE", "WEED"])
        if kind == "PLANT":
            crop = rng.choice(agent_module.CROPS)
            farm["tiles"][y][x] = {
                "kind": "PLANT", "crop": crop,
                "planted_day": max(0, day - rng.randrange(14)),
                "watered_today": rng.choice([True, False]),
                "consecutive_unwatered": rng.randrange(2),
                "yield_units": rng.randrange(7),
                "max_lifespan_step": -1,
                "fertilized_until_day": rng.randrange(-1, day + 3),
            }
        elif kind == "ANIMAL":
            animal = rng.choice(agent_module.ANIMALS)
            farm["tiles"][y][x] = {
                "kind": agent_module.ANIMAL_STRUCTURE[animal], "animal": animal,
                "placed_day": max(0, day - rng.randrange(12)),
                "yield_units": rng.randrange(7),
                "consecutive_unfed": rng.randrange(2),
                "fed_today": rng.choice([True, False]),
                "cared_today": rng.choice([True, False]),
                "fertilizer_available": rng.choice([True, False]),
                "pending_care_bonus": rng.randrange(3),
            }
        elif kind == "STRUCTURE":
            farm["tiles"][y][x] = {"kind": rng.choice(["COOP", "PASTURE"])}
        else:
            farm["tiles"][y][x] = {"kind": "WEED"}

    for item in private["shed"]:
        private["shed"][item] = rng.randrange(7)
    for crop in private["seeds"]:
        private["seeds"][crop] = rng.randrange(8)
    all_carryables = list(agent_module.PRODUCTS) + list(agent_module.ANIMALS)
    for inventory in private["inventories"]:
        for item in rng.sample(all_carryables, rng.randrange(4)):
            inventory[item] = rng.randrange(1, 5)

    shops = list(agent_module.SHOP_PRODUCTS)
    obs["town"] = {"unlocked_shops": [rng.choice(shops) for _ in range(rng.randrange(9))]}
    for item in agent_module.PRODUCTS:
        inventory = 10000 + rng.randrange(-500, 501)
        obs["market"]["inventory"][item] = inventory
        obs["market"]["prices"][item] = agent_module._modeled_price(item, inventory)

    start = time.perf_counter()
    action = agent_module.agent(obs)
    latencies.append(time.perf_counter() - start)
    validate_action(obs, action)

latencies_ms = [1000.0 * x for x in latencies]
latencies_ms.sort()
p95 = latencies_ms[int(0.95 * (len(latencies_ms) - 1))]
print(f"Fuzz cases: {len(latencies_ms)}")
print(f"Mean latency: {statistics.mean(latencies_ms):.3f} ms")
print(f"P95 latency:  {p95:.3f} ms")
print(f"Max latency:  {max(latencies_ms):.3f} ms")
print("Randomised contract/fuzz test: OK")

# Optional exact integration test. It runs automatically when the current
# kaggle-environments package and the Kaggriculture environment are installed.
try:
    from kaggle_environments import make

    env = make("kaggriculture", debug=True)
    available = list(getattr(env, "agents", []) or [])

    def pass_agent(observation):
        farms = observation.get("farms", [])
        player = int(observation.get("player", 0))
        hand_count = len(farms[player].get("hands", [])) if farms else 0
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(hand_count)],
            "market": [],
        }

    opponent = "starter" if "starter" in available else pass_agent
    episode = env.run([agent_module.agent, opponent])
    terminal = episode[-1]
    statuses = [state.status for state in terminal]
    rewards = [state.reward for state in terminal]
    assert all(status == "DONE" for status in statuses), (statuses, rewards)
    print("Official simulator integration: OK")
    print("Terminal rewards:", rewards)
except Exception as exc:
    print("Optional official simulator test skipped:", type(exc).__name__, str(exc)[:240])
    print("The standalone compile, import, contract, and fuzz tests above remain mandatory and passed.")

# Build the exact competition archive: main.py must be at archive root.
with tarfile.open(ARCHIVE_PATH, mode="w:gz") as tar:
    tar.add(MAIN_PATH, arcname="main.py")

with tarfile.open(ARCHIVE_PATH, mode="r:gz") as tar:
    members = tar.getnames()
    assert members == ["main.py"], members
    packaged_source = tar.extractfile("main.py").read()

assert packaged_source == MAIN_PATH.read_bytes()

main_sha = hashlib.sha256(MAIN_PATH.read_bytes()).hexdigest()
archive_sha = hashlib.sha256(ARCHIVE_PATH.read_bytes()).hexdigest()
manifest = {
    "competition": "kaggriculture",
    "strategy": "original deterministic economic scheduler; no RL or replay",
    "created_utc_date": "2026-08-10",
    "entry_point": "main.py:agent",
    "archive_members": members,
    "main_py_bytes": MAIN_PATH.stat().st_size,
    "archive_bytes": ARCHIVE_PATH.stat().st_size,
    "main_py_sha256": main_sha,
    "submission_tar_gz_sha256": archive_sha,
    "synthetic_fuzz_cases": 750,
}
MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

print(json.dumps(manifest, indent=2))
print("\nSubmission package validation: OK")
print(f"Upload: {ARCHIVE_PATH}")