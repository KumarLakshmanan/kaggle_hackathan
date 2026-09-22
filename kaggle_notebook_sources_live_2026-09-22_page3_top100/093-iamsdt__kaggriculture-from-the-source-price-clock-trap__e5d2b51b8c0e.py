import sys, subprocess
try:
    import kaggle_environments  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "kaggle-environments>=1.32.2"], check=True)

import json, math, statistics as st
from collections import OrderedDict

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture.kaggriculture import (
    CROPS, ANIMALS, PRODUCTS, SHOPS, MARKET_PARAMS, MARKET_I0, PRICE_FLOOR,
    TOWN_CENTER_PRODUCTS, market_price,
)
print("crops:", list(CROPS), "\nanimals:", list(ANIMALS), "\nproducts:", PRODUCTS)

%%writefile rulebook.py
"""EXP-08: mechanics ground truth, derived from the Kaggriculture env source.

Everything here calls the environment's own functions and constants. Nothing is
re-implemented from the docs, because the docs and the source disagree in
several places and the source is the authority.

The module is import-safe and side-effect free so the notebook and the agent can
both use it.

    from rulebook import floor_point, price_curve, sell_revenue, field_capacity
"""
import math
from collections import OrderedDict

from kaggle_environments.envs.kaggriculture.kaggriculture import (
    ANIMALS,
    CROPS,
    LAND_ORDER,
    LAND_PRICES,
    MARKET_I0,
    MARKET_PARAMS,
    PRICE_FLOOR,
    PRODUCTS,
    SHOPS,
    TOWN_CENTER_DEMAND_SCHEDULE,
    TOWN_CENTER_PRODUCTS,
    _fib,
    _quadrant_of,
    _shed_access_tiles,
    _spawn_hand,
    market_price,
)

