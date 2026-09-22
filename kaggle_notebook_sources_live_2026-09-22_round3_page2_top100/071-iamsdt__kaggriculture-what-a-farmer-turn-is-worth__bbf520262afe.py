import subprocess
import sys

# Kaggle's base image ships kaggle-environments, but often a build that predates
# Kaggriculture, so probe for the env module rather than the package.
try:
    from kaggle_environments.envs.kaggriculture import kaggriculture  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "kaggle-environments>=1.32.2"])

import kaggle_environments
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS, CROPS

print("kaggle-environments", kaggle_environments.__version__)

def watering_window(crop):
    # Bonus watering window for a one-time crop, straight from the WATER handler.
    cd = CROPS[crop]
    return (cd["max_yield_day"] + 1) // 2, cd["max_yield_day"]

def peak_yield(crop):
    # Units harvestable if you water every in-window day, no fertilizer.
    cd = CROPS[crop]
    lo, hi = watering_window(crop)
    return min(cd["max_yield"], 1 + (hi - lo + 1))

print(f"{'crop':11s} {'kind':9s} {'seed':>5s} {'window':>8s} {'reachable':>10s} {'advertised':>11s}")
for c, cd in CROPS.items():
    if cd["ongoing"]:
        # max_yield counts PRODUCTIONS, not units per production.
        busy = cd["first_yield_day"] + cd["interval"] * (cd["max_yield"] - 1)
        print(f"{c:11s} {'ongoing':9s} {cd['seed']:5d} {'-':>8s} "
              f"{cd['max_yield']:10d} {cd['max_yield']:11d}   ({cd['max_yield']} units total, tile busy ~{busy}d)")
    else:
        lo, hi = watering_window(c)
        print(f"{c:11s} {'one-time':9s} {cd['seed']:5d} {f'{lo}-{hi}':>8s} "
              f"{peak_yield(c):10d} {cd['max_yield']:11d}")

# The instrumented single-line agent (harness/monoculture.py).
from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS, CROPS

NW_SHED = (4, 4)  # only shed-access tile inside the starting NW quadrant

MOVE_OF = {(0, -1): "NORTH", (0, 1): "SOUTH", (1, 0): "EAST", (-1, 0): "WEST"}

# Op categories for the labor ledger.
MOVEMENT = {"NORTH", "SOUTH", "EAST", "WEST"}
SHED_OPS = {"PICKUP", "DROP", "PLACE"}
PRODUCTIVE = {
    "PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG",
    "BUILD_COOP", "BUILD_PASTURE", "FEED", "CARE", "COLLECT_FERTILIZER",
}


def g(obs, key, default=None):
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


def nw_tiles_by_distance():
    """NW-quadrant tiles ordered nearest-first from the shed access tile."""
    tiles = [(x, y) for y in range(5) for x in range(5)]
    tiles.sort(key=lambda t: (abs(t[0] - NW_SHED[0]) + abs(t[1] - NW_SHED[1]), t[1], t[0]))
    return tiles


def yield_at_age(crop, age):
    """Harvestable units for a one-time crop watered every in-window day."""
    cd = CROPS[crop]
    if cd["ongoing"]:
        return None
    ws = (cd["max_yield_day"] + 1) // 2
    if age < ws:
        return 1
    watered = min(age, cd["max_yield_day"]) - ws + 1
    return min(cd["max_yield"], 1 + watered)


def best_harvest_age(crop):
    """Earliest age that is both harvestable and at peak yield."""
    cd = CROPS[crop]
    ages = range(cd["first_yield_day"], cd["max_yield_day"] + 1)
    peak = max(yield_at_age(crop, a) for a in ages)
    return next(a for a in ages if yield_at_age(crop, a) == peak)


def step_toward(pos, target):
    px, py = pos
    tx, ty = target
    if px != tx:
        return MOVE_OF[(1, 0) if tx > px else (-1, 0)]
    if py != ty:
        return MOVE_OF[(0, 1) if ty > py else (0, -1)]
    return None


