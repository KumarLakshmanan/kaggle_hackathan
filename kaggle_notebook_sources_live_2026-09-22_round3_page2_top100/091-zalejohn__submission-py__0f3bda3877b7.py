%%writefile submission.py
"""
Kaggriculture 7-in-1 Adaptive Agent Framework
Submission / Notebook Script: main.py
"""

# =====================================================================
# CORE ENGINE HELPERS & PATHFINDING
# =====================================================================

def _get(obs, key, default=None):
    if obs is None:
        return default
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)

def _my_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or player is None or player < 0 or player >= len(farms):
        return None
    return farms[player]

def _opponent_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or len(farms) < 2:
        return None
    opp_idx = 1 if player == 0 else 0
    return farms[opp_idx]

def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"

def _nearest_unclaimed(pos, targets, claimed):
    fx, fy = pos
    best, best_dist = None, None
    for (x, y) in targets:
        if (x, y) in claimed:
            continue
        dist = abs(x - fx) + abs(y - fy)
        if best_dist is None or dist < best_dist:
            best, best_dist = (x, y), dist
    return best

def _scan_grid(tiles, harvest_thresh=2):
    harvest, water, plant_empty, feed, care, place_animal = {}, {}, {}, {}, {}, {}
    pasture_count = 0
    if not isinstance(tiles, list):
        return harvest, water, plant_empty, feed, care, place_animal, pasture_count

    for y, row in enumerate(tiles):
        if not isinstance(row, list):
            continue
        for x, cell in enumerate(row):
            if cell is None:
                plant_empty[(x, y)] = None
                continue
            if not isinstance(cell, dict):
                continue

            kind = cell.get("kind")
            if kind == "PLANT":
                if cell.get("yield_units", 0) >= harvest_thresh:
                    harvest[(x, y)] = cell
                elif not cell.get("watered_today", False):
                    water[(x, y)] = cell
            elif kind in ("PASTURE", "COOP"):
                pasture_count += 1
                if "animal" not in cell:
                    place_animal[(x, y)] = cell
                else:
                    if not cell.get("fed_today", False):
                        feed[(x, y)] = cell
                    elif not cell.get("cared_today", False):
                        care[(x, y)] = cell

    return harvest, water, plant_empty, feed, care, place_animal, pasture_count

def _assign_workers(positions, buckets, claimed, seeds, shed, money, pasture_count,
                    target_pastures=4, staple="WHEAT", secondary="MELON", build_thresh=150):
    actions = []
    harvest, water, plant_empty, feed, care, place_animal = buckets[:6]

    for raw_pos in positions:
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            actions.append(["PASS"])
            continue
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        act = None

        # Priority 1: Vital Maintenance (Feed -> Care -> Harvest -> Water)
        for targets, cmd in ((feed, ["FEED"]), (care, ["CARE"]), (harvest, ["HARVEST"]), (water, ["WATER"])):
            tgt = _nearest_unclaimed(pos, targets, claimed)
            if tgt:
                claimed.add(tgt)
                act = cmd if tgt == pos else [_step_toward(pos, tgt)]
                break
        if act:
            actions.append(act)
            continue

        # Priority 2: Populate pastures
        spare_animal = next((a for a in ("COW", "SHEEP", "GOOSE") if shed.get(a, 0) > 0), None)
        if spare_animal:
            tgt = _nearest_unclaimed(pos, place_animal, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLACE", spare_animal, 1] if tgt == pos else [_step_toward(pos, tgt)])
                continue

        # Priority 3: Build Pastures
        if pasture_count < target_pastures and money > build_thresh:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["BUILD_PASTURE"] if tgt == pos else [_step_toward(pos, tgt)])
                continue

        # Priority 4: Plant Crops
        crop_to_plant = next((c for c in (staple, secondary) if seeds.get(c, 0) > 0), None)
        if crop_to_plant:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLANT", crop_to_plant] if tgt == pos else [_step_toward(pos, tgt)])
                continue

        actions.append(["PASS"])
    return actions


# =====================================================================
# AGENT NOTEBOOK MODULES (1 - 7)
# =====================================================================

# Notebook 1: Livestock Dairy Dominance (Counters Crop Glut)
def agent_livestock_dairy(obs, conf=None):
    farm = _my_farm(obs)
    if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
    private = _get(obs, "private", {}) or {}
    shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
    buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=2)
    
    claimed = set()
    all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
    actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6],
                              target_pastures=6, staple="WHEAT", secondary="WHEAT", build_thresh=120)
    
    # Market Logic: Continuous Cow/Sheep stocking, high milk/wool sales
    orders = []
    hires_today = farm.get("hires_today", 0)
    target_hands = 6 if money < 1000 else (10 if money < 10000 else 14)
    if hires_today < target_hands and money > 60:
        orders.extend([["HIRE"]] * min(target_hands - hires_today, 3))
    if seeds.get("WHEAT", 0) < 10 and money > 50:
        orders.append(["BUY_SEED", "WHEAT", 15])
    for animal in ("COW", "SHEEP"):
        if money > 280 and buckets[6] > 0 and len(orders) < 8:
            orders.append(["BUY_ANIMAL", animal, 1])
    for item in ("MILK", "WOOL", "EGG"):
        if shed.get(item, 0) > 2 and len(orders) < 10:
            orders.append(["SELL", item, min(shed[item], 15)])
    return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}


# Notebook 2: Melon Peak Yield Engine (Counters Fast Low-Yield Harvesters)
def agent_melon_maximizer(obs, conf=None):
    farm = _my_farm(obs)
    if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
    private = _get(obs, "private", {}) or {}
    shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
    # Hold harvest until yield reaches 5
    buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=5)
    
    claimed = set()
    all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
    actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6],
                              target_pastures=1, staple="MELON", secondary="WHEAT", build_thresh=500)
    orders = []
    hires = farm.get("hires_today", 0)
    if hires < (8 if money < 5000 else 12) and money > 50:
        orders.append(["HIRE"])
    if seeds.get("MELON", 0) < 6 and money > 200:
        orders.append(["BUY_SEED", "MELON", 8])
    if shed.get("MELON", 0) > 4:
        orders.append(["SELL", "MELON", min(shed["MELON"], 20)])
    if money > 4000:
        orders.append(["BUY_LAND"])
    return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}


