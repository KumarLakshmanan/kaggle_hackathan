"""Kaggriculture v3.0 High-Performance Dynamic Agent.

Comprehensive multi-phase strategy targeting leaderboard placement (3,000-13,000+ coins).

Key design principles from top-30 analysis:
1. Correct observation format: obs["player"], obs["day"], obs["hour"],
   private["shed"], private["seeds"], private["inventories"],
   farms[player]["unlocked_quadrants"], farms[player]["money"]
2. Starting money is $3,000 — aggressive early expansion is critical
3. Multi-phase strategy: Early wheat/carrot → Land expansion → Melon/Livestock scaling → Terminal liquidation
4. Fertilizer as infinite revenue stream (animals produce free daily, town doesn't consume it)
5. CARE action banks yield bonuses for animals
6. Market price awareness: Premium goods (Melon, Milk, Wool, Strawberry) crash hard on overproduction
7. Town demand exploitation: shops unlock every 3 days, consumption grows over time
8. Shed capacity management (100 items cap)
9. Weed repair: DIG → retry planned action
10. Terminal liquidation at step 718 with opponent-exposure-aware priority selling
"""

import math

# Board layout constants
BOARD_SIZE = 10
SHED_ADJACENT = [(4, 4), (5, 4), (4, 5), (5, 5)]

# Crop data from competition spec
CROPS = {
    "WHEAT":      {"cost": 10, "base_price": 25, "first_yield_day": 2, "max_yield_day": 4, "max_yield": 6, "unfert_max": 4, "type": "one_time"},
    "CARROT":     {"cost": 20, "base_price": 35, "first_yield_day": 2, "max_yield_day": 3, "max_yield": 4, "unfert_max": 3, "type": "one_time"},
    "MELON":      {"cost": 80, "base_price": 250, "first_yield_day": 10, "max_yield_day": 10, "max_yield": 6, "type": "one_time"},
    "TOMATO":     {"cost": 50, "base_price": 60, "first_yield_day": 8, "max_yield_day": 11, "max_yield": 4, "type": "ongoing"},
    "STRAWBERRY": {"cost": 100, "base_price": 120, "first_yield_day": 10, "max_yield_day": 16, "max_yield": 4, "type": "ongoing"},
}

# Animal data
ANIMALS = {
    "GOOSE": {"cost": 300, "product": "EGG", "base_price": 50, "structure": "COOP", "interval": 1, "max_held": 4},
    "COW":   {"cost": 400, "product": "MILK", "base_price": 160, "structure": "PASTURE", "interval": 2, "max_held": 6},
    "SHEEP": {"cost": 500, "product": "WOOL", "base_price": 200, "structure": "PASTURE", "interval": 3, "max_held": 6},
}

PRODUCT_BY_ANIMAL = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}

# Sellable items ordered by value priority (premium first)
SELLABLE = ("MELON", "STRAWBERRY", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER")

# Market glut weights: how much selling each item hurts/helps
GLUT_WEIGHT = {
    "MELON": 3.6, "STRAWBERRY": 2.0, "MILK": 2.0, "WOOL": 3.2,
    "EGG": 1.5, "TOMATO": 1.3, "CARROT": 1.0, "WHEAT": 1.0, "FERTILIZER": 1.0,
}

# Premium items that crash hard on overproduction — sell carefully
PREMIUM_ITEMS = {"MELON", "STRAWBERRY", "MILK", "WOOL"}

# Land quadrant costs
LAND_COSTS = [1000, 2000, 4000]

# Fibonacci sequence for hiring costs
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]


