"""
Kaggriculture competitive agent.

Strategy summary
-----------------
1. ECONOMICS: replicate the environment's exact price/yield formulas to rank
   crops/animals by steady-state profit-per-tile-per-day at *current* market
   prices, so planting choices adapt as prices move.
2. TASK ENGINE: every turn, scan the whole farm for actionable opportunities
   (water, harvest, feed, care, dig weed, plant, place animal, collect
   fertilizer) and greedily assign the nearest opportunity to each free unit
   (farmer + hands) via BFS shortest-path movement.
3. CAPITAL POLICY: keep seed/fertilizer/animal stock topped up, hire hands
   when there is more work than hands, buy land when payback is short enough
   for the remaining season, and throttle market sells so premium goods
   aren't dumped straight to the price floor.
"""

import math
from collections import deque

# ---------------------------------------------------------------------------
# Static game constants (mirrors the environment's kaggriculture.py exactly)
# ---------------------------------------------------------------------------

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

MARKET_I0 = 10000
PRICE_FLOOR = 1

MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "I0": MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base":  35, "I0": MARKET_I0, "T": 450, "below_func": "log",    "below_target": 0.20, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base":  60, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base":  50, "I0": MARKET_I0, "T": 332, "below_func": "linear", "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]

SEASON_DAYS = 30          # documented default season length
TURNS_PER_DAY = 24        # documented default


def _shape(func, x):
    x = max(0.0, x)
    if func == "linear": return x
    if func == "sq":     return x * x
    if func == "sqrt":   return math.sqrt(x)
    if func == "log":    return math.log(1.0 + x)
    if func == "log10":  return math.log10(1.0 + x)
    return x


def market_price(item, inventory, params=None):
    p = (params or MARKET_PARAMS)[item]
    base, I0, T = p["base"], p["I0"], p["T"]
    if inventory < I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, T)
        price = base + amp * _shape(f, I0 - inventory)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, T)
        price = base - amp * _shape(f, inventory - I0)
    return max(PRICE_FLOOR, int(round(price)))


def simulate_sell(item, qty, inventory, params=None):
    """Replicate the interpreter's unit-by-unit sell walk to get (total_revenue, marginal_price, new_inventory)."""
    inv = inventory
    total = 0
    marginal = 0
    for _ in range(qty):
        price = market_price(item, inv, params)
        total += price
        marginal = price
        if price > 1:
            inv += 1
    return total, marginal, inv


def max_qty_above_reserve(item, inventory, available, reserve_frac, params=None):
    """Largest qty (<= available) sellable while the marginal (last-unit) price stays
    >= reserve_frac * base price. Falls back to 0 if even 1 unit is below reserve."""
    base = (params or MARKET_PARAMS)[item]["base"]
    reserve = reserve_frac * base
    lo, hi = 0, available
    while lo < hi:
        mid = (lo + hi + 1) // 2
        _, marginal, _ = simulate_sell(item, mid, inventory, params)
        if marginal >= reserve:
            lo = mid
        else:
            hi = mid - 1
    return lo


# ---------------------------------------------------------------------------
# Economics: rank crops / animals by approximate steady-state profit/tile/day
# ---------------------------------------------------------------------------

