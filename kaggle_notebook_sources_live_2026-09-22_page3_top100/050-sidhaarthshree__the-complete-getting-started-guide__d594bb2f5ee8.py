%pip install -q -U kaggle-environments
import kaggle_environments
print("kaggle-environments", kaggle_environments.version)

from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
print("configuration:")
for k, v in env.configuration.items():
    print(f"  {k:26} = {v}")

env.run(["starter", "random"])
final = env.steps[-1]
for i, s in enumerate(final):
    print(f"Player {i}: reward={s['reward']}, status={s['status']}")

#Will Work Only in Runtime
from IPython.display import HTML, IFrame
import html as _html


def show_replay(env, width=1000, height=720, mode="file", path="replays.html"):
    """Render an episode's visualiser inline. mode="file" (light) or "srcdoc" (heavy)."""
    doc = env.render(mode="html", width=width, height=height)

    if mode == "file":
        with open(path, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"wrote {path}  ({len(doc)/1024/1024:.1f} MB, kept OUT of the notebook)")
        return IFrame(src=path, width=width, height=height)

    return HTML(
        f'<iframe srcdoc="{_html.escape(doc, quote=True)}" '
        f'width="{width}" height="{height}" frameborder="0" '
        f'style="border:1px solid #ddd;border-radius:8px"></iframe>'
    )


show_replay(demo)

import json
from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 48}, debug=False)

CAPTURED = {}

def spy(obs):
    """An agent that records the observation it is handed, then does nothing useful."""
    if obs["step"] == 30:
        CAPTURED["obs"] = json.loads(json.dumps(obs))  # deep copy of a plain dict
    return {"farmer": ["PASS"], "hands": [], "market": []}

env.run([spy, "starter"])
obs = CAPTURED["obs"]

print("top-level keys :", sorted(obs.keys()))
print("day / hour     :", obs["day"], "/", obs["hour"])
print("my player id   :", obs["player"])
print("market prices  :", obs["market"]["prices"])
print("market inv     :", obs["market"]["inventory"])
print("unlocked shops :", obs["town"]["unlocked_shops"])
print("my shed        :", obs["private"]["shed"])
print("my seeds       :", obs["private"]["seeds"])
print("my money       :", obs["farms"][obs["player"]]["money"])

CROPS   = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
ANIMALS = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
PRODUCE = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def read_board(obs):
    """Flatten the observation into the handful of facts an agent actually uses."""
    me = obs["farms"][obs["player"]]
    opp = obs["farms"][1 - obs["player"]]
    tiles = me["tiles"]
    n = len(tiles)

    owned, empty, plants, weeds, structures = [], [], [], [], []
    for y in range(n):
        for x in range(n):
            t = tiles[y][x]
            if t == "LOCKED":
                continue
            owned.append((x, y))
            if t is None:
                empty.append((x, y))
            elif t["kind"] == "PLANT":
                plants.append((x, y, t))
            elif t["kind"] == "WEED":
                weeds.append((x, y))
            else:                       # COOP / PASTURE
                structures.append((x, y, t))

    return {
        "me": me, "opp": opp, "tiles": tiles, "size": n,
        "day": obs["day"], "hour": obs["hour"], "step": obs["step"],
        "money": me["money"],
        "farmer": tuple(me["farmer"]),
        "hands": [tuple(h) for h in me["hands"]],
        "units": [tuple(me["farmer"])] + [tuple(h) for h in me["hands"]],
        "shed": dict(obs["private"]["shed"]),
        "seeds": dict(obs["private"]["seeds"]),
        "invs": [dict(i) for i in obs["private"]["inventories"]],
        "prices": dict(obs["market"]["prices"]),
        "minv": dict(obs["market"]["inventory"]),
        "shops": list(obs["town"]["unlocked_shops"]),
        "owned": owned, "empty": empty, "plants": plants,
        "weeds": weeds, "structures": structures,
    }


b = read_board(obs)
print(f"day {b['day']} hour {b['hour']}  money ${b['money']:.0f}")
print(f"owned tiles {len(b['owned'])}  empty {len(b['empty'])}  plants {len(b['plants'])}  weeds {len(b['weeds'])}")
print(f"farmer at {b['farmer']}, {len(b['hands'])} hands")

