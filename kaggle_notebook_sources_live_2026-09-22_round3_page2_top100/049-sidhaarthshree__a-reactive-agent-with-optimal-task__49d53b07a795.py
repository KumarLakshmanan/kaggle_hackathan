%pip install -q -U kaggle-environments
import math, io, contextlib, statistics, collections, importlib.util, time, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from kaggle_environments import make
print("ready")

%%writefile main.py
"""Kaggriculture agent — "Scarcity Rancher II" (cost-based scheduler).

The one idea
------------
The town consumes every product every day, for free, forever. That consumption
is a *standing bid* nobody has to compete for. For three goods it is larger than
a single farm can possibly supply:

    milk        3 shops x 6/day + town centre  ->  up to 26/day drained
    wool        yarn store 12/day + centre     ->  up to 20/day drained
    strawberry  4 shops x 6/day + centre       ->  up to 32/day drained

A cow makes 1.5 milk/day. A sheep makes 1.33 wool/day. A strawberry tile makes
0.25/day. So a farm built on those three NEVER pushes their inventory above I0 --
their prices sit on the *scarcity* side of the curve and RISE all season, from
$160/$200/$120 base to roughly $300/$250/$270 by day 29.

Contrast wheat, carrot and melon: mass-produce them and you walk their price
straight down. A farm that fills 100 tiles with wheat is doing more work for a
third of the money.

Corollary: DON'T fill the board. Labour, not land, is the binding constraint, so
every unit-turn belongs on the highest-value thing available. Empty tiles are
fine.

Plus one thing the rules page gets wrong: it says fertilizer "can only be bought,
not sold". It can be sold -- FERTILIZER is in PRODUCTS and the SELL path accepts
it. Every fed animal makes one free unit a day at a $100 base, so
COLLECT_FERTILIZER is a one-action ~$70-100.

Scheduling
----------
Every task is priced in DOLLARS PER ACTION using live market prices, and each
unit takes the task maximising `value - TRAVEL_COST * distance`. Priority tiers
cannot express that a CARE two tiles away beats a watering underfoot; a dollar
value can. CARE is worth exactly +1 unit of the animal's product (~$250 for a
cow), watering a melon in its bonus window ~$250, collecting fertilizer ~$80,
watering wheat ~$25. With tiers those are all "priority 1-3" and the nearest one
wins, which is how a farm ends up doing $25 jobs while $250 ones expire.
"""

import math

CROPS = {
    "WHEAT":      dict(seed=10,  first=2,  maxday=4,  interval=0, maxy=6, ongoing=False),
    "CARROT":     dict(seed=20,  first=2,  maxday=3,  interval=0, maxy=4, ongoing=False),
    "TOMATO":     dict(seed=50,  first=8,  maxday=8,  interval=1, maxy=4, ongoing=True),
    "STRAWBERRY": dict(seed=100, first=10, maxday=10, interval=2, maxy=4, ongoing=True),
    "MELON":      dict(seed=80,  first=10, maxday=12, interval=0, maxy=6, ongoing=False),
}
ANIMALS = {
    "GOOSE": dict(cost=300, structure="COOP",    first=4, interval=1, max_held=4, product="EGG"),
    "COW":   dict(cost=400, structure="PASTURE", first=8, interval=2, max_held=6, product="MILK"),
    "SHEEP": dict(cost=500, structure="PASTURE", first=6, interval=3, max_held=6, product="WOOL"),
}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]
SELLABLE = PRODUCTS + ["FERTILIZER"]          # yes, fertilizer too -- see docstring
I0 = 10000
MP = {
    "WHEAT":      dict(base=25,  T=400, bf="sqrt",   bt=0.80, af="log",    at=0.20),
    "CARROT":     dict(base=35,  T=450, bf="log",    bt=0.20, af="sqrt",   at=0.70),
    "TOMATO":     dict(base=60,  T=200, bf="linear", bt=0.40, af="sqrt",   at=0.60),
    "STRAWBERRY": dict(base=120, T=100, bf="sqrt",   bt=0.70, af="linear", at=1.60),
    "MELON":      dict(base=250, T=300, bf="log",    bt=0.20, af="sq",     at=3.60),
    "EGG":        dict(base=50,  T=332, bf="linear", bt=0.40, af="log",    at=0.20),
    "MILK":       dict(base=160, T=122, bf="sqrt",   bt=0.60, af="linear", at=1.60),
    "WOOL":       dict(base=200, T=105, bf="log",    bt=0.20, af="sq",     at=3.20),
    "FERTILIZER": dict(base=100, T=200, bf="linear", bt=0.40, af="linear", at=0.40),
}
DIRS = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}

# Reserve price as a fraction of base -- the lowest price we'll still sell at.
# Deep, flat markets (wheat, egg) can afford a high floor because the price
# hardly moves. Milk and wool have steep glut curves, so a high floor there just
# means holding inventory that scores $0 at the end. Fertilizer has NO town
# demand at all -- its price only ever falls, so there is nothing to wait for.
RESERVE = {"WHEAT": 0.68, "CARROT": 0.55, "TOMATO": 0.50, "STRAWBERRY": 0.48,
           "MELON": 0.58, "EGG": 0.65, "MILK": 0.42, "WOOL": 0.40, "FERTILIZER": 0.18}

# Herd sized to the town's drain rate, so prices never leave the scarcity side.
# Opportunity cost of one unit-turn, in dollars. A well-run farm converts a
# turn into roughly this much, so a task must beat it to be worth walking to.
TRAVEL_COST = 15.0

# Cost, in dollars, of using a rancher for crop work or a hand for animal work. This
# used to be a hard filter (infinite penalty). A rancher standing next to the shed with
# wheat in hand genuinely is the right unit for FEED, so the preference is real -- but
# expressing it as a wall meant ranchers idled rather than help, and idling is never
# worth more than the second-best job available. 0.0 removes the preference entirely.
# Swept against the greedy baseline, 16 paired seeds: 150 gave +$5,916 at 14/16 wins,
# 1e9 (the old hard wall) +$5,182 at 13/16, 60 and 0 landed in noise. The penalty value
# itself is NOT separable at this sample size -- what is solid is that optimal assignment
# beats greedy regardless of it.
ROLE_PENALTY = 0.0

# Herd sized to what the ranchers can actually SERVICE. Geese stay at 0 -- an egg is
# ~$60 against milk at ~$260 for the same three actions a day, and an all-goose farm
# measured $53.8k against $99.4k.
# A4 (joint search, absolute money across a 2-opponent panel) moved this from 9/7 to
# 7/8: SHEEP-leaning, not cow-leaning. Wool's glut curve is `sq` and floors after 59
# units, so a big wool herd is only safe because the yarn store drains 12/day -- and the
# optimal assignment now services the herd well enough that the extra sheep get fed.
MAX_COW, MAX_SHEEP, MAX_GOOSE = 7, 8, 0

