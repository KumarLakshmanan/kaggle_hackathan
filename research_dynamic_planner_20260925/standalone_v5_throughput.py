"""Standalone daily farm planner. Experimental; not submitted.
Generated from readable economics.py and candidate.py.
"""

from __future__ import annotations

# ECONOMIC MODEL

"""Small public-state investment model for Kaggriculture 1.32.7.

Price curves are exact. Production assumes successful future service; market
forecasts approximate within-day sale timing and unknown future shops. Those
approximations are deliberately separate from observed game facts.
"""



import math


PARAMETERS = {
    "WHEAT": (25, 400, "sqrt", .8, "log", .2),
    "CARROT": (35, 450, "hinge", 1., "sqrt", .7),
    "TOMATO": (60, 200, "hinge", .4, "sqrt", .6),
    "STRAWBERRY": (120, 100, "sqrt", .7, "linear", 1.6),
    "MELON": (250, 300, "log", .2, "sq", 3.6),
    "EGG": (50, 332, "hinge", .4, "log", .2),
    "MILK": (160, 122, "sqrt", .6, "linear", 1.6),
    "WOOL": (200, 105, "log", .2, "sq", 3.2),
    "FERTILIZER": (100, 200, "linear", .4, "linear", .4),
}
PRODUCTS = tuple(PARAMETERS)
CROPS = {
    "WHEAT": (10, 2, 4, 0, 6), "CARROT": (20, 2, 3, 0, 4),
    "TOMATO": (50, 8, 8, 1, 4), "STRAWBERRY": (100, 10, 10, 2, 4),
    "MELON": (80, 10, 12, 0, 6),
}
ANIMALS = {
    "GOOSE": (300, 4, 1, 4, "EGG"), "COW": (400, 8, 2, 6, "MILK"),
    "SHEEP": (500, 6, 3, 6, "WOOL"),
}
SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}


def _shape(kind, x, throughput):
    x = max(0., x)
    if kind == "sq":
        return x*x
    if kind == "sqrt":
        return math.sqrt(x)
    if kind == "log":
        return math.log1p(x)
    if kind == "log10":
        return math.log10(1+x)
    if kind == "hinge" and throughput > 0:
        u = x/throughput
        return u+8*max(0., u-1)**2
    return x


def price(item, inventory, overrides=None):
    base, throughput, below, bt, above, at = PARAMETERS[item]
    equilibrium = 10000
    patch = (overrides or {}).get(item, {})
    if patch:
        base = patch.get("base", base)
        throughput = patch.get("T", throughput)
        equilibrium = patch.get("I0", equilibrium)
        below, bt = patch.get("below_func", below), patch.get("below_target", bt)
        above, at = patch.get("above_func", above), patch.get("above_target", at)
    if inventory < equilibrium:
        value = base+bt*base*_shape(below, equilibrium-inventory, throughput)/_shape(below, throughput, throughput)
    else:
        value = base-at*base*_shape(above, inventory-equilibrium, throughput)/_shape(above, throughput, throughput)
    return max(1, int(round(value)))


def demand_per_day(obs, cfg):
    tpd = int(cfg.get("turnsPerDay", 24))
    center = tpd/max(1, int(cfg.get("townCenterSellInterval", 24)))
    shop_rate = tpd/max(1, int(cfg.get("townShopSellInterval", 4)))
    rates = {k: center if k != "FERTILIZER" else 0. for k in PRODUCTS}
    for shop in obs.get("town", {}).get("unlocked_shops", []):
        products = SHOP_PRODUCTS.get(shop, ())
        for item in products:
            rates[item] += shop_rate*(2 if len(products) == 1 else 1)
    return rates


def _empty(horizon):
    return {k: [0.]*horizon for k in PRODUCTS}