TURNS_PER_DAY = 24
SEASON_DAYS = 30
EPISODE_STEPS = TURNS_PER_DAY * SEASON_DAYS
BOARD_SIZE = 10
QUADRANT_TILES = (BOARD_SIZE // 2) ** 2

# The window the `T` calibration comment refers to: "production capacity of one
# 5x5 field over a 24-day window at optimal watering, no fertilizer".
T_WINDOW_DAYS = 24
ANIMAL_T_DISCOUNT = 0.70  # "animal T pre-discounted 30% for wheat-feed overhead"


# --------------------------------------------------------------------------
# 1. The price machine
# --------------------------------------------------------------------------

def price_curve(item, lo=None, hi=None, n=400):
    """(inventories, prices) for `item` across an inventory range."""
    lo = MARKET_I0 - 1200 if lo is None else lo
    hi = MARKET_I0 + 1200 if hi is None else hi
    step = max(1, (hi - lo) // n)
    inv = list(range(lo, hi + 1, step))
    return inv, [market_price(item, i) for i in inv]


def floor_point(item, start_inventory=MARKET_I0, cap=5_000_000):
    """Units sold in one turn, starting from `start_inventory`, before the
    quoted price pins to PRICE_FLOOR.

    Mirrors `_commit_unit`: a sale only raises market inventory when the price
    it cleared at was above the floor, so a floored market stops absorbing.
    Returns None when the product cannot be floored within `cap` units.
    """
    inv = start_inventory
    for n in range(cap):
        if market_price(item, inv) <= PRICE_FLOOR:
            return n
        inv += 1
    return None


def sell_revenue(item, units, start_inventory=MARKET_I0):
    """Realized revenue for selling `units` in a single turn, uncontested.

    Replicates the per-unit loop in `_process_market` / `_commit_unit` for one
    player: quote at current inventory, commit, then raise inventory only if the
    unit cleared above the floor.
    """
    inv = start_inventory
    total = 0
    prices = []
    for _ in range(units):
        p = market_price(item, inv)
        total += p
        prices.append(p)
        if p > PRICE_FLOOR:
            inv += 1
    return total, prices, inv


def sell_revenue_contested(item, units_a, units_b, start_inventory=MARKET_I0):
    """Both players selling the same item in the same turn.

    `_process_market` runs a per-unit lockstep: both players are quoted against
    the *same* pre-commit inventory, then both commit. So a contested sale is
    not "first mover gets the good price" — both get it, and the inventory then
    moves by two.
    """
    inv = start_inventory
    rev = [0, 0]
    left = [units_a, units_b]
    while left[0] > 0 or left[1] > 0:
        quoted = [market_price(item, inv) if left[p] > 0 else None for p in (0, 1)]
        for p in (0, 1):
            if quoted[p] is None:
                continue
            rev[p] += quoted[p]
            left[p] -= 1
            if quoted[p] > PRICE_FLOOR:
                inv += 1
    return rev[0], rev[1], inv


def price_table():
    """One row per tradable: curve shapes, floor point, and shop demand."""
    rows = []
    for item in PRODUCTS:
        p = MARKET_PARAMS[item]
        fp = floor_point(item)
        shops = [s for s, prods in SHOPS.items() if item in prods]
        rows.append(OrderedDict(
            item=item,
            base=p["base"],
            T=p["T"],
            below=f'{p["below_func"]}x{p["below_target"]:.2f}',
            above=f'{p["above_func"]}x{p["above_target"]:.2f}',
            floor_units=fp,
            n_shops=len(shops),
            shops=shops,
        ))
    return rows


# --------------------------------------------------------------------------
# 2. The clock: crop and animal lifecycles
# --------------------------------------------------------------------------

def watering_window(crop):
    """(start_day, end_day) inclusive, in days since planting, or None.

    From `_apply_unit_action` WATER: window_start = (max_yield_day + 1) // 2,
    and the bonus only applies to one-time crops.
    """
    cd = CROPS[crop]
    if cd["ongoing"]:
        return None
    return ((cd["max_yield_day"] + 1) // 2, cd["max_yield_day"])


def reachable_yield(crop, fertilized=False):
    """Max yield_units one tile can reach, versus the advertised `max_yield`.

    One-time crops start at yield_units=1 (`_new_plant`) and gain 1 per watering
    inside the window (2 if fertilized), capped at max_yield. Ongoing crops
    accumulate one production per interval, capped at max_yield productions.
    """
    cd = CROPS[crop]
    if cd["ongoing"]:
        return cd["max_yield"]
    start, end = watering_window(crop)
    waterings = end - start + 1
    per = 2 if fertilized else 1
    return min(cd["max_yield"], 1 + waterings * per)


def crop_cycle_days(crop):
    """Days a tile is occupied by one full cycle of `crop`."""
    cd = CROPS[crop]
    if cd["ongoing"]:
        # Last production lands at first_yield_day + interval * (max_yield - 1).
        return cd["first_yield_day"] + cd["interval"] * (cd["max_yield"] - 1)
    return cd["max_yield_day"]


def crop_timeline(crop):
    """Named milestones in days since planting, for the lifecycle chart."""
    cd = CROPS[crop]
    out = OrderedDict(
        crop=crop,
        seed_cost=cd["seed"],
        ongoing=cd["ongoing"],
        first_yield_day=cd["first_yield_day"],
        max_yield_day=cd["max_yield_day"],
        cycle_days=crop_cycle_days(crop),
        advertised_max_yield=cd["max_yield"],
        reachable_yield=reachable_yield(crop),
        reachable_fertilized=reachable_yield(crop, fertilized=True),
    )
    win = watering_window(crop)
    out["window_start"], out["window_end"] = win if win else (None, None)
    if cd["ongoing"]:
        out["production_days"] = [
            cd["first_yield_day"] + cd["interval"] * i for i in range(cd["max_yield"])
        ]
    else:
        out["production_days"] = []
    # `_new_plant`: max_lifespan_step = (day + max_yield_day + 1) * turns_per_day.
    out["decay_starts_day"] = None if cd["ongoing"] else cd["max_yield_day"] + 1
    return out


def animal_timeline(animal):
    a = ANIMALS[animal]
    days = []
    d = a["first_yield_day"]
    while d < SEASON_DAYS:
        days.append(d)
        d += a["interval"]
    return OrderedDict(
        animal=animal,
        cost=a["cost"],
        structure=a["structure"],
        product=a["product"],
        first_yield_day=a["first_yield_day"],
        interval=a["interval"],
        max_held=a["max_held"],
        production_days=days,
    )


def decay_schedule(crop, harvest_missed_at_day):
    """`_decay_plants` runs every step and drops 1 unit every *other step* once
    past max_lifespan_step -- i.e. 12 units per day, not 1 per day.

    Returns [(step_offset, yield_units)] from the moment decay starts.
    """
    units = reachable_yield(crop)
    out, step = [(0, units)], 0
    while units > 0:
        step += 2
        units -= 1
        out.append((step, max(0, units)))
    return out


# --------------------------------------------------------------------------
# 3. Field capacity, and what `T` actually means
# --------------------------------------------------------------------------

def field_capacity(line, window_days=T_WINDOW_DAYS, tiles=QUADRANT_TILES):
    """Units one full 5x5 field of `line` produces in `window_days`.

    This is the quantity the `T` comment in the source claims to encode. For
    crops: whole cycles that fit in the window, times tiles, times reachable
    yield. For animals: scheduled productions inside the window, times tiles,
    discounted 30% for wheat-feed overhead exactly as the comment states.
    """
    if line in CROPS:
        cycle = crop_cycle_days(line)
        cycles = window_days // cycle
        return cycles * tiles * reachable_yield(line)
    a = ANIMALS[line]
    productions = len(range(a["first_yield_day"], window_days, a["interval"]))
    return int(round(productions * tiles * ANIMAL_T_DISCOUNT))


def calibration_table():
    """Computed field capacity against the `T` constant, per production line."""
    rows = []
    lines = [(c, c) for c in CROPS] + [(a, ANIMALS[a]["product"]) for a in ANIMALS]
    for line, product in lines:
        cap = field_capacity(line)
        T = MARKET_PARAMS[product]["T"]
        fp = floor_point(product)
        rows.append(OrderedDict(
            line=line,
            product=product,
            computed_capacity=cap,
            source_T=T,
            ratio=round(cap / T, 3),
            matches=(cap == T),
            floor_units=fp,
            # How many full fields of output it takes to floor this product.
            fields_to_floor=(None if fp is None else round(fp / cap, 2)),
        ))
    return rows


# --------------------------------------------------------------------------
# 4. The town: where demand comes from
# --------------------------------------------------------------------------

def town_center_multiplier(day):
    return next(m for threshold, m in TOWN_CENTER_DEMAND_SCHEDULE if day >= threshold)


def town_demand_schedule(unlock_order, shop_unlock_interval=3,
                         shop_interval=4, center_interval=12,
                         episode_steps=EPISODE_STEPS, turns_per_day=TURNS_PER_DAY):
    """Per-step town consumption per product, for a given shop unlock order.

    Mirrors `_town_consume` (runs every step) and the unlock rule at the end of
    `_end_of_day`: a shop unlocks when `(day + 1) % townShopUnlockInterval == 0`.
    Returns {product: [units_consumed_at_step]}.
    """
    drain = {item: [0] * episode_steps for item in PRODUCTS}
    unlocked, pending = [], list(unlock_order)

    for step in range(episode_steps):
        day = step // turns_per_day
        if step % shop_interval == 0:
            for shop in unlocked:
                products = SHOPS[shop]
                mult = 2 if len(products) == 1 else 1
                for item in products:
                    drain[item][step] += mult
        if step % center_interval == 0:
            mult = town_center_multiplier(day)
            for item in TOWN_CENTER_PRODUCTS:
                drain[item][step] += mult
        # End of day: unlock the next shop for the *following* day.
        if (step + 1) % turns_per_day == 0:
            next_day = day + 1
            if next_day > 0 and next_day % shop_unlock_interval == 0 and pending:
                unlocked.append(pending.pop(0))
    return drain


def drift_from_drain(drain, start_inventory=MARKET_I0):
    """Turn a per-step drain into inventory and price paths.

    Index 0 is the opening state before any town consumption, so the paths are
    one longer than the drain series and price_path[item][0] == base.
    """
    inv_path, price_path = {}, {}
    for item, series in drain.items():
        inv = start_inventory
        invs, prices = [inv], [market_price(item, inv)]
        for units in series:
            inv -= units
            invs.append(inv)
            prices.append(market_price(item, inv))
        inv_path[item], price_path[item] = invs, prices
    return inv_path, price_path


def shop_unlock_days(shop_unlock_interval=3, n_shops=None):
    """Days on which shops 1..N become active."""
    n_shops = len(SHOPS) if n_shops is None else n_shops
    days = [d for d in range(1, SEASON_DAYS + 1) if d % shop_unlock_interval == 0]
    return days[:n_shops]


# --------------------------------------------------------------------------
# 5. The board: geometry and the movement tax
# --------------------------------------------------------------------------

def quadrant_map(board_size=BOARD_SIZE):
    return [[_quadrant_of(x, y, board_size) for x in range(board_size)]
            for y in range(board_size)]


def shed_access(board_size=BOARD_SIZE):
    """The four shed-access tiles with the quadrant each one sits in."""
    return [(t, _quadrant_of(t[0], t[1], board_size)) for t in _shed_access_tiles(board_size)]


def hand_spawns(n_hands, board_size=BOARD_SIZE):
    """Where hires 1..n land, via the env's own `_spawn_hand`.

    The main farmer occupies the only shed-access tile inside NW, so the next
    three hires spawn in quadrants a player does not own at the start of the
    game. Movement off LOCKED tiles is legal precisely so they are not stranded.
    """
    farm = {"farmer": list(_default_spawn(board_size)), "hands": []}
    out = []
    for i in range(n_hands):
        pos = _spawn_hand(farm, board_size)
        farm["hands"].append(pos)
        quad = _quadrant_of(pos[0], pos[1], board_size)
        out.append(OrderedDict(hire=i + 1, pos=tuple(pos), quadrant=quad, starts_locked=quad != "NW"))
    return out


def _default_spawn(board_size=BOARD_SIZE):
    for tile in _shed_access_tiles(board_size):
        if _quadrant_of(tile[0], tile[1], board_size) == "NW":
            return tile
    return (0, 0)


def distance_map(board_size=BOARD_SIZE, origin=None):
    """Manhattan distance from the farmer spawn to every tile."""
    ox, oy = origin if origin else _default_spawn(board_size)
    return [[abs(x - ox) + abs(y - oy) for x in range(board_size)] for y in range(board_size)]


def quadrant_travel_cost(board_size=BOARD_SIZE):
    """Mean and worst round-trip walk from the shed into each quadrant."""
    dist = distance_map(board_size)
    out = []
    for quad in ["NW"] + LAND_ORDER:
        ds = [dist[y][x] for y in range(board_size) for x in range(board_size)
              if _quadrant_of(x, y, board_size) == quad]
        price = 0 if quad == "NW" else LAND_PRICES[LAND_ORDER.index(quad)]
        out.append(OrderedDict(
            quadrant=quad, price=price, tiles=len(ds),
            mean_round_trip=round(2 * sum(ds) / len(ds), 2),
            worst_round_trip=2 * max(ds),
        ))
    return out


def hire_cost_curve(n, mult=1):
    """Cost of the k-th hire of a day, and the cumulative day/season cost."""
    rows, cum = [], 0
    for k in range(n):
        c = mult * _fib(k)
        cum += c
        rows.append(OrderedDict(hire=k + 1, cost=c, cumulative_day=cum,
                                cumulative_season=cum * SEASON_DAYS))
    return rows


# --------------------------------------------------------------------------
# 6. The traps: mechanics that silently no-op
# --------------------------------------------------------------------------

TRAPS = [
    dict(
        name="Atomic PLANT rejection",
        source="interpreter()",
        rule="If the units requesting PLANT for a crop this turn outnumber the seeds you hold, "
             "ALL of those PLANT requests are replaced with PASS -- not partially filled.",
        cost="Ask 6 hands to plant melon holding 5 seeds and you plant zero, losing 6 unit-turns.",
    ),
    dict(
        name="Floored sales do not restock the market",
        source="_commit_unit()",
        rule="A SELL that clears at $1 does not increment market inventory.",
        cost="Once floored, a product stops absorbing supply -- so a glut recovers from town demand "
             "alone, and dumping past the floor point is pure waste.",
    ),
    dict(
        name="BUY_PRODUCT is wheat and fertilizer only",
        source="_process_market()",
        rule="BUY_PRODUCT is filled only for WHEAT and FERTILIZER. Every other item silently aborts "
             "the order.",
        cost="You cannot buy melon to corner it, and a malformed sub-op cancels the rest of that order.",
    ),
    dict(
        name="Buying is quoted one unit ahead",
        source="_process_market()",
        rule="BUY_PRODUCT quotes at market_price(inventory - 1), so a buy/sell round trip against an "
             "unchanged market nets exactly zero.",
        cost="There is no free arbitrage loop.",
    ),
    dict(
        name="Planting day counts as unwatered",
        source="_new_plant()",
        rule="A new plant starts with consecutive_unwatered = 1. Two consecutive unwatered end-of-days "
             "turn it into a weed.",
        cost="A seed planted and not watered the same day is a weed by the next end-of-day. The seed "
             "cost is gone.",
    ),
    dict(
        name="Decay runs every other STEP, not every other day",
        source="_decay_plants()",
        rule="Past max_lifespan_step, yield_units drops by 1 every 2 steps -- 12 units per day.",
        cost="A ripe 6-unit melon left one day past its lifespan is a weed within half a day.",
    ),
    dict(
        name="Hands spawn on land you do not own",
        source="_spawn_hand()",
        rule="Hires cycle through the four shed-access tiles; only one of them is inside NW.",
        cost="Your first three hires of every day appear in locked quadrants and spend turns walking back.",
    ),
    dict(
        name="The shed silently discards overflow",
        source="_drop_inventories_to_shed()",
        rule="End-of-day drops fill the shed to shedCapacity (100) and discard the remainder. "
             "BUY_PRODUCT and BUY_ANIMAL also fail outright when the shed is full.",
        cost="Harvest more than the shed can hold and the surplus evaporates at midnight, uncompensated.",
    ),
]

import rulebook
from rulebook import (
    price_curve, floor_point, sell_revenue, sell_revenue_contested, price_table,
    crop_timeline, animal_timeline, watering_window, reachable_yield, crop_cycle_days,
    field_capacity, calibration_table, town_demand_schedule, drift_from_drain,
    quadrant_map, distance_map, hand_spawns, quadrant_travel_cost, hire_cost_curve,
    shed_access, TRAPS, SEASON_DAYS, TURNS_PER_DAY, EPISODE_STEPS,
)
print("rulebook loaded")

INK       = "#0b0b0b"   # primary text
INK2      = "#52514e"   # secondary text
MUTED     = "#898781"   # axis labels
GRID      = "#e1e0d9"   # hairline gridlines
AXIS      = "#c3c2b7"   # baseline
SURFACE   = "#fcfcfb"   # chart surface

S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"   # categorical: blue, orange, aqua
CRIT       = "#d03b3b"                          # status: critical
GOOD       = "#0ca30c"                          # status: good
# Sequential blue ramp, light -> dark (magnitude only).
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
       "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
SEQ_CMAP = mpl.colors.LinearSegmentedColormap.from_list("kg_blue", SEQ)

mpl.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 10,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.labelcolor": INK2,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.titlelocation": "left", "axes.titlepad": 8,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.axisbelow": True,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "legend.frameon": False, "legend.fontsize": 9, "legend.labelcolor": INK2,
    "lines.linewidth": 2, "lines.solid_capstyle": "round",
    "figure.dpi": 120,
})

def tidy(ax, xgrid=False, ygrid=True):
    '''Hairline grid on one axis only; drop the box.'''
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.xaxis.grid(xgrid); ax.yaxis.grid(ygrid)
    return ax

def money(x, _=None):
    return f"${x:,.0f}"

print("style ready")

for t, quad in shed_access():
    print(f"shed-access tile {t}  ->  quadrant {quad}{'   (LOCKED at game start)' if quad != 'NW' else '   <- your only one'}")

spawns = hand_spawns(8)
for h in spawns:
    flag = "LOCKED — must walk home" if h["starts_locked"] else "on your land"
    print(f"hire {h['hire']}: spawns at {h['pos']} in {h['quadrant']:>2}  {flag}")

locked = sum(h["starts_locked"] for h in spawns)
print(f"\n{locked} of the first 8 hires each day start on land you do not own.")

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4), gridspec_kw={"width_ratios": [1, 1.05]})

