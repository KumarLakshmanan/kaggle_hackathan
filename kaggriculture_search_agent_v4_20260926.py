"""Standalone, observation-driven Kaggriculture search agent.

This is an experimental alternative to main.py, not a submission artifact.
At the start of each day a bounded beam search compares *complete* visible
production commitments plus several multi-tile investment bundles.  Its evaluation
simulates both players' effect on shared prices under three unknown-shop and
rival-output scenarios.  Workers then execute the selected plan and replan
from observations when reality differs from the forecast.

Only public observations and this player's private inventory are read.  No
episode seed, future shop sequence, replay tape, or incumbent route is used.
"""

from __future__ import annotations

import math


CROPS = {
    "WHEAT": (10, 2, 4, 0, 6),
    "CARROT": (20, 2, 3, 0, 4),
    "TOMATO": (50, 8, 8, 1, 4),
    "STRAWBERRY": (100, 10, 10, 2, 4),
    "MELON": (80, 10, 12, 0, 6),
}
ANIMALS = {
    "GOOSE": (300, "COOP", 4, 1, 4, "EGG"),
    "COW": (400, "PASTURE", 8, 2, 6, "MILK"),
    "SHEEP": (500, "PASTURE", 6, 3, 6, "WOOL"),
}
KINDS = tuple(CROPS) + tuple(ANIMALS)
BUNDLES = (4, 4, 4, 4, 4, 2, 2, 2)
PRODUCTS = tuple(CROPS) + ("EGG", "MILK", "WOOL", "FERTILIZER")
PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", .8, "log", .2),
    "CARROT": (35, 10000, 450, "hinge", 1., "sqrt", .7),
    "TOMATO": (60, 10000, 200, "hinge", .4, "sqrt", .6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", .7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", .2, "sq", 3.6),
    "EGG": (50, 10000, 332, "hinge", .4, "log", .2),
    "MILK": (160, 10000, 122, "sqrt", .6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", .2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", .4, "linear", .4),
}
SHOPS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
STATES = {}
STATS = {"plans": 0, "nodes": 0, "investments": 0, "passes": 0,
         "jobs": 0, "returns": 0, "missing_supply": 0}


def _shape(kind, x, throughput):
    x = max(0., x)
    if kind == "sqrt":
        return math.sqrt(x)
    if kind == "sq":
        return x*x
    if kind == "log":
        return math.log1p(x)
    if kind == "log10":
        return math.log10(1+x)
    if kind == "hinge":
        u = x/max(1., throughput)
        return u+8.*max(0., u-1.)**2
    return x


def _quote(item, stock, overrides=None):
    base, anchor, throughput, below, below_target, above, above_target = PARAMS[item]
    if overrides and item in overrides:
        patch = overrides[item]
        base = patch.get("base", base)
        anchor = patch.get("I0", anchor)
        throughput = patch.get("T", throughput)
        below = patch.get("below_func", below)
        below_target = patch.get("below_target", below_target)
        above = patch.get("above_func", above)
        above_target = patch.get("above_target", above_target)
    if stock < anchor:
        kind, target, gap = below, below_target, anchor-stock
        sign = 1
    else:
        kind, target, gap = above, above_target, stock-anchor
        sign = -1
    denominator = _shape(kind, throughput, throughput)
    price = base+sign*base*target*_shape(kind, gap, throughput)/max(1.e-9, denominator)
    return max(1, int(round(price)))


def _distance(a, b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])


def _towards(a, b):
    if a[0] < b[0]:
        return ["EAST"]
    if a[0] > b[0]:
        return ["WEST"]
    if a[1] < b[1]:
        return ["SOUTH"]
    if a[1] > b[1]:
        return ["NORTH"]
    return None


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a+b
    return a


def _new_flow(horizon):
    return {item: [0.] * horizon for item in PRODUCTS}


def _add_flow(dst, src, n=1):
    for item in PRODUCTS:
        a, b = dst[item], src[item]
        for d in range(len(a)):
            a[d] += n*b[d]