# Notebook 3: Rapid Wheat/Carrot Cash Rush (Counters Slow Capital Accumulators)
def agent_wheat_carrot_rush(obs, conf=None):
    farm = _my_farm(obs)
    if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
    private = _get(obs, "private", {}) or {}
    shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
    # Fast cycling: harvest as soon as yield >= 1
    buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=1)
    
    claimed = set()
    all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
    actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6],
                              target_pastures=0, staple="WHEAT", secondary="CARROT", build_thresh=9999)
    orders = []
    if farm.get("hires_today", 0) < 10 and money > 40:
        orders.extend([["HIRE"]] * 2)
    for c in ("WHEAT", "CARROT"):
        if seeds.get(c, 0) < 8 and money > 60:
            orders.append(["BUY_SEED", c, 12])
    for item in ("WHEAT", "CARROT"):
        if shed.get(item, 0) > 5:
            orders.append(["SELL", item, shed[item]])
    return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}


# Notebook 4: Dynamic Counter-Trader & Market Arbitrage (Counters Opponent Dumping)
def agent_counter_trader(obs, conf=None):
    farm, opp = _my_farm(obs), _opponent_farm(obs)
    if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
    private = _get(obs, "private", {}) or {}
    shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
    buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=2)

    # Counter-pivot: Detect opponent specialty and produce the opposite
    opp_tiles = opp.get("tiles", []) if opp else []
    opp_pastures = sum(1 for row in opp_tiles if isinstance(row, list) for c in row if isinstance(c, dict) and c.get("kind") in ("PASTURE", "COOP"))
    my_staple = "WHEAT" if opp_pastures > 3 else "MELON"

    claimed = set()
    all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
    actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6],
                              target_pastures=4 if opp_pastures <= 2 else 1, staple=my_staple, secondary="WHEAT")
    
    # Micro-batch selling to prevent price decay (staggered selling)
    orders = []
    if farm.get("hires_today", 0) < 8 and money > 50:
        orders.append(["HIRE"])
    if seeds.get(my_staple, 0) < 5 and money > 100:
        orders.append(["BUY_SEED", my_staple, 10])
    for item, qty in shed.items():
        if item not in {"FERTILIZER", "COW", "SHEEP"} and qty >= 3:
            orders.append(["SELL", item, min(qty, 4)]) # Small lots of 4
    return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}


# Notebook 5: Aggressive Land Baron (Counters Confined Board Archetypes)
def agent_land_expander(obs, conf=None):
    farm = _my_farm(obs)
    if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
    private = _get(obs, "private", {}) or {}
    shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
    buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=2)
    
    claimed = set()
    all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
    actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6],
                              target_pastures=2, staple="WHEAT", secondary="MELON", build_thresh=200)
    orders = []
    # Priority on land acquisitions above $2500
    if money > 2500 and len(orders) < 10:
        orders.append(["BUY_LAND"])
    if farm.get("hires_today", 0) < (12 if money > 2000 else 6) and money > 80:
        orders.append(["HIRE"])
    if seeds.get("WHEAT", 0) < 12 and money > 80:
        orders.append(["BUY_SEED", "WHEAT", 20])
    for item in shed:
        if shed[item] > 4 and item not in ("COW", "SHEEP", "FERTILIZER"):
            orders.append(["SELL", item, shed[item]])
    return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}


# Notebook 6: Strawberry Multi-Harvest Cycle (Counters Labor-Heavy Re-planters)
def agent_berry_engine(obs, conf=None):
    farm = _my_farm(obs)
    if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
    private = _get(obs, "private", {}) or {}
    shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
    buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=1)
    
    claimed = set()
    all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
    actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6],
                              target_pastures=2, staple="STRAWBERRY", secondary="TOMATO", build_thresh=200)
    orders = []
    if farm.get("hires_today", 0) < 7 and money > 60:
        orders.append(["HIRE"])
    for crop in ("STRAWBERRY", "TOMATO"):
        if seeds.get(crop, 0) < 4 and money > 150:
            orders.append(["BUY_SEED", crop, 6])
    for item in ("STRAWBERRY", "TOMATO"):
        if shed.get(item, 0) > 3:
            orders.append(["SELL", item, shed[item]])
    return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}


# Notebook 7: Master Adaptive Meta-Agent (Tournament Winner / Default Entry)
def agent_meta_hybrid(obs, conf=None):
    day = _get(obs, "day", 0) or 0
    step = _get(obs, "step", 0) or 0
    
    # Phase 1: Early game (Days 0-4) -> Cash Rush for rapid foundation
    if day < 5:
        return agent_wheat_carrot_rush(obs, conf)
    # Phase 2: Mid game (Days 5-20) -> Livestock & Melon expansion
    elif day < 21:
        return agent_livestock_dairy(obs, conf)
    # Phase 3: Late game (Days 21-30) -> Maximize Liquidation & Arbitrage
    else:
        return agent_counter_trader(obs, conf)


# Kaggle Competition Standard Entrypoint
def agent(observation, configuration=None):
    try:
        return agent_meta_hybrid(observation, configuration)
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}

%%writefile submission.py
"""
Kaggriculture agent -- v2.

Built from studying a real high-scoring replay (episode 93682830, final
scores ~118,646 / ~111,776), not just the abstract action spec. Key
mechanics discovered from that replay that the v1 baseline missed
entirely:

1. Hired hands are DAY LABORERS. farm["hands"] resets to an EMPTY list
   at the start of every single day (step % turnsPerDay == 0). You must
   re-hire every day or you're farming solo with just the farmer.
2. HIRE cost follows a Fibonacci sequence (1,1,2,3,5,8,13,21,34,55,89,...)
   times farmHandCostMult, reset daily -- so the first several hires each
   day are cheap, and it gets expensive fast after ~10-12 hands.
3. A planted tile looks like:
   {"crop": "WHEAT", "kind": "PLANT", "planted_day": 0,
    "watered_today": False, "consecutive_unwatered": 1,
    "fertilized_until_day": -1, "max_lifespan_step": 120, "yield_units": 1}
   yield_units grows the longer it's left unharvested (observed 1 -> 3
   over ~85 steps for a max_lifespan_step=120 wheat tile).
4. A pasture/animal tile looks like:
   {"kind": "PASTURE", "animal": "SHEEP", "fed_today": False,
    "cared_today": False, "consecutive_unfed": 0,
    "fertilizer_available": False, "pending_care_bonus": 0,
    "placed_day": 0, "yield_units": 0}
   A built-but-empty pasture is just {"kind": "PASTURE"} (no "animal" key)
   and needs an animal PLACEd on it.
5. An empty, unlocked, plantable tile is plain `None`. A locked tile is
   the string "LOCKED".

Because none of this is officially documented (I reverse-engineered it
from one replay), every threshold below is a tunable heuristic, not a
guarantee -- see the CONFIG block. Treat this as a solid, safe starting
strategy to iterate on, not a finished optimal bot.
"""