# --- left: the board, quadrants and spawn points ---
ax = axes[0]
qmap = quadrant_map()
owned = np.array([[1.0 if q == "NW" else 0.0 for q in row] for row in qmap])
ax.imshow(owned, cmap=mpl.colors.ListedColormap(["#f2f1ec", "#dbe9fb"]),
          vmin=0, vmax=1, origin="upper")
for i in (4.5,):
    ax.axhline(i, color=AXIS, lw=1.2); ax.axvline(i, color=AXIS, lw=1.2)

labels = {"NW": "NW — yours\n25 tiles", "NE": "NE\n$1,000", "SW": "SW\n$2,000", "SE": "SE\n$4,000"}
for q, (cx, cy) in {"NW": (2, 1.2), "NE": (7, 1.2), "SW": (2, 6.2), "SE": (7, 6.2)}.items():
    ax.text(cx, cy, labels[q], ha="center", va="center", color=INK2, fontsize=10)

for h in hand_spawns(4):
    x, y = h["pos"]
    ax.scatter([x], [y], s=150, color=CRIT if h["starts_locked"] else S1,
               edgecolor=SURFACE, linewidth=2, zorder=5)
    ax.annotate(f"hire {h['hire']}", (x, y), textcoords="offset points", xytext=(0, -17),
                ha="center", fontsize=8, color=INK)
