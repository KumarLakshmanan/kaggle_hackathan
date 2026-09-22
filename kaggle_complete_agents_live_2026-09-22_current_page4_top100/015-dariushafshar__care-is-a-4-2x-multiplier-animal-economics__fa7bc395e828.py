"""CARE-first animal husbandry agent.

A deliberately small agent that does one thing: keep a mixed herd fed, cared for and
harvested every single day. It grows no crops and runs no clever market model.
"""

SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
HERD = [("COW", 4), ("SHEEP", 3)]          # two species on purpose: two price curves
# NW is the only quadrant unlocked at the start, so every spot must satisfy x<5 and y<5.
# Ordered by walking distance from the shed-access tile (4,4).
PASTURE_SPOTS = [(4, 3), (3, 4), (3, 3), (4, 2), (2, 4), (2, 3), (3, 2), (4, 1)]
PRODUCTS = ("MILK", "WOOL", "EGG", "FERTILIZER")
CARE_ENABLED = True   # flip to False for the ablation


def _step(pos, target):
    x, y = pos
    tx, ty = target
    if x < tx: return "EAST"
    if x > tx: return "WEST"
    if y < ty: return "SOUTH"
    if y > ty: return "NORTH"
    return None


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def agent(obs):
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    tiles = me["tiles"]
    shed = priv["shed"]
    money = me["money"]
    invs = priv["inventories"]

    placed = {}
    empty_pastures = []
    animal_tiles = []
    free_spots = []
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if isinstance(t, dict) and "animal" in t:
                placed[t["animal"]] = placed.get(t["animal"], 0) + 1
                animal_tiles.append(((x, y), t))
            elif isinstance(t, dict) and t.get("kind") == "PASTURE":
                empty_pastures.append((x, y))
            elif t is None and (x, y) in PASTURE_SPOTS:
                free_spots.append((x, y))

    n_target = sum(n for _, n in HERD)
    n_structures = len(empty_pastures) + sum(placed.values())
    shed_animals = sum(shed.get(a, 0) for a, _ in HERD)

    # ---------------- market ----------------
    market = []
    carried_wheat = sum(i.get("WHEAT", 0) for i in invs)
    total_wheat = shed.get("WHEAT", 0) + carried_wheat
    n_alive = sum(placed.values())
    # keep roughly three days of feed in stock
    if total_wheat < max(8, n_alive * 3) and money > 600:
        market.append(["BUY_PRODUCT", "WHEAT", 12])

    for animal, target in HERD:
        if placed.get(animal, 0) + shed.get(animal, 0) < target and money > 1400:
            market.append(["BUY_ANIMAL", animal, 1])
            break

    for product in ("MILK", "WOOL"):
        held = shed.get(product, 0)
        if held > 0:
            market.append(["SELL", product, min(held, 4)])   # drip, never dump

    if obs["day"] >= 1 and me["hires_today"] < 3 and money > 2000:
        market.append(["HIRE"])

    # ---------------- workers ----------------
    workers = [tuple(me["farmer"])] + [tuple(p) for p in me["hands"]]
    claimed = set()
    ops = []

    for wi, pos in enumerate(workers):
        inv = invs[wi] if wi < len(invs) else {}
        x, y = pos
        here = tiles[y][x]
        carrying_animal = next((a for a, _ in HERD if inv.get(a, 0) > 0), None)
        job = None

        # --- act where we stand ---
        if isinstance(here, dict) and "animal" in here:
            if here.get("yield_units", 0) > 0:
                job = ["HARVEST"]
            elif not here.get("fed_today") and inv.get("WHEAT", 0) > 0:
                job = ["FEED"]
            elif CARE_ENABLED and not here.get("cared_today"):
                job = ["CARE"]
        elif carrying_animal and isinstance(here, dict) and here.get("kind") == "PASTURE":
            job = ["PLACE", carrying_animal, 1]
        elif here is None and (x, y) in PASTURE_SPOTS and n_structures < n_target:
            job = ["BUILD_PASTURE"]
        elif pos in SHED_TILES:
            if any(inv.get(p, 0) for p in PRODUCTS):
                job = ["DROP"]
            elif not carrying_animal and shed_animals > 0 and empty_pastures:
                for a, _ in HERD:
                    if shed.get(a, 0) > 0:
                        job = ["PICKUP", a, 1]
                        shed[a] -= 1
                        break
            elif inv.get("WHEAT", 0) < 3 and shed.get("WHEAT", 0) > 0:
                job = ["PICKUP", "WHEAT", 4]

        # --- otherwise, go somewhere useful ---
        if job is None:
            target = None
            if carrying_animal and empty_pastures:
                target = min((p for p in empty_pastures if p not in claimed),
                             key=lambda p: _dist(p, pos), default=None)
            if target is None and not carrying_animal and shed_animals > 0 and empty_pastures:
                target = min(SHED_TILES, key=lambda s: _dist(s, pos))
            if target is None and n_structures < n_target and free_spots:
                target = min((s for s in free_spots if s not in claimed),
                             key=lambda s: _dist(s, pos), default=None)
            if target is None and inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0:
                target = min(SHED_TILES, key=lambda s: _dist(s, pos))
            if target is None:
                best, best_score = None, 0.0
                for (ax, ay), t in animal_tiles:
                    if (ax, ay) in claimed:
                        continue
                    score = 0.0
                    if t.get("yield_units", 0) > 0: score += 3
                    if not t.get("fed_today") and inv.get("WHEAT", 0) > 0: score += 2
                    if CARE_ENABLED and not t.get("cared_today"): score += 1
                    score -= 0.1 * _dist((ax, ay), pos)
                    if score > best_score:
                        best, best_score = (ax, ay), score
                target = best
            if target is None and any(inv.get(p, 0) for p in PRODUCTS):
                target = min(SHED_TILES, key=lambda s: _dist(s, pos))
            if target is not None:
                claimed.add(target)
                mv = _step(pos, target)
                job = [mv] if mv else ["PASS"]
            else:
                job = ["PASS"]

        ops.append(job)

    return {"farmer": ops[0], "hands": ops[1:], "market": market[:10]}
