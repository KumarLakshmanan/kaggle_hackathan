# ============================================================
# CELL 3 — Environment Setup
# ============================================================
import sys, subprocess, time
t0 = time.time()

try:
    import kaggle_environments
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip",
                           "install", "-q", "-U", "kaggle-environments"])
    import kaggle_environments

from kaggle_environments import make

# Tiny 5-step probe, under 1 second
_probe = make("kaggriculture", configuration={"episodeSteps": 5}, debug=False)

print(f"✅ kaggle-environments {kaggle_environments.__version__} ready")
print(f"   Agents: {list(_probe.agents.keys())}")
print(f"   Setup took: {time.time()-t0:.2f}s")

# ============================================================
# CELL 3 — Environment Setup
# ============================================================
import sys, subprocess, time
t0 = time.time()

try:
    import kaggle_environments
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip",
                           "install", "-q", "-U", "kaggle-environments"])
    import kaggle_environments

from kaggle_environments import make

# Tiny 5-step probe, under 1 second
_probe = make("kaggriculture", configuration={"episodeSteps": 5}, debug=False)

print(f"✅ kaggle-environments {kaggle_environments.__version__} ready")
print(f"   Agents: {list(_probe.agents.keys())}")
print(f"   Setup took: {time.time()-t0:.2f}s")

# ============================================================
# CELL 4 — Timeout Guard
# ============================================================
import signal
from contextlib import contextmanager

class CellTimeout(Exception):
    pass

@contextmanager
def time_limit(seconds: int = 30):
    """Abort the wrapped block if it exceeds `seconds`."""
    def _handler(signum, frame):
        raise CellTimeout(f"Exceeded {seconds}s — aborted safely.")
    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)

# Fast smoke test
try:
    with time_limit(1):
        _ = sum(range(1000))
    print("✅ Timeout guard works.")
except CellTimeout as e:
    print("❌ Unexpected timeout:", e)

# ============================================================
# CELL 6 — LAYER 1: ROI Tables
# ============================================================
CROPS = {
    "WHEAT":      {"seed": 10,  "first": 2,  "max_d": 4,  "max_y": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first": 2,  "max_d": 3,  "max_y": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first": 8,  "max_d": 8,  "max_y": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_d": 10, "max_y": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first": 10, "max_d": 10, "max_y": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "first": 4, "interval": 1, "product": "EGG"},
    "COW":   {"cost": 400, "first": 8, "interval": 2, "product": "MILK"},
    "SHEEP": {"cost": 500, "first": 6, "interval": 3, "product": "WOOL"},
}

def crop_roi(crop, price, days_left):
    c = CROPS[crop]
    ypd = (c["max_y"] / max(1, c["max_d"] + 4)) if c["ongoing"] else (c["max_y"] / max(1, c["max_d"]))
    return (ypd * price) / max(1, c["seed"])

def animal_roi(animal, price, days_left):
    a = ANIMALS[animal]
    if days_left < a["first"] + 2:
        return 0.0
    return ((1.0 / a["interval"]) * price) / max(1, a["cost"] / 10)

# Smoke tests
assert crop_roi("WHEAT", 25, 20) > 0
assert animal_roi("GOOSE", 50, 20) > 0
assert animal_roi("GOOSE", 50, 2) == 0.0
print("✅ ROI tables defined and tested.")

# ============================================================
# CELL 7 — LAYER 2: Tile Scanner
# ============================================================
def scan_tiles(farm, day):
    """Return info-dicts for every NON-empty, NON-locked tile."""
    rows = []
    for y in range(len(farm["tiles"])):
        for x in range(len(farm["tiles"])):
            t = farm["tiles"][y][x]
            if t is None or t == "LOCKED":
                continue
            info = {"x": x, "y": y, "tile": t}
            if isinstance(t, dict):
                kind = t.get("kind")
                if kind == "PLANT":
                    info.update({
                        "type": "plant",
                        "crop": t["crop"],
                        "needs_water": not t.get("watered_today", False),
                        "harvestable": t.get("yield_units", 0) > 0,
                        "dying": t.get("consecutive_unwatered", 0) >= 1,
                    })
                elif kind in ("COOP", "PASTURE"):
                    if "animal" in t:
                        info.update({
                            "type": "animal",
                            "animal": t["animal"],
                            "needs_feed": not t.get("fed_today", False),
                            "fertilizer": t.get("fertilizer_available", False),
                            "harvestable": t.get("yield_units", 0) > 0,
                        })
                    else:
                        info.update({"type": "structure"})
                elif kind == "WEED":
                    info.update({"type": "weed"})
            rows.append(info)
    return rows