ax.scatter([4], [4], marker="s", s=170, color=INK, edgecolor=SURFACE, linewidth=2, zorder=6)
ax.annotate("farmer", (4, 4), textcoords="offset points", xytext=(-4, 14),
            ha="center", fontsize=8, color=INK, fontweight="bold")

ax.set_xticks(range(10)); ax.set_yticks(range(10))
ax.set_title("The board: one quadrant is yours,\nand 3 of every 4 hires spawn outside it")
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
ax.legend(handles=[
    Patch(facecolor="#dbe9fb", label="unlocked at start"),
    Patch(facecolor="#f2f1ec", label="locked"),
    plt.Line2D([], [], marker="o", ls="", color=CRIT, label="hire spawns on locked land"),
    plt.Line2D([], [], marker="o", ls="", color=S1, label="hire spawns on your land"),
], loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=2)

# --- right: walking distance from the shed ---
ax = axes[1]
dist = np.array(distance_map())
im = ax.imshow(dist, cmap=SEQ_CMAP, origin="upper")
for y in range(10):
    for x in range(10):
        v = dist[y][x]
        ax.text(x, y, str(v), ha="center", va="center", fontsize=8,
                color="#ffffff" if v >= 9 else INK2)
ax.axhline(4.5, color=AXIS, lw=1.2); ax.axvline(4.5, color=AXIS, lw=1.2)
ax.set_xticks(range(10)); ax.set_yticks(range(10))
ax.set_title("Turns to walk from the shed to any tile\n(one move = one whole action)")
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cb.set_label("moves", color=INK2); cb.outline.set_visible(False)
cb.ax.tick_params(color=MUTED, labelcolor=INK2)