# ----------------------------- CONFIG --------------------------------
# All tunable knobs live here so you can experiment without touching
# the logic below.

HARVEST_YIELD_THRESHOLD = 2     # harvest once yield_units reaches this
STAPLE_CROP = "WHEAT"           # cheap, fast-cycling crop to lean on
SECONDARY_CROP = "MELON"        # higher-value crop to mix in once flush
LOW_SEED_STOCK = 4              # restock when seed count for a crop drops below this
SEED_BUY_BATCH = 10             # how many seeds to buy per restock order

DESIRED_HANDS_BY_MONEY = [      # (money_threshold, target_hand_count)
    (0, 5),
    (500, 6),
    (2000, 8),
    (8000, 10),
    (25000, 12),
    (60000, 15),
]

SELL_THRESHOLD = 6              # sell shed stock above this quantity
SELL_BATCH_CAP = 20             # never sell more than this many units at once
KEEP_OUT_OF_SELLING = {"FERTILIZER", "COW", "SHEEP", "GOOSE"}  # keep for placing/using

LAND_BUY_MONEY_FLOOR = 3000     # only consider BUY_LAND above this cash cushion
TARGET_PASTURE_COUNT = 4        # keep at least this many pastures/coops built
BUILD_PASTURE_MONEY_FLOOR = 150 # only build a new pasture above this cash cushion

MAX_MARKET_ORDERS = 10          # matches configuration.maxMarketOrdersPerTurn

DEFAULT_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}


# ----------------------------- HELPERS --------------------------------

def _get(obs, key, default=None):
    """Read a field whether obs is a dict or an attribute-style object."""
    if obs is None:
        return default
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


def _my_farm(observation):
    farms = _get(observation, "farms", [])
    player = _get(observation, "player", 0)
    if not isinstance(farms, list) or player is None:
        return None
    if player < 0 or player >= len(farms):
        return None
    return farms[player]


def _desired_hand_count(money):
    target = DESIRED_HANDS_BY_MONEY[0][1]
    for threshold, count in DESIRED_HANDS_BY_MONEY:
        if money >= threshold:
            target = count
    return target


def _scan_tiles(tiles):
    """Single pass over the grid, bucketing tiles by what can be done to
    them. Returns dicts of {(x, y): tile_or_None} per category, plus a
    count of existing pasture/coop structures (built, whether occupied
    by an animal or not)."""
    harvest, water, plant_empty, feed, care, place_animal = {}, {}, {}, {}, {}, {}
    pasture_count = 0

    if not isinstance(tiles, list):
        return harvest, water, plant_empty, feed, care, place_animal, pasture_count

    for y, row in enumerate(tiles):
        if not isinstance(row, list):
            continue
        for x, cell in enumerate(row):
            if cell is None:
                plant_empty[(x, y)] = None
                continue
            if not isinstance(cell, dict):
                continue  # "LOCKED" or anything unexpected -- skip

            kind = cell.get("kind")
            if kind == "PLANT":
                if cell.get("yield_units", 0) >= HARVEST_YIELD_THRESHOLD:
                    harvest[(x, y)] = cell
                elif not cell.get("watered_today", False):
                    water[(x, y)] = cell
            elif kind in ("PASTURE", "COOP"):
                pasture_count += 1
                if "animal" not in cell:
                    place_animal[(x, y)] = cell
                else:
                    if not cell.get("fed_today", False):
                        feed[(x, y)] = cell
                    elif not cell.get("cared_today", False):
                        care[(x, y)] = cell

    return harvest, water, plant_empty, feed, care, place_animal, pasture_count


def _nearest_unclaimed(pos, targets, claimed):
    fx, fy = pos
    best, best_dist = None, None
    for (x, y) in targets:
        if (x, y) in claimed:
            continue
        dist = abs(x - fx) + abs(y - fy)
        if best_dist is None or dist < best_dist:
            best, best_dist = (x, y), dist
    return best


def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"


def _worker_action(pos, buckets, claimed, seeds, shed, money, pasture_count):
    """Decide one worker's (farmer or hand) action for this turn.
    Priority: harvest > water > feed > care > place animal >
    build pasture (if under target) > plant > PASS.
    Mutates `claimed` so other workers this turn don't pile onto the
    same tile."""
    harvest, water, plant_empty, feed, care, place_animal = buckets[:6]

    for targets, op_when_here in (
        (harvest, ["HARVEST"]),
        (water, ["WATER"]),
        (feed, ["FEED"]),
        (care, ["CARE"]),
    ):
        target = _nearest_unclaimed(pos, targets, claimed)
        if target is not None:
            claimed.add(target)
            if target == pos:
                return op_when_here
            return [_step_toward(pos, target)]

    # Place a spare animal on an empty pasture/coop, if we have one in the shed.
    spare_animal = None
    for animal in ("SHEEP", "COW", "GOOSE"):
        if shed.get(animal, 0) > 0:
            spare_animal = animal
            break
    if spare_animal is not None:
        target = _nearest_unclaimed(pos, place_animal, claimed)
        if target is not None:
            claimed.add(target)
            if target == pos:
                return ["PLACE", spare_animal, 1]
            return [_step_toward(pos, target)]

    # Build a new pasture if we're short of them and can afford it --
    # this is what actually grows the animal side of the economy instead
    # of only planting crops forever.
    if pasture_count < TARGET_PASTURE_COUNT and money > BUILD_PASTURE_MONEY_FLOOR:
        target = _nearest_unclaimed(pos, plant_empty, claimed)
        if target is not None:
            claimed.add(target)
            if target == pos:
                return ["BUILD_PASTURE"]
            return [_step_toward(pos, target)]

    # Plant on an empty tile if we're carrying seed stock.
    crop_to_plant = None
    for crop in (STAPLE_CROP, SECONDARY_CROP):
        if seeds.get(crop, 0) > 0:
            crop_to_plant = crop
            break
    if crop_to_plant is not None:
        target = _nearest_unclaimed(pos, plant_empty, claimed)
        if target is not None:
            claimed.add(target)
            if target == pos:
                return ["PLANT", crop_to_plant]
            return [_step_toward(pos, target)]

    return ["PASS"]


