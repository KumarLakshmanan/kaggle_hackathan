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

_probe = make("kaggriculture", configuration={"episodeSteps": 5}, debug=False)

print(f"kaggle-environments {kaggle_environments.__version__} ready")
print(f"Agents: {list(_probe.agents.keys())}")
print(f"Setup: {time.time()-t0:.2f}s")

# ============================================================
# CELL 4 — Timeout Guard
# ============================================================
import signal
from contextlib import contextmanager

class CellTimeout(Exception):
    pass

@contextmanager
def time_limit(seconds=30):
    """Abort the wrapped block if it exceeds `seconds`."""
    def _h(signum, frame):
        raise CellTimeout(f"Exceeded {seconds}s.")
    old = signal.signal(signal.SIGALRM, _h)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)

try:
    with time_limit(1):
        _ = sum(range(500))
    print("Timeout guard installed.")
except CellTimeout:
    print("Guard setup failed.")

# ============================================================
# CELL 5 — Game Constants
# ============================================================
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
SELL_LIMITS = {
    "WHEAT": 15, "CARROT": 10, "TOMATO": 6,
    "STRAWBERRY": 4, "MELON": 2,
    "EGG": 10, "MILK": 4, "WOOL": 3, "FERTILIZER": 10,
}

assert len(CROPS) == 5
assert len(ANIMALS) == 3
assert len(SHOP_DEMAND) == 8
print("Constants defined.")

# ============================================================
# CELL 6 — ROI Functions
# ============================================================
def crop_roi(crop, price, days_left):
    c = CROPS[crop]
    ypd = (c["max_y"] / max(1, c["max_d"] + 4)) if c["ongoing"] \
          else (c["max_y"] / max(1, c["max_d"]))
    return (ypd * price) / max(1, c["seed"])

def animal_roi(animal, price, days_left):
    a = ANIMALS[animal]
    if days_left < a["first"] + 2:
        return 0.0
    return ((1.0 / a["interval"]) * price) / max(1, a["cost"] / 10)

assert crop_roi("WHEAT", 25, 20) > 0
assert animal_roi("GOOSE", 50, 20) > 0
assert animal_roi("GOOSE", 50, 2) == 0.0
print("ROI functions ready.")

# ============================================================
# CELL 7 — Tile Scanner
# ============================================================
def scan_tiles(farm, day):
    """Return info-dicts for every non-empty, non-locked tile."""
    rows = []
    tiles = (farm or {}).get("tiles") or []
    for y in range(len(tiles)):
        for x in range(len(tiles[y])):
            t = tiles[y][x]
            if t is None or t == "LOCKED":
                continue
            info = {"x": x, "y": y, "tile": t}
            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    info.update({
                        "type": "plant",
                        "crop": t.get("crop"),
                        "needs_water": not t.get("watered_today", False),
                        "harvestable": t.get("yield_units", 0) > 0,
                        "dying": t.get("consecutive_unwatered", 0) >= 1,
                    })
                elif k in ("COOP", "PASTURE"):
                    if "animal" in t:
                        info.update({
                            "type": "animal",
                            "animal": t.get("animal"),
                            "needs_feed": not t.get("fed_today", False),
                            "fertilizer": t.get("fertilizer_available", False),
                            "harvestable": t.get("yield_units", 0) > 0,
                        })
                    else:
                        info.update({"type": "structure"})
                elif k == "WEED":
                    info.update({"type": "weed"})
            rows.append(info)
    return rows

assert scan_tiles({"tiles": [[None]*5 for _ in range(5)]}, 0) == []
assert scan_tiles({"tiles": [["LOCKED"]*5 for _ in range(5)]}, 0) == []
assert scan_tiles({}, 0) == []

mixed = {"tiles": [[None]*3 for _ in range(3)]}
mixed["tiles"][1][1] = {"kind": "WEED"}
mixed["tiles"][2][2] = {"kind": "PLANT", "crop": "WHEAT",
                         "watered_today": False,
                         "consecutive_unwatered": 0, "yield_units": 0}
