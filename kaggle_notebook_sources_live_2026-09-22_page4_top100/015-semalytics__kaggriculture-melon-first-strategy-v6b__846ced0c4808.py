from collections import deque

BOARD_SIZE = 10
HALF = BOARD_SIZE // 2

SHED_TILES = frozenset([
    (HALF - 1, HALF - 1),  # (4,4)
    (HALF,     HALF - 1),  # (5,4)
    (HALF - 1, HALF),      # (4,5)
    (HALF,     HALF),      # (5,5)
])

FIRST_YIELD = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}
MAX_YIELD_DAY = {"WHEAT": 4, "CARROT": 3, "TOMATO": None, "STRAWBERRY": None, "MELON": 12}
SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ONGOING = {"TOMATO": True, "STRAWBERRY": True}
ANIMAL_COST = {"COW": 400, "SHEEP": 500, "GOOSE": 300}

N_HANDS = 6   # hire cost: 1+1+2+3+5+8 = 20 coins/day total
N_COWS = 2    # 2 cows; saves $400 day-0 vs 3 cows

PASTURE_TILES = frozenset([(4, 3), (3, 4)])

def _tile_zone(x, y):
    if 0 <= x < 5 and 0 <= y < 5:
        if x >= 3: return 0
        return 3 - x
    elif 5 <= x <= 9 and 0 <= y < 5:
        if x <= 6: return 4
        if x <= 8: return 5
        return 6
    return -1

ZONE_TILE_COUNTS = [8, 5, 5, 5, 10, 10, 5]

def bfs_first_move(start, goal, board_size=BOARD_SIZE):
    if start == goal:
        return None
    visited = {start}
    q = deque([(start, None)])
    dirs = [("NORTH", 0, -1), ("SOUTH", 0, 1), ("EAST", 1, 0), ("WEST", -1, 0)]
    while q:
        (x, y), first = q.popleft()
        for mv, dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < board_size and 0 <= ny < board_size and (nx, ny) not in visited:
                visited.add((nx, ny))
                f = first or mv
                if (nx, ny) == goal:
                    return f
                q.append(((nx, ny), f))
    return None

def mdist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def is_plant(tile): return isinstance(tile, dict) and tile.get("kind") == "PLANT"
def is_weed(tile): return isinstance(tile, dict) and tile.get("kind") == "WEED"
def is_animal_tile(tile): return isinstance(tile, dict) and "animal" in tile
def is_empty_pasture(tile): return isinstance(tile, dict) and tile.get("kind") == "PASTURE" and "animal" not in tile
def needs_water(tile): return is_plant(tile) and not tile.get("watered_today", False)

def harvestable(tile, day):
    if not is_plant(tile) or tile.get("yield_units", 0) <= 0:
        return False
    return (day - tile.get("planted_day", 0)) >= FIRST_YIELD.get(tile.get("crop", ""), 99)

def is_exhausted_onetimer(tile, day):
    if not is_plant(tile): return False
    crop = tile.get("crop", "")
    if ONGOING.get(crop, False): return False
    max_day = MAX_YIELD_DAY.get(crop)
    if max_day is None: return False
    return (day - tile.get("planted_day", 0)) > max_day and tile.get("yield_units", 0) == 0

def build_tasks(tiles, day, seeds_avail, plant_crop, max_plant_tiles,
                zone_id, worker_inv, shed):
    tasks = []
    plant_slots = 0
    worker_wheat = worker_inv.get("WHEAT", 0)
    worker_animal = next((a for a in ["COW", "SHEEP", "GOOSE"] if worker_inv.get(a, 0) > 0), None)
    shed_cows = shed.get("COW", 0)
    unfed_count = 0
    empty_pasture_count = 0

    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile == "LOCKED": continue
            if _tile_zone(x, y) != zone_id: continue

            if tile is None:
                if (x, y) in PASTURE_TILES:
                    tasks.append((-5, x, y, ["BUILD_PASTURE"]))
                elif seeds_avail > 0 and plant_slots < max_plant_tiles:
                    tasks.append((4, x, y, ["PLANT", plant_crop]))
                    plant_slots += 1
            elif is_plant(tile):
                if needs_water(tile): tasks.append((0, x, y, ["WATER"]))
                if harvestable(tile, day): tasks.append((1, x, y, ["HARVEST"]))
                if is_exhausted_onetimer(tile, day): tasks.append((3, x, y, ["DIG"]))
            elif is_weed(tile):
                tasks.append((2, x, y, ["DIG"]))
            elif is_empty_pasture(tile):
                empty_pasture_count += 1
                if worker_animal in ("COW", "SHEEP", "GOOSE"):
                    tasks.append((-3, x, y, ["PLACE", worker_animal]))
            elif is_animal_tile(tile):
                if tile.get("yield_units", 0) > 0: tasks.append((1, x, y, ["HARVEST"]))
                if not tile.get("fed_today", False):
                    unfed_count += 1
                    if worker_wheat > 0: tasks.append((-1, x, y, ["FEED"]))
                if not tile.get("cared_today", False): tasks.append((1, x, y, ["CARE"]))

    if unfed_count > 0 and worker_wheat == 0 and shed.get("WHEAT", 0) > 0:
        for sx, sy in [(4, 4), (5, 4), (4, 5), (5, 5)]:
            tasks.append((-2, sx, sy, ["PICKUP", "WHEAT", unfed_count]))
    if empty_pasture_count > 0 and shed_cows > 0 and worker_animal is None:
        for sx, sy in [(4, 4), (5, 4), (4, 5), (5, 5)]:
            tasks.append((-4, sx, sy, ["PICKUP", "COW", 1]))

    return tasks


