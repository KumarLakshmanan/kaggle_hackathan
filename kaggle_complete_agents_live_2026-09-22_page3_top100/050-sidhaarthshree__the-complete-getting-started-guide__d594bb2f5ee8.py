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