out = scan_tiles(mixed, 0)
assert len(out) == 2
assert {r["type"] for r in out} == {"weed", "plant"}
print("Tile scanner tested (4 cases).")

# ============================================================
# CELL 8 — Worker Assignment
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
    tiles = [t for t in (tiles or []) if urgent_priority(t, day) > 0]
    tiles.sort(key=lambda t: -urgent_priority(t, day))
    assignment, used = {}, set()
    for wi, wpos in enumerate(workers):
        best, best_score = None, -1
        for ti, t in enumerate(tiles):
            if ti in used:
                continue
            s = urgent_priority(t, day) / (1 + manhattan(wpos, (t["x"], t["y"])))
            if s > best_score:
                best_score, best = s, ti
        if best is not None:
            assignment[wi] = tiles[best]
            used.add(best)
        else:
            assignment[wi] = None
    return assignment

assert assign_workers_to_tiles([], [], day=3) == {}
assert assign_workers_to_tiles([(4, 4)], [], day=3) == {0: None}
tile = {"x": 4, "y": 4, "type": "plant", "needs_water": True}
assert assign_workers_to_tiles([(4, 4)], [tile], day=3)[0] is tile
print("Worker assignment tested (3 cases).")

# ============================================================
# CELL 9 — Movement Helper
# ============================================================
def step_toward(pos, target):
    px, py = pos
    tx, ty = target
    if (px, py) == (tx, ty):
        return None
    if px < tx: return "EAST"
    if px > tx: return "WEST"
    if py < ty: return "SOUTH"
    if py > ty: return "NORTH"
    return None

assert step_toward((4, 4), (7, 4)) == "EAST"
assert step_toward((7, 4), (4, 4)) == "WEST"
assert step_toward((4, 4), (4, 7)) == "SOUTH"
assert step_toward((4, 7), (4, 4)) == "NORTH"
assert step_toward((4, 4), (4, 4)) is None
print("Movement helper tested (5 cases).")

# ============================================================
# CELL 10 — Market Seller
# ============================================================
def plan_sales(shed, prices, day):
    orders = []
    for item, qty in (shed or {}).items():
        if qty <= 0:
            continue
        p = (prices or {}).get(item, 0)
        if p <= 1:
            continue
        if day >= 27:
            orders.append(["SELL", item, qty])
        else:
            orders.append(["SELL", item, min(qty, SELL_LIMITS.get(item, qty))])
    return orders

assert ["SELL", "WHEAT", 15] in plan_sales({"WHEAT": 40}, {"WHEAT": 25}, day=5)
assert ["SELL", "MELON", 2] in plan_sales({"MELON": 5}, {"MELON": 250}, day=5)
assert plan_sales({"WHEAT": 40}, {"WHEAT": 25}, day=28) == [["SELL", "WHEAT", 40]]
assert plan_sales({"WHEAT": 5}, {"WHEAT": 1}, day=5) == []
assert plan_sales({}, {}, day=5) == []
print("Market seller tested (5 cases).")

# ============================================================
# CELL 11 — Target Picker
# ============================================================
def pick_best_target(shops, prices, cash, day):
    demand = Counter()
    for s in (shops or []):
        for p in SHOP_DEMAND.get(s, []):
            demand[p] += 1

    dl = 30 - day
    best, best_score = None, -1.0

    for crop, c in CROPS.items():
        if c["seed"] > cash:
            continue
        price = (prices or {}).get(crop, 0)
        if price <= 0:
            continue
        s = crop_roi(crop, price, dl) * (1 + 0.25 * demand.get(crop, 0))
        if s > best_score:
            best, best_score = crop, s

    for a, x in ANIMALS.items():
        if x["cost"] > cash * 3:
            continue
        if dl < x["first"] + 4:
            continue
        prod = x.get("product")
        price = (prices or {}).get(prod, 0)
        if price <= 0:
            continue
        s = animal_roi(a, price, dl) * (1 + 0.25 * demand.get(prod, 0))
        if s > best_score:
            best, best_score = a, s

    return best if best is not None else "WHEAT"