class Stats:
    def __init__(self):
        self.unit_turns = 0
        self.movement = 0
        self.productive = 0
        self.shed = 0
        self.idle = 0
        self.harvested = {}
        self.sold_units = 0
        self.sold_coins = 0.0
        self.hire_spend = 0.0
        self.buy_spend = 0.0
        self.hands_hired = 0
        self.lost_to_weeds = 0
        self.animals_lost = 0

    def record(self, op):
        self.unit_turns += 1
        if op in MOVEMENT:
            self.movement += 1
        elif op in PRODUCTIVE:
            self.productive += 1
        elif op in SHED_OPS:
            self.shed += 1
        else:
            self.idle += 1

    def as_row(self):
        return {
            "unit_turns": self.unit_turns,
            "movement_turns": self.movement,
            "productive_turns": self.productive,
            "shed_turns": self.shed,
            "idle_turns": self.idle,
            "units_harvested": sum(self.harvested.values()),
            "units_sold": self.sold_units,
            "sale_revenue": round(self.sold_coins, 1),
            "hire_spend": self.hire_spend,
            "purchase_spend": self.buy_spend,
            "hands_hired": self.hands_hired,
            "animals_lost": self.animals_lost,
        }


def make_agent(line, k=9, hands=0, harvest_age=None, collect_fertilizer=False,
               turns_per_day=24, season_days=30):
    """Build an instrumented agent running exactly one production line.

    line: a crop name, an animal name, or "IDLE" (control: hires and does nothing).
    k: number of tiles devoted to the line.
    hands: hands hired per day.
    """
    is_crop = line in CROPS
    is_animal = line in ANIMALS
    if is_crop and harvest_age is None:
        harvest_age = best_harvest_age(line)

    plots = nw_tiles_by_distance()[:k]
    stats = Stats()
    state = {"prev_money": None, "prev_shed": None}

    product = ANIMALS[line]["product"] if is_animal else (line if is_crop else None)
    structure = ANIMALS[line]["structure"] if is_animal else None
    build_op = f"BUILD_{structure}" if is_animal else None

    def agent(obs):
        me = g(obs, "player", 0)
        farms = g(obs, "farms")
        farm = farms[me]
        priv = g(obs, "private")
        shed = dict(g(priv, "shed", {}) or {})
        seeds = dict(g(priv, "seeds", {}) or {})
        invs = g(priv, "inventories", [{}]) or [{}]
        tiles = farm["tiles"]
        money = farm["money"]
        day = g(obs, "day", 0)
        hour = g(obs, "hour", 0)
        step = day * turns_per_day + hour
        prices = g(obs, "market", {})["prices"]

        positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]
        n_units = len(positions)
        market = []

        # ---- hiring: front-load at the start of each day -------------------
        if hands and hour < 2:
            want = hands - farm["hires_today"]
            for _ in range(min(want, 10)):
                market.append(["HIRE"])

        # ---- restock ------------------------------------------------------
        if is_crop:
            # Keep enough seed to fill every free plot.
            free = sum(1 for (x, y) in plots if tiles[y][x] is None)
            need = max(0, free - seeds.get(line, 0))
            if need and money > CROPS[line]["seed"] * need:
                market.append(["BUY_SEED", line, need])
        if is_animal:
            placed = sum(
                1 for (x, y) in plots
                if isinstance(tiles[y][x], dict) and "animal" in tiles[y][x]
            )
            in_hand = shed.get(line, 0) + sum(inv.get(line, 0) for inv in invs)
            structures_ready = sum(
                1 for (x, y) in plots
                if isinstance(tiles[y][x], dict)
                and tiles[y][x].get("kind") == structure
                and "animal" not in tiles[y][x]
            )
            want = min(k - placed - in_hand, structures_ready)
            # Keep a cash buffer so feed is always affordable.
            if want > 0 and money > ANIMALS[line]["cost"] + 600:
                market.append(["BUY_ANIMAL", line, 1])
            # Feed: one wheat per animal per day, bought into the shed.
            need_wheat = placed + 1 - shed.get("WHEAT", 0)
            if placed and need_wheat > 0 and money > 400:
                market.append(["BUY_PRODUCT", "WHEAT", max(1, need_wheat)])

        # ---- selling: liquidate produce as it lands ------------------------
        for item, n in shed.items():
            if n <= 0 or item == line and is_animal:
                continue
            if is_animal and item == "WHEAT":
                continue  # reserved for feed
            if item in ("FERTILIZER",) and not collect_fertilizer:
                continue
            if item == product or (collect_fertilizer and item == "FERTILIZER"):
                market.append(["SELL", item, n])

        market = market[:10]

        # ---- task list ----------------------------------------------------
        tasks = []  # (priority, tile, op)
        for (x, y) in plots:
            t = tiles[y][x]
            if t is None:
                if is_crop and seeds.get(line, 0) > 0:
                    tasks.append((3, (x, y), ["PLANT", line]))
                elif is_animal:
                    tasks.append((3, (x, y), [build_op]))
                continue
            if t == "LOCKED":
                continue
            kind = t.get("kind")
            if kind == "WEED":
                tasks.append((2, (x, y), ["DIG"]))
            elif kind == "PLANT":
                age = day - t["planted_day"]
                cd = CROPS[t["crop"]]
                ready = t.get("yield_units", 0) > 0 and age >= cd["first_yield_day"]
                if ready and (cd["ongoing"] or age >= harvest_age):
                    tasks.append((0, (x, y), ["HARVEST"]))
                if not t["watered_today"]:
                    tasks.append((1, (x, y), ["WATER"]))
            elif kind == structure:
                if "animal" not in t:
                    tasks.append((3, (x, y), ["PLACE", line]))
                else:
                    if t.get("yield_units", 0) > 0:
                        tasks.append((0, (x, y), ["HARVEST"]))
                    if not t["fed_today"]:
                        tasks.append((1, (x, y), ["FEED"]))
                    if not t["cared_today"]:
                        tasks.append((4, (x, y), ["CARE"]))
                    if collect_fertilizer and t.get("fertilizer_available"):
                        tasks.append((5, (x, y), ["COLLECT_FERTILIZER"]))
        tasks.sort(key=lambda t: t[0])

        # ---- assign units --------------------------------------------------
        ops = [["PASS"] for _ in range(n_units)]
        taken = [False] * n_units
        end_of_day = hour >= turns_per_day - 2

        for u in range(n_units):
            inv = invs[u] if u < len(invs) else {}
            pos = positions[u]
            # Deposit produce before the day ends (end-of-day auto-drop can overflow).
            if end_of_day and sum(inv.values()) > 0:
                if tuple(pos) == NW_SHED:
                    ops[u] = ["DROP"]
                else:
                    mv = step_toward(pos, NW_SHED)
                    ops[u] = [mv] if mv else ["PASS"]
                taken[u] = True

        # Animal lines: a unit must physically carry wheat to FEED, and carry the
        # animal itself to PLACE. Both are shed PICKUPs, and both cost turns.
        if is_animal:
            for u in range(n_units):
                if taken[u]:
                    continue
                inv = invs[u] if u < len(invs) else {}
                needs_feed = any(t[2][0] == "FEED" for t in tasks)
                needs_place = any(t[2][0] == "PLACE" for t in tasks)
                if needs_place and inv.get(line, 0) == 0 and shed.get(line, 0) > 0:
                    if tuple(positions[u]) == NW_SHED:
                        ops[u] = ["PICKUP", line, 1]
                    else:
                        mv = step_toward(positions[u], NW_SHED)
                        ops[u] = [mv] if mv else ["PASS"]
                    taken[u] = True
                elif needs_feed and inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0:
                    if tuple(positions[u]) == NW_SHED:
                        ops[u] = ["PICKUP", "WHEAT", min(4, shed.get("WHEAT", 0))]
                    else:
                        mv = step_toward(positions[u], NW_SHED)
                        ops[u] = [mv] if mv else ["PASS"]
                    taken[u] = True

        used_tiles = set()
        for prio, tile, op in tasks:
            if tile in used_tiles:
                continue
            # Cheapest free unit for this tile.
            best, best_d = None, None
            for u in range(n_units):
                if taken[u]:
                    continue
                inv = invs[u] if u < len(invs) else {}
                if op[0] == "FEED" and inv.get("WHEAT", 0) == 0:
                    continue
                if op[0] == "PLACE" and inv.get(line, 0) == 0:
                    continue
                d = abs(positions[u][0] - tile[0]) + abs(positions[u][1] - tile[1])
                if best_d is None or d < best_d:
                    best, best_d = u, d
            if best is None:
                continue
            if best_d == 0:
                ops[best] = op
            else:
                mv = step_toward(positions[best], tile)
                ops[best] = [mv] if mv else ["PASS"]
            taken[best] = True
            used_tiles.add(tile)

        for u in range(n_units):
            stats.record(ops[u][0])

        # ---- bookkeeping ---------------------------------------------------
        # Sales: only the product line ever leaves the shed by selling. Wheat held
        # for feed also leaves the shed via PICKUP, so it must not be counted.
        prev_shed = state["prev_shed"]
        if prev_shed is not None and product:
            drop = prev_shed.get(product, 0) - shed.get(product, 0)
            if drop > 0:
                stats.sold_units += drop
                stats.sold_coins += drop * state.get("prev_price", prices[product])
        state["prev_shed"] = shed
        state["prev_price"] = prices.get(product) if product else None

        # Harvest: units appearing in a unit inventory.
        prev_inv = state.get("prev_inv")
        if prev_inv is not None and product:
            now = sum(inv.get(product, 0) for inv in invs)
            gained = now - prev_inv
            if gained > 0:
                stats.harvested[product] = stats.harvested.get(product, 0) + gained
        state["prev_inv"] = sum(inv.get(product, 0) for inv in invs) if product else 0

        stats.hands_hired = max(stats.hands_hired, len(farm["hands"]))

        return {"farmer": ops[0], "hands": ops[1:], "market": market}

    agent.stats = stats
    agent.plots = plots
    agent.line = line
    return agent