# Correct smoke tests (empty tiles are SKIPPED)
assert scan_tiles({"tiles": [[None]*5 for _ in range(5)]}, 0) == []
assert scan_tiles({"tiles": [["LOCKED"]*5 for _ in range(5)]}, 0) == []

mixed = {"tiles": [[None]*3 for _ in range(3)]}
mixed["tiles"][1][1] = {"kind": "WEED"}
mixed["tiles"][2][2] = {"kind": "PLANT", "crop": "WHEAT",
                         "watered_today": False, "consecutive_unwatered": 0,
                         "yield_units": 0}
out = scan_tiles(mixed, 0)
assert len(out) == 2 and {r["type"] for r in out} == {"weed", "plant"}
print("✅ scan_tiles passes all 3 smoke tests.")

# ============================================================
# CELL 8 — LAYER 3: Worker-Tile Assignment
# ============================================================
def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def urgent_priority(t, day):
    if t.get("type") == "plant":
        if t.get("dying"):       return 100
        if t.get("harvestable"): return 90
        if t.get("needs_water"): return 70
    if t.get("type") == "animal":
        if t.get("needs_feed"):  return 95
        if t.get("harvestable"): return 80
        if t.get("fertilizer"):  return 40
    if t.get("type") == "weed":
        return 30
    return 0

def assign_workers_to_tiles(workers, tiles, day):
    tiles = [t for t in tiles if urgent_priority(t, day) > 0]
    tiles.sort(key=lambda t: -urgent_priority(t, day))

    assignment, used = {}, set()
    for wi, wpos in enumerate(workers):
        best, best_score = None, -1
        for ti, t in enumerate(tiles):
            if ti in used: continue
            s = urgent_priority(t, day) / (1 + manhattan(wpos, (t["x"], t["y"])))
            if s > best_score:
                best_score, best = s, ti
        if best is not None:
            assignment[wi] = tiles[best]
            used.add(best)
        else:
            assignment[wi] = None
    return assignment

# Smoke tests
assert assign_workers_to_tiles([], [], day=3) == {}
assert assign_workers_to_tiles([(4,4)], [], day=3) == {0: None}
tile = {"x":4, "y":4, "type":"plant", "needs_water":True}
assert assign_workers_to_tiles([(4,4)], [tile], day=3)[0] is tile
print("✅ Worker planner passes 3 smoke tests.")

# ============================================================
# CELL 9 — Movement Helper
# ============================================================
def step_toward(pos, target):
    px, py = pos
    tx, ty = target
    if (px, py) == (tx, ty): return None
    if px < tx: return "EAST"
    if px > tx: return "WEST"
    if py < ty: return "SOUTH"
    if py > ty: return "NORTH"
    return None

assert step_toward((4,4),(7,4)) == "EAST"
assert step_toward((7,4),(4,4)) == "WEST"
assert step_toward((4,4),(4,7)) == "SOUTH"
assert step_toward((4,7),(4,4)) == "NORTH"
assert step_toward((4,4),(4,4)) is None
print("✅ Movement helper passes 5 smoke tests.")

# ============================================================
# CELL 10 — LAYER 4: Smart Seller
# ============================================================
SELL_LIMITS = {
    "WHEAT": 15, "CARROT": 10, "TOMATO": 6,
    "STRAWBERRY": 4, "MELON": 2,
    "EGG": 10, "MILK": 4, "WOOL": 3, "FERTILIZER": 10,
}