P_full = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
          "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200}

assert pick_best_target([], P_full, 0, day=5) == "WHEAT"
assert pick_best_target([], P_full, 5000, day=5) in list(CROPS) + list(ANIMALS)
assert pick_best_target([], {"WHEAT": 25}, 5000, day=5) == "WHEAT"
assert pick_best_target([], {}, 5000, day=5) == "WHEAT"
assert pick_best_target([], P_full, 5000, day=29) in CROPS
print("Target picker tested (5 cases).")

# ============================================================
# CELL 12 — THE CROPSENSE AGENT
# ============================================================
def _safe_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

def cropsense(obs):
    """Four-pass adaptive farming agent."""
    obs   = obs or {}
    me    = _safe_int(obs.get("player", 0))
    day   = _safe_int(obs.get("day", 0))
    farms = obs.get("farms") or []
    farm  = farms[me] if 0 <= me < len(farms) else {}
    priv  = obs.get("private") or {}
    mkt   = obs.get("market")  or {}
    town  = obs.get("town")    or {}

    prices = mkt.get("prices", {}) or {}
    cash   = farm.get("money", 0) or 0
    shops  = town.get("unlocked_shops", []) or []
    target = pick_best_target(shops, prices, cash, day)

    shed  = priv.get("shed", {}) or {}
    seeds = priv.get("seeds", {}) or {}

    # Pass 4: sell
    market_orders = plan_sales(shed, prices, day)

    # Buy seeds for target if we have room
    if target in CROPS:
        if seeds.get(target, 0) < 3 and cash >= CROPS[target]["seed"] * 3:
            market_orders.append(["BUY_SEED", target, 3])
    elif target in ANIMALS:
        if cash > ANIMALS[target]["cost"] * 2:
            market_orders.append(["BUY_ANIMAL", target, 1])

    # Pass 2: scan
    tiles = scan_tiles(farm, day) if farm else []

    # Pass 3: assign
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

agent = cropsense   # Kaggle entry point


# ============================================================
# 6 defensive smoke tests — every obs shape must not crash
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
    "private": {"shed": {}, "seeds": {"WHEAT": 3}, "inventories": [{}]},
    "market": {"inventory": {"WHEAT": 10000}, "prices": P_full},
    "town": {"unlocked_shops": []},
}

assert isinstance(cropsense(fake_full), dict)
partial = dict(fake_full); partial["market"] = {"inventory": {}, "prices": {"WHEAT": 25}}
assert isinstance(cropsense(partial), dict)
empty = dict(fake_full); empty["market"] = {}
assert isinstance(cropsense(empty), dict)
notown = dict(fake_full); del notown["town"]
assert isinstance(cropsense(notown), dict)
nopriv = dict(fake_full); del nopriv["private"]
assert isinstance(cropsense(nopriv), dict)
assert isinstance(cropsense({}), dict)
print("Agent defined. 6 smoke tests pass.")
print("Example action:", cropsense(fake_full)["farmer"])

# ============================================================
# CELL 13 — 30 Synthetic Turns (no engine)
# ============================================================
def synth_obs(step, money=3000, seeds=None):
    return {
        "player": 0, "day": step // 24, "hour": step % 24,
        "farms": [
            {"money": money, "tiles": [[None]*10 for _ in range(10)],
             "farmer": [4, 4], "hands": [],
             "unlocked_quadrants": ["NW"], "hires_today": 0},
            {"money": money, "tiles": [[None]*10 for _ in range(10)],
             "farmer": [4, 4], "hands": [],
             "unlocked_quadrants": ["NW"], "hires_today": 0},
        ],
        "private": {"shed": {}, "seeds": seeds or {"WHEAT": 3}, "inventories": [{}]},
        "market": {"inventory": {"WHEAT": 10000},
                   "prices": {"WHEAT":25, "CARROT":35, "TOMATO":60,
                              "STRAWBERRY":120, "MELON":250,
                              "EGG":50, "MILK":160, "WOOL":200}},
        "town": {"unlocked_shops": []},
    }

