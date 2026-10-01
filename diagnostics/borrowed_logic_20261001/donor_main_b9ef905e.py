"""General Kaggriculture engine v3. Generated from inspectable source modules.
No replay routes, external imports beyond Python stdlib, or evaluator seeds.
Research candidate; no guaranteed strength or leaderboard qualification.
"""
import sys as _sys
import types as _types
_PACKAGE = _types.ModuleType('_kaggriculture_general_v3')
_PACKAGE.__path__ = []
_sys.modules[_PACKAGE.__name__] = _PACKAGE

# BEGIN SOURCE native_core.py
_SOURCE_NATIVE_CORE = '''"""Pure Kaggriculture 1.32.7 transitions; initialized-state use only."""
import math
import random

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]

MARKET_I0 = 10000

PRICE_FLOOR = 1

MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "I0": MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base":  35, "I0": MARKET_I0, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base":  60, "I0": MARKET_I0, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base":  50, "I0": MARKET_I0, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

HINGE_GAIN = 8.0

def _shape(func, x, T=None):
    x = max(0.0, x)
    if func == "linear": return x
    if func == "sq":     return x * x
    if func == "sqrt":   return math.sqrt(x)
    if func == "log":    return math.log(1.0 + x)
    if func == "log10":  return math.log10(1.0 + x)
    if func == "hinge":
        # Degenerates to linear if T is missing or non-positive.
        if not T or T <= 0:
            return x
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x

def _resolve_market_params(overrides):
    """Merge per-resource overrides onto MARKET_PARAMS defaults (sparse)."""
    resolved = {item: dict(p) for item, p in MARKET_PARAMS.items()}
    if not overrides:
        return resolved
    for item, patch in overrides.items():
        if item in resolved and isinstance(patch, dict):
            resolved[item].update(patch)
    return resolved

FARMER_MOVES = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST":  (1, 0),
    "WEST":  (-1, 0),
}

LAND_ORDER = ["NE", "SW", "SE"]

LAND_PRICES = [1000, 2000, 4000]

FARM_HAND_COST_MULT = 1

SHOPS = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

TOWN_CENTER_PRODUCTS = [p for p in PRODUCTS if p != "FERTILIZER"]

MAX_SHOP_INSTANCES = 8

def get(d, key, default):
    if isinstance(d, dict):
        return d.get(key, default)
    return getattr(d, key, default)

def _quadrant_of(x, y, board_size):
    half = board_size // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")

def _shed_access_tiles(board_size):
    """Four inner-corner tiles around the shed, in NWSE order."""
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]

def _is_shed_adjacent(pos, board_size):
    return tuple(pos) in {(x, y) for (x, y) in _shed_access_tiles(board_size)}

def _new_farm(board_size, starting_money):
    return {
        "money": float(starting_money),
        # tiles[y][x] = None (empty unlocked) | "LOCKED" | dict structure
        "tiles": [
            [_initial_tile(x, y, board_size) for x in range(board_size)]
            for y in range(board_size)
        ],
        "farmer": list(_default_spawn(board_size)),
        "hands": [],
        "unlocked_quadrants": ["NW"],
        "hires_today": 0,
    }

def _initial_tile(x, y, board_size):
    return None if _quadrant_of(x, y, board_size) == "NW" else "LOCKED"

def _default_spawn(board_size):
    """First free shed-access tile, NWSE preference."""
    for tile in _shed_access_tiles(board_size):
        if _quadrant_of(tile[0], tile[1], board_size) == "NW":
            return tile
    return (0, 0)

def _new_private():
    return {
        "shed": {item: 0 for item in PRODUCTS + list(ANIMALS)},
        "seeds": {crop: 0 for crop in CROPS},
        # inventories[0] = main farmer; hands appended/removed each day.
        "inventories": [{}],
    }

def _new_market(params=None):
    params = params or MARKET_PARAMS
    inv = {item: params[item]["I0"] for item in PRODUCTS}
    prices = {item: params[item]["base"] for item in PRODUCTS}
    market = {"inventory": inv, "prices": prices}
    if params is not MARKET_PARAMS:
        market["params"] = params
    return market

def _new_town():
    return {"unlocked_shops": []}

def market_price(item, inventory, params=None):
    """Floor at PRICE_FLOOR."""
    p = (params or MARKET_PARAMS)[item]
    base = p["base"]
    I0 = p["I0"]
    T = p["T"]
    if inventory < I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, T, T)
        price = base + amp * _shape(f, I0 - inventory, T)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, T, T)
        price = base - amp * _shape(f, inventory - I0, T)
    return max(PRICE_FLOOR, int(round(price)))

def _refresh_prices(market):
    params = market.get("params")
    for item in PRODUCTS:
        market["prices"][item] = market_price(item, market["inventory"][item], params)

def _new_plant(crop, day, turns_per_day):
    cd = CROPS[crop]
    return {
        "kind": "PLANT",
        "crop": crop,
        "planted_day": day,
        "watered_today": False,
        "consecutive_unwatered": 1,  # planting day counts as unwatered
        "yield_units": 0 if cd["ongoing"] else 1,
        "max_lifespan_step": (-1 if cd["ongoing"] else (day + cd["max_yield_day"] + 1) * turns_per_day),
        "fertilized_until_day": -1,
    }

def _new_animal(animal, day):
    a = ANIMALS[animal]
    return {
        "kind": a["structure"],
        "animal": animal,
        "placed_day": day,
        "yield_units": 0,
        "consecutive_unfed": 0,
        "fed_today": False,
        "cared_today": False,
        "fertilizer_available": False,
        "pending_care_bonus": 0,
    }

def _farmer_position(farm, idx):
    """idx 0 = main farmer, 1+ = hand index."""
    if idx == 0:
        return farm["farmer"]
    return farm["hands"][idx - 1] if idx - 1 < len(farm["hands"]) else None

def _set_farmer_position(farm, idx, pos):
    if idx == 0:
        farm["farmer"] = list(pos)
    else:
        farm["hands"][idx - 1] = list(pos)

def _farmer_inventory(private, idx):
    """Inventories list is [main_farmer, *hands]; grow it if idx is past the end."""
    while len(private["inventories"]) <= idx:
        private["inventories"].append({})
    return private["inventories"][idx]

def _inv_add(inv, item, n=1):
    inv[item] = inv.get(item, 0) + n

def _inv_take(inv, item, n=1):
    if inv.get(item, 0) < n:
        return False
    inv[item] -= n
    if inv[item] == 0:
        del inv[item]
    return True

def _apply_unit_action(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
    """Process one farmer/hand's action. Invalid / illegal actions are silent no-ops."""
    if not isinstance(action, list) or not action:
        return
    op = action[0]
    pos = _farmer_position(farm, idx)
    if pos is None:
        return
    fx, fy = pos[0], pos[1]
    inv = _farmer_inventory(private, idx)

    if op in FARMER_MOVES:
        dx, dy = FARMER_MOVES[op]
        nx, ny = fx + dx, fy + dy
        if not (0 <= nx < board_size and 0 <= ny < board_size):
            return
        # Movement onto LOCKED tiles is allowed: a hand can spawn on a locked
        # shed-access tile, and blocking movement would strand it there forever.
        # Tile operations (PLANT, WATER, etc.) still no-op on LOCKED tiles.
        _set_farmer_position(farm, idx, (nx, ny))
        return

    if op == "PASS":
        return

    tile = farm["tiles"][fy][fx]

    # Shed operations resolve before the LOCKED guard. They use the tile only as
    # a standing position -- the shed itself is always owned -- and three of the
    # four shed-access tiles start LOCKED, so guarding them first would make the
    # shed unreachable from those tiles.
    if op == "DROP":
        if not _is_shed_adjacent((fx, fy), board_size):
            return
        shed = private["shed"]
        for item, n in list(inv.items()):
            if n <= 0:
                del inv[item]
                continue
            room = max(0, shed_capacity - sum(shed.values()))
            take = min(n, room)
            if take > 0:
                shed[item] = shed.get(item, 0) + take
            del inv[item]
        return

    if op == "PICKUP":
        if not _is_shed_adjacent((fx, fy), board_size):
            return
        if len(action) < 2:
            return
        item = action[1]
        n = int(action[2]) if len(action) >= 3 else 1
        if n <= 0:
            return
        # Seeds live in private["seeds"] and are consumed directly by PLANT;
        # they never pass through farmer inventory or the shed.
        available = private["shed"].get(item, 0)
        n = min(n, available)
        if n <= 0:
            return
        private["shed"][item] -= n
        _inv_add(inv, item, n)
        return

    if op == "PLACE":
        if len(action) < 2:
            return
        item = action[1]
        # Animal placement: standing on a matching unoccupied structure. A LOCKED
        # tile is the string "LOCKED", never a dict, so this branch cannot match
        # there and PLACE falls through to the shed path below.
        if (
            item in ANIMALS
            and isinstance(tile, dict)
            and tile.get("kind") == ANIMALS[item]["structure"]
            and "animal" not in tile
        ):
            if _inv_take(inv, item, 1):
                farm["tiles"][fy][fx] = _new_animal(item, day)
            return
        # Shed drop: orthogonally adjacent to the shed; obeys shedCapacity.
        if _is_shed_adjacent((fx, fy), board_size):
            n = int(action[2]) if len(action) >= 3 else 1
            if n <= 0:
                return
            n = min(n, inv.get(item, 0))
            if n <= 0:
                return
            current = sum(private["shed"].values())
            room = max(0, shed_capacity - current)
            n = min(n, room)
            if n <= 0:
                return
            inv[item] -= n
            if inv[item] == 0:
                del inv[item]
            private["shed"][item] = private["shed"].get(item, 0) + n
        return

    # Everything below mutates the tile the unit stands on, so it requires that
    # tile to be owned.
    if tile == "LOCKED":
        return

    if op == "PLANT":
        if len(action) < 2:
            return
        crop = action[1]
        if crop not in CROPS:
            return
        if tile is not None:
            return
        if private["seeds"].get(crop, 0) <= 0:
            return
        private["seeds"][crop] -= 1
        farm["tiles"][fy][fx] = _new_plant(crop, day, turns_per_day)
        return

    if op == "WATER":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            return
        if tile["watered_today"]:
            return
        tile["watered_today"] = True
        crop_data = CROPS[tile["crop"]]
        if not crop_data["ongoing"]:
            age_days = day - tile["planted_day"]
            window_start = (crop_data["max_yield_day"] + 1) // 2
            if window_start <= age_days <= crop_data["max_yield_day"]:
                bonus = 2 if tile["fertilized_until_day"] >= day else 1
                tile["yield_units"] = min(crop_data["max_yield"], tile["yield_units"] + bonus)
        return

    if op == "HARVEST":
        if not isinstance(tile, dict):
            return
        if tile.get("yield_units", 0) <= 0:
            return
        if tile.get("kind") == "PLANT":
            crop_data = CROPS[tile["crop"]]
            if day - tile["planted_day"] < crop_data["first_yield_day"]:
                # Ongoing crops only accumulate yield_units after first_yield_day,
                # so reaching here with yield_units > 0 indicates a bug.
                if crop_data["ongoing"]:
                    print(
                        f"WARNING: HARVEST on immature ongoing {tile['crop']} "
                        f"(planted day {tile['planted_day']}, current day {day}, "
                        f"first_yield_day {crop_data['first_yield_day']}, "
                        f"yield_units {tile['yield_units']}); should never happen"
                    )
                return
            units = tile["yield_units"]
            tile["yield_units"] = 0
            _inv_add(inv, tile["crop"], units)
            if not crop_data["ongoing"]:
                farm["tiles"][fy][fx] = None
        elif "animal" in tile:
            units = tile["yield_units"]
            tile["yield_units"] = 0
            _inv_add(inv, ANIMALS[tile["animal"]]["product"], units)
        return

    if op == "FERTILIZE":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            return
        if not _inv_take(inv, "FERTILIZER", 1):
            return
        # Active for `day`, `day+1`, `day+2` (3 days inclusive).
        tile["fertilized_until_day"] = max(tile.get("fertilized_until_day", -1), day + 2)
        return

    if op == "DIG":
        if tile is None:
            return
        # Removes plants, weeds, empty coop/pasture. Does NOT remove a placed animal.
        if isinstance(tile, dict) and "animal" in tile:
            return
        farm["tiles"][fy][fx] = None
        return

    if op == "BUILD_COOP":
        if tile is not None:
            return
        farm["tiles"][fy][fx] = {"kind": "COOP"}
        return

    if op == "BUILD_PASTURE":
        if tile is not None:
            return
        farm["tiles"][fy][fx] = {"kind": "PASTURE"}
        return

    if op == "FEED":
        if not (isinstance(tile, dict) and "animal" in tile):
            return
        if tile["fed_today"]:
            return
        if not _inv_take(inv, "WHEAT", 1):
            return
        tile["fed_today"] = True
        return

    if op == "COLLECT_FERTILIZER":
        if not (isinstance(tile, dict) and "animal" in tile):
            return
        if not tile["fertilizer_available"]:
            return
        tile["fertilizer_available"] = False
        _inv_add(inv, "FERTILIZER", 1)
        return

    if op == "CARE":
        if not (isinstance(tile, dict) and "animal" in tile):
            return
        if tile["cared_today"]:
            return
        tile["cared_today"] = True
        return

def _spawn_hand(farm, board_size):
    """First free shed-access tile (NWSE order); ties broken by min occupancy."""
    occupants = {tile: 0 for tile in _shed_access_tiles(board_size)}
    all_pos = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]
    for pos in all_pos:
        if pos in occupants:
            occupants[pos] += 1
    best = sorted(occupants.items(), key=lambda kv: (kv[1], _shed_access_tiles(board_size).index(kv[0])))
    return list(best[0][0])

def _process_market(state, env):
    """Per-unit lockstep: at each step, quote both players' current-unit prices, then commit both."""
    obs0 = state[0].observation
    market = obs0.market
    farms = obs0.farms
    privates = [s.observation.private for s in state]
    board_size = int(get(env.configuration, "boardSize", 10))
    max_orders = max(1, int(get(env.configuration, "maxMarketOrdersPerTurn", 10)))
    hire_mult = int(get(env.configuration, "farmHandCostMult", FARM_HAND_COST_MULT))
    shed_capacity = int(get(env.configuration, "shedCapacity", 100))

    queues = []
    for s in state:
        action = s.action if isinstance(s.action, dict) else {}
        m = action.get("market", []) if isinstance(action, dict) else []
        q = list(m) if isinstance(m, list) else []
        queues.append(q[:max_orders])

    max_len = max((len(q) for q in queues), default=0)
    for i in range(max_len):
        order_states = []
        for player_id, q in enumerate(queues):
            ostate = None
            if i < len(q):
                ostate = _parse_order(q[i])
            order_states.append(ostate)

        # Atomic orders (HIRE, BUY_LAND): handle once, in player order.
        for player_id, ostate in enumerate(order_states):
            if ostate is None:
                continue
            op = ostate["type"]
            if op == "HIRE":
                _do_hire(farms[player_id], privates[player_id], board_size, hire_mult)
                order_states[player_id] = None
            elif op == "BUY_LAND":
                _do_buy_land(farms[player_id], board_size)
                order_states[player_id] = None

        # Per-unit lockstep loop for SELL / BUY_*.
        idx_esc = 0
        while True:
            idx_esc += 1
            if idx_esc >= 100_000:
                print("WARNING: kaggriculture market loop exceeded 100k iterations; aborting")
                break
            quoted = [None, None]
            for player_id, ostate in enumerate(order_states):
                if ostate is None or ostate["remaining"] <= 0:
                    continue
                op = ostate["type"]
                item = ostate["item"]
                if op == "SELL" and item in PRODUCTS:
                    quoted[player_id] = ("SELL", item, market_price(item, market["inventory"][item], market.get("params")), ostate)
                elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                    # Quote at post-buy inventory so a buy/sell round-trip
                    # against an unchanged market nets zero.
                    quoted[player_id] = ("BUY_PRODUCT", item, market_price(item, market["inventory"][item] - 1, market.get("params")), ostate)
                elif op == "BUY_SEED" and item in CROPS:
                    quoted[player_id] = ("BUY_SEED", item, CROPS[item]["seed"], ostate)
                elif op == "BUY_ANIMAL" and item in ANIMALS:
                    quoted[player_id] = ("BUY_ANIMAL", item, ANIMALS[item]["cost"], ostate)
                else:
                    order_states[player_id] = None  # malformed sub-op; abort

            if all(q is None for q in quoted):
                break

            # Both players see the same pre-commit inventory for this unit.
            committed_any = False
            for player_id, q in enumerate(quoted):
                if q is None:
                    continue
                op, item, price, ostate = q
                ok = _commit_unit(op, item, price, farms[player_id], privates[player_id], market, shed_capacity)
                if ok:
                    ostate["remaining"] -= 1
                    committed_any = True
                else:
                    order_states[player_id] = None  # can't continue this order

            if not committed_any:
                break

        _refresh_prices(market)

def _parse_order(order):
    if not isinstance(order, list) or not order:
        return None
    op = order[0]
    if op == "HIRE":
        return {"type": "HIRE"}
    if op == "BUY_LAND":
        return {"type": "BUY_LAND"}
    if op in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"):
        if len(order) < 3:
            return None
        try:
            n = int(order[2])
        except (TypeError, ValueError):
            return None
        if n <= 0:
            return None
        return {"type": op, "item": order[1], "remaining": n}
    return None

def _commit_unit(op, item, price, farm, private, market, shed_capacity=100):
    if op == "SELL":
        if private["shed"].get(item, 0) <= 0:
            return False
        private["shed"][item] -= 1
        farm["money"] += price
        # Sales at $1 do not increase market supply.
        if price > 1:
            market["inventory"][item] += 1
        return True
    if op == "BUY_PRODUCT":
        if farm["money"] < price:
            return False
        # Bought goods land in the shed, which obeys shedCapacity like every
        # other deposit path (pickup, shed-drop, end-of-day drop).
        if sum(private["shed"].values()) >= shed_capacity:
            return False
        farm["money"] -= price
        private["shed"][item] = private["shed"].get(item, 0) + 1
        market["inventory"][item] -= 1
        return True
    if op == "BUY_SEED":
        if farm["money"] < price:
            return False
        farm["money"] -= price
        private["seeds"][item] = private["seeds"].get(item, 0) + 1
        return True
    if op == "BUY_ANIMAL":
        if farm["money"] < price:
            return False
        if sum(private["shed"].values()) >= shed_capacity:
            return False
        farm["money"] -= price
        private["shed"][item] = private["shed"].get(item, 0) + 1
        return True
    return False

def _fib(n):
    """Indexed so _fib(0)=1, _fib(1)=1, _fib(2)=2, _fib(3)=3, _fib(4)=5..."""
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def _hire_cost(n_already_today, mult=FARM_HAND_COST_MULT):
    return mult * _fib(n_already_today)

def _do_hire(farm, private, board_size, mult=FARM_HAND_COST_MULT):
    cost = _hire_cost(farm["hires_today"], mult)
    if farm["money"] < cost:
        return
    farm["money"] -= cost
    farm["hires_today"] += 1
    farm["hands"].append(_spawn_hand(farm, board_size))
    private["inventories"].append({})

def _do_buy_land(farm, board_size):
    n_unlocked_extra = len(farm["unlocked_quadrants"]) - 1  # NW is always there
    if n_unlocked_extra >= len(LAND_ORDER):
        return
    cost = LAND_PRICES[n_unlocked_extra]
    if farm["money"] < cost:
        return
    farm["money"] -= cost
    quadrant = LAND_ORDER[n_unlocked_extra]
    farm["unlocked_quadrants"].append(quadrant)
    for y in range(board_size):
        for x in range(board_size):
            if _quadrant_of(x, y, board_size) == quadrant and farm["tiles"][y][x] == "LOCKED":
                farm["tiles"][y][x] = None

def _town_consume(env, state, step):
    obs0 = state[0].observation
    market = obs0.market
    town = obs0.town
    cfg = env.configuration
    shop_interval = max(1, int(get(cfg, "townShopSellInterval", 4)))
    center_interval = max(1, int(get(cfg, "townCenterSellInterval", 24)))

    if step % shop_interval == 0:
        # unlocked_shops may list the same shop more than once (shops are drawn
        # with replacement); each instance consumes independently.
        for shop_name in town.get("unlocked_shops", []):
            products = SHOPS[shop_name]
            multiplier = 2 if len(products) == 1 else 1
            for item in products:
                market["inventory"][item] -= multiplier

    if step % center_interval == 0:
        for item in TOWN_CENTER_PRODUCTS:
            market["inventory"][item] -= 1

    _refresh_prices(market)

def _decay_plants(farm, step):
    board_size = len(farm["tiles"])
    for y in range(board_size):
        for x in range(board_size):
            tile = farm["tiles"][y][x]
            if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
                continue
            mls = tile["max_lifespan_step"]
            if mls < 0 or step < mls:
                continue
            if (step - mls) % 2 != 0:
                continue
            tile["yield_units"] -= 1
            if tile["yield_units"] <= 0:
                farm["tiles"][y][x] = {"kind": "WEED"}

def _daily_refresh_plants(farm, current_day, turns_per_day):
    board_size = len(farm["tiles"])
    next_day = current_day + 1
    for y in range(board_size):
        for x in range(board_size):
            tile = farm["tiles"][y][x]
            if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
                continue
            was_watered = tile["watered_today"]
            if was_watered:
                tile["consecutive_unwatered"] = 0
            else:
                tile["consecutive_unwatered"] += 1
            tile["watered_today"] = False
            if tile["consecutive_unwatered"] >= 2:
                farm["tiles"][y][x] = {"kind": "WEED"}
                continue
            cd = CROPS[tile["crop"]]
            if not cd["ongoing"]:
                continue
            days_since_first = next_day - tile["planted_day"] - cd["first_yield_day"]
            if days_since_first < 0:
                continue
            interval = cd["interval"]
            if days_since_first % interval != 0:
                continue
            production_count = days_since_first // interval + 1
            if production_count > cd["max_yield"]:
                continue
            # Fertilizer bonus only applies on watered days (basic needs first).
            fertilized = was_watered and tile.get("fertilized_until_day", -1) >= current_day
            tile["yield_units"] = min(cd["max_yield"], tile["yield_units"] + (2 if fertilized else 1))
            if production_count == cd["max_yield"]:
                tile["max_lifespan_step"] = (next_day + 1) * turns_per_day

def _daily_refresh_animals(farm, day):
    board_size = len(farm["tiles"])
    next_day = day + 1
    for y in range(board_size):
        for x in range(board_size):
            tile = farm["tiles"][y][x]
            if not (isinstance(tile, dict) and "animal" in tile):
                continue
            if tile["fed_today"]:
                tile["consecutive_unfed"] = 0
            else:
                tile["consecutive_unfed"] += 1
            if tile["consecutive_unfed"] >= 2:
                # Animal escapes; structure remains.
                farm["tiles"][y][x] = {"kind": ANIMALS[tile["animal"]]["structure"]}
                continue
            a = ANIMALS[tile["animal"]]
            days_since_first = next_day - tile["placed_day"] - a["first_yield_day"]
            if days_since_first >= 0 and days_since_first % a["interval"] == 0:
                base = 1
                # Care bonus only consumed on a fed production day.
                bonus = tile.pop("pending_care_bonus", 0) if tile["fed_today"] else 0
                tile["yield_units"] = min(a["max_held"], tile["yield_units"] + base + bonus)
                tile["pending_care_bonus"] = 0
            if tile["cared_today"] and tile["fed_today"]:
                tile["pending_care_bonus"] = tile.get("pending_care_bonus", 0) + 1
            tile["fertilizer_available"] = True
            tile["fed_today"] = False
            tile["cared_today"] = False

def _spawn_weeds(farm, board_size, weed_chance, rng):
    for y in range(board_size):
        for x in range(board_size):
            if farm["tiles"][y][x] is None and rng.random() < weed_chance:
                farm["tiles"][y][x] = {"kind": "WEED"}

def _drop_inventories_to_shed(private, capacity):
    """Drop every per-farmer inventory into the shed up to `capacity`; overflow is discarded.
    Seeds are tracked separately in private["seeds"] and don't pass through the shed."""
    shed = private["shed"]
    for inv in private["inventories"]:
        for item, n in list(inv.items()):
            if n <= 0:
                del inv[item]
                continue
            current = sum(v for k, v in shed.items())
            room = max(0, capacity - current)
            take = min(n, room)
            if take > 0:
                shed[item] = shed.get(item, 0) + take
            del inv[item]

def _end_of_day(state, env, day):
    obs0 = state[0].observation
    cfg = env.configuration
    board_size = int(get(cfg, "boardSize", 10))
    turns_per_day = max(1, int(get(cfg, "turnsPerDay", 24)))
    weed_chance = float(get(cfg, "weedSpawnChance", 0.005))
    shed_cap = int(get(cfg, "shedCapacity", 100))
    shop_interval = max(1, int(get(cfg, "townShopUnlockInterval", 3)))

    # Stable RNG keyed off env.info["seed"] + day so replays reproduce.
    seed = env.info.get("seed", 0)
    rng = random.Random((seed * 1_000_003) ^ day)

    for player_id, farm in enumerate(obs0.farms):
        private = state[player_id].observation.private
        _daily_refresh_plants(farm, day, turns_per_day)
        _daily_refresh_animals(farm, day)
        _spawn_weeds(farm, board_size, weed_chance, rng)
        _drop_inventories_to_shed(private, shed_cap)
        farm["farmer"] = list(_default_spawn(board_size))
        farm["hands"] = []
        farm["hires_today"] = 0
        private["inventories"] = [{}]

    next_day = day + 1
    town = obs0.town
    if next_day > 0 and next_day % shop_interval == 0:
        # Drawn with replacement: the same shop can unlock repeatedly, and each
        # copy consumes independently. Variety is not guaranteed; only the total
        # instance count is capped.
        if len(town["unlocked_shops"]) < MAX_SHOP_INSTANCES:
            town["unlocked_shops"].append(rng.choice(sorted(SHOPS)))

def interpreter(state, env):
    num_agents = len(state)
    obs0 = state[0].observation

    if not hasattr(obs0, "farms") or not obs0.farms:
        _initialize(state, env)
        return state

    if env.done:
        return state

    cfg = env.configuration
    turns_per_day = max(1, int(get(cfg, "turnsPerDay", 24)))
    board_size = int(get(cfg, "boardSize", 10))
    shed_capacity = int(get(cfg, "shedCapacity", 100))

    step = get(obs0, "step", 0)
    day = step // turns_per_day

    for i, s in enumerate(state):
        action = s.action if isinstance(s.action, dict) else {}
        farmer_action = action.get("farmer", ["PASS"]) if isinstance(action, dict) else ["PASS"]
        hands_actions = action.get("hands", []) if isinstance(action, dict) else []
        if not isinstance(hands_actions, list):
            hands_actions = []

        # Atomic PLANT validation: if total PLANT requests for a crop this turn
        # exceed available seeds, drop ALL PLANT requests for that crop.
        unit_actions = [farmer_action, *hands_actions]
        plant_demand = {}
        for a in unit_actions:
            if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
                plant_demand[a[1]] = plant_demand.get(a[1], 0) + 1
        seeds = s.observation.private.get("seeds", {}) if hasattr(s.observation.private, "get") else {}
        blocked = {crop for crop, n in plant_demand.items() if n > seeds.get(crop, 0)}

        def _allowed(a):
            if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT" and a[1] in blocked:
                return ["PASS"]
            return a

        _apply_unit_action(obs0.farms[i], s.observation.private, 0, _allowed(farmer_action),
                           board_size, day, turns_per_day, shed_capacity)
        for h_idx, hand_action in enumerate(hands_actions):
            _apply_unit_action(obs0.farms[i], s.observation.private, h_idx + 1,
                               _allowed(hand_action), board_size, day, turns_per_day, shed_capacity)

    _process_market(state, env)
    _town_consume(env, state, step)
    for farm in obs0.farms:
        _decay_plants(farm, step)
    if (step + 1) % turns_per_day == 0:
        _end_of_day(state, env, day)

    next_step = step + 1
    obs0.day = next_step // turns_per_day
    obs0.hour = next_step % turns_per_day
    for i in range(1, num_agents):
        state[i].observation.farms = obs0.farms
        state[i].observation.market = obs0.market
        state[i].observation.town = obs0.town
        state[i].observation.day = obs0.day
        state[i].observation.hour = obs0.hour

    # `step` here is the previous step counter; framework records the post-interpreter
    # state at the next index. -2 fires DONE on the final recorded step.
    if step >= cfg.episodeSteps - 2:
        for s in state:
            s.status = "DONE"
            s.reward = float(obs0.farms[s.observation.player]["money"])

    return state

def _initialize(state, env):
    raise ValueError("An initialized observation is required")
'''
_mod = _types.ModuleType(_PACKAGE.__name__ + ".native_core")
_mod.__package__ = _PACKAGE.__name__
_sys.modules[_mod.__name__] = _mod
setattr(_PACKAGE, "native_core", _mod)
exec(compile(_SOURCE_NATIVE_CORE, "<general_v3/native_core.py>", "exec"), _mod.__dict__)