def worker_action(pos, tasks, claimed, seeds_local, plant_crop):
    wx, wy = pos
    for prio, tx, ty, action in sorted(tasks, key=lambda t: t[0]):
        if (tx, ty) == (wx, wy) and (tx, ty) not in claimed:
            if action[0] == "PLANT" and seeds_local.get(plant_crop, 0) <= 0: continue
            claimed.add((tx, ty))
            if action[0] == "PLANT": seeds_local[plant_crop] = max(0, seeds_local[plant_crop] - 1)
            return action

    best = None
    for prio, tx, ty, action in tasks:
        if (tx, ty) in claimed: continue
        if action[0] == "PLANT" and seeds_local.get(plant_crop, 0) <= 0: continue
        dist = mdist((wx, wy), (tx, ty))
        if best is None or (prio, dist) < (best[0], best[1]):
            best = (prio, dist, tx, ty, action)

    if best is None:
        shed_target = min(SHED_TILES, key=lambda p: mdist((wx, wy), p))
        mv = bfs_first_move((wx, wy), shed_target)
        return [mv] if mv else ["PASS"]

    _, _, tx, ty, action = best
    claimed.add((tx, ty))
    if action[0] == "PLANT": seeds_local[plant_crop] = max(0, seeds_local[plant_crop] - 1)
    if (tx, ty) == (wx, wy): return action
    mv = bfs_first_move((wx, wy), (tx, ty))
    return [mv] if mv else ["PASS"]

def build_market(me, private, day, hour, plant_crop, placed_cows, unlocked):
    orders = []
    shed = private["shed"]
    seeds = private["seeds"]
    money = me["money"]
    tiles = me["tiles"]
    shed_wheat = shed.get("WHEAT", 0)
    WHEAT_RESERVE = N_COWS * 6

    if hour == 0:
        for _ in range(N_HANDS - me["hires_today"]):
            orders.append(["HIRE"])

    for item in ("MILK", "WOOL", "EGG", "TOMATO", "CARROT", "STRAWBERRY", "MELON"):
        qty = shed.get(item, 0)
        if qty > 0 and len(orders) < 10:
            orders.append(["SELL", item, qty])

    if shed_wheat > WHEAT_RESERVE and len(orders) < 10:
        orders.append(["SELL", "WHEAT", shed_wheat - WHEAT_RESERVE])

    if shed_wheat < WHEAT_RESERVE and money > 500 and len(orders) < 9:
        buy_qty = min(WHEAT_RESERVE - shed_wheat, max(0, int((money - 400) // 25)))
        if buy_qty > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", buy_qty])

    cows_total = placed_cows + shed.get("COW", 0)
    if cows_total < N_COWS and money > 1500 and len(orders) < 9:
        need = N_COWS - cows_total
        if money - need * ANIMAL_COST["COW"] > 300:
            orders.append(["BUY_ANIMAL", "COW", need])

    planted = sum(1 for row in tiles for t in row if is_plant(t))
    ne_unlocked = "NE" in unlocked
    target_tiles = (25 - len(PASTURE_TILES)) + (25 if ne_unlocked else 0)
    slots_wanted = max(0, target_tiles - planted)

    if slots_wanted > 0 and len(orders) < 10:
        have = seeds.get(plant_crop, 0)
        empty = sum(1 for row in tiles for t in row if t is None and row is not None)
        need = min(slots_wanted, empty) - have
        budget = money - 300
        if need > 0 and budget >= SEED_COST[plant_crop]:
            qty = min(need, int(budget // SEED_COST[plant_crop]), 15)
            if qty > 0:
                orders.append(["BUY_SEED", plant_crop, qty])

    return orders[:10]

def agent(obs):
    player = obs["player"]
    day = obs["day"]
    hour = obs["hour"]
    me = obs["farms"][player]
    private = obs["private"]
    tiles = me["tiles"]
    seeds = private["seeds"]
    shed = private["shed"]
    unlocked = me.get("unlocked_quadrants", ["NW"])

    plant_crop = "MELON"

    placed_cows = sum(
        1 for row in tiles for t in row
        if isinstance(t, dict) and t.get("animal") == "COW"
    )

    market = build_market(me, private, day, hour, plant_crop, placed_cows, unlocked)

    seeds_local = dict(seeds)
    claimed = set()
    inventories = private["inventories"]
    worker_positions = [tuple(me["farmer"])] + [tuple(h) for h in me["hands"]]
    ne_unlocked = "NE" in unlocked

    actions = []
    for idx, pos in enumerate(worker_positions):
        zone_id = min(idx, 6)
        if zone_id >= 4 and not ne_unlocked:
            zone_id = zone_id - 3  # overflow NE workers back to NW zones 1-3
        zone_cap = ZONE_TILE_COUNTS[zone_id] if zone_id < len(ZONE_TILE_COUNTS) else 5
        worker_inv = inventories[idx] if idx < len(inventories) else {}

        zone_tasks = build_tasks(
            tiles, day, seeds_local.get(plant_crop, 0),
            plant_crop, zone_cap, zone_id, worker_inv, shed
        )
        act = worker_action(pos, zone_tasks, claimed, seeds_local, plant_crop)
        actions.append(act)

    return {
        "farmer": actions[0],
        "hands": actions[1:],
        "market": market,
    }