def _get(data, key, default=None):
    """Safe dict access that handles various observation formats."""
    if isinstance(data, dict):
        return data.get(key, default)
    getter = getattr(data, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(data, key, default)


def _dist(p1, p2):
    """Manhattan distance between two points."""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def _step_toward(cx, cy, tx, ty):
    """Return movement action toward target tile."""
    if cx == tx and cy == ty:
        return ["PASS"]
    dx = tx - cx
    dy = ty - cy
    # Prefer the axis with larger distance
    if abs(dx) >= abs(dy):
        return ["EAST"] if dx > 0 else ["WEST"]
    return ["SOUTH"] if dy > 0 else ["NORTH"]


def _is_shed_adjacent(x, y):
    """Check if position is orthogonally adjacent to the shed center."""
    return (x, y) in SHED_ADJACENT


def _tile_at(tiles, x, y):
    """Safe tile access."""
    try:
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
            return tiles[y][x]
    except (IndexError, TypeError):
        pass
    return "LOCKED"


# ─── State tracking across turns (persists within a single episode) ───
_AGENT_STATE = {}


def _get_state(player):
    """Get or initialize per-player persistent state."""
    if player not in _AGENT_STATE:
        _AGENT_STATE[player] = {
            "last_step": -1,
            "weed_repairs": {},   # actor -> {start_step, intended_action}
            "sold_this_day": {},  # item -> quantity sold today
        }
    return _AGENT_STATE[player]


def _reset_state_if_needed(state, step, day):
    """Reset state on new episode or new day."""
    if step <= state["last_step"]:
        # New episode detected
        state.update({"last_step": step, "weed_repairs": {}, "sold_this_day": {}})
    if step % 24 == 0:
        state["sold_this_day"] = {}
    state["last_step"] = step


def agent(obs):
    """Main agent entry point — compatible with Kaggle submission format."""
    try:
        return _agent_logic(obs)
    except Exception:
        # Failsafe: never crash
        player = int(_get(obs, "player", 0) or 0)
        farms = list(_get(obs, "farms", []) or [])
        farm = farms[player] if player < len(farms) else {}
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
            "market": [],
        }