for step in range(30):
    a = cropsense(synth_obs(step))
    assert isinstance(a["farmer"], list)
    assert isinstance(a["hands"], list)
    assert isinstance(a["market"], list)
    assert len(a["market"]) <= 10

print("30 synthetic turns produced valid actions.")

# ============================================================
# CELL 15 — Optional: 150-turn match vs starter
# ============================================================
import time

def run_one_match(opponent="starter", steps=150, seed=101, timeout=20):
    try:
        with time_limit(timeout):
            t0 = time.time()
            env = make("kaggriculture",
                       configuration={"episodeSteps": steps, "seed": seed})
            env.run([cropsense, opponent])
            final = env.steps[-1]
            a, b = final[0]["reward"], final[1]["reward"]
            tag = "WIN" if a > b else ("TIE" if a == b else "LOSS")
            print(f"CropSense ${a:>9,.0f} | {opponent} ${b:>9,.0f} | "
                  f"{tag} | {time.time()-t0:.1f}s")
            return a, b
    except CellTimeout as e:
        print(f"Match aborted: {e}")
        return None, None

run_one_match("starter")

# ============================================================
# CELL 16 — Optional: 100-turn benchmark
# ============================================================
import time

def quick_bench(opponent, steps=100, timeout=15):
    try:
        with time_limit(timeout):
            t0 = time.time()
            env = make("kaggriculture",
                       configuration={"episodeSteps": steps, "seed": 1})
            env.run([cropsense, opponent])
            final = env.steps[-1]
            a, b = final[0]["reward"], final[1]["reward"]
            tag = "WIN" if a > b else ("TIE" if a == b else "LOSS")
            print(f"  vs {opponent:<9} | me=${a:>8,.0f} opp=${b:>8,.0f} | "
                  f"{tag} | {time.time()-t0:.1f}s")
    except CellTimeout as e:
        print(f"  vs {opponent:<9} | skipped: {e}")

print("Quick 100-turn benchmark:")
for opp in ["starter", "random", "pass"]:
    quick_bench(opp)

# ============================================================
# CELL 17 — Optional: Save a 200-turn replay JSON
# ============================================================
import json, time

def save_short_replay(opponent="starter", steps=200, seed=42, timeout=20):
    try:
        with time_limit(timeout):
            t0 = time.time()
            env = make("kaggriculture",
                       configuration={"episodeSteps": steps, "seed": seed})
            env.run([cropsense, opponent])
            with open("cropsense_replay.json", "w") as f:
                json.dump(env.toJSON(), f)
            final = env.steps[-1]
            print(f"Replay saved in {time.time()-t0:.1f}s")
            print(f"  CropSense: ${final[0]['reward']:,.0f}")
            print(f"  {opponent}: ${final[1]['reward']:,.0f}")
    except CellTimeout as e:
        print(f"Replay aborted: {e}")

save_short_replay()

# ============================================================
# CELL 18 — Build submission.tar.gz (offline)
# ============================================================
import io, gzip, tarfile, hashlib
from pathlib import Path