# BEGIN SOURCE beliefs.py
_SOURCE_BELIEFS = '''"""Bounded, observation-only rival supply and hypothetical future demand models.

No hidden state, episode identity, native seed, recorded action, or rank is read.
A SupplyBelief belongs to ONE policy instance/episode. Its summaries are evidence
plus explicitly labelled hypotheses, never a reconstruction of private state.
"""
from __future__ import annotations

import copy
import math

from . import native_core as core


RULE_DEFAULTS = dict(episodeSteps=720, boardSize=10, turnsPerDay=24,
                     shedCapacity=100, maxMarketOrdersPerTurn=10,
                     townShopSellInterval=4, townCenterSellInterval=24,
                     townShopUnlockInterval=3)
# These are named stress mixtures, not calibrated probabilities or RNG predictions.
# The legacy low/high aliases describe demand for premium animal products only.
REGIMES = {
    'low_demand': dict(shop_weights={'PET_CAFE': 3, 'FARMERS_MARKET': 3, 'BAKERY': 2}, service=1.0, care=1.0),
    'central': dict(shop_weights={name: 1 for name in core.SHOPS}, service=0.8, care=0.65),
    'high_demand': dict(shop_weights={'YARN_STORE': 3, 'ICE_CREAM_SHOP': 3, 'SMOOTHIE_SHOP': 2}, service=0.55, care=0.35),
}
REGIME_ALIASES = {'field': 'low_demand', 'mixed': 'central', 'premium': 'high_demand',
                  'balanced': 'central'}


def _cfg(configuration=None):
    supplied = configuration or {}
    return {k: max(1, int(supplied.get(k, v))) for k, v in RULE_DEFAULTS.items()}


def _zeros():
    return {p: 0.0 for p in core.PRODUCTS}


def _count(value):
    try:
        number = float(value)
        return max(0.0, number) if math.isfinite(number) else 0.0
    except (ValueError, TypeError):
        return 0.0


def _positions(farm):
    return [farm.get('farmer', [0, 0]), *farm.get('hands', [])]


def _tiles(farm):
    return [(x, y, tile) for y, row in enumerate(farm['tiles'])
            for x, tile in enumerate(row) if isinstance(tile, dict)]


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _public_features(farm, step, cfg):
    day = step // cfg['turnsPerDay']
    positions = _positions(farm)
    access = core._shed_access_tiles(len(farm['tiles']))
    held, throughput = _zeros(), _zeros()
    sources, work = {}, 0.0
    animals = 0
    for x, y, tile in _tiles(farm):
        p = None
        if tile.get('crop') in core.CROPS:
            p = tile['crop']; data = core.CROPS[p]
            age = day - int(tile.get('planted_day', day))
            held[p] += _count(tile.get('yield_units', 0)) if age >= data['first_yield_day'] else 0
            lifetime = (data['first_yield_day'] + (data['max_yield'] - 1) * data['interval']
                        if data['ongoing'] else data['max_yield_day'])
            throughput[p] += data['max_yield'] / max(1, lifetime + 1)
            work += 2.0
        elif tile.get('animal') in core.ANIMALS:
            data = core.ANIMALS[tile['animal']]; p = data['product']
            held[p] += _count(tile.get('yield_units', 0))
            throughput[p] += (1 + data['interval']) / data['interval']
            throughput['FERTILIZER'] += 1
            animals += 1; work += 5.5
        if p:
            sources[(x, y)] = p
    worker_capacity = len(positions) * cfg['turnsPerDay'] * 0.7
    service = min(1.0, worker_capacity / max(1.0, work))
    nearby = sum(min((_distance(pos, target) for target in sources), default=999) <= 1
                 for pos in positions)
    # Positions affect delivery readiness, never provide proof of carried stock.
    near_shed = sum(tuple(pos) in access for pos in positions)
    return dict(held=held, throughput=throughput, animals=animals, service=service,
                near_sources=nearby, near_shed=near_shed, sources=sources,
                workers=len(positions))


def _town_consumption(observation, cfg):
    step = int(observation['step'])
    result = _zeros()
    if step % cfg['townShopSellInterval'] == 0:
        for shop in observation['town'].get('unlocked_shops', []):
            products = core.SHOPS.get(shop, ())
            for p in products:
                result[p] += 2 if len(products) == 1 else 1
    if step % cfg['townCenterSellInterval'] == 0:
        for p in core.TOWN_CENTER_PRODUCTS:
            result[p] += 1
    return result


def _own_worker_projection(previous, action, cfg):
    farm = copy.deepcopy(previous['farms'][int(previous['player'])])
    private = copy.deepcopy(previous['private'])
    units = [action.get('farmer', ['PASS']), *action.get('hands', [])]
    demand = {}
    for command in units:
        if isinstance(command, list) and len(command) >= 2 and command[0] == 'PLANT':
            demand[command[1]] = demand.get(command[1], 0) + 1
    blocked = {p for p, n in demand.items() if n > private.get('seeds', {}).get(p, 0)}
    for i, command in enumerate(units):
        if isinstance(command, list) and len(command) >= 2 and command[0] == 'PLANT' and command[1] in blocked:
            command = ['PASS']
        core._apply_unit_action(farm, private, i, command, len(farm['tiles']),
                                int(previous['step']) // cfg['turnsPerDay'],
                                cfg['turnsPerDay'], cfg['shedCapacity'])
    return private


def _total(private, product):
    return _count(private.get('shed', {}).get(product, 0)) + sum(
        _count(inv.get(product, 0)) for inv in private.get('inventories', []))


def _own_market_intervals(previous, current, cfg, action, consumption):
    """Contribution to public inventory, including unknown $1-floor attribution."""
    capacity = cfg['shedCapacity']; orders = cfg['maxMarketOrdersPerTurn']
    maximum = float(capacity * orders)
    if action is None:
        return {p: (-maximum, maximum) if p in ('WHEAT', 'FERTILIZER') else (0., maximum)
                for p in core.PRODUCTS}, False
    sold, bought = _zeros(), _zeros()
    for order in action.get('market', [])[:orders]:
        if not isinstance(order, list) or len(order) < 3 or order[1] not in sold:
            continue
        quantity = min(capacity, _count(order[2]))
        if order[0] == 'SELL':
            sold[order[1]] += quantity
        elif order[0] == 'BUY_PRODUCT' and order[1] in ('WHEAT', 'FERTILIZER'):
            bought[order[1]] += quantity
    before = _own_worker_projection(previous, action, cfg)
    boundary = (int(previous['step']) + 1) % cfg['turnsPerDay'] == 0
    params = core._resolve_market_params(previous['market'].get('params'))
    result = {}
    censored = False
    for p in core.PRODUCTS:
        delta = _total(before, p) - _total(current['private'], p)
        discarded = (sum(_count(inv.get(p, 0)) for inv in before.get('inventories', []))
                     if boundary else 0.0)
        # Non-shed product change is native-known worker action or midnight loss.
        lo = max(-bought[p], delta - discarded)
        hi = min(sold[p], delta)
        if lo > hi + 1e-8:
            # Invalid/out-of-order snapshots: preserve only action quantity limits.
            lo, hi = -bought[p], sold[p]
        start = float(previous['market']['inventory'][p])
        end = float(current['market']['inventory'][p]) + consumption[p]
        # Non-purchasable products are monotone within the market phase.
        # Purchasable products may first peak and then fall, so include all buys.
        peak_bound = max(start, end) + (maximum + bought[p] if p in ('WHEAT', 'FERTILIZER') else 0)
        floor_possible = core.market_price(p, peak_bound, params) <= core.PRICE_FLOOR
        if floor_possible and sold[p] > 0:
            lo = max(-bought[p], lo - sold[p])
            censored = True
        result[p] = (float(lo), float(hi))
    return result, censored


def _harvest_evidence(previous, current, cfg):
    seat = 1 - int(previous['player']); before = previous['farms'][seat]
    after = current['farms'][seat]
    positions = [tuple(p) for p in _positions(before)]
    possible = _zeros(); certain = _zeros(); by_worker = {}
    step = int(previous['step']); day = step // cfg['turnsPerDay']
    boundary = (step + 1) % cfg['turnsPerDay'] == 0
    for x, y, tile in _tiles(before):
        if (x, y) not in positions or _count(tile.get('yield_units', 0)) <= 0:
            continue
        now = after['tiles'][y][x]
        if tile.get('crop') in core.CROPS:
            p = tile['crop']; rule = core.CROPS[p]
            if day - int(tile.get('planted_day', day)) < rule['first_yield_day']:
                continue
            decay = int(tile.get('max_lifespan_step', -1))
            decay = 1 if decay >= 0 and step >= decay and (step - decay) % 2 == 0 else 0
            remaining = _count(now.get('yield_units', 0)) if isinstance(now, dict) else 0
            if remaining >= _count(tile['yield_units']) - decay and isinstance(now, dict) and now.get('crop') == p:
                continue
        elif tile.get('animal') in core.ANIMALS:
            p = core.ANIMALS[tile['animal']]['product']
            if not isinstance(now, dict) or now.get('animal') != tile['animal'] or now.get('placed_day') != tile.get('placed_day'):
                continue
            if _count(now.get('yield_units', 0)) >= _count(tile['yield_units']):
                continue
            if not boundary:
                certain[p] += _count(tile['yield_units'])
        else:
            continue
        quantity = _count(tile['yield_units'])
        possible[p] += quantity
        indexes = [i for i, pos in enumerate(positions) if pos == (x, y)]
        if len(indexes) == 1 and not boundary:
            by_worker[indexes[0]] = {p: quantity * (1.0 if p not in core.CROPS else 0.5)}
    return dict(possible=possible, certain=certain, by_worker=by_worker)


class SupplyBelief:
    """Episode-local finite evidence window; caller owns and resets this object.

    observe() accepts only public farms/market/town, own private state and own
    previous action. Call remember_action() after choosing the ACTUAL action.
    Search branches must never update this object. Non-adjacent/repeated steps,
    changed seat or rules discard history. Explicit reset covers host-side game
    switches that are otherwise observationally indistinguishable.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self._last = None
        self._action = None
        self._signature = None
        self._events = []

    def remember_action(self, action):
        self._action = {k: copy.deepcopy(action.get(k, [] if k != 'farmer' else ['PASS']))
                        for k in ('farmer', 'hands', 'market')}

    def observe(self, observation, configuration=None, previous_action=None):
        cfg = _cfg(configuration)
        # Explicit allowed fields prevent metadata from changing beliefs or resets.
        current = {k: copy.deepcopy(observation[k]) for k in ('farms', 'private', 'market', 'town', 'step', 'player')}
        step = int(current['step']); seat = int(current['player'])
        params = core._resolve_market_params(current['market'].get('params'))
        signature = (seat, tuple(sorted(cfg.items())),
                     int((configuration or {}).get('farmHandCostMult', 1)),
                     float((configuration or {}).get('weedSpawnChance', 0.005)),
                     repr(sorted((p, sorted(params[p].items())) for p in core.PRODUCTS)))
        adjacent = (self._last is not None and step == int(self._last['step']) + 1
                    and signature == self._signature and step > 0)
        if not adjacent:
            self._events = []
            self._action = None
        latest = None
        if adjacent:
            action = previous_action if previous_action is not None else self._action
            consumption = _town_consumption(self._last, cfg)
            own, floor = _own_market_intervals(self._last, current, cfg, action, consumption)
            intervals = {}
            cap = cfg['shedCapacity'] * cfg['maxMarketOrdersPerTurn']
            for p in core.PRODUCTS:
                joint = float(current['market']['inventory'][p]) - float(self._last['market']['inventory'][p]) + consumption[p]
                lo, hi = joint - own[p][1], joint - own[p][0]
                minimum = -cap if p in ('WHEAT', 'FERTILIZER') else 0
                lo, hi = max(minimum, lo), min(cap, hi)
                if lo > hi:
                    lo, hi = float(minimum), float(cap)
                intervals[p] = [float(lo), float(hi)]
            latest = dict(step=step, market_net=intervals, own_market=own,
                          town_consumption=consumption, own_floor_censored=floor,
                          harvest=_harvest_evidence(self._last, current, cfg))
            self._events.append(latest)
            self._events = self._events[-min(256, max(1, cfg['turnsPerDay'] * 2)):]
        features = _public_features(current['farms'][1-seat], step, cfg)
        rates = _zeros(); rates_low = _zeros(); rates_high = _zeros()
        n = len(self._events)
        for event in self._events:
            for p, (lo, hi) in event['market_net'].items():
                rates_low[p] += max(0.0, lo)
                rates_high[p] += max(0.0, hi)
        for p in rates:
            factor = cfg['turnsPerDay'] / max(1, n)
            rates_low[p] *= factor; rates_high[p] *= factor
            # Wide ambiguous residuals are not evidence for a giant hidden farm.
            rates[p] = rates_low[p]
        carry_bound = (step + 1) * max(cfg['shedCapacity'], max(d['max_held'] for d in core.ANIMALS.values()),
                                       max(d['max_yield'] for d in core.CROPS.values()))
        summary = dict(step=step, player=seat, adjacent=adjacent, observed_transitions=n,
                       shed_bounds={p: [0, cfg['shedCapacity']] for p in core.PRODUCTS + list(core.ANIMALS)},
                       shed_total_bound=[0, cfg['shedCapacity']],
                       carried_total_per_worker_bound=[0, carry_bound],
                       workers=features['workers'], near_sources=features['near_sources'],
                       near_shed=features['near_shed'], service=features['service'],
                       public_held=features['held'], visible_daily_throughput=features['throughput'],
                       sale_rate=rates, sale_rate_interval={p: [rates_low[p], rates_high[p]] for p in rates},
                       latest=copy.deepcopy(latest),
                       warning='Bounds are feasible envelopes, not calibrated probabilities. Market net excludes censored floor sales; buys can mask sales.')
        self._last = current; self._signature = signature; self._action = None
        return summary


def estimate_private(public_farm, configuration=None, scale=1.0, summary=None):
    """One feasible hidden-stock hypothesis, NOT a hard-state estimate.

    Shed quantity obeys a shared capacity. Worker inventories are separate and
    only assigned small public-source/carry hypotheses. No own inventory is read.
    """
    cfg = _cfg(configuration)
    step = int((summary or {}).get('step', (configuration or {}).get('currentStep', 0)))
    features = _public_features(public_farm, step, cfg)
    scale = max(0., min(3., float(scale)))
    private = core._new_private()
    private['inventories'] = [{} for _ in _positions(public_farm)]
    weights = _zeros()
    history = (summary or {}).get('sale_rate', {})
    for p in weights:
        # A half-day backlog of serviceable public production. Observed disposal
        # reduces hypothesized backlog rather than creating private inventory.
        baseline = features['throughput'][p] * features['service'] * 0.5
        sold = min(baseline, _count(history.get(p, 0)) * 0.25)
        weights[p] = max(0., baseline - sold) + 0.2 * features['held'][p]
    weights['WHEAT'] += features['animals'] * 0.5
    quantities = {p: int(math.ceil(scale * weight)) for p, weight in weights.items() if weight > 0}
    total = sum(quantities.values()); capacity = cfg['shedCapacity']
    if total > capacity:
        raw = {p: q * capacity / total for p, q in quantities.items()}
        quantities = {p: int(q) for p, q in raw.items()}
        for p in sorted(raw, key=lambda p: (-(raw[p] - quantities[p]), p))[:capacity - sum(quantities.values())]:
            quantities[p] += 1
    private['shed'].update(quantities)
    if scale:
        observed = ((summary or {}).get('latest') or {}).get('harvest', {}).get('by_worker', {})
        for index, pos in enumerate(_positions(public_farm)):
            # Publicly located farm work is ambiguous. Treat unobserved wheat
            # custody as a hypothesis only, small enough to avoid free resources.
            p = features['sources'].get(tuple(pos))
            carry = observed.get(index, observed.get(str(index), {}))
            if carry:
                private['inventories'][index] = {item: min(6, int(math.ceil(n * min(1., scale))))
                                                 for item, n in carry.items() if item in core.PRODUCTS}
            elif p and features['animals'] and p in ('EGG', 'MILK', 'WOOL') and scale >= 1:
                private['inventories'][index] = {'WHEAT': 1}
        for crop in core.CROPS:
            private['seeds'][crop] = min(2, int(scale)) if features['throughput'][crop] else 0
    return private


def _events_between(start, stop, interval):
    """Multiples in [start, stop), matching native consumption-before-midnight."""
    if stop <= start:
        return 0
    return (stop - 1) // interval - (start - 1) // interval


def _farm_supply_path(farm, step, days, cfg, service, care):
    """Finite public-asset output under explicit ideal service, no free renewal."""
    path = [_zeros() for _ in range(days + 1)]
    day = step // cfg['turnsPerDay']
    feature = _public_features(farm, step, cfg)
    factor = service * feature['service']
    positions = _positions(farm)
    for x, y, tile in _tiles(farm):
        near = min((_distance(pos, (x, y)) for pos in positions), default=999)
        access = min(_distance((x, y), s) for s in core._shed_access_tiles(len(farm['tiles'])))
        delivery_days = max(1, int(math.ceil((near + 1 + access + 1) / cfg['turnsPerDay'])))
        if tile.get('crop') in core.CROPS:
            p = tile['crop']; rule = core.CROPS[p]
            age = day - int(tile.get('planted_day', day))
            held = _count(tile.get('yield_units', 0))
            if rule['ongoing']:
                if held and delivery_days <= days:
                    path[delivery_days][p] += held * factor
                for count in range(rule['max_yield']):
                    delay = rule['first_yield_day'] + count * rule['interval'] - age
                    if 1 <= delay <= days and delivery_days <= days:
                        path[max(delay, delivery_days)][p] += factor
            else:
                delay = max(delivery_days, rule['max_yield_day'] - age)
                decay_start = int(tile.get('max_lifespan_step', -1))
                if 1 <= delay <= days and not (decay_start >= 0 and step >= decay_start + 2 * max(1, held)):
                    window = (rule['max_yield_day'] + 1) // 2
                    gains = max(0, rule['max_yield_day'] - max(age, window - 1))
                    path[delay][p] += min(rule['max_yield'], held + gains) * factor
        elif tile.get('animal') in core.ANIMALS:
            rule = core.ANIMALS[tile['animal']]; p = rule['product']
            age = day - int(tile.get('placed_day', day))
            held = _count(tile.get('yield_units', 0))
            if held and delivery_days <= days:
                path[delivery_days][p] += held * factor
            pending_care = _count(tile.get('pending_care_bonus', 0))
            for delay in range(1, days + 1):
                future_age = age + delay
                if delivery_days <= days and future_age >= rule['first_yield_day'] and (future_age - rule['first_yield_day']) % rule['interval'] == 0:
                    # Existing public care is known; future care is hypothetical.
                    # Native consumes pending care before adding today's care.
                    path[max(delay, delivery_days)][p] += min(rule['max_held'], 1 + pending_care) * factor
                    pending_care = 0.0
                pending_care += care
                path[delay]['FERTILIZER'] += factor * 0.7
                # Feed procurement is market demand, represented as negative supply.
                path[delay]['WHEAT'] -= factor
    return path


def _market_addition(product, stock, desired, params):
    """Apply the native $1 censor to approximate daily inventory additions.

    Fractional demand/production paths remain approximate, but never fabricate
    accumulating $1-floor supply. A final indivisible sale may cross the floor.
    """
    if desired <= 0:
        return desired
    if core.market_price(product, stock, params) <= core.PRICE_FLOOR:
        return 0.0
    if core.market_price(product, stock + desired, params) > core.PRICE_FLOOR:
        return desired
    low, high = 0.0, desired
    for _ in range(30):
        mid = (low + high) / 2
        if core.market_price(product, stock + mid, params) > core.PRICE_FLOOR:
            low = mid
        else:
            high = mid
    return min(desired, math.floor(low) + 1.0)


def future_market(observation, configuration=None, horizon_days=8, regime='central', summary=None, exclude_player=None):
    """Daily hypothetical stock/price paths including not-yet-revealed shops.

    Central uses the correct uniform marginal recipe distribution, NOT expected
    price over all native trajectories. Stress mixtures are declared assumptions.
    Revealed shops, duplicates, cadence, unlock cap and remaining game are exact.
    The horizon is days, independent of short native action rollout depth.
    """
    cfg = _cfg(configuration)
    regime = REGIME_ALIASES.get(regime, regime)
    if regime not in REGIMES:
        raise ValueError('Unknown future-demand regime: ' + str(regime))
    model = REGIMES[regime]
    step = int(observation['step']); tpd = cfg['turnsPerDay']
    last = cfg['episodeSteps'] - 1
    days = max(0, min(64, int(horizon_days), int(math.ceil(max(0, last - step) / tpd))))
    params = core._resolve_market_params(observation['market'].get('params'))
    stocks = {p: float(observation['market']['inventory'][p]) for p in core.PRODUCTS}
    rows = [dict(prices={p: float(core.market_price(p, stocks[p], params)) for p in core.PRODUCTS},
                 inventory=dict(stocks), demand=_zeros(), supply=_zeros())]
    weights = model['shop_weights']; weight_sum = sum(weights.values())
    new_recipe = _zeros()
    for name, weight in weights.items():
        recipe = core.SHOPS[name]
        for p in recipe:
            new_recipe[p] += weight / weight_sum * (2 if len(recipe) == 1 else 1)
    shops = list(observation['town'].get('unlocked_shops', []))
    recipe = _zeros()
    for name in shops:
        products = core.SHOPS.get(name, ())
        for p in products:
            recipe[p] += 2 if len(products) == 1 else 1
    # Forecast supply from existing assets only. No assumed future purchases,
    # replants, population growth, or invisible rival action programme.
    paths = []
    for player, farm in enumerate(observation['farms']):
        if player != exclude_player:
            paths.append((player, _farm_supply_path(farm, step, days, cfg, model['service'], model['care'])))
    unlock_every = cfg['townShopUnlockInterval'] * tpd
    first_unlock = (step // unlock_every + 1) * unlock_every
    unlocks = list(range(first_unlock, last, unlock_every))[:max(0, core.MAX_SHOP_INSTANCES - len(shops))]
    for delay in range(1, days + 1):
        start, stop = step + (delay - 1) * tpd, min(last, step + delay * tpd)
        demand = _zeros(); supply = _zeros()
        current_ticks = _events_between(start, stop, cfg['townShopSellInterval'])
        center_ticks = _events_between(start, stop, cfg['townCenterSellInterval'])
        future_ticks = sum(_events_between(max(start, unlock), stop, cfg['townShopSellInterval'])
                           for unlock in unlocks if unlock < stop)
        for p in core.PRODUCTS:
            demand[p] = current_ticks * recipe[p] + future_ticks * new_recipe[p]
            if p in core.TOWN_CENTER_PRODUCTS:
                demand[p] += center_ticks
        for player, path in paths:
            for p in supply:
                projected = path[delay][p]
                if summary and player == 1 - int(summary.get('player', observation['player'])) and p != 'WHEAT':
                    # Recent certain disposal supports a finite decaying supply
                    # alternative; use max rather than double-count visible output.
                    recent = min(cfg['shedCapacity'] * 2, _count(summary.get('sale_rate', {}).get(p, 0)))
                    projected = max(projected, recent * math.exp(-delay / 3.0) * model['service'])
                supply[p] += projected
        for p in stocks:
            supply[p] = _market_addition(p, stocks[p], supply[p], params)
            stocks[p] += supply[p] - demand[p]
        rows.append(dict(prices={p: float(core.market_price(p, stocks[p], params)) for p in core.PRODUCTS},
                         inventory=dict(stocks), demand=demand, supply=supply))
    return rows


def future_prices(observation, configuration=None, horizon_days=8, regime='central', summary=None, exclude_player=None):
    """Price-dict view of future_market; index zero is current market."""
    return [row['prices'] for row in future_market(observation, configuration, horizon_days,
                                                  regime, summary, exclude_player)]
'''
_mod = _types.ModuleType(_PACKAGE.__name__ + ".beliefs")
_mod.__package__ = _PACKAGE.__name__
_sys.modules[_mod.__name__] = _mod
setattr(_PACKAGE, "beliefs", _mod)
exec(compile(_SOURCE_BELIEFS, "<general_v3/beliefs.py>", "exec"), _mod.__dict__)