fig.suptitle("Geometry is the budget", x=0.005, ha="left", fontsize=14,
             fontweight="bold", color=INK)
fig.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()

print("Round trip from the shed into each quadrant (a round trip is what a harvest actually costs):\n")
print(f"{'quadrant':>9}  {'price':>7}  {'mean round trip':>16}  {'worst':>7}")
for r in quadrant_travel_cost():
    print(f"{r['quadrant']:>9}  {money(r['price']):>7}  {r['mean_round_trip']:>13} turns  {r['worst_round_trip']:>2} turns")
print(f"\nA day is only {TURNS_PER_DAY} turns long.")

rows = [crop_timeline(c) for c in CROPS]
print(f"{'crop':>11} {'seed':>5} {'window':>8} {'waterings':>10} {'advertised':>11} {'reachable':>10} {'+fertilizer':>12}")
for r in rows:
    win = f"{r['window_start']}-{r['window_end']}" if r["window_start"] is not None else "n/a"
    n_w = (r["window_end"] - r["window_start"] + 1) if r["window_start"] is not None else 0
    gap = "  <-- unreachable" if r["reachable_yield"] < r["advertised_max_yield"] else ""
    print(f"{r['crop']:>11} {money(r['seed_cost']):>5} {win:>8} {n_w:>10} "
          f"{r['advertised_max_yield']:>11} {r['reachable_yield']:>10} {r['reachable_fertilized']:>12}{gap}")

fig, ax = plt.subplots(figsize=(12.5, 5.2))
crops = list(CROPS)
y_pos = {c: i for i, c in enumerate(reversed(crops))}

for c in crops:
    t = crop_timeline(c)
    y = y_pos[c]
    end = t["cycle_days"]
    # tile occupied
    ax.barh(y, end, height=0.52, color="#e8eef7", zorder=2)
    if t["window_start"] is not None:
        ws, we = t["window_start"], t["window_end"]
        ax.barh(y, we - ws + 1, left=ws, height=0.52, color=S1, zorder=3)
        ax.plot([t["first_yield_day"]], [y], marker="o", ms=9, color=S2,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=5)
    for d in t["production_days"]:
        ax.plot([d], [y], marker="o", ms=9, color=S3,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=5)
    # decay tail: 1 unit every 2 steps once past lifespan -> 12 units/day
    if t["decay_starts_day"] is not None:
        dstart = t["decay_starts_day"]
        ddays = t["reachable_yield"] * 2 / TURNS_PER_DAY
        ax.barh(y, ddays, left=dstart, height=0.52, color=CRIT, zorder=4)
        ax.annotate("dead", (dstart + ddays, y), textcoords="offset points",
                    xytext=(6, 0), va="center", fontsize=8, color=CRIT)
    ax.text(-0.4, y, f"{t['reachable_yield']} units", ha="right", va="center",
            fontsize=9, color=INK, fontweight="bold")

ax.set_yticks(list(y_pos.values()))
ax.set_yticklabels([f"{c}  (${CROPS[c]['seed']})" for c in reversed(crops)])
ax.set_xlim(-6, 20)
ax.set_xlabel("days since planting")
ax.set_title("Every crop's real lifecycle — and how fast a ripe tile rots")
tidy(ax, xgrid=True, ygrid=False)
ax.legend(handles=[
    Patch(facecolor="#e8eef7", label="tile occupied, no yield gain"),
    Patch(facecolor=S1, label="watering window (+1 unit per watered day)"),
    plt.Line2D([], [], marker="o", ls="", color=S2, label="first day harvestable (one-time)"),
    plt.Line2D([], [], marker="o", ls="", color=S3, label="scheduled production (ongoing)"),
    Patch(facecolor=CRIT, label="decay: 1 unit every 2 turns"),
], loc="lower right", ncol=2)
fig.tight_layout()
plt.show()

