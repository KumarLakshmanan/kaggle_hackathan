from dataclasses import dataclass, field
import math
import matplotlib.pyplot as plt
import numpy as np

TURNS_PER_DAY, DAYS = 24, 30
TOTAL_ACTIONS = TURNS_PER_DAY * DAYS
print(f"Season budget: {TURNS_PER_DAY} turns/day x {DAYS} days = {TOTAL_ACTIONS} farmer actions")
print("Market orders are separate (10/turn), so BUY/SELL cost no farmer actions.")

TURNS = TURNS_PER_DAY * DAYS          # 720 turns in a season

# Transcribed from each release. `schedule` is (day_threshold, multiplier), highest first;
# None means the release has no schedule and the town centre buys a flat 1 per firing.
ECONOMIES = {
    "1.29.3": dict(center_interval=6,  schedule=[(20, 4), (10, 2), (0, 1)], replacement=False),
    "1.32.5": dict(center_interval=12, schedule=[(20, 4), (10, 2), (0, 1)], replacement=False),
    "1.32.6": dict(center_interval=24, schedule=None,                       replacement=True),
}

def town_centre_season_demand(econ):
    """Units of EACH product the town centre removes over one 30-day season."""
    total = 0
    for step in range(TURNS):
        if step % econ["center_interval"] == 0:
            if econ["schedule"] is None:
                total += 1
            else:
                day = step // TURNS_PER_DAY
                total += next(m for thr, m in econ["schedule"] if day >= thr)
    return total

demand = {v: town_centre_season_demand(e) for v, e in ECONOMIES.items()}
for v, d in demand.items():
    print(f"  {v:<8} {d:>4} units of each product bought per season")
print(f"\n  1.29.3 -> 1.32.6 : {demand['1.29.3'] / demand['1.32.6']:.2f}x cut "
      f"({demand['1.29.3'] - demand['1.32.6']} units of demand removed)")

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(list(demand), list(demand.values()), color=["#AAAAAA", "#FF851B", "#FF4136"])
for b, v in zip(bars, demand.values()):
    ax.text(b.get_x() + b.get_width() / 2, v + 6, str(v), ha="center", fontweight="bold")
ax.set_ylabel("units of each product the town centre buys per season")
ax.set_title("The town stopped buying\n"
             "kaggriculture town-centre demand, by kaggle-environments release",
             fontweight="bold")
ax.text(0.5, 0.62, "Kaggle's stock notebook image\nships the one on the left",
        transform=ax.transAxes, ha="center", fontsize=10, color="#0074D9")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.show()

@dataclass
class Crop:
    name: str
    seed_cost: int
    price: int          # base market price per unit
    max_yield_day: int  # age at which the yield bonus stops accruing
    max_yield: int      # cap on harvestable units (unfertilized figure in the README)
    ongoing: bool = False
    yield_interval: int = 0   # days between scheduled productions (ongoing only)
    n_yields: int = 0         # number of scheduled productions before decay

# One-time crops. README: "Wheat and Carrot only reach their listed Max Yield of 6 and 4
# with fertilizer; watering alone peaks at 4 and 3." So max_yield here is the watered-only
# figure, which is what the no-fertilizer baseline should use.
CROPS = [
    Crop("Wheat",      10,  25, max_yield_day=4,  max_yield=4),
    Crop("Carrot",     20,  35, max_yield_day=3,  max_yield=3),
    Crop("Melon",      80, 250, max_yield_day=12, max_yield=6),
    Crop("Tomato",     50,  60, max_yield_day=11, max_yield=4, ongoing=True, yield_interval=1, n_yields=4),
    Crop("Strawberry",100, 120, max_yield_day=16, max_yield=4, ongoing=True, yield_interval=2, n_yields=4),
]