def plan_sales(shed, market, day):
    orders = []
    prices = market.get("prices", {}) or {}
    for item, qty in (shed or {}).items():
        if qty <= 0:
            continue
        price = prices.get(item, 0)
        if price <= 1:
            continue
        cap = SELL_LIMITS.get(item, qty)
        if day >= 27:
            orders.append(["SELL", item, qty])
        else:
            orders.append(["SELL", item, min(qty, cap)])
    return orders

# Smoke tests
r1 = plan_sales({"WHEAT": 40, "MELON": 5},
                {"prices": {"WHEAT": 25, "MELON": 250}}, day=5)
assert ["SELL", "WHEAT", 15] in r1
assert ["SELL", "MELON", 2] in r1

r2 = plan_sales({"WHEAT": 40}, {"prices": {"WHEAT": 25}}, day=28)
assert r2 == [["SELL", "WHEAT", 40]]

r3 = plan_sales({"WHEAT": 5}, {"prices": {"WHEAT": 1}}, day=5)
assert r3 == []
print("✅ Seller passes 3 smoke tests.")

# ============================================================
# CELL 11 — Target Picker (safe against missing prices)
# ============================================================
from collections import Counter

SHOP_DEMAND = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

def pick_best_target(shops, prices, cash, day):
    demand = Counter()
    for s in shops or []:
        for p in SHOP_DEMAND.get(s, []):
            demand[p] += 1

    days_left = 30 - day
    best, best_score = None, -1.0

    for crop, c in CROPS.items():
        if c["seed"] > cash: continue
        price = (prices or {}).get(crop, 0)
        if price <= 0: continue
        s = crop_roi(crop, price, days_left) * (1 + 0.25 * demand.get(crop, 0))
        if s > best_score:
            best, best_score = crop, s

    for animal, a in ANIMALS.items():
        if a["cost"] > cash * 3: continue
        if days_left < a["first"] + 4: continue
        prod = a.get("product")
        price = (prices or {}).get(prod, 0)
        if price <= 0: continue
        s = animal_roi(animal, price, days_left) * (1 + 0.25 * demand.get(prod, 0))
        if s > best_score:
            best, best_score = animal, s

    return best if best is not None else "WHEAT"

# Smoke tests
P_full = {"WHEAT":25,"CARROT":35,"TOMATO":60,"STRAWBERRY":120,
          "MELON":250,"EGG":50,"MILK":160,"WOOL":200}
assert pick_best_target([], P_full, 0, day=5) == "WHEAT"
assert pick_best_target([], P_full, 5000, day=5) in list(CROPS) + list(ANIMALS)
assert pick_best_target([], {"WHEAT": 25}, 5000, day=5) == "WHEAT"
assert pick_best_target([], {}, 5000, day=5) == "WHEAT"
assert pick_best_target([], P_full, 5000, day=29) in CROPS
print("✅ Target picker is KeyError-proof (5 smoke tests).")

# ============================================================
# CELL 12 — THE AGRIMIND AGENT (bulletproof)
# ============================================================
def _safe_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