import pandas as pd

LEDGER = pd.DataFrame([
    # line,        tiles, hands,   net,   sd,  units, coins/turn, $/unit, move%, idle%
    ("SHEEP",      16, 6, 46887, 4370, 348.0,  9.66, 134.69, 0.38, 0.40),
    ("MELON",      25, 2, 41702,  436, 245.7, 19.89, 169.76, 0.63, 0.02),
    ("COW",         4, 2, 29072, 4310, 144.0, 13.86, 201.89, 0.27, 0.52),
    ("STRAWBERRY", 25, 4, 19045, 2282, 132.0,  5.48, 144.28, 0.46, 0.30),
    ("WHEAT",      25, 8,  9390,  565, 525.0,  1.51,  17.89, 0.42, 0.40),
    ("TOMATO",     25, 6,  7712,  829, 184.0,  1.59,  41.91, 0.46, 0.33),
    ("CARROT",     25, 6,  6673, 1711, 428.0,  1.38,  15.59, 0.60, 0.16),
    ("GOOSE",       4, 1,  3570, 1133, 212.0,  2.54,  16.84, 0.32, 0.37),
], columns=["line", "tiles", "hands", "net", "net_sd", "units",
            "coins_per_turn", "net_per_unit", "movement_frac", "idle_frac"])