MAIN_PY = r'''"""
CropSense — a four-pass adaptive farming agent for Kaggriculture.
Kaggle entry point: agent(obs)
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


def _crop_roi(crop, price, dl):
    c = CROPS[crop]
    ypd = (c["max_y"] / max(1, c["max_d"] + 4)) if c["ongoing"] else (c["max_y"] / max(1, c["max_d"]))
    return (ypd * price) / max(1, c["seed"])


def _animal_roi(animal, price, dl):
    a = ANIMALS[animal]
    if dl < a["first"] + 2:
        return 0.0
    return ((1.0 / a["interval"]) * price) / max(1, a["cost"] / 10)


def _scan_tiles(farm, day):
    rows = []
    tiles = (farm or {}).get("tiles") or []
    for y in range(len(tiles)):
        for x in range(len(tiles[y])):
            t = tiles[y][x]
            if t is None or t == "LOCKED":
                continue
            info = {"x": x, "y": y, "tile": t}
            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    info.update({"type":"plant", "crop": t.get("crop"),
                                 "needs_water": not t.get("watered_today", False),
                                 "harvestable": t.get("yield_units", 0) > 0,
                                 "dying": t.get("consecutive_unwatered", 0) >= 1})
                elif k in ("COOP", "PASTURE"):
                    if "animal" in t:
                        info.update({"type":"animal", "animal": t.get("animal"),
                                     "needs_feed": not t.get("fed_today", False),
                                     "fertilizer": t.get("fertilizer_available", False),
                                     "harvestable": t.get("yield_units", 0) > 0})
                    else:
                        info.update({"type": "structure"})
                elif k == "WEED":
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
    tiles = [t for t in (tiles or []) if _priority(t, day) > 0]
    tiles.sort(key=lambda t: -_priority(t, day))
    assignment, used = {}, set()
    for wi, wpos in enumerate(workers):
        best, best_score = None, -1
        for ti, t in enumerate(tiles):
            if ti in used:
                continue
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
    if (px, py) == (tx, ty):
        return None
    if px < tx: return "EAST"
    if px > tx: return "WEST"
    if py < ty: return "SOUTH"
    if py > ty: return "NORTH"
    return None


def _plan_sales(shed, prices, day):
    orders = []
    for item, qty in (shed or {}).items():
        if qty <= 0:
            continue
        p = (prices or {}).get(item, 0)
        if p <= 1:
            continue
        if day >= 27:
            orders.append(["SELL", item, qty])
        else:
            orders.append(["SELL", item, min(qty, SELL_LIMITS.get(item, qty))])
    return orders


def _pick_target(shops, prices, cash, day):
    demand = Counter()
    for s in (shops or []):
        for p in SHOP_DEMAND.get(s, []):
            demand[p] += 1
    dl = 30 - day
    best, best_score = None, -1.0
    for crop, c in CROPS.items():
        if c["seed"] > cash:
            continue
        price = (prices or {}).get(crop, 0)
        if price <= 0:
            continue
        s = _crop_roi(crop, price, dl) * (1 + 0.25 * demand.get(crop, 0))
        if s > best_score:
            best, best_score = crop, s
    for a, x in ANIMALS.items():
        if x["cost"] > cash * 3:
            continue
        if dl < x["first"] + 4:
            continue
        prod = x.get("product")
        price = (prices or {}).get(prod, 0)
        if price <= 0:
            continue
        s = _animal_roi(a, price, dl) * (1 + 0.25 * demand.get(prod, 0))
        if s > best_score:
            best, best_score = a, s
    return best if best is not None else "WHEAT"


def _safe_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def agent(obs):
    obs   = obs or {}
    me    = _safe_int(obs.get("player", 0))
    day   = _safe_int(obs.get("day", 0))
    farms = obs.get("farms") or []
    farm  = farms[me] if 0 <= me < len(farms) else {}
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
        if t is None:
            return ["PASS"]
        pos = workers[wi]
        if tuple(pos) != (t["x"], t["y"]):
            mv = _step_toward(pos, (t["x"], t["y"]))
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
'''

main_path = Path("main.py")
main_path.write_text(MAIN_PY, encoding="utf-8")

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
print(f"main.py written ({len(MAIN_PY):,} bytes, sha256 {digest}...)")
print(f"submission.tar.gz created ({len(tar_bytes):,} bytes)")

with tarfile.open(archive, "r:gz") as t:
    names = t.getnames()
    inner = t.extractfile("main.py").read().decode("utf-8")
    assert names == ["main.py"], names
    assert inner == MAIN_PY
    assert "def agent(obs):" in inner

print("Archive verified: contains only main.py, entry point present.")
print("Ready to upload submission.tar.gz to Kaggle.")

