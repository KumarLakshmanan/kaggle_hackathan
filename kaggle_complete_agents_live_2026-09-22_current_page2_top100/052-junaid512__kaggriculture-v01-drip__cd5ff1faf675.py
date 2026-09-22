"""
Kaggriculture agent — v01 "Drip"

Strategy in one line:
    Saturate the highest $/action lanes (melon, sheep, cow), harvest the free
    fertilizer byproduct from every animal, and METER every sale against the
    live price curve instead of dumping.

All game constants below are transcribed from the environment source
(kaggle_environments/envs/kaggriculture/kaggriculture.py) and NOT from the
published docs, which are wrong on several decisive points:

  * FERTILIZER *is* sellable  (PRODUCTS L25 includes it; SELL whitelist L571).
    The town never consumes it, so its 493-unit pool is drained only by the
    two players -> a first-mover race worth ~$25k.
  * CARE banks +1/day, not +2   (L800).
  * fertilizer_available is set every end-of-day for every surviving animal,
    with no CARE dependency     (L801).
  * A plant not watered on its PLANTING DAY dies that night
    (_new_plant seeds consecutive_unwatered = 1).
  * Animals have no lifespan and no production cap; max_held is storage only.

Hard runtime limit: actTimeout = 1s/turn, 60s total overage for the episode.
This file is pure stdlib and does no search; typical turn cost is < 5 ms.
"""

import math
import os

# ----------------------------------------------------------------------------
# Verified game constants
# ----------------------------------------------------------------------------