print(LEDGER.to_string(index=False))

import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
d = LEDGER.sort_values("net")
axes[0].barh(d.line, d.net, color="#4c72b0")
axes[0].set_title("Total net coins\n(at each line's best setup)")
axes[0].set_xlabel("coins")

d2 = LEDGER.sort_values("coins_per_turn")
axes[1].barh(d2.line, d2.coins_per_turn, color="#dd8452")
axes[1].set_title("Coins per unit-turn\nthe labor-adjusted ranking")
axes[1].set_xlabel("coins / unit-turn")

d3 = LEDGER.sort_values("movement_frac")
axes[2].barh(d3.line, d3.movement_frac * 100, color="#55a868")
axes[2].set_title("Share of unit-turns spent walking")
axes[2].set_xlabel("% of all unit-turns")
for ax in axes:
    ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.show()

def fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def hire_day_cost(h):
    return sum(fib(i) for i in range(h))

print(f"{'hands':>5s} {'$/day':>7s} {'$/season':>9s}")
for h in [0, 1, 2, 4, 6, 8, 10, 12, 14, 16]:
    print(f"{h:5d} {hire_day_cost(h):7d} {30 * hire_day_cost(h):9d}")

MARGINAL = pd.DataFrame([
    ("MELON", 0, 15833,  70), ("MELON", 1, 27450, 130), ("MELON", 2, 41702, 246),
    ("MELON", 4, 37865, 250), ("MELON", 6, 37315, 250), ("MELON", 8, 36455, 250),
    ("MELON", 12, 21653, 160),
    ("SHEEP", 0, -2609,  42), ("SHEEP", 1, -2016,  84), ("SHEEP", 2,  5948, 132),
    ("SHEEP", 4, 34601, 266), ("SHEEP", 6, 46887, 348), ("SHEEP", 8, 45219, 337),
    ("SHEEP", 12, -3000,   2),
    ("STRAWBERRY", 0, 2738, 30), ("STRAWBERRY", 1, 5532, 57), ("STRAWBERRY", 2, 11466, 92),
    ("STRAWBERRY", 4, 19045, 132), ("STRAWBERRY", 6, 18313, 138), ("STRAWBERRY", 8, 17514, 145),
    ("STRAWBERRY", 12, 12076, 114),
    ("COW", 0, 16984, 95), ("COW", 1, 28650, 144), ("COW", 2, 29072, 144),
    ("COW", 4, 28613, 144), ("COW", 6, 27905, 144), ("COW", 8, 26297, 141),
    ("COW", 12, -3000, 0),
], columns=["line", "hands", "net", "units"])

fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
for line, grp in MARGINAL.groupby("line"):
    axes[0].plot(grp.hands, grp.net, marker="o", label=line)
axes[0].axhline(0, color="k", lw=0.8)
axes[0].set_xlabel("hands hired per day"); axes[0].set_ylabel("net coins")
axes[0].set_title("Profit against hand count"); axes[0].legend(); axes[0].grid(alpha=0.3)

m = MARGINAL[MARGINAL.line == "MELON"]
axes[1].plot(m.hands, m.units, marker="o", color="#c44e52", label="melons produced")
axes[1].set_xlabel("hands hired per day"); axes[1].set_ylabel("units produced")
axes[1].set_title("Melon output saturates at 2 hands"); axes[1].grid(alpha=0.3); axes[1].legend()
plt.tight_layout(); plt.show()

HARVEST_AGE = pd.DataFrame([
    ("WHEAT",  2, 3355, 160.2), ("WHEAT",  3, 5322, 212.5), ("WHEAT",  4, 6620, 250.5),
    ("CARROT", 2, 1971, 160.2), ("CARROT", 3, 4682, 212.5),
    ("MELON", 10, 27150, 125.0), ("MELON", 11, 32642, 150.0), ("MELON", 12, 33912, 150.0),
], columns=["crop", "harvest_age", "net", "units"])
print(HARVEST_AGE.to_string(index=False))

import time