def _profile(tile, today, horizon, new=False):
    """Daily net market flow under service: product sales minus inputs.

    A new ongoing crop receives two fertilizer applications; existing crops
    only receive known fertilizer bonuses in this conservative projection.
    Animals are fed/cared for daily, their bank applies before the next care.
    """
    out = _empty(horizon)
    if tile.get("animal") in ANIMALS:
        animal = tile["animal"]
        _, first, interval, cap, product = ANIMALS[animal]
        placed = tile["placed_day"]
        bank = tile.get("pending_care_bonus", 0)
        out[product][0] = tile.get("yield_units", 0)
        out["FERTILIZER"][0] = int(tile.get("fertilizer_available", False))
        for d in range(horizon-1):
            current = today+d
            out["WHEAT"][d] -= 1
            age = current+1-placed
            if age >= first and (age-first) % interval == 0:
                out[product][d+1] += min(cap, 1+bank)
                bank = 0
            bank += 1
            out["FERTILIZER"][d+1] += 1
        return out
    crop = tile["crop"]
    _, first, peak, interval, cap = CROPS[crop]
    planted = tile["planted_day"]
    age = today-planted
    units = tile.get("yield_units", 0 if interval else 1)
    fert_until = tile.get("fertilized_until_day", -1)
    if interval:
        out[crop][0] = units if age >= first else 0
        if new:
            # Tomato ages 7 and 10; strawberry 9 and 13. Each application
            # covers the following overnight events for three days.
            applications = (first-1, first+2) if interval == 1 else (first-1, first+3)
            for a in applications:
                if 0 <= a < horizon:
                    out["FERTILIZER"][a] -= 1
        else:
            applications = ()
        for prod in range(4):
            date = planted+first+prod*interval
            offset = date-today
            if offset <= 0 or offset >= horizon:
                continue
            fertilized = fert_until >= date-1 or any(a <= offset-1 <= a+2 for a in applications)
            out[crop][offset] += 2 if fertilized else 1
        return out
    harvest_age = 10 if crop == "MELON" else peak
    harvest_day = max(today, planted+harvest_age)
    offset = harvest_day-today
    if offset >= horizon or harvest_day-planted < first:
        return out
    for date in range(today, harvest_day+1):
        current_age = date-planted
        if date == today and tile.get("watered_today"):
            continue
        if (peak+1)//2 <= current_age <= peak:
            units = min(cap, units+(2 if fert_until >= date else 1))
    out[crop][offset] = units
    return out


def _add(destination, source, multiplier=1.):
    for item in PRODUCTS:
        for d, n in enumerate(source[item]):
            destination[item][d] += multiplier*n


def _new_profile(item, today, horizon):
    if item in ANIMALS:
        tile = {"animal": item, "placed_day": today}
    else:
        tile = {"crop": item, "planted_day": today}
    return _profile(tile, today, horizon, new=True)


def _market_step(item, stock, amount, overrides):
    # Midpoint valuation approximates daily mixed sales. At the $1 floor,
    # additional sales do not increase inventory in the real environment.
    quote = price(item, stock+amount/2, overrides)
    after = stock+amount
    if amount > 0 and price(item, after, overrides) == 1:
        if price(item, stock, overrides) == 1:
            after = stock
        else:
            low, high = stock, after
            for _ in range(14):
                mid = (low+high)/2
                if price(item, mid, overrides) > 1:
                    low = mid
                else:
                    high = mid
            after = high
    return quote, after


