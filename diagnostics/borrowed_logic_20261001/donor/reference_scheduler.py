"""Stateless, observation-only farm execution and conservative investment policy.

All worker commands are applied to a private copy with the authoritative native
transition before the next worker is assigned. Prices beyond the current turn
are bounded heuristics, not guaranteed receipts. No episode identity, seed,
opponent identity, recorded actions, or persistent process state is used.
"""
import copy
import math

from . import native_core as core


def _get(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def _context(observation, configuration=None):
    cfg = configuration or {}
    farms = _get(observation, "farms", [])
    seat = int(_get(observation, "player", 0))
    farm = farms[seat]
    tpd = max(1, int(_get(cfg, "turnsPerDay", 24)))
    step = int(_get(observation, "step", int(_get(observation, "day", 0)) * tpd
                    + int(_get(observation, "hour", 0))))
    end = max(1, int(_get(cfg, "episodeSteps", 720))) - 2
    return farm, _get(observation, "private", {}), tpd, step, end


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _move(source, target):
    # Locked ground is traversable, so Manhattan paths are always legal.
    if source[0] != target[0]:
        return ["EAST" if source[0] < target[0] else "WEST"]
    return ["SOUTH" if source[1] < target[1] else "NORTH"]


def _tiles(farm):
    return [(x, y, tile) for y, row in enumerate(farm["tiles"])
            for x, tile in enumerate(row) if tile != "LOCKED"]


def _prices(observation, configuration, horizon=4):
    """Current-shop demand, with visible farm supply and a short forecast cap."""
    cfg = configuration or {}
    market = _get(observation, "market", {})
    params = core._resolve_market_params(market.get("params"))
    inventory = market.get("inventory", {})
    tpd = max(1, int(_get(cfg, "turnsPerDay", 24)))
    demand = {p: tpd / max(1, int(_get(cfg, "townCenterSellInterval", 24)))
              for p in core.PRODUCTS}
    demand["FERTILIZER"] = 0.0
    shop_rate = tpd / max(1, int(_get(cfg, "townShopSellInterval", 4)))
    for shop in _get(observation, "town", {}).get("unlocked_shops", []):
        products = core.SHOPS.get(shop, [])
        for p in products:
            demand[p] += shop_rate * (2 if len(products) == 1 else 1)
    supply = {p: 0.0 for p in core.PRODUCTS}
    for farm in _get(observation, "farms", []):
        for _, _, tile in _tiles(farm):
            if not isinstance(tile, dict):
                continue
            if tile.get("animal") in core.ANIMALS:
                data = core.ANIMALS[tile["animal"]]
                supply[data["product"]] += (1 + data["interval"]) / data["interval"]
                supply["FERTILIZER"] += 0.75
            elif tile.get("crop") in core.CROPS:
                data = core.CROPS[tile["crop"]]
                supply[tile["crop"]] += (4 / (data["first_yield_day"] + 4)
                                           if data["ongoing"] else
                                           data["max_yield"] / (data["max_yield_day"] + 1))
    values = {}
    for item in core.PRODUCTS:
        now = float(market.get("prices", {}).get(item, params[item]["base"]))
        stock = inventory.get(item, params[item]["I0"])
        projected = stock + (supply[item] - demand[item]) * min(6, max(0, horizon))
        future = core.market_price(item, projected, params)
        # Keep demand extrapolation local; later shops and rival actions are unknown.
        future = min(future, max(1.5 * now, 2 * params[item]["base"]))
        values[item] = max(1.0, 0.6 * now + 0.4 * future)
    return values


def _crop_returns(crop, remaining_days, prices, age=0, held=0):
    data = core.CROPS[crop]
    if data["ongoing"]:
        future = [d for d in range(data["first_yield_day"],
                                   data["first_yield_day"] + 4 * data["interval"],
                                   data["interval"])
                  if age < d <= age + remaining_days]
        return held * prices[crop] + sum(prices[crop] * 0.965 ** (d - age) for d in future)
    harvest_day = min(data["max_yield_day"], age + remaining_days)
    if harvest_day < data["first_yield_day"]:
        return 0.0
    start = (data["max_yield_day"] + 1) // 2
    units = min(data["max_yield"], max(1, held) + max(0, harvest_day - max(age, start - 1)))
    return units * prices[crop] * 0.965 ** max(0, harvest_day - age)


def _investment_values(prices, days, style):
    """Profit and economic productivity, charging feed and finite daily labor."""
    crop_values, animal_values = {}, {}
    for crop, data in core.CROPS.items():
        lifetime = data["first_yield_day"] + 3 * data["interval"] if data["ongoing"] else data["max_yield_day"]
        duration = min(days, lifetime)
        revenue = 0.85 * _crop_returns(crop, days, prices)
        labor = 3 + duration * 1.5 + (4 if data["ongoing"] else 1)
        net = revenue - data["seed"] - 1.5 * labor
        speed = max(1, duration + 1)
        # Capital tied up for ten days is less helpful during the opening.
        crop_values[crop] = (net, net / speed / (1 + labor / speed * 0.12))
    for animal, data in core.ANIMALS.items():
        product = data["product"]
        revenue = 0.0
        for age in range(data["first_yield_day"], days + 1, data["interval"]):
            units = min(data["max_held"], data["first_yield_day"] if age == data["first_yield_day"]
                        else 1 + data["interval"])
            revenue += units * prices[product] * 0.965 ** age
        # Fertilizer has no town demand: heavily discount its long-run price.
        revenue += max(0, days - 1) * min(prices["FERTILIZER"], 45) * 0.65
        labor = 4 + 5.2 * days
        net = 0.8 * revenue - data["cost"] - days * prices["WHEAT"] - 1.5 * labor
        if days < data["first_yield_day"]:
            net = -data["cost"]
        animal_values[animal] = (net, net / max(1, days) / 1.65)
    if style == "liquidate":
        crop_values = {c: (-1, -1) for c in crop_values}
        animal_values = {a: (-1, -1) for a in animal_values}
    return crop_values, animal_values


def asset_value(observation, configuration=None):
    """Discounted noncash value for search leaves, including own physical stock.

    This is a bounded economic estimate, not simulated future cash. Do not add
    another inventory-salvage term to it. At the final action there is no assumed
    terminal conversion of undelivered inventory or immature assets.
    """
    farm, private, tpd, step, end = _context(observation, configuration)
    if step > end:
        return 0.0
    day, last_day = step // tpd, end // tpd
    remaining = max(0, last_day - day)
    prices = _prices(observation, configuration)
    actual = _get(observation, "market", {}).get("prices", prices)
    value = sum(0.8 * min(prices.get(p, 0), actual.get(p, 0)) * n
                for p, n in private.get("shed", {}).items() if p in core.PRODUCTS)
    positions = [farm["farmer"], *farm.get("hands", [])]
    access = core._shed_access_tiles(len(farm["tiles"]))
    for idx, inv in enumerate(private.get("inventories", [])):
        distance = min(_distance(positions[idx], p) for p in access) if idx < len(positions) else 999
        can_deliver = end - step >= distance
        if can_deliver:
            value += sum(0.7 * min(prices.get(p, 0), actual.get(p, 0)) * n
                         for p, n in inv.items() if p in core.PRODUCTS)
    cv, av = _investment_values(prices, remaining, "balanced")
    for crop, n in private.get("seeds", {}).items():
        if crop in cv and cv[crop][0] > 0 and remaining >= core.CROPS[crop]["first_yield_day"]:
            value += n * min(core.CROPS[crop]["seed"], 0.25 * cv[crop][0])
    for animal, data in core.ANIMALS.items():
        unplaced = private.get("shed", {}).get(animal, 0) + sum(
            inv.get(animal, 0) for inv in private.get("inventories", []))
        if av[animal][0] > 0:
            value += unplaced * min(data["cost"], av[animal][0] * 0.35)
    future_value, daily_labor = 0.0, 0.0
    for x, y, tile in _tiles(farm):
        if not isinstance(tile, dict):
            continue
        if tile.get("crop") in core.CROPS:
            crop = tile["crop"]
            age = day - tile.get("planted_day", day)
            revenue = _crop_returns(crop, remaining, prices, age, tile.get("yield_units", 0))
            future_value += max(0, revenue * 0.65 - 2 * min(remaining, 10))
            daily_labor += 2
        elif tile.get("animal") in core.ANIMALS:
            animal = tile["animal"]
            data = core.ANIMALS[animal]
            age = day - tile.get("placed_day", day)
            revenue = tile.get("yield_units", 0) * prices[data["product"]]
            for delay in range(1, remaining + 1):
                if age + delay >= data["first_yield_day"] and (age + delay - data["first_yield_day"]) % data["interval"] == 0:
                    revenue += min(data["max_held"], 1 + data["interval"]) * prices[data["product"]] * 0.96 ** delay
            revenue += remaining * min(40, prices["FERTILIZER"]) * 0.6
            future_value += max(0, revenue * 0.65 - remaining * prices["WHEAT"] - 7 * remaining)
            daily_labor += 5.5
    # Value only a serviceable farm; no infinite forecast from planted assets.
    capacity = tpd * 0.7 * max(1, min(9, 1 + len(farm.get("hands", [])) + 2))
    return float(value + future_value * min(1.0, capacity / max(1, daily_labor)))


def schedule(observation, configuration=None, style="balanced"):
    """Produce coordinated worker commands followed by a funded market queue."""
    if style not in ("balanced", "growth", "liquidate"):
        style = "balanced"
    original, own, tpd, step, end = _context(observation, configuration)
    cfg = configuration or {}
    farm, private = copy.deepcopy(original), copy.deepcopy(own)
    private.setdefault("shed", {})
    private.setdefault("seeds", {})
    private.setdefault("inventories", [{}])
    size = len(farm["tiles"])
    day, hour = divmod(step, tpd)
    turns_left = min(tpd - hour, max(0, end - step + 1))
    remaining_days = max(0, end // tpd - day)
    capacity = max(0, int(_get(cfg, "shedCapacity", 100)))
    prices = _prices(observation, cfg)
    cv, av = _investment_values(prices, remaining_days, style)
    crop_order = sorted(cv, key=lambda c: (-cv[c][1], c))
    animal_order = sorted(av, key=lambda a: (-av[a][1], a))
    positions = [farm["farmer"], *farm.get("hands", [])]
    access = core._shed_access_tiles(size)
    reserved, commands = set(), []
    planned_pickup = 0
    planned_animals = {a: 0 for a in core.ANIMALS}

    for idx in range(len(positions)):
        pos = core._farmer_position(farm, idx)
        inv = core._farmer_inventory(private, idx)
        current_tiles = _tiles(farm)
        animals = [(x, y, t) for x, y, t in current_tiles if isinstance(t, dict) and t.get("animal") in core.ANIMALS]
        unfed = sum(not t.get("fed_today", False) for _, _, t in animals)
        carried_feed = sum(i.get("WHEAT", 0) for i in private["inventories"])
        shed_pos = min(access, key=lambda p: (_distance(pos, p), p))
        best = (0.0, None, ["PASS"], ["PASS"])

        def offer(target, command, value, work=1, deadline=None):
            nonlocal best
            target = tuple(target)
            distance = _distance(pos, target)
            shed_command = command[0] in ("DROP", "PICKUP") or (command[0] == "PLACE" and command[1] in core.PRODUCTS)
            if (target in reserved and not shed_command) or value <= 0:
                return
            if deadline is not None and distance + work > deadline:
                return
            # The target operation must fit before the hand disappears at midnight.
            if distance + work > turns_left:
                return
            score = value / (1 + 0.65 * distance + 0.3 * (work - 1))
            if score > best[0]:
                best = (score, target, command if distance == 0 else _move(pos, target), command)

        carrier = next((a for a in animal_order if inv.get(a, 0) > 0), None)
        if carrier:
            kind = core.ANIMALS[carrier]["structure"]
            homes = [(x, y, t) for x, y, t in current_tiles
                     if (x, y) not in reserved and (t is None or (isinstance(t, dict) and t.get("kind") == kind and "animal" not in t))]
            homes.sort(key=lambda p: (0 if p[2] is not None else 1, _distance(pos, p), p[1], p[0]))
            if homes:
                x, y, tile = homes[0]
                offer((x, y), ["PLACE", carrier] if tile else ["BUILD_" + kind],
                      200 + core.ANIMALS[carrier]["cost"] * 0.4)

        for x, y, tile in current_tiles:
            target = (x, y)
            if tile is None:
                if carrier:
                    continue
                for crop in crop_order:
                    if private["seeds"].get(crop, 0) and cv[crop][0] > 0 and turns_left > 1:
                        offer(target, ["PLANT", crop], 25 + min(85, cv[crop][1]) * (1.2 if style == "growth" else 1), work=2)
                        break
                continue
            if not isinstance(tile, dict):
                continue
            crop, animal = tile.get("crop"), tile.get("animal")
            if crop in core.CROPS:
                data = core.CROPS[crop]
                age = day - tile.get("planted_day", day)
                units = tile.get("yield_units", 0)
                watered = tile.get("watered_today", False)
                mature = age >= data["first_yield_day"] and units > 0
                window = (data["max_yield_day"] + 1) // 2 <= age <= data["max_yield_day"]
                can_increase = not data["ongoing"] and window and units < data["max_yield"]
                final = end - step < tpd
                if mature and (data["ongoing"] or age >= data["max_yield_day"] or units >= data["max_yield"] or final):
                    if not watered and can_increase and turns_left >= 2:
                        offer(target, ["WATER"], 100 + prices[crop] * (units + 1) * 0.6, work=2)
                    else:
                        delivery = min(_distance(target, p) for p in access) + 1 if remaining_days == 0 else 0
                        offer(target, ["HARVEST"], 85 + prices[crop] * units * 0.6, work=1 + delivery)
                if not watered and remaining_days > 0:
                    risk = tile.get("consecutive_unwatered", 0) >= 1
                    future = _crop_returns(crop, remaining_days, prices, age, units)
                    value = (45 + min(200, future * 0.2)) if risk else 9
                    if can_increase:
                        value += prices[crop] * 0.65
                    offer(target, ["WATER"], value)
                if inv.get("FERTILIZER", 0) and tile.get("fertilized_until_day", -1) < day and remaining_days:
                    bonus = (min(3, max(0, data["max_yield_day"] - age + 1)) if not data["ongoing"] and window else
                             min(3, 3 / max(1, data["interval"])) if data["ongoing"] and age + 3 >= data["first_yield_day"] else 0)
                    offer(target, ["FERTILIZE"], max(0, bonus * prices[crop] * 0.6 - prices["FERTILIZER"]))
                exhausted = (data["ongoing"] and age >= data["first_yield_day"] + 3 * data["interval"] and units == 0)
                if exhausted and any(private["seeds"].get(c, 0) and cv[c][0] > 0 for c in crop_order):
                    offer(target, ["DIG"], 30)
            elif animal in core.ANIMALS:
                data = core.ANIMALS[animal]
                product = data["product"]
                units = tile.get("yield_units", 0)
                if units:
                    delivery = min(_distance(target, p) for p in access) + 1 if remaining_days == 0 else 0
                    offer(target, ["HARVEST"], 90 + prices[product] * units * 0.65, work=1 + delivery)
                if not tile.get("fed_today", False) and inv.get("WHEAT", 0) and remaining_days:
                    urgency = 120 if tile.get("consecutive_unfed", 0) else 60
                    offer(target, ["FEED"], urgency + min(150, prices[product] * 0.75))
                if not tile.get("cared_today", False) and tile.get("fed_today", False) and remaining_days:
                    offer(target, ["CARE"], 20 + prices[product] * 0.65 / data["interval"])
                if tile.get("fertilizer_available", False):
                    delivery = min(_distance(target, p) for p in access) + 1 if remaining_days == 0 else 0
                    offer(target, ["COLLECT_FERTILIZER"], 15 + prices["FERTILIZER"] * 0.8, work=1 + delivery)
            elif tile.get("kind") == "WEED" and (carrier or any(private["seeds"].get(c, 0) and cv[c][0] > 0 for c in crop_order)):
                offer(target, ["DIG"], 35)

        # Supplies are physically owned by this worker only after an actual pickup.
        if not carrier:
            for animal in animal_order:
                if private["shed"].get(animal, 0) > planned_animals[animal] and remaining_days >= core.ANIMALS[animal]["first_yield_day"]:
                    space = any(t is None or (isinstance(t, dict) and t.get("kind") == core.ANIMALS[animal]["structure"] and "animal" not in t)
                                for _, _, t in current_tiles)
                    if space:
                        offer(shed_pos, ["PICKUP", animal, 1], 180)
                        break
        need = max(0, unfed - carried_feed - planned_pickup)
        if not inv.get("WHEAT", 0) and private["shed"].get("WHEAT", 0) and need and remaining_days:
            quantity = min(6, need, private["shed"]["WHEAT"])
            offer(shed_pos, ["PICKUP", "WHEAT", quantity], 130 + 10 * quantity)
        # Preserve animal/feed cargo when depositing saleable products.
        saleable = {p: n for p, n in inv.items() if p in core.PRODUCTS and n > 0
                    and not (p == "WHEAT" and unfed and remaining_days)}
        if saleable and sum(private["shed"].values()) < capacity:
            item = max(saleable, key=lambda p: (saleable[p] * prices[p], p))
            value = sum(n * prices[p] for p, n in saleable.items())
            terminal = end - step < tpd
            priority = 35 + value * (1.1 if terminal else 0.55)
            command = ["DROP"] if len(saleable) == len(inv) else ["PLACE", item, saleable[item]]
            offer(shed_pos, command, priority)
        _, target, command, intended = best
        if target is not None and tuple(pos) != target:
            # Reserve tasks, not worker locations: collocated work is legal.
            if intended[0] not in ("DROP", "PICKUP"):
                reserved.add(target)
            if intended[:2] == ["PICKUP", "WHEAT"]:
                planned_pickup += intended[2]
            elif intended[0] == "PICKUP" and intended[1] in planned_animals:
                planned_animals[intended[1]] += intended[2]
        core._apply_unit_action(farm, private, idx, command, size, day, tpd, capacity)
        commands.append(command)

    orders = _market(observation, cfg, farm, private, prices, cv, av, style,
                     tpd, hour, remaining_days, turns_left, capacity)
    return {"farmer": commands[0], "hands": commands[1:], "market": orders}


def _market(observation, cfg, farm, private, prices, cv, av, style,
            tpd, hour, days, turns_left, capacity):
    """Budget only after workers. Project each order, including Fibonacci hires."""
    market = copy.deepcopy(_get(observation, "market", {}))
    market.setdefault("inventory", {p: core.MARKET_I0 for p in core.PRODUCTS})
    orders = []
    limit = max(1, int(_get(cfg, "maxMarketOrdersPerTurn", 10)))
    size = len(farm["tiles"])
    hire_mult = max(0, int(_get(cfg, "farmHandCostMult", core.FARM_HAND_COST_MULT)))

    def order(op, item=None, quantity=1, reserve=0):
        if len(orders) >= limit or quantity <= 0:
            return 0
        if op in ("HIRE", "BUY_LAND"):
            cost = core._hire_cost(farm["hires_today"], hire_mult) if op == "HIRE" else core.LAND_PRICES[len(farm["unlocked_quadrants"]) - 1]
            if farm["money"] < cost + reserve:
                return 0
            (core._do_hire(farm, private, size, hire_mult) if op == "HIRE" else core._do_buy_land(farm, size))
            orders.append([op])
            return 1
        done = 0
        for _ in range(int(quantity)):
            if op == "BUY_SEED":
                price = core.CROPS[item]["seed"]
            elif op == "BUY_ANIMAL":
                price = core.ANIMALS[item]["cost"]
            else:
                stock = market["inventory"][item] - (1 if op == "BUY_PRODUCT" else 0)
                price = core.market_price(item, stock, market.get("params"))
            if op != "SELL" and farm["money"] < price + reserve:
                break
            if not core._commit_unit(op, item, price, farm, private, market, capacity):
                break
            done += 1
        if done:
            orders.append([op, item, done])
        return done

    tiles = _tiles(farm)
    animals = [t for _, _, t in tiles if isinstance(t, dict) and t.get("animal") in core.ANIMALS]
    crops = [t for _, _, t in tiles if isinstance(t, dict) and t.get("crop") in core.CROPS]
    unplaced = sum(private["shed"].get(a, 0) + sum(i.get(a, 0) for i in private["inventories"]) for a in core.ANIMALS)
    feed_held = sum(i.get("WHEAT", 0) for i in private["inventories"])
    animal_count = len(animals) + unplaced
    feed_reserve = max(0, min(capacity // 3, animal_count * min(2, days)) - feed_held)
    # Sell deposits made by this turn's workers, but never their still-carried goods.
    products = sorted(core.PRODUCTS, key=lambda p: (-private["shed"].get(p, 0) * prices[p], p))
    for item in products:
        qty = private["shed"].get(item, 0) - (feed_reserve if item == "WHEAT" else 0)
        order("SELL", item, max(0, qty))
    if turns_left <= 1:
        return orders
    # Feed commitments are funded before discretionary growth.
    missing_feed = max(0, feed_reserve - private["shed"].get("WHEAT", 0))
    order("BUY_PRODUCT", "WHEAT", missing_feed, reserve=2)
    best_crop = max(cv, key=lambda c: (cv[c][1], c))
    best_animal = max(av, key=lambda a: (av[a][1], a))
    empty = sum(t is None or (isinstance(t, dict) and t.get("kind") == "WEED") for _, _, t in tiles)
    seed_stock = sum(private["seeds"].values())
    base_reserve = max(8, animal_count * prices["WHEAT"] * 0.6)
    growth = style != "liquidate" and days >= 2
    # Staged bundles prevent buying a barnyard that cannot be staffed or placed.
    if growth and av[best_animal][0] > 0 and animal_count < max(1, len(tiles) // 3):
        space = empty - min(seed_stock, empty) - unplaced
        empty_home = any(isinstance(t, dict) and t.get("kind") == core.ANIMALS[best_animal]["structure"] and "animal" not in t for _, _, t in tiles)
        if (space > 0 or empty_home) and unplaced < 2 and (av[best_animal][1] >= cv[best_crop][1] * 0.65 or not crops):
            # Buying feed alongside an animal must leave money for workers.
            reserve = base_reserve + 2 * prices["WHEAT"] + 2 * core.CROPS[best_crop]["seed"]
            if order("BUY_ANIMAL", best_animal, 1, reserve):
                animal_count += 1
                unplaced += 1
                order("BUY_PRODUCT", "WHEAT", min(2, days), reserve=base_reserve)
    if growth and cv[best_crop][0] > 0:
        planting_room = max(0, empty - seed_stock - unplaced)
        # Seed purchases are a one-day work queue, not unlimited asset accumulation.
        daily_capacity = max(1, min(10, (turns_left * max(2, len(farm["hands"]) + 1) - 2 * len(crops) - 4 * animal_count) // 4))
        qty = min(planting_room, max(0, daily_capacity - seed_stock))
        order("BUY_SEED", best_crop, qty, reserve=base_reserve)
    pending_plants = min(empty, sum(n for crop, n in private["seeds"].items() if crop in cv and cv[crop][0] > 0))
    day = int(_get(observation, "step", 0)) // tpd
    maintenance = sum((bool(days) and not t.get("watered_today", False)) * 2
                      + (bool(t.get("yield_units", 0)) and day - t.get("planted_day", day) >= core.CROPS[t["crop"]]["first_yield_day"])
                      for t in crops)
    maintenance += sum(2 * (bool(days) and not t.get("fed_today", False)) + (bool(days) and not t.get("cared_today", False))
                       + bool(t.get("yield_units", 0)) + bool(t.get("fertilizer_available", False)) for t in animals)
    work = maintenance + pending_plants * 4 + unplaced * 5
    desired = max(1, min(12, math.ceil(work / max(1, (turns_left - 1) * 0.72))))
    if work and hour <= tpd // 3:
        desired = max(desired, min(3, 1 + len(crops) // 6 + animal_count // 3 + bool(pending_plants)))
    while len(farm["hands"]) + 1 < desired and turns_left >= 4:
        cost = core._hire_cost(farm["hires_today"], hire_mult)
        if cost > max(3, (turns_left - 2) * min(12, max(prices.values()) * 0.04)):
            break
        if not order("HIRE", reserve=2 + animal_count * prices["WHEAT"] * 0.2):
            break
    # Expansion only after current ground and labor can actually use more room.
    extras = len(farm["unlocked_quadrants"]) - 1
    if growth and extras < len(core.LAND_PRICES) and days >= 5 and empty <= 2 and cv[best_crop][0] > 0:
        land_cost = core.LAND_PRICES[extras]
        future_net = (size // 2) ** 2 * cv[best_crop][0] * 0.55
        if future_net > land_cost * (1.2 if style == "growth" else 1.6):
            order("BUY_LAND", reserve=base_reserve + 4 * core.CROPS[best_crop]["seed"])
    return orders