def crop_profit_per_day(crop, price, fert_price, use_fertilizer):
    cd = CROPS[crop]
    if not cd["ongoing"]:
        window_start = (cd["max_yield_day"] + 1) // 2
        window_days = max(0, cd["max_yield_day"] - window_start + 1)
        bonus = 2 if use_fertilizer else 1
        yield_units = min(cd["max_yield"], 1 + window_days * bonus)
        fert_apps = math.ceil(window_days / 3) if use_fertilizer else 0
        cost = cd["seed"] + fert_apps * fert_price
        tile_days = cd["max_yield_day"] + 1
        return (yield_units * price - cost) / tile_days, yield_units
    else:
        # Ongoing crops (tomato/strawberry) are NOT indefinite income streams: they
        # produce exactly `max_yield` scheduled ticks (tomato: 4 daily ticks, ages
        # 8-11; strawberry: 4 ticks every other day, ages 10/12/14/16) and then decay
        # into a weed. Value them the same way as one-time crops: total yield over
        # the finite tile-days they actually occupy, not a perpetual daily rate.
        last_tick_age = cd["first_yield_day"] + (cd["max_yield"] - 1) * cd["interval"]
        tile_days = last_tick_age + 1
        yield_per_tick = 2 if use_fertilizer else 1
        total_yield = cd["max_yield"] * yield_per_tick
        fert_apps = math.ceil(tile_days / 3) if use_fertilizer else 0
        cost = cd["seed"] + fert_apps * fert_price
        return (total_yield * price - cost) / tile_days, yield_per_tick


def animal_profit_per_day(animal, product_price, wheat_price):
    ad = ANIMALS[animal]
    revenue_per_day = product_price / ad["interval"]
    feed_cost_per_day = wheat_price
    cost_amort = ad["cost"] / max(1, (SEASON_DAYS - ad["first_yield_day"]))
    return revenue_per_day - feed_cost_per_day - cost_amort


def crop_tile_days(crop):
    """Full occupancy span (planting day .. last productive day, inclusive)."""
    cd = CROPS[crop]
    if not cd["ongoing"]:
        return cd["max_yield_day"] + 1
    last_tick_age = cd["first_yield_day"] + (cd["max_yield"] - 1) * cd["interval"]
    return last_tick_age + 1


def rank_options(prices, day):
    """Return sorted list of (kind, name, use_fertilizer, profit_per_day) best-first.
    Options that can no longer mature before the season ends are excluded."""
    remaining_days = SEASON_DAYS - day
    fert_price = prices.get("FERTILIZER", 100)
    wheat_price = prices.get("WHEAT", 25)
    options = []
    for crop, cd in CROPS.items():
        if crop_tile_days(crop) > remaining_days + 1:
            continue
        for use_fert in (False, True):
            pd, _ = crop_profit_per_day(crop, prices.get(crop, cd["seed"]), fert_price, use_fert)
            options.append(("CROP", crop, use_fert, pd))
    for animal, ad in ANIMALS.items():
        if ad["first_yield_day"] + ad["interval"] > remaining_days:
            continue
        pd = animal_profit_per_day(animal, prices.get(ad["product"], 50), wheat_price)
        options.append(("ANIMAL", animal, False, pd))
    options.sort(key=lambda o: -o[3])
    return options


# ---------------------------------------------------------------------------
# Pathfinding
# ---------------------------------------------------------------------------

DIRS = [("NORTH", 0, -1), ("SOUTH", 0, 1), ("EAST", 1, 0), ("WEST", -1, 0)]


def bfs_next_step(start, goal, tiles, board_size):
    """Return the direction name to move from `start` one step closer to `goal`
    (BFS shortest path). Locked tiles are passable for movement (only tile actions
    no-op there), and every action target we ever compute already excludes locked
    tiles, so we don't need to route around them here. None if already there."""
    if tuple(start) == tuple(goal):
        return None
    visited = {tuple(start): None}
    q = deque([tuple(start)])
    while q:
        cur = q.popleft()
        if cur == tuple(goal):
            break
        for name, dx, dy in DIRS:
            nx, ny = cur[0] + dx, cur[1] + dy
            if not (0 <= nx < board_size and 0 <= ny < board_size):
                continue
            npos = (nx, ny)
            if npos not in visited:
                visited[npos] = (cur, name)
                q.append(npos)
    if tuple(goal) not in visited:
        return None
    # walk back from goal to start to find first move
    node = tuple(goal)
    first_move = None
    while visited[node] is not None:
        prev, move = visited[node]
        first_move = move
        node = prev
    return first_move


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ---------------------------------------------------------------------------
# Per-turn world snapshot + task planning
# ---------------------------------------------------------------------------

