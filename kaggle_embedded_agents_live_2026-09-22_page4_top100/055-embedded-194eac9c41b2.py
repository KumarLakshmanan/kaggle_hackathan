
"""Kaggriculture heuristic agent.

Strategy - a capital-compounding wheat loop, sized to one farmer's watering capacity:

  1. Keep a small, waterable set of WHEAT tiles (cheap seed 10, sells ~25, fast payback).
  2. Every turn the farmer does the single highest-value thing reachable on its tile:
     HARVEST a ready plant > WATER a dry plant > PLANT on empty soil > else step toward
     the nearest tile that needs attention.
  3. Market orders each turn: sell harvested produce in small batches (price crashes on
     gluts, so never dump), and top up seed stock when cash allows.
  4. Once comfortably capitalised, fold in a few MELON tiles (seed 80, sells ~250) for
     margin, still bounded by how many tiles one farmer can water per day.

Everything is wrapped so a malformed observation or an unexpected field can never raise -
a crash forfeits the whole episode, so the agent always returns a valid action dict.
"""

CROP_SELL_BATCH = 3          # units sold per market tick, to avoid crashing the price
WHEAT_TARGET = 8             # wheat tiles to keep planted early
MELON_TARGET = 5             # melon tiles once rich (still bounded by watering capacity)
MELON_CASH_GATE = 4200       # switch to melons only once the bank grows past the ~3000 start
SEED_BUFFER = 2              # keep this many seeds of the active crop in stock

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}


def _safe(fn):
    """Never let the agent raise: on any error, PASS with no market orders."""
    def wrapped(obs, *a, **k):
        try:
            action = fn(obs, *a, **k)
            if not isinstance(action, dict):
                return {"farmer": ["PASS"], "market": []}
            action.setdefault("farmer", ["PASS"])
            action.setdefault("market", [])
            return action
        except Exception:
            return {"farmer": ["PASS"], "market": []}
    return wrapped


def _my_farm(obs):
    return obs["farms"][obs["player"]]


def _tile_at(farm, x, y):
    return farm["tiles"][y][x]


def _step_toward(fx, fy, tx, ty):
    """One cardinal move from (fx,fy) toward (tx,ty)."""
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    if fy > ty:
        return "NORTH"
    return "PASS"


def _scan(farm):
    """Categorise tiles into harvestable / dry / plantable, with coordinates."""
    harvest, dry, empty = [], [], []
    tiles = farm["tiles"]
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile is None:
                empty.append((x, y))
            elif isinstance(tile, dict) and tile.get("kind") == "PLANT":
                if tile.get("yield_units", 0) > 0:
                    harvest.append((x, y))
                if not tile.get("watered_today", True):
                    dry.append((x, y))
    return harvest, dry, empty


def _nearest(fx, fy, cells):
    if not cells:
        return None
    return min(cells, key=lambda c: abs(c[0] - fx) + abs(c[1] - fy))


def _active_crop(obs):
    money = _my_farm(obs).get("money", 0)
    return "MELON" if money >= MELON_CASH_GATE else "WHEAT"


def _market_orders(obs):
    """Sell surplus produce in small batches; keep a seed buffer stocked."""
    orders = []
    priv = obs.get("private", {})
    shed = priv.get("shed", {}) or {}
    seeds = priv.get("seeds", {}) or {}
    money = _my_farm(obs).get("money", 0)
    prices = obs.get("market", {}).get("prices", {}) or {}

    # sell harvested produce (anything sellable sitting in the shed that is not a seed
    # input we still need). Sell wheat only above a small feed reserve.
    for item, qty in sorted(shed.items(), key=lambda kv: -prices.get(kv[0], 0)):
        if qty <= 0:
            continue
        reserve = 4 if item == "WHEAT" else 0   # keep a little wheat for animal feed
        sellable = qty - reserve
        if sellable > 0:
            orders.append(["SELL", item, min(CROP_SELL_BATCH, sellable)])
        if len(orders) >= 4:
            break

    # keep the active crop's seed stocked
    crop = _active_crop(obs)
    have = seeds.get(crop, 0)
    cost = SEED_COST.get(crop, 999)
    if have < SEED_BUFFER and money >= cost * 2:
        orders.append(["BUY_SEED", crop, SEED_BUFFER - have])

    return orders[:8]   # stay under maxMarketOrdersPerTurn with headroom


def _farmer_action(obs):
    """Pick the single best farmer action for this turn."""
    farm = _my_farm(obs)
    fx, fy = farm["farmer"]
    tile = _tile_at(farm, fx, fy)
    harvest, dry, empty = _scan(farm)

    crop = _active_crop(obs)
    target_count = MELON_TARGET if crop == "MELON" else WHEAT_TARGET
    planted = sum(
        1 for row in farm["tiles"] for t in row
        if isinstance(t, dict) and t.get("kind") == "PLANT"
    )

    # 1) standing on a ready plant -> harvest it
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("yield_units", 0) > 0:
        return "HARVEST"
    # 2) standing on a dry plant -> water it
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", True):
        return "WATER"
    # 3) standing on empty soil, still want more crops -> plant a seed we hold
    #    (prefer the active crop, but never waste a seed already in stock)
    seeds = obs.get("private", {}).get("seeds", {}) or {}
    if tile is None and planted < target_count:
        if seeds.get(crop, 0) > 0:
            return "PLANT " + crop
        for alt in ("WHEAT", "CARROT", "MELON", "TOMATO", "STRAWBERRY"):
            if seeds.get(alt, 0) > 0:
                return "PLANT " + alt

    # 4) otherwise move toward the most urgent tile: dry plant first (they die),
    #    then a harvest, then empty soil to expand (only if we hold any seed).
    have_seed = any(seeds.get(c, 0) > 0 for c in CROPS)
    want_expand = planted < target_count and have_seed
    for cells in (dry, harvest, empty if want_expand else []):
        tgt = _nearest(fx, fy, cells)
        if tgt is not None:
            return _step_toward(fx, fy, tgt[0], tgt[1])
    return "PASS"


@_safe
def agent(obs, config=None):
    action = {"farmer": [_farmer_action(obs)], "market": _market_orders(obs)}
    # if hands exist, have each help water/harvest independently (best effort)
    farm = _my_farm(obs)
    hands = farm.get("hands", []) or []
    if hands:
        action["hands"] = [_farmer_action(obs) for _ in hands]
    return action


# kaggle_environments calls the module-level `agent` function.
def act(obs, config=None):
    return agent(obs, config)