# Strawberry is the largest block on the farm: the only product whose town drain
# (~32/day) is far above what a farm supplies (0.25/day per tile), so it never crushes
# its own price. A4 raised it 30 -> 33. Note single-parameter sweeps under the OLD greedy
# scheduler said 36 and 44 were worse; that was true of that scheduler, not this one.
MAX_STRAWBERRY = 40

# Melon is an OPENING, not a strategy. No shop demands it, so its only buyer is the town
# centre (2-8/day) and its glut curve is `sq`: ~90 units halves the price, ~158 floors
# it. A4 trimmed the block 10 -> 8 -- with a bigger strawberry block competing for the
# same early labour, the marginal melon tile stopped paying for itself.
MAX_MELON = 8
# Feed is BOUGHT, not grown. Growing it looks cheaper (a wheat tile yields ~1
# wheat/day and buying costs $40-58 once your own purchases walk the price up
# the scarcity curve) -- but measured head-to-head, switching a herd-sized wheat
# block on cost ~$11k, because those tiles' real price is the unit-turns spent
# watering them. Labour, not cash, is the binding constraint.
MAX_WHEAT = 6
# Carrot is a LATE-GAME SINK, not part of the core mix. Once strawberry's
# planting window shuts the farm runs out of jobs -- measured 54-68 PASS turns a
# day in the last week, against ~5 for a top agent. A carrot is 3 units x ~$42
# for ~5 actions, i.e. ~$25/action: far below milk, far above idling.
MAX_CARROT = 0
# A3 opponent-aware rotation. The town's milk/wool drain is a shared standing bid, so
# two farms both running cows split it and ride the price down together. Rotate toward
# whichever the opponent is running LESS of.
ROTATE_FROM_DAY = 4   # before this nobody has a herd worth reading
ROTATE_GAP = 3        # ignore differences this small -- noise, not a strategy signal
ROTATE_MAX = 4        # cap the swing; a wholesale flip churns the layout for nothing
SHED_CAP = 100        # engine `shedCapacity`; a full shed now BLOCKS buying too
LAST_DAY = 29
CYCLE = {"WHEAT": 4, "CARROT": 3, "MELON": 10, "TOMATO": 11, "STRAWBERRY": 16}


def _shape(f, x):
    x = max(0.0, x)
    if f == "linear":
        return x
    if f == "sq":
        return x * x
    if f == "sqrt":
        return math.sqrt(x)
    if f == "log":
        return math.log(1.0 + x)
    return x


def price_at(item, inv):
    p = MP[item]
    if inv < I0:
        amp = p["bt"] * p["base"] / _shape(p["bf"], p["T"])
        v = p["base"] + amp * _shape(p["bf"], I0 - inv)
    else:
        amp = p["at"] * p["base"] / _shape(p["af"], p["T"])
        v = p["base"] - amp * _shape(p["af"], inv - I0)
    return max(1, int(round(v)))


def fib_sum(k):
    a, b, s = 1, 1, 0
    for _ in range(k):
        s += a
        a, b = b, a + b
    return s


def bfs(tiles, start, n, through_locked=False):
    """Step distances. LOCKED is a wall by default, a corridor when escaping one.

    Engine 1.32.4 legalised MOVING onto locked tiles (tile operations still no-op
    there). Tried as a general routing shortcut -- owned land is often L-shaped, so
    cutting through a locked quadrant looked like a free win -- and measured
    \\$97,668 vs \\$101,896 over 16 seeds: no gain, slightly worse. Land gets bought
    early, so the L-shape window is short and the shortcut rarely pays.

    It is still needed for one case. A hand can spawn on a locked shed-access tile,
    and `(5,5)` -- the one diagonally opposite the starting quadrant -- has ALL FOUR
    orthogonal neighbours locked. Treating locked as a wall strands that hand for the
    whole game. So: wall for routing, corridor for escape.
    """
    dist = {start: 0}
    q, head = [start], 0
    while head < len(q):
        x, y = q[head]
        head += 1
        d = dist[(x, y)] + 1
        for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < n and (nx, ny) not in dist \
                    and (through_locked or tiles[ny][nx] != "LOCKED"):
                dist[(nx, ny)] = d
                q.append((nx, ny))
    return dist


def move_towards(tiles, start, goal, n, field=None, through_locked=False):
    if start == goal:
        return None
    back = field if field is not None else bfs(tiles, goal, n, through_locked)
    best = None
    for op, (dx, dy) in DIRS.items():
        nx, ny = start[0] + dx, start[1] + dy
        if not (0 <= nx < n and 0 <= ny < n):
            continue
        if not through_locked and tiles[ny][nx] == "LOCKED":
            continue
        d = back.get((nx, ny))
        if d is not None and (best is None or d < best[0]):
            best = (d, op)
    return best[1] if best else None