def _build_market_orders(farm, private, day, step, turns_per_day):
    orders = []
    money = farm.get("money", 0)
    hires_today = farm.get("hires_today", 0)
    seeds = private.get("seeds", {})
    shed = private.get("shed", {})

    desired_hands = _desired_hand_count(money)

    # 1) Re-hire at the start of each day (hands reset to empty daily).
    #    Keep queuing HIRE while under target and money looks comfortable
    #    (cheap early hires; later ones cost more via the Fibonacci curve,
    #    so we stop trusting "just hire" once money gets tight).
    if hires_today < desired_hands and money > 50:
        need = desired_hands - hires_today
        for _ in range(min(need, MAX_MARKET_ORDERS - len(orders))):
            orders.append(["HIRE"])

    # 2) Restock seeds when running low.
    for crop in (STAPLE_CROP, SECONDARY_CROP):
        if len(orders) >= MAX_MARKET_ORDERS:
            break
        if seeds.get(crop, 0) < LOW_SEED_STOCK and money > 100:
            orders.append(["BUY_SEED", crop, SEED_BUY_BATCH])

    # 3) Sell surplus shed stock.
    for item, qty in shed.items():
        if len(orders) >= MAX_MARKET_ORDERS:
            break
        if item in KEEP_OUT_OF_SELLING:
            continue
        if qty > SELL_THRESHOLD:
            sell_qty = min(qty - SELL_THRESHOLD, SELL_BATCH_CAP)
            if sell_qty > 0:
                orders.append(["SELL", item, sell_qty])

    # 4) Buy an animal to stock an empty pasture, if the shed has none spare.
    if len(orders) < MAX_MARKET_ORDERS and money > 300:
        if not any(shed.get(a, 0) > 0 for a in ("SHEEP", "COW", "GOOSE")):
            orders.append(["BUY_ANIMAL", "SHEEP", 1])

    # 5) Expand land once there's a healthy cash cushion.
    if len(orders) < MAX_MARKET_ORDERS and money > LAND_BUY_MONEY_FLOOR:
        orders.append(["BUY_LAND"])

    return orders[:MAX_MARKET_ORDERS]


# ------------------------------- AGENT ---------------------------------

def agent(observation, configuration=None):
    try:
        farm = _my_farm(observation)
        if not farm:
            return DEFAULT_ACTION

        farmer_xy = farm.get("farmer", [0, 0])
        if not isinstance(farmer_xy, (list, tuple)) or len(farmer_xy) < 2:
            return DEFAULT_ACTION
        farmer_pos = (int(farmer_xy[0]), int(farmer_xy[1]))

        hand_positions = farm.get("hands", [])
        if not isinstance(hand_positions, list):
            hand_positions = []

        private = _get(observation, "private", {}) or {}
        seeds = private.get("seeds", {}) or {}
        shed = private.get("shed", {}) or {}

        money = farm.get("money", 0)

        tiles = farm.get("tiles", [])
        buckets = _scan_tiles(tiles)
        pasture_count = buckets[6]

        claimed = set()
        farmer_action = _worker_action(farmer_pos, buckets, claimed, seeds, shed, money, pasture_count)

        hand_actions = []
        for hp in hand_positions:
            if not isinstance(hp, (list, tuple)) or len(hp) < 2:
                hand_actions.append(["PASS"])
                continue
            pos = (int(hp[0]), int(hp[1]))
            hand_actions.append(_worker_action(pos, buckets, claimed, seeds, shed, money, pasture_count))

        day = _get(observation, "day", 0) or 0
        step = _get(observation, "step", 0) or 0
        turns_per_day = 24
        if isinstance(configuration, dict):
            turns_per_day = configuration.get("turnsPerDay", 24)
        else:
            turns_per_day = _get(configuration, "turnsPerDay", 24) or 24

        market_orders = _build_market_orders(farm, private, day, step, turns_per_day)

        return {"farmer": farmer_action, "hands": hand_actions, "market": market_orders}

    except Exception:
        return DEFAULT_ACTION

import importlib.util

spec = importlib.util.spec_from_file_location("submission", "submission.py")
submission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(submission)

assert callable(getattr(submission, "agent", None)), "agent() was not found in submission.py"
print("agent() found and callable.")

import json
import os

REPLAY_PATH = "replay.json"