# BEGIN SOURCE commitments.py
_SOURCE_COMMITMENTS = '''"""Auditable, observation-only lifecycle commitments and marginal production books.

This is a cash-flow approximation, not a hidden-information simulator. Native
crop/animal refresh determines production; movement, prices and rival service
are declared estimates. Existing assets own their future obligations exactly
once. New purchases are compared with that entire book, including cash timing,
marginal daily Fibonacci wages, land, physical supply and shared-market impact.
"""
import copy
import math
from collections import OrderedDict
from . import native_core as core


def _get(obj, key, default=None):
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def _context(obs, cfg):
    tpd = max(1, int(_get(cfg, 'turnsPerDay', 24)))
    step = int(_get(obs, 'step', 0))
    end = max(1, int(_get(cfg, 'episodeSteps', 720))) - 2
    seat = int(_get(obs, 'player', 0))
    return obs['farms'][seat], obs.get('private', {}), tpd, step, end


def _distance(a, b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])


def _row():
    return dict(sales={}, feed=0, seed_cost=0., animal_cost=0., land_cost=0.,
                service=0., travel=0., delivery=0.)


def _flow(item, units, row):
    if units > 0:
        row['sales'][item] = row['sales'].get(item, 0)+units


def _merge(target, source):
    for dest, row in zip(target, source):
        for item, qty in row['sales'].items():
            _flow(item, qty, dest)
        for key in ('feed', 'seed_cost', 'animal_cost', 'land_cost', 'service', 'travel', 'delivery'):
            dest[key] += row[key]
    return target


def _lifecycle_uncached(item, day, last_day, tpd=24, tile=None, target=(0, 0),
                        shed_distance=0, owned=False, repeat=False, final_delivery=True):
    """Daily production ledger with native refresh order and finite crop lifetime.

    Sales normally occur the day after harvest because midnight deposits cargo
    automatically. Final-day output requires explicit harvest and shed delivery.
    `repeat` is an explicit replant programme, with every replacement seed paid.
    Already-held yield and pending animal care are preserved; sunk costs are not
    charged again. No fertilizer is invented for crops.
    """
    count = max(0, last_day-day+1)
    rows = [_row() for _ in range(count)]
    if not count:
        return rows
    is_crop = item in core.CROPS
    state = copy.deepcopy(tile) if tile is not None else (
        core._new_plant(item, day, tpd) if is_crop else core._new_animal(item, day))
    simulated = {'tiles': [[state]], 'farmer': [0, 0], 'hands': []}
    private = {'seeds': {}, 'shed': {}, 'inventories': [{}]}
    if tile is None:
        rows[0]['service'] += 1 if is_crop else 3  # plant, or pickup/build/place
        if not owned:
            rows[0]['seed_cost' if is_crop else 'animal_cost'] += (
                core.CROPS[item]['seed'] if is_crop else core.ANIMALS[item]['cost'])
    # An efficient tile tour shares travel with neighbouring assets. This charge
    # is explicit and deliberately never represented as an exact worker route.
    ingress = min(float(shed_distance), 2.0)
    for offset, current in enumerate(range(day, last_day+1)):
        row = rows[offset]
        state = simulated['tiles'][0][0]
        if not isinstance(state, dict) or ('crop' not in state and 'animal' not in state):
            if not (is_crop and repeat and last_day-current >= core.CROPS[item]['first_yield_day']):
                break
            state = core._new_plant(item, current, tpd)
            simulated['tiles'][0][0] = state
            row['seed_cost'] += core.CROPS[item]['seed']
            row['service'] += 1
        final = current == last_day
        active = False
        if is_crop:
            data = core.CROPS[item]
            age = current-state['planted_day']
            exhausted = data['ongoing'] and age > data['first_yield_day']+(data['max_yield']-1)*data['interval']
            if exhausted and not state.get('yield_units', 0):
                if repeat:
                    simulated['tiles'][0][0] = None
                    row['service'] += 1
                    continue
                break
            window = (data['max_yield_day']+1)//2 <= age <= data['max_yield_day']
            if not state.get('watered_today', False) and (not final or (not data['ongoing'] and window)):
                core._apply_unit_action(simulated, private, 0, ['WATER'], 1, current, tpd)
                row['service'] += 1
                active = True
            mature = age >= data['first_yield_day']
            harvest = mature and state.get('yield_units', 0) > 0 and (
                data['ongoing'] or age >= data['max_yield_day'] or final)
        else:
            data = core.ANIMALS[item]
            if not final:
                if not state.get('fed_today', False):
                    private['inventories'][0]['WHEAT'] = 1
                    core._apply_unit_action(simulated, private, 0, ['FEED'], 1, current, tpd)
                    row['feed'] += 1
                    row['service'] += 1.25  # amortized physical feed pickup
                    active = True
                if not state.get('cared_today', False):
                    core._apply_unit_action(simulated, private, 0, ['CARE'], 1, current, tpd)
                    row['service'] += 1
                    active = True
            harvest = state.get('yield_units', 0) > 0
            if state.get('fertilizer_available', False):
                core._apply_unit_action(simulated, private, 0, ['COLLECT_FERTILIZER'], 1, current, tpd)
                row['service'] += 1
                active = True
        if harvest:
            core._apply_unit_action(simulated, private, 0, ['HARVEST'], 1, current, tpd)
            row['service'] += 1
            active = True
        cargo = private['inventories'][0]
        if cargo:
            sale_offset = min(offset+1, count-1)
            can_sell = not final or final_delivery
            if can_sell:
                for product, units in cargo.items():
                    if product in core.PRODUCTS:
                        _flow(product, units, rows[sale_offset])
                if final:
                    row['delivery'] += shed_distance+1
            cargo.clear()
        if active:
            row['travel'] += ingress
        if not final:
            core._daily_refresh_plants(simulated, current, tpd)
            core._daily_refresh_animals(simulated, current)
    return rows



_LIFECYCLE_CACHE = OrderedDict()
_LIFECYCLE_CACHE_LIMIT = 512
_LIFECYCLE_HITS = 0
_LIFECYCLE_MISSES = 0
_LIFECYCLE_RULE_SNAPSHOT = None
_LIFECYCLE_RULE_KEY = None


def _frozen(value):
    """Preserve complete nested rule/observation content and container types."""
    if isinstance(value, dict):
        return ('dict', tuple((key, _frozen(item)) for key,item in value.items()))
    if isinstance(value, list):
        return ('list', tuple(_frozen(item) for item in value))
    if isinstance(value, tuple):
        return ('tuple', tuple(_frozen(item) for item in value))
    return (type(value).__name__, value)


def clear_caches():
    """Discard pure memoized lifecycle work at an episode boundary."""
    global _LIFECYCLE_HITS, _LIFECYCLE_MISSES, _LIFECYCLE_RULE_SNAPSHOT, _LIFECYCLE_RULE_KEY
    _LIFECYCLE_RULE_SNAPSHOT = _LIFECYCLE_RULE_KEY = None
    _LIFECYCLE_CACHE.clear()
    _LIFECYCLE_HITS = _LIFECYCLE_MISSES = 0


def cache_info():
    return dict(hits=_LIFECYCLE_HITS, misses=_LIFECYCLE_MISSES,
                size=len(_LIFECYCLE_CACHE), maxsize=_LIFECYCLE_CACHE_LIMIT)



def _native_rules_key():
    """C-level deep equality checks all rules; fingerprint only on real change."""
    global _LIFECYCLE_RULE_SNAPSHOT, _LIFECYCLE_RULE_KEY
    rules=(core.CROPS,core.ANIMALS,core.PRODUCTS,core.FARMER_MOVES)
    if _LIFECYCLE_RULE_SNAPSHOT is None or rules != _LIFECYCLE_RULE_SNAPSHOT:
        _LIFECYCLE_RULE_SNAPSHOT=copy.deepcopy(rules)
        # A shared immutable string caches its own hash; it contains the full
        # typed representation, not an abbreviated rule-version identifier.
        _LIFECYCLE_RULE_KEY=repr(_frozen(_LIFECYCLE_RULE_SNAPSHOT))
    return _LIFECYCLE_RULE_KEY

def lifecycle(item, day, last_day, tpd=24, tile=None, target=(0, 0),
              shed_distance=0, owned=False, repeat=False, final_delivery=True,
              use_cache=True):
    """Pure lifecycle memo; every returned row and sales map is caller-owned.

    The full native tile, every argument and all consulted mutable native rule
    tables are part of the key. No market, opponent identity or episode seed is
    stored. Disabling the cache changes work reuse only, never economics.
    """
    global _LIFECYCLE_HITS, _LIFECYCLE_MISSES
    if not use_cache:
        return _lifecycle_uncached(item,day,last_day,tpd,tile,target,shed_distance,
                                   owned,repeat,final_delivery)
    rules = _native_rules_key()
    key = (item,day,last_day,tpd,_frozen(tile),_frozen(target),shed_distance,
           owned,repeat,final_delivery,rules)
    cached = _LIFECYCLE_CACHE.get(key)
    if cached is None:
        _LIFECYCLE_MISSES += 1
        cached = _lifecycle_uncached(item,day,last_day,tpd,tile,target,shed_distance,
                                     owned,repeat,final_delivery)
        _LIFECYCLE_CACHE[key] = cached
        if len(_LIFECYCLE_CACHE) > _LIFECYCLE_CACHE_LIMIT:
            _LIFECYCLE_CACHE.popitem(last=False)
    else:
        _LIFECYCLE_HITS += 1
        _LIFECYCLE_CACHE.move_to_end(key)
    return [dict(row, sales=dict(row['sales'])) for row in cached]

def hire_bill(actions, turns, mult=1, existing_workers=1, already_hired=0):
    """Exact native Fibonacci wage staircase for a declared usable action budget."""
    if turns <= 0:
        return 0., 0
    usable = max(1., float(turns)*0.82)
    needed = max(1, int(math.ceil(max(0., actions)/usable)))
    extra = max(0, needed-max(1, existing_workers))
    # Very large malformed observations must not make an unbounded Fibonacci sum.
    extra = min(32, extra)
    return float(sum(core._hire_cost(already_hired+i, mult) for i in range(extra))), extra


def _market_frames(obs, cfg, days, prices, regime, summary=None):
    try:
        from . import beliefs
        frames = beliefs.future_market(obs, cfg, days, regime=regime,
                                       exclude_player=int(obs.get('player', 0)), summary=summary)
    except ImportError:
        # Supports standalone module contracts before the optional beliefs layer
        # is installed. There is no swallowed runtime error from that model.
        market = obs.get('market', {})
        params = core._resolve_market_params(market.get('params'))
        frames = [dict(prices={p: market.get('prices', {}).get(p, params[p]['base']) for p in core.PRODUCTS},
                       inventory={p: market.get('inventory', {}).get(p, params[p]['I0']) for p in core.PRODUCTS},
                       supply={}, demand={}) for _ in range(days+1)]
    if prices is not None:
        quote_rows = prices if isinstance(prices, (list, tuple)) else [prices]*(days+1)
        frames = [dict(frame, prices=dict(quote_rows[min(i, len(quote_rows)-1)]), external_prices=True)
                  for i, frame in enumerate(frames)]
    return frames


def _quotes(item, stock, quantity, params, buy=False):
    """Exact self-impact quotes, including the native $1 sale-stock exception."""
    total = 0.
    for _ in range(max(0, int(quantity))):
        quote = core.market_price(item, stock-1 if buy else stock, params)
        total += quote
        if buy:
            stock -= 1
        elif quote > 1:
            stock += 1
    return total, stock


def _value(rows, frames, obs, cfg, feed_owned=0):
    farm, private, tpd, step, end = _context(obs, cfg)
    params = core._resolve_market_params(obs.get('market', {}).get('params'))
    stock_shift = {p: 0. for p in core.PRODUCTS}
    cumulative = 0.
    minimum = 0.
    total_sales = total_cost = rival_effect = 0.
    audit = []
    for offset, source in enumerate(rows):
        row = dict(source, sales=dict(source['sales']))
        frame = frames[min(offset, len(frames)-1)]
        receipts = 0.
        feed_units = max(0, int(row['feed']))
        credit = min(feed_owned, feed_units)
        feed_owned -= credit
        feed_units -= credit
        base = float(frame['inventory'].get('WHEAT', params['WHEAT']['I0']))
        before = base+stock_shift['WHEAT']
        feed_cost, after = _quotes('WHEAT', before, feed_units, params, buy=True)
        if frame.get('external_prices'):
            feed_cost = feed_units*frame['prices'].get('WHEAT', params['WHEAT']['base'])
        stock_shift['WHEAT'] += after-before
        for item, qty in row['sales'].items():
            base = float(frame['inventory'].get(item, params[item]['I0']))
            before = base+stock_shift[item]
            revenue, after = _quotes(item, before, qty, params)
            if frame.get('external_prices'):
                # Preserve marginal self-impact around the caller's scenario quote.
                native_quote = core.market_price(item, base, params)
                revenue += qty*(frame['prices'].get(item, native_quote)-native_quote)
                revenue = max(float(qty), revenue)
            stock_shift[item] += after-before
            receipts += revenue
        rival_delta = 0.
        for item in core.PRODUCTS:
            supply = float(frame.get('supply', {}).get(item, 0.))
            if supply and stock_shift[item]:
                base = float(frame['inventory'].get(item, params[item]['I0']))
                rival_delta += supply*(core.market_price(item, base+stock_shift[item], params)
                                       - core.market_price(item, base, params))
        turns = min(tpd-step%tpd-1, end-step) if offset == 0 else (end%tpd+1 if offset == len(rows)-1 else tpd-1)
        workers = 1+len(farm.get('hands', [])) if offset == 0 else 1
        hired = int(farm.get('hires_today', 0)) if offset == 0 else 0
        wage, extra = hire_bill(row['service']+row['travel']+row['delivery'], turns,
                               int(_get(cfg, 'farmHandCostMult', 1)), workers, hired)
        costs = feed_cost+wage+row['seed_cost']+row['animal_cost']+row['land_cost']
        # Outgoings must be available before same-day production is collected.
        minimum = min(minimum, cumulative-costs)
        cumulative += receipts-costs
        total_sales += receipts
        total_cost += costs
        rival_effect += rival_delta
        row.update(day=step//tpd+offset, receipts=receipts, feed_cost=feed_cost,
                   wages=wage, hires=extra, costs=costs, cash_flow=receipts-costs,
                   cumulative=cumulative, rival_cash_delta=rival_delta)
        audit.append(row)
    return dict(net=total_sales-total_cost, revenue=total_sales, costs=total_cost,
                rival_cash_delta=rival_effect, margin=total_sales-total_cost-rival_effect,
                required_cash=max(0., -minimum), daily=audit)



def liquidity_requirement(daily, opening_credit=0.):
    """Move known shed receipts before day-zero costs, never count them twice."""
    cumulative=0.;required=0.
    for offset,row in enumerate(daily):
        required=max(required,row['costs']-cumulative-(opening_credit if offset==0 else 0.))
        cumulative+=row['receipts']-row['costs']
    return max(0.,required)

def build_book(observation, configuration=None, style='balanced', prices=None,
               regime='central', include_candidates=True, summary=None):
    """Return baseline commitments and marginal funded candidate programmes.

    Fields are plain JSON. Each seed/unplaced animal is assigned once to one
    compatible owned slot before new purchases are considered. Unplaced assets
    beyond usable ground receive no fictitious salvage. Land candidates buy the
    whole next quadrant and fund a bounded work queue with its complete costs.
    """
    cfg = configuration or {}
    farm, private, tpd, step, end = _context(observation, cfg)
    day, last = step//tpd, end//tpd
    days = max(0, last-day)
    length = days+1
    if step > end:
        return dict(asset_value=0., baseline={'net': 0., 'margin': 0., 'required_cash': 0., 'daily': []},
                    candidates=[], owned=[], reserve=0., assumptions=[])
    access = core._shed_access_tiles(len(farm['tiles']))
    tiles = [(x,y,t) for y,row in enumerate(farm['tiles']) for x,t in enumerate(row) if t != 'LOCKED']
    distance = lambda p: min(_distance(p,a) for a in access)
    empty = sorted([(x,y,t) for x,y,t in tiles if t is None or (isinstance(t,dict) and 'animal' not in t and 'crop' not in t)],
                   key=lambda v:(distance(v[:2]),v[1],v[0]))
    rows = [_row() for _ in range(length)]
    def queued_lifecycle(item, target, ground=None, owned_asset=False, repeat=False, force_delay=0):
        crop=item in core.CROPS
        workers=[farm['farmer'],*farm.get('hands',[])]
        approach=min(_distance(p,target) for p in workers)
        actions=2 if crop else 4  # plant/water or pickup/build/place/feed
        if not crop and isinstance(ground,dict) and ground.get('kind')==core.ANIMALS[item]['structure']:
            actions-=1
        available=min(tpd-step%tpd,end-step+1)-(0 if owned_asset else 1)
        delay=max(force_delay,int(approach+actions>available))
        if delay>=length:
            return [_row() for _ in rows]
        result=[_row() for _ in range(delay)]+lifecycle(item,day+delay,last,tpd,target=target,
                        shed_distance=distance(target),owned=owned_asset,repeat=repeat)
        if delay and not owned_asset:
            key='seed_cost' if crop else 'animal_cost'
            first_cost=core.CROPS[item]['seed'] if crop else core.ANIMALS[item]['cost']
            result[delay][key]-=first_cost
            result[0][key]+=first_cost  # bought now, placed at earliest legal day
        return result
    owned = []
    positions = [farm['farmer'], *farm.get('hands', [])]
    for x,y,tile in tiles:
        if not isinstance(tile,dict):
            continue
        item = tile.get('crop',tile.get('animal'))
        if item not in core.CROPS and item not in core.ANIMALS:
            continue
        reachable = any(_distance(p,(x,y))+1+distance((x,y))+1 <= end-step+1 for p in positions)
        ledger = lifecycle(item,day,last,tpd,tile=tile,target=(x,y),shed_distance=distance((x,y)),
                           final_delivery=(day < last or reachable),repeat=item in core.CROPS)
        _merge(rows,ledger)
        owned.append(dict(kind='placed',item=item,target=[x,y]))
    reserved = set()
    stock_items = [(item,int(qty),'seed') for item,qty in private.get('seeds',{}).items() if item in core.CROPS]
    stock_items += [(item,int(private.get('shed',{}).get(item,0)+sum(i.get(item,0) for i in private.get('inventories',[]))),'animal') for item in core.ANIMALS]
    for item,quantity,kind in stock_items:
        for _ in range(min(quantity,len(empty))):
            home = next(((x,y,t) for x,y,t in empty if (x,y) not in reserved and
                         (kind=='seed' or t is None or t.get('kind') in ('WEED',core.ANIMALS[item]['structure']))),None)
            if home is None:
                break
            x,y,tile=home
            reserved.add((x,y))
            ledger=queued_lifecycle(item,(x,y),tile,owned_asset=True,repeat=item in core.CROPS)
            if tile is not None:
                ledger[next((i for i,r in enumerate(ledger) if r['service']),0)]['service'] += 1 if tile.get('kind')=='WEED' or kind=='seed' else -1
            _merge(rows,ledger)
            owned.append(dict(kind=kind,item=item,target=[x,y]))
    # Existing stock has one ownership path: reserved feed or sale, never both.
    feed_need=sum(row['feed'] for row in rows)
    wheat=int(private.get('shed',{}).get('WHEAT',0)+sum(i.get('WHEAT',0) for i in private.get('inventories',[])))
    feed_owned=min(wheat,int(feed_need))
    feed_remaining=feed_owned
    for item,n in private.get('shed',{}).items():
        if item not in core.PRODUCTS:
            continue
        qty=int(n)
        if item=='WHEAT':
            keep=min(feed_remaining,qty);qty-=keep;feed_remaining-=keep
        _flow(item,qty,rows[0])
    positions=[farm['farmer'],*farm.get('hands',[])]
    cap=max(0,int(_get(cfg,'shedCapacity',100))-sum(private.get('shed',{}).values()))
    for idx,inv in enumerate(private.get('inventories',[])):
        dist=distance(positions[idx]) if idx<len(positions) else 999
        midnight=step+(tpd-step%tpd)
        auto=midnight<=end
        deliver=dist+1<=end-step+1
        sale_day=1 if auto else 0
        goods=[]
        for item,n in inv.items():
            if item not in core.PRODUCTS:
                continue
            qty=int(n)
            if item=='WHEAT':
                keep=min(feed_remaining,qty);qty-=keep;feed_remaining-=keep
            if qty>0:
                goods.append((item,qty))
        # Exact midnight inventory ordering is retained when capacity is tight.
        for item,qty in goods:
            if auto:
                qty=min(qty,cap);cap-=qty
            if auto or deliver:
                _flow(item,qty,rows[sale_day])
        if goods and not auto and deliver:
            rows[0]['delivery']+=dist+1
    frames=_market_frames(observation,cfg,days,prices,regime,summary=summary)
    baseline=_value(rows,frames,observation,cfg,feed_owned)
    candidates=[]
    free=[(x,y,t) for x,y,t in empty if (x,y) not in reserved]
    if include_candidates and style!='liquidate' and days>0:
        candidate_items = include_candidates if isinstance(include_candidates, (list, tuple, set)) else [*core.CROPS,*core.ANIMALS]
        for item in candidate_items:
            is_crop=item in core.CROPS
            data=core.CROPS[item] if is_crop else core.ANIMALS[item]
            if days<data['first_yield_day']:
                continue
            homes=[p for p in free if is_crop or p[2] is None or p[2].get('kind') in ('WEED',data['structure'])]
            if not homes:
                continue
            x,y,tile=homes[0]
            ledger=queued_lifecycle(item,(x,y),tile,repeat=is_crop)
            if tile is not None:
                ledger[next((i for i,r in enumerate(ledger) if r['service']),0)]['service']+=1 if is_crop or tile.get('kind')=='WEED' else -1
            combined=_merge([dict(r, sales=dict(r['sales'])) for r in rows],ledger)
            valued=_value(combined,frames,observation,cfg,feed_owned)
            own_net=valued['net']-baseline['net']
            margin=valued['margin']-baseline['margin']
            candidates.append(dict(item=item,kind='crop' if is_crop else 'animal',target=[x,y],quantity=1,
                                   net=own_net,margin=margin,score=min(own_net,margin),
                                   required_cash=valued['required_cash'],upfront=ledger[0]['seed_cost']+ledger[0]['animal_cost'],
                                   daily=valued['daily'],marginal_daily=ledger,
                                   policy={'focus':'crop' if is_crop else 'animal','item':item,'regime':regime}))
        # A crop cohort is valued as one combined marginal programme, never
        # quantity times a single-plot NPV. Every plot owns a distinct free tile;
        # merged cash, nonlinear sale prices and daily wages are recomputed.
        singles=[candidate for candidate in candidates if candidate['kind']=='crop']
        queue_limit=max(1,min(8,(tpd-step%tpd-1)*max(2,len(farm.get('hands',[]))+1)//4))
        pending_count=sum(1 for entry in owned if entry['kind']!='placed')
        available_queue=max(0,queue_limit-pending_count)
        for single in singles:
            item=single['item']
            maximum=min(len(free),available_queue,
                        max(0,int(farm.get('money',0)//max(1,core.CROPS[item]['seed']))))
            quantities=sorted(set(q for q in (2,maximum) if 1<q<=maximum))
            for quantity in quantities:
                ledger=[_row() for _ in rows]
                for x,y,tile in free[:quantity]:
                    part=queued_lifecycle(item,(x,y),tile,repeat=True)
                    if tile is not None:
                        part[next((i for i,r in enumerate(part) if r['service']),0)]['service']+=1
                    _merge(ledger,part)
                valued=_value(_merge([dict(r,sales=dict(r['sales'])) for r in rows],ledger),frames,observation,cfg,feed_owned)
                own_net=valued['net']-baseline['net'];margin=valued['margin']-baseline['margin']
                candidates.append(dict(item=item,kind='crop',target=[list(p[:2]) for p in free[:quantity]],quantity=quantity,
                                       net=own_net,margin=margin,score=min(own_net,margin),required_cash=valued['required_cash'],
                                       upfront=ledger[0]['seed_cost'],daily=valued['daily'],marginal_daily=ledger,
                                       policy={'focus':'crop','item':item,'quantity':quantity,'regime':regime}))
        extras=len(farm.get('unlocked_quadrants',['NW']))-1
        if len(free)<2 and extras<len(core.LAND_PRICES) and days>=3:
            # Charge the entire land transaction once, never amortize an
            # unaffordable quadrant into a fictitious cheap individual tile.
            options=[c for c in candidates if c['kind']=='crop' and c['quantity']==1]
            if not options:
                # Empty current land is not needed to quote the next quadrant.
                for item,data in core.CROPS.items():
                    if days>=data['first_yield_day']:
                        ledger=lifecycle(item,day,last,tpd,shed_distance=2,repeat=True)
                        options.append(dict(item=item,marginal_daily=ledger,score=0))
            for option in options:
                quantity=min(8,(len(farm['tiles'])//2)**2)
                ledger=[_row() for _ in rows]
                for _ in range(quantity):
                    _merge(ledger,option['marginal_daily'])
                ledger[0]['land_cost']=core.LAND_PRICES[extras]
                valued=_value(_merge([dict(r, sales=dict(r['sales'])) for r in rows],ledger),frames,observation,cfg,feed_owned)
                own_net=valued['net']-baseline['net'];margin=valued['margin']-baseline['margin']
                candidates.append(dict(item=option['item'],kind='land',target=None,quantity=quantity,
                                       net=own_net,margin=margin,score=min(own_net,margin),
                                       required_cash=valued['required_cash'],upfront=ledger[0]['land_cost']+ledger[0]['seed_cost'],
                                       daily=valued['daily'],marginal_daily=ledger,
                                       policy={'focus':'crop','item':option['item'],'regime':regime}))
    candidates.sort(key=lambda c:(-c['score'],c['kind'],c['item']))
    # Immediate shed sales fund feed/hiring before those market orders. Credit
    # only unreserved stock: wheat cannot simultaneously be sold and own feed.
    params=core._resolve_market_params(observation.get('market',{}).get('params'))
    inventory=observation.get('market',{}).get('inventory',{})
    immediate=[]
    stock={p:max(0,int(private.get('shed',{}).get(p,0))) for p in core.PRODUCTS}
    for item,qty in stock.items():
        spendable=max(0,qty-(min(qty,feed_owned) if item=='WHEAT' else 0))
        receipts,_=_quotes(item,inventory.get(item,params[item]['I0']),spendable,params)
        immediate.append(receipts)
    slots=max(1,int(_get(cfg,'maxMarketOrdersPerTurn',10)))
    opening_credit=sum(sorted(immediate,reverse=True)[:slots])
    funding_cash=max(0.,farm.get('money',0))
    baseline['required_cash']=liquidity_requirement(baseline['daily'],opening_credit)
    funded=funding_cash+1e-9>=baseline['required_cash']
    # Reject unfunded future production, retaining only observable liquidation.
    # No fractional phantom herd or borrowed feed is introduced. Midnight stock
    # is capacity-limited; terminal cargo must actually reach the shed in time.
    midnight=step+(tpd-step%tpd)<=end
    cargo_room=max(0,int(_get(cfg,'shedCapacity',100))-(0 if midnight or end-step>=1 else sum(stock.values())))
    for idx,inv in enumerate(private.get('inventories',[])):
        reachable=idx<len(positions) and distance(positions[idx])+1<=end-step+1
        if not midnight and not reachable:
            continue
        for item,qty in inv.items():
            if item not in core.PRODUCTS:
                continue
            take=min(max(0,int(qty)),cargo_room);cargo_room-=take
            stock[item]+=take
    liquidation=[]
    for item,qty in stock.items():
        receipts,_=_quotes(item,inventory.get(item,params[item]['I0']),qty,params)
        liquidation.append(receipts)
    # With only the final market phase remaining, its actual order cap applies.
    liquidation_value=sum(sorted(liquidation,reverse=True)[:slots] if step==end else liquidation)
    asset=max(0.,liquidation_value,baseline['net'] if funded else 0.)
    return dict(asset_value=asset,baseline=baseline,candidates=candidates,owned=owned,
                continuation_funded=funded,liquidation_value=liquidation_value,funding_cash=funding_cash,opening_sale_credit=opening_credit,
                reserve=min(max(0.,farm.get('money',0)),baseline['required_cash']),
                feed_owned=feed_owned,free_slots=len(free),
                assumptions=['Native lifecycle and daily care ordering; full finite crop lifespan',
                             'Shared tile tours, 82% usable worker turns, exact Fibonacci wage staircase',
                             'Midnight cargo deposit except explicit final-day delivery; future capacity approximate',
                             'Scenario prices, visible rival supply, no unseen future shop/RNG information'])


def asset_value(observation,configuration=None,prices=None,regime='central',summary=None):
    return build_book(observation,configuration,prices=prices,regime=regime,include_candidates=False,summary=summary)['asset_value']


def market_options(observation,configuration=None,book=None):
    """Expose genuinely different executable families before same-family variants."""
    book=book or build_book(observation,configuration)
    useful=[c for c in book['candidates'] if c['score']>0]
    policies=[]
    for family in ('crop','animal'):
        candidate=next((c for c in useful if c['kind']==family),None)
        if candidate is not None:
            policies.append(candidate['policy'])
    for candidate in useful:
        if candidate['policy'] not in policies:
            policies.append(candidate['policy'])
        if len(policies)>=3:
            break
    policies.append({'focus':'liquidate','item':None,'regime':'central'})
    return policies


def service_hires(observation, configuration=None, prices=None, max_hires=32):
    """Conservative spatial marginal-hire audit, never a mandatory-work bill.

    Existing workers reserve reachable bundles first. A new hand starts at its
    native next-turn spawn and must recover its exact wage from still-unclaimed
    work within the day. Terminal bundles include physical sale delivery and no
    future husbandry. This bounded greedy executable-route estimate can leave
    work undone; more demanded work is not permission to spend unlimited cash.
    """
    cfg=configuration or {}
    farm,private,tpd,step,end=_context(observation,cfg)
    turns=max(0,min(tpd-step%tpd-1,end-step))
    if turns<2:
        return []
    day=step//tpd;days=max(0,end//tpd-day);terminal=days==0
    quotes=prices or observation.get('market',{}).get('prices',{})
    size=len(farm['tiles']);access=core._shed_access_tiles(size)
    nearest=lambda p:min(access,key=lambda a:(_distance(p,a),a))
    tasks=[]
    for y,row in enumerate(farm['tiles']):
        for x,tile in enumerate(row):
            if not isinstance(tile,dict):
                continue
            value=0.;work=0;feed=0;sale=False
            item=tile.get('crop',tile.get('animal'))
            if item in core.CROPS:
                data=core.CROPS[item];price=max(1.,quotes.get(item,core.MARKET_PARAMS[item]['base']))
                age=day-tile.get('planted_day',day);held=tile.get('yield_units',0)
                mature=age>=data['first_yield_day']
                if mature and held and (data['ongoing'] or age>=data['max_yield_day'] or terminal):
                    value+=held*price*.8;work+=1;sale=True
                future_dates=(max(0,min(data['max_yield'],1+(age+days-data['first_yield_day'])//max(1,data['interval'])))-
                              max(0,min(data['max_yield'],1+(age-data['first_yield_day'])//max(1,data['interval'])))) if data['ongoing'] else int(age+days>=data['first_yield_day'])
                if not terminal and not tile.get('watered_today',False) and (future_dates or held):
                    survival=min(data['seed']+2*price,(held+max(1,future_dates))*price*.6)
                    value+=survival if tile.get('consecutive_unwatered',0)>=1 else survival/max(2,data['first_yield_day']-age+1)
                    work+=1
            elif item in core.ANIMALS:
                data=core.ANIMALS[item];price=max(1.,quotes.get(data['product'],core.MARKET_PARAMS[data['product']]['base']))
                held=tile.get('yield_units',0)
                if held:
                    value+=held*price*.8;work+=1;sale=True
                if tile.get('fertilizer_available',False):
                    value+=max(1.,quotes.get('FERTILIZER',100))*.8;work+=1;sale=True
                age=day-tile.get('placed_day',day)
                future=any(age+d>=data['first_yield_day'] and (age+d-data['first_yield_day'])%data['interval']==0 for d in range(1,days+1))
                if not terminal and future:
                    if not tile.get('fed_today',False):
                        feed=1;work+=1
                        tomorrow=age+1>=data['first_yield_day'] and (age+1-data['first_yield_day'])%data['interval']==0
                        survival=(min(data['cost'],price*(1+data['interval']))*.6
                                  if tile.get('consecutive_unfed',0)>=1 else
                                  tile.get('pending_care_bonus',0)*price*.8 if tomorrow else 0.)
                        value+=max(0.,survival-quotes.get('WHEAT',25))
                    if not tile.get('cared_today',False):
                        value+=price*.6/max(1,data['interval']);work+=1
            if work and value>0:
                tasks.append(dict(target=(x,y),work=work,value=value,feed=feed,sale=sale))
    # Owned seed/animal stock contributes executable placement tasks, each once.
    free=[(x,y) for y,row in enumerate(farm['tiles']) for x,t in enumerate(row) if t is None]
    free.sort(key=lambda p:(_distance(p,nearest(p)),p))
    for item,qty in private.get('seeds',{}).items():
        if item not in core.CROPS or days<core.CROPS[item]['first_yield_day']:
            continue
        for _ in range(min(int(qty),len(free))):
            target=free.pop(0);data=core.CROPS[item]
            price=quotes.get(item,core.MARKET_PARAMS[item]['base'])
            value=max(0.,data['max_yield']*price*.5-data['seed'])
            tasks.append(dict(target=target,work=2,value=value,feed=0,sale=False))
    for animal,data in core.ANIMALS.items():
        if days<data['first_yield_day']:
            continue
        carriers=[(idx,int(inv.get(animal,0))) for idx,inv in enumerate(private.get('inventories',[])) if inv.get(animal,0)]
        stocks=[(None,int(private.get('shed',{}).get(animal,0))),*carriers]
        for owner,quantity in stocks:
            for _ in range(min(quantity,len(free))):
                target=free.pop(0)
                price=quotes.get(data['product'],core.MARKET_PARAMS[data['product']]['base'])
                value=max(0.,min(data['cost'],price*data['first_yield_day']*.6)-quotes.get('WHEAT',25))
                tasks.append(dict(target=target,work=3 if owner is not None else 4,value=value,
                                  feed=1,sale=False,owner=owner,shed_pickup=owner is None))
    feed_available=int(private.get('shed',{}).get('WHEAT',0))
    pool=list(tasks)
    def route(position,carried,budget,consume,worker_id=None):
        nonlocal feed_available
        plan=[];value=0.;used_feed=0
        while pool:
            choices=[]
            for index,task in enumerate(pool):
                if task.get('owner') is not None and task['owner'] != worker_id:
                    continue
                target=task['target'];cost=_distance(position,target)+task['work']
                need=max(0,task['feed']-carried)
                if need or task.get('shed_pickup'):
                    if need>feed_available-used_feed:
                        continue
                    shed=nearest(position)
                    cost=_distance(position,shed)+1+_distance(shed,target)+task['work']
                if terminal and task['sale']:
                    cost+=_distance(target,nearest(target))+1
                if cost<=budget:
                    choices.append((task['value']/max(1,cost),task['value'],-cost,-index,index,cost,need))
            if not choices:
                break
            _,_,_,_,index,cost,need=max(choices)
            task=pool.pop(index);plan.append(task);budget-=cost;value+=task['value'];used_feed+=need
            carried=max(0,carried-task['feed'])
            position=nearest(task['target']) if terminal and task['sale'] else task['target']
        if consume:
            feed_available-=used_feed
        return value,plan,used_feed
    positions=[farm['farmer'],*farm.get('hands',[])]
    for index,pos in enumerate(positions):
        inv=private.get('inventories',[{}])[index] if index<len(private.get('inventories',[])) else {}
        route(tuple(pos),int(inv.get('WHEAT',0)),turns,True,worker_id=index)
    audit=[];virtual=dict(farm,hands=list(farm.get('hands',[])))
    for i in range(min(32,max(0,int(max_hires)))):
        wage=core._hire_cost(int(farm.get('hires_today',0))+i,int(_get(cfg,'farmHandCostMult',1)))
        spawn=core._spawn_hand(virtual,size)
        before=list(pool)
        value,plan,used_feed=route(tuple(spawn),0,turns,False)
        if not plan or value<=wage:
            pool=before
            break
        feed_available-=used_feed
        audit.append(dict(wage=wage,executable_value=value,targets=[list(t['target']) for t in plan],
                          turns=turns,terminal=terminal))
        virtual['hands'].append(spawn)
    return audit
'''
_mod = _types.ModuleType(_PACKAGE.__name__ + ".commitments")
_mod.__package__ = _PACKAGE.__name__
_sys.modules[_mod.__name__] = _mod
setattr(_PACKAGE, "commitments", _mod)
exec(compile(_SOURCE_COMMITMENTS, "<general_v3/commitments.py>", "exec"), _mod.__dict__)