def infer_shed(obs, cache={}):
    """Shed position, inferred from the hour-0 spawn and cached for the episode."""
    if "shed" in cache:
        return cache["shed"]
    me = obs["farms"][obs["player"]]
    fx, fy = me["farmer"]
    tiles = me["tiles"]
    n = len(tiles)
    # candidates: neighbours of the spawn that are not ordinary farmable tiles
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        x, y = fx + dx, fy + dy
        if 0 <= x < n and 0 <= y < n and tiles[y][x] == "LOCKED":
            continue
    cache["shed"] = (fx, fy)     # spawn tile is adjacent to the shed; good enough for routing
    return cache["shed"]


# In practice: treat the hour-0 spawn tile as "home". Distance-to-home is what routing needs,
# and being ON home means you are shed-adjacent, so DROP / PICKUP / PLACE work.
print("home (hour-0 spawn) =", tuple(obs["farms"][obs["player"]]["farmer"]))

import math
import pandas as pd

CROP = {
    # seed, base_price, first_yield_day, max_yield_day, max_yield, ongoing, interval
    "WHEAT":      dict(seed=10,  base=25,  first=2,  maxday=4,  maxy=6, ongoing=False, every=0),
    "CARROT":     dict(seed=20,  base=35,  first=2,  maxday=3,  maxy=4, ongoing=False, every=0),
    "TOMATO":     dict(seed=50,  base=60,  first=8,  maxday=0,  maxy=4, ongoing=True,  every=1),
    "STRAWBERRY": dict(seed=100, base=120, first=10, maxday=0,  maxy=4, ongoing=True,  every=2),
    "MELON":      dict(seed=80,  base=250, first=10, maxday=12, maxy=6, ongoing=False, every=1),
}

rows = []
for name, c in CROP.items():
    if not c["ongoing"]:
        window = c["maxday"] - math.ceil(c["maxday"] / 2) + 1        # days of watering bonus
        units  = min(c["maxy"], 1 + window)                          # unfertilized
        unitsF = min(c["maxy"], 1 + 2 * window)                      # fertilized
        cycle  = c["maxday"]                                         # plant -> harvest
        # actions: 1 plant + 1 water/day + 1 harvest
        acts   = 1 + cycle + 1
    else:
        cycle  = c["first"] + (c["maxy"] - 1) * c["every"]            # last scheduled production
        units  = c["maxy"]
        unitsF = c["maxy"] * 2
        acts   = 1 + cycle + c["maxy"]                                # plant + daily water + harvests
    gross  = units * c["base"]
    rows.append(dict(
        crop=name, seed=c["seed"], base=c["base"], cycle_days=cycle,
        units=units, units_fert=unitsF,
        gross_at_base=gross, profit=gross - c["seed"],
        per_tile_day=round((gross - c["seed"]) / cycle, 1),
        actions=acts,
        per_action=round((gross - c["seed"]) / acts, 1),
        cycles_in_30d=30 // cycle,
    ))

df = pd.DataFrame(rows).sort_values("per_tile_day", ascending=False)
df

ANIMAL = {
    # cost, produce, base, first_day, every_n_days, max_held, feed_wheat_per_day
    "GOOSE": dict(cost=300, produce="EGG",  base=50,  first=4, every=1, max_held=4),
    "COW":   dict(cost=400, produce="MILK", base=160, first=8, every=2, max_held=6),
    "SHEEP": dict(cost=500, produce="WOOL", base=200, first=6, every=3, max_held=6),
}

rows = []
for name, a in ANIMAL.items():
    bonus = 1 * a["every"]        # +1 per cared-and-fed day (SOURCE, not the docs' +2)
    per_prod = min(a["max_held"], 1 + bonus)
    per_day  = per_prod / a["every"]
    gross_day = per_day * a["base"]
    # daily actions: FEED + CARE every day, HARVEST on production days
    acts_day = 2 + (1 / a["every"])
    rows.append(dict(
        animal=name, cost=a["cost"], produce=a["produce"], base=a["base"],
        first_yield_day=a["first"], every=a["every"],
        units_per_production=per_prod, units_per_day=round(per_day, 2),
        gross_per_day=round(gross_day, 0),
        actions_per_day=round(acts_day, 2),
        gross_per_action=round(gross_day / acts_day, 0),
        payback_days=round(a["cost"] / gross_day, 1),
        season_gross_if_bought_day2=round((30 - 2 - a["first"]) * gross_day, 0),
    ))

pd.DataFrame(rows).sort_values("gross_per_action", ascending=False)

import math
import numpy as np

I0 = 10000