if os.path.exists(REPLAY_PATH):
    with open(REPLAY_PATH) as f:
        replay = json.load(f)

    steps = replay["steps"]
    config = replay["configuration"]
    max_orders = config.get("maxMarketOrdersPerTurn", 10)

    # Sample across the whole game, including day boundaries (multiples of turnsPerDay).
    turns_per_day = config.get("turnsPerDay", 24)
    sample_indices = sorted(set(
        [0, 1, turns_per_day, turns_per_day + 1, len(steps) - 1]
        + list(range(0, len(steps), max(1, len(steps) // 15)))
    ))

    failures = 0
    for t in sample_indices:
        for p in range(len(steps[t])):
            obs = steps[t][p]["observation"]
            try:
                action = submission.agent(obs, config)
                assert isinstance(action, dict) and set(action) == {"farmer", "hands", "market"}
                assert len(action["market"]) <= max_orders
            except Exception as exc:
                failures += 1
                print(f"FAILED at t={t} p={p}: {exc!r}")

    if failures == 0:
        print(f"Replay test PASS -- {len(sample_indices) * len(steps[0])} observations, 0 failures.")
    else:
        print(f"Replay test: {failures} failures -- fix before submitting.")
else:
    print(f"No {REPLAY_PATH} found -- skipping replay test. "
          f"Upload a real episode JSON as \'{REPLAY_PATH}\' to run this check.")


bad_observations = [
    None, {}, {"farms": []}, {"farms": [{}], "player": 0},
    {"farms": [{"farmer": "garbage", "tiles": "garbage"}], "player": 0},
    5, "string", [],
]

for obs in bad_observations:
    try:
        result = submission.agent(obs, {})
        assert isinstance(result, dict) and "farmer" in result
    except Exception as exc:
        print(f"FAILED on {obs!r}: {exc!r}")
        raise

print("Fuzz tests passed -- malformed input never crashes the agent.")

try:
    from kaggle_environments import make

    env = make("kaggriculture", debug=True)
    env.run(["submission.py", "submission.py"])

    for i, state in enumerate(env.state):
        print(f"Agent {i}: status={state.status}, reward={state.reward}")

    print("Live environment test: PASS")
except ModuleNotFoundError:
    print("kaggle_environments is not installed here -- skipping live test. "
          "Run `pip install kaggle_environments` and re-run this cell before submitting.")
except Exception as exc:
    print(f"Live environment test FAILED: {exc!r}")
    print("Fix this before submitting -- the hidden rerun will hit the same issue.")

import os

assert os.path.exists("submission.py"), "submission.py was not written"
assert callable(submission.agent), "agent must be callable"
print("FINAL CHECK: submission.py exists =", os.path.exists("submission.py"))
print("FINAL CHECK: agent is callable =", callable(submission.agent))
print("Ready: submit submission.py to the competition.")

"""
Notebook 1: Dairy & Livestock Mogul
Focus: Rapid Pasture setup, Cows (Milk) + Sheep (Wool).
"""

def _get(obs, key, default=None):
    if obs is None: return default
    return obs.get(key, default) if isinstance(obs, dict) else getattr(obs, key, default)

def _my_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or player is None or player < 0 or player >= len(farms):
        return None
    return farms[player]

def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"

def _nearest_unclaimed(pos, targets, claimed):
    fx, fy = pos
    best, best_dist = None, None
    for (x, y) in targets:
        if (x, y) in claimed: continue
        dist = abs(x - fx) + abs(y - fy)
        if best_dist is None or dist < best_dist:
            best, best_dist = (x, y), dist
    return best

def _scan_grid(tiles, harvest_thresh=2):
    harvest, water, plant_empty, feed, care, place_animal = {}, {}, {}, {}, {}, {}
    pasture_count = 0
    if not isinstance(tiles, list):
        return harvest, water, plant_empty, feed, care, place_animal, pasture_count

    for y, row in enumerate(tiles):
        if not isinstance(row, list): continue
        for x, cell in enumerate(row):
            if cell is None:
                plant_empty[(x, y)] = None
                continue
            if not isinstance(cell, dict): continue
            kind = cell.get("kind")
            if kind == "PLANT":
                if cell.get("yield_units", 0) >= harvest_thresh: harvest[(x, y)] = cell
                elif not cell.get("watered_today", False): water[(x, y)] = cell
            elif kind in ("PASTURE", "COOP"):
                pasture_count += 1
                if "animal" not in cell: place_animal[(x, y)] = cell
                else:
                    if not cell.get("fed_today", False): feed[(x, y)] = cell
                    elif not cell.get("cared_today", False): care[(x, y)] = cell
    return harvest, water, plant_empty, feed, care, place_animal, pasture_count

def _assign_workers(positions, buckets, claimed, seeds, shed, money, pasture_count):
    actions = []
    harvest, water, plant_empty, feed, care, place_animal = buckets[:6]
    for raw_pos in positions:
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            actions.append(["PASS"])
            continue
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        act = None
        for targets, cmd in ((feed, ["FEED"]), (care, ["CARE"]), (harvest, ["HARVEST"]), (water, ["WATER"])):
            tgt = _nearest_unclaimed(pos, targets, claimed)
            if tgt:
                claimed.add(tgt)
                act = cmd if tgt == pos else [_step_toward(pos, tgt)]
                break
        if act:
            actions.append(act)
            continue

        spare = next((a for a in ("COW", "SHEEP", "GOOSE") if shed.get(a, 0) > 0), None)
        if spare:
            tgt = _nearest_unclaimed(pos, place_animal, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLACE", spare, 1] if tgt == pos else [_step_toward(pos, tgt)])
                continue

        if pasture_count < 6 and money > 120:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["BUILD_PASTURE"] if tgt == pos else [_step_toward(pos, tgt)])
                continue

        if seeds.get("WHEAT", 0) > 0:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLANT", "WHEAT"] if tgt == pos else [_step_toward(pos, tgt)])
                continue
        actions.append(["PASS"])
    return actions

def agent(observation, configuration=None):
    try:
        farm = _my_farm(observation)
        if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
        private = _get(observation, "private", {}) or {}
        shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
        buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=2)

        claimed = set()
        all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
        actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6])

        orders = []
        hires_today = farm.get("hires_today", 0)
        target_hands = 6 if money < 1000 else (10 if money < 10000 else 14)
        if hires_today < target_hands and money > 60:
            orders.extend([["HIRE"]] * min(target_hands - hires_today, 3))
        if seeds.get("WHEAT", 0) < 8 and money > 50:
            orders.append(["BUY_SEED", "WHEAT", 12])
        for animal in ("COW", "SHEEP"):
            if money > 280 and buckets[6] > 0 and len(orders) < 8:
                orders.append(["BUY_ANIMAL", animal, 1])
        for item in ("MILK", "WOOL", "EGG"):
            if shed.get(item, 0) > 2 and len(orders) < 10:
                orders.append(["SELL", item, min(shed[item], 15)])

        return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}

"""
Notebook 2: Melon Peak-Yield Optimizer
Focus: High value crop patience, holding until maximum yield.
"""

def _get(obs, key, default=None):
    if obs is None: return default
    return obs.get(key, default) if isinstance(obs, dict) else getattr(obs, key, default)

def _my_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or player is None or player < 0 or player >= len(farms):
        return None
    return farms[player]

def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"

def _nearest_unclaimed(pos, targets, claimed):
    fx, fy = pos
    best, best_dist = None, None
    for (x, y) in targets:
        if (x, y) in claimed: continue
        dist = abs(x - fx) + abs(y - fy)
        if best_dist is None or dist < best_dist:
            best, best_dist = (x, y), dist
    return best

def _scan_grid(tiles, harvest_thresh=5):
    harvest, water, plant_empty, feed, care, place_animal = {}, {}, {}, {}, {}, {}
    pasture_count = 0
    if not isinstance(tiles, list):
        return harvest, water, plant_empty, feed, care, place_animal, pasture_count

    for y, row in enumerate(tiles):
        if not isinstance(row, list): continue
        for x, cell in enumerate(row):
            if cell is None:
                plant_empty[(x, y)] = None
                continue
            if not isinstance(cell, dict): continue
            kind = cell.get("kind")
            if kind == "PLANT":
                if cell.get("yield_units", 0) >= harvest_thresh: harvest[(x, y)] = cell
                elif not cell.get("watered_today", False): water[(x, y)] = cell
            elif kind in ("PASTURE", "COOP"):
                pasture_count += 1
                if "animal" not in cell: place_animal[(x, y)] = cell
                else:
                    if not cell.get("fed_today", False): feed[(x, y)] = cell
                    elif not cell.get("cared_today", False): care[(x, y)] = cell
    return harvest, water, plant_empty, feed, care, place_animal, pasture_count

def _assign_workers(positions, buckets, claimed, seeds, shed, money, pasture_count):
    actions = []
    harvest, water, plant_empty, feed, care, place_animal = buckets[:6]
    for raw_pos in positions:
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            actions.append(["PASS"])
            continue
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        act = None
        for targets, cmd in ((harvest, ["HARVEST"]), (water, ["WATER"]), (feed, ["FEED"]), (care, ["CARE"])):
            tgt = _nearest_unclaimed(pos, targets, claimed)
            if tgt:
                claimed.add(tgt)
                act = cmd if tgt == pos else [_step_toward(pos, tgt)]
                break
        if act:
            actions.append(act)
            continue

        crop = "MELON" if seeds.get("MELON", 0) > 0 else ("WHEAT" if seeds.get("WHEAT", 0) > 0 else None)
        if crop:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLANT", crop] if tgt == pos else [_step_toward(pos, tgt)])
                continue
        actions.append(["PASS"])
    return actions