def _agent_logic(obs):
    # ─── Parse observation ───
    player = int(_get(obs, "player", 0) or 0)
    step = int(_get(obs, "step", 0) or 0)
    day = int(_get(obs, "day", 0) or 0)
    hour = int(_get(obs, "hour", 0) or 0)

    farms = list(_get(obs, "farms", []) or [])
    my_farm = farms[player] if player < len(farms) else {}
    opp_farm = farms[1 - player] if len(farms) >= 2 else {}

    private = _get(obs, "private", {}) or {}
    money = float(_get(my_farm, "money", 0) or 0)
    shed = dict(_get(private, "shed", {}) or {})
    seeds = dict(_get(private, "seeds", {}) or {})
    inventories = list(_get(private, "inventories", []) or [])

    unlocks = list(_get(my_farm, "unlocked_quadrants", []) or [])
    farmer_pos = list(_get(my_farm, "farmer", [4, 4]) or [4, 4])
    hands_list = list(_get(my_farm, "hands", []) or [])
    hands_pos = [list(h) for h in hands_list]
    hires_today = int(_get(my_farm, "hires_today", 0) or 0)
    tiles = _get(my_farm, "tiles", []) or []

    market_data = _get(obs, "market", {}) or {}
    prices = dict(_get(market_data, "prices", {}) or {})
    market_inv = dict(_get(market_data, "inventory", {}) or {})

    town = _get(obs, "town", {}) or {}
    unlocked_shops = list(_get(town, "unlocked_shops", []) or [])

    state = _get_state(player)
    _reset_state_if_needed(state, step, day)

    positions = [farmer_pos] + hands_pos
    num_units = len(positions)

    # ─── PHASE 1: Board Audit ───
    empty_tiles = []       # (x, y) — empty unlocked tiles
    unwatered = []         # (x, y, crop, age) — plants needing water
    harvestable = []       # (x, y, crop, value_estimate)
    weed_tiles = []        # (x, y)
    animal_tiles = []      # (x, y, animal_type, tile_dict)
    empty_structures = []  # (x, y, structure_kind)
    plant_tiles = []       # (x, y, crop, tile_dict) — all plants

    cow_count = 0
    sheep_count = 0
    goose_count = 0
    pasture_count = 0
    coop_count = 0
    total_plants = 0

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            tile = _tile_at(tiles, x, y)
            if tile == "LOCKED" or tile is None and not _is_in_unlocked(x, y, unlocks):
                continue

            if tile is None:
                empty_tiles.append((x, y))
            elif isinstance(tile, dict):
                kind = tile.get("kind", "")
                if kind == "PLANT":
                    total_plants += 1
                    crop = tile.get("crop", "")
                    planted_day = int(tile.get("planted_day", 0) or 0)
                    crop_age = day - planted_day
                    watered = tile.get("watered_today", False)
                    yield_units = int(tile.get("yield_units", 0) or 0)
                    plant_tiles.append((x, y, crop, tile))

                    if not watered:
                        unwatered.append((x, y, crop, crop_age))

                    # Check if harvestable
                    cfg = CROPS.get(crop, {})
                    first_yield = cfg.get("first_yield_day", 4)
                    if crop_age >= first_yield and yield_units > 0:
                        value = yield_units * cfg.get("base_price", 25)
                        harvestable.append((x, y, crop, value))

                elif kind == "WEED":
                    weed_tiles.append((x, y))

                elif kind in ("COOP", "PASTURE"):
                    animal = tile.get("animal")
                    if kind == "PASTURE":
                        pasture_count += 1
                    else:
                        coop_count += 1

                    if animal:
                        animal_tiles.append((x, y, animal, tile))
                        if animal == "COW":
                            cow_count += 1
                        elif animal == "SHEEP":
                            sheep_count += 1
                        elif animal == "GOOSE":
                            goose_count += 1
                    else:
                        empty_structures.append((x, y, kind))
            elif tile == "WEED" or (isinstance(tile, dict) and tile.get("kind") == "WEED"):
                weed_tiles.append((x, y))

    # Sort harvestable by value (highest first)
    harvestable.sort(key=lambda h: h[3], reverse=True)

    # ─── PHASE 2: Market Strategy ───
    market_orders = []
    reserve = 200  # Always keep a cash reserve
    available_money = money - reserve

    # Calculate worker capacity: each unit can handle ~8 tiles/day
    manageable_tiles = num_units * 8
    # Don't plant more than we can water
    max_new_plants = max(0, manageable_tiles - total_plants)

    # 2a. Selling Strategy (FIRST — generate revenue before spending)
    # Sell produce to free up shed and generate cash
    if step >= 718:
        # Terminal liquidation: sell EVERYTHING
        sell_orders = _terminal_sell(shed, prices, opp_farm)
        market_orders.extend(sell_orders)
    else:
        for item in SELLABLE:
            qty = shed.get(item, 0)
            if qty <= 0:
                continue
            price = prices.get(item, 10)
            if item in PREMIUM_ITEMS:
                # Premium: sell in smaller batches
                base_p = {"MELON": 250, "STRAWBERRY": 120, "MILK": 160, "WOOL": 200}.get(item, 100)
                if price >= base_p * 0.4:
                    sell_qty = min(qty, 8)
                else:
                    sell_qty = min(qty, 3)
            elif item == "FERTILIZER":
                # Fertilizer: sell all (town doesn't consume it)
                sell_qty = qty
            else:
                sell_qty = qty
            if sell_qty > 0:
                market_orders.append(["SELL", item, sell_qty])

    # Recalculate money after expected sales
    expected_revenue = sum(
        min(shed.get(o[1], 0), o[2]) * prices.get(o[1], 10)
        for o in market_orders if len(o) >= 3 and o[0] == "SELL"
    )
    projected_money = available_money + expected_revenue

    # 2b. Farm Hand Hiring (daily at start of day)
    if day < 2:
        target_hands = 1
    elif day < 6:
        target_hands = 2
    elif day < 12:
        target_hands = 3
    elif day < 22:
        target_hands = 4
    else:
        target_hands = 5

    num_hands = len(hands_pos)
    if hour == 0 and num_hands < target_hands:
        hands_to_hire = min(target_hands - num_hands, 2)
        for i in range(hands_to_hire):
            hire_cost = FIB[min(hires_today + i, len(FIB) - 1)]
            if projected_money >= hire_cost + 50:
                market_orders.append(["HIRE"])
                projected_money -= hire_cost

    # 2c. Land Expansion — buy when we have enough workers to use it
    num_unlocks = len(unlocks)
    if num_unlocks < 4:
        land_cost = LAND_COSTS[num_unlocks - 1] if num_unlocks >= 1 else 1000
        # Only expand when we can afford it AND have workers to cover more land
        need_expand = (total_plants + 5 >= manageable_tiles and num_units >= 3) or day >= 10
        if projected_money >= land_cost + 200 and need_expand:
            market_orders.append(["BUY_LAND"])
            projected_money -= land_cost

    # 2d. Wheat stock for animal feed
    total_animals = cow_count + sheep_count + goose_count
    wheat_available = shed.get("WHEAT", 0) + seeds.get("WHEAT", 0)
    if total_animals > 0 and wheat_available < total_animals * 3:
        buy_wheat = total_animals * 3
        cost = buy_wheat * prices.get("WHEAT", 25)
        if projected_money >= cost + 100:
            market_orders.append(["BUY_PRODUCT", "WHEAT", buy_wheat])
            projected_money -= cost

    # 2e. Animal purchases — only when pasture/coop already exists or can be built
    empty_pastures = sum(1 for _, _, k in empty_structures if k == "PASTURE")
    empty_coops = sum(1 for _, _, k in empty_structures if k == "COOP")
    has_empty_for_pasture = len(empty_tiles) > 3  # Leave room

    if day >= 3 and day <= 20:
        # Buy cow only if we have a pasture ready OR can build one
        if (cow_count + shed.get("COW", 0)) < 2 and projected_money >= 500:
            if empty_pastures > 0 or has_empty_for_pasture:
                market_orders.append(["BUY_ANIMAL", "COW", 1])
                projected_money -= 400
        if day >= 4 and (goose_count + shed.get("GOOSE", 0)) < 1 and projected_money >= 400:
            if empty_coops > 0 or has_empty_for_pasture:
                market_orders.append(["BUY_ANIMAL", "GOOSE", 1])
                projected_money -= 300

    # 2f. Seed purchases — STRICTLY limited to worker capacity
    total_seeds = sum(seeds.values())
    seeds_budget = max(0, max_new_plants - total_seeds)

    if seeds_budget > 0 and projected_money >= 30:
        if day <= 5:
            # Early: wheat (for feed + cash) and carrots
            wh = min(max(2, seeds_budget // 3), int(projected_money // 15))
            if wh > 0:
                market_orders.append(["BUY_SEED", "WHEAT", wh])
                projected_money -= wh * 10
                seeds_budget -= wh
            if seeds_budget > 0 and projected_money >= 30:
                ca = min(seeds_budget, int(projected_money // 25))
                if ca > 0:
                    market_orders.append(["BUY_SEED", "CARROT", ca])
                    projected_money -= ca * 20
        elif day <= 18:
            # Mid: melons (if early enough) + carrots for rotation
            if day + 10 <= 29 and projected_money >= 100:
                mel = min(seeds_budget, int(projected_money // 100))
                if mel > 0:
                    market_orders.append(["BUY_SEED", "MELON", mel])
                    projected_money -= mel * 80
                    seeds_budget -= mel
            if seeds_budget > 0 and projected_money >= 30:
                ca = min(seeds_budget, int(projected_money // 25))
                if ca > 0:
                    market_orders.append(["BUY_SEED", "CARROT", ca])
                    projected_money -= ca * 20
        elif day <= 26:
            # Late: only fast crops that can mature
            ca = min(seeds_budget, int(projected_money // 25))
            if ca > 0:
                market_orders.append(["BUY_SEED", "CARROT", ca])
                projected_money -= ca * 20

    # 2g. Fertilizer for melons
    fert_available = shed.get("FERTILIZER", 0)
    melon_plants = sum(1 for _, _, c, _ in plant_tiles if c == "MELON")
    if melon_plants > 0 and fert_available < melon_plants and projected_money >= 150:
        fert_buy = min(melon_plants - fert_available, 5)
        if fert_buy > 0:
            market_orders.append(["BUY_PRODUCT", "FERTILIZER", fert_buy])

    # Cap market orders at 10
    market_orders = market_orders[:10]

    # ─── PHASE 3: Unit Action Dispatch ───
    unit_actions = []

    # Priority task queues for all units
    # High priority: watering (prevent weed conversion!)
    # Medium: harvesting mature crops, feeding animals
    # Low: planting, building, navigating

    # Create task assignment tracking to avoid duplicate assignments
    assigned_tiles = set()

    for idx in range(num_units):
        pos = positions[idx]
        x, y = int(pos[0]), int(pos[1])
        inv = inventories[idx] if idx < len(inventories) else {}
        actor_key = "farmer" if idx == 0 else idx - 1

        # Check for active weed repair transactions
        if actor_key in state["weed_repairs"]:
            repair = state["weed_repairs"][actor_key]
            age = step - repair["start_step"]
            if age == 1:
                # Retry the intended action
                unit_actions.append(list(repair["intended_action"]))
                del state["weed_repairs"][actor_key]
                continue
            elif age > 1:
                del state["weed_repairs"][actor_key]

        tile = _tile_at(tiles, x, y)
        has_items = any(v > 0 for v in inv.values()) if isinstance(inv, dict) else False

        # ── Standing Actions (immediate, on current tile) ──

        # On a WEED: DIG it
        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            unit_actions.append(["DIG"])
            continue

        # On a PLANT
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop = tile.get("crop", "")
            planted_day_val = int(tile.get("planted_day", 0) or 0)
            crop_age = day - planted_day_val
            watered = tile.get("watered_today", False)
            yield_units = int(tile.get("yield_units", 0) or 0)
            cfg = CROPS.get(crop, {})

            # Harvest if mature and has yield
            if crop_age >= cfg.get("first_yield_day", 4) and yield_units > 0:
                unit_actions.append(["HARVEST"])
                assigned_tiles.add((x, y))
                continue

            # Water if unwatered (critical: prevents weed!)
            if not watered:
                unit_actions.append(["WATER"])
                assigned_tiles.add((x, y))
                continue

            # Fertilize if plant can benefit and we have fertilizer
            fert_until = int(tile.get("fertilized_until_day", -1) or -1)
            if fert_until < day and (inv.get("FERTILIZER", 0) > 0 or shed.get("FERTILIZER", 0) > 0):
                # Fertilize melons and ongoing crops preferentially
                if crop in ("MELON", "TOMATO", "STRAWBERRY"):
                    unit_actions.append(["FERTILIZE"])
                    assigned_tiles.add((x, y))
                    continue

        # On a COOP or PASTURE with animal
        if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
            animal = tile.get("animal")
            if animal:
                # Feed if unfed (critical: prevents escape!)
                if not tile.get("fed_today", False):
                    if inv.get("WHEAT", 0) > 0 or shed.get("WHEAT", 0) > 0:
                        unit_actions.append(["FEED"])
                        assigned_tiles.add((x, y))
                        continue

                # Harvest animal product if available
                yield_u = int(tile.get("yield_units", 0) or 0)
                if yield_u > 0:
                    unit_actions.append(["HARVEST"])
                    assigned_tiles.add((x, y))
                    continue

                # Care for animal (banks yield bonus)
                if not tile.get("cared_today", False):
                    unit_actions.append(["CARE"])
                    assigned_tiles.add((x, y))
                    continue

                # Collect fertilizer (free daily revenue!)
                if tile.get("fertilizer_available", False):
                    unit_actions.append(["COLLECT_FERTILIZER"])
                    assigned_tiles.add((x, y))
                    continue

            elif animal is None:
                # Empty structure: place an animal if we have one
                structure_kind = tile.get("kind")
                if structure_kind == "PASTURE":
                    if shed.get("COW", 0) > 0 or inv.get("COW", 0) > 0:
                        unit_actions.append(["PLACE", "COW"])
                        assigned_tiles.add((x, y))
                        continue
                    elif shed.get("SHEEP", 0) > 0 or inv.get("SHEEP", 0) > 0:
                        unit_actions.append(["PLACE", "SHEEP"])
                        assigned_tiles.add((x, y))
                        continue
                elif structure_kind == "COOP":
                    if shed.get("GOOSE", 0) > 0 or inv.get("GOOSE", 0) > 0:
                        unit_actions.append(["PLACE", "GOOSE"])
                        assigned_tiles.add((x, y))
                        continue

        # On an empty tile: plant or build
        if tile is None:
            # Build structure if we have animals waiting
            if shed.get("COW", 0) > 0 or shed.get("SHEEP", 0) > 0:
                if pasture_count < cow_count + sheep_count + shed.get("COW", 0) + shed.get("SHEEP", 0):
                    unit_actions.append(["BUILD_PASTURE"])
                    assigned_tiles.add((x, y))
                    continue
            if shed.get("GOOSE", 0) > 0:
                if coop_count < goose_count + shed.get("GOOSE", 0):
                    unit_actions.append(["BUILD_COOP"])
                    assigned_tiles.add((x, y))
                    continue

            # Plant crop if we have seeds
            planted = False
            # Priority: Melon (if early enough to mature), then Carrot, then Wheat
            for crop_name in ["MELON", "CARROT", "WHEAT"]:
                if seeds.get(crop_name, 0) > 0:
                    cfg = CROPS[crop_name]
                    # Don't plant if it can't mature before end of season
                    days_to_mature = cfg["first_yield_day"]
                    if day + days_to_mature <= 29:
                        unit_actions.append(["PLANT", crop_name])
                        planted = True
                        assigned_tiles.add((x, y))
                        break
            if planted:
                continue

        # ── Drop inventory at shed if carrying items ──
        if has_items and _is_shed_adjacent(x, y):
            unit_actions.append(["DROP"])
            continue

        # ── Route to shed to drop off items ──
        if has_items:
            nearest_shed = min(SHED_ADJACENT, key=lambda s: _dist(pos, s))
            unit_actions.append(_step_toward(x, y, nearest_shed[0], nearest_shed[1]))
            continue

        # ── Navigation: Find best task to walk toward ──
        target = _find_best_target(x, y, unwatered, harvestable, animal_tiles,
                                   weed_tiles, empty_tiles, assigned_tiles, day, shed, seeds)
        if target:
            tx, ty = target
            if tx == x and ty == y:
                unit_actions.append(["PASS"])
            else:
                unit_actions.append(_step_toward(x, y, tx, ty))
                assigned_tiles.add((tx, ty))
        else:
            unit_actions.append(["PASS"])

    # ─── PHASE 4: Weed Repair Check ───
    # Check if any unit is about to PLANT or BUILD but standing on a weed
    for idx in range(num_units):
        pos = positions[idx]
        x, y = int(pos[0]), int(pos[1])
        tile = _tile_at(tiles, x, y)
        action = unit_actions[idx] if idx < len(unit_actions) else ["PASS"]

        if isinstance(action, list) and action[0] in ("PLANT", "BUILD_PASTURE", "BUILD_COOP"):
            if isinstance(tile, dict) and tile.get("kind") == "WEED":
                actor_key = "farmer" if idx == 0 else idx - 1
                state["weed_repairs"][actor_key] = {
                    "start_step": step,
                    "intended_action": list(action),
                }
                unit_actions[idx] = ["DIG"]

    # Build final action dict
    farmer_action = unit_actions[0] if unit_actions else ["PASS"]
    hands_actions = unit_actions[1:] if len(unit_actions) > 1 else []

    # Align hands count
    expected_hands = len(hands_pos)
    while len(hands_actions) < expected_hands:
        hands_actions.append(["PASS"])
    hands_actions = hands_actions[:expected_hands]

    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market_orders,
    }


def _is_in_unlocked(x, y, unlocks):
    """Check if tile is in an unlocked quadrant."""
    if x < 5 and y < 5:
        return "NW" in unlocks
    if x >= 5 and y < 5:
        return "NE" in unlocks
    if x < 5 and y >= 5:
        return "SW" in unlocks
    if x >= 5 and y >= 5:
        return "SE" in unlocks
    return False


def _find_best_target(x, y, unwatered, harvestable, animal_tiles,
                      weed_tiles, empty_tiles, assigned, day, shed, seeds):
    """Find the best tile to navigate toward based on priority."""
    best = None
    best_score = -float("inf")

    # Priority 1: Unwatered crops (prevent weeds!)
    for ux, uy, crop, age in unwatered:
        if (ux, uy) in assigned:
            continue
        dist = _dist((x, y), (ux, uy))
        score = 10000 - dist * 10  # Very high priority
        if score > best_score:
            best_score = score
            best = (ux, uy)

    # Priority 2: Animals needing feed
    for ax, ay, animal, tile in animal_tiles:
        if (ax, ay) in assigned:
            continue
        if not tile.get("fed_today", False):
            dist = _dist((x, y), (ax, ay))
            score = 9000 - dist * 10
            if score > best_score:
                best_score = score
                best = (ax, ay)

    # Priority 3: Harvestable crops (highest value first)
    for hx, hy, crop, value in harvestable:
        if (hx, hy) in assigned:
            continue
        dist = _dist((x, y), (hx, hy))
        score = 5000 + value - dist * 20
        if score > best_score:
            best_score = score
            best = (hx, hy)

    # Priority 4: Animal products/fertilizer to collect
    for ax, ay, animal, tile in animal_tiles:
        if (ax, ay) in assigned:
            continue
        yield_u = int(tile.get("yield_units", 0) or 0)
        fert = tile.get("fertilizer_available", False)
        cared = tile.get("cared_today", False)
        if yield_u > 0 or fert or not cared:
            dist = _dist((x, y), (ax, ay))
            score = 3000 - dist * 10
            if score > best_score:
                best_score = score
                best = (ax, ay)

    # Priority 5: Weed clearing
    for wx, wy in weed_tiles:
        if (wx, wy) in assigned:
            continue
        dist = _dist((x, y), (wx, wy))
        score = 2000 - dist * 10
        if score > best_score:
            best_score = score
            best = (wx, wy)

    # Priority 6: Empty tiles for planting
    has_seeds = any(v > 0 for v in seeds.values())
    if has_seeds or shed.get("COW", 0) > 0 or shed.get("GOOSE", 0) > 0 or shed.get("SHEEP", 0) > 0:
        for ex, ey in empty_tiles:
            if (ex, ey) in assigned:
                continue
            dist = _dist((x, y), (ex, ey))
            score = 1000 - dist * 10
            if score > best_score:
                best_score = score
                best = (ex, ey)

    return best


def _terminal_sell(shed, prices, opp_farm):
    """Terminal market liquidation — sell everything for maximum final score."""
    # Calculate opponent exposure
    exposure = {}
    for item in SELLABLE:
        exposure[item] = 0.0
    for row in (_get(opp_farm, "tiles", []) or []):
        if not isinstance(row, list):
            continue
        for tile in row:
            if not isinstance(tile, dict):
                continue
            crop = str(tile.get("crop", "")).upper()
            if crop in exposure:
                exposure[crop] += max(1.0, float(tile.get("yield_units", 0) or 0))
            product = PRODUCT_BY_ANIMAL.get(str(tile.get("animal", "")).upper())
            if product:
                exposure[product] += 1.0 + max(0.0, float(tile.get("yield_units", 0) or 0))
            if tile.get("fertilizer_available", False):
                exposure["FERTILIZER"] += 1.0

    rows = []
    for i, item in enumerate(SELLABLE):
        qty = max(0, int(shed.get(item, 0) or 0))
        if qty <= 0:
            continue
        price = max(1.0, float(prices.get(item, 1) or 1))
        score = (
            (1.0 + exposure.get(item, 0.0))
            * GLUT_WEIGHT.get(item, 1.0)
            * price
            * math.log1p(qty)
        )
        rows.append((score, -i, item, qty))

    rows.sort(reverse=True)
    return [["SELL", item, qty] for _, _, item, qty in rows[:10]]


my_agent = agent