MARKET_PARAMS = {
    #                base  T     below_f  below_t  above_f  above_t
    "WHEAT":      dict(base=25,  T=400, bf="sqrt",  bt=0.80, af="log",    at=0.20),
    "CARROT":     dict(base=35,  T=450, bf="log",   bt=0.20, af="sqrt",   at=0.70),
    "TOMATO":     dict(base=60,  T=200, bf="linear",bt=0.40, af="sqrt",   at=0.60),
    "STRAWBERRY": dict(base=120, T=100, bf="sqrt",  bt=0.70, af="linear", at=1.60),
    "MELON":      dict(base=250, T=300, bf="log",   bt=0.20, af="sq",     at=3.60),
    "EGG":        dict(base=50,  T=332, bf="linear",bt=0.40, af="log",    at=0.20),
    "MILK":       dict(base=160, T=122, bf="sqrt",  bt=0.60, af="linear", at=1.60),
    "WOOL":       dict(base=200, T=105, bf="log",   bt=0.20, af="sq",     at=3.20),
    "FERTILIZER": dict(base=100, T=200, bf="linear",bt=0.40, af="linear", at=0.40),
}

F = {
    "linear": lambda x: x,
    "sq":     lambda x: x * x,
    "sqrt":   lambda x: math.sqrt(x),
    "log":    lambda x: math.log(1.0 + x),
    "log10":  lambda x: math.log10(1.0 + x),
}


def price_at(item, inv):
    """Quoted unit price for `item` at market inventory `inv`."""
    p = MARKET_PARAMS[item]
    d = abs(inv - I0)
    if inv < I0:
        f, tgt = F[p["bf"]], p["bt"]
        sign = 1.0
    else:
        f, tgt = F[p["af"]], p["at"]
        sign = -1.0
    amp = tgt * p["base"] / f(p["T"])
    return max(1.0, round(p["base"] + sign * amp * f(d)))


def sell_revenue(item, n, inv=I0):
    """Exact coins from dumping n units in one go, starting at market inventory `inv`."""
    total = 0.0
    for _ in range(int(n)):
        px = price_at(item, inv)
        total += px
        if px > 1:            # at the $1 floor units are bought but not added to inventory
            inv += 1
    return total, inv


# sanity check against the published table
for item in MARKET_PARAMS:
    p = MARKET_PARAMS[item]
    T = p["T"]
    print(f"{item:11} P(I0-T)=${price_at(item, I0-T):>5.0f}   "
          f"P(I0)=${price_at(item, I0):>5.0f}   "
          f"P(I0+T)=${price_at(item, I0+T):>5.0f}   "
          f"P(I0+2T)=${price_at(item, I0+2*T):>5.0f}")

import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

qty = np.arange(0, 601)
for item in ["WHEAT", "CARROT", "TOMATO", "EGG"]:
    axes[0].plot(qty, [price_at(item, I0 + q) for q in qty], label=item, lw=2)
for item in ["STRAWBERRY", "MELON", "MILK", "WOOL"]:
    axes[1].plot(qty, [price_at(item, I0 + q) for q in qty], label=item, lw=2)

for ax, title in zip(axes, ["Staples — shallow glut curves", "Premium — cliff-edge glut curves"]):
    ax.set_xlabel("cumulative units sold into the market")
    ax.set_ylabel("unit price ($)")
    ax.set_title(title)
    ax.grid(alpha=.3)
    ax.legend()
plt.tight_layout()
plt.show()

rows = []
for item in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]:
    r = {"item": item, "base": MARKET_PARAMS[item]["base"]}
    for n in (25, 50, 100, 200, 400, 800, 1600):
        rev, _ = sell_revenue(item, n)
        r[f"avg@{n}"] = round(rev / n, 1)
    # market depth: units until the price halves, and until it hits the floor
    inv, half, floor_at = I0, None, None
    b = MARKET_PARAMS[item]["base"]
    for k in range(1, 4001):
        px = price_at(item, inv)
        if half is None and px <= b / 2:
            half = k
        if px <= 1:
            floor_at = k
            break
        inv += 1
    r["half_price_at"] = half
    r["floor_at"] = floor_at if floor_at else ">4000"
    rows.append(r)

depth = pd.DataFrame(rows)
depth

def buy_cost(item, n, inv=I0):
    """Exact coins to buy n units, starting at market inventory `inv`."""
    total = 0.0
    for _ in range(int(n)):
        inv -= 1
        total += price_at(item, inv)
    return total, inv


for n in (50, 100, 200, 400, 800, 1600):
    c, inv = buy_cost("WHEAT", n)
    print(f"buy {n:>4} wheat: total ${c:>8,.0f}   avg ${c/n:>5.1f}   final unit price ${price_at('WHEAT', inv):>4.0f}")