SELL_RESERVE_STAPLE = 0.55     # wheat / carrot / egg: sell fairly freely
SELL_RESERVE_PREMIUM = 0.65    # tomato/strawberry/melon/milk/wool: throttle harder
STAPLES = {"WHEAT", "CARROT", "EGG", "FERTILIZER"}
SHED_CAP_DEFAULT = 100
DIVERSIFY_SHARE_CAP = 0.45     # don't let one option exceed ~45% of planted tiles


def _crop_still_useful(crop, age, cd):
    """True while the tile is still worth tending. One-time crops stop needing
    water/fertilizer once past their harvest window; ongoing crops (tomato,
    strawberry) must keep being watered every day they're alive — right through
    all of their scheduled ticks — since 2 consecutive missed waterings turns
    ANY plant into a weed, not just one-time crops."""
    if cd["ongoing"]:
        return True
    return age <= cd["max_yield_day"]


def _crop_still_worth_fertilizing(crop, age, cd):
    """Like _crop_still_useful, but for ongoing crops stops once the last
    scheduled tick has passed — no more bonus ticks are coming, so further
    fertilizer spend is wasted even though watering should continue."""
    if cd["ongoing"]:
        last_tick_age = cd["first_yield_day"] + (cd["max_yield"] - 1) * cd["interval"]
        return age <= last_tick_age
    return age <= cd["max_yield_day"]