# BEGIN SOURCE reference_scheduler.py
_SOURCE_REFERENCE_SCHEDULER = '''"""Stateless, observation-only farm execution and conservative investment policy.

All worker commands are applied to a private copy with the authoritative native
transition before the next worker is assigned. Prices beyond the current turn
are bounded heuristics, not guaranteed receipts. No episode identity, seed,
opponent identity, recorded actions, or persistent process state is used.
"""
import copy
import math

from . import native_core as core


def _get(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def _context(observation, configuration=None):
    cfg = configuration or {}
    farms = _get(observation, "farms", [])
    seat = int(_get(observation, "player", 0))
    farm = farms[seat]
    tpd = max(1, int(_get(cfg, "turnsPerDay", 24)))
    step = int(_get(observation, "step", int(_get(observation, "day", 0)) * tpd
                    + int(_get(observation, "hour", 0))))
    end = max(1, int(_get(cfg, "episodeSteps", 720))) - 2
    return farm, _get(observation, "private", {}), tpd, step, end


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _move(source, target):
    # Locked ground is traversable, so Manhattan paths are always legal.
    if source[0] != target[0]:
        return ["EAST" if source[0] < target[0] else "WEST"]
    return ["SOUTH" if source[1] < target[1] else "NORTH"]


def _tiles(farm):
    return [(x, y, tile) for y, row in enumerate(farm["tiles"])
            for x, tile in enumerate(row) if tile != "LOCKED"]


def _prices(observation, configuration, horizon=4):
    """Current-shop demand, with visible farm supply and a short forecast cap."""
    cfg = configuration or {}
    market = _get(observation, "market", {})
    params = core._resolve_market_params(market.get("params"))
    inventory = market.get("inventory", {})
    tpd = max(1, int(_get(cfg, "turnsPerDay", 24)))
    demand = {p: tpd / max(1, int(_get(cfg, "townCenterSellInterval", 24)))
              for p in core.PRODUCTS}
    demand["FERTILIZER"] = 0.0
    shop_rate = tpd / max(1, int(_get(cfg, "townShopSellInterval", 4)))
    for shop in _get(observation, "town", {}).get("unlocked_shops", []):
        products = core.SHOPS.get(shop, [])
        for p in products:
            demand[p] += shop_rate * (2 if len(products) == 1 else 1)
    supply = {p: 0.0 for p in core.PRODUCTS}
    for farm in _get(observation, "farms", []):
        for _, _, tile in _tiles(farm):
            if not isinstance(tile, dict):
                continue
            if tile.get("animal") in core.ANIMALS:
                data = core.ANIMALS[tile["animal"]]
                supply[data["product"]] += (1 + data["interval"]) / data["interval"]
                supply["FERTILIZER"] += 0.75
            elif tile.get("crop") in core.CROPS:
                data = core.CROPS[tile["crop"]]
                supply[tile["crop"]] += (4 / (data["first_yield_day"] + 4)
                                           if data["ongoing"] else
                                           data["max_yield"] / (data["max_yield_day"] + 1))
    values = {}
    for item in core.PRODUCTS:
        now = float(market.get("prices", {}).get(item, params[item]["base"]))
        stock = inventory.get(item, params[item]["I0"])
        projected = stock + (supply[item] - demand[item]) * min(6, max(0, horizon))
        future = core.market_price(item, projected, params)
        # Keep demand extrapolation local; later shops and rival actions are unknown.
        future = min(future, max(1.5 * now, 2 * params[item]["base"]))
        values[item] = max(1.0, 0.6 * now + 0.4 * future)
    return values


def _crop_returns(crop, remaining_days, prices, age=0, held=0):
    data = core.CROPS[crop]
    if data["ongoing"]:
        future = [d for d in range(data["first_yield_day"],
                                   data["first_yield_day"] + 4 * data["interval"],
                                   data["interval"])
                  if age < d <= age + remaining_days]
        return held * prices[crop] + sum(prices[crop] * 0.965 ** (d - age) for d in future)
    harvest_day = min(data["max_yield_day"], age + remaining_days)
    if harvest_day < data["first_yield_day"]:
        return 0.0
    start = (data["max_yield_day"] + 1) // 2
    units = min(data["max_yield"], max(1, held) + max(0, harvest_day - max(age, start - 1)))
    return units * prices[crop] * 0.965 ** max(0, harvest_day - age)


def _investment_values(prices, days, style):
    """Profit and economic productivity, charging feed and finite daily labor."""
    crop_values, animal_values = {}, {}
    for crop, data in core.CROPS.items():
        lifetime = data["first_yield_day"] + 3 * data["interval"] if data["ongoing"] else data["max_yield_day"]
        duration = min(days, lifetime)
        revenue = 0.85 * _crop_returns(crop, days, prices)
        labor = 3 + duration * 1.5 + (4 if data["ongoing"] else 1)
        net = revenue - data["seed"] - 1.5 * labor
        speed = max(1, duration + 1)
        # Capital tied up for ten days is less helpful during the opening.
        crop_values[crop] = (net, net / speed / (1 + labor / speed * 0.12))
    for animal, data in core.ANIMALS.items():
        product = data["product"]
        revenue = 0.0
        for age in range(data["first_yield_day"], days + 1, data["interval"]):
            units = min(data["max_held"], data["first_yield_day"] if age == data["first_yield_day"]
                        else 1 + data["interval"])
            revenue += units * prices[product] * 0.965 ** age
        # Fertilizer has no town demand: heavily discount its long-run price.
        revenue += max(0, days - 1) * min(prices["FERTILIZER"], 45) * 0.65
        labor = 4 + 5.2 * days
        net = 0.8 * revenue - data["cost"] - days * prices["WHEAT"] - 1.5 * labor
        if days < data["first_yield_day"]:
            net = -data["cost"]
        animal_values[animal] = (net, net / max(1, days) / 1.65)
    if style == "liquidate":
        crop_values = {c: (-1, -1) for c in crop_values}
        animal_values = {a: (-1, -1) for a in animal_values}
    return crop_values, animal_values


def asset_value(observation, configuration=None):
    """Discounted noncash value for search leaves, including own physical stock.

    This is a bounded economic estimate, not simulated future cash. Do not add
    another inventory-salvage term to it. At the final action there is no assumed
    terminal conversion of undelivered inventory or immature assets.
    """
    farm, private, tpd, step, end = _context(observation, configuration)
    if step > end:
        return 0.0
    day, last_day = step // tpd, end // tpd
    remaining = max(0, last_day - day)
    prices = _prices(observation, configuration)
    actual = _get(observation, "market", {}).get("prices", prices)
    value = sum(0.8 * min(prices.get(p, 0), actual.get(p, 0)) * n
                for p, n in private.get("shed", {}).items() if p in core.PRODUCTS)
    positions = [farm["farmer"], *farm.get("hands", [])]
    access = core._shed_access_tiles(len(farm["tiles"]))
    for idx, inv in enumerate(private.get("inventories", [])):
        distance = min(_distance(positions[idx], p) for p in access) if idx < len(positions) else 999
        can_deliver = end - step >= distance
        if can_deliver:
            value += sum(0.7 * min(prices.get(p, 0), actual.get(p, 0)) * n
                         for p, n in inv.items() if p in core.PRODUCTS)
    cv, av = _investment_values(prices, remaining, "balanced")
    for crop, n in private.get("seeds", {}).items():
        if crop in cv and cv[crop][0] > 0 and remaining >= core.CROPS[crop]["first_yield_day"]:
            value += n * min(core.CROPS[crop]["seed"], 0.25 * cv[crop][0])
    for animal, data in core.ANIMALS.items():
        unplaced = private.get("shed", {}).get(animal, 0) + sum(
            inv.get(animal, 0) for inv in private.get("inventories", []))
        if av[animal][0] > 0:
            value += unplaced * min(data["cost"], av[animal][0] * 0.35)
    future_value, daily_labor = 0.0, 0.0
    for x, y, tile in _tiles(farm):
        if not isinstance(tile, dict):
            continue
        if tile.get("crop") in core.CROPS:
            crop = tile["crop"]
            age = day - tile.get("planted_day", day)
            revenue = _crop_returns(crop, remaining, prices, age, tile.get("yield_units", 0))
            future_value += max(0, revenue * 0.65 - 2 * min(remaining, 10))
            daily_labor += 2
        elif tile.get("animal") in core.ANIMALS:
            animal = tile["animal"]
            data = core.ANIMALS[animal]
            age = day - tile.get("placed_day", day)
            revenue = tile.get("yield_units", 0) * prices[data["product"]]
            for delay in range(1, remaining + 1):
                if age + delay >= data["first_yield_day"] and (age + delay - data["first_yield_day"]) % data["interval"] == 0:
                    revenue += min(data["max_held"], 1 + data["interval"]) * prices[data["product"]] * 0.96 ** delay
            revenue += remaining * min(40, prices["FERTILIZER"]) * 0.6
            future_value += max(0, revenue * 0.65 - remaining * prices["WHEAT"] - 7 * remaining)
            daily_labor += 5.5
    # Value only a serviceable farm; no infinite forecast from planted assets.
    capacity = tpd * 0.7 * max(1, min(9, 1 + len(farm.get("hands", [])) + 2))
    return float(value + future_value * min(1.0, capacity / max(1, daily_labor)))


def schedule(observation, configuration=None, style="balanced"):
    """Produce coordinated worker commands followed by a funded market queue."""
    if style not in ("balanced", "growth", "liquidate"):
        style = "balanced"
    original, own, tpd, step, end = _context(observation, configuration)
    cfg = configuration or {}
    farm, private = copy.deepcopy(original), copy.deepcopy(own)
    private.setdefault("shed", {})
    private.setdefault("seeds", {})
    private.setdefault("inventories", [{}])
    size = len(farm["tiles"])
    day, hour = divmod(step, tpd)
    turns_left = min(tpd - hour, max(0, end - step + 1))
    remaining_days = max(0, end // tpd - day)
    capacity = max(0, int(_get(cfg, "shedCapacity", 100)))
    prices = _prices(observation, cfg)
    cv, av = _investment_values(prices, remaining_days, style)
    crop_order = sorted(cv, key=lambda c: (-cv[c][1], c))
    animal_order = sorted(av, key=lambda a: (-av[a][1], a))
    positions = [farm["farmer"], *farm.get("hands", [])]
    access = core._shed_access_tiles(size)
    reserved, commands = set(), []
    planned_pickup = 0
    planned_animals = {a: 0 for a in core.ANIMALS}

    for idx in range(len(positions)):
        pos = core._farmer_position(farm, idx)
        inv = core._farmer_inventory(private, idx)
        current_tiles = _tiles(farm)
        animals = [(x, y, t) for x, y, t in current_tiles if isinstance(t, dict) and t.get("animal") in core.ANIMALS]
        unfed = sum(not t.get("fed_today", False) for _, _, t in animals)
        carried_feed = sum(i.get("WHEAT", 0) for i in private["inventories"])
        shed_pos = min(access, key=lambda p: (_distance(pos, p), p))
        best = (0.0, None, ["PASS"], ["PASS"])

        def offer(target, command, value, work=1, deadline=None):
            nonlocal best
            target = tuple(target)
            distance = _distance(pos, target)
            shed_command = command[0] in ("DROP", "PICKUP") or (command[0] == "PLACE" and command[1] in core.PRODUCTS)
            if (target in reserved and not shed_command) or value <= 0:
                return
            if deadline is not None and distance + work > deadline:
                return
            # The target operation must fit before the hand disappears at midnight.
            if distance + work > turns_left:
                return
            score = value / (1 + 0.65 * distance + 0.3 * (work - 1))
            if score > best[0]:
                best = (score, target, command if distance == 0 else _move(pos, target), command)

        carrier = next((a for a in animal_order if inv.get(a, 0) > 0), None)
        if carrier:
            kind = core.ANIMALS[carrier]["structure"]
            homes = [(x, y, t) for x, y, t in current_tiles
                     if (x, y) not in reserved and (t is None or (isinstance(t, dict) and t.get("kind") == kind and "animal" not in t))]
            homes.sort(key=lambda p: (0 if p[2] is not None else 1, _distance(pos, p), p[1], p[0]))
            if homes:
                x, y, tile = homes[0]
                offer((x, y), ["PLACE", carrier] if tile else ["BUILD_" + kind],
                      200 + core.ANIMALS[carrier]["cost"] * 0.4)

        for x, y, tile in current_tiles:
            target = (x, y)
            if tile is None:
                if carrier:
                    continue
                for crop in crop_order:
                    if private["seeds"].get(crop, 0) and cv[crop][0] > 0 and turns_left > 1:
                        offer(target, ["PLANT", crop], 25 + min(85, cv[crop][1]) * (1.2 if style == "growth" else 1), work=2)
                        break
                continue
            if not isinstance(tile, dict):
                continue
            crop, animal = tile.get("crop"), tile.get("animal")
            if crop in core.CROPS:
                data = core.CROPS[crop]
                age = day - tile.get("planted_day", day)
                units = tile.get("yield_units", 0)
                watered = tile.get("watered_today", False)
                mature = age >= data["first_yield_day"] and units > 0
                window = (data["max_yield_day"] + 1) // 2 <= age <= data["max_yield_day"]
                can_increase = not data["ongoing"] and window and units < data["max_yield"]
                final = end - step < tpd
                if mature and (data["ongoing"] or age >= data["max_yield_day"] or units >= data["max_yield"] or final):
                    if not watered and can_increase and turns_left >= 2:
                        offer(target, ["WATER"], 100 + prices[crop] * (units + 1) * 0.6, work=2)
                    else:
                        delivery = min(_distance(target, p) for p in access) + 1 if remaining_days == 0 else 0
                        offer(target, ["HARVEST"], 85 + prices[crop] * units * 0.6, work=1 + delivery)
                if not watered and remaining_days > 0:
                    risk = tile.get("consecutive_unwatered", 0) >= 1
                    future = _crop_returns(crop, remaining_days, prices, age, units)
                    value = (45 + min(200, future * 0.2)) if risk else 9
                    if can_increase:
                        value += prices[crop] * 0.65
                    offer(target, ["WATER"], value)
                if inv.get("FERTILIZER", 0) and tile.get("fertilized_until_day", -1) < day and remaining_days:
                    bonus = (min(3, max(0, data["max_yield_day"] - age + 1)) if not data["ongoing"] and window else
                             min(3, 3 / max(1, data["interval"])) if data["ongoing"] and age + 3 >= data["first_yield_day"] else 0)
                    offer(target, ["FERTILIZE"], max(0, bonus * prices[crop] * 0.6 - prices["FERTILIZER"]))
                exhausted = (data["ongoing"] and age >= data["first_yield_day"] + 3 * data["interval"] and units == 0)
                if exhausted and any(private["seeds"].get(c, 0) and cv[c][0] > 0 for c in crop_order):
                    offer(target, ["DIG"], 30)
            elif animal in core.ANIMALS:
                data = core.ANIMALS[animal]
                product = data["product"]
                units = tile.get("yield_units", 0)
                if units:
                    delivery = min(_distance(target, p) for p in access) + 1 if remaining_days == 0 else 0
                    offer(target, ["HARVEST"], 90 + prices[product] * units * 0.65, work=1 + delivery)
                if not tile.get("fed_today", False) and inv.get("WHEAT", 0) and remaining_days:
                    urgency = 120 if tile.get("consecutive_unfed", 0) else 60
                    offer(target, ["FEED"], urgency + min(150, prices[product] * 0.75))
                if not tile.get("cared_today", False) and tile.get("fed_today", False) and remaining_days:
                    offer(target, ["CARE"], 20 + prices[product] * 0.65 / data["interval"])
                if tile.get("fertilizer_available", False):
                    delivery = min(_distance(target, p) for p in access) + 1 if remaining_days == 0 else 0
                    offer(target, ["COLLECT_FERTILIZER"], 15 + prices["FERTILIZER"] * 0.8, work=1 + delivery)
            elif tile.get("kind") == "WEED" and (carrier or any(private["seeds"].get(c, 0) and cv[c][0] > 0 for c in crop_order)):
                offer(target, ["DIG"], 35)

        # Supplies are physically owned by this worker only after an actual pickup.
        if not carrier:
            for animal in animal_order:
                if private["shed"].get(animal, 0) > planned_animals[animal] and remaining_days >= core.ANIMALS[animal]["first_yield_day"]:
                    space = any(t is None or (isinstance(t, dict) and t.get("kind") == core.ANIMALS[animal]["structure"] and "animal" not in t)
                                for _, _, t in current_tiles)
                    if space:
                        offer(shed_pos, ["PICKUP", animal, 1], 180)
                        break
        need = max(0, unfed - carried_feed - planned_pickup)
        if not inv.get("WHEAT", 0) and private["shed"].get("WHEAT", 0) and need and remaining_days:
            quantity = min(6, need, private["shed"]["WHEAT"])
            offer(shed_pos, ["PICKUP", "WHEAT", quantity], 130 + 10 * quantity)
        # Preserve animal/feed cargo when depositing saleable products.
        saleable = {p: n for p, n in inv.items() if p in core.PRODUCTS and n > 0
                    and not (p == "WHEAT" and unfed and remaining_days)}
        if saleable and sum(private["shed"].values()) < capacity:
            item = max(saleable, key=lambda p: (saleable[p] * prices[p], p))
            value = sum(n * prices[p] for p, n in saleable.items())
            terminal = end - step < tpd
            priority = 35 + value * (1.1 if terminal else 0.55)
            command = ["DROP"] if len(saleable) == len(inv) else ["PLACE", item, saleable[item]]
            offer(shed_pos, command, priority)
        _, target, command, intended = best
        if target is not None and tuple(pos) != target:
            # Reserve tasks, not worker locations: collocated work is legal.
            if intended[0] not in ("DROP", "PICKUP"):
                reserved.add(target)
            if intended[:2] == ["PICKUP", "WHEAT"]:
                planned_pickup += intended[2]
            elif intended[0] == "PICKUP" and intended[1] in planned_animals:
                planned_animals[intended[1]] += intended[2]
        core._apply_unit_action(farm, private, idx, command, size, day, tpd, capacity)
        commands.append(command)

    orders = _market(observation, cfg, farm, private, prices, cv, av, style,
                     tpd, hour, remaining_days, turns_left, capacity)
    return {"farmer": commands[0], "hands": commands[1:], "market": orders}


def _market(observation, cfg, farm, private, prices, cv, av, style,
            tpd, hour, days, turns_left, capacity):
    """Budget only after workers. Project each order, including Fibonacci hires."""
    market = copy.deepcopy(_get(observation, "market", {}))
    market.setdefault("inventory", {p: core.MARKET_I0 for p in core.PRODUCTS})
    orders = []
    limit = max(1, int(_get(cfg, "maxMarketOrdersPerTurn", 10)))
    size = len(farm["tiles"])
    hire_mult = max(0, int(_get(cfg, "farmHandCostMult", core.FARM_HAND_COST_MULT)))

    def order(op, item=None, quantity=1, reserve=0):
        if len(orders) >= limit or quantity <= 0:
            return 0
        if op in ("HIRE", "BUY_LAND"):
            cost = core._hire_cost(farm["hires_today"], hire_mult) if op == "HIRE" else core.LAND_PRICES[len(farm["unlocked_quadrants"]) - 1]
            if farm["money"] < cost + reserve:
                return 0
            (core._do_hire(farm, private, size, hire_mult) if op == "HIRE" else core._do_buy_land(farm, size))
            orders.append([op])
            return 1
        done = 0
        for _ in range(int(quantity)):
            if op == "BUY_SEED":
                price = core.CROPS[item]["seed"]
            elif op == "BUY_ANIMAL":
                price = core.ANIMALS[item]["cost"]
            else:
                stock = market["inventory"][item] - (1 if op == "BUY_PRODUCT" else 0)
                price = core.market_price(item, stock, market.get("params"))
            if op != "SELL" and farm["money"] < price + reserve:
                break
            if not core._commit_unit(op, item, price, farm, private, market, capacity):
                break
            done += 1
        if done:
            orders.append([op, item, done])
        return done

    tiles = _tiles(farm)
    animals = [t for _, _, t in tiles if isinstance(t, dict) and t.get("animal") in core.ANIMALS]
    crops = [t for _, _, t in tiles if isinstance(t, dict) and t.get("crop") in core.CROPS]
    unplaced = sum(private["shed"].get(a, 0) + sum(i.get(a, 0) for i in private["inventories"]) for a in core.ANIMALS)
    feed_held = sum(i.get("WHEAT", 0) for i in private["inventories"])
    animal_count = len(animals) + unplaced
    feed_reserve = max(0, min(capacity // 3, animal_count * min(2, days)) - feed_held)
    # Sell deposits made by this turn's workers, but never their still-carried goods.
    products = sorted(core.PRODUCTS, key=lambda p: (-private["shed"].get(p, 0) * prices[p], p))
    for item in products:
        qty = private["shed"].get(item, 0) - (feed_reserve if item == "WHEAT" else 0)
        order("SELL", item, max(0, qty))
    if turns_left <= 1:
        return orders
    # Feed commitments are funded before discretionary growth.
    missing_feed = max(0, feed_reserve - private["shed"].get("WHEAT", 0))
    order("BUY_PRODUCT", "WHEAT", missing_feed, reserve=2)
    best_crop = max(cv, key=lambda c: (cv[c][1], c))
    best_animal = max(av, key=lambda a: (av[a][1], a))
    empty = sum(t is None or (isinstance(t, dict) and t.get("kind") == "WEED") for _, _, t in tiles)
    seed_stock = sum(private["seeds"].values())
    base_reserve = max(8, animal_count * prices["WHEAT"] * 0.6)
    growth = style != "liquidate" and days >= 2
    # Staged bundles prevent buying a barnyard that cannot be staffed or placed.
    if growth and av[best_animal][0] > 0 and animal_count < max(1, len(tiles) // 3):
        space = empty - min(seed_stock, empty) - unplaced
        empty_home = any(isinstance(t, dict) and t.get("kind") == core.ANIMALS[best_animal]["structure"] and "animal" not in t for _, _, t in tiles)
        if (space > 0 or empty_home) and unplaced < 2 and (av[best_animal][1] >= cv[best_crop][1] * 0.65 or not crops):
            # Buying feed alongside an animal must leave money for workers.
            reserve = base_reserve + 2 * prices["WHEAT"] + 2 * core.CROPS[best_crop]["seed"]
            if order("BUY_ANIMAL", best_animal, 1, reserve):
                animal_count += 1
                unplaced += 1
                order("BUY_PRODUCT", "WHEAT", min(2, days), reserve=base_reserve)
    if growth and cv[best_crop][0] > 0:
        planting_room = max(0, empty - seed_stock - unplaced)
        # Seed purchases are a one-day work queue, not unlimited asset accumulation.
        daily_capacity = max(1, min(10, (turns_left * max(2, len(farm["hands"]) + 1) - 2 * len(crops) - 4 * animal_count) // 4))
        qty = min(planting_room, max(0, daily_capacity - seed_stock))
        order("BUY_SEED", best_crop, qty, reserve=base_reserve)
    pending_plants = min(empty, sum(n for crop, n in private["seeds"].items() if crop in cv and cv[crop][0] > 0))
    day = int(_get(observation, "step", 0)) // tpd
    maintenance = sum((bool(days) and not t.get("watered_today", False)) * 2
                      + (bool(t.get("yield_units", 0)) and day - t.get("planted_day", day) >= core.CROPS[t["crop"]]["first_yield_day"])
                      for t in crops)
    maintenance += sum(2 * (bool(days) and not t.get("fed_today", False)) + (bool(days) and not t.get("cared_today", False))
                       + bool(t.get("yield_units", 0)) + bool(t.get("fertilizer_available", False)) for t in animals)
    work = maintenance + pending_plants * 4 + unplaced * 5
    desired = max(1, min(12, math.ceil(work / max(1, (turns_left - 1) * 0.72))))
    if work and hour <= tpd // 3:
        desired = max(desired, min(3, 1 + len(crops) // 6 + animal_count // 3 + bool(pending_plants)))
    while len(farm["hands"]) + 1 < desired and turns_left >= 4:
        cost = core._hire_cost(farm["hires_today"], hire_mult)
        if cost > max(3, (turns_left - 2) * min(12, max(prices.values()) * 0.04)):
            break
        if not order("HIRE", reserve=2 + animal_count * prices["WHEAT"] * 0.2):
            break
    # Expansion only after current ground and labor can actually use more room.
    extras = len(farm["unlocked_quadrants"]) - 1
    if growth and extras < len(core.LAND_PRICES) and days >= 5 and empty <= 2 and cv[best_crop][0] > 0:
        land_cost = core.LAND_PRICES[extras]
        future_net = (size // 2) ** 2 * cv[best_crop][0] * 0.55
        if future_net > land_cost * (1.2 if style == "growth" else 1.6):
            order("BUY_LAND", reserve=base_reserve + 4 * core.CROPS[best_crop]["seed"])
    return orders
'''
_mod = _types.ModuleType(_PACKAGE.__name__ + ".reference_scheduler")
_mod.__package__ = _PACKAGE.__name__
_sys.modules[_mod.__name__] = _mod
setattr(_PACKAGE, "reference_scheduler", _mod)
exec(compile(_SOURCE_REFERENCE_SCHEDULER, "<general_v3/reference_scheduler.py>", "exec"), _mod.__dict__)