@dataclass
class Animal:
    name: str
    cost: int
    price: int          # price per unit of product
    first_yield_day: int
    interval: int       # days between scheduled productions
    max_held: int       # cap on unharvested units on the tile
    build_actions: int = 2   # BUILD_COOP/PASTURE + PLACE

ANIMALS = [
    Animal("Goose/Egg",  300,  50, first_yield_day=4, interval=1, max_held=4),
    Animal("Cow/Milk",   400, 160, first_yield_day=8, interval=2, max_held=6),
    Animal("Sheep/Wool", 500, 200, first_yield_day=6, interval=3, max_held=6),
]

for c in CROPS: print(f"{c.name:<11} seed {c.seed_cost:>4}  price {c.price:>4}")
for a in ANIMALS: print(f"{a.name:<11} cost {a.cost:>4}  price {a.price:>4}  every {a.interval}d")

def watering_days(crop):
    """Minimum set of days to water for max yield: survive, then saturate the window."""
    window_start = math.ceil(crop.max_yield_day / 2)
    # Yield is base 1 plus one unit per watered day in the window, capped at max_yield.
    days_needed_in_window = min(crop.max_yield - 1, crop.max_yield_day - window_start + 1)
    harvest_day = window_start + days_needed_in_window - 1

    days = {0}                                    # planting day is mandatory
    days |= set(range(window_start, harvest_day + 1))   # daily through the window
    d = 0                                          # every-other-day survival before the window
    while d < window_start:
        days.add(d); d += 2
    return sorted(days), harvest_day

print(f"{'crop':<11} {'window':<9} {'harvest':<8} {'waters':<7} yield")
for c in CROPS:
    if c.ongoing: continue
    w, h = watering_days(c)
    print(f"{c.name:<11} day {math.ceil(c.max_yield_day/2):<5} {h:<8} {len(w):<7} {min(c.max_yield, 1+sum(1 for d in w if d>=math.ceil(c.max_yield_day/2)))}")

def one_time_yield(crop):
    w, _ = watering_days(crop)
    window_start = math.ceil(crop.max_yield_day / 2)
    bonus = sum(1 for d in w if d >= window_start)
    return min(crop.max_yield, 1 + bonus)

checks = {"Wheat": 4, "Carrot": 3, "Melon": 6}
ok = True
for c in CROPS:
    if c.name in checks:
        got, want = one_time_yield(c), checks[c.name]
        flag = "OK " if got == want else "MISMATCH"
        if got != want: ok = False
        print(f"  {flag} {c.name:<8} model={got}  README={want}")
print("\nmodel reproduces the README's stated yields" if ok else "\nMODEL DISAGREES WITH SPEC — trust the spec, not this notebook")

def crop_profit_per_action(crop):
    if not crop.ongoing:
        w, harvest_day = watering_days(crop)
        actions = 1 + len(w) + 1                       # PLANT + WATERs + HARVEST
        units = one_time_yield(crop)
        profit = units * crop.price - crop.seed_cost
        return profit / actions, actions, units, harvest_day
    # Ongoing: base 1 per scheduled production, water daily to survive/keep it alive.
    last_day = crop.max_yield_day
    waters = len({0} | set(range(0, last_day + 1, 2)))
    actions = 1 + waters + crop.n_yields               # PLANT + WATERs + one HARVEST each
    units = crop.n_yields
    profit = units * crop.price - crop.seed_cost
    return profit / actions, actions, units, last_day

def animal_profit_per_action(a, care, horizon_days=None):
    """Actions and profit over the animal's productive window within the season."""
    horizon = horizon_days if horizon_days else DAYS
    prod_days = list(range(a.first_yield_day, horizon + 1, a.interval))
    if not prod_days: return 0.0, 0, 0
    feed = horizon - 0                                  # FEED every day it is alive
    care_actions = feed if care else 0
    harvests = len(prod_days)
    actions = a.build_actions + feed + care_actions + harvests

    if not care:
        units = harvests                                # base 1 each
    else:
        # Bank +1 per cared day between productions, paid out at the next production,
        # capped by max_held.
        units, bank = 0, 0
        for d in range(1, horizon + 1):
            bank += 1                                   # fed AND cared this day
            if d in prod_days:
                units += min(1 + bank, a.max_held); bank = 0
    profit = units * a.price - a.cost
    return profit / actions, actions, units