def agrimind(obs):
    """Bulletproof agent — never crashes on partial obs."""
    obs  = obs or {}
    me   = _safe_int(obs.get("player", 0))
    day  = _safe_int(obs.get("day", 0))

    farms = obs.get("farms") or []
    farm  = farms[me] if me < len(farms) else {}
    priv  = obs.get("private") or {}
    mkt   = obs.get("market")  or {}
    town  = obs.get("town")    or {}

    prices = mkt.get("prices", {}) or {}
    cash   = farm.get("money", 0) or 0
    shops  = town.get("unlocked_shops", []) or []

    target = pick_best_target(shops, prices, cash, day)

    # Layer 4 — sell
    shed = priv.get("shed", {}) or {}
    market_orders = plan_sales(shed, {"prices": prices}, day)

    # Layer 1 — buy
    seeds = priv.get("seeds", {}) or {}
    if target in CROPS:
        if seeds.get(target, 0) < 3 and cash >= CROPS[target]["seed"] * 3:
            market_orders.append(["BUY_SEED", target, 3])
    elif target in ANIMALS:
        if cash > ANIMALS[target]["cost"] * 2:
            market_orders.append(["BUY_ANIMAL", target, 1])

    # Layer 2 — scan
    tiles = scan_tiles(farm, day) if farm else []

    # Layer 3 — assign
    farmer_pos = tuple(farm.get("farmer", [4, 4]))
    hands_pos  = [tuple(h) for h in (farm.get("hands", []) or [])]
    workers    = [farmer_pos] + hands_pos
    assignment = assign_workers_to_tiles(workers, tiles, day)

    def action_for(wi):
        t = assignment.get(wi)
        if t is None:
            return ["PASS"]
        pos = workers[wi]
        if tuple(pos) != (t["x"], t["y"]):
            mv = step_toward(pos, (t["x"], t["y"]))
            return [mv] if mv else ["PASS"]
        if t["type"] == "plant":
            if t.get("dying") or t.get("needs_water"):
                return ["WATER"]
            if t.get("harvestable"):
                return ["HARVEST"]
        if t["type"] == "animal":
            if t.get("needs_feed"):
                return ["FEED"]
            if t.get("harvestable"):
                return ["HARVEST"]
            if t.get("fertilizer"):
                return ["COLLECT_FERTILIZER"]
        if t["type"] == "weed":
            return ["DIG"]
        if t["tile"] is None and seeds.get(target, 0) > 0:
            return ["PLANT", target]
        return ["PASS"]

    return {
        "farmer": action_for(0),
        "hands":  [action_for(i + 1) for i in range(len(hands_pos))],
        "market": market_orders[:10],
    }

agent = agrimind   # Kaggle submission entry point


# ============================================================
# 6 SMOKE TESTS — obs of every shape must NOT crash
# ============================================================
P_full = {"WHEAT":25,"CARROT":35,"TOMATO":60,"STRAWBERRY":120,
          "MELON":250,"EGG":50,"MILK":160,"WOOL":200}

fake_full = {
    "player": 0, "day": 0, "hour": 0,
    "farms": [
        {"money": 3000, "tiles": [[None]*10 for _ in range(10)],
         "farmer": [4,4], "hands": [],
         "unlocked_quadrants": ["NW"], "hires_today": 0},
        {"money": 3000, "tiles": [[None]*10 for _ in range(10)],
         "farmer": [4,4], "hands": [],
         "unlocked_quadrants": ["NW"], "hires_today": 0},
    ],
    "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
    "market": {"inventory": {"WHEAT":10000,"CARROT":10000,"MELON":10000},
               "prices":    P_full},
    "town": {"unlocked_shops": []},
}
assert isinstance(agrimind(fake_full), dict)

p = dict(fake_full); p["market"] = {"inventory":{"WHEAT":10000}, "prices":{"WHEAT":25}}
assert isinstance(agrimind(p), dict)

e = dict(fake_full); e["market"] = {"inventory":{}, "prices":{}}
assert isinstance(agrimind(e), dict)

n = dict(fake_full); del n["town"]
assert isinstance(agrimind(n), dict)

m = dict(fake_full); del m["private"]
assert isinstance(agrimind(m), dict)

assert isinstance(agrimind({}), dict)

print("✅ Agent defined. All 6 obs-shape smoke tests pass.")
print("   Example output:", agrimind(fake_full)["farmer"])

# ============================================================
# CELL 13 — Sanity: agent returns valid action structure
# ============================================================
# Runs 30 synthetic turns without touching the game engine.
# Finishes in milliseconds.

def synth_obs(step, money=3000):
    return {
        "player": 0, "day": step // 24, "hour": step % 24,
        "farms": [
            {"money": money, "tiles": [[None]*10 for _ in range(10)],
             "farmer": [4,4], "hands": [],
             "unlocked_quadrants": ["NW"], "hires_today": 0},
            {"money": money, "tiles": [[None]*10 for _ in range(10)],
             "farmer": [4,4], "hands": [],
             "unlocked_quadrants": ["NW"], "hires_today": 0},
        ],
        "private": {"shed": {}, "seeds": {"WHEAT": 3}, "inventories": [{}]},
        "market": {"inventory": {"WHEAT":10000},
                   "prices": {"WHEAT":25, "CARROT":35, "TOMATO":60,
                              "STRAWBERRY":120, "MELON":250,
                              "EGG":50, "MILK":160, "WOOL":200}},
        "town": {"unlocked_shops": []},
    }