# BEGIN SOURCE scheduler.py
_SOURCE_SCHEDULER = '''"""Stateless, observation-only farm execution and conservative investment policy.

All worker commands are applied to a private copy with the authoritative native
transition before the next worker is assigned. Prices beyond the current turn
are bounded heuristics, not guaranteed receipts. No episode identity, seed,
opponent identity, recorded actions, or persistent process state is used.
"""
import copy
import math

from . import native_core as core
from . import commitments


def _get(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def _context(observation, configuration=None):
    cfg = configuration or {}
    farms = _get(observation, "farms", [])
    seat = int(_get(observation, "player", 0))
    farm = farms[seat]
    tpd = max(1, int(_get(cfg, "turnsPerDay", 24)))
    step = int(_get(observation, "step", int(_get(observation, "day", 0)) * tpd
                    + int(_get(observation, "hour", 0))))
    end = max(1, int(_get(cfg, "episodeSteps", 720))) - 2
    return farm, _get(observation, "private", {}), tpd, step, end


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _move(source, target):
    # Locked ground is traversable, so Manhattan paths are always legal.
    if source[0] != target[0]:
        return ["EAST" if source[0] < target[0] else "WEST"]
    return ["SOUTH" if source[1] < target[1] else "NORTH"]


def _tiles(farm):
    return [(x, y, tile) for y, row in enumerate(farm["tiles"])
            for x, tile in enumerate(row) if tile != "LOCKED"]


def _prices(observation, configuration, horizon=4):
    """Current-shop demand, with visible farm supply and a short forecast cap."""
    cfg = configuration or {}
    market = _get(observation, "market", {})
    params = core._resolve_market_params(market.get("params"))
    inventory = market.get("inventory", {})
    tpd = max(1, int(_get(cfg, "turnsPerDay", 24)))
    demand = {p: tpd / max(1, int(_get(cfg, "townCenterSellInterval", 24)))
              for p in core.PRODUCTS}
    demand["FERTILIZER"] = 0.0
    shop_rate = tpd / max(1, int(_get(cfg, "townShopSellInterval", 4)))
    for shop in _get(observation, "town", {}).get("unlocked_shops", []):
        products = core.SHOPS.get(shop, [])
        for p in products:
            demand[p] += shop_rate * (2 if len(products) == 1 else 1)
    supply = {p: 0.0 for p in core.PRODUCTS}
    for farm in _get(observation, "farms", []):
        for _, _, tile in _tiles(farm):
            if not isinstance(tile, dict):
                continue
            if tile.get("animal") in core.ANIMALS:
                data = core.ANIMALS[tile["animal"]]
                supply[data["product"]] += (1 + data["interval"]) / data["interval"]
                supply["FERTILIZER"] += 0.75
            elif tile.get("crop") in core.CROPS:
                data = core.CROPS[tile["crop"]]
                supply[tile["crop"]] += (4 / (data["first_yield_day"] + 4)
                                           if data["ongoing"] else
                                           data["max_yield"] / (data["max_yield_day"] + 1))
    values = {}
    for item in core.PRODUCTS:
        now = float(market.get("prices", {}).get(item, params[item]["base"]))
        stock = inventory.get(item, params[item]["I0"])
        projected = stock + (supply[item] - demand[item]) * min(6, max(0, horizon))
        future = core.market_price(item, projected, params)
        # Keep demand extrapolation local; later shops and rival actions are unknown.
        future = min(future, max(1.5 * now, 2 * params[item]["base"]))
        values[item] = max(1.0, 0.6 * now + 0.4 * future)
    return values


def _crop_returns(crop, remaining_days, prices, age=0, held=0):
    data = core.CROPS[crop]
    if data["ongoing"]:
        future = [d for d in range(data["first_yield_day"],
                                   data["first_yield_day"] + 4 * data["interval"],
                                   data["interval"])
                  if age < d <= age + remaining_days]
        return held * prices[crop] + sum(prices[crop] * 0.965 ** (d - age) for d in future)
    harvest_day = min(data["max_yield_day"], age + remaining_days)
    if harvest_day < data["first_yield_day"]:
        return 0.0
    start = (data["max_yield_day"] + 1) // 2
    units = min(data["max_yield"], max(1, held) + max(0, harvest_day - max(age, start - 1)))
    return units * prices[crop] * 0.965 ** max(0, harvest_day - age)


def _investment_values(prices, days, style):
    """Profit and economic productivity, charging feed and finite daily labor."""
    crop_values, animal_values = {}, {}
    for crop, data in core.CROPS.items():
        lifetime = data["first_yield_day"] + 3 * data["interval"] if data["ongoing"] else data["max_yield_day"]
        duration = min(days, lifetime)
        revenue = 0.85 * _crop_returns(crop, days, prices)
        labor = 3 + duration * 1.5 + (4 if data["ongoing"] else 1)
        net = revenue - data["seed"] - 1.5 * labor
        speed = max(1, duration + 1)
        # Capital tied up for ten days is less helpful during the opening.
        crop_values[crop] = (net, net / speed / (1 + labor / speed * 0.12))
    for animal, data in core.ANIMALS.items():
        product = data["product"]
        revenue = 0.0
        for age in range(data["first_yield_day"], days + 1, data["interval"]):
            units = min(data["max_held"], data["first_yield_day"] if age == data["first_yield_day"]
                        else 1 + data["interval"])
            revenue += units * prices[product] * 0.965 ** age
        # Fertilizer has no town demand: heavily discount its long-run price.
        revenue += max(0, days - 1) * min(prices["FERTILIZER"], 45) * 0.65
        labor = 4 + 5.2 * days
        net = 0.8 * revenue - data["cost"] - days * prices["WHEAT"] - 1.5 * labor
        if days < data["first_yield_day"]:
            net = -data["cost"]
        animal_values[animal] = (net, net / max(1, days) / 1.65)
    if style == "liquidate":
        crop_values = {c: (-1, -1) for c in crop_values}
        animal_values = {a: (-1, -1) for a in animal_values}
    return crop_values, animal_values


def asset_value(observation, configuration=None, prices=None, regime="central", summary=None):
    """Net continuation cash from one complete owned commitment book."""
    return commitments.asset_value(observation, configuration, prices=prices, regime=regime, summary=summary)


def _rescue_value(tile, day, last_day, prices, final_actions=None, delivery_travel=0,
                  market_slots=10):
    """Two explicit continuation policies versus abandoning an endangered animal.

    Acquisition is sunk; held output has equal salvage in the two alternatives.
    It still occupies native storage until an assumed future-day harvest. Keep
    native refresh dates, pending care, clipping and two-unfed-day escape. Test
    each finite prefix of daily feed/care and minimum-survival feeding, followed
    by retirement, rather than obliging either policy to fund a negative tail.
    Future service, equal salvage and constant prices remain estimates, not a
    proof that retirement is optimal. This is not a portfolio optimizer.
    """
    data = core.ANIMALS[tile['animal']]
    wheat = max(1., prices.get('WHEAT', 25.))
    product = max(1., prices.get(data['product'], 1.))
    fertilizer = min(45., max(0., prices.get('FERTILIZER', 0.)))
    labor = 1.5
    values = []
    for daily_care in (False, True):
        hunger = int(tile.get('consecutive_unfed', 0))
        pending = int(tile.get('pending_care_bonus', 0))
        held = max(0, int(tile.get('yield_units', 0)))
        held_fertilizer = bool(tile.get('fertilizer_available', False))
        new_held, new_fertilizer = 0, False
        value, best = 0., None
        for current in range(day, last_day+1):
            discount = .965 ** (current-day)
            if current > day:
                # Each intermediate day's harvest deposits at midnight and can
                # sell next day. The final day must collect and deliver itself.
                receipts = [new_held*product] if new_held else []
                if new_fertilizer:
                    receipts.append(fertilizer)
                if current == last_day:
                    available = final_actions if final_actions is not None else 1000000
                    receipts.sort(reverse=True)
                    options = [0.]
                    for take in range(1, len(receipts)+1):
                        work = delivery_travel+take+1
                        sales_delay = (take-1)//max(1, market_slots)
                        if work+sales_delay <= available:
                            options.append(sum(receipts[:take])-labor*(work+sales_delay))
                    gain = max(options)
                else:
                    # Collection labor is paid today; midnight cargo can be
                    # sold only in the following day's market phase.
                    gain = sum(max(0., .965*revenue-labor) for revenue in receipts)
                value += discount*max(0., gain)
                best = value if best is None else max(best, value)
                held, new_held, held_fertilizer, new_fertilizer = 0, 0, False, False
            if current == last_day:
                break
            feed = daily_care or hunger >= 1
            care = daily_care or (current == day and tile.get('cared_today', False))
            if feed:
                # Feed, amortized pickup and a shared-tile-tour travel charge.
                value -= discount * (wheat + labor * 2.25)
                hunger = 0
            else:
                hunger += 1
            if hunger >= 2:
                break
            next_day = current + 1
            since_first = next_day-tile.get('placed_day', day)-data['first_yield_day']
            if since_first >= 0 and since_first % data['interval'] == 0:
                units = min(max(0, data['max_held']-held), 1 + (pending if feed else 0))
                held += units
                new_held += units
                pending = 0
            # Each survived refresh exposes one collectable fertilizer unit.
            new_fertilizer = not held_fertilizer
            held_fertilizer = True
            if feed and care:
                pending += 1
                if current != day or not tile.get('cared_today', False):
                    value -= discount*labor
        values.append(best if best is not None else 0.)
    return max(values, default=0.)


def _feed_route(position, carried, targets, access):
    """One worker's exact feed-only tour, with one real batched pickup if needed."""
    position = tuple(position)
    carried = max(0, int(carried))
    cost, first, pickup = 0, None, 0
    for offset, target in enumerate(targets):
        if not carried:
            shed = min(access, key=lambda p: (_distance(position, p)+_distance(p, target), p))
            distance = _distance(position, shed)
            pickup = len(targets)-offset
            if first is None:
                first = _move(position, shed) if distance else ['PICKUP', 'WHEAT', pickup]
            cost += distance+1
            position, carried = tuple(shed), pickup
        distance = _distance(position, target)
        if first is None:
            first = _move(position, target) if distance else ['FEED']
        cost += distance+1
        position, carried = tuple(target), carried-1
    return dict(targets=list(targets), turns=cost, pickup=pickup,
                first=first or ['PASS'], end=position, carried=carried)


def _assign_feed_jobs(farm, private, jobs, turns):
    """Bounded, deterministic custody-aware coverage, not an optimal tour proof.

    Each target and each shed unit belongs to at most one route. Appending or
    prepending a job gives at most two choices per worker, rather than an
    unbounded assignment/permutation search. Uncovered jobs stay explicit.
    """
    positions = [farm['farmer'], *farm.get('hands', [])]
    inventories = private.get('inventories', [])
    wheat = [max(0, int(inventories[i].get('WHEAT', 0))) if i < len(inventories) else 0
             for i in range(len(positions))]
    access = core._shed_access_tiles(len(farm['tiles']))
    shed = max(0, int(private.get('shed', {}).get('WHEAT', 0)))
    routes = [_feed_route(p, w, [], access) for p, w in zip(positions, wheat)]
    reserved = 0
    def difficulty(job):
        costs = [_feed_route(p, w, [job['target']], access) for p, w in zip(positions, wheat)]
        feasible = [r['turns'] for r in costs if r['turns'] <= turns and r['pickup'] <= shed]
        return (len(feasible), turns-min(feasible, default=turns+1), -job['value'], job['target'])
    for job in sorted(jobs, key=difficulty):
        choices = []
        for index, route in enumerate(routes):
            for targets in (route['targets']+[job['target']], [job['target']]+route['targets']):
                proposal = _feed_route(positions[index], wheat[index], targets, access)
                if proposal['turns'] > turns or reserved-route['pickup']+proposal['pickup'] > shed:
                    continue
                extra = proposal['turns']-route['turns']
                # The continuation ledger already pays a feed action and a
                # small shared-tour allowance; charge longer actual detours.
                if job['value'] <= 1.5*max(0, extra-2.25):
                    continue
                choices.append((extra, proposal['turns'], index, tuple(targets), proposal))
        if choices:
            _, _, index, _, proposal = min(choices, key=lambda c:c[:4])
            reserved += proposal['pickup']-routes[index]['pickup']
            routes[index] = proposal
    assigned = {target for route in routes for target in route['targets']}
    return dict(routes=routes, assigned=sorted(assigned),
                unassigned=[job['target'] for job in jobs if job['target'] not in assigned],
                shed_reserved=reserved, turns=turns)


def feed_service_plan(observation, configuration=None, prices=None):
    """Audit profitable imminent escape obligations using only this observation.

    This is a survival deadline guard, not a guarantee of daily feeding/care.
    Retirements are allowed when neither stated continuation policy repays its
    future feed/service cost, or no saleable refresh remains in the episode.
    """
    farm, private, tpd, step, end = _context(observation, configuration)
    day, hour = divmod(step, tpd)
    turns = max(0, min(tpd-hour, end-step+1))
    prices = prices or _prices(observation, configuration)
    jobs, retirements = [], []
    access = core._shed_access_tiles(len(farm['tiles']))
    final_actions = end % tpd+1
    for x, y, tile in _tiles(farm):
        if (not isinstance(tile, dict) or tile.get('animal') not in core.ANIMALS
                or tile.get('fed_today', False) or tile.get('consecutive_unfed', 0) < 1):
            continue
        target = (x, y)
        delivery_travel = (_distance(core._default_spawn(len(farm['tiles'])), target)
                           + min(_distance(target, p) for p in access))
        value = _rescue_value(tile, day, end//tpd, prices, final_actions, delivery_travel,
                              max(1, int(_get(configuration, 'maxMarketOrdersPerTurn', 10)))) if turns else 0.
        entry = dict(target=(x, y), animal=tile['animal'], value=value)
        (jobs if value > 0 else retirements).append(entry)
    plan = _assign_feed_jobs(farm, private, jobs, turns)
    plan.update(jobs=jobs, retirements=retirements)
    return plan


def _project_service_workers(observation, cfg, commands):
    original, own, tpd, step, _ = _context(observation, cfg)
    farm, private = copy.deepcopy(original), copy.deepcopy(own)
    for index, command in enumerate(commands):
        core._apply_unit_action(farm, private, index, command, len(farm['tiles']),
                                step//tpd, tpd, int(_get(cfg, 'shedCapacity', 100)))
    return farm, private


def repair_feed_service(observation, configuration, action, prices=None, return_report=False):
    """Preserve the last executable rescue window across every search executor.

    A normal command is retained when its ordered native worker projection
    still covers all currently assigned profitable rescues. Otherwise reserve
    the feeding workers' first route steps. Market orders are then re-funded
    against the changed worker state, preserving rescue wheat and refusing
    discretionary growth while any profitable deadline remains uncovered.
    """
    cfg = configuration or {}
    plan = feed_service_plan(observation, cfg, prices)
    report = dict(jobs=plan['jobs'], retirements=plan['retirements'],
                  before_unassigned=plan['unassigned'], forced_workers=[])
    if not plan['jobs']:
        return (action, report) if return_report else action
    farm, private, tpd, step, end = _context(observation, cfg)
    count = len(farm.get('hands', []))+1
    commands = [copy.deepcopy(action.get('farmer', ['PASS']))]
    commands += copy.deepcopy(list(action.get('hands', []))[:count-1])
    commands += [['PASS'] for _ in range(count-len(commands))]
    turns_after = max(0, plan['turns']-1)
    def remaining(projected):
        return [job for job in plan['jobs']
                if not projected['tiles'][job['target'][1]][job['target'][0]].get('fed_today', False)]
    projected_farm, projected_private = _project_service_workers(observation, cfg, commands)
    pending = remaining(projected_farm)
    after = _assign_feed_jobs(projected_farm, projected_private, pending, turns_after)
    fed = {job['target'] for job in plan['jobs']} - {job['target'] for job in pending}
    if not set(plan['assigned']).issubset(fed | set(after['assigned'])):
        for index, route in enumerate(plan['routes']):
            if route['targets']:
                commands[index] = list(route['first'])
                report['forced_workers'].append(index)
        # Earlier unrelated pickups cannot consume a later feeder's reservation.
        available = max(0, int(private.get('shed', {}).get('WHEAT', 0)))
        for index, command in enumerate(commands):
            if command[:2] != ['PICKUP', 'WHEAT']:
                continue
            if not core._is_shed_adjacent(core._farmer_position(farm, index), len(farm['tiles'])):
                continue
            later = sum(r['first'][2] for r in plan['routes'][index+1:]
                        if r['targets'] and r['first'][:2] == ['PICKUP', 'WHEAT'])
            take = min(int(command[2]) if len(command)>2 else 1, max(0, available-later))
            commands[index] = ['PICKUP', 'WHEAT', take] if take else ['PASS']
            available -= take
        projected_farm, projected_private = _project_service_workers(observation, cfg, commands)
        pending = remaining(projected_farm)
        after = _assign_feed_jobs(projected_farm, projected_private, pending, turns_after)
    # Exact own-side funding mirrors legalize. No worker can use these purchases
    # or new hires until the next turn, and no next-turn capacity exists at dusk.
    market = copy.deepcopy(_get(observation, 'market', {}))
    capacity = max(0, int(_get(cfg, 'shedCapacity', 100)))
    hire_mult = max(0, int(_get(cfg, 'farmHandCostMult', core.FARM_HAND_COST_MULT)))
    orders = []
    for original_order in action.get('market', [])[:max(1, int(_get(cfg, 'maxMarketOrdersPerTurn', 10)))]:
        order = list(original_order)
        op = order[0]
        discretionary = op in ('BUY_ANIMAL', 'BUY_SEED', 'BUY_LAND') or (op == 'BUY_PRODUCT' and order[1] != 'WHEAT')
        if discretionary and after['unassigned']:
            continue
        if op == 'HIRE':
            if not turns_after:
                continue
            cost = core._hire_cost(projected_farm.get('hires_today', 0), hire_mult)
            if projected_farm['money'] < cost:
                continue
            core._do_hire(projected_farm, projected_private, len(farm['tiles']), hire_mult)
            orders.append(order)
        elif op == 'BUY_LAND':
            extra = len(projected_farm['unlocked_quadrants'])-1
            if extra >= len(core.LAND_PRICES) or projected_farm['money'] < core.LAND_PRICES[extra]:
                continue
            core._do_buy_land(projected_farm, len(farm['tiles']))
            orders.append(order)
        else:
            item, quantity = order[1], min(200, max(0, int(order[2])))
            if op == 'SELL' and item == 'WHEAT':
                # Conservative even when unreachable carriers hold other wheat.
                quantity = min(quantity, max(0, projected_private['shed'].get('WHEAT', 0)-len(pending)))
            filled = 0
            for _ in range(quantity):
                price = (core.CROPS[item]['seed'] if op == 'BUY_SEED' else
                         core.ANIMALS[item]['cost'] if op == 'BUY_ANIMAL' else
                         core.market_price(item, market['inventory'][item]-int(op == 'BUY_PRODUCT'), market.get('params')))
                if not core._commit_unit(op, item, price, projected_farm, projected_private, market, capacity):
                    break
                filled += 1
            if filled:
                orders.append([op, item, filled])
        if op == 'HIRE' or (op == 'BUY_PRODUCT' and order[1] == 'WHEAT'):
            after = _assign_feed_jobs(projected_farm, projected_private, pending, turns_after)
    result = dict(farmer=commands[0], hands=commands[1:], market=orders)
    report['after_unassigned'] = after['unassigned']
    return (result, report) if return_report else result


def schedule(observation, configuration=None, style="balanced", policy=None):
    """Produce coordinated worker commands followed by a funded market queue."""
    policy = policy or {}
    if policy.get("focus") == "liquidate":
        style = "liquidate"
    if style not in ("balanced", "growth", "liquidate"):
        style = "balanced"
    original, own, tpd, step, end = _context(observation, configuration)
    cfg = configuration or {}
    farm, private = copy.deepcopy(original), copy.deepcopy(own)
    private.setdefault("shed", {})
    private.setdefault("seeds", {})
    private.setdefault("inventories", [{}])
    size = len(farm["tiles"])
    day, hour = divmod(step, tpd)
    turns_left = min(tpd - hour, max(0, end - step + 1))
    remaining_days = max(0, end // tpd - day)
    capacity = max(0, int(_get(cfg, "shedCapacity", 100)))
    prices = _prices(observation, cfg)
    cv, av = _investment_values(prices, remaining_days, style)
    # Purchased seeds are already-owned obligations. The legacy short/spot
    # proxy must not veto execution of a funded multi-day commitment merely
    # because today's market differs from its future-price scenario.
    for crop, quantity in private["seeds"].items():
        if crop in core.CROPS and quantity > 0 and remaining_days >= core.CROPS[crop]["first_yield_day"] and style != "liquidate":
            cv[crop] = (max(1., cv[crop][0]), max(1., cv[crop][1]))
    crop_order = sorted(cv, key=lambda c: (-cv[c][1], c))
    animal_order = sorted(av, key=lambda a: (-av[a][1], a))
    if policy.get("item") in crop_order:
        crop_order.remove(policy["item"]); crop_order.insert(0, policy["item"])
    if policy.get("item") in animal_order:
        animal_order.remove(policy["item"]); animal_order.insert(0, policy["item"])
    positions = [farm["farmer"], *farm.get("hands", [])]
    access = core._shed_access_tiles(size)
    reserved, commands = set(), []
    planned_pickup = 0
    planned_animals = {a: 0 for a in core.ANIMALS}
    planned_seeds = {c: 0 for c in core.CROPS}

    for idx in range(len(positions)):
        pos = core._farmer_position(farm, idx)
        inv = core._farmer_inventory(private, idx)
        current_tiles = _tiles(farm)
        animals = [(x, y, t) for x, y, t in current_tiles if isinstance(t, dict) and t.get("animal") in core.ANIMALS]
        unfed = sum(not t.get("fed_today", False) for _, _, t in animals)
        # Distant or already-busy carriers cannot reserve every animal's feed.
        carried_feed = sum(min(i.get("WHEAT", 0), sum(
            not t.get("fed_today", False) and _distance(positions[j], (x,y))+1 <= turns_left
            for x,y,t in animals)) for j,i in enumerate(private["inventories"]) if j < len(positions))
        shed_pos = min(access, key=lambda p: (_distance(pos, p), p))
        best = (0.0, None, ["PASS"], ["PASS"])

        def offer(target, command, value, work=1, deadline=None):
            nonlocal best
            target = tuple(target)
            distance = _distance(pos, target)
            shed_command = command[0] in ("DROP", "PICKUP") or (command[0] == "PLACE" and command[1] in core.PRODUCTS)
            if (target in reserved and not shed_command) or value <= 0:
                return
            if deadline is not None and distance + work > deadline:
                return
            # The target operation must fit before the hand disappears at midnight.
            if distance + work > turns_left:
                return
            score = value / (1 + 0.65 * distance + 0.3 * (work - 1))
            if score > best[0]:
                best = (score, target, command if distance == 0 else _move(pos, target), command)

        carrier = next((a for a in animal_order if inv.get(a, 0) > 0), None)
        if carrier:
            kind = core.ANIMALS[carrier]["structure"]
            homes = [(x, y, t) for x, y, t in current_tiles
                     if (x, y) not in reserved and (t is None or (isinstance(t, dict) and t.get("kind") == kind and "animal" not in t))]
            homes.sort(key=lambda p: (0 if p[2] is not None else 1, _distance(pos, p), p[1], p[0]))
            if homes:
                x, y, tile = homes[0]
                offer((x, y), ["PLACE", carrier] if tile else ["BUILD_" + kind],
                      200 + core.ANIMALS[carrier]["cost"] * 0.4)

        for x, y, tile in current_tiles:
            target = (x, y)
            if tile is None:
                if carrier:
                    continue
                for crop in crop_order:
                    if private["seeds"].get(crop, 0) > planned_seeds[crop] and cv[crop][0] > 0 and turns_left > 1:
                        offer(target, ["PLANT", crop], 25 + min(85, cv[crop][1]) * (1.2 if style == "growth" else 1), work=2)
                        break
                continue
            if not isinstance(tile, dict):
                continue
            crop, animal = tile.get("crop"), tile.get("animal")
            if crop in core.CROPS:
                data = core.CROPS[crop]
                age = day - tile.get("planted_day", day)
                units = tile.get("yield_units", 0)
                watered = tile.get("watered_today", False)
                mature = age >= data["first_yield_day"] and units > 0
                window = (data["max_yield_day"] + 1) // 2 <= age <= data["max_yield_day"]
                can_increase = not data["ongoing"] and window and units < data["max_yield"]
                final = end - step < tpd
                if mature and (data["ongoing"] or age >= data["max_yield_day"] or units >= data["max_yield"] or final):
                    if not watered and can_increase and turns_left >= 2:
                        offer(target, ["WATER"], 100 + prices[crop] * (units + 1) * 0.6, work=2)
                    else:
                        delivery = min(_distance(target, p) for p in access) + 1 if remaining_days == 0 else 0
                        offer(target, ["HARVEST"], 85 + prices[crop] * units * 0.6, work=1 + delivery)
                if not watered and remaining_days > 0:
                    risk = tile.get("consecutive_unwatered", 0) >= 1
                    future = _crop_returns(crop, remaining_days, prices, age, units)
                    value = (45 + min(200, future * 0.2)) if risk else 9
                    if can_increase:
                        value += prices[crop] * 0.65
                    offer(target, ["WATER"], value)
                if inv.get("FERTILIZER", 0) and tile.get("fertilized_until_day", -1) < day and remaining_days:
                    bonus = (min(3, max(0, data["max_yield_day"] - age + 1)) if not data["ongoing"] and window else
                             min(3, 3 / max(1, data["interval"])) if data["ongoing"] and age + 3 >= data["first_yield_day"] else 0)
                    offer(target, ["FERTILIZE"], max(0, bonus * prices[crop] * 0.6 - prices["FERTILIZER"]))
                exhausted = (data["ongoing"] and age >= data["first_yield_day"] + 3 * data["interval"] and units == 0)
                if exhausted and any(private["seeds"].get(c, 0) and cv[c][0] > 0 for c in crop_order):
                    offer(target, ["DIG"], 30)
            elif animal in core.ANIMALS:
                data = core.ANIMALS[animal]
                product = data["product"]
                units = tile.get("yield_units", 0)
                if units:
                    delivery = min(_distance(target, p) for p in access) + 1 if remaining_days == 0 else 0
                    offer(target, ["HARVEST"], 90 + prices[product] * units * 0.65, work=1 + delivery)
                if not tile.get("fed_today", False) and inv.get("WHEAT", 0) and remaining_days:
                    urgency = 120 if tile.get("consecutive_unfed", 0) else 60
                    offer(target, ["FEED"], urgency + min(150, prices[product] * 0.75))
                if not tile.get("cared_today", False) and tile.get("fed_today", False) and remaining_days:
                    offer(target, ["CARE"], 20 + prices[product] * 0.65 / data["interval"])
                if tile.get("fertilizer_available", False):
                    delivery = min(_distance(target, p) for p in access) + 1 if remaining_days == 0 else 0
                    offer(target, ["COLLECT_FERTILIZER"], 15 + prices["FERTILIZER"] * 0.8, work=1 + delivery)
            elif tile.get("kind") == "WEED" and (carrier or any(private["seeds"].get(c, 0) and cv[c][0] > 0 for c in crop_order)):
                offer(target, ["DIG"], 35)

        # Supplies are physically owned by this worker only after an actual pickup.
        if not carrier:
            for animal in animal_order:
                if private["shed"].get(animal, 0) > planned_animals[animal] and remaining_days >= core.ANIMALS[animal]["first_yield_day"]:
                    space = any(t is None or (isinstance(t, dict) and t.get("kind") == core.ANIMALS[animal]["structure"] and "animal" not in t)
                                for _, _, t in current_tiles)
                    if space:
                        offer(shed_pos, ["PICKUP", animal, 1], 180)
                        break
        need = max(0, unfed - carried_feed - planned_pickup)
        if not inv.get("WHEAT", 0) and private["shed"].get("WHEAT", 0) and need and remaining_days:
            quantity = min(3, need, private["shed"]["WHEAT"])
            offer(shed_pos, ["PICKUP", "WHEAT", quantity], 130 + 10 * quantity)
        # Preserve animal/feed cargo when depositing saleable products.
        saleable = {p: n for p, n in inv.items() if p in core.PRODUCTS and n > 0
                    and not (p == "WHEAT" and unfed and remaining_days)}
        if saleable and sum(private["shed"].values()) < capacity:
            item = max(saleable, key=lambda p: (saleable[p] * prices[p], p))
            value = sum(n * prices[p] for p, n in saleable.items())
            terminal = end - step < tpd
            # Native midnight deposits every worker's inventory from anywhere.
            # Return early only for funding, overflow, or terminal liquidation;
            # otherwise finish the local production tour instead of yo-yoing.
            total_cargo = sum(sum(i.values()) for i in private["inventories"])
            room = capacity-sum(private["shed"].values())
            feed_bill = max(0, unfed-carried_feed)*prices["WHEAT"]
            urgent_cash = farm["money"] < max(12, feed_bill+4)
            overflow = total_cargo > room
            priority = (35+value*1.1 if terminal else
                        28+value*0.55 if urgent_cash or overflow else
                        8+value*0.04 if _distance(pos, shed_pos)==0 else 0)
            # DROP destroys overflow. PLACE preserves what cannot fit.
            all_saleable = len(saleable) == len(inv)
            command = ["DROP"] if all_saleable and sum(inv.values()) <= room else ["PLACE", item, min(saleable[item], room)]
            offer(shed_pos, command, priority)
        _, target, command, intended = best
        if target is not None and tuple(pos) != target:
            # Reserve tasks, not worker locations: collocated work is legal.
            if intended[0] not in ("DROP", "PICKUP"):
                reserved.add(target)
            if intended[:2] == ["PICKUP", "WHEAT"]:
                planned_pickup += intended[2]
            elif intended[0] == "PICKUP" and intended[1] in planned_animals:
                planned_animals[intended[1]] += intended[2]
            elif intended[0] == "PLANT":
                planned_seeds[intended[1]] += 1
        core._apply_unit_action(farm, private, idx, command, size, day, tpd, capacity)
        commands.append(command)

    orders = _market(observation, cfg, farm, private, prices, cv, av, style,
                     tpd, hour, remaining_days, turns_left, capacity, policy)
    action = {"farmer": commands[0], "hands": commands[1:], "market": orders}
    return repair_feed_service(observation, cfg, action, prices=prices)


def _market(observation, cfg, farm, private, prices, cv, av, style,
            tpd, hour, days, turns_left, capacity, policy=None):
    """Budget only after workers. Project each order, including Fibonacci hires."""
    market = copy.deepcopy(_get(observation, "market", {}))
    market.setdefault("inventory", {p: core.MARKET_I0 for p in core.PRODUCTS})
    orders = []
    limit = max(1, int(_get(cfg, "maxMarketOrdersPerTurn", 10)))
    size = len(farm["tiles"])
    hire_mult = max(0, int(_get(cfg, "farmHandCostMult", core.FARM_HAND_COST_MULT)))

    def order(op, item=None, quantity=1, reserve=0):
        if len(orders) >= limit or quantity <= 0:
            return 0
        if op in ("HIRE", "BUY_LAND"):
            cost = core._hire_cost(farm["hires_today"], hire_mult) if op == "HIRE" else core.LAND_PRICES[len(farm["unlocked_quadrants"]) - 1]
            if farm["money"] < cost + reserve:
                return 0
            (core._do_hire(farm, private, size, hire_mult) if op == "HIRE" else core._do_buy_land(farm, size))
            orders.append([op])
            return 1
        done = 0
        for _ in range(int(quantity)):
            if op == "BUY_SEED":
                price = core.CROPS[item]["seed"]
            elif op == "BUY_ANIMAL":
                price = core.ANIMALS[item]["cost"]
            else:
                stock = market["inventory"][item] - (1 if op == "BUY_PRODUCT" else 0)
                price = core.market_price(item, stock, market.get("params"))
            if op != "SELL" and farm["money"] < price + reserve:
                break
            if not core._commit_unit(op, item, price, farm, private, market, capacity):
                break
            done += 1
        if done:
            orders.append([op, item, done])
        return done

    tiles = _tiles(farm)
    animals = [t for _, _, t in tiles if isinstance(t, dict) and t.get("animal") in core.ANIMALS]
    crops = [t for _, _, t in tiles if isinstance(t, dict) and t.get("crop") in core.CROPS]
    unplaced = sum(private["shed"].get(a, 0) + sum(i.get(a, 0) for i in private["inventories"]) for a in core.ANIMALS)
    feed_held = sum(i.get("WHEAT", 0) for i in private["inventories"])
    animal_count = len(animals) + unplaced
    feed_reserve = max(0, min(capacity // 3, animal_count * min(2, days)) - feed_held)
    # Sell deposits made by this turn's workers, but never their still-carried goods.
    products = sorted(core.PRODUCTS, key=lambda p: (-private["shed"].get(p, 0) * prices[p], p))
    for item in products:
        qty = private["shed"].get(item, 0) - (feed_reserve if item == "WHEAT" else 0)
        order("SELL", item, max(0, qty))
    if turns_left <= 1:
        return orders
    # Feed commitments are funded before discretionary growth.
    missing_feed = max(0, feed_reserve - private["shed"].get("WHEAT", 0))
    order("BUY_PRODUCT", "WHEAT", missing_feed, reserve=2)
    # The remaining queue is generated against complete observed commitments.
    # All worker effects and preceding sales/feed purchases are already included.
    projected = dict(observation)
    projected["farms"] = list(_get(observation, "farms", []))
    projected["farms"][int(_get(observation, "player", 0))] = farm
    projected["private"] = private
    projected["market"] = market
    focus = (policy or {}).get("item")
    can_expand = style != "liquidate" and days >= 2 and turns_left >= 4
    empty = sum(t is None or (isinstance(t, dict) and t.get("kind") == "WEED") for _,_,t in tiles)
    seed_stock = sum(private["seeds"].values())
    # A bounded pending work queue prevents purchasing a whole season twice.
    pending = seed_stock+unplaced
    planting_slots = max(0, empty-pending)
    queue_room = max(0, min(8, (turns_left*max(2,len(farm["hands"])+1))//4)-pending)
    # Current execution needs only an observed one-day service list. Do not
    # rebuild whole-season valuations on every movement/maintenance tick.
    day = int(_get(observation, "step", 0))//tpd
    work = pending*4
    for x,y,tile in tiles:
        if not isinstance(tile, dict):
            continue
        tasks = 0
        if tile.get("crop") in core.CROPS:
            data = core.CROPS[tile["crop"]]
            age = day-tile.get("planted_day", day)
            tasks += bool(days) and not tile.get("watered_today", False)
            tasks += bool(tile.get("yield_units", 0)) and age >= data["first_yield_day"]
        elif tile.get("animal") in core.ANIMALS:
            tasks += 1.25*(bool(days) and not tile.get("fed_today", False))
            tasks += bool(days) and not tile.get("cared_today", False)
            tasks += bool(tile.get("yield_units", 0))+bool(tile.get("fertilizer_available", False))
        if tasks:
            ingress = min(_distance((x,y), p) for p in [farm["farmer"], *farm.get("hands", [])])
            work += tasks+min(2, ingress)
    # Demand is optional when its marginal executable value is below wages.
    # Existing workers claim reachable bundles first, preventing the shrinking
    # clock from multiplying hires for the same still-unfinished assets.
    hire_audit = commitments.service_hires(projected, cfg, prices)
    for proposed in hire_audit:
        if not order("HIRE", reserve=2):
            break
    # Animal custody is serial, while distinct owned crop slots may execute
    # concurrently inside the bounded, explicitly staffed seed cohort.
    if not can_expand or not queue_room or unplaced:
        return orders
    shortlist = [focus] if focus in core.CROPS or focus in core.ANIMALS else True
    book = commitments.build_book(projected, cfg, style=style,
                                 regime=(policy or {}).get("regime", "central"),
                                 include_candidates=shortlist)
    candidates = [c for c in book["candidates"] if c["score"] > 0 and c["net"] > 0
                  and (c["kind"] != "crop" or c["quantity"] <= queue_room)]
    if focus:
        candidates = [c for c in candidates if c["item"] == focus]
    if (policy or {}).get("quantity"):
        candidates = [c for c in candidates if c["kind"] != "crop" or c["quantity"] <= int(policy["quantity"])]
    if (policy or {}).get("focus") == "crop":
        candidates = [c for c in candidates if c["kind"] in ("crop", "land")]
    elif (policy or {}).get("focus") == "animal":
        candidates = [c for c in candidates if c["kind"] == "animal"]
    for candidate in candidates:
        # This cash trough includes every currently owned crop/animal's future
        # feed/wages and the entire prospective programme, before its receipts.
        if farm["money"]+1e-9 < candidate["required_cash"]:
            continue
        item, kind = candidate["item"], candidate["kind"]
        if kind == "land":
            if pending or planting_slots > 1:
                continue
            reserve = max(book["reserve"], candidate["upfront"]-core.LAND_PRICES[len(farm["unlocked_quadrants"])-1])
            if order("BUY_LAND", reserve=reserve):
                # Seeds are purchased next turn against the newly observed slots.
                break
        elif kind == "animal":
            if unplaced or planting_slots < 1:
                continue
            price = core.ANIMALS[item]["cost"]
            reserve = max(2, candidate["required_cash"]-price)
            if order("BUY_ANIMAL", item, 1, reserve=reserve):
                order("BUY_PRODUCT", "WHEAT", min(2, days), reserve=max(2, book["reserve"]))
                break
        elif planting_slots:
            # One marginal bundle per turn; owned seed stock is credited next
            # call. Root policy persists, so this is progressive portfolio fill.
            quantity = candidate.get("quantity", 1)
            price = core.CROPS[item]["seed"]*quantity
            if order("BUY_SEED", item, quantity, reserve=max(2,candidate["required_cash"]-price)):
                # A real cohort is staffed against its now-owned seeds, after
                # their purchase, rather than serialized behind one planter.
                for proposed in commitments.service_hires(projected, cfg, prices):
                    if not order("HIRE", reserve=2):
                        break
                break
    return orders
'''
_mod = _types.ModuleType(_PACKAGE.__name__ + ".scheduler")
_mod.__package__ = _PACKAGE.__name__
_sys.modules[_mod.__name__] = _mod
setattr(_PACKAGE, "scheduler", _mod)
exec(compile(_SOURCE_SCHEDULER, "<general_v3/scheduler.py>", "exec"), _mod.__dict__)

