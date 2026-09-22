"""Kaggriculture: sell into the hole, not into the market.

The whole game turns on a sign. Market inventory starts at I0 = 10,000 and moves
both ways: players selling push it up, the town eating pulls it down. Price is a
function of the *distance* from I0, and for most products the lower branch is far
steeper than the upper one. So what a product is worth is set not by its base
price but by how much the town has already eaten out of it, and by the shape of
that lower curve.

Computed from the engine's own market_price, accounting for shops unlocking
gradually (days 3, 6, 9, ... up to 8 instances, drawn with replacement):

    product       town eats     fill the hole     dump into a flat market
    STRAWBERRY        426          $100,445           $4,173     (x24)
    MILK              327          $ 86,662           $6,432     (x13.5)
    WOOL              228          $ 54,340
    WHEAT             525          $ 21,152
    TOMATO            228          $ 16,812
    CARROT            327          $ 13,246
    EGG               228          $ 12,972
    MELON              30          $  8,184

Per tile per season, after seed or livestock cost:

    cow $8,333    sheep $7,343    melon $4,092    goose $2,820
    strawberry $1,674    wheat $1,209    tomato $737

Hence the layout: pastures with cows and sheep first, then melon, then geese,
with wheat pulled in behind them as feed. Strawberry is the most valuable thing
to *sell* and a mediocre thing to *grow* -- a plant yields four units in
seventeen days.

The trading rule: sell only while the price is above base, because once
inventory reaches I0 the hole is full and the next unit goes up the shallow
branch, where the same strawberry is worth a tenth as much. The agent
re-implements market_price to work out exactly how many units it can sell before
crossing that threshold, and holds the rest. Two corrections make it survive
contact with an opponent:

  * the threshold decays through the season, because the hole is shared and
    holding out for a price that never comes leaves you with a full shed;
  * liquidity beats price -- below two days of running costs it sells whatever
    it has at whatever it fetches.

On the last days it dumps everything: unsold goods do not count.
"""


P = {
    # Target layout, from allocating tiles greedily by marginal revenue: while
    # the next cow tile pays more than the next sheep tile, take the cow. The
    # order comes out cows -> sheep -> melon -> geese, with wheat pulled in as
    # feed. These caps were then trimmed by the sweep: fewer head than the
    # static optimum, because servicing an animal costs four actions a day.
    "cows": 8,
    "sheep": 9,
    "melons": 16,
    "geese": 10,
    "wheat_per_animal": 0.5,   # one wheat tile feeds about one head
    "buy_animal_until": 22,     # later than this a cow never pays back: first milk on day 8
    "plant_until": {"MELON": 16, "WHEAT": 26},
    # --- trading
    # The hole is shared with the opponent: whoever sells first takes the
    # premium. So the threshold decays through the season -- holding is only
    # worth it while there are days left for the town to eat more.
    "floor_start": 1.15,   # early on, sell only above base
    "floor_end": 0.8,      # by the end, at almost any price
    # Holding stock is a luxury for the solvent. The market is shared: if the
    # opponent is filling the hole, the price never recovers, and a farm with
    # no cash does nothing. Below this many days of running costs, sell
    # everything at whatever it fetches.
    "cash_floor_days": 2,
    "dump_day": 28,        # from this day, dump everything: leftovers score nothing
    "wheat_days": 2,       # days of feed kept in the shed
    # --- labour and money
    "hands": 10,
    "hire_max": 250,
    "carry": 6,
    "shed_cap": 55,
    "hold_until": 30,     # below this shed load, holding is free
    "drop_load": 3,
    "evening": 17,
    "hunger": 4,
    "runway": 3,
    "hire_day_cost": 200,
    "land_day_min": 1,
    "land_free_left": 8,
}

