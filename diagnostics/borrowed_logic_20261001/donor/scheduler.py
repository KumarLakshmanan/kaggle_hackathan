"""Stateless, observation-only farm execution and conservative investment policy.

All worker commands are applied to a private copy with the authoritative native
transition before the next worker is assigned. Prices beyond the current turn
are bounded heuristics, not guaranteed receipts. No episode identity, seed,
opponent identity, recorded actions, or persistent process state is used.
"""
import copy
import math

from . import native_core as core
from . import commitments


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


def asset_value(observation, configuration=None, prices=None, regime="central", summary=None):
    """Net continuation cash from one complete owned commitment book."""
    return commitments.asset_value(observation, configuration, prices=prices, regime=regime, summary=summary)


def _rescue_value(tile, day, last_day, prices, final_actions=None, delivery_travel=0,
                  market_slots=10):
    """Two explicit continuation policies versus abandoning an endangered animal.

    Acquisition is sunk; held output has equal salvage in the two alternatives.
    It still occupies native storage until an assumed future-day harvest. Keep
    native refresh dates, pending care, clipping and two-unfed-day escape. Test
    each finite prefix of daily feed/care and minimum-survival feeding, followed
    by retirement, rather than obliging either policy to fund a negative tail.
    Future service, equal salvage and constant prices remain estimates, not a
    proof that retirement is optimal. This is not a portfolio optimizer.
    """
    data = core.ANIMALS[tile['animal']]
    wheat = max(1., prices.get('WHEAT', 25.))
    product = max(1., prices.get(data['product'], 1.))
    fertilizer = min(45., max(0., prices.get('FERTILIZER', 0.)))
    labor = 1.5
    values = []
    for daily_care in (False, True):
        hunger = int(tile.get('consecutive_unfed', 0))
        pending = int(tile.get('pending_care_bonus', 0))
        held = max(0, int(tile.get('yield_units', 0)))
        held_fertilizer = bool(tile.get('fertilizer_available', False))
        new_held, new_fertilizer = 0, False
        value, best = 0., None
        for current in range(day, last_day+1):
            discount = .965 ** (current-day)
            if current > day:
                # Each intermediate day's harvest deposits at midnight and can
                # sell next day. The final day must collect and deliver itself.
                receipts = [new_held*product] if new_held else []
                if new_fertilizer:
                    receipts.append(fertilizer)
                if current == last_day:
                    available = final_actions if final_actions is not None else 1000000
                    receipts.sort(reverse=True)
                    options = [0.]
                    for take in range(1, len(receipts)+1):
                        work = delivery_travel+take+1
                        sales_delay = (take-1)//max(1, market_slots)
                        if work+sales_delay <= available:
                            options.append(sum(receipts[:take])-labor*(work+sales_delay))
                    gain = max(options)
                else:
                    # Collection labor is paid today; midnight cargo can be
                    # sold only in the following day's market phase.
                    gain = sum(max(0., .965*revenue-labor) for revenue in receipts)
                value += discount*max(0., gain)
                best = value if best is None else max(best, value)
                held, new_held, held_fertilizer, new_fertilizer = 0, 0, False, False
            if current == last_day:
                break
            feed = daily_care or hunger >= 1
            care = daily_care or (current == day and tile.get('cared_today', False))
            if feed:
                # Feed, amortized pickup and a shared-tile-tour travel charge.
                value -= discount * (wheat + labor * 2.25)
                hunger = 0
            else:
                hunger += 1
            if hunger >= 2:
                break
            next_day = current + 1
            since_first = next_day-tile.get('placed_day', day)-data['first_yield_day']
            if since_first >= 0 and since_first % data['interval'] == 0:
                units = min(max(0, data['max_held']-held), 1 + (pending if feed else 0))
                held += units
                new_held += units
                pending = 0
            # Each survived refresh exposes one collectable fertilizer unit.
            new_fertilizer = not held_fertilizer
            held_fertilizer = True
            if feed and care:
                pending += 1
                if current != day or not tile.get('cared_today', False):
                    value -= discount*labor
        values.append(best if best is not None else 0.)
    return max(values, default=0.)