# BEGIN SOURCE engine.py
_SOURCE_ENGINE = '''"""Observation-only receding-horizon search with explicit imperfect-information models.

All simulated transitions are native rules. Leaf asset values and hidden inventory,
future events and rival decisions are assumptions, not measured final scores.
"""
from __future__ import annotations

import copy
import json
import math
import time
from dataclasses import dataclass, asdict

from . import native_core as core
from . import scheduler
from . import beliefs
from . import commitments
from . import reference_scheduler


class Box(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key) from None

    def __setattr__(self, key, value):
        self[key] = value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def clean_config(configuration=None, observation=None):
    """Only rule fields, never episode seed, identity, or arbitrary agent metadata."""
    defaults = dict(episodeSteps=720, boardSize=10, turnsPerDay=24,
                    maxMarketOrdersPerTurn=10, farmHandCostMult=1, shedCapacity=100,
                    townShopSellInterval=4, townCenterSellInterval=24,
                    townShopUnlockInterval=3, weedSpawnChance=0.005)
    cfg = configuration or {}
    for key in defaults:
        if key in cfg:
            defaults[key] = cfg[key]
    if observation:
        defaults['boardSize'] = len(observation['farms'][int(observation['player'])]['tiles'])
    for key in defaults:
        if key != 'weedSpawnChance':
            defaults[key] = int(defaults[key])
    defaults['weedSpawnChance'] = float(defaults['weedSpawnChance'])
    if (defaults['episodeSteps'] < 2 or defaults['boardSize'] < 2 or
            defaults['turnsPerDay'] < 1 or defaults['shedCapacity'] < 1 or
            defaults['maxMarketOrdersPerTurn'] < 1):
        raise ValueError('Invalid rule configuration')
    return defaults


def visible_observation(observation):
    """Enforce the information boundary at entry to every policy and search."""
    keys = ('farms', 'private', 'market', 'town', 'step', 'player')
    result = {key: copy.deepcopy(observation[key]) for key in keys}
    if int(result['player']) not in (0, 1) or len(result['farms']) != 2:
        raise ValueError('Kaggriculture requires two farms and seat 0 or 1')
    result['step'] = int(result['step'])
    if result['step'] < 0:
        raise ValueError('Negative step')
    return result


@dataclass(frozen=True)
class SearchConfig:
    horizon: int = 2
    max_candidates: int = 6
    max_transitions: int = 48
    seconds: float = 0.70
    event_horizon: int = 4
    finalists: int = 2
    cache: bool = True
    risk_weight: float = 0.35

    def __post_init__(self):
        for key in ('horizon','max_candidates','max_transitions','event_horizon','finalists'):
            if type(getattr(self,key)) is not int:
                raise ValueError(key+' must be an integer')
        if not 1 <= self.horizon <= 96:
            raise ValueError('horizon must be in [1, 96]')
        if not 1 <= self.max_candidates <= 64:
            raise ValueError('max_candidates must be in [1, 64]')
        if not 1 <= self.max_transitions <= 20000:
            raise ValueError('max_transitions must be in [1, 20000]')
        if not math.isfinite(self.seconds) or self.seconds < 0:
            raise ValueError('seconds must be finite and nonnegative (0 means node-only)')
        if not 0 <= self.event_horizon <= 96 or not 1 <= self.finalists <= 8:
            raise ValueError('invalid event extension bounds')
        if not 0 <= self.risk_weight <= 1:
            raise ValueError('risk_weight must be in [0, 1]')


# Hypothetical seeds drive only native future events; never evaluator seed input.
# Long-horizon demand regimes matter even when a short rollout crosses no shop.
SCENARIOS = (
    dict(name='low_supply_low_demand', stock_scale=0.25, rival_style='balanced', future_seed=846101, regime='low_demand'),
    dict(name='central_reactive', stock_scale=1.0, rival_style='reference', future_seed=846103, regime='central'),
    dict(name='high_supply_high_demand', stock_scale=1.8, rival_style='growth', future_seed=846107, regime='high_demand'),
)


def clone(value):
    """Copy JSON-like state, preserving insertion order and immutable rule data.

    This does not memoize arbitrary aliases. clone_world explicitly restores the
    authoritative shared public objects used by both native observations.
    """
    if isinstance(value, dict):
        # Foreign mapping subclasses (notably Kaggle Struct) may accept only
        # keyword arguments or maintain stale attribute mirrors. Normalize them
        # to plain JSON dictionaries; retain only our own attribute-aware Box.
        cls = Box if isinstance(value, Box) else dict
        return cls((key, clone(item)) for key, item in value.items())
    if isinstance(value, list):
        return [clone(item) for item in value]
    if isinstance(value, tuple):
        return tuple(clone(item) for item in value)
    return value


def frozen(value):
    """Complete hashable state key; preserve ordered inventories and rule fields."""
    if isinstance(value, dict):
        return tuple((key, frozen(item)) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return tuple(frozen(item) for item in value)
    return value


def clone_world(world):
    state, env = world
    public = clone({key: state[0].observation[key] for key in ('farms','market','town','step','day','hour')})
    copied = [Box(status=entry.status, reward=entry.reward, action=clone(entry.action),
                  observation=Box(**public, player=p, private=clone(entry.observation.private)))
              for p, entry in enumerate(state)]
    return copied, Box(configuration=env.configuration, info=dict(env.info), done=env.done, summary=getattr(env,'summary',None))


def guess_private(public_farm, capacity, scale):
    # Backwards-compatible public helper. Full engine uses age/config/history.
    return beliefs.estimate_private(public_farm, {'shedCapacity':capacity}, scale)


def make_world(observation, configuration, scenario, summary=None):
    public = clone({key: observation[key] for key in ('farms', 'market', 'town', 'step')})
    seat = int(observation['player'])
    public['day'], public['hour'] = divmod(public['step'], configuration['turnsPerDay'])
    cfg = dict(configuration, currentStep=public['step'])
    other = beliefs.estimate_private(public['farms'][1-seat], cfg, scenario['stock_scale'], summary)
    state = [Box(status='ACTIVE', reward=0, action={}, observation=Box(**public, player=p,
                 private=clone(observation['private']) if p == seat else other)) for p in (0, 1)]
    return state, Box(configuration=Box(**configuration), info={'seed': scenario['future_seed']}, done=False, summary=summary)


def idle_action(observation):
    seat = int(observation.get('player', 0))
    try:
        count = len(observation['farms'][seat].get('hands', []))
    except (KeyError, IndexError, TypeError):
        count = 0
    return dict(farmer=['PASS'], hands=[['PASS'] for _ in range(count)], market=[])


def unit_fingerprint(farm, private, index):
    """Only state a worker action can mutate, checked against native contracts."""
    pos = core._farmer_position(farm, index)
    if pos is None:
        return None
    tile = farm['tiles'][pos[1]][pos[0]]
    inv = private.get('inventories', [])
    return (tuple(pos), frozen(tile), frozen(private.get('seeds', {})),
            frozen(private.get('shed', {})), frozen(inv[index] if index < len(inv) else {}))


def legalize(observation, action, cfg):
    """Clip worker requests to available units and resources before atomic validation.

    Sequential exact own-worker projection prevents stale shared-tile, seed and
    pickup conflicts. Market quantities remain bounded; execution is modeled by
    the joint transition because the rival may change prices simultaneously.
    """
    seat = int(observation['player'])
    farm = copy.deepcopy(observation['farms'][seat])
    private = copy.deepcopy(observation['private'])
    worker_count = 1 + len(farm.get('hands', []))
    raw = [action.get('farmer', ['PASS'])] + list(action.get('hands', []))[:worker_count-1]
    raw += [['PASS'] for _ in range(worker_count-len(raw))]
    units = []
    for index, command in enumerate(raw):
        if not isinstance(command, list) or not command:
            command = ['PASS']
        else:
            command = copy.deepcopy(command)
        before = unit_fingerprint(farm, private, index)
        try:
            core._apply_unit_action(farm, private, index, command, cfg['boardSize'],
                                    observation['step']//cfg['turnsPerDay'], cfg['turnsPerDay'], cfg['shedCapacity'])
        except (TypeError, ValueError, IndexError, KeyError):
            raise ValueError('Malformed generated worker command') from None
        if unit_fingerprint(farm, private, index) == before:
            command = ['PASS']
        units.append(command)
    market = []
    for order in action.get('market', [])[:cfg['maxMarketOrdersPerTurn']]:
        if not isinstance(order, list) or not order:
            continue
        if order[0] in ('HIRE', 'BUY_LAND'):
            market.append([order[0]])
        elif (len(order) >= 3 and order[0] in ('SELL', 'BUY_SEED', 'BUY_PRODUCT', 'BUY_ANIMAL')
              and isinstance(order[2], (int, float)) and math.isfinite(order[2])):
            item, qty = order[1], max(0, min(200, int(order[2])))
            allowed = (core.PRODUCTS if order[0] == 'SELL' else core.CROPS if order[0] == 'BUY_SEED'
                       else ('WHEAT', 'FERTILIZER') if order[0] == 'BUY_PRODUCT' else core.ANIMALS)
            if item in allowed and qty:
                market.append([order[0], item, qty])
    # Make every emitted order funded against the exact post-worker own state.
    # Concurrent rival trades remain uncertainty, represented in joint rollouts.
    projected_market = copy.deepcopy(observation['market'])
    funded = []
    for order in market:
        op = order[0]
        if op == 'HIRE':
            price = core._hire_cost(farm.get('hires_today', 0), cfg['farmHandCostMult'])
            if farm['money'] >= price:
                core._do_hire(farm, private, cfg['boardSize'], cfg['farmHandCostMult'])
                funded.append(order)
        elif op == 'BUY_LAND':
            extra = len(farm['unlocked_quadrants']) - 1
            if extra < len(core.LAND_PRICES) and farm['money'] >= core.LAND_PRICES[extra]:
                core._do_buy_land(farm, cfg['boardSize'])
                funded.append(order)
        else:
            item, quantity = order[1:]
            filled = 0
            for _ in range(quantity):
                if op == 'BUY_SEED':
                    price = core.CROPS[item]['seed']
                elif op == 'BUY_ANIMAL':
                    price = core.ANIMALS[item]['cost']
                else:
                    stock = projected_market['inventory'][item] - int(op == 'BUY_PRODUCT')
                    price = core.market_price(item, stock, projected_market.get('params'))
                if not core._commit_unit(op, item, price, farm, private, projected_market, cfg['shedCapacity']):
                    break
                filled += 1
            if filled:
                funded.append([op, item, filled])
    return dict(farmer=units[0], hands=units[1:], market=funded)


def schedule_policy(obs, cfg, style='balanced', policy=None):
    if (policy or {}).get('executor') == 'reference':
        action = reference_scheduler.schedule(obs, cfg, style)
        return scheduler.repair_feed_service(obs, cfg, action)
    return scheduler.schedule(obs, cfg, style, policy)


class DecisionCache:
    """Bounded per-decision memo; no cross-game policy or private-state leakage."""
    def __init__(self, enabled=True, maximum=512):
        self.enabled, self.maximum = enabled, maximum
        self.schedules, self.values = {}, {}
        self.hits = self.misses = 0

    def schedule(self, obs, cfg, style, policy=None):
        if not self.enabled:
            return schedule_policy(obs, cfg, style, policy)
        key = (frozen(obs), frozen(cfg), style, frozen(policy))
        if key in self.schedules:
            self.hits += 1
            return clone(self.schedules[key])
        self.misses += 1
        action = schedule_policy(obs, cfg, style, policy)
        if len(self.schedules) < self.maximum:
            self.schedules[key] = clone(action)
        return action


def advance(world, seat, first_action, scenario, policy=None, cache=None):
    state, env = world
    own, rival, cfg = state[seat].observation, state[1-seat].observation, env.configuration
    schedule = cache.schedule if cache is not None else schedule_policy
    state[seat].action = first_action if first_action is not None else schedule(own, cfg, 'balanced', policy)
    rival_policy = {'focus':'diverse', 'item':None, 'regime':scenario.get('regime','central')}
    if scenario['rival_style']=='reference':
        rival_policy['executor']='reference'
    state[1-seat].action = (idle_action(rival) if scenario['rival_style']=='passive' else
                           schedule(rival, cfg, 'balanced' if scenario['rival_style']=='reference' else scenario['rival_style'], rival_policy))
    previous_step = int(own.step)
    core.interpreter(state, env)
    for entry in state:
        entry.observation.step = previous_step + 1
    return world


def inventory_value(observation, cfg):
    """Conservative realizable spot liquidation value, including price impact."""
    private = observation['private']
    total = dict(private.get('shed', {}))
    remaining = cfg['episodeSteps'] - 1 - int(observation['step'])
    for inv in private.get('inventories', []):
        for item, qty in inv.items():
            # Carried goods require transfer or a midnight before the final action.
            if remaining > 1:
                total[item] = total.get(item, 0) + qty
    market = observation['market']
    value = 0.0
    for item in core.PRODUCTS:
        supply = market['inventory'][item]
        for _ in range(min(cfg['shedCapacity']*2, int(total.get(item, 0)))):
            price = core.market_price(item, supply, market.get('params'))
            value += price
            supply += int(price > 1)
    if remaining > 3:
        value += 0.25 * sum(core.CROPS[crop]['seed'] * qty for crop, qty in private.get('seeds', {}).items() if crop in core.CROPS)
        value += 0.2 * sum(core.ANIMALS[item]['cost'] * total.get(item, 0) for item in core.ANIMALS)
    return value


def future_assets(observation, cfg, regime='central', summary=None):
    """Net realizable continuation estimate, charging feed, wages and delivery.

    Capital already paid is sunk; unplaced inputs are credited only through an
    executable future lifecycle. No terminal automatic liquidation is assumed.
    """
    return float(commitments.asset_value(observation, cfg, regime=regime, summary=summary))


def evaluate(world, seat, scenario=None, cache=None):
    state, env = world
    farms = state[0].observation.farms
    cash = float(farms[seat]['money'] - farms[1-seat]['money'])
    if state[seat].status == 'DONE':
        return cash
    regime = (scenario or {}).get('regime','central')
    assets = []
    for p in (seat, 1-seat):
        obs = state[p].observation
        key = (frozen(obs), frozen(env.configuration), regime, frozen(getattr(env,'summary',None)))
        if cache is not None and cache.enabled and key in cache.values:
            value = cache.values[key]; cache.hits += 1
        else:
            value = future_assets(obs, env.configuration, regime, getattr(env,'summary',None))
            if cache is not None and cache.enabled and len(cache.values)<cache.maximum:
                cache.values[key] = value
        assets.append(value)
    return cash + assets[0] - assets[1]


def candidate_programs(observation, cfg, maximum=6, summary=None):
    """Funded production programs plus bounded tactical branches.

    A program carries its economic focus through every simulated future turn.
    Different programs may intentionally share a first action; their exact
    common transition is cached rather than conflated with an identical plan.
    """
    book = commitments.build_book(observation, cfg, summary=summary)
    policies = commitments.market_options(observation, cfg, book)
    result, seen = [], set()
    def add(action, name, policy):
        # Every executor and tactical market variant must preserve the same
        # physically feasible survival commitments before native legalization.
        guarded = scheduler.repair_feed_service(observation, cfg, action)
        normalized = legalize(observation, guarded, cfg)
        key = (frozen(normalized), frozen(policy))
        if key not in seen and len(result)<maximum:
            seen.add(key); result.append((name, normalized, policy))
    # Retain the previous general scheduler as one executable mixed portfolio,
    # not a replay or external fallback. New valuation/scenarios/search compare
    # it on exactly the same footing as the new funded commitment programmes.
    reference_policy={'executor':'reference','focus':'diverse','item':None,'regime':'central'}
    add(reference_scheduler.schedule(observation,cfg,'balanced'),
        'retained_mixed_program',reference_policy)
    for index, policy in enumerate(policies):
        style = 'liquidate' if policy.get('focus')=='liquidate' else 'balanced'
        add(scheduler.schedule(observation,cfg,style,policy),
            'commit_'+str(index)+'_'+str(policy.get('focus'))+'_'+str(policy.get('item')), policy)
    if not result:
        policy={'focus':'diverse','item':None,'regime':'central'}
        add(scheduler.schedule(observation,cfg,'balanced',policy),'balanced',policy)
    base, policy = result[0][1:]
    # Preserve deliberate wait/liquidation alternatives without unbounded tuples.
    liquidation={'focus':'liquidate','item':None,'regime':'central'}
    add(scheduler.schedule(observation,cfg,'liquidate',liquidation),'liquidate',liquidation)
    # Expensive daily hands are optional financial decisions. Keeping a
    # no-hire branch exposes their cash cost to exact joint continuations,
    # particularly when late-day service demand cannot all be profitably met.
    if any(order[0]=='HIRE' for order in base['market']):
        add(dict(base,market=[order for order in base['market'] if order[0]!='HIRE']),
            'defer_new_hires',policy)
    if len(base['market'])>1:
        add(dict(base,market=list(reversed(base['market']))),'reverse_market_program',policy)
    for i, order in enumerate(base['market']):
        if order[0]=='SELL' and order[2]>=2:
            orders=clone(base['market']);orders[i][2]=max(1,order[2]//2)
            add(dict(base,market=orders),'partial_sale_'+order[1],policy)
            break
    return result, book


def candidates(observation, cfg, maximum=6):
    return [(name, action) for name, action, _ in candidate_programs(observation,cfg,maximum)[0]]


def decide(observation, configuration=None, settings=None, belief_summary=None):
    settings = settings or SearchConfig()
    started = time.perf_counter()
    obs = visible_observation(observation)
    cfg = clean_config(configuration, obs)
    obs['day'], obs['hour'] = divmod(obs['step'], cfg['turnsPerDay'])
    if obs['step'] >= cfg['episodeSteps']-1:
        return idle_action(obs),dict(terminal=True,transitions=0,elapsed_seconds=time.perf_counter()-started)
    seat=int(obs['player'])
    roots,book=candidate_programs(obs,cfg,settings.max_candidates,belief_summary)
    chosen=roots[0][1]
    cache=DecisionCache(settings.cache)
    # Search cannot change the emitted action when every generated programme
    # agrees. Avoid paying for indistinguishable root decisions on maintenance
    # turns; this is explicit action-set equivalence, never a strength shortcut.
    if len({frozen(action) for _,action,_ in roots}) == 1:
        return chosen, dict(scope='common_generated_action',settings=asdict(settings),
                            scenarios=[],belief=belief_summary or {},transitions=0,
                            completed_candidates=0,requested_horizon=min(settings.horizon,cfg['episodeSteps']-1-obs['step']),
                            budget_exhausted=False,selected=roots[0][0],candidate_results=[],extensions=[],
                            fallback_unsearched=False,forced_common_action=True,generated_programs=len(roots),
                            cache_hits=0,schedule_evaluations=0,
                            elapsed_seconds=time.perf_counter()-started)
    worlds=[make_world(obs,cfg,s,belief_summary) for s in SCENARIOS]
    initial_scores=[evaluate(w,seat,s,cache) for w,s in zip(worlds,SCENARIOS)]
    horizon=min(settings.horizon,cfg['episodeSteps']-1-obs['step'])
    report=dict(scope='persistent_commitment_programs_equal_scenario_rollouts',settings=asdict(settings),
                scenarios=[dict(s,hidden_stock_assumption=clone(w[0][1-seat].observation.private['shed'])) for s,w in zip(SCENARIOS,worlds)],
                belief=belief_summary or {},transitions=0,completed_candidates=0,requested_horizon=horizon,
                budget_exhausted=False,selected=roots[0][0],candidate_results=[],extensions=[],
                value_warning='Native transitions are exact conditional on hypotheses; lifecycle coin-margin estimates are not guarantees or win probabilities.')
    def expired():
        return settings.seconds and time.perf_counter()-started>=settings.seconds
    def outcome(world,j,depth):
        farms=world[0][0].observation.farms
        return dict(name=SCENARIOS[j]['name'],completed_depth=depth,own_cash=farms[seat]['money'],
                    rival_cash=farms[1-seat]['money'],cash_margin=farms[seat]['money']-farms[1-seat]['money'],
                    heuristic_delta=evaluate(world,seat,SCENARIOS[j],cache)-initial_scores[j],
                    terminal=world[0][seat].status=='DONE')
    def score(outcomes):
        vals=[r['heuristic_delta'] for r in outcomes]
        return (1-settings.risk_weight)*sum(vals)/len(vals)+settings.risk_weight*min(vals)
    finished=[];first_cache={}
    for index,(name,action,policy) in enumerate(roots):
        if report['transitions']+horizon*len(SCENARIOS)>settings.max_transitions or expired():
            report['budget_exhausted']=True;break
        simulated=[];outcomes=[];complete=True
        for j,(initial,scenario) in enumerate(zip(worlds,SCENARIOS)):
            prefix=(j,frozen(action))
            if settings.cache and prefix in first_cache:
                world=clone_world(first_cache[prefix]);first_depth=1;cache.hits+=1
            else:
                world=clone_world(initial);first_depth=0
            for depth in range(first_depth,horizon):
                if expired():complete=False;report['budget_exhausted']=True;break
                advance(world,seat,action if depth==0 else None,scenario,policy,cache)
                report['transitions']+=1
                if depth==0 and settings.cache:first_cache[prefix]=clone_world(world)
            if not complete:break
            simulated.append(world);outcomes.append(outcome(world,j,horizon))
        if not complete:break
        utility=score(outcomes)
        row=dict(name=name,policy=policy,utility=utility,outcomes=outcomes)
        report['candidate_results'].append(row);report['completed_candidates']+=1
        finished.append((utility,index,simulated,row))
    if finished:
        finished.sort(key=lambda r:(r[0],-r[1]),reverse=True)
        _,index,_,_=finished[0];chosen=roots[index][1];report['selected']=roots[index][0]
        # Select finalists only after all shallow scenario sets complete. Deepen
        # them equally through an imminent day boundary, keeping the shallow
        # winner if a complete equal-depth finalist cohort cannot finish.
        event_depth=min(cfg['turnsPerDay']-obs['hour']+1,settings.event_horizon,
                        cfg['episodeSteps']-1-obs['step'])
        finalists=finished[:settings.finalists]
        extra=max(0,event_depth-horizon)
        needed=extra*len(SCENARIOS)*len(finalists)
        if extra and len(finalists)>1 and needed+report['transitions']<=settings.max_transitions and not expired():
            extensions=[];all_complete=True
            for _,index,simulated,row in finalists:
                outcomes=[]
                for j,(previous,scenario) in enumerate(zip(simulated,SCENARIOS)):
                    world=clone_world(previous)
                    for depth in range(horizon,event_depth):
                        if expired():all_complete=False;report['budget_exhausted']=True;break
                        advance(world,seat,None,scenario,roots[index][2],cache);report['transitions']+=1
                    if not all_complete:break
                    outcomes.append(outcome(world,j,event_depth))
                if not all_complete:break
                extensions.append(dict(name=roots[index][0],index=index,utility=score(outcomes),outcomes=outcomes))
            report['extensions_complete']=all_complete
            if all_complete:
                report['extensions']=extensions
                best=max(extensions,key=lambda r:(r['utility'],-r['index']))
                chosen=roots[best['index']][1];report['selected']=best['name']
    report['fallback_unsearched']=not finished
    report['cache_hits']=cache.hits;report['schedule_evaluations']=cache.misses
    report['generated_programs']=len(roots)
    report['commitment_summary']={key:book.get(key) for key in ('owned','reserve','assumptions')}
    report['elapsed_seconds']=time.perf_counter()-started
    return chosen,report


_LAST_REPORT = {}
_STATS = dict(calls=0, errors=0, transitions=0, budget_stops=0, unsearched_fallbacks=0, cache_hits=0, lifecycle_cache_hits=0, lifecycle_cache_misses=0, max_seconds=0.)
_BELIEF = beliefs.SupplyBelief()


def agent(observation, configuration=None):
    """Kaggle entry point; bounded public history resets on episode boundaries; no hidden inputs."""
    global _LAST_REPORT
    started=time.perf_counter()
    if int(observation.get('step',0))==0:
        commitments.clear_caches()
        for key in _STATS:
            _STATS[key]=0
    try:
        obs=visible_observation(observation)
        cfg=clean_config(configuration,obs)
        summary=_BELIEF.observe(obs,cfg)
        action,report=decide(obs,cfg,belief_summary=summary)
        _BELIEF.remember_action(action)
        _LAST_REPORT=report
        _STATS['transitions']+=report['transitions']
        _STATS['cache_hits']+=report.get('cache_hits',0)
        _STATS['budget_stops']+=int(report.get('budget_exhausted',False))
        _STATS['unsearched_fallbacks']+=int(report.get('fallback_unsearched',False))
    except Exception as error:
        _STATS['errors']+=1
        _LAST_REPORT={'error':type(error).__name__+': '+str(error),'fallback':'legal_idle'}
        action=idle_action(observation)
    _STATS['calls']+=1
    lifecycle_info=commitments.cache_info()
    _STATS['lifecycle_cache_hits']=lifecycle_info['hits']
    _STATS['lifecycle_cache_misses']=lifecycle_info['misses']
    _STATS['max_seconds']=max(_STATS['max_seconds'],time.perf_counter()-started)
    agent.telemetry=dict(_STATS)
    return action


agent.telemetry={}
'''
_mod = _types.ModuleType(_PACKAGE.__name__ + ".engine")
_mod.__package__ = _PACKAGE.__name__
_sys.modules[_mod.__name__] = _mod
setattr(_PACKAGE, "engine", _mod)
exec(compile(_SOURCE_ENGINE, "<general_v3/engine.py>", "exec"), _mod.__dict__)


def agent(observation, configuration=None):
    result = _PACKAGE.engine.agent(observation, configuration)
    agent.telemetry = dict(_PACKAGE.engine.agent.telemetry)
    return result


agent.telemetry = {}


def kaggle_general_engine_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