def agent(observation, configuration=None):
    try:
        farm = _my_farm(observation)
        if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
        private = _get(observation, "private", {}) or {}
        shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
        buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=5)

        claimed = set()
        all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
        actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6])

        orders = []
        hires = farm.get("hires_today", 0)
        target_hands = 8 if money < 5000 else 12
        if hires < target_hands and money > 50:
            orders.append(["HIRE"])
        if seeds.get("MELON", 0) < 6 and money > 200:
            orders.append(["BUY_SEED", "MELON", 8])
        if shed.get("MELON", 0) > 4:
            orders.append(["SELL", "MELON", min(shed["MELON"], 20)])
        if money > 4000:
            orders.append(["BUY_LAND"])

        return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}

"""
Notebook 3: High-Frequency Cash Crop Rush
Focus: 1-turn turnover Wheat/Carrot cycles for early capital accumulation.
"""

def _get(obs, key, default=None):
    if obs is None: return default
    return obs.get(key, default) if isinstance(obs, dict) else getattr(obs, key, default)

def _my_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or player is None or player < 0 or player >= len(farms):
        return None
    return farms[player]

def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"

def _nearest_unclaimed(pos, targets, claimed):
    fx, fy = pos
    best, best_dist = None, None
    for (x, y) in targets:
        if (x, y) in claimed: continue
        dist = abs(x - fx) + abs(y - fy)
        if best_dist is None or dist < best_dist:
            best, best_dist = (x, y), dist
    return best

def _scan_grid(tiles, harvest_thresh=1):
    harvest, water, plant_empty = {}, {}, {}
    if not isinstance(tiles, list): return harvest, water, plant_empty

    for y, row in enumerate(tiles):
        if not isinstance(row, list): continue
        for x, cell in enumerate(row):
            if cell is None:
                plant_empty[(x, y)] = None
                continue
            if not isinstance(cell, dict): continue
            if cell.get("kind") == "PLANT":
                if cell.get("yield_units", 0) >= harvest_thresh: harvest[(x, y)] = cell
                elif not cell.get("watered_today", False): water[(x, y)] = cell
    return harvest, water, plant_empty

def _assign_workers(positions, buckets, claimed, seeds):
    actions = []
    harvest, water, plant_empty = buckets
    for raw_pos in positions:
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            actions.append(["PASS"])
            continue
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        act = None
        for targets, cmd in ((harvest, ["HARVEST"]), (water, ["WATER"])):
            tgt = _nearest_unclaimed(pos, targets, claimed)
            if tgt:
                claimed.add(tgt)
                act = cmd if tgt == pos else [_step_toward(pos, tgt)]
                break
        if act:
            actions.append(act)
            continue

        crop = "WHEAT" if seeds.get("WHEAT", 0) > 0 else ("CARROT" if seeds.get("CARROT", 0) > 0 else None)
        if crop:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLANT", crop] if tgt == pos else [_step_toward(pos, tgt)])
                continue
        actions.append(["PASS"])
    return actions

def agent(observation, configuration=None):
    try:
        farm = _my_farm(observation)
        if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
        private = _get(observation, "private", {}) or {}
        shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
        buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=1)

        claimed = set()
        all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
        actions = _assign_workers(all_workers, buckets, claimed, seeds)

        orders = []
        if farm.get("hires_today", 0) < 10 and money > 40:
            orders.extend([["HIRE"]] * 2)
        for c in ("WHEAT", "CARROT"):
            if seeds.get(c, 0) < 8 and money > 60:
                orders.append(["BUY_SEED", c, 12])
        for item in ("WHEAT", "CARROT"):
            if shed.get(item, 0) > 4:
                orders.append(["SELL", item, shed[item]])

        return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}

"""
Notebook 4: Market Arbitrage & Anti-Glut Trader
Focus: Dynamic opposing production counter and staggered micro-batch liquidation.
"""

def _get(obs, key, default=None):
    if obs is None: return default
    return obs.get(key, default) if isinstance(obs, dict) else getattr(obs, key, default)

def _my_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or player is None or player < 0 or player >= len(farms):
        return None
    return farms[player]

def _opponent_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or len(farms) < 2: return None
    return farms[1 if player == 0 else 0]

def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"

def _nearest_unclaimed(pos, targets, claimed):
    fx, fy = pos
    best, best_dist = None, None
    for (x, y) in targets:
        if (x, y) in claimed: continue
        dist = abs(x - fx) + abs(y - fy)
        if best_dist is None or dist < best_dist:
            best, best_dist = (x, y), dist
    return best

def _scan_grid(tiles, harvest_thresh=2):
    harvest, water, plant_empty, feed, care, place_animal = {}, {}, {}, {}, {}, {}
    pasture_count = 0
    if not isinstance(tiles, list):
        return harvest, water, plant_empty, feed, care, place_animal, pasture_count

    for y, row in enumerate(tiles):
        if not isinstance(row, list): continue
        for x, cell in enumerate(row):
            if cell is None:
                plant_empty[(x, y)] = None
                continue
            if not isinstance(cell, dict): continue
            kind = cell.get("kind")
            if kind == "PLANT":
                if cell.get("yield_units", 0) >= harvest_thresh: harvest[(x, y)] = cell
                elif not cell.get("watered_today", False): water[(x, y)] = cell
            elif kind in ("PASTURE", "COOP"):
                pasture_count += 1
                if "animal" not in cell: place_animal[(x, y)] = cell
                else:
                    if not cell.get("fed_today", False): feed[(x, y)] = cell
                    elif not cell.get("cared_today", False): care[(x, y)] = cell
    return harvest, water, plant_empty, feed, care, place_animal, pasture_count

def _assign_workers(positions, buckets, claimed, seeds, shed, money, pasture_count, staple):
    actions = []
    harvest, water, plant_empty, feed, care, place_animal = buckets[:6]
    for raw_pos in positions:
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            actions.append(["PASS"])
            continue
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        act = None
        for targets, cmd in ((feed, ["FEED"]), (care, ["CARE"]), (harvest, ["HARVEST"]), (water, ["WATER"])):
            tgt = _nearest_unclaimed(pos, targets, claimed)
            if tgt:
                claimed.add(tgt)
                act = cmd if tgt == pos else [_step_toward(pos, tgt)]
                break
        if act:
            actions.append(act)
            continue

        if seeds.get(staple, 0) > 0:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLANT", staple] if tgt == pos else [_step_toward(pos, tgt)])
                continue
        actions.append(["PASS"])
    return actions