def _asset_flow(tile, today, horizon, fresh=False):
    """Forecast saleable output at day granularity, discounted for execution."""
    flow = _new_flow(horizon)
    animal = tile.get("animal")
    if animal in ANIMALS:
        _, _, first, interval, cap, product = ANIMALS[animal]
        placed = int(tile.get("placed_day", today))
        held = int(tile.get("yield_units", 0))
        bank = int(tile.get("pending_care_bonus", 0))
        if held:
            flow[product][0] += held*.92
        if tile.get("fertilizer_available"):
            flow["FERTILIZER"][0] += .75
        for d in range(horizon-1):
            date = today+d
            flow["WHEAT"][d] -= .94
            flow["FERTILIZER"][d+1] += .68
            age = date+1-placed
            if age >= first and (age-first) % interval == 0:
                flow[product][d+1] += min(cap, 1+bank)*.78
                bank = 0
            bank = min(cap, bank+1)
        return flow
    crop = tile.get("crop")
    if crop not in CROPS:
        return flow
    _, first, peak, interval, cap = CROPS[crop]
    planted = int(tile.get("planted_day", today))
    age = today-planted
    held = int(tile.get("yield_units", 0 if interval else 1))
    if interval:
        if held and age >= first:
            flow[crop][0] += held*.90
        for n in range(cap):
            due = planted+first+n*interval-today
            if 0 < due < horizon:
                flow[crop][due] += .88
    else:
        harvest_age = 10 if crop == "MELON" else peak
        due = max(today, planted+harvest_age)-today
        if due < horizon and age <= peak+2:
            expected = min(cap, held+max(0, harvest_age-max(0, age)//2))
            flow[crop][due] += expected*.89
    return flow


class Search:
    """Small beam search over additions to the observed committed portfolio."""

    def __init__(self, obs, cfg):
        self.obs, self.cfg = obs, cfg
        self.player = int(obs.get("player", 0))
        self.me = obs["farms"][self.player]
        self.day = int(obs.get("day", int(obs.get("step", 0))//int(cfg.get("turnsPerDay", 24))))
        self.final_day = (int(cfg.get("episodeSteps", 720))-2)//int(cfg.get("turnsPerDay", 24))
        self.horizon = self.final_day-self.day+1
        self.money = float(self.me["money"])
        self.overrides = cfg.get("marketParams")
        self.existing = [0]*len(KINDS)
        self.own = _new_flow(self.horizon)
        self.rival = _new_flow(self.horizon)
        for seat, farm in enumerate(obs["farms"]):
            for row in farm["tiles"]:
                for tile in row:
                    if not isinstance(tile, dict):
                        continue
                    item = tile.get("animal", tile.get("crop"))
                    if item not in KINDS:
                        continue
                    if seat == self.player:
                        self.existing[KINDS.index(item)] += 1
                    _add_flow(self.own if seat == self.player else self.rival,
                              _asset_flow(tile, self.day, self.horizon))
        self.profiles = [_asset_flow({("crop" if k in CROPS else "animal"): k,
                                      ("planted_day" if k in CROPS else "placed_day"): self.day},
                                     self.day, self.horizon, True) for k in KINDS]
        self.stock = obs["market"]["inventory"]
        self.demand = self._demand()
        self.open_land = 25*len(self.me.get("unlocked_quadrants", ["NW"]))
        self.occupied = sum(self.existing)
        self.cache = {}

    def _demand(self):
        tpd = int(self.cfg.get("turnsPerDay", 24))
        center_rate = tpd/max(1, int(self.cfg.get("townCenterSellInterval", 24)))
        shop_rate = tpd/max(1, int(self.cfg.get("townShopSellInterval", 4)))
        known = {k: (0. if k == "FERTILIZER" else center_rate) for k in PRODUCTS}
        for shop in self.obs.get("town", {}).get("unlocked_shops", []):
            goods = SHOPS.get(shop, ())
            for k in goods:
                known[k] += shop_rate*(2 if len(goods) == 1 else 1)
        mean = {k: 0. for k in PRODUCTS}
        for goods in SHOPS.values():
            for k in goods:
                mean[k] += shop_rate*(2 if len(goods) == 1 else 1)/len(SHOPS)
        unlock = max(1, int(self.cfg.get("townShopUnlockInterval", 3)))
        already = len(self.obs.get("town", {}).get("unlocked_shops", []))
        return {k: [known[k]+mean[k]*min(8-already,
                         (self.day+d)//unlock-self.day//unlock)
                    for d in range(self.horizon)] for k in PRODUCTS}

    def _capital(self, counts):
        capital = sum(counts[i]*(CROPS[k][0] if k in CROPS else ANIMALS[k][0])
                      for i, k in enumerate(KINDS))
        extra = max(0, self.occupied+sum(counts)-self.open_land)
        land_costs = (1000, 2000, 4000)
        land_buy = (extra+24)//25
        if land_buy > 4-len(self.me.get("unlocked_quadrants", ["NW"])):
            return 1.e9
        for j in range(land_buy):
            capital += land_costs[len(self.me.get("unlocked_quadrants", ["NW"]))-1+j]
        return capital

    def evaluate(self, counts):
        if counts in self.cache:
            return self.cache[counts]
        STATS["nodes"] += 1
        capital = self._capital(counts)
        if capital > max(0., self.money-max(120., self.occupied*9.)):
            self.cache[counts] = -1.e10
            return -1.e10
        own = _new_flow(self.horizon)
        _add_flow(own, self.own)
        for i, n in enumerate(counts):
            if n:
                _add_flow(own, self.profiles[i], n)
        scenarios = []
        for future_shop, rival_scale in ((.55, 1.), (1., 1.12), (1.45, 1.3)):
            margin = -capital
            for item in PRODUCTS:
                stock = float(self.stock.get(item, 10000))
                base_demand = self.demand[item]
                # Shops already open are certain; only later shops are scaled.
                initial = base_demand[0]
                for d in range(self.horizon):
                    demand = initial+(base_demand[d]-initial)*future_shop
                    stock -= demand
                    a = own[item][d]
                    b = self.rival[item][d]*rival_scale
                    quote = _quote(item, stock+(a+b)*.5, self.overrides)
                    margin += (a-b)*quote
                    if quote > 1:
                        stock += a+b
                    else:
                        stock += min(0., a+b)
            scenarios.append(margin)
        # Full-plan throughput cost: each worker can finish about 16 useful
        # actions per day after travel and supply trips. The first worker is
        # free; up to eight cheap hires are modeled in the forecast.
        work = 0.
        for i, k in enumerate(KINDS):
            n = self.existing[i]+counts[i]
            work += n*(.95 if k in CROPS else 3.35)
        peak_workers = 1+min(8, max(0, math.ceil(work/16.)-1))
        overload = max(0., work-peak_workers*16.)
        labor_cost = (peak_workers-1)*4*self.horizon+overload*35*self.horizon
        score = .65*sum(scenarios)/3+.35*min(scenarios)-labor_cost
        self.cache[counts] = score
        return score

    def plan(self):
        zero = (0,)*len(KINDS)
        best, best_score = zero, self.evaluate(zero)
        beam = [(best_score, zero)]
        # Each layer is one whole investment; transpositions are collapsed.
        # Receding-horizon planning makes the next observed day authoritative.
        for _ in range(8):
            children = {}
            for _, counts in beam:
                for i, kind in enumerate(KINDS):
                    if self.horizon <= (CROPS[kind][1]+2 if kind in CROPS else ANIMALS[kind][2]+3):
                        continue
                    if (kind in ANIMALS and self.money < 5000 and
                            sum(counts[5:])+BUNDLES[i] > 4):
                        continue
                    nxt = list(counts)
                    nxt[i] += BUNDLES[i]
                    nxt = tuple(nxt)
                    if nxt not in children:
                        children[nxt] = self.evaluate(nxt)
            if not children:
                break
            beam = sorted(((score, counts) for counts, score in children.items()),
                          reverse=True)[:5]
            if beam[0][0] > best_score+10:
                best_score, best = beam[0]
        # Spend leftover capital with a few single-tile full-plan extensions.
        for _ in range(3):
            alternatives = []
            for i, kind in enumerate(KINDS):
                if self.horizon <= (CROPS[kind][1]+2 if kind in CROPS else ANIMALS[kind][2]+3):
                    continue
                if kind in ANIMALS and self.money < 5000 and sum(best[5:]) >= 4:
                    continue
                nxt = list(best)
                nxt[i] += 1
                nxt = tuple(nxt)
                alternatives.append((self.evaluate(nxt), nxt))
            if not alternatives:
                break
            score, counts = max(alternatives)
            if score <= best_score+10:
                break
            best_score, best = score, counts
        return {kind: self.existing[i]+best[i] for i, kind in enumerate(KINDS)}


class Executor:
    def __init__(self, obs, cfg):
        self.cfg = cfg
        self.player = int(obs.get("player", 0))
        self.day = -1
        self.last_step = -1
        self.jobs = {}
        self.targets = {}

    def read(self, obs):
        self.obs = obs
        self.step = int(obs.get("step", 0))
        self.tpd = int(self.cfg.get("turnsPerDay", 24))
        self.today = self.step//self.tpd
        self.hour = self.step%self.tpd
        self.last = int(self.cfg.get("episodeSteps", 720))-2
        self.final = self.today == self.last//self.tpd
        self.remaining = min(self.last, (self.today+1)*self.tpd-1)-self.step+1
        self.me = obs["farms"][self.player]
        self.tiles = self.me["tiles"]
        self.positions = [tuple(self.me["farmer"])] + [tuple(p) for p in self.me["hands"]]
        private = obs["private"]
        self.inv = [dict(x) for x in private["inventories"]]
        self.shed = dict(private["shed"])
        self.seeds = dict(private["seeds"])
        self.prices = obs["market"]["prices"]
        self.money = float(self.me["money"])
        self.capacity = int(self.cfg.get("shedCapacity", 100))
        half = len(self.tiles)//2
        self.depotes = ((half-1, half-1), (half, half-1), (half-1, half), (half, half))
        self.assets = {k: 0 for k in KINDS}
        for row in self.tiles:
            for tile in row:
                if isinstance(tile, dict):
                    key = tile.get("crop", tile.get("animal"))
                    if key in self.assets:
                        self.assets[key] += 1
        if self.today != self.day:
            self.day = self.today
            self.jobs = {}
            self.targets = Search(obs, self.cfg).plan()
            STATS["plans"] += 1

    def depot(self, pos):
        target = min(self.depotes, key=lambda t: _distance(pos, t))
        return target, _distance(pos, target)

    def tile(self, xy):
        return self.tiles[xy[1]][xy[0]]

    def service_ops(self, xy):
        tile = self.tile(xy)
        if not isinstance(tile, dict):
            return [], 0., 0
        crop = tile.get("crop")
        if crop in CROPS:
            _, first, peak, interval, cap = CROPS[crop]
            age = self.today-int(tile.get("planted_day", self.today))
            held = int(tile.get("yield_units", 0))
            ops = []
            urgent = 0
            if not tile.get("watered_today") and not self.final:
                bonus_window = (not interval and (peak+1)//2 <= age <= peak)
                if tile.get("consecutive_unwatered", 0) or bonus_window:
                    ops.append("WATER")
                    urgent = 2 if tile.get("consecutive_unwatered", 0) else 0
            elif self.final and not tile.get("watered_today") and not interval and \
                    (peak+1)//2 <= age <= peak and held:
                ops.append("WATER")
            if held and age >= first:
                deadline = int(tile.get("max_lifespan_step", -1))
                ripe = (held >= (2 if interval else cap) or age >= peak or self.final or
                        0 <= deadline <= self.step+self.remaining+3)
                if ripe:
                    ops.append("HARVEST")
                    if self.final or 0 <= deadline <= self.step+self.remaining+3:
                        urgent = max(urgent, 1)
            value = held*self.prices.get(crop, 0)*.85+len(ops)*18
            return ops, value, urgent
        animal = tile.get("animal")
        if animal in ANIMALS:
            product = ANIMALS[animal][5]
            ops = []
            urgent = 0
            held = int(tile.get("yield_units", 0))
            if held:
                ops.append("HARVEST")
                urgent = 1 if held >= ANIMALS[animal][4]-1 or self.final else 0
            if tile.get("fertilizer_available"):
                ops.append("COLLECT_FERTILIZER")
            new_animal = int(tile.get("placed_day", -1)) == self.today
            if not self.final and not new_animal and not tile.get("fed_today"):
                ops.append("FEED")
                urgent = 2 if tile.get("consecutive_unfed", 0) else urgent
            if not self.final and not new_animal and not tile.get("cared_today"):
                ops.append("CARE")
            value = held*self.prices.get(product, 0)+(
                self.prices.get("FERTILIZER", 0)*.7 if tile.get("fertilizer_available") else 0)
            value += (self.prices.get(product, 0)*.35 if "CARE" in ops else 0)
            value += 55 if "FEED" in ops else 0
            return ops, value, urgent
        return [], 0., 0

    def valid_job(self, job):
        xy = job["target"]
        tile = self.tile(xy)
        if job["kind"] == "service":
            return bool(self.service_ops(xy)[0])
        if job["kind"] == "deliver":
            return True
        item = job["item"]
        if item in CROPS:
            return tile is None or (isinstance(tile, dict) and tile.get("crop") == item and
                                    not tile.get("watered_today")) or \
                   (isinstance(tile, dict) and tile.get("kind") in ("WEED", "COOP", "PASTURE") and
                    not tile.get("animal"))
        return tile is None or (isinstance(tile, dict) and
                                (tile.get("kind") in ("WEED", "COOP", "PASTURE")) and
                                not tile.get("animal"))

    def job_cost(self, idx, job):
        pos = self.positions[idx]
        target = job["target"]
        d = _distance(pos, target)
        if job["kind"] == "service":
            ops = self.service_ops(target)[0]
            if "FEED" in ops and not self.inv[idx].get("WHEAT", 0):
                depot, back = self.depot(pos)
                d = back+1+_distance(depot, target)
            return d+len(ops)
        if job["kind"] == "invest":
            item = job["item"]
            ops = 2 if item in CROPS else 3
            if item in ANIMALS and not self.inv[idx].get(item, 0):
                depot, back = self.depot(pos)
                d = back+1+_distance(depot, target)
            return d+ops
        return d+1

    def choose(self, idx, claimed):
        options = []
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                xy = (x, y)
                if xy in claimed or not isinstance(tile, dict):
                    continue
                ops, value, urgency = self.service_ops(xy)
                if not ops:
                    continue
                job = {"kind": "service", "target": xy}
                cost = self.job_cost(idx, job)
                if cost > self.remaining and urgency < 2:
                    continue
                utility = urgency*350+value/max(1., cost)**.7
                options.append((utility, -cost, job))
        if not self.final and self.hour <= 16:
            reserved = {k: 0 for k in KINDS}
            for job in self.jobs.values():
                if job["kind"] == "invest":
                    reserved[job["item"]] += 1
            gaps = {k: self.targets.get(k, 0)-self.assets[k]-reserved[k] for k in KINDS}
            if any(v > 0 for v in gaps.values()):
                sites = []
                for y, row in enumerate(self.tiles):
                    for x, tile in enumerate(row):
                        xy = (x, y)
                        if xy in claimed or tile == "LOCKED":
                            continue
                        if tile is None or isinstance(tile, dict) and tile.get("kind") in \
                                ("WEED", "COOP", "PASTURE") and not tile.get("animal"):
                            sites.append((_distance(self.positions[idx], xy), xy, tile))
                sites.sort()
                for item in KINDS:
                    if gaps[item] <= 0:
                        continue
                    capital = CROPS[item][0] if item in CROPS else ANIMALS[item][0]
                    if capital > self.money-max(60, self.assets["SHEEP"]*5):
                        continue
                    for _, xy, tile in sites[:4]:
                        job = {"kind": "invest", "target": xy, "item": item}
                        cost = self.job_cost(idx, job)
                        if cost > self.remaining-2:
                            continue
                        # Search determined the type and quantity. Execution
                        # chooses the nearest feasible site and worker.
                        site_bonus = 14 if tile is None else 0
                        utility = 130/max(1., cost)**.55+site_bonus
                        if item in ANIMALS:
                            utility += 55
                        options.append((utility, -cost, job))
        if not options:
            return None
        return max(options, key=lambda row: (row[0], row[1]))[2]

    def perform(self, idx, job):
        pos = self.positions[idx]
        inventory = self.inv[idx]
        if job["kind"] == "deliver":
            depot, distance = self.depot(pos)
            if distance:
                return _towards(pos, depot)
            room = max(0, self.capacity-sum(self.shed.values()))
            for item, n in list(inventory.items()):
                take = min(room, n)
                self.shed[item] = self.shed.get(item, 0)+take
                room -= take
            inventory.clear()
            self.jobs.pop(idx, None)
            STATS["returns"] += 1
            return ["DROP"]
        xy = job["target"]
        tile = self.tile(xy)
        item = job.get("item")
        if job["kind"] == "invest":
            if item in CROPS:
                if isinstance(tile, dict) and tile.get("crop") == item:
                    return ["WATER"] if not tile.get("watered_today") else ["PASS"]
                if isinstance(tile, dict):
                    return _towards(pos, xy) or ["DIG"]
                if self.seeds.get(item, 0) <= 0:
                    STATS["missing_supply"] += 1
                    return _towards(pos, xy) or ["PASS"]
                if pos != xy:
                    return _towards(pos, xy)
                self.seeds[item] -= 1
                return ["PLANT", item]
            if isinstance(tile, dict) and tile.get("animal") == item:
                self.jobs.pop(idx, None)
                return ["PASS"]
            structure = ANIMALS[item][1]
            if tile is None or isinstance(tile, dict) and tile.get("kind") != structure:
                if pos != xy:
                    return _towards(pos, xy)
                return ["BUILD_"+structure] if tile is None else ["DIG"]
            if inventory.get(item, 0) <= 0:
                depot, distance = self.depot(pos)
                if distance:
                    return _towards(pos, depot)
                if self.shed.get(item, 0) <= 0:
                    STATS["missing_supply"] += 1
                    return ["PASS"]
                self.shed[item] -= 1
                inventory[item] = inventory.get(item, 0)+1
                return ["PICKUP", item, 1]
            if pos != xy:
                return _towards(pos, xy)
            inventory[item] -= 1
            return ["PLACE", item]
        ops, _, _ = self.service_ops(xy)
        if not ops:
            self.jobs.pop(idx, None)
            return ["PASS"]
        # Product collection can be done before a supply trip. For feed, a
        # worker carries several wheat units to amortize shed travel.
        local = next((op for op in ops if op in ("HARVEST", "COLLECT_FERTILIZER", "WATER")), None)
        if local and pos == xy:
            return [local]
        if "FEED" in ops and inventory.get("WHEAT", 0) <= 0:
            depot, distance = self.depot(pos)
            if distance:
                return _towards(pos, depot)
            n = min(3, self.shed.get("WHEAT", 0))
            if n:
                self.shed["WHEAT"] -= n
                inventory["WHEAT"] = inventory.get("WHEAT", 0)+n
                return ["PICKUP", "WHEAT", n]
            STATS["missing_supply"] += 1
            return ["PASS"]
        if pos != xy:
            return _towards(pos, xy)
        if "FEED" in ops:
            inventory["WHEAT"] -= 1
            return ["FEED"]
        if "CARE" in ops:
            return ["CARE"]
        return [ops[0]]

    def market(self):
        limit = int(self.cfg.get("maxMarketOrdersPerTurn", 10))
        orders = []
        money = self.money
        def add(order, cost=0):
            nonlocal money
            if len(orders) >= limit or money < cost:
                return False
            orders.append(order)
            money -= cost
            return True
        live_animals = sum(self.assets[k] for k in ANIMALS)
        queued_animals = {k: 0 for k in ANIMALS}
        queued_seeds = {k: 0 for k in CROPS}
        for job in self.jobs.values():
            if job["kind"] != "invest":
                continue
            item = job["item"]
            if item in ANIMALS:
                queued_animals[item] += 1
            else:
                queued_seeds[item] += 1
        reserve = 0 if self.final else live_animals
        wheat_target = reserve+3 if reserve else 0
        # Sell first to fund this turn's input orders. Shed stock was updated
        # with all worker actions that can complete before the market phase.
        sales = []
        for item in PRODUCTS:
            n = max(0, self.shed.get(item, 0)-(wheat_target if item == "WHEAT" else 0))
            if n:
                sales.append((self.prices.get(item, 1)*n, item, n))
        for _, item, n in sorted(sales, reverse=True)[:4]:
            if add(["SELL", item, n]):
                money += n*max(1, self.prices.get(item, 1))*.90
        if self.hour <= 2:
            current = int(self.me.get("hires_today", 0))
            assets = sum(self.assets.values())+sum(queued_animals.values())+sum(queued_seeds.values())
            planned_assets = sum(self.targets.values())
            desired = min(9, max(5 if not self.final else 2,
                                 4+max(assets, planned_assets)//4))
            while current < desired and len(orders) < limit-2:
                price = _fib(current)*float(self.cfg.get("farmHandCostMult", 1))
                if not add(["HIRE"], price):
                    break
                current += 1
        for item, needed in queued_animals.items():
            held = self.shed.get(item, 0)+sum(inv.get(item, 0) for inv in self.inv)
            missing = max(0, needed-held)
            if missing:
                add(["BUY_ANIMAL", item, missing], missing*ANIMALS[item][0])
        for item, needed in queued_seeds.items():
            missing = max(0, needed-self.seeds.get(item, 0))
            if missing:
                add(["BUY_SEED", item, missing], missing*CROPS[item][0])
        if reserve:
            stock = self.shed.get("WHEAT", 0)+sum(inv.get("WHEAT", 0) for inv in self.inv)
            # Wheat held by one hand cannot feed another hand's animal.
            missing = max(0, wheat_target-stock,
                          min(8, reserve)-self.shed.get("WHEAT", 0))
            room = max(0, self.capacity-sum(self.shed.values()))
            missing = min(missing, room)
            if missing:
                price = self.prices.get("WHEAT", 25)+5
                quantity = min(missing, max(0, int((money-30)//price)))
                if quantity:
                    add(["BUY_PRODUCT", "WHEAT", quantity], quantity*price)
        if self.hour <= 3 and not self.final:
            desired_assets = sum(self.targets.values())
            free = sum(tile is None or isinstance(tile, dict) and tile.get("kind") == "WEED"
                       for row in self.tiles for tile in row)
            land_count = len(self.me.get("unlocked_quadrants", ["NW"]))
            if desired_assets > sum(self.assets.values())+free and land_count < 4:
                cost = (1000, 2000, 4000)[land_count-1]
                if money >= cost+100:
                    add(["BUY_LAND"], cost)
        return orders

    def run(self, obs):
        self.read(obs)
        actions = []
        for idx, pos in enumerate(self.positions):
            job = self.jobs.get(idx)
            if job and not self.valid_job(job):
                self.jobs.pop(idx, None)
                job = None
            depot, distance = self.depot(pos)
            cargo = sum(v for k, v in self.inv[idx].items() if k in PRODUCTS)
            urgent_drop = self.final and cargo and self.remaining <= distance+3
            cargo_value = sum(v*self.prices.get(k, 0) for k, v in self.inv[idx].items()
                              if k in PRODUCTS)
            early_drop = (cargo_value >= 500 and self.hour <= 20 and distance <= 4 or
                          cargo >= 10 and self.hour >= 14 and distance <= 3)
            if urgent_drop or early_drop and not job:
                job = {"kind": "deliver", "target": depot}
                self.jobs[idx] = job
            if not job:
                claimed = {other["target"] for key, other in self.jobs.items()
                           if key != idx and other["kind"] != "deliver"}
                job = self.choose(idx, claimed)
                if job:
                    self.jobs[idx] = job
                    STATS["jobs"] += 1
                    if job["kind"] == "invest":
                        STATS["investments"] += 1
            action = self.perform(idx, job) if job else ["PASS"]
            actions.append(action)
            STATS["passes"] += action[0] == "PASS"
        result = {"farmer": actions[0], "hands": actions[1:], "market": self.market()}
        self.last_step = self.step
        return result


def agent(observation, configuration=None):
    cfg = configuration if hasattr(configuration, "get") else {}
    player = int(observation.get("player", 0))
    step = int(observation.get("step", 0))
    state = STATES.get(player)
    if state is None or step <= state.last_step:
        state = Executor(observation, cfg)
        STATES[player] = state
    return state.run(observation)


agent.telemetry = STATS