SHOP_DEMAND = {
    "BAKERY":        {"EGG": 1, "WHEAT": 1},
    "PIZZA_SHOP":    {"MILK": 1, "TOMATO": 1, "WHEAT": 1},
    "BRUNCH_SPOT":   {"EGG": 1, "WHEAT": 1, "STRAWBERRY": 1},
    "YARN_STORE":    {"WOOL": 2},
    "ICE_CREAM_SHOP":{"STRAWBERRY": 1, "MILK": 1, "WHEAT": 1},
    "PET_CAFE":      {"CARROT": 2},
    "SMOOTHIE_SHOP": {"STRAWBERRY": 1, "MILK": 1},
    "FARMERS_MARKET":{"WHEAT": 1, "CARROT": 1, "TOMATO": 1, "STRAWBERRY": 1},
}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]

# how many shops demand each product, if ALL shops were unlocked (late game)
rows = []
for prod in PRODUCTS:
    per_shop = sum(v.get(prod, 0) for v in SHOP_DEMAND.values())
    rows.append(dict(
        product=prod,
        shops_demanding=sum(1 for v in SHOP_DEMAND.values() if prod in v),
        shop_units_per_day_all_unlocked=per_shop * 6,       # 6 ticks/day
        town_centre_per_day_d0=2, town_centre_per_day_d10=4, town_centre_per_day_d20=8,
        max_daily_drain=per_shop * 6 + 8,
    ))
town = pd.DataFrame(rows).sort_values("max_daily_drain", ascending=False)
town

def fib_costs(n):
    a, b, out = 1, 1, []
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out

costs = fib_costs(22)
rows, tot = [], 0
for i, c in enumerate(costs, start=1):
    tot += c
    rows.append(dict(hands=i, cost_of_this_hand=c, total_cost_today=tot,
                     extra_actions=i * 24, cost_per_action=round(tot / (i * 24), 2),
                     season_cost_if_daily=tot * 28))
pd.DataFrame(rows)

rows = []
for hands in (0, 3, 5, 8, 10, 12, 14, 16, 18):
    turns = 24 * (1 + hands)
    cost = sum(fib_costs(hands))
    rows.append(dict(
        hands=hands, unit_turns_per_day=turns, hire_cost_per_day=cost,
        animals_serviceable=turns // 6,
        crop_tiles_serviceable=turns // 2,     # ~1 water + amortised plant/harvest/walk
    ))
pd.DataFrame(rows)

%%writefile main.py
"""Kaggriculture — a simple, complete baseline agent.

A complete, readable agent: hires hands, keeps every unit on a nearest-task
schedule, plants/waters/harvests carrots and wheat, walks produce back to the
shed, drip-sells, and liquidates at the end. Beats `starter` ~20x.

Deliberately simple: no market modelling, no livestock. The structure is the
part to keep; the decisions inside it are the part to improve.
"""

CROP = {"WHEAT": dict(seed=10, maxday=4, maxy=6),
        "CARROT": dict(seed=20, maxday=3, maxy=4)}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]
DIRS = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
LAST_DAY = 29


def bfs(tiles, start, n):
    """Distances over unlocked tiles. Needed because the owned quadrants can
    form an L-shape, where greedy Manhattan stepping wedges a unit forever."""
    dist = {start: 0}
    q, head = [start], 0
    while head < len(q):
        x, y = q[head]
        head += 1
        d = dist[(x, y)] + 1
        for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < n and (nx, ny) not in dist and tiles[ny][nx] != "LOCKED":
                dist[(nx, ny)] = d
                q.append((nx, ny))
    return dist


def move_towards(tiles, start, goal, n):
    if start == goal:
        return None
    back = bfs(tiles, goal, n)
    best = None
    for op, (dx, dy) in DIRS.items():
        nx, ny = start[0] + dx, start[1] + dy
        if not (0 <= nx < n and 0 <= ny < n) or tiles[ny][nx] == "LOCKED":
            continue
        d = back.get((nx, ny))
        if d is not None and (best is None or d < best[0]):
            best = (d, op)
    return best[1] if best else None