def agent(observation, configuration=None):
    try:
        farm, opp = _my_farm(observation), _opponent_farm(observation)
        if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
        private = _get(observation, "private", {}) or {}
        shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
        buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=2)

        opp_tiles = opp.get("tiles", []) if opp else []
        opp_pastures = sum(1 for row in opp_tiles if isinstance(row, list) for c in row if isinstance(c, dict) and c.get("kind") in ("PASTURE", "COOP"))
        staple = "WHEAT" if opp_pastures > 2 else "MELON"

        claimed = set()
        all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
        actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6], staple)

        orders = []
        if farm.get("hires_today", 0) < 8 and money > 50:
            orders.append(["HIRE"])
        if seeds.get(staple, 0) < 5 and money > 100:
            orders.append(["BUY_SEED", staple, 10])
        for item, qty in shed.items():
            if item not in {"FERTILIZER", "COW", "SHEEP"} and qty >= 3:
                orders.append(["SELL", item, min(qty, 4)])

        return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}

"""
Notebook 5: Land Expansionist Baron
Focus: Maximizing map space via BUY_LAND triggers.
"""

def _get(obs, key, default=None):
    if obs is None: return default
    return obs.get(key, default) if isinstance(obs, dict) else getattr(obs, key, default)

def _my_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or player is None or player < 0 or player >= len(farms):
        return None
    return farms[player]

def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"

def _nearest_unclaimed(pos, targets, claimed):
    fx, fy = pos
    best, best_dist = None, None
    for (x, y) in targets:
        if (x, y) in claimed: continue
        dist = abs(x - fx) + abs(y - fy)
        if best_dist is None or dist < best_dist:
            best, best_dist = (x, y), dist
    return best

def _scan_grid(tiles, harvest_thresh=2):
    harvest, water, plant_empty = {}, {}, {}
    if not isinstance(tiles, list): return harvest, water, plant_empty

    for y, row in enumerate(tiles):
        if not isinstance(row, list): continue
        for x, cell in enumerate(row):
            if cell is None:
                plant_empty[(x, y)] = None
                continue
            if not isinstance(cell, dict): continue
            if cell.get("kind") == "PLANT":
                if cell.get("yield_units", 0) >= harvest_thresh: harvest[(x, y)] = cell
                elif not cell.get("watered_today", False): water[(x, y)] = cell
    return harvest, water, plant_empty

def _assign_workers(positions, buckets, claimed, seeds):
    actions = []
    harvest, water, plant_empty = buckets
    for raw_pos in positions:
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            actions.append(["PASS"])
            continue
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        act = None
        for targets, cmd in ((harvest, ["HARVEST"]), (water, ["WATER"])):
            tgt = _nearest_unclaimed(pos, targets, claimed)
            if tgt:
                claimed.add(tgt)
                act = cmd if tgt == pos else [_step_toward(pos, tgt)]
                break
        if act:
            actions.append(act)
            continue

        if seeds.get("WHEAT", 0) > 0:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLANT", "WHEAT"] if tgt == pos else [_step_toward(pos, tgt)])
                continue
        actions.append(["PASS"])
    return actions

def agent(observation, configuration=None):
    try:
        farm = _my_farm(observation)
        if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
        private = _get(observation, "private", {}) or {}
        shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
        buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=2)

        claimed = set()
        all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
        actions = _assign_workers(all_workers, buckets, claimed, seeds)

        orders = []
        if money > 2500:
            orders.append(["BUY_LAND"])
        if farm.get("hires_today", 0) < (12 if money > 2000 else 6) and money > 80:
            orders.append(["HIRE"])
        if seeds.get("WHEAT", 0) < 12 and money > 80:
            orders.append(["BUY_SEED", "WHEAT", 20])
        for item, qty in shed.items():
            if qty > 4 and item not in ("COW", "SHEEP", "FERTILIZER"):
                orders.append(["SELL", item, qty])

        return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}

"""
Notebook 6: Strawberry Continuous Multi-Harvest Engine
Focus: Minimizing re-planting turn loss with recurring crops.
"""

def _get(obs, key, default=None):
    if obs is None: return default
    return obs.get(key, default) if isinstance(obs, dict) else getattr(obs, key, default)

def _my_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or player is None or player < 0 or player >= len(farms):
        return None
    return farms[player]

def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"

def _nearest_unclaimed(pos, targets, claimed):
    fx, fy = pos
    best, best_dist = None, None
    for (x, y) in targets:
        if (x, y) in claimed: continue
        dist = abs(x - fx) + abs(y - fy)
        if best_dist is None or dist < best_dist:
            best, best_dist = (x, y), dist
    return best

def _scan_grid(tiles, harvest_thresh=1):
    harvest, water, plant_empty = {}, {}, {}
    if not isinstance(tiles, list): return harvest, water, plant_empty

    for y, row in enumerate(tiles):
        if not isinstance(row, list): continue
        for x, cell in enumerate(row):
            if cell is None:
                plant_empty[(x, y)] = None
                continue
            if not isinstance(cell, dict): continue
            if cell.get("kind") == "PLANT":
                if cell.get("yield_units", 0) >= harvest_thresh: harvest[(x, y)] = cell
                elif not cell.get("watered_today", False): water[(x, y)] = cell
    return harvest, water, plant_empty

def _assign_workers(positions, buckets, claimed, seeds):
    actions = []
    harvest, water, plant_empty = buckets
    for raw_pos in positions:
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            actions.append(["PASS"])
            continue
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        act = None
        for targets, cmd in ((harvest, ["HARVEST"]), (water, ["WATER"])):
            tgt = _nearest_unclaimed(pos, targets, claimed)
            if tgt:
                claimed.add(tgt)
                act = cmd if tgt == pos else [_step_toward(pos, tgt)]
                break
        if act:
            actions.append(act)
            continue

        crop = "STRAWBERRY" if seeds.get("STRAWBERRY", 0) > 0 else ("TOMATO" if seeds.get("TOMATO", 0) > 0 else None)
        if crop:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLANT", crop] if tgt == pos else [_step_toward(pos, tgt)])
                continue
        actions.append(["PASS"])
    return actions