CROPS = {
    "WHEAT":      {"seed": 10, "first": 2, "max_day": 4,  "ongoing": False},
    "CARROT":     {"seed": 20, "first": 2, "max_day": 3,  "ongoing": False},
    "TOMATO":     {"seed": 50, "first": 8, "max_day": 8,  "ongoing": True, "interval": 1, "n": 4},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_day": 10, "ongoing": True, "interval": 2, "n": 4},
    "MELON":      {"seed": 80, "first": 10, "max_day": 12, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "struct": "COOP",    "product": "EGG"},
    "COW":   {"cost": 400, "struct": "PASTURE", "product": "MILK"},
    "SHEEP": {"cost": 500, "struct": "PASTURE", "product": "WOOL"},
}
# from the engine's MARKET_PARAMS; needed to work out how much can be sold
MP = {
    "WHEAT":      (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT":     (35, 450, "log", 0.20, "sqrt", 0.70),
    "TOMATO":     (60, 200, "linear", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON":      (250, 300, "log", 0.20, "sq", 3.60),
    "EGG":        (50, 332, "linear", 0.40, "log", 0.20),
    "MILK":       (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL":       (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
I0 = 10000
PRODUCTS = list(MP)
SELLABLE = ["MILK", "WOOL", "STRAWBERRY", "MELON", "EGG", "TOMATO",
            "CARROT", "FERTILIZER", "WHEAT"]


def _shape(f, x):
    import math
    x = max(0.0, x)
    if f == "linear":
        return x
    if f == "sq":
        return x * x
    if f == "sqrt":
        return math.sqrt(x)
    if f == "log":
        return math.log(1.0 + x)
    return x


def price_of(item, inv):
    base, T, bf, bt, af, at = MP[item]
    if inv < I0:
        amp = bt * base / _shape(bf, T)
        p = base + amp * _shape(bf, I0 - inv)
    else:
        amp = at * base / _shape(af, T)
        p = base - amp * _shape(af, inv - I0)
    return max(1, int(round(p)))


def sellable_units(item, inv, floor_price):
    """How many units go before the price drops below floor_price.

    Each sale raises inventory by one, so the price falls as the order fills.
    This walks the curve exactly the way the engine does.
    """
    n = 0
    while n < 200:
        if price_of(item, inv + n) < floor_price:
            break
        n += 1
    return n


def _get(d, key, default=None):
    if isinstance(d, dict):
        return d.get(key, default)
    return getattr(d, key, default)


def _shed_tiles(n):
    h = n // 2
    return [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]


def _step(fx, fy, tx, ty):
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    if fy > ty:
        return "NORTH"
    return None


def _d(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def agent(obs):
    player = _get(obs, "player", 0)
    farms = _get(obs, "farms", [])
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    private = _get(obs, "private", {}) or {}
    shed = dict(_get(private, "shed", {}) or {})
    seeds = dict(_get(private, "seeds", {}) or {})
    invs = [dict(i) if i else {} for i in (_get(private, "inventories", [{}]) or [{}])]
    tiles = farm["tiles"]
    n = len(tiles)
    day, hour = _get(obs, "day", 0), _get(obs, "hour", 0)
    money = farm["money"]
    mkt = _get(obs, "market", {}) or {}
    inv_mkt = _get(mkt, "inventory", {}) or {}
    prices = _get(mkt, "prices", {}) or {}
    wheat_price = max(1, prices.get("WHEAT", 25))

    units = [tuple(farm["farmer"])] + [tuple(p) for p in farm.get("hands", [])]
    n_units = len(units)
    while len(invs) < n_units:
        invs.append({})
    shed_access = _shed_tiles(n)
    centre = shed_access[0]

    # -------------------------------------------------------- read the farm
    animals, structs, free, weeds, plants = [], [], [], [], []
    for y in range(n):
        for x in range(n):
            t = tiles[y][x]
            if t is None:
                free.append((x, y))
            elif t == "LOCKED":
                continue
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "WEED":
                    weeds.append((x, y))
                elif k == "PLANT":
                    plants.append((x, y, t))
                elif "animal" in t:
                    animals.append((x, y, t))
                else:
                    structs.append((x, y, k))       # empty coop or pasture
    free.sort(key=lambda p: _d(p, centre))
    structs.sort(key=lambda s: _d((s[0], s[1]), centre))

    have = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
    unfed = []
    for (x, y, t) in animals:
        have[t["animal"]] += 1
        if not t.get("fed_today"):
            unfed.append((x, y))
    for a in ANIMALS:
        have[a] += shed.get(a, 0) + sum(i.get(a, 0) for i in invs)

    crop_count = {}
    for (x, y, t) in plants:
        crop_count[t["crop"]] = crop_count.get(t["crop"], 0) + 1

    n_animals = sum(have.values())
    wheat_carried = sum(i.get("WHEAT", 0) for i in invs)
    wheat_have = shed.get("WHEAT", 0) + wheat_carried
    shed_total = sum(shed.values())
    day_cost = P["hire_day_cost"] + n_animals * wheat_price
    reserve = P["runway"] * day_cost

    # ------------------------------------------------------------ the market
    # Only 10 orders per turn are accepted and the rest are silently dropped,
    # so the queue is built by priority rather than in the order the code
    # happens to be written. Feed goes first: a shed full of unsold milk once
    # blocked a wheat purchase and the whole herd walked off in two days.
    market = []
    dumping = day >= P["dump_day"]

    # feed: one wheat per head per day; two missed days and it is gone for good
    wheat_target = max(2, int(n_animals * P["wheat_days"]))
    if wheat_have < wheat_target and shed_total < 95 and money > wheat_price:
        want = min(wheat_target - wheat_have, 95 - shed_total,
                   int(money // wheat_price))
        if want > 0:
            market.append(["BUY_PRODUCT", "WHEAT", want])

    # Sell into the hole: below I0 every unit fetches a premium, above it the
    # same strawberry is worth a tenth as much. But holding only works while
    # there is somewhere to put things -- the shed holds 100 and whatever does
    # not fit at nightfall is simply discarded. So the fuller the shed, the
    # lower the price we are willing to accept.
    t = min(1.0, day / max(1, P["dump_day"]))
    floor_day = P["floor_start"] + (P["floor_end"] - P["floor_start"]) * t
    if money < P["cash_floor_days"] * day_cost:
        floor_day = 0.0        # liquidity beats price
    slack = max(0.0, min(1.0, (shed_total - P["hold_until"]) /
                         max(1, 95 - P["hold_until"])))
    floor_mult = floor_day * (1.0 - slack)
    order = sorted((i for i in SELLABLE if shed.get(i, 0) > 0),
                   key=lambda i: -prices.get(i, 0) * shed.get(i, 0))
    for item in order:
        n_have = shed.get(item, 0)
        if item == "WHEAT":
            n_have -= wheat_target
            if n_have <= 0:
                continue
        if dumping:
            market.append(["SELL", item, n_have])
            continue
        base = MP[item][0]
        allow = sellable_units(item, inv_mkt.get(item, I0), base * floor_mult)
        k = min(n_have, allow)
        if k > 0:
            market.append(["SELL", item, k])

    # Hands: the fib(n) price resets every morning, so ten cost $143. Hired
    # across two turns so the hires do not eat the whole order queue at once.
    if hour in (0, 1) and len(market) < 9:
        a, b = 1, 1
        for _ in range(farm.get("hires_today", 0)):
            a, b = b, a + b
        budget = money - n_animals * wheat_price * 2
        while len(market) < 9 and farm.get("hires_today", 0) + \
                sum(1 for o in market if o[0] == "HIRE") < P["hands"]:
            if a > P["hire_max"] or a > budget:
                break
            market.append(["HIRE"])
            budget -= a
            a, b = b, a + b

    # Feed wheat comes before any investment. A herd you cannot feed walks off
    # in two days, and that is the only irreversible loss in the game.
    wheat_want = int(round(n_animals * P["wheat_per_animal"])) + 2
    wheat_planted = crop_count.get("WHEAT", 0) + seeds.get("WHEAT", 0)
    if wheat_planted < wheat_want and day <= P["plant_until"]["WHEAT"] and free:
        k = min(wheat_want - wheat_planted, len(free), 10,
                int(money // CROPS["WHEAT"]["seed"]))
        if k > 0:
            market.append(["BUY_SEED", "WHEAT", k])
            money -= k * 10

    # Animals pay best per tile and per dollar; bought strictly in marginal-
    # revenue order, and only once there is feed growing for them.
    room = len(free) + len(structs)
    # the herd never grows faster than the feed under it
    feed_ok = wheat_planted >= n_animals * P["wheat_per_animal"]
    if room > 0 and shed_total < 90 and day <= P["buy_animal_until"]:
        for kind, cap in (("COW", P["cows"]), ("SHEEP", P["sheep"]),
                          ("GOOSE", P["geese"])):
            if have[kind] >= cap or (kind == "GOOSE" and not feed_ok):
                continue
            cost = ANIMALS[kind]["cost"]
            afford = int((money - reserve) // (cost + P["runway"] * wheat_price))
            k = max(0, min(afford, cap - have[kind], room, 4))
            if k > 0:
                market.append(["BUY_ANIMAL", kind, k])
                money -= k * cost
                room -= k
                break

    # Melon: its hole is only 30 units, but the glut curve starts from $250,
    # so the first hundred still sell dear. A handful of tiles is right.
    melon_planted = crop_count.get("MELON", 0) + seeds.get("MELON", 0)
    if (melon_planted < P["melons"] and day <= P["plant_until"]["MELON"]
            and len(free) > 2 and money - reserve > 400):
        k = min(P["melons"] - melon_planted, len(free) - 2, 4,
                int((money - reserve) // CROPS["MELON"]["seed"]))
        if k > 0:
            market.append(["BUY_SEED", "MELON", k])
            money -= k * 80

    # Land: the 25 NW tiles hold neither the herd nor the feed for it.
    n_extra = len(farm.get("unlocked_quadrants", ["NW"])) - 1
    land_price = [1000, 2000, 4000][n_extra] if n_extra < 3 else None
    if (land_price and day >= P["land_day_min"] and day <= 22
            and len(free) <= P["land_free_left"]
            and money - land_price >= reserve + 600):
        market.append(["BUY_LAND"])

    market = market[:10]

    # ------------------------------------------------------------- the tasks
    # Every job at an animal is done from its own square: arrive, feed, care,
    # harvest, collect. So tasks are grouped by tile, and a unit already
    # standing on one finishes it before moving. Without this rule 83% of all
    # unit-turns went into walking, because units retargeted every turn.
    pending = {}

    def add(p, op):
        pending.setdefault(p, []).append(op)

    for (x, y, t) in animals:
        p = (x, y)
        if not t.get("fed_today"):
            add(p, ["FEED"])
        if t.get("yield_units", 0) > 0:
            add(p, ["HARVEST"])
        if not t.get("cared_today"):
            add(p, ["CARE"])          # +1 on the next scheduled yield
        if t.get("fertilizer_available"):
            add(p, ["COLLECT_FERTILIZER"])
    for (x, y, t) in plants:
        p = (x, y)
        cd = CROPS[t["crop"]]
        age = day - t["planted_day"]
        if not t.get("watered_today"):
            add(p, ["WATER"])
        if t.get("yield_units", 0) > 0:
            ripe = age >= cd["max_day"] if not cd["ongoing"] else age >= cd["first"]
            if ripe:
                add(p, ["HARVEST"])
    for (x, y) in weeds:
        add((x, y), ["DIG"])

    # what to build on the free tiles
    need_struct = {"PASTURE": max(0, shed.get("COW", 0) + shed.get("SHEEP", 0)
                                  + sum(i.get("COW", 0) + i.get("SHEEP", 0) for i in invs)
                                  - sum(1 for s in structs if s[2] == "PASTURE")),
                   "COOP": max(0, shed.get("GOOSE", 0)
                               + sum(i.get("GOOSE", 0) for i in invs)
                               - sum(1 for s in structs if s[2] == "COOP"))}
    plantable = []
    bi = 0
    for (x, y) in free:
        if need_struct["PASTURE"] > 0:
            add((x, y), ["BUILD_PASTURE"])
            need_struct["PASTURE"] -= 1
        elif need_struct["COOP"] > 0:
            add((x, y), ["BUILD_COOP"])
            need_struct["COOP"] -= 1
        else:
            plantable.append((x, y))
        bi += 1

    # --------------------------------------------------- assigning the units
    actions = [None] * n_units
    order = sorted(range(n_units), key=lambda i: _d(units[i], centre))
    unfed_left = set(unfed)
    targeted = set()
    seeds_left = dict(seeds)
    struct_free = {"COOP": [(x, y) for (x, y, k) in structs if k == "COOP"],
                   "PASTURE": [(x, y) for (x, y, k) in structs if k == "PASTURE"]}
    plant_left = list(plantable)
    wheat_shed = shed.get("WHEAT", 0)
    wheat_en_route = wheat_carried
    animals_shed = {a: shed.get(a, 0) for a in ANIMALS}

    def crop_for_tile():
        """What to plant on the next free tile."""
        for crop in ("WHEAT", "MELON"):
            if seeds_left.get(crop, 0) > 0:
                return crop
        return None

    for idx in order:
        pos, inv = units[idx], invs[idx]
        has_wheat = inv.get("WHEAT", 0) > 0
        carried_animal = next((a for a in ANIMALS if inv.get(a, 0) > 0), None)
        load = sum(v for k, v in inv.items()
                   if k not in ("WHEAT",) and k not in ANIMALS)
        at_shed = pos in shed_access

        # 1. finish the tile we are standing on
        here = pending.get(pos)
        if here:
            op = None
            for cand in here:
                if cand[0] == "FEED" and not has_wheat:
                    continue
                op = cand
                break
            if op is not None:
                here.remove(op)
                if op[0] == "FEED":
                    inv["WHEAT"] = inv.get("WHEAT", 0) - 1
                    unfed_left.discard(pos)
                actions[idx] = list(op)
                continue
        if carried_animal:
            st = ANIMALS[carried_animal]["struct"]
            if pos in struct_free[st]:
                struct_free[st].remove(pos)
                inv[carried_animal] = inv.get(carried_animal, 0) - 1
                actions[idx] = ["PLACE", carried_animal]
                continue
        if pos in plant_left:
            crop = crop_for_tile()
            if crop:
                plant_left.remove(pos)
                seeds_left[crop] -= 1
                crop_count[crop] = crop_count.get(crop, 0) + 1
                actions[idx] = ["PLANT", crop]
                continue

        # 2. a trip to the shed
        want = None
        pending_animal = next((a for a, k in animals_shed.items() if k > 0
                               and struct_free[ANIMALS[a]["struct"]]), None)
        if unfed_left and not has_wheat and wheat_shed > 0:
            want = "WHEAT"
        elif pending_animal and not carried_animal and not has_wheat:
            want = pending_animal
        elif load >= P["drop_load"] or (hour >= P["evening"] and load > 0):
            want = "DROP"
        if want:
            if at_shed:
                if want == "WHEAT":
                    take = min(P["carry"], wheat_shed)
                    actions[idx] = ["PICKUP", "WHEAT", take]
                    wheat_shed -= take
                    wheat_en_route += take
                elif want == "DROP":
                    actions[idx] = ["DROP"]
                else:
                    actions[idx] = ["PICKUP", want, 1]
                    animals_shed[want] -= 1
            else:
                tgt = min(shed_access, key=lambda p: _d(pos, p))
                actions[idx] = [_step(*pos, *tgt)]
            continue

        # 3. from mid-morning, the unfed outrank everything else
        if has_wheat and unfed_left and hour >= P["hunger"]:
            tgt = min(unfed_left, key=lambda p: _d(pos, p))
            unfed_left.discard(tgt)
            mv = _step(*pos, *tgt)
            actions[idx] = [mv] if mv else ["FEED"]
            continue

        # 4. head for the densest nearby tile
        best, best_key = None, None
        for p, ops in pending.items():
            if not ops or p in targeted:
                continue
            if all(o[0] == "FEED" for o in ops) and not has_wheat:
                continue
            d = _d(pos, p)
            key = (-len(ops) / (d + 1), d)
            if best_key is None or key < best_key:
                best, best_key = p, key
        if best is None and carried_animal:
            st = struct_free[ANIMALS[carried_animal]["struct"]]
            if st:
                best = min(st, key=lambda p: _d(pos, p))
        if best is None and plant_left and crop_for_tile():
            best = min(plant_left, key=lambda p: _d(pos, p))
        if best is None:
            if load:
                tgt = min(shed_access, key=lambda p: _d(pos, p))
                mv = _step(*pos, *tgt)
                actions[idx] = [mv] if mv else ["DROP"]
            else:
                actions[idx] = ["PASS"]
            continue
        targeted.add(best)
        mv = _step(*pos, *best)
        actions[idx] = [mv] if mv else ["PASS"]

    for i in range(n_units):
        if not actions[i] or actions[i][0] is None:
            actions[i] = ["PASS"]

    return {"farmer": actions[0], "hands": actions[1:], "market": market}