def run(line, k, hands, seed=101, harvest_age=None):
    ag = make_agent(line, k=k, hands=hands, harvest_age=harvest_age)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([ag, "pass"])
    money = env.steps[-1][0].observation.farms[0]["money"]
    s = ag.stats.as_row()
    return {
        "line": line, "k": k, "hands": hands, "net": money - 3000,
        "units": s["units_harvested"],
        "move%": round(100 * s["movement_turns"] / max(1, s["unit_turns"]), 1),
        "idle%": round(100 * s["idle_turns"] / max(1, s["unit_turns"]), 1),
        "coins/turn": round((money - 3000) / max(1, s["unit_turns"]), 2),
    }

t0 = time.time()
rows = [run("MELON", 25, h) for h in [0, 1, 2, 4, 8]]
demo = pd.DataFrame(rows)
print(demo.to_string(index=False))
print(f"\n{time.time() - t0:.0f}s")
print("\nOutput saturates while net coins peak earlier. Extra hands past the tile")
print("ceiling convert into a worse realised price, not more melons.")

%%writefile submission.py
"""Sheep build for Kaggriculture. 16 pastures in the NW quadrant, 6 hands a day.

Config comes from EXP-01: sheep at k=16, h=6 was the highest measured net
($46,887 against a passing opponent), and 6 hands cost $600 a season against the
$11,280 that 12 hands cost. Everything past 8 hands is negative marginal value.
"""

from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS

LINE = "SHEEP"
TILES = 16
HANDS = 6

NW_SHED = (4, 4)  # only shed-access tile inside the starting NW quadrant
TURNS_PER_DAY = 24

MOVE_OF = {(0, -1): "NORTH", (0, 1): "SOUTH", (1, 0): "EAST", (-1, 0): "WEST"}

PRODUCT = ANIMALS[LINE]["product"]
STRUCTURE = ANIMALS[LINE]["structure"]
BUILD_OP = "BUILD_" + STRUCTURE


def g(obs, key, default=None):
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


def nw_tiles_by_distance():
    """NW-quadrant tiles ordered nearest-first from the shed access tile."""
    tiles = [(x, y) for y in range(5) for x in range(5)]
    tiles.sort(key=lambda t: (abs(t[0] - NW_SHED[0]) + abs(t[1] - NW_SHED[1]), t[1], t[0]))
    return tiles


def step_toward(pos, target):
    px, py = pos
    tx, ty = target
    if px != tx:
        return MOVE_OF[(1, 0) if tx > px else (-1, 0)]
    if py != ty:
        return MOVE_OF[(0, 1) if ty > py else (0, -1)]
    return None


PLOTS = nw_tiles_by_distance()[:TILES]