fig, axes = plt.subplots(3, 3, figsize=(13, 9.5), sharex=True)
span = 900
for ax, item in zip(axes.flat, PRODUCTS):
    p = MARKET_PARAMS[item]
    inv, pr = price_curve(item, MARKET_I0 - span, MARKET_I0 + span, n=900)
    x = [i - MARKET_I0 for i in inv]
    ax.axvspan(0, span, color="#faeee8", zorder=0)
    ax.plot(x, pr, color=S1, zorder=3)
    ax.axvline(0, color=AXIS, lw=1)
    ax.axhline(p["base"], color=MUTED, lw=0.8, zorder=1)
    ax.annotate(f"base ${p['base']}", (-span, p["base"]), textcoords="offset points",
                xytext=(2, 4), fontsize=8, color=MUTED)
    fp = floor_point(item)
    if fp is not None and fp <= span:
        ax.plot([fp], [1], marker="o", ms=7, color=CRIT,
                markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=5)
        ax.annotate(f"$1 at\n{fp} units", (fp, 1), textcoords="offset points",
                    xytext=(6, 12), fontsize=8, color=CRIT, fontweight="bold")
    ax.set_title(f"{item}   ↓{p['above_func']}×{p['above_target']}  ↑{p['below_func']}×{p['below_target']}",
                 fontsize=10)
    ax.set_ylim(0, p["base"] * 2.3)
    tidy(ax)

for ax in axes[-1]:
    ax.set_xlabel("market inventory − I₀")
for ax in axes[:, 0]:
    ax.set_ylabel("price")
fig.suptitle("The price curve of every tradable — glut side shaded",
             x=0.005, ha="left", fontsize=14, fontweight="bold", color=INK)
fig.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()

cal = calibration_table()
print(f"{'line':>11} {'product':>11} {'one field / 24d':>16} {'source T':>9} {'ratio':>6}")
for r in cal:
    mark = "  exact" if r["matches"] else ""
    print(f"{r['line']:>11} {r['product']:>11} {r['computed_capacity']:>16} {r['source_T']:>9} {r['ratio']:>6}{mark}")

tab = price_table()
print(f"{'product':>11} {'base':>5} {'floor at':>10} {'max revenue in one turn':>24} {'town shops':>11}")
for r in tab:
    fp = r["floor_units"]
    if fp is None:
        print(f"{r['item']:>11} {money(r['base']):>5} {'never':>10} {'unbounded':>24} {r['n_shops']:>11}")
    else:
        rev, _, _ = sell_revenue(r["item"], fp + 400)
        print(f"{r['item']:>11} {money(r['base']):>5} {fp:>7} units {money(rev):>24} {r['n_shops']:>11}")

fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={"width_ratios": [1, 1.25]})

# --- left: floor points ---
ax = axes[0]
finite = [(r["item"], r["floor_units"]) for r in tab if r["floor_units"] is not None]
finite.sort(key=lambda kv: kv[1])
names = [k for k, _ in finite]; vals = [v for _, v in finite]
ax.barh(names, vals, height=0.6, color=S1, zorder=3)
for n, v in finite:
    ax.annotate(f"{v}", (v, n), textcoords="offset points", xytext=(5, 0),
                va="center", fontsize=9, color=INK, fontweight="bold")
never = ", ".join(r["item"] for r in tab if r["floor_units"] is None)
ax.annotate(f"{never} never reach $1\nat any sale size",
            (0.5, 0.12), xycoords="axes fraction", fontsize=9.5,
            color=GOOD, fontweight="bold")
ax.set_xscale("log")
ax.set_xlabel("units sold in one turn before the price pins to $1  (log scale)")
ax.set_title("How much a single turn can absorb")
tidy(ax, xgrid=True, ygrid=False)

# --- right: revenue saturation ---
ax = axes[1]
highlight = {"MELON": S1, "WOOL": S2, "STRAWBERRY": S3}
ns = list(range(1, 601, 3))
for item in ["CARROT", "TOMATO", "MILK", "EGG", "WHEAT", "FERTILIZER"]:
    ys = [sell_revenue(item, n)[0] for n in ns]
    ax.plot(ns, ys, color="#d8d7d0", lw=1.4, zorder=2)
for item, col in highlight.items():
    ys = [sell_revenue(item, n)[0] for n in ns]
    ax.plot(ns, ys, color=col, zorder=4, label=item)
    fp = floor_point(item)
    ax.plot([fp], [sell_revenue(item, fp)[0]], marker="o", ms=8, color=col,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=5)
    ax.annotate(f"{item}\nsaturates at {money(ys[-1])}", (ns[-1], ys[-1]),
                textcoords="offset points", xytext=(-8, 0), ha="right",
                fontsize=8.5, color=col, fontweight="bold")
ax.annotate("everything else", (ns[-1], sell_revenue("CARROT", ns[-1])[0]),
            textcoords="offset points", xytext=(-8, 8), ha="right",
            fontsize=8.5, color=MUTED)
ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(money))
ax.set_xlabel("units dumped in a single turn")
ax.set_ylabel("total revenue")
ax.set_title("Revenue has a ceiling: past the floor point, extra units earn $1 each")
tidy(ax)
ax.legend(loc="center right")