CROPS = {
    "WHEAT":      {"seed": 10,  "first_yield_day": 2,  "max_yield_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False, "product": "WHEAT"},
    "CARROT":     {"seed": 20,  "first_yield_day": 2,  "max_yield_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False, "product": "CARROT"},
    "TOMATO":     {"seed": 50,  "first_yield_day": 8,  "max_yield_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True,  "product": "TOMATO"},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True,  "product": "STRAWBERRY"},
    "MELON":      {"seed": 80,  "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False, "product": "MELON"},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER"]

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

LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]

TURNS_PER_DAY = 24
LAST_DAY = 29
SHED_CAPACITY = 100
MAX_MARKET_ORDERS = 10

MOVE_OPS = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


# ----------------------------------------------------------------------------
# Tunable policy config  (this is the parameter search space)
# ----------------------------------------------------------------------------

class CFG:
    # --- labour ---------------------------------------------------------
    HAND_BASE = 4               # hands even with an empty farm
    HAND_PER_ANIMAL = 0.34      # ~3 animals serviced per unit per day
    HAND_PER_PLANT = 0.10       # extra hands per living plant
    HAND_MAX = int(os.environ.get("KAGG_HANDS", "12"))               # fib(15)=$987 for the 16th hire
    HAND_MONEY_FRAC = 0.10      # never spend >10% of bank on a day's hires

    # --- capital allocation ---------------------------------------------
    # Animal count is NOT a fixed cap. It is bounded by (a) how many units we
    # can afford to work them and (b) whether the product still clears above
    # our price floor. Measured episodes end with milk/wool at ~2x base, i.e.
    # the market is starved: production, not demand depth, is the constraint.
    ANIMALS_PER_UNIT = float(os.environ.get("KAGG_APU", "2.2"))      # animals one unit can service per day
    ANIMAL_BUY_PRICE_FRAC = 0.80   # stop buying a species below this x base
    # Geese are deliberately excluded: ~$5-22 per action once wheat inflates,
    # and each one needs BUILD_COOP + PICKUP + PLACE before it earns anything.
    # In testing the agent bought 36 and managed to place 2.
    SPECIES_ORDER = ("SHEEP", "COW")
    # never hold more unplaced animals than we can house shortly
    ANIMAL_BACKLOG = 3
    # Herd target = (daily town demand) / (yield per animal per day) x ratio.
    # Slightly under-supplying keeps the price at or above base; over-supplying
    # crashes it (28 cows drove milk from $160 to $24 in testing).
    SUPPLY_RATIO = {"MILK": 0.95, "WOOL": 0.95, "EGG": 2.20}
    # An animal that starves is a total loss, so every purchase must also
    # reserve its feed. This is what stops the herd outrunning the bank.
    FEED_BUFFER_PER_ANIMAL = 280
    MAX_BUY_PER_DAY = int(os.environ.get("KAGG_MBD", "4"))         # ramp the herd instead of spiking it
    # Crop tile budget. STRAWBERRY is the single best lane in the game and is
    # easy to miss: the town drains 32/day of it (more than any other product),
    # so a farm of this size never gluts it and it clears at ~2x base all
    # season. It also needs no feed and no daily FEED/CARE, unlike animals.
    STRAWBERRY_TILES = int(os.environ.get("KAGG_STRAW", "16"))
    MELON_TILES = int(os.environ.get("KAGG_MEL", "12"))            # 2 cycles; metered against its 8/day drain
    WHEAT_TILES = 6             # fast cash (first yield day 2) + feed
    CASH_RESERVE = 300          # floor under the bank at all times
    # Never sink the whole bank into slow seed. Strawberry costs $100 and pays
    # nothing until day 10; buying 30 on day 0 spends the entire starting bank
    # and leaves nothing for land, which is the real multiplier.
    SEED_BUDGET_FRAC = float(os.environ.get("KAGG_SEEDF", "0.80"))
    SEED_TILE_LOOKAHEAD = 4     # buy at most this many seeds beyond free tiles

    LAND_BUY_MONEY = [1200, 2400, 5000]   # bank needed before each BUY_LAND
    LAND_BUY_DAY = [0, 3, 8]              # earliest day for each BUY_LAND

    # last day it is still worth starting each investment
    LAST_DAY_BUY = {"SHEEP": 23, "COW": 21, "GOOSE": 24}
    # strawberry fires productions at +10/+12/+14/+16 days
    LAST_DAY_PLANT_STRAWBERRY = 19
    LAST_DAY_PLANT_MELON = 19
    LAST_DAY_PLANT_WHEAT = 26

    # --- wheat / feed ----------------------------------------------------
    # CRITICAL: the shed holds only 100 items TOTAL, shared between feed wheat
    # and unsold produce, and end-of-day overflow is DESTROYED. Hoarding feed
    # silently bins every harvest. So we buy wheat just-in-time -- market
    # orders cost zero unit-actions, so re-buying every turn is free.
    WHEAT_BUY_MAX_PRICE = 110   # feed is cheap next to a $300 milk cheque
    WHEAT_SPARE = 8             # shed wheat target = unfed animals + this
    WHEAT_PICKUP = 12           # bigger loads = fewer shed round-trips
    SHED_SOFT_LIMIT = 52        # above this, start discounting sell floors
    SHED_PANIC = 88             # above this, dump at any price

    # --- market metering: sell only while price >= frac * base ----------
    # Floors are expressed as a fraction of base price. Setting them AT base
    # (1.0) is the key to the whole economy: the town drains the market every
    # turn, so price recovers above base continuously and we sell only into
    # that recovery -- roughly one unit per turn per product, which is exactly
    # the drain rate. Selling below base means pushing inventory past I0, and
    # the premium curves are savage there (wool and melon are worth $1 after
    # ~59 and ~158 units of glut). Measured: floors at 0.5-0.62 ended the
    # season with melon at $31 and milk at $24; at 1.0 they hold ~$250.
    SELL_FLOOR = {
        "MELON": 0.66, "WOOL": 0.66, "MILK": 0.62, "STRAWBERRY": 0.60,
        "EGG": 0.75, "FERTILIZER": 0.40, "WHEAT": 0.76,
        "CARROT": 0.70, "TOMATO": 0.70,
    }
    # sweep hook: scale every floor at once for offline tuning
    FLOOR_SCALE = float(os.environ.get("KAGG_FLOOR", "1.0"))
    LIQUIDATE_DAY = 28          # from here, floors decay toward 1
    FERT_USE_BELOW = 45         # if fertilizer sells under this, use it instead
    # Sell no faster than the town consumes. >1 leans on the instantaneous
    # depth as well as the daily drain.
    SELL_RATE_MULT = float(os.environ.get("KAGG_RATE", "6.0"))
    FERT_SELL_PER_DAY = 18      # fertilizer has no town demand at all

    # --- scheduling ------------------------------------------------------
    TRAVEL_COST = 20            # $ of opportunity cost per turn spent walking
    SHED_DEPOSIT_LOAD = 14      # carry this many items before a shed run
    DIG_VALUE = 210.0           # a blocked tile is a lost crop
    WATER_INSURANCE = 0.35      # x product price, for a not-yet-critical water
    # Don't plant more than the labour force can keep alive. Each plant costs
    # roughly this many actions per day (water on alternate days, plus its
    # share of harvest/fertilize/travel); each animal ~3.5.
    ACTIONS_PER_PLANT = 1.15
    ACTIONS_PER_ANIMAL = 3.6
    PRODUCTIVE_FRAC = float(os.environ.get("KAGG_PF", "0.62"))      # share of unit-turns that are not walking
    CAPACITY_SLACK = 0.88       # only plant up to this share of capacity


# ----------------------------------------------------------------------------
# Market maths (exact replica of the environment's price function)
# ----------------------------------------------------------------------------

def _shape(func, x):
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "log10":
        return math.log10(1.0 + x)
    return x


def market_price(item, inventory):
    """Mirror of kaggriculture.market_price (L177-191)."""
    p = MARKET_PARAMS[item]
    base, i0, t = p["base"], p["I0"], p["T"]
    if inventory < i0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, t)
        price = base + amp * _shape(f, i0 - inventory)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, t)
        price = base - amp * _shape(f, inventory - i0)
    return max(PRICE_FLOOR, int(round(price)))


def drain_per_day(product, unlocked_shops, day, full=False):
    """Units of `product` the town removes from the market each day.

    Shops tick every 4 steps (6x/day) and take 1 of each product they demand,
    doubled for single-product shops. The town centre ticks every 12 steps
    (2x/day) and scales x2 from day 10 and x4 from day 20.

    `full=True` prices in every shop as if already unlocked - used for herd
    planning, because an animal bought today only starts producing in 6-8 days
    by which time more shops will have opened.
    """
    shops = SHOPS.keys() if full else (unlocked_shops or [])
    n = 0
    for shop in shops:
        items = SHOPS.get(shop)
        if items and product in items:
            n += (2 if len(items) == 1 else 1) * 6
    if product != "FERTILIZER":
        mult = 4 if (full or day >= 20) else (2 if day >= 10 else 1)
        n += mult * 2
    return n


def units_above_floor(item, inventory, floor, cap=400):
    """How many units can be sold before the price drops below `floor`.

    Selling adds one unit to market inventory at a time, so this walks the
    curve forward. This is the whole of our sell discipline: premium goods
    have only 59-76 units of depth but are replenished by town demand every
    day, so we drip to the floor and let the town refill overnight.
    """
    n = 0
    inv = inventory
    while n < cap:
        if market_price(item, inv) < floor:
            break
        n += 1
        inv += 1
    return n


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def _tile_at(tiles, x, y):
    try:
        return tiles[y][x]
    except Exception:
        return "LOCKED"


def _is_dict(v):
    return isinstance(v, dict)


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _step_toward(fx, fy, tx, ty):
    """One orthogonal step. LOCKED tiles are passable so no pathfinding."""
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    if fy > ty:
        return "NORTH"
    return None


def _shed_ports(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1),
            (half - 1, half), (half, half)]


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _hire_cost(n_already_today):
    return _fib(n_already_today)