def agent(observation, configuration=None):
    try:
        farm = _my_farm(observation)
        if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
        private = _get(observation, "private", {}) or {}
        shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)
        buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=1)

        claimed = set()
        all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
        actions = _assign_workers(all_workers, buckets, claimed, seeds)

        orders = []
        if farm.get("hires_today", 0) < 7 and money > 60:
            orders.append(["HIRE"])
        for crop in ("STRAWBERRY", "TOMATO"):
            if seeds.get(crop, 0) < 4 and money > 150:
                orders.append(["BUY_SEED", crop, 6])
        for item in ("STRAWBERRY", "TOMATO"):
            if shed.get(item, 0) > 3:
                orders.append(["SELL", item, shed[item]])

        return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}

"""
Notebook 7: Dynamic Multi-Armed Hybrid Meta Agent
Focus: Phase-aware state machine transitioning through Rush, Scaling, and Arbitrage.
"""

def _get(obs, key, default=None):
    if obs is None: return default
    return obs.get(key, default) if isinstance(obs, dict) else getattr(obs, key, default)

def _my_farm(obs):
    farms = _get(obs, "farms", [])
    player = _get(obs, "player", 0)
    if not isinstance(farms, list) or player is None or player < 0 or player >= len(farms):
        return None
    return farms[player]

def _step_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"

def _nearest_unclaimed(pos, targets, claimed):
    fx, fy = pos
    best, best_dist = None, None
    for (x, y) in targets:
        if (x, y) in claimed: continue
        dist = abs(x - fx) + abs(y - fy)
        if best_dist is None or dist < best_dist:
            best, best_dist = (x, y), dist
    return best

def _scan_grid(tiles, harvest_thresh=2):
    harvest, water, plant_empty, feed, care, place_animal = {}, {}, {}, {}, {}, {}
    pasture_count = 0
    if not isinstance(tiles, list):
        return harvest, water, plant_empty, feed, care, place_animal, pasture_count

    for y, row in enumerate(tiles):
        if not isinstance(row, list): continue
        for x, cell in enumerate(row):
            if cell is None:
                plant_empty[(x, y)] = None
                continue
            if not isinstance(cell, dict): continue
            kind = cell.get("kind")
            if kind == "PLANT":
                if cell.get("yield_units", 0) >= harvest_thresh: harvest[(x, y)] = cell
                elif not cell.get("watered_today", False): water[(x, y)] = cell
            elif kind in ("PASTURE", "COOP"):
                pasture_count += 1
                if "animal" not in cell: place_animal[(x, y)] = cell
                else:
                    if not cell.get("fed_today", False): feed[(x, y)] = cell
                    elif not cell.get("cared_today", False): care[(x, y)] = cell
    return harvest, water, plant_empty, feed, care, place_animal, pasture_count

def _assign_workers(positions, buckets, claimed, seeds, shed, money, pasture_count, target_pastures, staple):
    actions = []
    harvest, water, plant_empty, feed, care, place_animal = buckets[:6]
    for raw_pos in positions:
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            actions.append(["PASS"])
            continue
        pos = (int(raw_pos[0]), int(raw_pos[1]))
        act = None
        for targets, cmd in ((feed, ["FEED"]), (care, ["CARE"]), (harvest, ["HARVEST"]), (water, ["WATER"])):
            tgt = _nearest_unclaimed(pos, targets, claimed)
            if tgt:
                claimed.add(tgt)
                act = cmd if tgt == pos else [_step_toward(pos, tgt)]
                break
        if act:
            actions.append(act)
            continue

        spare = next((a for a in ("COW", "SHEEP", "GOOSE") if shed.get(a, 0) > 0), None)
        if spare:
            tgt = _nearest_unclaimed(pos, place_animal, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLACE", spare, 1] if tgt == pos else [_step_toward(pos, tgt)])
                continue

        if pasture_count < target_pastures and money > 150:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["BUILD_PASTURE"] if tgt == pos else [_step_toward(pos, tgt)])
                continue

        crop = staple if seeds.get(staple, 0) > 0 else ("WHEAT" if seeds.get("WHEAT", 0) > 0 else None)
        if crop:
            tgt = _nearest_unclaimed(pos, plant_empty, claimed)
            if tgt:
                claimed.add(tgt)
                actions.append(["PLANT", crop] if tgt == pos else [_step_toward(pos, tgt)])
                continue
        actions.append(["PASS"])
    return actions

def agent(observation, configuration=None):
    try:
        farm = _my_farm(observation)
        if not farm: return {"farmer": ["PASS"], "hands": [], "market": []}
        day = _get(observation, "day", 0) or 0
        private = _get(observation, "private", {}) or {}
        shed, seeds, money = private.get("shed", {}), private.get("seeds", {}), farm.get("money", 0)

        # Dynamic State Adjustment
        if day < 5:
            harvest_thresh, target_pastures, staple = 1, 0, "WHEAT"
        elif day < 22:
            harvest_thresh, target_pastures, staple = 3, 5, "MELON"
        else:
            harvest_thresh, target_pastures, staple = 2, 5, "WHEAT"

        buckets = _scan_grid(farm.get("tiles", []), harvest_thresh=harvest_thresh)
        claimed = set()
        all_workers = [farm.get("farmer", [0, 0])] + farm.get("hands", [])
        actions = _assign_workers(all_workers, buckets, claimed, seeds, shed, money, buckets[6], target_pastures, staple)

        orders = []
        target_hands = 6 if day < 5 else (12 if day < 22 else 8)
        if farm.get("hires_today", 0) < target_hands and money > 50:
            orders.append(["HIRE"])
        if seeds.get(staple, 0) < 6 and money > 100:
            orders.append(["BUY_SEED", staple, 10])
        if day >= 5 and day < 22 and buckets[6] > 0 and money > 300:
            orders.append(["BUY_ANIMAL", "COW", 1])
        if money > 3500 and day < 20:
            orders.append(["BUY_LAND"])
        for item, qty in shed.items():
            if item not in {"FERTILIZER", "COW", "SHEEP"} and qty > 2:
                orders.append(["SELL", item, min(qty, 10)])

        return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}

# Universal Fail-Safe Wrapper
def safe_agent_execution(obs, conf, core_strategy_func):
    try:
        # Check remaining overage time to prevent DQ / Timeout
        time_left = _get(obs, "remainingOverageTime", 60)
        if time_left < 5.0:
            # Emergency fast fallback: pass immediately to avoid timeout disqualification
            return {"farmer": ["PASS"], "hands": [], "market": []}
            
        return core_strategy_func(obs, conf)
    except Exception:
        # Prevent crash disqualification
        return {"farmer": ["PASS"], "hands": [], "market": []}