fig.tight_layout()
plt.show()

print(f"{'product':>11} {'shops':>5}   demanded by")
for r in price_table():
    print(f"{r['item']:>11} {r['n_shops']:>5}   {', '.join(r['shops']) if r['shops'] else '— nothing —'}")

# Reproduce the no-trade drift live. EXP-08 ran 160 seeds; 12 is enough to show the shape.
LIVE_SEEDS = list(range(101, 113))
paths = {it: [] for it in PRODUCTS}
orders = []
for seed in LIVE_SEEDS:
    env = make("kaggriculture", configuration={"episodeSteps": EPISODE_STEPS, "seed": seed})
    env.run(["pass", "pass"])
    orders.append(env.steps[-1][0].observation["town"]["unlocked_shops"])
    for it in PRODUCTS:
        paths[it].append([s[0].observation["market"]["prices"][it] for s in env.steps])
print(f"{len(LIVE_SEEDS)} episodes, no player ever traded. Distinct shop-unlock orders: "
      f"{len({tuple(o) for o in orders})}")

fig, axes = plt.subplots(3, 3, figsize=(13, 9), sharex=True)
days = np.arange(EPISODE_STEPS) / TURNS_PER_DAY
for ax, item in zip(axes.flat, PRODUCTS):
    arr = np.array([p[:EPISODE_STEPS] for p in paths[item]], dtype=float)
    lo, hi, mean = arr.min(0), arr.max(0), arr.mean(0)
    base = MARKET_PARAMS[item]["base"]
    ax.fill_between(days, lo, hi, color=S1, alpha=0.18, linewidth=0, zorder=2)
    ax.plot(days, mean, color=S1, zorder=4)
    ax.axhline(base, color=MUTED, lw=0.8, zorder=1)
    for d in (10, 20):
        ax.axvline(d, color=GRID, lw=1, zorder=1)
    drift = (mean[-1] / base - 1) * 100
    col = GOOD if drift > 50 else INK2
    ax.annotate(f"{drift:+.0f}%", (days[-1], mean[-1]), textcoords="offset points",
                xytext=(-4, 4), ha="right", fontsize=10, color=col, fontweight="bold")
    ax.set_title(item, fontsize=10)
    tidy(ax)
for ax in axes[-1]:
    ax.set_xlabel("day")
for ax in axes[:, 0]:
    ax.set_ylabel("price")
fig.suptitle("Prices with zero player trading — the town alone lifts them all season",
             x=0.005, ha="left", fontsize=14, fontweight="bold", color=INK)
fig.text(0.005, 0.925, "band = spread across 12 seeds · grey rules = town-centre demand "
         "doubling (day 10) and quadrupling (day 20)", fontsize=9, color=INK2)
fig.tight_layout(rect=[0, 0, 1, 0.92])
plt.show()

CONTEST_N = 60
rows = []
for item in PRODUCTS:
    solo, _, _ = sell_revenue(item, CONTEST_N)
    mine, _, _ = sell_revenue_contested(item, CONTEST_N, CONTEST_N)
    rows.append((item, solo, mine, (1 - mine / solo) * 100 if solo else 0))
rows.sort(key=lambda r: -r[3])

fig, ax = plt.subplots(figsize=(11.5, 5))
y = np.arange(len(rows))
ax.barh(y + 0.20, [r[1] for r in rows], height=0.36, color=S1, label="selling alone", zorder=3)
ax.barh(y - 0.20, [r[2] for r in rows], height=0.36, color=S2,
        label="rival dumps the same amount, same turn", zorder=3)
for i, r in enumerate(rows):
    ax.annotate(f"−{r[3]:.0f}%", (max(r[1], r[2]), i), textcoords="offset points",
                xytext=(6, 0), va="center", fontsize=9,
                color=CRIT if r[3] > 30 else INK2, fontweight="bold")
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows])
ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(money))
ax.set_xlabel(f"revenue from selling {CONTEST_N} units in one turn")
ax.set_title(f"What a mirror-match costs you: both players dumping {CONTEST_N} units at once")
tidy(ax, xgrid=True, ygrid=False)
ax.legend(loc="lower right")
fig.tight_layout()
plt.show()

for i, t in enumerate(TRAPS, 1):
    print(f"{i}. {t['name']}   [{t['source']}]")
    print(f"   rule: {t['rule']}")
    print(f"   cost: {t['cost']}\n")

def step_toward(pos, target):
    (x, y), (tx, ty) = pos, target
    if y != ty: return "SOUTH" if ty > y else "NORTH"
    if x != tx: return "EAST" if tx > x else "WEST"
    return None

PLANT_TARGETS = [(4, 4), (3, 4), (2, 4), (1, 4), (0, 4), (4, 3)]