def plan_and_act(obs):
    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    me = farms[player]
    private = obs.get("private", {}) or {}
    market = obs.get("market", {}) or {}
    day = obs.get("day", 0)

    tiles = me["tiles"]
    board_size = len(tiles)
    prices = market.get("prices", {}) or {}
    inv_market = market.get("inventory", {}) or {}
    shed = dict(private.get("shed", {}) or {})
    seeds = private.get("seeds", {}) or {}
    inventories = private.get("inventories", [{}])
    money = me["money"]

    shed_access = [(board_size // 2 - 1, board_size // 2 - 1), (board_size // 2, board_size // 2 - 1),
                   (board_size // 2 - 1, board_size // 2), (board_size // 2, board_size // 2)]
    shed_pos = shed_access[0]  # any of the four works as a movement target; adjacency handles the rest

    units = [{"idx": 0, "pos": tuple(me["farmer"]), "inv": inventories[0] if inventories else {}}]
    for h_i, h_pos in enumerate(me.get("hands", [])):
        inv = inventories[h_i + 1] if h_i + 1 < len(inventories) else {}
        units.append({"idx": h_i + 1, "pos": tuple(h_pos), "inv": inv})

    # ---- 1. Scan farm ----
    crop_tile_counts = {c: 0 for c in CROPS}
    animal_tile_counts = {a: 0 for a in ANIMALS}
    empty_tiles = []
    weed_tiles = []
    unwatered = []          # (pos, crop)
    harvestable = []        # (pos,)
    fertilize_due = {c: [] for c in CROPS}
    unfed_animals = []      # (pos, animal)
    uncared_animals = []    # (pos,)
    fert_collectable = []   # (pos,)
    empty_structures = {"COOP": [], "PASTURE": []}

    for y in range(board_size):
        for x in range(board_size):
            t = tiles[y][x]
            if t is None:
                empty_tiles.append((x, y))
            elif t == "LOCKED":
                continue
            elif isinstance(t, dict):
                kind = t.get("kind")
                if kind == "WEED":
                    weed_tiles.append((x, y))
                elif kind == "PLANT":
                    crop = t["crop"]
                    cd = CROPS[crop]
                    crop_tile_counts[crop] += 1
                    age = day - t["planted_day"]
                    yield_units = t.get("yield_units", 0)
                    spent = False
                    if cd["ongoing"]:
                        last_tick_age = cd["first_yield_day"] + (cd["max_yield"] - 1) * cd["interval"]
                        spent = age > last_tick_age and yield_units == 0
                    if yield_units > 0 and (cd["ongoing"] or age >= cd["max_yield_day"]):
                        harvestable.append((x, y))
                    if spent:
                        # No more ticks coming and nothing left to harvest — reclaim
                        # the tile via DIG instead of watering it forever.
                        weed_tiles.append((x, y))
                    else:
                        if not t.get("watered_today") and _crop_still_useful(crop, age, cd):
                            unwatered.append(((x, y), crop))
                        if t.get("fertilized_until_day", -1) < day and _crop_still_worth_fertilizing(crop, age, cd):
                            fertilize_due[crop].append((x, y))
                elif kind in ("COOP", "PASTURE"):
                    if "animal" in t:
                        animal_tile_counts[t["animal"]] += 1
                        if not t.get("fed_today"):
                            unfed_animals.append(((x, y), t["animal"]))
                        if not t.get("cared_today"):
                            uncared_animals.append((x, y))
                        if t.get("fertilizer_available"):
                            fert_collectable.append((x, y))
                        if t.get("yield_units", 0) > 0:
                            harvestable.append((x, y))
                    else:
                        empty_structures[kind].append((x, y))

    total_planted = sum(crop_tile_counts.values()) + sum(animal_tile_counts.values())

    # ---- 2. Economics: choose current best crop / animal target (with diversification) ----
    ranked = rank_options(prices, day)
    # Liquidity guard: steady-state profit/day rewards slow-maturing, high-value crops
    # (melon, strawberry) even at day 0, but with no cash flow yet that locks up capital
    # for 8-12 days. While cash is tight, restrict to fast-cycle crops (wheat/carrot,
    # first yield in 2 days) so the farm has income before it needs to spend again.
    cash_tight = money < 900 or day < 3
    if cash_tight:
        fast = [o for o in ranked if o[0] == "CROP" and CROPS[o[1]]["first_yield_day"] <= 3]
        if fast:
            ranked = fast + [o for o in ranked if o not in fast]
    target_crop, target_fert, target_animal = None, False, None
    for kind, name, use_fert, pd in ranked:
        if pd <= 0:
            break
        share = (crop_tile_counts.get(name, 0) if kind == "CROP" else animal_tile_counts.get(name, 0))
        share_frac = share / max(1, total_planted)
        if share_frac < DIVERSIFY_SHARE_CAP or total_planted == 0:
            if kind == "CROP":
                target_crop, target_fert = name, use_fert
            else:
                target_animal = name
            break
    if target_crop is None and target_animal is None and ranked:
        kind, name, use_fert, pd = ranked[0]
        if kind == "CROP":
            target_crop, target_fert = name, use_fert
        else:
            target_animal = name

    should_fertilize_crop = {c: False for c in CROPS}
    if target_fert and target_crop:
        should_fertilize_crop[target_crop] = True
    # also fertilize any other already-planted crop if fertilizing beats not, at current prices
    for crop in CROPS:
        if crop_tile_counts[crop] > 0:
            pd_no, _ = crop_profit_per_day(crop, prices.get(crop, CROPS[crop]["seed"]), prices.get("FERTILIZER", 100), False)
            pd_yes, _ = crop_profit_per_day(crop, prices.get(crop, CROPS[crop]["seed"]), prices.get("FERTILIZER", 100), True)
            if pd_yes > pd_no:
                should_fertilize_crop[crop] = True

    # trim fertilize_due to only crops we've decided are worth it
    for crop in list(fertilize_due):
        if not should_fertilize_crop[crop]:
            fertilize_due[crop] = []
    fertilize_positions = [p for crop in fertilize_due for p in fertilize_due[crop]]

    # ---- 3. Market orders (capital policy) ----
    market_orders = []
    reserve_cash = 150.0  # keep a small buffer for safety

    # 3a. Sell shed inventory (throttled to avoid crashing premium prices), full liquidation at season end
    remaining_days = SEASON_DAYS - day
    liquidate_all = remaining_days <= 1
    sell_orders = []
    for item, qty in shed.items():
        if qty <= 0 or item not in inv_market:
            continue
        if item == "FERTILIZER" and not liquidate_all:
            continue  # keep for our own crops instead of flipping it
        if liquidate_all:
            sell_qty = qty
        else:
            reserve_frac = SELL_RESERVE_STAPLE if item in STAPLES else SELL_RESERVE_PREMIUM
            sell_qty = max_qty_above_reserve(item, inv_market[item], qty, reserve_frac)
            # if shed is getting full, force-sell more to avoid overflow loss next EOD
            shed_total = sum(shed.values())
            if shed_total >= 85:
                sell_qty = qty
        if sell_qty > 0:
            sell_orders.append(["SELL", item, sell_qty])
    sell_orders.sort(key=lambda o: -(o[2] * prices.get(o[1], 0)))
    market_orders.extend(sell_orders)

    # 3b. Keep wheat stocked for animal feed (buy shortfall)
    if animal_tile_counts and sum(animal_tile_counts.values()) > 0:
        need_wheat = sum(animal_tile_counts.values()) * 2  # ~2 days buffer
        have_wheat = shed.get("WHEAT", 0) + sum(u["inv"].get("WHEAT", 0) for u in units)
        shortfall = need_wheat - have_wheat
        if shortfall > 0 and money - reserve_cash > shortfall * prices.get("WHEAT", 25):
            market_orders.append(["BUY_PRODUCT", "WHEAT", shortfall])

    # 3c. Keep fertilizer stocked if any crop is worth fertilizing
    if any(should_fertilize_crop.values()):
        have_fert = shed.get("FERTILIZER", 0) + sum(u["inv"].get("FERTILIZER", 0) for u in units)
        target_stock = 3
        if have_fert < target_stock and money - reserve_cash > prices.get("FERTILIZER", 100):
            market_orders.append(["BUY_PRODUCT", "FERTILIZER", target_stock - have_fert])

    # 3d. Hire the day's crew. Hands vanish at end of day and must be re-hired every
    # morning, but the fib-indexed cost resets too, so a small crew is cheap relative
    # to the extra tile-throughput it buys. Hire the whole crew in one shot at the
    # start of the day (hour 0), sized to how much unlocked land there is to work.
    n_hands = len(me.get("hands", []))
    unlocked_tiles = sum(1 for row in tiles for t in row if t != "LOCKED")
    max_hands = min(8, 1 + unlocked_tiles // 10)
    hour = obs.get("hour", 0)
    if hour == 0 and n_hands == 0 and remaining_days > 1:
        hires_today = 0
        cumulative = 0.0
        n_to_hire = 0
        while hires_today < max_hands:
            c = _fib_cost(hires_today)
            if money - reserve_cash < cumulative + c:
                break
            cumulative += c
            hires_today += 1
            n_to_hire += 1
        for _ in range(n_to_hire):
            market_orders.append(["HIRE"])

    # 3e. Buy seed for target crop (stock enough to keep every idle unit planting)
    if target_crop:
        want = min(len(empty_tiles) + 1, 6)
        have = seeds.get(target_crop, 0)
        if have < want and money - reserve_cash > CROPS[target_crop]["seed"]:
            afford = int((money - reserve_cash) // CROPS[target_crop]["seed"])
            buy_n = max(0, min(want - have, afford))
            if buy_n > 0:
                market_orders.append(["BUY_SEED", target_crop, buy_n])

    # 3f. Animal purchase: if best target is an animal and we have (or will have) a free structure
    pending_animal_purchase = False
    if target_animal:
        structure = ANIMALS[target_animal]["structure"]
        have_animal_units = shed.get(target_animal, 0) + sum(u["inv"].get(target_animal, 0) for u in units)
        free_structures = len(empty_structures[structure])
        if free_structures > have_animal_units and money - reserve_cash > ANIMALS[target_animal]["cost"]:
            market_orders.append(["BUY_ANIMAL", target_animal, 1])
            pending_animal_purchase = True

    # 3g. Land purchase: buy next quadrant once the farm is running fairly full and
    # payback is short enough given the days left in the season.
    n_extra_unlocked = len(me.get("unlocked_quadrants", [])) - 1
    if n_extra_unlocked < len(LAND_ORDER):
        land_cost = LAND_PRICES[n_extra_unlocked]
        best_pd = ranked[0][3] if ranked else 0
        payback_days = land_cost / max(1.0, best_pd * 20)  # ~20 usable tiles per new quadrant
        unlocked_now = sum(1 for row in tiles for t in row if t != "LOCKED")
        farm_is_busy = len(empty_tiles) < 0.5 * max(1, unlocked_now)
        if (farm_is_busy and money - reserve_cash > land_cost * 1.15
                and payback_days < remaining_days * 1.1 and remaining_days > 4):
            market_orders.append(["BUY_LAND"])

    market_orders = market_orders[:10]

    # ---- 4. Per-unit task assignment ----
    claimed_tiles = set()
    claimed_pickup = {}  # item -> reserved amount this turn

    def take_shed(item, amt):
        avail = shed.get(item, 0) - claimed_pickup.get(item, 0)
        take = max(0, min(amt, avail))
        if take > 0:
            claimed_pickup[item] = claimed_pickup.get(item, 0) + take
        return take

    farmer_action = ["PASS"]
    hand_actions = []

    for u in units:
        pos = u["pos"]
        inv = u["inv"]
        action = None

        # (a) direct high-value actions available right where useful, prefer nearest of each category
        def nearest(cands):
            cands = [c for c in cands if c not in claimed_tiles]
            if not cands:
                return None
            return min(cands, key=lambda c: manhattan(pos, c))

        carry_wheat = inv.get("WHEAT", 0) > 0
        carry_fert = inv.get("FERTILIZER", 0) > 0
        carry_animal = target_animal and inv.get(target_animal, 0) > 0

        build_structure = None
        if target_animal:
            structure = ANIMALS[target_animal]["structure"]
            existing = len(empty_structures.get(structure, [])) + animal_tile_counts[target_animal]
            want = min(4, 1 + total_planted // 8)
            if existing < want and money - reserve_cash > ANIMALS[target_animal]["cost"]:
                build_structure = structure

        chosen = None

        # Priority 0: keep animals alive. Losing one is unrecoverable, so this is
        # resolved before anything else — including fetching wheat first if the
        # unit isn't already carrying any, rather than waiting for a turn where it
        # happens to be.
        reachable_unfed = [p for p, _a in unfed_animals if p not in claimed_tiles]
        if reachable_unfed:
            if carry_wheat:
                chosen = (nearest(reachable_unfed), "FEED")
            elif take_shed("WHEAT", 10) > 0:
                chosen = (shed_pos, "PICKUP_WHEAT")

        # Priority 1: everything else that's directly actionable right now, nearest
        # of each category first.
        if chosen is None:
            n_fert = nearest(fertilize_positions) if carry_fert else None
            n_place = nearest(empty_structures.get(ANIMALS[target_animal]["structure"], [])) if carry_animal else None
            n_harvest = nearest(harvestable)
            n_water = nearest([p for p, _c in unwatered])
            n_dig = nearest(weed_tiles)
            n_plant = nearest(empty_tiles) if (target_crop and seeds.get(target_crop, 0) > 0) else None
            n_care = nearest(uncared_animals)
            n_collect = nearest(fert_collectable)
            n_build = nearest(empty_tiles) if build_structure else None

            candidates = []
            if n_fert: candidates.append((n_fert, "FERTILIZE"))
            if n_place: candidates.append((n_place, "PLACE"))
            if n_harvest: candidates.append((n_harvest, "HARVEST"))
            if n_water: candidates.append((n_water, "WATER"))
            if n_collect: candidates.append((n_collect, "COLLECT_FERTILIZER"))
            if n_dig: candidates.append((n_dig, "DIG"))
            if n_build: candidates.append((n_build, f"BUILD_{build_structure}"))
            if n_plant: candidates.append((n_plant, "PLANT"))
            if n_care: candidates.append((n_care, "CARE"))
            chosen = candidates[0] if candidates else None

        # Priority 2: nothing directly actionable — fetch from shed for a task that
        # needs an item we don't carry yet, or drop off what we're carrying.
        if chosen is None:
            need_fert_somewhere = len(fertilize_positions) > 0 and not carry_fert
            need_animal_somewhere = bool(target_animal) and not carry_animal and (
                shed.get(target_animal, 0) - claimed_pickup.get(target_animal, 0) > 0)

            if need_fert_somewhere and take_shed("FERTILIZER", 3) > 0:
                chosen = (shed_pos, "PICKUP_FERTILIZER")
            elif need_animal_somewhere and take_shed(target_animal, 1) > 0:
                chosen = (shed_pos, f"PICKUP_{target_animal}")
            elif inv and sum(inv.values()) > 0:
                chosen = (shed_pos, "DROP")
            elif target_animal and not empty_structures.get(ANIMALS[target_animal]["structure"]) and empty_tiles:
                structure = ANIMALS[target_animal]["structure"]
                build_pos = nearest(empty_tiles)
                if build_pos:
                    chosen = (build_pos, f"BUILD_{structure}")

        if chosen is None:
            act = ["PASS"]
        else:
            target_pos, category = chosen
            if tuple(pos) == tuple(target_pos) or _is_shed_adjacent_local(pos, board_size) and category.startswith(("PICKUP", "DROP")):
                act = _execute(category, target_crop, target_animal)
                claimed_tiles.add(target_pos)
            else:
                move = bfs_next_step(pos, target_pos, tiles, board_size)
                act = [move] if move else ["PASS"]

        if u["idx"] == 0:
            farmer_action = act
        else:
            hand_actions.append(act)

    return {"farmer": farmer_action, "hands": hand_actions, "market": market_orders}


def _is_shed_adjacent_local(pos, board_size):
    half = board_size // 2
    return tuple(pos) in {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}


def _execute(category, target_crop, target_animal=None):
    if category == "FEED": return ["FEED"]
    if category == "FERTILIZE": return ["FERTILIZE"]
    if category == "PLACE": return ["PLACE", target_animal]
    if category == "HARVEST": return ["HARVEST"]
    if category == "WATER": return ["WATER"]
    if category == "COLLECT_FERTILIZER": return ["COLLECT_FERTILIZER"]
    if category == "DIG": return ["DIG"]
    if category == "PLANT": return ["PLANT", target_crop]
    if category == "CARE": return ["CARE"]
    if category == "PICKUP_WHEAT": return ["PICKUP", "WHEAT", 10]
    if category == "PICKUP_FERTILIZER": return ["PICKUP", "FERTILIZER", 3]
    if category.startswith("PICKUP_"): return ["PICKUP", category[len("PICKUP_"):], 1]
    if category == "DROP": return ["DROP"]
    if category == "BUILD_COOP": return ["BUILD_COOP"]
    if category == "BUILD_PASTURE": return ["BUILD_PASTURE"]
    return ["PASS"]


def _fib_cost(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def agent(obs):
    try:
        return plan_and_act(obs)
    except Exception:
        # Never let an unhandled exception forfeit the episode.
        return {"farmer": ["PASS"], "hands": [], "market": []}