def _feed_route(position, carried, targets, access):
    """One worker's exact feed-only tour, with one real batched pickup if needed."""
    position = tuple(position)
    carried = max(0, int(carried))
    cost, first, pickup = 0, None, 0
    for offset, target in enumerate(targets):
        if not carried:
            shed = min(access, key=lambda p: (_distance(position, p)+_distance(p, target), p))
            distance = _distance(position, shed)
            pickup = len(targets)-offset
            if first is None:
                first = _move(position, shed) if distance else ['PICKUP', 'WHEAT', pickup]
            cost += distance+1
            position, carried = tuple(shed), pickup
        distance = _distance(position, target)
        if first is None:
            first = _move(position, target) if distance else ['FEED']
        cost += distance+1
        position, carried = tuple(target), carried-1
    return dict(targets=list(targets), turns=cost, pickup=pickup,
                first=first or ['PASS'], end=position, carried=carried)


def _assign_feed_jobs(farm, private, jobs, turns):
    """Bounded, deterministic custody-aware coverage, not an optimal tour proof.

    Each target and each shed unit belongs to at most one route. Appending or
    prepending a job gives at most two choices per worker, rather than an
    unbounded assignment/permutation search. Uncovered jobs stay explicit.
    """
    positions = [farm['farmer'], *farm.get('hands', [])]
    inventories = private.get('inventories', [])
    wheat = [max(0, int(inventories[i].get('WHEAT', 0))) if i < len(inventories) else 0
             for i in range(len(positions))]
    access = core._shed_access_tiles(len(farm['tiles']))
    shed = max(0, int(private.get('shed', {}).get('WHEAT', 0)))
    routes = [_feed_route(p, w, [], access) for p, w in zip(positions, wheat)]
    reserved = 0
    def difficulty(job):
        costs = [_feed_route(p, w, [job['target']], access) for p, w in zip(positions, wheat)]
        feasible = [r['turns'] for r in costs if r['turns'] <= turns and r['pickup'] <= shed]
        return (len(feasible), turns-min(feasible, default=turns+1), -job['value'], job['target'])
    for job in sorted(jobs, key=difficulty):
        choices = []
        for index, route in enumerate(routes):
            for targets in (route['targets']+[job['target']], [job['target']]+route['targets']):
                proposal = _feed_route(positions[index], wheat[index], targets, access)
                if proposal['turns'] > turns or reserved-route['pickup']+proposal['pickup'] > shed:
                    continue
                extra = proposal['turns']-route['turns']
                # The continuation ledger already pays a feed action and a
                # small shared-tour allowance; charge longer actual detours.
                if job['value'] <= 1.5*max(0, extra-2.25):
                    continue
                choices.append((extra, proposal['turns'], index, tuple(targets), proposal))
        if choices:
            _, _, index, _, proposal = min(choices, key=lambda c:c[:4])
            reserved += proposal['pickup']-routes[index]['pickup']
            routes[index] = proposal
    assigned = {target for route in routes for target in route['targets']}
    return dict(routes=routes, assigned=sorted(assigned),
                unassigned=[job['target'] for job in jobs if job['target'] not in assigned],
                shed_reserved=reserved, turns=turns)