def agent(obs):
    me = g(obs, "player", 0)
    farm = g(obs, "farms")[me]
    priv = g(obs, "private")
    shed = dict(g(priv, "shed", {}) or {})
    invs = g(priv, "inventories", [{}]) or [{}]
    tiles = farm["tiles"]
    money = farm["money"]
    hour = g(obs, "hour", 0)

    positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]
    n_units = len(positions)
    market = []

    # Hiring, front-loaded at the start of the day.
    if hour < 2:
        for _ in range(min(HANDS - farm["hires_today"], 10)):
            market.append(["HIRE"])

    # Restock: one animal at a time onto a ready pasture, keeping a feed buffer.
    placed = sum(
        1 for (x, y) in PLOTS
        if isinstance(tiles[y][x], dict) and "animal" in tiles[y][x]
    )
    in_hand = shed.get(LINE, 0) + sum(inv.get(LINE, 0) for inv in invs)
    structures_ready = sum(
        1 for (x, y) in PLOTS
        if isinstance(tiles[y][x], dict)
        and tiles[y][x].get("kind") == STRUCTURE
        and "animal" not in tiles[y][x]
    )
    if min(TILES - placed - in_hand, structures_ready) > 0 and money > ANIMALS[LINE]["cost"] + 600:
        market.append(["BUY_ANIMAL", LINE, 1])

    # Feed: one wheat per animal per day, bought into the shed.
    need_wheat = placed + 1 - shed.get("WHEAT", 0)
    if placed and need_wheat > 0 and money > 400:
        market.append(["BUY_PRODUCT", "WHEAT", max(1, need_wheat)])

    # Sell the product as it lands. Wheat in the shed is feed, never stock.
    if shed.get(PRODUCT, 0) > 0:
        market.append(["SELL", PRODUCT, shed[PRODUCT]])

    market = market[:10]

    # Task list, lowest priority number first.
    tasks = []
    for (x, y) in PLOTS:
        t = tiles[y][x]
        if t is None:
            tasks.append((3, (x, y), [BUILD_OP]))
            continue
        if t == "LOCKED":
            continue
        kind = t.get("kind")
        if kind == "WEED":
            tasks.append((2, (x, y), ["DIG"]))
        elif kind == STRUCTURE:
            if "animal" not in t:
                tasks.append((3, (x, y), ["PLACE", LINE]))
            else:
                if t.get("yield_units", 0) > 0:
                    tasks.append((0, (x, y), ["HARVEST"]))
                if not t["fed_today"]:
                    tasks.append((1, (x, y), ["FEED"]))
                if not t["cared_today"]:
                    tasks.append((4, (x, y), ["CARE"]))
    tasks.sort(key=lambda t: t[0])

    ops = [["PASS"] for _ in range(n_units)]
    taken = [False] * n_units
    end_of_day = hour >= TURNS_PER_DAY - 2

    # Deposit produce before the day ends, since the auto-drop can overflow.
    for u in range(n_units):
        inv = invs[u] if u < len(invs) else {}
        if end_of_day and sum(inv.values()) > 0:
            if positions[u] == NW_SHED:
                ops[u] = ["DROP"]
            else:
                mv = step_toward(positions[u], NW_SHED)
                ops[u] = [mv] if mv else ["PASS"]
            taken[u] = True

    # FEED and PLACE both draw from the unit's own inventory, so a unit has to
    # walk to the shed and pick up before it can do either.
    needs_feed = any(t[2][0] == "FEED" for t in tasks)
    needs_place = any(t[2][0] == "PLACE" for t in tasks)
    for u in range(n_units):
        if taken[u]:
            continue
        inv = invs[u] if u < len(invs) else {}
        if needs_place and inv.get(LINE, 0) == 0 and shed.get(LINE, 0) > 0:
            pick = ["PICKUP", LINE, 1]
        elif needs_feed and inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0:
            pick = ["PICKUP", "WHEAT", min(4, shed.get("WHEAT", 0))]
        else:
            continue
        if positions[u] == NW_SHED:
            ops[u] = pick
        else:
            mv = step_toward(positions[u], NW_SHED)
            ops[u] = [mv] if mv else ["PASS"]
        taken[u] = True

    # Assign each task to the nearest free unit that can actually perform it.
    used_tiles = set()
    for prio, tile, op in tasks:
        if tile in used_tiles:
            continue
        best, best_d = None, None
        for u in range(n_units):
            if taken[u]:
                continue
            inv = invs[u] if u < len(invs) else {}
            if op[0] == "FEED" and inv.get("WHEAT", 0) == 0:
                continue
            if op[0] == "PLACE" and inv.get(LINE, 0) == 0:
                continue
            d = abs(positions[u][0] - tile[0]) + abs(positions[u][1] - tile[1])
            if best_d is None or d < best_d:
                best, best_d = u, d
        if best is None:
            continue
        if best_d == 0:
            ops[best] = op
        else:
            mv = step_toward(positions[best], tile)
            ops[best] = [mv] if mv else ["PASS"]
        taken[best] = True
        used_tiles.add(tile)

    return {"farmer": ops[0], "hands": ops[1:], "market": market}

# Sanity check the written file before submitting it.
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 101})
env.run(["submission.py", "starter"])
farms = env.steps[-1][0].observation.farms
print(f"submission.py {farms[0]['money']:>8.0f}      starter {farms[1]['money']:>8.0f}")

# Then submit, with your API token attached as a Kaggle secret:
# !kaggle competitions submit -c kaggriculture -f submission.py -m "sheep 16x6"