for step in range(30):
    action = agrimind(synth_obs(step))
    assert "farmer" in action and isinstance(action["farmer"], list)
    assert "hands" in action and isinstance(action["hands"], list)
    assert "market" in action and isinstance(action["market"], list)

print("✅ 30 synthetic turns produced valid actions. No engine needed.")

# ============================================================
# CELL 15 — Optional: One 150-turn match vs starter
# ============================================================
# Skip this cell if you want the fastest possible notebook.

import time

def run_match(opponent="starter", steps=150, seed=101, timeout=30):
    try:
        with time_limit(timeout):
            t0 = time.time()
            env = make("kaggriculture",
                       configuration={"episodeSteps": steps, "seed": seed})
            env.run([agrimind, opponent])
            final = env.steps[-1]
            a, b = final[0]["reward"], final[1]["reward"]
            tag = "WIN " if a > b else ("TIE " if a == b else "LOSS")
            print(f"AgriMind ${a:>9,.0f} | {opponent} ${b:>9,.0f} | {tag} | {time.time()-t0:.1f}s")
            return a, b
    except CellTimeout as e:
        print(f"⏱️ Match aborted: {e}")
        return None, None

run_match("starter")

# ============================================================
# CELL 16 — Optional: Quick benchmark vs starter / random / pass
# ============================================================
def bench_one(opponent):
    a, b = run_match(opponent, steps=150, seed=1, timeout=25)
    return None if a is None else (a, b)

print("Quick benchmark (150-turn games):")
for opp in ["starter", "random", "pass"]:
    bench_one(opp)

# ============================================================
# CELL 17 — Optional: Full 720-turn game → JSON replay
# ============================================================
# Skip this cell if you want the notebook to end in ~7s.
import json, time

def save_full_replay(opponent="starter", seed=42, timeout=45):
    try:
        with time_limit(timeout):
            t0 = time.time()
            env = make("kaggriculture",
                       configuration={"episodeSteps": 720, "seed": seed})
            env.run([agrimind, opponent])
            with open("agrimind_replay.json", "w") as f:
                json.dump(env.toJSON(), f)
            final = env.steps[-1]
            print(f"Full game done in {time.time()-t0:.1f}s")
            print(f"  AgriMind: ${final[0]['reward']:,.0f}")
            print(f"  {opponent}: ${final[1]['reward']:,.0f}")
            print("  Replay saved → agrimind_replay.json")
    except CellTimeout as e:
        print(f"⏱️ Skipped: {e}")

# Uncomment if you want the full replay:
# save_full_replay()
print("(Optional cell — uncomment save_full_replay() to run.)")

# ============================================================
# CELL 18 — Build submission.tar.gz  (offline, no game needed)
# ============================================================
# Writes a self-contained main.py (agent only, no env import),
# then packs it deterministically into submission.tar.gz.
# Runs in ~1 second.
# ============================================================
import io, gzip, tarfile, hashlib
from pathlib import Path

