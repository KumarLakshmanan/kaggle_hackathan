"""Small public-state investment model for Kaggriculture 1.32.7.

Price curves are exact. Production assumes successful future service; market
forecasts approximate within-day sale timing and unknown future shops. Those
approximations are deliberately separate from observed game facts.
"""

from __future__ import annotations

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