def investment_values(obs, cfg, planned_counts=None):
    today = int(obs.get("day", 0))
    tpd = int(cfg.get("turnsPerDay", 24))
    final = (int(cfg.get("episodeSteps", 720))-2)//tpd
    horizon = final-today+1
    if horizon <= 1:
        return {}
    player = int(obs.get("player", 0))
    own, rival = _empty(horizon), _empty(horizon)
    for seat, farm in enumerate(obs["farms"]):
        target = own if seat == player else rival
        for row in farm["tiles"]:
            for tile in row:
                if isinstance(tile, dict) and (tile.get("animal") in ANIMALS or tile.get("crop") in CROPS):
                    _add(target, _profile(tile, today, horizon))
    for item, n in (planned_counts or {}).items():
        if item in ANIMALS or item in CROPS:
            _add(own, _new_profile(item, today, horizon), n)
    known = demand_per_day(obs, cfg)
    shop_rate = tpd/max(1, int(cfg.get("townShopSellInterval", 4)))
    mean_shop = {k: 0. for k in PRODUCTS}
    for products in SHOP_PRODUCTS.values():
        for k in products:
            mean_shop[k] += shop_rate*(2 if len(products) == 1 else 1)/len(SHOP_PRODUCTS)
    unlock_interval = max(1, int(cfg.get("townShopUnlockInterval", 3)))
    remaining_shops = max(0, 8-len(obs.get("town", {}).get("unlocked_shops", [])))
    new_shops = [min(remaining_shops, (today+d)//unlock_interval-today//unlock_interval)
                 for d in range(horizon)]
    overrides = cfg.get("marketParams")
    result = {}
    for item in tuple(CROPS)+tuple(ANIMALS):
        if item in ANIMALS:
            capital, first, interval, cap, _ = ANIMALS[item]
            duration = horizon
            actions = 4.25+1/interval
            # Very short livestock investments cannot recover setup/feed cost.
            allowed = horizon > first+3
        else:
            capital, first, peak, interval, cap = CROPS[item]
            duration = (first+3*interval+1) if interval else ((10 if item == "MELON" else peak)+1)
            actions = 1.4+(4/duration if interval else 2/duration)
            allowed = horizon >= duration
        if not allowed:
            result[item] = dict(score=-1e9, net=-capital, capital=capital,
                                horizon=duration, daily_actions=actions, output={})
            continue
        flow = _new_profile(item, today, horizon)
        scenario_nets = []
        # Both scenarios use only current observations. Future shops are an
        # explicit expectation; the cautious case halves their assumed demand.
        for rival_scale, shop_expectation in ((1., 1.), (1.2, .5)):
            revenue = 0.
            for product in PRODUCTS:
                base_stock = changed_stock = float(obs["market"]["inventory"][product])
                for d in range(horizon):
                    demand = known[product]+new_shops[d]*mean_shop[product]*shop_expectation
                    base_stock -= demand
                    changed_stock -= demand
                    base_flow = own[product][d]+rival_scale*rival[product][d]
                    before, base_stock = _market_step(product, base_stock, base_flow, overrides)
                    after, changed_stock = _market_step(product, changed_stock, base_flow+flow[product][d], overrides)
                    revenue += own[product][d]*(after-before)+flow[product][d]*after
            scenario_nets.append(revenue-capital-4*actions*duration)
        net = .65*scenario_nets[0]+.35*min(scenario_nets)
        # Experimental v5: value *resource throughput*, not just total
        # horizon profit. Capital tied in the project and future worker time
        # are both scarce early in a 30-day game. The 30-coin action shadow
        # price is a common normalization, not the engine's HIRE cost.
        resource_commitment = capital + 30.0*actions*duration
        score = 100.0*net/max(1.0, resource_commitment)
        result[item] = dict(score=score, net=net, capital=capital,
                                horizon=duration, daily_actions=actions,
                                resource_commitment=resource_commitment,
                                output={k: sum(v) for k, v in flow.items() if sum(v)},
                                scenario_nets=scenario_nets)
    return result


# WORKER AND FARM PLANNER

"""Readable observation-driven Kaggriculture planner (research candidate).

No action tapes or incumbent imports. Jobs are selected from observed tiles,
and each emitted action is checked against the current worker and supplies.
"""



import importlib.util
from pathlib import Path
import sys




CROP = {
    "WHEAT": (10, 2, 4, 0, 6), "CARROT": (20, 2, 3, 0, 4),
    "TOMATO": (50, 8, 8, 1, 4), "STRAWBERRY": (100, 10, 10, 2, 4),
    "MELON": (80, 10, 12, 0, 6),
}
ANIMAL = {
    "GOOSE": (300, "COOP", 4, 1, 4, "EGG"),
    "COW": (400, "PASTURE", 8, 2, 6, "MILK"),
    "SHEEP": (500, "PASTURE", 6, 3, 6, "WOOL"),
}
SELLABLE = tuple(CROP) + ("EGG", "MILK", "WOOL", "FERTILIZER")
MAX_HANDS = 13
LABOR_PRICE = 4.0
MIN_PROJECT_SCORE = 3.0
EARLY_SLOW_CROP_LIMIT = 1.1
LATE_STAPLE_BONUS = 0.0
_STATES = {}
_STATS = {"jobs": 0, "investments": 0, "replans": 0,
          "wait_supply": 0, "forced_returns": 0, "passes": 0}


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _move(a, b):
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
        a, b = b, a + b
    return a


def _next_production(tile, day, strictly_after=0):
    _, _, first, interval, _, _ = ANIMAL[tile["animal"]]
    first += tile["placed_day"]
    minimum = day + strictly_after
    if first >= minimum:
        return first
    return first + ((minimum - first + interval - 1) // interval) * interval


class Planner:
    def __init__(self, obs, cfg):
        self.cfg = cfg
        self.player = int(obs.get("player", 0))
        self.last_step = -1
        self.day = -1
        self.jobs = {}
        self.values = {}
        self.values_step = -100
        self.desired_hands = 0

    def read(self, obs):
        self.obs = obs
        self.step = int(obs.get("step", 0))
        self.tpd = int(self.cfg.get("turnsPerDay", 24))
        self.last = int(self.cfg.get("episodeSteps", 720)) - 2
        self.today = self.step // self.tpd
        self.hour = self.step % self.tpd
        self.end_day = min(self.last, (self.today + 1) * self.tpd - 1)
        self.remaining = self.end_day - self.step + 1
        self.final = self.today == self.last // self.tpd
        self.me = obs["farms"][self.player]
        self.tiles = self.me["tiles"]
        self.size = len(self.tiles)
        half = self.size // 2
        self.shed_tiles = ((half-1, half-1), (half, half-1),
                           (half-1, half), (half, half))
        self.positions = [tuple(self.me["farmer"])] + [tuple(p) for p in self.me["hands"]]
        self.private = obs["private"]
        self.inventory = [dict(i) for i in self.private["inventories"]]
        self.shed = dict(self.private["shed"])
        self.seeds = dict(self.private["seeds"])
        self.prices = obs["market"]["prices"]
        self.money = float(self.me["money"])
        self.capacity = int(self.cfg.get("shedCapacity", 100))
        self.animals = sum(isinstance(t, dict) and t.get("animal") in ANIMAL
                           for row in self.tiles for t in row)
        self.crops = sum(isinstance(t, dict) and t.get("kind") == "PLANT"
                         for row in self.tiles for t in row)
        if self.day != self.today:
            self.day = self.today
            self.jobs.clear()
            self.values_step = -100
            # Estimate a day's work, including local movement and supply trips.
            work = 4.6 * self.animals + 2.0 * self.crops
            expansion = 25 if self.today < 24 and self.money > 150 else 0
            target = int((work + expansion + 15) / 18)
            if self.today < 23:
                target = max(5, target)
            if self.final:
                work = sum(2 + self.near_shed((x, y))[1]
                           for y, row in enumerate(self.tiles) for x, t in enumerate(row)
                           if isinstance(t, dict) and (t.get("yield_units", 0) > 0
                               or t.get("fertilizer_available", False)))
                target = int((work + 15) / 18)
            self.desired_hands = min(MAX_HANDS, max(0, target))
        # Reprice on bounded public-state intervals, not on replay identity.
        if self.step - self.values_step >= 4:
            counts = {}
            for job in self.jobs.values():
                if job["kind"] == "invest":
                    item = job["item"]
                    t = self.tile(job["target"])
                    if not (isinstance(t, dict) and (t.get("crop") == item or t.get("animal") == item)):
                        counts[item] = counts.get(item, 0) + 1
            self.values = investment_values(obs, self.cfg, counts)
            self.values_step = self.step

    def tile(self, target):
        return self.tiles[target[1]][target[0]]

    def near_shed(self, pos):
        target = min(self.shed_tiles, key=lambda p: _distance(pos, p))
        return target, _distance(pos, target)

    def cargo_value(self, idx):
        inv = self.inventory[idx]
        return sum(n * self.prices.get(k, 0) for k, n in inv.items()
                   if k in SELLABLE and k != "WHEAT")

    def fertilize_worthwhile(self, tile):
        if self.final or tile.get("fertilized_until_day", -1) >= self.today:
            return False
        crop = tile["crop"]
        _, first, peak, interval, _ = CROP[crop]
        age = self.today - tile["planted_day"]
        fert_price = self.prices.get("FERTILIZER", 100)
        price = self.prices.get(crop, 1)
        if interval:
            # Bonus is paid overnight. Start immediately before a production.
            prod_age = age + 1
            scheduled = prod_age >= first and (prod_age-first) % interval == 0
            left = first + 3*interval - prod_age
            bonus_count = min(1 + 2//interval, 1 + max(0, left)//interval)
            return scheduled and left >= 0 and bonus_count * price > fert_price + 2*LABOR_PRICE
        if crop == "MELON":
            # Reaching six units early does not bypass the engine's age-10
            # harvest gate. Daily watering already reaches six at age 10.
            return False
        window = [d for d in range(age, peak+1) if (peak+1)//2 <= d <= peak]
        base_final = min(CROP[crop][4], tile.get("yield_units", 1)+len(window))
        boosted = min(CROP[crop][4], tile.get("yield_units", 1)+len(window)
                      +sum(d <= age+2 for d in window))
        return (first-1 <= age <= peak-1 and
                (boosted-base_final)*price > fert_price + 2*LABOR_PRICE)

    def crop_ops(self, tile):
        crop = tile["crop"]
        _, first, peak, interval, max_yield = CROP[crop]
        age = self.today - tile["planted_day"]
        units = tile.get("yield_units", 0)
        ops = []
        expired = tile.get("max_lifespan_step", -1)
        if expired >= 0 and self.step >= expired and not units:
            return []
        harvest = False
        if units and age >= first:
            if interval:
                next_produces = (age+1 >= first and (age+1-first) % interval == 0
                                 and (age+1-first)//interval < 4)
                harvest = (units >= 2 or self.final or
                           (expired >= 0 and expired <= self.end_day+1) or
                           (next_produces and units >= 3))
            else:
                harvest = self.final or units >= max_yield or age >= (10 if crop == "MELON" else peak)
        needs_water = (not tile.get("watered_today") and
                       (tile.get("consecutive_unwatered", 0) >= 1 or
                        not interval and (peak+1)//2 <= age <= peak or
                        interval and self.fertilize_worthwhile(tile)))
        # An ongoing plant needs water for every fertilized production tick.
        if interval and tile.get("fertilized_until_day", -1) >= self.today:
            if age+1 >= first and (age+1-first) % interval == 0:
                needs_water = not tile.get("watered_today")
        if self.final:
            needs_water = bool(harvest and not interval and not tile.get("watered_today")
                               and (peak+1)//2 <= age <= peak and units < max_yield)
        if self.fertilize_worthwhile(tile) and not harvest:
            ops.append("FERTILIZE")
            needs_water = True
        if needs_water:
            ops.append("WATER")
        if harvest:
            ops.append("HARVEST")
        return ops

    def service_job(self, target, tile):
        if tile.get("kind") == "PLANT":
            ops = self.crop_ops(tile)
            if not ops:
                return None
            item = tile["crop"]
            units = tile.get("yield_units", 0)
            value = units * self.prices.get(item, 0) if "HARVEST" in ops else 0
            if "WATER" in ops:
                # Protect existing capital and growth; mandatory care has high
                # priority but still shares the finite labor budget.
                value += 140 if tile.get("consecutive_unwatered", 0) >= 1 else 35
            if "FERTILIZE" in ops:
                value += max(20, 2*self.prices.get(item, 0)-self.prices.get("FERTILIZER", 100))
            priority = 2 if "WATER" in ops and tile.get("consecutive_unwatered", 0) >= 1 else 0
            deadline = tile.get("max_lifespan_step", -1)
            if "HARVEST" in ops and (self.final or 0 <= deadline <= self.end_day+1):
                priority = max(priority, 1)
            return dict(kind="service", target=target, item=item, ops=ops, value=value, priority=priority)
        if tile.get("animal") in ANIMAL:
            animal = tile["animal"]
            product = ANIMAL[animal][5]
            ops, value = [], 0
            if tile.get("yield_units", 0):
                ops.append("HARVEST")
                value += tile["yield_units"] * self.prices.get(product, 0)
            if not self.final and not tile.get("fed_today"):
                ops.append("FEED")
                value += 210 + (220 if tile.get("consecutive_unfed", 0) else 0)
            # Today's CARE enters the bank after tomorrow's production event.
            if (not self.final and not tile.get("cared_today")
                    and _next_production(tile, self.today, 2) <= self.last // self.tpd):
                ops.append("CARE")
                value += max(0, self.prices.get(product, 0) - LABOR_PRICE)
            if tile.get("fertilizer_available"):
                ops.append("COLLECT_FERTILIZER")
                value += self.prices.get("FERTILIZER", 0)
            if ops:
                priority = 2 if "FEED" in ops and tile.get("consecutive_unfed", 0) >= 1 else 0
                return dict(kind="service", target=target, item=animal, ops=ops, value=value, priority=priority)
        return None

    def remaining_ops(self, job):
        tile = self.tile(job["target"])
        if job["kind"] == "deliver":
            return ["DROP"]
        if job["kind"] == "invest":
            item = job["item"]
            if item in CROP:
                if isinstance(tile, dict) and tile.get("crop") == item:
                    return [] if tile.get("watered_today") else ["WATER"]
                if tile is None:
                    return ["PLANT", "WATER"]
                if isinstance(tile, dict) and tile.get("kind") in ("WEED", "COOP", "PASTURE") and not tile.get("animal"):
                    return ["DIG", "PLANT", "WATER"]
                return []
            structure = ANIMAL[item][1]
            if isinstance(tile, dict) and tile.get("animal") == item:
                ops = []
                if not tile.get("fed_today"):
                    ops.append("FEED")
                if not tile.get("cared_today"):
                    ops.append("CARE")
                return ops
            if tile is None:
                return ["BUILD_"+structure, "PLACE", "FEED", "CARE"]
            if isinstance(tile, dict) and tile.get("kind") == structure and not tile.get("animal"):
                return ["PLACE", "FEED", "CARE"]
            if isinstance(tile, dict) and not tile.get("animal") and tile.get("kind") != "PLANT":
                return ["DIG", "BUILD_"+structure, "PLACE", "FEED", "CARE"]
            return []
        if not isinstance(tile, dict):
            return []
        ops = []
        for op in job["ops"]:
            if op == "WATER" and tile.get("kind") == "PLANT" and not tile.get("watered_today"):
                ops.append(op)
            elif op == "FERTILIZE" and tile.get("kind") == "PLANT" and tile.get("fertilized_until_day", -1) < self.today:
                ops.append(op)
            elif op == "FEED" and tile.get("animal") and not tile.get("fed_today"):
                ops.append(op)
            elif op == "CARE" and tile.get("animal") and not tile.get("cared_today"):
                ops.append(op)
            elif op == "HARVEST" and tile.get("yield_units", 0) > 0:
                ops.append(op)
            elif op == "COLLECT_FERTILIZER" and tile.get("fertilizer_available"):
                ops.append(op)
        return ops

    def supplies(self, job, ops):
        need = {}
        if "FEED" in ops:
            need["WHEAT"] = 1
        if "FERTILIZE" in ops:
            need["FERTILIZER"] = 1
        if "PLACE" in ops:
            need[job["item"]] = 1
        return need

    def cost(self, idx, job):
        ops = self.remaining_ops(job)
        pos = self.positions[idx]
        need = self.supplies(job, ops)
        missing = [k for k, n in need.items() if self.inventory[idx].get(k, 0) < n]
        if missing:
            depot, distance = self.near_shed(pos)
            travel = distance + len(missing) + _distance(depot, job["target"])
        else:
            travel = _distance(pos, job["target"])
        total = travel + len(ops)
        if self.final and ("HARVEST" in ops or "COLLECT_FERTILIZER" in ops):
            total += self.near_shed(job["target"])[1] + 1
        return total

    def reserved_capital(self):
        seeds, animals = {}, {}
        for job in self.jobs.values():
            ops = self.remaining_ops(job)
            item = job.get("item")
            if "PLANT" in ops:
                seeds[item] = seeds.get(item, 0) + 1
            if "PLACE" in ops:
                animals[item] = animals.get(item, 0) + 1
        cost = sum(max(0, n-self.seeds.get(k, 0))*CROP[k][0] for k, n in seeds.items())
        for k, n in animals.items():
            owned = self.shed.get(k, 0) + sum(inv.get(k, 0) for inv in self.inventory)
            cost += max(0, n-owned)*ANIMAL[k][0]
        return cost

    def select_job(self, idx, claimed):
        options = []
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                target = (x, y)
                if target in claimed or not isinstance(tile, dict):
                    continue
                job = self.service_job(target, tile)
                if job:
                    cost = self.cost(idx, job)
                    if cost > self.remaining and job.get("priority") == 2:
                        essential = "WATER" if tile.get("kind") == "PLANT" else "FEED"
                        job = dict(job, ops=[essential])
                        cost = self.cost(idx, job)
                    if cost <= self.remaining:
                        utility = job["value"] / max(1, cost)**0.85 + 1000*job.get("priority", 0)
                        options.append((utility, -cost, job))
        # Empty sites are investment opportunities; choose close ones, but
        # value each commodity against all visible committed production.
        if not self.final and self.hour <= 16:
            available = self.money - self.reserved_capital() - max(40, self.animals*5)
            projects = sorted(self.values.items(), key=lambda p: p[1].get("score", -1), reverse=True)
            counts = {}
            for existing in self.jobs.values():
                if existing["kind"] == "invest":
                    key = existing["item"]
                    counts[key] = counts.get(key, 0) + 1
            visible = {}
            for row in self.tiles:
                for tile in row:
                    if isinstance(tile, dict):
                        item = tile.get("crop", tile.get("animal"))
                        if item:
                            visible[item] = visible.get(item, 0)+1
            slow_crops = sum(visible.get(k, 0)+counts.get(k, 0)
                             for k in ("STRAWBERRY", "TOMATO"))
            occupied = self.animals+self.crops+sum(counts.values())
            for item, value in projects:
                capital = CROP[item][0] if item in CROP else ANIMAL[item][0]
                if value.get("score", 0) <= MIN_PROJECT_SCORE or capital > available:
                    continue
                if item in ("STRAWBERRY", "TOMATO") and self.today >= 10 and occupied >= 20:
                    if slow_crops/occupied >= EARLY_SLOW_CROP_LIMIT:
                        continue
                empties = []
                for y, row in enumerate(self.tiles):
                    for x, tile in enumerate(row):
                        if (x, y) in claimed or tile == "LOCKED":
                            continue
                        if tile is None or isinstance(tile, dict) and tile.get("kind") in ("WEED", "COOP", "PASTURE") and not tile.get("animal"):
                            empties.append((_distance(self.positions[idx], (x, y)), x, y))
                for _, x, y in sorted(empties)[:3]:
                    job = dict(kind="invest", target=(x, y), item=item, value=value.get("net", 0))
                    cost = self.cost(idx, job)
                    if cost > self.remaining:
                        continue
                    score = value["score"] / (1 + 0.22*counts.get(item, 0))
                    if self.today >= 18 and item in ("WHEAT", "CARROT"):
                        # Short crops can occupy land that aging strawberries
                        # will release before the terminal sale deadline.
                        score += LATE_STAPLE_BONUS
                    utility = score * 3.0 / max(1, cost)**0.55
                    options.append((utility, -cost, job))
        if not options:
            return None
        return max(options, key=lambda p: (p[0], p[1]))[2]

    def act_job(self, idx, job):
        pos = self.positions[idx]
        inv = self.inventory[idx]
        if job["kind"] == "deliver":
            depot, distance = self.near_shed(pos)
            if distance:
                return _move(pos, depot)
            for k, n in list(inv.items()):
                room = max(0, self.capacity-sum(self.shed.values()))
                self.shed[k] = self.shed.get(k, 0)+min(n, room)
            inv.clear()
            self.jobs.pop(idx, None)
            return ["DROP"]
        ops = self.remaining_ops(job)
        need = self.supplies(job, ops)
        missing = [k for k, n in need.items() if inv.get(k, 0) < n]
        if missing:
            depot, distance = self.near_shed(pos)
            if distance:
                return _move(pos, depot)
            item = missing[0]
            batch = min(4, self.animals+1) if item == "WHEAT" else 2 if item == "FERTILIZER" else 1
            n = min(batch, self.shed.get(item, 0))
            if n:
                self.shed[item] -= n
                inv[item] = inv.get(item, 0) + n
                return ["PICKUP", item, n]
            _STATS["wait_supply"] += 1
            return ["PASS"]
        move = _move(pos, job["target"])
        if move:
            return move
        if not ops:
            self.jobs.pop(idx, None)
            return ["PASS"]
        op = ops[0]
        if op == "PLANT":
            item = job["item"]
            if self.seeds.get(item, 0) <= 0:
                _STATS["wait_supply"] += 1
                return ["PASS"]
            self.seeds[item] -= 1
            return [op, item]
        if op == "PLACE":
            return [op, job["item"]]
        return [op]

    def market(self):
        orders = []
        seed_need, animal_need, supply_need = {}, {}, {}
        for idx, job in self.jobs.items():
            ops = self.remaining_ops(job)
            item = job.get("item")
            if "PLANT" in ops and self.emitted.get(idx, [None])[0] != "PLANT":
                seed_need[item] = seed_need.get(item, 0) + 1
            if "PLACE" in ops:
                animal_need[item] = animal_need.get(item, 0) + 1
            for k, n in self.supplies(job, ops).items():
                if k not in ANIMAL:
                    supply_need[k] = supply_need.get(k, 0)+max(0,n-self.inventory[idx].get(k,0))
        feed_reserve = 0 if self.final else max(supply_need.get("WHEAT", 0), self.animals+len(animal_need))
        fert_reserve = 0 if self.final else supply_need.get("FERTILIZER", 0)
        reserves = {"WHEAT": feed_reserve, "FERTILIZER": fert_reserve}
        # Unit deposits occur before this market queue, including same-turn
        # final-day delivery. Keep resources required by assigned jobs.
        sales = []
        for item in SELLABLE:
            qty = max(0, self.shed.get(item, 0)-reserves.get(item, 0))
            if qty:
                sales.append((self.prices.get(item, 0)*qty, item, qty))
        for _, item, qty in sorted(sales, reverse=True):
            orders.append(["SELL", item, qty])
            inventory = self.obs["market"]["inventory"][item]
            revenue = 0
            for _ in range(qty):
                p = price(item, inventory, self.cfg.get("marketParams"))
                revenue += p
                if p > 1:
                    inventory += 1
            self.money += revenue*0.85
        limit = int(self.cfg.get("maxMarketOrdersPerTurn", 10))
        def add(order, cost):
            if len(orders) < limit and cost <= self.money:
                orders.append(order)
                self.money -= cost
                return True
            return False
        hires = int(self.me.get("hires_today", 0))
        # A few cheap workers are needed to turn assets into saleable output;
        # retain them even when a whole day's feed order is unaffordable.
        if self.hour <= 2:
            while hires < min(5, self.desired_hands):
                cost = _fib(hires)*float(self.cfg.get("farmHandCostMult", 1))
                if not add(["HIRE"], cost):
                    break
                hires += 1
        for item, n in animal_need.items():
            owned = self.shed.get(item, 0)+sum(inv.get(item, 0) for inv in self.inventory)
            missing = max(0, n-owned)
            if missing:
                add(["BUY_ANIMAL", item, missing], missing*ANIMAL[item][0])
        for item, n in seed_need.items():
            missing = max(0, n-self.seeds.get(item, 0))
            if missing:
                add(["BUY_SEED", item, missing], missing*CROP[item][0])
        for item, desired in (("WHEAT", feed_reserve), ("FERTILIZER", fert_reserve)):
            missing = max(0, desired-self.shed.get(item, 0))
            if missing:
                unit_cost = self.prices.get(item, 100)+2
                affordable = min(missing, max(0, int((self.money-10)//unit_cost)))
                if affordable:
                    add(["BUY_PRODUCT", item, affordable], affordable*unit_cost)
        if self.hour <= 2:
            while hires < self.desired_hands:
                cost = _fib(hires)*float(self.cfg.get("farmHandCostMult", 1))
                if cost > max(0, self.money-50) or not add(["HIRE"], cost):
                    break
                hires += 1
        occupied = self.animals+self.crops
        empty = sum(t is None or isinstance(t, dict) and t.get("kind") == "WEED"
                    for row in self.tiles for t in row)
        lands = len(self.me.get("unlocked_quadrants", []))
        if lands < 4 and empty < 6 and self.today < 22 and occupied >= 15:
            cost = (1000, 2000, 4000)[max(0, lands-1)]
            if self.money > cost+1000:
                add(["BUY_LAND"], cost)
        return orders[:limit]

    def run(self, obs):
        self.read(obs)
        actions = []
        self.emitted = {}
        cargo_total = sum(sum(inv.values()) for inv in self.inventory)
        for idx, pos in enumerate(self.positions):
            inv = self.inventory[idx]
            job = self.jobs.get(idx)
            if job and not self.remaining_ops(job):
                self.jobs.pop(idx, None)
                job = None
            depot, distance = self.near_shed(pos)
            products = sum(v for k, v in inv.items() if k in SELLABLE and k != "WHEAT")
            products += max(0, inv.get("WHEAT", 0)-(3 if self.animals and not self.final else 0))
            urgent_return = bool(inv) and self.final and self.remaining <= distance+2
            sell_trip = (products > 0 and
                         (cargo_total >= self.capacity-25 or
                          products >= 10 and distance <= 2 or
                          self.final and self.hour >= 16))
            if urgent_return or sell_trip and not job:
                job = dict(kind="deliver", target=depot)
                self.jobs[idx] = job
                _STATS["forced_returns"] += 1
            if not job:
                claimed = {j["target"] for j in self.jobs.values() if j["kind"] != "deliver"}
                job = self.select_job(idx, claimed)
                if job:
                    self.jobs[idx] = job
                    _STATS["jobs"] += 1
                    if job["kind"] == "invest":
                        _STATS["investments"] += 1
                elif products and (self.final or distance < 3):
                    job = dict(kind="deliver", target=depot)
                    self.jobs[idx] = job
            if job:
                action = self.act_job(idx, job)
            else:
                action = ["PASS"]
            _STATS["passes"] += action[0] == "PASS"
            actions.append(action)
            self.emitted[idx] = action
        result = {"farmer": actions[0], "hands": actions[1:], "market": self.market()}
        self.last_step = self.step
        return result


def agent(observation, configuration=None):
    cfg = configuration if hasattr(configuration, "get") else {}
    player = int(observation.get("player", 0))
    step = int(observation.get("step", 0))
    state = _STATES.get(player)
    if state is None or step <= state.last_step:
        state = Planner(observation, cfg)
        _STATES[player] = state
    return state.run(observation)


agent.telemetry = _STATS