MAIN_PY = r'''"""
AgriMind — a four-layer adaptive farming agent for Kaggriculture.
Kaggle submission entry point: agent(obs)
"""
from collections import Counter

CROPS = {
    "WHEAT":      {"seed": 10,  "first": 2,  "max_d": 4,  "max_y": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first": 2,  "max_d": 3,  "max_y": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first": 8,  "max_d": 8,  "max_y": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_d": 10, "max_y": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first": 10, "max_d": 10, "max_y": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "first": 4, "interval": 1, "product": "EGG"},
    "COW":   {"cost": 400, "first": 8, "interval": 2, "product": "MILK"},
    "SHEEP": {"cost": 500, "first": 6, "interval": 3, "product": "WOOL"},
}
SHOP_DEMAND = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
SELL_LIMITS = {"WHEAT":15,"CARROT":10,"TOMATO":6,"STRAWBERRY":4,"MELON":2,
               "EGG":10,"MILK":4,"WOOL":3,"FERTILIZER":10}


def _crop_roi(crop, price, days_left):
    c = CROPS[crop]
    ypd = (c["max_y"] / max(1, c["max_d"] + 4)) if c["ongoing"] else (c["max_y"] / max(1, c["max_d"]))
    return (ypd * price) / max(1, c["seed"])


def _animal_roi(animal, price, days_left):
    a = ANIMALS[animal]
    if days_left < a["first"] + 2:
        return 0.0
    return ((1.0 / a["interval"]) * price) / max(1, a["cost"] / 10)


def _scan_tiles(farm, day):
    rows = []
    for y in range(len(farm["tiles"])):
        for x in range(len(farm["tiles"])):
            t = farm["tiles"][y][x]
            if t is None or t == "LOCKED":
                continue
            info = {"x": x, "y": y, "tile": t}
            if isinstance(t, dict):
                kind = t.get("kind")
                if kind == "PLANT":
                    info.update({"type": "plant", "crop": t["crop"],
                                 "needs_water": not t.get("watered_today", False),
                                 "harvestable": t.get("yield_units", 0) > 0,
                                 "dying": t.get("consecutive_unwatered", 0) >= 1})
                elif kind in ("COOP", "PASTURE"):
                    if "animal" in t:
                        info.update({"type": "animal", "animal": t["animal"],
                                     "needs_feed": not t.get("fed_today", False),
                                     "fertilizer": t.get("fertilizer_available", False),
                                     "harvestable": t.get("yield_units", 0) > 0})
                    else:
                        info.update({"type": "structure"})
                elif kind == "WEED":
                    info.update({"type": "weed"})
            rows.append(info)
    return rows


def _manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def _priority(t, day):
    if t.get("type") == "plant":
        if t.get("dying"):       return 100
        if t.get("harvestable"): return 90
        if t.get("needs_water"): return 70
    if t.get("type") == "animal":
        if t.get("needs_feed"):  return 95
        if t.get("harvestable"): return 80
        if t.get("fertilizer"):  return 40
    if t.get("type") == "weed":
        return 30
    return 0


def _assign(workers, tiles, day):
    tiles = [t for t in tiles if _priority(t, day) > 0]
    tiles.sort(key=lambda t: -_priority(t, day))
    assignment, used = {}, set()
    for wi, wpos in enumerate(workers):
        best, best_score = None, -1
        for ti, t in enumerate(tiles):
            if ti in used: continue
            s = _priority(t, day) / (1 + _manhattan(wpos, (t["x"], t["y"])))
            if s > best_score:
                best_score, best = s, ti
        if best is not None:
            assignment[wi] = tiles[best]
            used.add(best)
        else:
            assignment[wi] = None
    return assignment


def _step_toward(pos, target):
    px, py = pos
    tx, ty = target
    if (px, py) == (tx, ty): return None
    if px < tx: return "EAST"
    if px > tx: return "WEST"
    if py < ty: return "SOUTH"
    if py > ty: return "NORTH"
    return None


def _plan_sales(shed, prices, day):
    orders = []
    for item, qty in (shed or {}).items():
        if qty <= 0: continue
        p = prices.get(item, 0)
        if p <= 1: continue
        if day >= 27:
            orders.append(["SELL", item, qty])
        else:
            orders.append(["SELL", item, min(qty, SELL_LIMITS.get(item, qty))])
    return orders


def _pick_target(shops, prices, cash, day):
    d = Counter()
    for s in shops or []:
        for p in SHOP_DEMAND.get(s, []):
            d[p] += 1
    dl = 30 - day
    best, best_score = None, -1.0
    for crop, c in CROPS.items():
        if c["seed"] > cash: continue
        price = (prices or {}).get(crop, 0)
        if price <= 0: continue
        s = _crop_roi(crop, price, dl) * (1 + 0.25 * d.get(crop, 0))
        if s > best_score: best, best_score = crop, s
    for a, x in ANIMALS.items():
        if x["cost"] > cash * 3: continue
        if dl < x["first"] + 4: continue
        price = (prices or {}).get(x.get("product"), 0)
        if price <= 0: continue
        s = _animal_roi(a, price, dl) * (1 + 0.25 * d.get(x.get("product"), 0))
        if s > best_score: best, best_score = a, s
    return best if best is not None else "WHEAT"


def _safe_int(v, default=0):
    try:    return int(v)
    except: return default


def agent(obs):
    obs  = obs or {}
    me   = _safe_int(obs.get("player", 0))
    day  = _safe_int(obs.get("day", 0))
    farms = obs.get("farms") or []
    farm  = farms[me] if me < len(farms) else {}
    priv  = obs.get("private") or {}
    mkt   = obs.get("market")  or {}
    town  = obs.get("town")    or {}

    prices = mkt.get("prices", {}) or {}
    cash   = farm.get("money", 0) or 0
    shops  = town.get("unlocked_shops", []) or []
    target = _pick_target(shops, prices, cash, day)

    shed  = priv.get("shed", {}) or {}
    seeds = priv.get("seeds", {}) or {}
    market_orders = _plan_sales(shed, prices, day)

    if target in CROPS:
        if seeds.get(target, 0) < 3 and cash >= CROPS[target]["seed"] * 3:
            market_orders.append(["BUY_SEED", target, 3])
    elif target in ANIMALS:
        if cash > ANIMALS[target]["cost"] * 2:
            market_orders.append(["BUY_ANIMAL", target, 1])

    tiles = _scan_tiles(farm, day) if farm else []

    farmer_pos = tuple(farm.get("farmer", [4, 4]))
    hands_pos  = [tuple(h) for h in (farm.get("hands", []) or [])]
    workers    = [farmer_pos] + hands_pos
    assignment = _assign(workers, tiles, day)

    def action_for(wi):
        t = assignment.get(wi)
        if t is None: return ["PASS"]
        pos = workers[wi]
        if tuple(pos) != (t["x"], t["y"]):
            mv = _step_toward(pos, (t["x"], t["y"]))
            return [mv] if mv else ["PASS"]
        if t["type"] == "plant":
            if t.get("dying") or t.get("needs_water"): return ["WATER"]
            if t.get("harvestable"):                    return ["HARVEST"]
        if t["type"] == "animal":
            if t.get("needs_feed"):  return ["FEED"]
            if t.get("harvestable"): return ["HARVEST"]
            if t.get("fertilizer"):  return ["COLLECT_FERTILIZER"]
        if t["type"] == "weed":
            return ["DIG"]
        if t["tile"] is None and seeds.get(target, 0) > 0:
            return ["PLANT", target]
        return ["PASS"]

    return {
        "farmer": action_for(0),
        "hands":  [action_for(i + 1) for i in range(len(hands_pos))],
        "market": market_orders[:10],
    }
'''