# ----------------------------------------------------------------------------
# Per-episode state
# ----------------------------------------------------------------------------

_STATE = {}


def _state(player):
    if player not in _STATE:
        _STATE[player] = {"last_step": -1}
    return _STATE[player]


# ----------------------------------------------------------------------------
# Farm scan
# ----------------------------------------------------------------------------

class Farm(object):
    """Flattened, typed view of everything we need from the observation."""

    def __init__(self, obs):
        self.player = obs.get("player", 0)
        me = obs["farms"][self.player]
        self.money = float(me.get("money", 0))
        self.tiles = me["tiles"]
        self.board = len(self.tiles)
        self.farmer = list(me.get("farmer", [0, 0]))
        self.hands = [list(h) for h in (me.get("hands") or [])]
        self.hires_today = int(me.get("hires_today", 0))
        self.quadrants = list(me.get("unlocked_quadrants") or ["NW"])

        priv = obs.get("private", {}) or {}
        self.shed = dict(priv.get("shed", {}) or {})
        self.seeds = dict(priv.get("seeds", {}) or {})
        self.inventories = [dict(i or {}) for i in (priv.get("inventories") or [{}])]

        mk = obs.get("market", {}) or {}
        self.inv = dict(mk.get("inventory", {}) or {})
        self.prices = dict(mk.get("prices", {}) or {})
        town = obs.get("town", {}) or {}
        self.shops = list(town.get("unlocked_shops") or [])

        self.day = int(obs.get("day", 0))
        self.hour = int(obs.get("hour", 0))
        self.step = int(obs.get("step", self.day * TURNS_PER_DAY + self.hour))

        self.ports = [p for p in _shed_ports(self.board)
                      if _tile_at(self.tiles, p[0], p[1]) != "LOCKED"]
        if not self.ports:                       # defensive; NW always unlocked
            self.ports = [(self.board // 2 - 1, self.board // 2 - 1)]

        # --- classify every tile once -----------------------------------
        self.empty = []            # unlocked, nothing on it
        self.plants = []           # (x, y, tile)
        self.weeds = []
        self.animals = []          # (x, y, tile) occupied structures
        self.free_struct = []      # (x, y, tile) built but empty
        for y in range(self.board):
            row = self.tiles[y]
            for x in range(self.board):
                t = row[x]
                if t == "LOCKED":
                    continue
                if t is None:
                    self.empty.append((x, y))
                elif _is_dict(t):
                    kind = t.get("kind")
                    if kind == "PLANT":
                        self.plants.append((x, y, t))
                    elif kind == "WEED":
                        self.weeds.append((x, y))
                    elif kind in ("COOP", "PASTURE"):
                        if t.get("animal"):
                            self.animals.append((x, y, t))
                        else:
                            self.free_struct.append((x, y, t))

        self.n_animals = len(self.animals)
        self.counts = {"SHEEP": 0, "COW": 0, "GOOSE": 0}
        for _, _, t in self.animals:
            a = t.get("animal")
            if a in self.counts:
                self.counts[a] += 1
        # animals bought but not yet placed still count against the caps
        for a in self.counts:
            self.counts[a] += int(self.shed.get(a, 0))
            for inv in self.inventories:
                self.counts[a] += int(inv.get(a, 0))

        self.crop_tiles = {}
        for _, _, t in self.plants:
            c = t.get("crop")
            self.crop_tiles[c] = self.crop_tiles.get(c, 0) + 1

        self.shed_used = sum(int(v) for v in self.shed.values())

    # -- convenience -----------------------------------------------------
    def price(self, item):
        if item in self.prices:
            return max(1, int(self.prices[item]))
        return market_price(item, self.inv.get(item, MARKET_I0))

    def can_absorb(self, product, n):
        """Is there room in BOTH the shed and the market for n more units?"""
        carried = sum(int(i.get(product, 0)) for i in self.inventories)
        if self.shed_used + carried + n > CFG.SHED_SOFT_LIMIT + 20:
            return False
        # Deliberately a SHED check only. Gating harvest on the sell price too
        # was fatal: with a floor at base, ripe melons were never harvested at
        # all and rotted on the plant (income did not start until day 21).
        # Standing crop is safe until decay; the shed is the real hazard.
        return True

    def port_dist(self, x, y):
        return min(_dist((x, y), p) for p in self.ports)

    def nearest_port(self, x, y):
        return min(self.ports, key=lambda p: _dist((x, y), p))

    def unit_pos(self, i):
        return self.farmer if i == 0 else self.hands[i - 1]

    def unit_inv(self, i):
        return self.inventories[i] if i < len(self.inventories) else {}

    @property
    def n_units(self):
        return 1 + len(self.hands)


# ----------------------------------------------------------------------------
# Sell floors
# ----------------------------------------------------------------------------

def _sell_floor(farm, item):
    base = MARKET_PARAMS[item]["base"]
    frac = CFG.SELL_FLOOR.get(item, 0.6) * CFG.FLOOR_SCALE
    floor = base * frac

    # Shed pressure: every item still sitting in the shed at nightfall risks
    # pushing the day's harvest over the 100-item cap, where it is destroyed.
    # A discounted sale always beats an incinerated one.
    used = farm.shed_used
    if used > CFG.SHED_SOFT_LIMIT:
        if used >= CFG.SHED_PANIC:
            return 1.0
        span = float(CFG.SHED_PANIC - CFG.SHED_SOFT_LIMIT)
        floor *= max(0.05, 1.0 - (used - CFG.SHED_SOFT_LIMIT) / span)

    # End-of-season liquidation: anything unsold at step 718 is worth zero.
    if farm.day >= CFG.LIQUIDATE_DAY:
        decay = (farm.day - CFG.LIQUIDATE_DAY) * TURNS_PER_DAY + farm.hour
        span = float((LAST_DAY - CFG.LIQUIDATE_DAY + 1) * TURNS_PER_DAY)
        floor = floor * max(0.0, 1.0 - decay / span)
    return max(1.0, floor)


# ----------------------------------------------------------------------------
# Market planning
# ----------------------------------------------------------------------------

def plan_market(farm, state):
    """Build this turn's ordered market queue (max 10 slots).

    Slot order matters: orders are consumed slot-by-slot against the
    opponent's queue, so the most valuable sales go first.
    """
    orders = []
    money = farm.money
    day = farm.day

    # --- 1. land ---------------------------------------------------------
    n_extra = len(farm.quadrants) - 1
    if n_extra < len(LAND_PRICES):
        need = LAND_PRICES[n_extra]
        if (money >= max(need, CFG.LAND_BUY_MONEY[n_extra])
                and day >= CFG.LAND_BUY_DAY[n_extra]
                and day <= 24):
            orders.append(["BUY_LAND"])
            money -= need

    # --- 2. labour -------------------------------------------------------
    want = (CFG.HAND_BASE
            + CFG.HAND_PER_ANIMAL * farm.n_animals
            + CFG.HAND_PER_PLANT * len(farm.plants))
    want = int(min(CFG.HAND_MAX, max(1, round(want))))
    if farm.hour <= 2 and farm.hires_today < want:
        budget = money * CFG.HAND_MONEY_FRAC
        spent = 0.0
        n = farm.hires_today
        while n < want and len(orders) < 6:
            c = _hire_cost(n)
            if spent + c > budget or c > money - spent:
                break
            orders.append(["HIRE"])
            spent += c
            n += 1
        money -= spent

    # --- 3. metered sells (highest value first) --------------------------
    sells = []
    unfed_now = sum(1 for (_, _, t) in farm.animals if not t.get("fed_today"))
    wheat_reserve = unfed_now + CFG.WHEAT_SPARE
    for item in PRODUCTS:
        have = int(farm.shed.get(item, 0))
        if have <= 0:
            continue
        if item == "WHEAT":
            have -= wheat_reserve
            if have <= 0:
                continue
        if item == "FERTILIZER":
            # keep a couple for melon fertilising when fertilizer is cheap
            if farm.price("FERTILIZER") < CFG.FERT_USE_BELOW:
                have -= 4
                if have <= 0:
                    continue
        inv = int(farm.inv.get(item, MARKET_I0))
        floor = _sell_floor(farm, item)
        n = units_above_floor(item, inv, floor, cap=min(have, 300))

        # RATE LIMIT -- the heart of the strategy. A price floor alone does not
        # stop a dump: sixteen ripe melons clear the floor check and go out in
        # ONE order, tanking the price. The town only consumes so much per
        # turn, so we sell at roughly that rate and let demand refill the well
        # between turns. Without this the floor value makes no difference at
        # all (measured: identical results from 0.45x to 0.75x base).
        if item != "WHEAT" and farm.day < CFG.LIQUIDATE_DAY:
            per_day = drain_per_day(item, farm.shops, farm.day)
            if item == "FERTILIZER":
                # nothing in town eats fertilizer, so pace it against the pool
                per_day = CFG.FERT_SELL_PER_DAY
            rate = max(1, int(math.ceil(per_day / float(TURNS_PER_DAY)
                                        * CFG.SELL_RATE_MULT)))
            n = min(n, rate)
        if n > 0:
            sells.append((farm.price(item) * n, item, n))
    sells.sort(reverse=True)
    for _, item, n in sells:
        orders.append(["SELL", item, int(n)])

    # --- 4. feed wheat (just-in-time; see WHEAT_SPARE note in CFG) --------
    wheat_target = unfed_now + CFG.WHEAT_SPARE
    wheat_have = int(farm.shed.get("WHEAT", 0))
    for inv in farm.inventories:
        wheat_have += int(inv.get("WHEAT", 0))
    if farm.n_animals > 0 and wheat_have < wheat_target:
        wprice = market_price("WHEAT", int(farm.inv.get("WHEAT", MARKET_I0)) - 1)
        if wprice <= CFG.WHEAT_BUY_MAX_PRICE:
            n = wheat_target - wheat_have
            n = int(min(n, max(0, (money - CFG.CASH_RESERVE) // max(1, wprice))))
            if n > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", n])
                money -= n * wprice

    # --- 5. animals FIRST -------------------------------------------------
    # Livestock has no lifespan and no production cap, so a cow bought on day 0
    # earns for 21 days while the same cow bought on day 13 earns for 8. That
    # makes early livestock the highest-compounding purchase in the game, and
    # it must outrank seed. (Buying seed first delayed our first animal to
    # day 13 and cost roughly two thirds of the season's income.)
    crop_room = {}
    for crop, target, last_day in (
            ("WHEAT", CFG.WHEAT_TILES, CFG.LAST_DAY_PLANT_WHEAT),
            ("MELON", CFG.MELON_TILES, CFG.LAST_DAY_PLANT_MELON),
            ("STRAWBERRY", CFG.STRAWBERRY_TILES, CFG.LAST_DAY_PLANT_STRAWBERRY)):
        gap = target - farm.crop_tiles.get(crop, 0) - int(farm.seeds.get(crop, 0))
        if day <= last_day and gap > 0:
            crop_room[crop] = gap

    placed = farm.n_animals
    held = sum(farm.counts.get(k, 0) for k in ANIMALS)
    unplaced = held - placed
    wprice = max(25, farm.price("WHEAT"))
    spare = money - CFG.CASH_RESERVE - held * wprice * 2
    labour_room = int(CFG.ANIMALS_PER_UNIT * farm.n_units)
    # leave the crop plan room to breathe, but never starve livestock of tiles
    tile_room = (len(farm.empty) + len(farm.free_struct)
                 - min(sum(crop_room.values()), len(farm.empty) // 2))
    # don't buy livestock faster than we can house it
    housing = len(farm.free_struct) + CFG.ANIMAL_BACKLOG - unplaced
    room = max(0, min(labour_room - held, tile_room, housing,
                      CFG.MAX_BUY_PER_DAY))

    # Size each species to the town's appetite for its product, then buy the
    # one furthest below its target. Piling into one product destroys its own
    # price (wool dies after 59 units of glut, milk after 76).
    ranked = []
    for name in CFG.SPECIES_ORDER:
        a = ANIMALS[name]
        if day > CFG.LAST_DAY_BUY.get(name, 20):
            continue
        product = a["product"]
        base = MARKET_PARAMS[product]["base"]
        ratio = farm.price(product) / float(base)
        if ratio < CFG.ANIMAL_BUY_PRICE_FRAC:
            continue
        yield_per_day = (1.0 + a["interval"]) / float(a["interval"])
        demand = drain_per_day(product, farm.shops, day, full=True)
        target = demand / yield_per_day * CFG.SUPPLY_RATIO.get(product, 1.0)
        have = farm.counts.get(name, 0)
        if have >= target:
            continue
        # rank by how far below target we are, weighted by how well the
        # product is currently clearing
        ranked.append(((target - have) * ratio, name))
    ranked.sort(reverse=True)

    for _, name in ranked:
        if room <= 0 or spare <= 0:
            break
        a = ANIMALS[name]
        # charge each purchase its own feed buffer as well as its price
        eff = a["cost"] + CFG.FEED_BUFFER_PER_ANIMAL
        n = int(min(room, spare // eff, max(1, CFG.MAX_BUY_PER_DAY // 2)))
        if n > 0:
            orders.append(["BUY_ANIMAL", name, n])
            spare -= n * eff
            room -= n

    # --- 6. seeds ---------------------------------------------------------
    # Whatever livestock left on the table goes into crops. Melon is the best
    # return per dollar ($80 of seed -> ~6 melon at ~$250 by day 10) and
    # strawberry is the best sustained lane, but both pay nothing before day 10
    # so they cannot be allowed to crowd out the early herd.
    seed_budget = max(0.0, spare) * CFG.SEED_BUDGET_FRAC
    # only buy seed we have somewhere to put -- a seed in the bag earns nothing
    tiles_free = len(farm.empty) + CFG.SEED_TILE_LOOKAHEAD
    for c in CROPS:
        tiles_free -= int(farm.seeds.get(c, 0))

    # Labour capacity gate. Planting past what the crew can water just makes
    # weeds: an unwatered plant dies after two days, and everything sown on the
    # same day dries out on the same day.
    capacity = farm.n_units * TURNS_PER_DAY * CFG.PRODUCTIVE_FRAC
    committed = (farm.n_animals * CFG.ACTIONS_PER_ANIMAL
                 + len(farm.plants) * CFG.ACTIONS_PER_PLANT)
    headroom = capacity * CFG.CAPACITY_SLACK - committed
    tiles_free = min(tiles_free, int(max(0, headroom / CFG.ACTIONS_PER_PLANT)))
    for crop in ("WHEAT", "MELON", "STRAWBERRY"):
        gap = crop_room.get(crop, 0)
        if gap <= 0 or tiles_free <= 0:
            continue
        cost = CROPS[crop]["seed"]
        n = int(min(gap, tiles_free, seed_budget // cost))
        if n > 0:
            orders.append(["BUY_SEED", crop, n])
            seed_budget -= n * cost
            spare -= n * cost
            tiles_free -= n

    return orders[:MAX_MARKET_ORDERS]


# ----------------------------------------------------------------------------
# Job generation
# ----------------------------------------------------------------------------
# A job is a dict:
#   x, y     target tile
#   op       action list to emit when standing there
#   value    $ gained by doing it (used for scheduling)
#   needs    optional item the acting unit must be carrying
#   key      dedup key so two units never take the same job

def _plant_jobs(farm, jobs):
    for (x, y, t) in farm.plants:
        crop = t.get("crop")
        cd = CROPS.get(crop)
        if not cd:
            continue
        prod_price = farm.price(cd["product"])
        age = farm.day - int(t.get("planted_day", farm.day))
        yu = int(t.get("yield_units", 0))
        unwatered = int(t.get("consecutive_unwatered", 0))
        watered = bool(t.get("watered_today", False))
        fert_until = int(t.get("fertilized_until_day", -1))

        # ---- WATER -----------------------------------------------------
        if not watered:
            value = 0.0
            if not cd["ongoing"]:
                ws = (cd["max_yield_day"] + 1) // 2
                if ws <= age <= cd["max_yield_day"] and yu < cd["max_yield"]:
                    inc = 2 if fert_until >= farm.day else 1
                    inc = min(inc, cd["max_yield"] - yu)
                    value += inc * prod_price
            else:
                if fert_until >= farm.day:
                    value += prod_price * 0.5
            if unwatered >= 1:
                # dies tonight -> value is the whole remaining plant
                remain = max(yu, cd["max_yield"] * 0.7)
                value += remain * prod_price
            else:
                # Insurance watering. A plant only has to miss two days in a
                # row to become a weed, and demand spikes because everything
                # planted together dries out together. Watering early costs an
                # otherwise-idle action and smooths that spike flat.
                value += prod_price * CFG.WATER_INSURANCE
            if value > 0:
                jobs.append({"x": x, "y": y, "op": ["WATER"], "value": value,
                             "key": ("W", x, y)})

        # ---- HARVEST ---------------------------------------------------
        if yu > 0:
            ready = False
            if cd["ongoing"]:
                ready = True
            elif age >= cd["max_yield_day"] or yu >= cd["max_yield"]:
                ready = True

            # Standing crop is free storage; the 100-item shed is not. Sixteen
            # ripe melons is 96 units landing at once, which overflows the shed
            # and forces a panic dump that took melon from $250 to $31. A
            # one-time crop holds its yield until decay, so we harvest only what
            # the shed and the market can actually take today.
            mls = int(t.get("max_lifespan_step", -1))
            urgent = (farm.day >= LAST_DAY - 1 or (0 <= mls <= farm.step))
            if ready and not urgent and not cd["ongoing"]:
                if not farm.can_absorb(cd["product"], yu):
                    ready = False

            if ready:
                jobs.append({"x": x, "y": y, "op": ["HARVEST"],
                             "value": yu * prod_price, "key": ("H", x, y)})

        # ---- FERTILIZE -------------------------------------------------
        # For ONGOING crops this is the big one: a production that is both
        # fertilized and watered yields 2 instead of 1, so keeping strawberry
        # fertilized literally doubles the tile. Fertilizer is free from the
        # animals, so this is close to pure profit.
        if fert_until < farm.day + 1:
            worth = 0.0
            if cd["ongoing"]:
                since = age - cd["first_yield_day"]
                nxt = 0 if since < 0 else (cd["interval"] - since % cd["interval"])
                if since < 0:
                    nxt = cd["first_yield_day"] - age
                if nxt <= 2:                       # a production lands in-window
                    worth = prod_price * 1.6
            else:
                ws = (cd["max_yield_day"] + 1) // 2
                if ws <= age < cd["max_yield_day"] and yu < cd["max_yield"]:
                    worth = prod_price * 1.2
            if worth > 0:
                jobs.append({"x": x, "y": y, "op": ["FERTILIZE"],
                             "value": worth, "needs": "FERTILIZER",
                             "key": ("F", x, y)})


def _animal_jobs(farm, jobs):
    for (x, y, t) in farm.animals:
        name = t.get("animal")
        a = ANIMALS.get(name)
        if not a:
            continue
        pprice = farm.price(a["product"])
        fed = bool(t.get("fed_today", False))
        cared = bool(t.get("cared_today", False))
        unfed = int(t.get("consecutive_unfed", 0))
        yu = int(t.get("yield_units", 0))

        # FEED — costs 1 wheat from the acting unit's CARRIED inventory
        if not fed:
            value = pprice * 2.0
            if unfed >= 1:
                value += a["cost"]          # escapes tonight otherwise
            jobs.append({"x": x, "y": y, "op": ["FEED"], "value": value,
                         "needs": "WHEAT", "key": ("FE", x, y)})

        # CARE — banks +1 unit onto the next production, but only counts
        # if the animal is ALSO fed today.
        if fed and not cared:
            jobs.append({"x": x, "y": y, "op": ["CARE"], "value": pprice,
                         "key": ("C", x, y)})

        # HARVEST — value scales with the stack, so big stacks win
        if yu > 0:
            v = yu * pprice
            if yu >= a["max_held"] - 2:
                v *= 1.4                     # avoid capping out and wasting
            jobs.append({"x": x, "y": y, "op": ["HARVEST"], "value": v,
                         "key": ("AH", x, y)})

        # COLLECT_FERTILIZER — free money, one per animal per day
        if t.get("fertilizer_available"):
            jobs.append({"x": x, "y": y, "op": ["COLLECT_FERTILIZER"],
                         "value": farm.price("FERTILIZER") * 0.95,
                         "key": ("CF", x, y)})


def _build_and_plant_jobs(farm, jobs, carried_animals):
    # place bought animals onto free structures
    for (x, y, t) in farm.free_struct:
        struct = t.get("kind")
        for name, a in ANIMALS.items():
            if a["structure"] != struct:
                continue
            if carried_animals.get(name, 0) > 0:
                jobs.append({"x": x, "y": y, "op": ["PLACE", name],
                             "value": a["cost"] * 1.5, "needs": name,
                             "key": ("PL", x, y)})
                break

    # build housing for animals sitting in the shed / inventories
    homeless = {"PASTURE": 0, "COOP": 0}
    for name, a in ANIMALS.items():
        n = int(farm.shed.get(name, 0)) + carried_animals.get(name, 0)
        homeless[a["structure"]] += n
    for (x, y, t) in farm.free_struct:
        k = t.get("kind")
        if k in homeless:
            homeless[k] -= 1

    empties = sorted(farm.empty, key=lambda e: farm.port_dist(e[0], e[1]))
    used = set()
    for struct, n in homeless.items():
        if n <= 0:
            continue
        op = "BUILD_PASTURE" if struct == "PASTURE" else "BUILD_COOP"
        for e in empties:
            if n <= 0:
                break
            if e in used:
                continue
            used.add(e)
            jobs.append({"x": e[0], "y": e[1], "op": [op], "value": 620.0,
                         "key": ("B", e[0], e[1])})
            n -= 1

    # Planting layout. Wheat sits nearest the shed (it is carried back and
    # feeds animals), strawberry mid-ring (long-lived, watered often), melon
    # furthest out (it only ever needs water).
    free = [e for e in empties if e not in used]           # already port-sorted
    far = sorted(free, key=lambda e: -farm.port_dist(e[0], e[1]))

    plan = (
        ("WHEAT", CFG.WHEAT_TILES, CFG.LAST_DAY_PLANT_WHEAT, free, 130.0),
        ("MELON", CFG.MELON_TILES, CFG.LAST_DAY_PLANT_MELON, far,
         farm.price("MELON") * 3.0),
        ("STRAWBERRY", CFG.STRAWBERRY_TILES, CFG.LAST_DAY_PLANT_STRAWBERRY,
         free, farm.price("STRAWBERRY") * 4.0),
    )
    for crop, target, last_day, order, value in plan:
        if farm.day > last_day:
            continue
        seeds = int(farm.seeds.get(crop, 0))
        room = target - farm.crop_tiles.get(crop, 0)
        n = min(seeds, room)
        if n <= 0:
            continue
        for e in order:
            if n <= 0:
                break
            if e in used:
                continue
            used.add(e)
            n -= 1
            jobs.append({"x": e[0], "y": e[1], "op": ["PLANT", crop],
                         "value": value, "crop": crop,
                         "key": ("P", e[0], e[1])})

    for (x, y) in farm.weeds:
        # A weed occupies a tile that could hold a $800 strawberry, so
        # clearing it is worth far more than the action it costs.
        jobs.append({"x": x, "y": y, "op": ["DIG"], "value": CFG.DIG_VALUE,
                     "key": ("D", x, y)})


def _logistics_jobs(farm, jobs, need_wheat, carried_animals):
    """Shed trips: pick up feed wheat, pick up animals, deposit produce."""
    wheat_in_shed = int(farm.shed.get("WHEAT", 0))
    for pi, port in enumerate(farm.ports):
        if need_wheat > 0 and wheat_in_shed > 0:
            n = int(min(CFG.WHEAT_PICKUP, wheat_in_shed, need_wheat))
            jobs.append({"x": port[0], "y": port[1],
                         "op": ["PICKUP", "WHEAT", n],
                         "value": 150.0 + 40.0 * n, "key": ("PW", pi)})
        for name, a in ANIMALS.items():
            if int(farm.shed.get(name, 0)) > 0:
                # only fetch an animal if there is somewhere to put it
                free = sum(1 for (_, _, t) in farm.free_struct
                           if t.get("kind") == a["structure"])
                if free - carried_animals.get(name, 0) > 0:
                    jobs.append({"x": port[0], "y": port[1],
                                 "op": ["PICKUP", name, 1],
                                 "value": a["cost"] * 1.2,
                                 "key": ("PA", pi, name)})
        if int(farm.shed.get("FERTILIZER", 0)) > 0 and \
                farm.price("FERTILIZER") < CFG.FERT_USE_BELOW:
            jobs.append({"x": port[0], "y": port[1],
                         "op": ["PICKUP", "FERTILIZER", 3],
                         "value": 70.0, "key": ("PF", pi)})


# ----------------------------------------------------------------------------
# Assignment
# ----------------------------------------------------------------------------

def _carry_count(inv):
    return sum(int(v) for v in inv.values())


def assign(farm, jobs):
    """Greedy value-minus-travel assignment of units to jobs.

    ~16 units x ~200 jobs = 3200 candidate pairs, sorted once. Well inside
    the 1 s/turn budget (measured p99 < 6 ms).
    """
    n_units = farm.n_units
    actions = [["PASS"] for _ in range(n_units)]
    assigned = [False] * n_units
    taken = set()

    pairs = []
    for i in range(n_units):
        pos = farm.unit_pos(i)
        inv = farm.unit_inv(i)
        for j, job in enumerate(jobs):
            need = job.get("needs")
            if need and int(inv.get(need, 0)) <= 0:
                continue
            d = _dist(pos, (job["x"], job["y"]))
            score = job["value"] - CFG.TRAVEL_COST * d
            if score <= 0:
                continue
            pairs.append((score, i, j))
    pairs.sort(key=lambda p: -p[0])

    # respect the atomic-PLANT rule: requesting more plants of a crop than we
    # hold seeds cancels ALL of them, so cap plant requests at seeds held.
    seed_budget = {c: int(farm.seeds.get(c, 0)) for c in CROPS}

    for score, i, j in pairs:
        if assigned[i]:
            continue
        job = jobs[j]
        key = job["key"]
        if key in taken:
            continue
        crop = job.get("crop")
        if crop is not None:
            if seed_budget.get(crop, 0) <= 0:
                continue
        pos = farm.unit_pos(i)
        if pos[0] == job["x"] and pos[1] == job["y"]:
            actions[i] = list(job["op"])
            if crop is not None:
                seed_budget[crop] -= 1
        else:
            mv = _step_toward(pos[0], pos[1], job["x"], job["y"])
            if mv is None:
                continue
            actions[i] = [mv]
        assigned[i] = True
        taken.add(key)

    # idle units: bank what they are carrying, otherwise drift to a port
    for i in range(n_units):
        if assigned[i]:
            continue
        inv = farm.unit_inv(i)
        load = _carry_count(inv)
        pos = farm.unit_pos(i)
        if load <= 0:
            continue
        port = farm.nearest_port(pos[0], pos[1])
        if tuple(pos) == tuple(port):
            # PLACE clamps to remaining shed room; DROP would destroy overflow
            item = max(inv.items(), key=lambda kv: int(kv[1]))[0]
            actions[i] = ["PLACE", item, int(inv[item])]
        elif load >= CFG.SHED_DEPOSIT_LOAD or farm.day >= LAST_DAY:
            mv = _step_toward(pos[0], pos[1], port[0], port[1])
            if mv:
                actions[i] = [mv]
    return actions


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------

def _policy(obs):
    farm = Farm(obs)
    state = _state(farm.player)

    carried_animals = {}
    for inv in farm.inventories:
        for name in ANIMALS:
            c = int(inv.get(name, 0))
            if c:
                carried_animals[name] = carried_animals.get(name, 0) + c

    # how much feed wheat still needs carrying out to the field today
    unfed = sum(1 for (_, _, t) in farm.animals if not t.get("fed_today"))
    carried_wheat = sum(int(i.get("WHEAT", 0)) for i in farm.inventories)
    need_wheat = max(0, unfed - carried_wheat)

    jobs = []
    _animal_jobs(farm, jobs)
    _plant_jobs(farm, jobs)
    _build_and_plant_jobs(farm, jobs, carried_animals)
    _logistics_jobs(farm, jobs, need_wheat, carried_animals)

    unit_actions = assign(farm, jobs)
    market = plan_market(farm, state)

    state["last_step"] = farm.step
    return {
        "farmer": unit_actions[0] if unit_actions else ["PASS"],
        "hands": unit_actions[1:],
        "market": market,
    }


# Set True when testing locally so bugs surface instead of silently degrading
# the agent to PASS. MUST be False for submission.
DEBUG_RAISE = False


def agent(obs, config=None):
    """Kaggle entry point. Never raises: a crash forfeits the whole episode."""
    try:
        return _policy(obs)
    except Exception:
        if DEBUG_RAISE:
            raise
        try:
            n = len(obs["farms"][obs.get("player", 0)].get("hands") or [])
        except Exception:
            n = 0
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}