def atomic_plant_probe(seeds_held, planters):
    '''Walk every unit onto its own tile, then have them all PLANT at once.'''
    log = {"planted": False}
    def agent(obs):                       # one parameter: kaggle-environments
        me = obs["farms"][obs["player"]]  # passes `configuration` to any second one
        hands = me["hands"]; n = len(hands)
        have = obs["private"]["seeds"].get("WHEAT", 0)
        noop = {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}
        if n < planters - 1:      return {**noop, "market": [["HIRE"]]}
        if have < seeds_held:     return {**noop, "market": [["BUY_SEED", "WHEAT", seeds_held - have]]}
        if log["planted"]:        return noop
        pos = [me["farmer"]] + list(hands)
        ops = [step_toward(tuple(p), PLANT_TARGETS[i]) for i, p in enumerate(pos)]
        if any(ops):
            acts = [[o] if o else ["PASS"] for o in ops]
            return {"farmer": acts[0], "hands": acts[1:], "market": []}
        log["planted"] = True
        return {"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]] * n, "market": []}

    env = make("kaggriculture", configuration={"episodeSteps": 24, "seed": 101})
    env.run([agent, "pass"])
    farm = env.steps[-1][0].observation["farms"][0]
    return sum(1 for row in farm["tiles"] for t in row
               if isinstance(t, dict) and t.get("kind") == "PLANT")

print(f"{'units asking to PLANT':>22} {'seeds held':>11} {'planted':>8} {'partial fill would give':>24}")
for seeds, planters in ((6, 6), (5, 6), (3, 3), (2, 3)):
    got = atomic_plant_probe(seeds, planters)
    print(f"{planters:>22} {seeds:>11} {got:>8} {min(seeds, planters):>24}")

def unwatered_probe():
    state = {"planted": None, "weed": None}
    def agent(obs):
        me = obs["farms"][obs["player"]]
        fx, fy = me["farmer"]; tile = me["tiles"][fy][fx]
        if obs["private"]["seeds"].get("WHEAT", 0) == 0 and state["planted"] is None:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
        if tile is None and state["planted"] is None:
            state["planted"] = obs["step"]
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
        if isinstance(tile, dict) and tile.get("kind") == "WEED" and state["weed"] is None:
            state["weed"] = obs["step"]
        return {"farmer": ["PASS"], "hands": [], "market": []}
    env = make("kaggriculture", configuration={"episodeSteps": 120, "seed": 101})
    env.run([agent, "pass"])
    return state

s = unwatered_probe()
print(f"planted at step {s['planted']}, became a weed at step {s['weed']} "
      f"— {s['weed'] - s['planted']} turns, the very first end-of-day.\n")

def decay_probe():
    trace = []
    def agent(obs):
        me = obs["farms"][obs["player"]]
        fx, fy = me["farmer"]; tile = me["tiles"][fy][fx]
        market = []
        if obs["private"]["seeds"].get("MELON", 0) == 0 and tile is None:
            market = [["BUY_SEED", "MELON", 1]]
        if tile is None and obs["private"]["seeds"].get("MELON", 0) > 0:
            return {"farmer": ["PLANT", "MELON"], "hands": [], "market": market}
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            trace.append((obs["step"], tile["yield_units"], tile["max_lifespan_step"]))
            if not tile["watered_today"]:
                return {"farmer": ["WATER"], "hands": [], "market": market}
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            trace.append((obs["step"], 0, None))
        return {"farmer": ["PASS"], "hands": [], "market": market}
    env = make("kaggriculture", configuration={"episodeSteps": 400, "seed": 101})
    env.run([agent, "pass"])
    return trace

tr = decay_probe()
mls = next(m for _, _, m in tr if m)
peak = max(u for _, u, _ in tr)
weed = next(s for s, u, m in tr if m is None)
print(f"A melon grown to its full {peak} units, then left unharvested:")
print(f"  max_lifespan_step = {mls}  (= (planted_day + max_yield_day + 1) x 24)")
print(f"  became a weed at step {weed}  —  {weed - mls} turns later, "
      f"under half a day.")

from kaggle_environments.envs.kaggriculture.kaggriculture import (
    _process_market, _new_market, _new_farm, _new_private)

def market_fixture(stock):
    market = _new_market()
    farms = [_new_farm(10, 0.0) for _ in range(2)]
    privates = [_new_private() for _ in range(2)]
    for pid, s in enumerate(stock):
        for item, n in s.items():
            privates[pid]["shed"][item] = n
    class O: pass
    class S: pass
    states = []
    for pid in range(2):
        o = O(); o.market, o.farms, o.private, o.player = market, farms, privates[pid], pid
        s = S(); s.observation, s.action = o, {}
        states.append(s)
    class Cfg:
        boardSize = 10; maxMarketOrdersPerTurn = 10
        farmHandCostMult = 1; shedCapacity = 10_000_000
    class Env: configuration = Cfg()
    return states, Env(), market, farms

SIZES = [1, 5, 20, 50, 60, 100, 158, 300, 529, 842, 1500]
checked = mismatched = 0
for item in PRODUCTS:
    for n in SIZES:
        st_, env_, mk, fm = market_fixture([{item: n}, {}])
        st_[0].action = {"market": [["SELL", item, n]]}
        _process_market(st_, env_)
        pred, _, pred_inv = sell_revenue(item, n)
        checked += 1
        mismatched += not (abs(fm[0]["money"] - pred) < 1e-6 and mk["inventory"][item] == pred_inv)

        st2, env2, mk2, fm2 = market_fixture([{item: n}, {item: n}])
        st2[0].action = {"market": [["SELL", item, n]]}
        st2[1].action = {"market": [["SELL", item, n]]}
        _process_market(st2, env2)
        pa, pb, _ = sell_revenue_contested(item, n, n)
        checked += 1
        mismatched += not (abs(fm2[0]["money"] - pa) < 1e-6 and abs(fm2[1]["money"] - pb) < 1e-6)

print(f"{checked} predictions checked against the environment's own market loop")
print(f"mismatches: {mismatched}")