# --- Write main.py ---
main_path = Path("main.py")
main_path.write_text(MAIN_PY, encoding="utf-8")

# --- Deterministic tar.gz ---
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w", format=tarfile.GNU_FORMAT) as tar:
    info = tarfile.TarInfo("main.py")
    info.size = len(MAIN_PY.encode("utf-8"))
    info.mtime = 0
    info.mode = 0o644
    tar.addfile(info, io.BytesIO(MAIN_PY.encode("utf-8")))

tar_bytes = gzip.compress(buf.getvalue(), mtime=0)
archive = Path("submission.tar.gz")
archive.write_bytes(tar_bytes)

digest = hashlib.sha256(main_path.read_bytes()).hexdigest()[:16]
print(f"✅ main.py written ({len(MAIN_PY):,} bytes, sha256 {digest}...)")
print(f"✅ submission.tar.gz created ({len(tar_bytes):,} bytes)")

# --- Verify round-trip ---
with tarfile.open(archive, "r:gz") as t:
    names = t.getnames()
    inner = t.extractfile("main.py").read()
    assert names == ["main.py"], names
    assert inner.decode("utf-8") == MAIN_PY
print("✅ Archive verified: contains only main.py, content matches.")
print("\n🎉 Ready to submit → upload submission.tar.gz to Kaggle.")