def lap_max(w, neg=-1e9):
    """Optimal max-weight assignment of rows (units) to columns (tasks).

    Replaces a single-pass greedy match. Greedy on sorted (unit, task) pairs has a
    proven competitive ratio of only 1/3 on online weighted bipartite matching; at our
    scale -- at most 13 units against a few dozen live tasks -- the true optimum is
    computable every turn in well under a millisecond, so there is no reason to accept
    a third of it.

    Pure Python on purpose: scipy.optimize.linear_sum_assignment would do this, but I
    cannot verify scipy is in the competition image and an ImportError at submit time
    scores zero. numpy is not needed either.

    This is the classic O(n^2 m) Hungarian with potentials (shortest augmenting path).
    It requires rows <= cols, so columns are padded with zero-value dummies -- a unit
    matched to a dummy simply has nothing worth doing this turn.

    Returns a list `res` with res[row] = col, or -1 if that unit got no real task.
    """
    n = len(w)
    if n == 0:
        return []
    m0 = len(w[0])
    # ONE DUMMY COLUMN PER UNIT, always. The Hungarian below produces a perfect matching
    # on rows, so every unit must be assignable to something. With only max(n, m0)
    # columns there are no dummies whenever tasks outnumber units, and the solver is then
    # forced to hand a unit a task that is infeasible or worth less than idling -- which
    # made it measurably sub-optimal (27 mismatches in 300 brute-force comparisons).
    # m0 + n columns guarantees idling is always available at value 0.
    m = m0 + n
    INF = float("inf")
    a = [[(-w[i][j] if w[i][j] > neg else 1e18) if j < m0 else 0.0
          for j in range(m)] for i in range(n)]
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            for j in range(1, m + 1):
                if not used[j]:
                    cur = a[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            if j1 < 0:
                break
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    res = [-1] * n
    for j in range(1, m + 1):
        r = p[j]
        if r and j - 1 < m0 and w[r - 1][j - 1] > neg:
            res[r - 1] = j - 1
    return res


def needs_water(t, day):
    """Water only when it buys something: survival, or a yield bonus.
    Ongoing crops get NO watering bonus, so strawberry only needs survival
    watering -- every other day. That halves the cost of the strawberry block."""
    if t["watered_today"]:
        return False
    if t["consecutive_unwatered"] >= 1:
        return True
    c = CROPS[t["crop"]]
    if c["ongoing"]:
        return False
    age = day - t["planted_day"]
    return (c["maxday"] + 1) // 2 <= age <= c["maxday"] and t["yield_units"] < c["maxy"]


def ripe(t, day):
    c = CROPS[t["crop"]]
    if t["yield_units"] <= 0:
        return False
    age = day - t["planted_day"]
    if age < c["first"]:
        return False
    if c["ongoing"]:
        return True
    return age >= c["maxday"] or t["yield_units"] >= c["maxy"]


def agent(obs):
    p = obs["player"]
    me = obs["farms"][p]
    priv = obs["private"]
    tiles = me["tiles"]
    n = len(tiles)
    day, hour = obs["day"], obs["hour"]
    money = me["money"]
    shed = dict(priv["shed"])
    seeds = dict(priv["seeds"])
    invs = [dict(i) for i in priv["inventories"]]
    minv = obs["market"]["inventory"]

    h = n // 2
    home_tiles = [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]
    open_home = [t for t in home_tiles if tiles[t[1]][t[0]] != "LOCKED"]
    home_set = set(open_home)
    units = [tuple(me["farmer"])] + [tuple(hd) for hd in me["hands"]]
    market = []
    endgame = day >= LAST_DAY

    # A3: census the opponent's livestock. Their tiles are fully visible; only the shed
    # is private. Cheap -- one pass over 100 tiles, and only at hour 0 when the herd
    # decision is actually made.
    opp_stock = {}
    if hour == 0 and len(obs["farms"]) > 1:
        opp_tiles = obs["farms"][1 - p].get("tiles") or []
        for row in opp_tiles:
            for t in row:
                if isinstance(t, dict) and t.get("animal"):
                    opp_stock[t["animal"]] = opp_stock.get(t["animal"], 0) + 1

    # ---------------------------------------------------------------- scan
    empty, plants, weeds, animals = [], [], [], []
    free_coop, free_pasture = [], []
    counts = dict.fromkeys(list(ANIMALS) + list(CROPS), 0)
    for y in range(n):
        for x in range(n):
            t = tiles[y][x]
            if t == "LOCKED":
                continue
            if t is None:
                empty.append((x, y))
            elif t["kind"] == "WEED":
                weeds.append((x, y))
            elif t["kind"] == "PLANT":
                plants.append((x, y, t))
                counts[t["crop"]] += 1
            elif t.get("animal"):
                animals.append((x, y, t))
                counts[t["animal"]] += 1
            elif t["kind"] == "COOP":
                free_coop.append((x, y))
            else:
                free_pasture.append((x, y))

    n_animals = len(animals)
    pending = {a: shed.get(a, 0) + sum(i.get(a, 0) for i in invs) for a in ANIMALS}
    n_pending = sum(pending.values())
    herd = n_animals + n_pending
    # Two missed days kills an animal permanently, so carry a real buffer.
    wheat_reserve = 0 if endgame else int(1.5 * herd) + 6
    cash_floor = 120 + 15 * herd

    # ============================ MARKET =====================================
    # HIRING IS DELIBERATELY CAPPED AT 10 HANDS. Only 10 market orders are
    # processed per turn and HIRE shares that budget with SELL, so hiring at
    # hour 0 alone is a hard ceiling of 10 however rich the farm gets. That looks
    # like a bug -- the reference agent runs 12 -- and it is not. Measured, 8
    # paired seeds:
    #     hour 0 only (this)                 $99,408
    #     hours 0-1, hires_today guarded     $85,454
    #     hours 0-1, ceiling raised to 16    $74,118
    # Hands cost fib(n) and reset daily, so the 11th and 12th are expensive and
    # arrive with nothing to do. Widening this window WITHOUT the hires_today
    # guard is worse again ($11,374): it simply buys a second full batch at hour 1.
    if hour == 0 and day < LAST_DAY:
        budget = max(200, 0.06 * money)
        want = 0
        while want < 14 and fib_sum(want + 1) <= budget:
            want += 1
        work = (sum(1 for _, _, t in plants if not t["watered_today"] or t["yield_units"] > 0)
                + min(len(empty), sum(seeds.values()) + 6) + 5 * n_animals)
        # Swept: a floor of 6 hands and one extra hand per 6 pending jobs beat
        # (4, //7) by ~$18k. Under-hiring is the more expensive mistake -- an
        # idle hand costs a few dollars, an unfed cow costs $400 plus its output.
        # A top agent runs a flat 12 hands from day 12 to the end -- it does not
        # try to be clever about workload. Hands cost fib(n) and reset daily, so
        # 12 of them is ~$376/day against a farm turning over $8k/day. Sizing to
        # an estimate of "work" under-hires exactly when the farm is richest.
        want = max(6, min(want, 3 + work // 6))
        for _ in range(min(want, 10)):
            market.append(["HIRE"])
    if hour != 0:
        # ------------------------------------------------- 1. feed (highest)
        # SHED CAPACITY IS NOW A HARD GATE ON BUYING. Engine 1.32.4 made
        # BUY_PRODUCT and BUY_ANIMAL respect shedCapacity -- a buy into a full shed
        # simply returns False. Measured on 1.32.4 before this fix: our shed sat at
        # the 100 cap (the 1360 reference peaks at 79), so feed purchases were
        # silently failing and the herd starved. Never request more than fits.
        shed_used = sum(v for v in shed.values() if v > 0)
        headroom = max(0, SHED_CAP - shed_used)
        wheat_stock = shed.get("WHEAT", 0) + sum(i.get("WHEAT", 0) for i in invs)
        if herd and not endgame and wheat_stock < wheat_reserve:
            px = price_at("WHEAT", minv["WHEAT"] - 1)
            need = min(wheat_reserve + 6 - wheat_stock, int(money // max(1, px)),
                       headroom)
            if need > 0:
                market.append(["BUY_PRODUCT", "WHEAT", need])
                money -= px * need
                headroom -= need

        # ------------------------------------------------------------ 2. land
        # Before livestock, not after: 25 tiles for $1k is the cheapest thing on
        # the board, and a herd with nowhere to stand is dead capital.
        n_extra = len(me["unlocked_quadrants"]) - 1
        room_now = len(empty) + len(free_pasture) + len(free_coop)
        # THREE quadrants, never four. The 4th costs $4k and buys 25 tiles you
        # have no labour to work -- it just lengthens every walk.
        if n_extra < 3 and day <= 18 and room_now < 10:
            cost = (1000, 2000, 4000)[n_extra]
            if money >= cost + 250:
                market.append(["BUY_LAND"])
                money -= cost
                room_now += 25

        # ------------------------------------------------- 3. livestock
        # Bought early: a cow placed on day 0 produces from day 8 and then every
        # 2 days at ~$250/unit, so every day of delay is a lost cycle. But NEVER
        # buy more than there is room to house -- an animal sitting in the shed
        # is $400 doing nothing, and it silently starves the cash flow.
        # Herd SCHEDULE, not just a cap. Livestock and the strawberry block
        # compete for the same early cash, and strawberry's planting window
        # shuts on day 13 (16-day cycle) -- so an unrestrained herd eats the
        # bank until the window has closed. Staging the herd is worth more than
        # getting to full size two days sooner.
        # NO STAGING. This is a full reversal: under the greedy scheduler, staging the
        # herd over days 6/10 measured +$8k and is documented in the playbook as worth
        # keeping. Under optimal assignment it measures -$12,013 at 7/8 wins. Staging
        # existed because greedy could not service a large herd -- it starved ranchers of
        # animal jobs -- so growing slowly avoided owning animals that would go unfed.
        # An optimal assignment services them, so staging now only delays income.
        herd_cap = MAX_COW + MAX_SHEEP + MAX_GOOSE
        # A3: OPPONENT-AWARE HERD MIX. The town's drain for milk and wool is a fixed
        # standing bid, and it is SHARED. If both farms pile into cows, the milk drain
        # splits and both sides ride the price down together -- textbook Cournot. Their
        # tiles are visible, so read what they are running and lean the other way.
        # Only cow/sheep rotate: melon, wheat and carrot sit on the glut side whatever
        # the opponent does, so there is nothing to differentiate there.
        cow_cap, sheep_cap = MAX_COW, MAX_SHEEP
        if opp_stock and day >= ROTATE_FROM_DAY:
            gap = opp_stock.get("COW", 0) - opp_stock.get("SHEEP", 0)
            # threshold, not a reflex: a couple of animals' difference is noise, and
            # re-planning the herd every day would churn the layout for nothing
            if abs(gap) >= ROTATE_GAP:
                shift = min(ROTATE_MAX, abs(gap) // 2)
                if gap > 0:          # they are cow-heavy -> take the wool side
                    cow_cap, sheep_cap = MAX_COW - shift, MAX_SHEEP + shift
                else:
                    cow_cap, sheep_cap = MAX_COW + shift, MAX_SHEEP - shift
        if day <= 21 and n_pending == 0:
            for a, cap in (("COW", cow_cap), ("SHEEP", sheep_cap), ("GOOSE", MAX_GOOSE)):
                spec = ANIMALS[a]
                prods = (LAST_DAY - (day + spec["first"])) // spec["interval"] + 1
                if prods < 3 or room_now <= 1 or herd >= herd_cap:
                    continue
                need = cap - counts[a] - pending[a]
                if need <= 0:
                    continue
                afford = int((money - cash_floor) // spec["cost"])
                buy = max(0, min(need, afford, 3, room_now - 1, herd_cap - herd))
                if buy > 0:
                    market.append(["BUY_ANIMAL", a, buy])
                    money -= buy * spec["cost"]
                    pending[a] += buy
                    n_pending += buy
                    herd += buy
                    room_now -= buy

        # ----------------------------------------------------------- 4. seeds
        room = len(empty) + len(weeds)
        want_seed = {}
        # Melon FIRST, and on day 0. It is the bootstrap: $80 of seed becomes 6
        # melons on day 10, so a 10-tile block is a ~$14k payday exactly when the
        # herd starts eating and the strawberry block needs paying for. Strawberry
        # seed is $100 each -- buying 30 up front eats the entire bank and the
        # melon window closes.
        if day <= LAST_DAY - CYCLE["MELON"]:
            want_seed["MELON"] = max(0, MAX_MELON - counts["MELON"] - seeds.get("MELON", 0))
        # No cash gate, and the window is much wider than "must fit 4 productions".
        # A strawberry planted on day 19 still yields once on day 29 -- $250 for
        # $100 of seed. Cutting off at day 13 throws away six days of planting.
        if day <= LAST_DAY - CYCLE["STRAWBERRY"]:
            want_seed["STRAWBERRY"] = max(
                0, MAX_STRAWBERRY - counts["STRAWBERRY"] - seeds.get("STRAWBERRY", 0))
        if day <= LAST_DAY - CYCLE["WHEAT"]:
            want_seed["WHEAT"] = max(0, MAX_WHEAT - counts["WHEAT"] - seeds.get("WHEAT", 0))
        for crop in ("MELON", "STRAWBERRY", "WHEAT"):
            want = min(want_seed.get(crop, 0), room)
            c = CROPS[crop]["seed"]
            want = min(want, int(max(0, money - cash_floor) // c))
            if want > 0:
                market.append(["BUY_SEED", crop, want])
                money -= c * want
                seeds[crop] = seeds.get(crop, 0) + want
                room -= want

        # --------------------------------------------------------- 5. selling
        # Sell down to a reserve price, never past it. The whole strategy is to
        # stay on the scarcity side of the curve, so a sale that would push a
        # product below its base price is a sale we simply don't make.
        # Reserve price per product, as a fraction of base. These are NOT all the
        # same number, because the products are not the same shape: wheat/egg
        # barely move when you sell so a high floor costs nothing, while milk and
        # wool have steep linear/sq glut curves where insisting on a high price
        # just means never selling. Holding out is only free if the price
        # recovers -- and at turn 720 unsold stock is worth exactly $0.
        # Measured, against a strong opponent: dropping the reserve prices to
        # RESERVE (milk 0.42 x base, wool 0.40) LOSES ~$11k versus holding out
        # near base. Milk, wool and strawberry sit on the scarcity side of the
        # curve all season, so patience genuinely pays -- right up until the last
        # day, when unsold stock scores $0 and the floor has to collapse.
        # A flat floor, not the old three-stage climbdown. Measured +$9,473 at 8/8 wins
        # once the scheduler became optimal (A1). The staged version was compensating
        # for greedy assignment: it under-sold early because produce was reaching the
        # shed erratically, so it held out for higher prices to make up the difference.
        # With work actually getting done on time that hedge is pure cost.
        keep = 0.0 if endgame else 0.85
        # A full shed is not just lost produce any more -- on 1.32.4 it also blocks
        # BUY_PRODUCT, so it starves the herd. When the shed is nearly full, drop the
        # reserve price: taking a merely-good price beats holding stock that stops us
        # buying feed. Below ~70% full this does nothing.
        if not endgame and sum(v for v in shed.values() if v > 0) > 0.70 * SHED_CAP:
            keep = min(keep, 0.55)
        orders = []
        for item in SELLABLE:
            held = shed.get(item, 0)
            if held <= 0:
                continue
            if item == "WHEAT":
                if endgame:
                    pass
                else:
                    continue                      # wheat is feed, not income
            # Fertilizer is the exception: no shop and not the town centre
            # consumes it, so its price only ever falls. Nothing to wait for.
            floor = MP[item]["base"] * (min(keep, 0.30) if item == "FERTILIZER" else keep)
            inv0 = minv[item]
            q = 0
            while q < held and price_at(item, inv0 + q) >= floor:
                q += 1
            if q:
                orders.append((price_at(item, inv0) * q, item, q))
        orders.sort(reverse=True)
        for _, item, q in orders:
            market.append(["SELL", item, q])
    market = market[:10]

    # ============================ TASKS ======================================
    # (value_per_action, pos, op, requirement). Values are dollars, from live
    # market prices, so unlike a priority tier they are directly comparable.
    px = obs["market"]["prices"]
    tasks = []

    for (x, y, t) in animals:
        a = ANIMALS[t["animal"]]
        unit_px = px[a["product"]]
        per_day = (1 + a["interval"]) / a["interval"]          # with CARE
        if t["yield_units"] > 0:
            # held yield is capped at max_held: unharvested production is lost
            urgency = 2.0 if t["yield_units"] >= a["max_held"] else 1.0
            tasks.append((t["yield_units"] * unit_px * urgency, (x, y), ["HARVEST"], None))
        if not t["fed_today"] and not endgame:
            # missing a day costs a production; missing two costs the animal
            v = per_day * unit_px * (12.0 if t["consecutive_unfed"] >= 1 else 1.0)
            tasks.append((v, (x, y), ["FEED"], "WHEAT"))
        if not t["cared_today"] and day < LAST_DAY - 1:
            # CARE banks exactly +1 unit, paid on the next production
            tasks.append((unit_px, (x, y), ["CARE"], None))
        if t.get("fertilizer_available"):
            tasks.append((px["FERTILIZER"], (x, y), ["COLLECT_FERTILIZER"], None))

    for (x, y, t) in plants:
        c = CROPS[t["crop"]]
        unit_px = px[t["crop"]]
        if ripe(t, day):
            tasks.append((t["yield_units"] * unit_px, (x, y), ["HARVEST"], None))
        if needs_water(t, day) and not endgame:
            if t["consecutive_unwatered"] >= 1:
                # watering saves the whole plant, not just today's increment
                remaining = max(1, c["maxy"] - t["yield_units"])
                v = remaining * unit_px * 0.8
            else:
                v = (2 if t.get("fertilized_until_day", -1) >= day else 1) * unit_px
            tasks.append((v, (x, y), ["WATER"], None))

    for a in ("COW", "SHEEP", "GOOSE"):
        spec = ANIMALS[a]
        spots = free_pasture if spec["structure"] == "PASTURE" else free_coop
        prods = max(0, (LAST_DAY - (day + spec["first"])) // spec["interval"] + 1)
        # placing unlocks the animal's whole remaining output
        v = max(200.0, prods * (1 + spec["interval"]) * px[spec["product"]] * 0.30)
        for i in range(min(pending[a], len(spots))):
            tasks.append((v, spots[i], ["PLACE", a], a))

    need_pasture = max(0, pending["COW"] + pending["SHEEP"] - len(free_pasture))
    need_coop = max(0, pending["GOOSE"] - len(free_coop))

    plan = ["PASTURE"] * need_pasture + ["COOP"] * need_coop
    if day <= LAST_DAY - CYCLE["MELON"]:
        plan += ["MELON"] * min(max(0, MAX_MELON - counts["MELON"]), seeds.get("MELON", 0))
    if day <= LAST_DAY - CYCLE["STRAWBERRY"]:
        plan += ["STRAWBERRY"] * min(max(0, MAX_STRAWBERRY - counts["STRAWBERRY"]),
                                     seeds.get("STRAWBERRY", 0))
    if day <= LAST_DAY - CYCLE["WHEAT"]:
        plan += ["WHEAT"] * min(max(0, MAX_WHEAT - counts["WHEAT"]), seeds.get("WHEAT", 0))

    # Per-action value of starting a crop: lifetime profit / actions it will cost.
    # Units are computed from the days actually remaining, so a late strawberry
    # is priced at the one or two productions it will really fire, not four.
    PLANT_ACTIONS = {"MELON": 10.0, "STRAWBERRY": 13.0, "WHEAT": 6.0, "CARROT": 5.0}
    PLANT_UNITS = {"MELON": 6, "STRAWBERRY": 4, "WHEAT": 4, "CARROT": 3}

    # Allocate everything nearest-first, in plan order: structures, then melon,
    # then strawberry. Deliberately banishing "low-touch" crops to the far
    # corners was right under a priority-tier scheduler and is WRONG under a
    # cost-based one -- planting a melon is worth ~$142/action, so at
    # TRAVEL_COST=22 a tile 7 steps away scores negative and simply never gets
    # planted. Let the cost model do the placement; it already prices distance.
    home_field = bfs(tiles, open_home[0] if open_home else (0, 0), n)

    # RESERVE a compact animal zone: the N tiles closest to the shed, where N is
    # the maximum herd. Crops may never use them. Without this the herd sprawls,
    # because structures are only built when an animal is bought and by then the
    # near tiles are full of strawberries -- and a scattered herd is what makes
    # ranchers spend their whole day walking instead of feeding.
    # Measured: the reference feeds 15/15 animals every day; a sprawling 23-head
    # herd of mine managed 14-18, so a third of it was quietly under-producing.
    owned_sorted = sorted(
        (pt for pt in ((x, y) for y in range(n) for x in range(n))
         if tiles[pt[1]][pt[0]] != "LOCKED"),
        key=lambda pt: home_field.get(pt, 99))
    zone = set(owned_sorted[:MAX_COW + MAX_SHEEP + MAX_GOOSE])

    near_all = sorted(empty, key=lambda pt: home_field.get(pt, 99))
    near_animal = [p for p in near_all if p in zone]
    near_crop = [p for p in near_all if p not in zone] + [p for p in near_all if p in zone]
    ai = ci = 0
    used = set()
    for what in plan:
        is_struct = what in ("PASTURE", "COOP")
        src = near_animal if is_struct else near_crop
        pos = None
        idx = ai if is_struct else ci
        while idx < len(src):
            cand = src[idx]
            idx += 1
            if cand not in used:
                pos = cand
                break
        if is_struct:
            ai = idx
        else:
            ci = idx
        if pos is None:
            continue
        used.add(pos)
        if what == "PASTURE":
            tasks.append((400.0, pos, ["BUILD_PASTURE"], None))
        elif what == "COOP":
            tasks.append((250.0, pos, ["BUILD_COOP"], None))
        else:
            v = (PLANT_UNITS[what] * px[what] - CROPS[what]["seed"]) / PLANT_ACTIONS[what]
            tasks.append((max(5.0, v), pos, ["PLANT", what], "SEED:" + what))

    # a weed is only worth clearing if we actually want to plant on it
    if len(empty) < 4 and day <= LAST_DAY - CYCLE["WHEAT"]:
        for pos in weeds:
            tasks.append((30.0, pos, ["DIG"], None))

    # ========================== ASSIGNMENT ===================================
    # Global greedy over every (unit, task) pair, scored in dollars:
    #     net = value - TRAVEL_COST * steps_to_get_there
    # Assigning globally rather than unit-by-unit also kills the task churn that
    # made an earlier scheduler spend two thirds of its unit-turns walking:
    # the result no longer depends on the order units are considered in.
    animal_pos = {(x, y) for x, y, _ in animals}
    animal_tasks = {i for i, t in enumerate(tasks)
                    if t[2][0] in ("FEED", "CARE", "COLLECT_FERTILIZER")
                    or (t[2][0] == "HARVEST" and t[1] in animal_pos)}
    # FEED takes wheat from the ACTING unit's inventory, so livestock needs
    # dedicated units that keep wheat in hand, or the herd starves.
    # A top agent lands FEED=CARE=COLLECT=15 for a 15-head herd, every day.
    # At one rancher per 3 animals mine managed 12 of 15 -- and a cow that eats
    # every other day produces every other cycle. Budget one per 2.5 instead.
    n_ranch = (0 if not animals else
               min(max(1, len(units) - 2), max(1, -(-len(animals) // 3))))

    ops = [None] * len(units)
    seed_left = dict(seeds)
    inv_of = {}
    fields = {}
    for idx, pos in enumerate(units):
        inv_of[idx] = invs[idx] if idx < len(invs) else {}

    # --- logistics first: these units are not available for field work -------
    busy = set()
    for idx, pos in enumerate(units):
        inv = inv_of[idx]
        rancher = idx < n_ranch
        on_locked = tiles[pos[1]][pos[0]] == "LOCKED"
        at_home = (pos in home_set) and not on_locked
        # a rancher's wheat is FEED, not produce -- counting it as produce makes
        # the unit PICKUP then DROP forever on the shed tile
        produce = sum(v for k2, v in inv.items()
                      if k2 in SELLABLE and not (rancher and k2 == "WHEAT"))
        op = None
        if on_locked:
            goal = min(home_set, key=lambda hh: abs(hh[0] - pos[0]) + abs(hh[1] - pos[1])) \
                if home_set else None
            # through_locked: the whole point. A hand spawned on (5,5) has every
            # orthogonal neighbour locked, so a wall-respecting path never gets it out.
            mv = move_towards(tiles, pos, goal, n, through_locked=True) if goal else None
            op = [mv] if mv else ["PASS"]
        elif at_home:
            if rancher and inv.get("WHEAT", 0) < 2 and shed.get("WHEAT", 0) > 0 and not endgame:
                # FAIR SHARE, not "everything". Taking `len(animals) + 2` means
                # the first rancher to reach the shed walks off with the entire
                # day's feed and the other four find it empty -- which is
                # precisely why feeding was landing at 12 of 15 animals a day,
                # and an unfed animal produces nothing AND loses its care bonus.
                per_ranch = -(-len(animals) // max(1, n_ranch)) + 2
                take = min(per_ranch, shed["WHEAT"])
                if take > 0:
                    shed["WHEAT"] -= take
                    inv["WHEAT"] = inv.get("WHEAT", 0) + take
                    op = ["PICKUP", "WHEAT", take]
            elif produce >= 3 or (hour >= 20 and produce > 0):
                op = ["DROP"]
            if op is None and not rancher and not any(inv.get(a, 0) for a in ANIMALS):
                for a in ("COW", "SHEEP", "GOOSE"):
                    if shed.get(a, 0) > 0 and any(t[3] == a for t in tasks):
                        shed[a] -= 1
                        inv[a] = inv.get(a, 0) + 1
                        op = ["PICKUP", a, 1]
                        break
        elif produce >= 8 or (hour >= 20 and produce >= 2):
            goal = min(home_set, key=lambda hh: abs(hh[0] - pos[0]) + abs(hh[1] - pos[1]))
            mv = move_towards(tiles, pos, goal, n)
            op = [mv] if mv else None
        if op is not None:
            ops[idx] = op
            busy.add(idx)

    # --- score every remaining (unit, task) pair -----------------------------
    free_units = [i for i in range(len(units)) if i not in busy]
    for idx in free_units:
        fields[idx] = bfs(tiles, units[idx], n)

    # Build the full (unit x task) value matrix, then solve it optimally instead of
    # walking a sorted list. The ranch/crop split becomes a PRICE rather than a wall:
    # the old hard filter meant ~5 reserved ranchers covered ~45 animal jobs a day and
    # then idled -- measured at 952 idle unit-turns while 44 tiles rotted into weeds --
    # because they were forbidden from watering. With a joint optimum a rancher waters a
    # dying strawberry exactly when no animal task outbids it, which is the behaviour
    # the wall was crudely approximating.
    NEG = -1e9
    W = []
    for idx in free_units:
        inv = inv_of[idx]
        rancher = idx < n_ranch
        d = fields[idx]
        row = []
        for i, (val, tpos, top, req) in enumerate(tasks):
            ok = tpos in d
            if ok and req == "WHEAT" and inv.get("WHEAT", 0) <= 0:
                ok = False
            if ok and req in ANIMALS and inv.get(req, 0) <= 0:
                ok = False
            if ok and req and req.startswith("SEED:") and seed_left.get(req[5:], 0) <= 0:
                ok = False
            if not ok:
                row.append(NEG)
                continue
            net = val - TRAVEL_COST * d[tpos]
            if (i in animal_tasks) != rancher:
                net -= ROLE_PENALTY
            row.append(net)
        W.append(row)

    assign = lap_max(W, NEG)

    # The atomic-PLANT rule makes over-committing seeds catastrophic rather than merely
    # wasteful: if the PLANT ops issued in one turn exceed the seeds held, EVERY one of
    # them is silently dropped. The optimum is computed without that global constraint,
    # so cap per crop here, keeping the highest-value plantings.
    plant_bids = {}
    for r, i in enumerate(assign):
        if i < 0:
            continue
        req = tasks[i][3]
        if req and req.startswith("SEED:"):
            plant_bids.setdefault(req[5:], []).append((W[r][i], r))
    dropped = set()
    for crop, bids in plant_bids.items():
        cap = seed_left.get(crop, 0)
        if len(bids) > cap:
            bids.sort(reverse=True)
            dropped.update(r for _, r in bids[cap:])

    for r, i in enumerate(assign):
        idx = free_units[r]
        if i < 0 or r in dropped:
            continue
        val, tpos, top, req = tasks[i]
        pos = units[idx]
        inv = inv_of[idx]
        if pos == tpos:
            ops[idx] = top
            if req == "WHEAT":
                inv["WHEAT"] = inv.get("WHEAT", 0) - 1
            elif req in ANIMALS:
                inv[req] = inv.get(req, 0) - 1
            elif req and req.startswith("SEED:"):
                seed_left[req[5:]] -= 1
        else:
            mv = move_towards(tiles, pos, tpos, n)
            ops[idx] = [mv] if mv else ["PASS"]

    for idx in free_units:
        if ops[idx] is None:
            pos = units[idx]
            if pos not in home_set and home_set:
                goal = min(home_set, key=lambda hh: abs(hh[0] - pos[0]) + abs(hh[1] - pos[1]))
                mv = move_towards(tiles, pos, goal, n)
                ops[idx] = [mv] if mv else ["PASS"]
            else:
                ops[idx] = ["PASS"]

    return {"farmer": ops[0], "hands": ops[1:len(units)], "market": market}

# kaggle-environments calls the LAST callable defined in this file, not the one
# named `agent`. Never add a helper below this line.

# Kaggle's notebook "Submit to Competition" button looks for submission.py in
# /kaggle/working; the CLI (`kaggle competitions submit -f main.py`) wants main.py.
import shutil
shutil.copyfile("main.py", "submission.py")
print("wrote submission.py")

I0 = 10000
MP = {
    "WHEAT":      dict(base=25,  T=400, bf="sqrt",   bt=0.80, af="log",    at=0.20),
    "CARROT":     dict(base=35,  T=450, bf="log",    bt=0.20, af="sqrt",   at=0.70),
    "TOMATO":     dict(base=60,  T=200, bf="linear", bt=0.40, af="sqrt",   at=0.60),
    "STRAWBERRY": dict(base=120, T=100, bf="sqrt",   bt=0.70, af="linear", at=1.60),
    "MELON":      dict(base=250, T=300, bf="log",    bt=0.20, af="sq",     at=3.60),
    "EGG":        dict(base=50,  T=332, bf="linear", bt=0.40, af="log",    at=0.20),
    "MILK":       dict(base=160, T=122, bf="sqrt",   bt=0.60, af="linear", at=1.60),
    "WOOL":       dict(base=200, T=105, bf="log",    bt=0.20, af="sq",     at=3.20),
    "FERTILIZER": dict(base=100, T=200, bf="linear", bt=0.40, af="linear", at=0.40),
}
F = {"linear": lambda x: x, "sq": lambda x: x * x, "sqrt": math.sqrt,
     "log": lambda x: math.log(1 + x)}


def price_at(item, inv):
    """price(inv) = base +- amp * f(|inv - I0|);  amp = target * base / f(T)."""
    p = MP[item]
    if inv < I0:
        amp = p["bt"] * p["base"] / F[p["bf"]](p["T"])
        v = p["base"] + amp * F[p["bf"]](I0 - inv)
    else:
        amp = p["at"] * p["base"] / F[p["af"]](p["T"])
        v = p["base"] - amp * F[p["af"]](inv - I0)
    return max(1, round(v))


def depth(item):
    """Units sellable before the price halves, and before it hits the $1 floor."""
    inv, half, floor = I0, None, None
    b = MP[item]["base"]
    for k in range(1, 4001):
        px = price_at(item, inv)
        if half is None and px <= b / 2:
            half = k
        if px <= 1:
            floor = k
            break
        inv += 1
    return half, (floor or ">4000")


print("price model loaded; sanity check against the published table:")
for it in ("WHEAT", "MELON", "MILK"):
    T = MP[it]["T"]
    print(f"  {it:<11} P(I0-T)=${price_at(it, I0-T):>4}  P(I0)=${price_at(it, I0):>4}  "
          f"P(I0+T)=${price_at(it, I0+T):>4}")

SHOP_DEMAND = {
    "BAKERY":         {"EGG": 1, "WHEAT": 1},
    "PIZZA_SHOP":     {"MILK": 1, "TOMATO": 1, "WHEAT": 1},
    "BRUNCH_SPOT":    {"EGG": 1, "WHEAT": 1, "STRAWBERRY": 1},
    "YARN_STORE":     {"WOOL": 2},
    "ICE_CREAM_SHOP": {"STRAWBERRY": 1, "MILK": 1, "WHEAT": 1},
    "PET_CAFE":       {"CARROT": 2},
    "SMOOTHIE_SHOP":  {"STRAWBERRY": 1, "MILK": 1},
    "FARMERS_MARKET": {"WHEAT": 1, "CARROT": 1, "TOMATO": 1, "STRAWBERRY": 1},
}
# what ONE tile (or one animal, including its CARE bonus) supplies per day
SUPPLY = {"MILK": 1.5, "WOOL": 4/3, "STRAWBERRY": 0.25, "EGG": 2.0,
          "MELON": 0.6, "WHEAT": 1.0, "CARROT": 1.0, "TOMATO": 4/11}

rows = []
for prod, per in SUPPLY.items():
    shop = sum(v.get(prod, 0) for v in SHOP_DEMAND.values()) * 6   # 6 ticks/day
    drain = shop + 8                                               # + town centre, day 20+
    h, fl = depth(prod)
    rows.append(dict(product=prod, drain_per_day=drain,
                     supply_per_unit=round(per, 2),
                     headroom_units=round(drain / per, 1),
                     halves_after=h, floors_after=fl))
pd.DataFrame(rows).sort_values("headroom_units", ascending=False)

def price_history(agent_a="main.py", agent_b="starter", steps=720, seed=7):
    """Actual market prices over a whole season -- theory is nice, this is what happened."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
        env.run([agent_a, agent_b])
    rows = []
    for st in env.steps:
        o = st[0]["observation"]
        if "farms" not in o or o["step"] % 24:
            continue
        rows.append(dict(day=o["day"], money=o["farms"][0]["money"],
                         **o["market"]["prices"]))
    return pd.DataFrame(rows), env


hist, env = price_history()
fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
for it in ("MILK", "WOOL", "STRAWBERRY"):
    ax[0].plot(hist.day, hist[it] / MP[it]["base"], lw=2, label=it)
for it in ("MELON", "WHEAT", "CARROT"):
    ax[1].plot(hist.day, hist[it] / MP[it]["base"], lw=2, label=it)
for a, t in zip(ax, ["Scarcity side: price RISES all season",
                     "Glut side: you crush your own price"]):
    a.axhline(1.0, color="k", ls="--", lw=1, alpha=.6)
    a.set_xlabel("day"); a.set_ylabel("price / base price"); a.set_title(t)
    a.grid(alpha=.3); a.legend()
plt.tight_layout(); plt.show()
hist[["day", "money", "MILK", "WOOL", "STRAWBERRY", "MELON", "WHEAT"]].iloc[::4]

px = {"MILK": 260, "WOOL": 240, "STRAWBERRY": 250, "MELON": 200,
      "EGG": 60, "WHEAT": 30, "CARROT": 40, "FERTILIZER": 80}

jobs = [
    ("CARE a cow",             px["MILK"],                   1),
    ("CARE a sheep",           px["WOOL"],                   1),
    ("HARVEST a cow (3 milk)", 3 * px["MILK"],               1),
    ("WATER a melon (window)", px["MELON"],                  1),
    ("PLANT a melon",          6 * px["MELON"] - 80,        10),
    ("COLLECT_FERTILIZER",     px["FERTILIZER"],             1),
    ("PLANT a strawberry",     4 * px["STRAWBERRY"] - 100,  13),
    ("CARE a goose",           px["EGG"],                    1),
    ("PLANT a carrot",         3 * px["CARROT"] - 20,        5),
    ("WATER wheat (window)",   px["WHEAT"],                  1),
    ("PLANT wheat",            4 * px["WHEAT"] - 10,         6),
]
pd.DataFrame([dict(job=j, value=round(v), actions=a, per_action=round(v / a))
              for j, v, a in jobs]).sort_values("per_action", ascending=False)

def duel(a, b, games=4, steps=720, seed0=1000, label=("A", "B")):
    """Alternate seats: players 0 and 1 are NOT symmetric in market resolution."""
    wins, mine, theirs = 0, [], []
    buf = io.StringIO()
    for g in range(games):
        swap = g % 2 == 1
        pair = [b, a] if swap else [a, b]
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed0 + g})
            env.run(pair)
        rw = [s["reward"] or 0 for s in env.steps[-1]]
        m, t = (rw[1], rw[0]) if swap else (rw[0], rw[1])
        mine.append(m); theirs.append(t); wins += m > t
        print(f"  seat {int(swap)}: {label[0]} ${m:>10,.0f}   {label[1]} ${t:>10,.0f}   "
              f"{'WIN' if m > t else 'LOSS'}")
    print(f"  => {wins}/{games}, mean ${statistics.mean(mine):,.0f} "
          f"vs ${statistics.mean(theirs):,.0f}")
    return statistics.mean(mine)

duel("main.py", "starter", games=2, label=("agent", "starter"))

def census(agent_path, opponent="pass", steps=720, seed=7):
    """Ops per day. Every real bug I had was invisible in the score and obvious here."""
    spec = importlib.util.spec_from_file_location("subm", agent_path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    AGENT = [v for v in vars(mod).values() if callable(v)][-1]
    log = collections.defaultdict(collections.Counter)

    def wrapped(obs):
        a = AGENT(obs)
        for op in [a.get("farmer", ["PASS"])] + list(a.get("hands", [])):
            log[obs["day"]]["op_" + (op[0] if op else "NONE")] += 1
        return a

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
        env.run([wrapped, opponent])
    money = {o["day"]: o["farms"][0]["money"]
             for o in (s[0]["observation"] for s in env.steps)
             if "farms" in o and o["step"] % 24 == 0}
    return pd.DataFrame([
        dict(day=d, money=round(money.get(d, 0)),
             MOVE=sum(log[d]["op_" + x] for x in ("NORTH", "SOUTH", "EAST", "WEST")),
             WATER=log[d]["op_WATER"], HARVEST=log[d]["op_HARVEST"],
             PLANT=log[d]["op_PLANT"], FEED=log[d]["op_FEED"], CARE=log[d]["op_CARE"],
             FERT=log[d]["op_COLLECT_FERTILIZER"], DROP=log[d]["op_DROP"],
             PICKUP=log[d]["op_PICKUP"], PASS=log[d]["op_PASS"])
        for d in sorted(log)])

census("main.py").tail(12)

def preflight(path="main.py"):
    ok = True
    spec = importlib.util.spec_from_file_location("subm", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

    last = [v for v in vars(mod).values() if callable(v)][-1]
    if getattr(last, "__name__", None) != "agent":
        print(f"[FAIL] last callable is {last.__name__!r}, not 'agent'")
        print("       the framework calls the LAST callable in the file -- move helpers ABOVE it")
        ok = False
    else:
        print("[ok] last callable is `agent`")

    buf, t0 = io.StringIO(), time.time()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
        env.run([path, path])            # exactly the validation episode Kaggle runs
    st, dur = [s["status"] for s in env.steps[-1]], time.time() - t0
    good = all(s == "DONE" for s in st)
    print(f"[{'ok' if good else 'FAIL'}] self-play {st}  ({dur:.0f}s, ~{dur/720*1000:.0f} ms/turn)")
    print("\nPREFLIGHT", "PASSED" if ok and good else "FAILED")
    return ok and good

preflight("main.py")