def feed_service_plan(observation, configuration=None, prices=None):
    """Audit profitable imminent escape obligations using only this observation.

    This is a survival deadline guard, not a guarantee of daily feeding/care.
    Retirements are allowed when neither stated continuation policy repays its
    future feed/service cost, or no saleable refresh remains in the episode.
    """
    farm, private, tpd, step, end = _context(observation, configuration)
    day, hour = divmod(step, tpd)
    turns = max(0, min(tpd-hour, end-step+1))
    prices = prices or _prices(observation, configuration)
    jobs, retirements = [], []
    access = core._shed_access_tiles(len(farm['tiles']))
    final_actions = end % tpd+1
    for x, y, tile in _tiles(farm):
        if (not isinstance(tile, dict) or tile.get('animal') not in core.ANIMALS
                or tile.get('fed_today', False) or tile.get('consecutive_unfed', 0) < 1):
            continue
        target = (x, y)
        delivery_travel = (_distance(core._default_spawn(len(farm['tiles'])), target)
                           + min(_distance(target, p) for p in access))
        value = _rescue_value(tile, day, end//tpd, prices, final_actions, delivery_travel,
                              max(1, int(_get(configuration, 'maxMarketOrdersPerTurn', 10)))) if turns else 0.
        entry = dict(target=(x, y), animal=tile['animal'], value=value)
        (jobs if value > 0 else retirements).append(entry)
    plan = _assign_feed_jobs(farm, private, jobs, turns)
    plan.update(jobs=jobs, retirements=retirements)
    return plan