rows = []
for c in CROPS:
    ppa, act, units, _ = crop_profit_per_action(c)
    rows.append((c.name, ppa, act, units, "crop"))
for a in ANIMALS:
    for care in (False, True):
        ppa, act, units = animal_profit_per_action(a, care)
        rows.append((f"{a.name}{' +CARE' if care else ''}", ppa, act, units, "animal"))

rows.sort(key=lambda r: -r[1])
print(f"{'strategy':<20} {'$/action':>9} {'actions':>8} {'units':>6}")
print("-" * 47)
for name, ppa, act, units, _ in rows:
    print(f"{name:<20} {ppa:>9.1f} {act:>8} {units:>6}")

names = [r[0] for r in rows][::-1]
vals  = [r[1] for r in rows][::-1]
cols  = ["#2ECC40" if r[4] == "crop" else "#FF851B" for r in rows][::-1]

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.barh(names, vals, color=cols)
ax.set_xlabel("profit per farmer action ($)")
ax.set_title("What a turn is worth, by strategy", fontweight="bold")
for i, v in enumerate(vals):
    ax.text(v + max(vals) * 0.01, i, f"{v:.0f}", va="center", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.show()

import importlib.metadata as _md
from kaggle_environments import make

try:
    KE_VERSION = _md.version("kaggle-environments")
except Exception:
    KE_VERSION = "unknown"

def idle(obs, cfg):
    return {}

def run_idle(seed=None):
    env = make("kaggriculture", configuration=({"seed": seed} if seed is not None else {}),
               debug=False)
    env.run([idle, idle])
    obs = env.steps[-1][0].observation
    absorbed = {k: 10000 - v for k, v in obs["market"]["inventory"].items()}
    return absorbed, list(obs["town"]["unlocked_shops"])

absorbed, shops = run_idle(seed=1)
melon = absorbed["MELON"]
match = [v for v, d in demand.items() if d == melon]

print(f"kaggle-environments reports version : {KE_VERSION}")
print(f"MELON units absorbed in an idle season: {melon}")
print(f"that demand level belongs to          : {', '.join(match) if match else 'none of the three'}")
print(f"\nshops this season unlocked: {len(set(shops))} distinct out of 8")
print("\nfull idle-season absorption:")
for item, n in absorbed.items():
    print(f"  {item:<11} {n:>5}")

from kaggle_environments.envs.kaggriculture.kaggriculture import SHOPS, PRODUCTS

print("shop baskets, straight out of the engine:")
for name, basket in SHOPS.items():
    print(f"  {name:<15} {', '.join(basket)}")

sellers = {p: [s for s, basket in SHOPS.items() if p in basket]
           for p in PRODUCTS if p != "FERTILIZER"}
print(f"\n{'product':<11} {'shops that buy it':>18}   which")
print("-" * 62)
for p, ss in sorted(sellers.items(), key=lambda kv: len(kv[1])):
    print(f"{p:<11} {len(ss):>18}   {', '.join(ss) if ss else '-- none --'}")

N_SLOTS, N_SHOPS = 8, len(SHOPS)     # 8 unlocks at townShopUnlockInterval=3 within 30 days

print("probability a product gets NO shop buyer all season")
print(f"{'product':<11} {'buyers':>7} {'<= 1.32.5':>11} {'1.32.6':>9}")
print("-" * 41)
for p, ss in sorted(sellers.items(), key=lambda kv: len(kv[1])):
    m = len(ss)
    p_new = ((N_SHOPS - m) / N_SHOPS) ** N_SLOTS    # 8 draws with replacement
    p_old = 1.0 if m == 0 else 0.0                  # without replacement, all 8 unlock
    print(f"{p:<11} {m:>7} {p_old * 100:>10.1f}% {p_new * 100:>8.1f}%")

print(f"\nexpected distinct shops under 1.32.6: "
      f"{N_SHOPS * (1 - ((N_SHOPS - 1) / N_SHOPS) ** N_SLOTS):.2f} of {N_SHOPS} "
      f"(earlier releases always delivered all {N_SHOPS})")

import math

# _shape and market_price, transcribed from kaggriculture.py — identical in both releases.
# Note the last line of market_price: max(PRICE_FLOOR, int(round(price))). Prices are
# integers, and rounding is not cosmetic — it moves where the $1 floor is reached on the
# shallow curves. Reproduce it exactly or the numbers below are approximately right, which
# is the wrong kind of right.
PRICE_FLOOR = 1

def _shape(func, x):
    x = max(0.0, x)
    return {"linear": x, "sq": x * x, "sqrt": math.sqrt(x),
            "log": math.log(1.0 + x), "log10": math.log10(1.0 + x)}[func]

def glut_price(base, func, target, T, units_sold):
    amp = target * base / _shape(func, T)
    return max(PRICE_FLOOR, int(round(base - amp * _shape(func, units_sold))))

# above_func / above_target / T, transcribed per release. base and T never changed.
GLUT = {   # product: (base, above_func, T, target_1293, target_1326)
    "MELON":      (250, "sq",     300, 0.90, 3.60),
    "WOOL":       (200, "sq",     105, 0.80, 3.20),
    "MILK":       (160, "linear", 122, 0.40, 1.60),
    "STRAWBERRY": (120, "linear", 100, 0.40, 1.60),
    "TOMATO":     ( 60, "sqrt",   200, 0.60, 0.60),
    "EGG":        ( 50, "log",    332, 0.20, 0.20),
    "CARROT":     ( 35, "sqrt",   450, 0.70, 0.70),
    "WHEAT":      ( 25, "log",    400, 0.20, 0.20),
}

def walk_down(base, func, target, T, k):
    """Revenue from selling k units, quoting each unit the way interpreter() does."""
    revenue, inv = 0.0, 0
    for _ in range(k):
        price = glut_price(base, func, target, T, inv)
        revenue += price
        if price > 1:              # sales at the $1 floor do not add to supply
            inv += 1
    return revenue

K = 20
print(f"fraction of the base-price estimate you actually collect, selling {K} units")
print(f"{'product':<11} {'1.29.3':>8} {'1.32.6':>8}    {'$1 floor at (1.32.6)':>20}")
print("-" * 52)
for p, (base, func, T, t_old, t_new) in GLUT.items():
    r_old = walk_down(base, func, t_old, T, K) / (base * K)
    r_new = walk_down(base, func, t_new, T, K) / (base * K)
    floor = next((k for k in range(1, 3001) if glut_price(base, func, t_new, T, k) <= 1), None)
    print(f"{p:<11} {r_old:>8.2f} {r_new:>8.2f}    {(str(floor) if floor else '>3000'):>20}")

print("days for the town centre alone to re-absorb a glut you create")
print(f"{'glut':>7} {'1.29.3 (day 20+)':>18} {'1.32.6':>9}")
print("-" * 36)
OLD_LATE = (TURNS_PER_DAY // ECONOMIES["1.29.3"]["center_interval"]) * 4   # firings/day x late multiplier
NEW_RATE = TURNS_PER_DAY // ECONOMIES["1.32.6"]["center_interval"]         # 1/day, flat
for k in (6, 12, 20, 60):
    print(f"{k:>5} u {k / OLD_LATE:>16.1f}d {k / NEW_RATE:>8.0f}d")
print("\n(town centre only; melon has no other buyer, so for melon this is the whole story)")