def agent(obs):
    p = obs["player"]
    me = obs["farms"][p]
    priv = obs["private"]
    tiles = me["tiles"]
    n = len(tiles)
    day, hour = obs["day"], obs["hour"]
    money = me["money"]
    shed = priv["shed"]
    seeds = dict(priv["seeds"])
    invs = priv["inventories"]

    h = n // 2
    home = [t for t in [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]
            if tiles[t[1]][t[0]] != "LOCKED"]
    home_set = set(home)
    units = [tuple(me["farmer"])] + [tuple(u) for u in me["hands"]]
    market = []

    # ---- market. Hour 0 is HIRE-only so the 10-order cap never eats a SELL.
    if hour == 0 and day < LAST_DAY:
        for _ in range(6):
            market.append(["HIRE"])
    else:
        if len(me["unlocked_quadrants"]) < 4 and day < 20 and money > 5000:
            market.append(["BUY_LAND"])
        empt = sum(1 for r in tiles for t in r if t is None)
        for crop, until in (("CARROT", 26), ("WHEAT", 25)):
            want = min(empt, 30) - seeds.get(crop, 0)
            if want > 0 and day <= until and money > CROP[crop]["seed"] * want + 400:
                market.append(["BUY_SEED", crop, want])
                break
        for item in PRODUCTS:
            if shed.get(item, 0) > 0:
                market.append(["SELL", item, shed[item]])
    market = market[:10]

    # ---- tasks: (priority, position, op, needs_a_seed_of)
    tasks = []
    for y in range(n):
        for x in range(n):
            t = tiles[y][x]
            if t == "LOCKED":
                continue
            if t is None:
                for crop, until in (("CARROT", 26), ("WHEAT", 25)):
                    if day <= until and seeds.get(crop, 0) > 0:
                        tasks.append((3, (x, y), ["PLANT", crop], crop))
                        break
            elif t["kind"] == "WEED":
                tasks.append((4, (x, y), ["DIG"], None))
            elif t["kind"] == "PLANT":
                c = CROP.get(t["crop"])
                if c is None:
                    continue
                age = day - t["planted_day"]
                # Water BEFORE harvesting: the last day in the bonus window is
                # still worth a whole extra unit.
                if not t["watered_today"] and age <= c["maxday"] and day < LAST_DAY:
                    tasks.append((1, (x, y), ["WATER"], None))
                elif age >= c["maxday"] and t["yield_units"] > 0:
                    tasks.append((2, (x, y), ["HARVEST"], None))
    tasks.sort(key=lambda t: t[0])

    # ---- assign each unit its cheapest useful task
    ops, taken = [], set()
    seed_left = dict(seeds)
    for idx, pos in enumerate(units):
        inv = invs[idx] if idx < len(invs) else {}
        carried = sum(v for k, v in inv.items() if k in PRODUCTS)
        # a hand can spawn on a LOCKED centre tile; there it can only move
        if tiles[pos[1]][pos[0]] == "LOCKED":
            goal = min(home_set, key=lambda q: abs(q[0] - pos[0]) + abs(q[1] - pos[1]))
            mv = move_towards(tiles, pos, goal, n)
            ops.append([mv] if mv else ["PASS"])
            continue

        op = None
        if pos in home_set and carried > 0:
            op = ["DROP"]
        elif carried >= 8 or (hour >= 21 and carried > 0):
            goal = min(home_set, key=lambda q: abs(q[0] - pos[0]) + abs(q[1] - pos[1]))
            mv = move_towards(tiles, pos, goal, n)
            op = [mv] if mv else None

        if op is None:
            d = bfs(tiles, pos, n)
            best = None
            for i, (prio, tp, top, need) in enumerate(tasks):
                if i in taken or tp not in d:
                    continue
                if need and seed_left.get(need, 0) <= 0:
                    continue
                s = d[tp] + prio * 3
                if best is None or s < best[0]:
                    best = (s, i, tp, top, need)
            if best is not None:
                _, i, tp, top, need = best
                taken.add(i)
                if pos == tp:
                    op = top
                    if need:                       # reserve it: over-requesting
                        seed_left[need] -= 1       # drops ALL plants of that crop
                else:
                    mv = move_towards(tiles, pos, tp, n)
                    op = [mv] if mv else ["PASS"]
        ops.append(op or ["PASS"])

    return {"farmer": ops[0], "hands": ops[1:len(units)], "market": market}

# The framework calls the LAST callable defined in this file, not the one named
# `agent`. Never add a helper below this line.

from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 7})
env.run(["main.py", "starter"])
r = [s["reward"] for s in env.steps[-1]]
print(f"baseline agent: ${r[0]:,.0f}   starter: ${r[1]:,.0f}")
# typically lands around $9-10k against starter's ~$3.3k