def _project_service_workers(observation, cfg, commands):
    original, own, tpd, step, _ = _context(observation, cfg)
    farm, private = copy.deepcopy(original), copy.deepcopy(own)
    for index, command in enumerate(commands):
        core._apply_unit_action(farm, private, index, command, len(farm['tiles']),
                                step//tpd, tpd, int(_get(cfg, 'shedCapacity', 100)))
    return farm, private


def repair_feed_service(observation, configuration, action, prices=None, return_report=False):
    """Preserve the last executable rescue window across every search executor.

    A normal command is retained when its ordered native worker projection
    still covers all currently assigned profitable rescues. Otherwise reserve
    the feeding workers' first route steps. Market orders are then re-funded
    against the changed worker state, preserving rescue wheat and refusing
    discretionary growth while any profitable deadline remains uncovered.
    """
    cfg = configuration or {}
    plan = feed_service_plan(observation, cfg, prices)
    report = dict(jobs=plan['jobs'], retirements=plan['retirements'],
                  before_unassigned=plan['unassigned'], forced_workers=[])
    if not plan['jobs']:
        return (action, report) if return_report else action
    farm, private, tpd, step, end = _context(observation, cfg)
    count = len(farm.get('hands', []))+1
    commands = [copy.deepcopy(action.get('farmer', ['PASS']))]
    commands += copy.deepcopy(list(action.get('hands', []))[:count-1])
    commands += [['PASS'] for _ in range(count-len(commands))]
    turns_after = max(0, plan['turns']-1)
    def remaining(projected):
        return [job for job in plan['jobs']
                if not projected['tiles'][job['target'][1]][job['target'][0]].get('fed_today', False)]
    projected_farm, projected_private = _project_service_workers(observation, cfg, commands)
    pending = remaining(projected_farm)
    after = _assign_feed_jobs(projected_farm, projected_private, pending, turns_after)
    fed = {job['target'] for job in plan['jobs']} - {job['target'] for job in pending}
    if not set(plan['assigned']).issubset(fed | set(after['assigned'])):
        for index, route in enumerate(plan['routes']):
            if route['targets']:
                commands[index] = list(route['first'])
                report['forced_workers'].append(index)
        # Earlier unrelated pickups cannot consume a later feeder's reservation.
        available = max(0, int(private.get('shed', {}).get('WHEAT', 0)))
        for index, command in enumerate(commands):
            if command[:2] != ['PICKUP', 'WHEAT']:
                continue
            if not core._is_shed_adjacent(core._farmer_position(farm, index), len(farm['tiles'])):
                continue
            later = sum(r['first'][2] for r in plan['routes'][index+1:]
                        if r['targets'] and r['first'][:2] == ['PICKUP', 'WHEAT'])
            take = min(int(command[2]) if len(command)>2 else 1, max(0, available-later))
            commands[index] = ['PICKUP', 'WHEAT', take] if take else ['PASS']
            available -= take
        projected_farm, projected_private = _project_service_workers(observation, cfg, commands)
        pending = remaining(projected_farm)
        after = _assign_feed_jobs(projected_farm, projected_private, pending, turns_after)
    # Exact own-side funding mirrors legalize. No worker can use these purchases
    # or new hires until the next turn, and no next-turn capacity exists at dusk.
    market = copy.deepcopy(_get(observation, 'market', {}))
    capacity = max(0, int(_get(cfg, 'shedCapacity', 100)))
    hire_mult = max(0, int(_get(cfg, 'farmHandCostMult', core.FARM_HAND_COST_MULT)))
    orders = []
    for original_order in action.get('market', [])[:max(1, int(_get(cfg, 'maxMarketOrdersPerTurn', 10)))]:
        order = list(original_order)
        op = order[0]
        discretionary = op in ('BUY_ANIMAL', 'BUY_SEED', 'BUY_LAND') or (op == 'BUY_PRODUCT' and order[1] != 'WHEAT')
        if discretionary and after['unassigned']:
            continue
        if op == 'HIRE':
            if not turns_after:
                continue
            cost = core._hire_cost(projected_farm.get('hires_today', 0), hire_mult)
            if projected_farm['money'] < cost:
                continue
            core._do_hire(projected_farm, projected_private, len(farm['tiles']), hire_mult)
            orders.append(order)
        elif op == 'BUY_LAND':
            extra = len(projected_farm['unlocked_quadrants'])-1
            if extra >= len(core.LAND_PRICES) or projected_farm['money'] < core.LAND_PRICES[extra]:
                continue
            core._do_buy_land(projected_farm, len(farm['tiles']))
            orders.append(order)
        else:
            item, quantity = order[1], min(200, max(0, int(order[2])))
            if op == 'SELL' and item == 'WHEAT':
                # Conservative even when unreachable carriers hold other wheat.
                quantity = min(quantity, max(0, projected_private['shed'].get('WHEAT', 0)-len(pending)))
            filled = 0
            for _ in range(quantity):
                price = (core.CROPS[item]['seed'] if op == 'BUY_SEED' else
                         core.ANIMALS[item]['cost'] if op == 'BUY_ANIMAL' else
                         core.market_price(item, market['inventory'][item]-int(op == 'BUY_PRODUCT'), market.get('params')))
                if not core._commit_unit(op, item, price, projected_farm, projected_private, market, capacity):
                    break
                filled += 1
            if filled:
                orders.append([op, item, filled])
        if op == 'HIRE' or (op == 'BUY_PRODUCT' and order[1] == 'WHEAT'):
            after = _assign_feed_jobs(projected_farm, projected_private, pending, turns_after)
    result = dict(farmer=commands[0], hands=commands[1:], market=orders)
    report['after_unassigned'] = after['unassigned']
    return (result, report) if return_report else result


def schedule(observation, configuration=None, style="balanced", policy=None):
    """Produce coordinated worker commands followed by a funded market queue."""
    policy = policy or {}
    if policy.get("focus") == "liquidate":
        style = "liquidate"
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
    # Purchased seeds are already-owned obligations. The legacy short/spot
    # proxy must not veto execution of a funded multi-day commitment merely
    # because today's market differs from its future-price scenario.
    for crop, quantity in private["seeds"].items():
        if crop in core.CROPS and quantity > 0 and remaining_days >= core.CROPS[crop]["first_yield_day"] and style != "liquidate":
            cv[crop] = (max(1., cv[crop][0]), max(1., cv[crop][1]))
    crop_order = sorted(cv, key=lambda c: (-cv[c][1], c))
    animal_order = sorted(av, key=lambda a: (-av[a][1], a))
    if policy.get("item") in crop_order:
        crop_order.remove(policy["item"]); crop_order.insert(0, policy["item"])
    if policy.get("item") in animal_order:
        animal_order.remove(policy["item"]); animal_order.insert(0, policy["item"])
    positions = [farm["farmer"], *farm.get("hands", [])]
    access = core._shed_access_tiles(size)
    reserved, commands = set(), []
    planned_pickup = 0
    planned_animals = {a: 0 for a in core.ANIMALS}
    planned_seeds = {c: 0 for c in core.CROPS}

    for idx in range(len(positions)):
        pos = core._farmer_position(farm, idx)
        inv = core._farmer_inventory(private, idx)
        current_tiles = _tiles(farm)
        animals = [(x, y, t) for x, y, t in current_tiles if isinstance(t, dict) and t.get("animal") in core.ANIMALS]
        unfed = sum(not t.get("fed_today", False) for _, _, t in animals)
        # Distant or already-busy carriers cannot reserve every animal's feed.
        carried_feed = sum(min(i.get("WHEAT", 0), sum(
            not t.get("fed_today", False) and _distance(positions[j], (x,y))+1 <= turns_left
            for x,y,t in animals)) for j,i in enumerate(private["inventories"]) if j < len(positions))
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
                    if private["seeds"].get(crop, 0) > planned_seeds[crop] and cv[crop][0] > 0 and turns_left > 1:
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
            quantity = min(3, need, private["shed"]["WHEAT"])
            offer(shed_pos, ["PICKUP", "WHEAT", quantity], 130 + 10 * quantity)
        # Preserve animal/feed cargo when depositing saleable products.
        saleable = {p: n for p, n in inv.items() if p in core.PRODUCTS and n > 0
                    and not (p == "WHEAT" and unfed and remaining_days)}
        if saleable and sum(private["shed"].values()) < capacity:
            item = max(saleable, key=lambda p: (saleable[p] * prices[p], p))
            value = sum(n * prices[p] for p, n in saleable.items())
            terminal = end - step < tpd
            # Native midnight deposits every worker's inventory from anywhere.
            # Return early only for funding, overflow, or terminal liquidation;
            # otherwise finish the local production tour instead of yo-yoing.
            total_cargo = sum(sum(i.values()) for i in private["inventories"])
            room = capacity-sum(private["shed"].values())
            feed_bill = max(0, unfed-carried_feed)*prices["WHEAT"]
            urgent_cash = farm["money"] < max(12, feed_bill+4)
            overflow = total_cargo > room
            priority = (35+value*1.1 if terminal else
                        28+value*0.55 if urgent_cash or overflow else
                        8+value*0.04 if _distance(pos, shed_pos)==0 else 0)
            # DROP destroys overflow. PLACE preserves what cannot fit.
            all_saleable = len(saleable) == len(inv)
            command = ["DROP"] if all_saleable and sum(inv.values()) <= room else ["PLACE", item, min(saleable[item], room)]
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
            elif intended[0] == "PLANT":
                planned_seeds[intended[1]] += 1
        core._apply_unit_action(farm, private, idx, command, size, day, tpd, capacity)
        commands.append(command)

    orders = _market(observation, cfg, farm, private, prices, cv, av, style,
                     tpd, hour, remaining_days, turns_left, capacity, policy)
    action = {"farmer": commands[0], "hands": commands[1:], "market": orders}
    return repair_feed_service(observation, cfg, action, prices=prices)


def _market(observation, cfg, farm, private, prices, cv, av, style,
            tpd, hour, days, turns_left, capacity, policy=None):
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
    # The remaining queue is generated against complete observed commitments.
    # All worker effects and preceding sales/feed purchases are already included.
    projected = dict(observation)
    projected["farms"] = list(_get(observation, "farms", []))
    projected["farms"][int(_get(observation, "player", 0))] = farm
    projected["private"] = private
    projected["market"] = market
    focus = (policy or {}).get("item")
    can_expand = style != "liquidate" and days >= 2 and turns_left >= 4
    empty = sum(t is None or (isinstance(t, dict) and t.get("kind") == "WEED") for _,_,t in tiles)
    seed_stock = sum(private["seeds"].values())
    # A bounded pending work queue prevents purchasing a whole season twice.
    pending = seed_stock+unplaced
    planting_slots = max(0, empty-pending)
    queue_room = max(0, min(8, (turns_left*max(2,len(farm["hands"])+1))//4)-pending)
    # Current execution needs only an observed one-day service list. Do not
    # rebuild whole-season valuations on every movement/maintenance tick.
    day = int(_get(observation, "step", 0))//tpd
    work = pending*4
    for x,y,tile in tiles:
        if not isinstance(tile, dict):
            continue
        tasks = 0
        if tile.get("crop") in core.CROPS:
            data = core.CROPS[tile["crop"]]
            age = day-tile.get("planted_day", day)
            tasks += bool(days) and not tile.get("watered_today", False)
            tasks += bool(tile.get("yield_units", 0)) and age >= data["first_yield_day"]
        elif tile.get("animal") in core.ANIMALS:
            tasks += 1.25*(bool(days) and not tile.get("fed_today", False))
            tasks += bool(days) and not tile.get("cared_today", False)
            tasks += bool(tile.get("yield_units", 0))+bool(tile.get("fertilizer_available", False))
        if tasks:
            ingress = min(_distance((x,y), p) for p in [farm["farmer"], *farm.get("hands", [])])
            work += tasks+min(2, ingress)
    # Demand is optional when its marginal executable value is below wages.
    # Existing workers claim reachable bundles first, preventing the shrinking
    # clock from multiplying hires for the same still-unfinished assets.
    hire_audit = commitments.service_hires(projected, cfg, prices)
    for proposed in hire_audit:
        if not order("HIRE", reserve=2):
            break
    # Animal custody is serial, while distinct owned crop slots may execute
    # concurrently inside the bounded, explicitly staffed seed cohort.
    if not can_expand or not queue_room or unplaced:
        return orders
    shortlist = [focus] if focus in core.CROPS or focus in core.ANIMALS else True
    book = commitments.build_book(projected, cfg, style=style,
                                 regime=(policy or {}).get("regime", "central"),
                                 include_candidates=shortlist)
    candidates = [c for c in book["candidates"] if c["score"] > 0 and c["net"] > 0
                  and (c["kind"] != "crop" or c["quantity"] <= queue_room)]
    if focus:
        candidates = [c for c in candidates if c["item"] == focus]
    if (policy or {}).get("quantity"):
        candidates = [c for c in candidates if c["kind"] != "crop" or c["quantity"] <= int(policy["quantity"])]
    if (policy or {}).get("focus") == "crop":
        candidates = [c for c in candidates if c["kind"] in ("crop", "land")]
    elif (policy or {}).get("focus") == "animal":
        candidates = [c for c in candidates if c["kind"] == "animal"]
    for candidate in candidates:
        # This cash trough includes every currently owned crop/animal's future
        # feed/wages and the entire prospective programme, before its receipts.
        if farm["money"]+1e-9 < candidate["required_cash"]:
            continue
        item, kind = candidate["item"], candidate["kind"]
        if kind == "land":
            if pending or planting_slots > 1:
                continue
            reserve = max(book["reserve"], candidate["upfront"]-core.LAND_PRICES[len(farm["unlocked_quadrants"])-1])
            if order("BUY_LAND", reserve=reserve):
                # Seeds are purchased next turn against the newly observed slots.
                break
        elif kind == "animal":
            if unplaced or planting_slots < 1:
                continue
            price = core.ANIMALS[item]["cost"]
            reserve = max(2, candidate["required_cash"]-price)
            if order("BUY_ANIMAL", item, 1, reserve=reserve):
                order("BUY_PRODUCT", "WHEAT", min(2, days), reserve=max(2, book["reserve"]))
                break
        elif planting_slots:
            # One marginal bundle per turn; owned seed stock is credited next
            # call. Root policy persists, so this is progressive portfolio fill.
            quantity = candidate.get("quantity", 1)
            price = core.CROPS[item]["seed"]*quantity
            if order("BUY_SEED", item, quantity, reserve=max(2,candidate["required_cash"]-price)):
                # A real cohort is staffed against its now-owned seeds, after
                # their purchase, rather than serialized behind one planter.
                for proposed in commitments.service_hires(projected, cfg, prices):
                    if not order("HIRE", reserve=2):
                        break
                break
    return orders