import statistics
from kaggle_environments import make


def duel(a, b, games=8, steps=720, verbose=True):
    """Play `games` episodes of a vs b, alternating seats. Returns a summary dict."""
    wins = draws = losses = 0
    my_banks, opp_banks = [], []
    for g in range(games):
        swap = g % 2 == 1
        pair = [b, a] if swap else [a, b]
        env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": 1000 + g})
        env.run(pair)
        rw = [s["reward"] or 0 for s in env.steps[-1]]
        mine, theirs = (rw[1], rw[0]) if swap else (rw[0], rw[1])
        my_banks.append(mine)
        opp_banks.append(theirs)
        if mine > theirs:
            wins += 1
        elif mine == theirs:
            draws += 1
        else:
            losses += 1
        if verbose:
            print(f"  game {g} (seat {int(swap)}): ${mine:>10,.0f}  vs  ${theirs:>10,.0f}"
                  f"   {'WIN ' if mine > theirs else ('TIE ' if mine == theirs else 'LOSS')}")
    return dict(
        games=games, wins=wins, draws=draws, losses=losses,
        winrate=round(wins / games, 3),
        my_mean=round(statistics.mean(my_banks)),
        my_median=round(statistics.median(my_banks)),
        my_min=round(min(my_banks)), my_max=round(max(my_banks)),
        opp_mean=round(statistics.mean(opp_banks)),
    )


res = duel("main.py", "starter", games=4)
print()
print(res)

env = make("kaggriculture", configuration={"episodeSteps": 240}, debug=True)
env.run(["main.py", "pass"])
for i, s in enumerate(env.steps[-1]):
    print(i, s["status"])
# with debug=True, exceptions from your agent are printed above this line

import collections
from kaggle_environments import make


def trace_episode(agent_file="main.py", opponent="starter", steps=720):
    env = make("kaggriculture", configuration={"episodeSteps": steps})
    env.run([agent_file, opponent])
    hist = []
    for st in env.steps:
        o = st[0]["observation"]
        if "farms" not in o:
            continue
        hist.append(dict(step=o["step"], day=o["day"],
                         money=o["farms"][0]["money"],
                         opp=o["farms"][1]["money"],
                         **{f"px_{k}": v for k, v in o["market"]["prices"].items()}))
    return pd.DataFrame(hist)


tr = trace_episode(steps=720)
daily = tr.groupby("day").last()
ax = daily[["money", "opp"]].plot(figsize=(11, 4), lw=2, title="Bank balance by day")
ax.set_ylabel("$"); ax.grid(alpha=.3); plt.show()

px_cols = [c for c in daily.columns if c.startswith("px_")]
ax = daily[px_cols].plot(figsize=(11, 4), title="Market prices by day")
ax.set_ylabel("$"); ax.grid(alpha=.3); plt.show()

import importlib.util, sys, time
from kaggle_environments import make


def preflight(path="main.py"):
    ok = True

    # 1. imports cleanly and exposes `agent`
    spec = importlib.util.spec_from_file_location("subm", path)
    mod = importlib.util.module_from_spec(spec)
    t0 = time.time()
    spec.loader.exec_module(mod)
    print(f"[ok] imports in {time.time()-t0:.2f}s")
    if not callable(getattr(mod, "agent", None)):
        print("[FAIL] no module-level callable named `agent`"); ok = False

    # 2. self-play validation episode (this is what Kaggle runs)
    t0 = time.time()
    env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
    env.run([path, path])
    dur = time.time() - t0
    st = [s["status"] for s in env.steps[-1]]
    print(f"[{'ok' if all(s == 'DONE' for s in st) else 'FAIL'}] self-play status {st}  ({dur:.1f}s)")
    if not all(s == "DONE" for s in st):
        ok = False

    # 3. per-turn latency
    print(f"[info] ~{dur/720*1000:.1f} ms per turn per agent")

    # 4. beats the baselines
    for opp in ("pass", "random", "starter"):
        env = make("kaggriculture", configuration={"episodeSteps": 720})
        env.run([path, opp])
        r = [s["reward"] or 0 for s in env.steps[-1]]
        verdict = "ok" if r[0] > r[1] else "FAIL"
        if r[0] <= r[1]:
            ok = False
        print(f"[{verdict}] vs {opp:8} ${r[0]:>12,.0f}  vs  ${r[1]:>12,.0f}")

    print("\nPREFLIGHT", "PASSED ✅" if ok else "FAILED ❌")
    return ok


preflight("main.py")