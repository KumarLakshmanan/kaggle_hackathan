"""Purchase missing supplies immediately before an already scheduled use."""
import math as _proc_math

_PROC_PARENT = agent
_PROC_STATS = {"animal_units": 0, "seed_units": 0, "repair_turns": 0,
               "projection_errors": 0, "fund_turns": 0, "fund_errors": 0}
_PROC_PARAMS = {
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
_PROC_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def _proc_shape(kind, amount, threshold):
    x = max(0., float(amount))
    if kind == "sqrt":
        return _proc_math.sqrt(x)
    if kind == "sq":
        return x*x
    if kind == "log":
        return _proc_math.log1p(x)
    if kind == "log10":
        return _proc_math.log10(1.+x)
    if kind == "hinge" and threshold > 0:
        u = x/threshold
        return u + 8.*max(0., u-1.)**2
    return x


def _proc_price(item, inventory, overrides):
    base, threshold, below, below_target, above, above_target = _PROC_PARAMS[item]
    patch = overrides.get(item, {})
    base, threshold = patch.get("base", base), patch.get("T", threshold)
    i0 = patch.get("I0", 10000)
    low = inventory <= i0
    kind = patch.get("below_func" if low else "above_func", below if low else above)
    target = patch.get("below_target" if low else "above_target", below_target if low else above_target)
    shift = target*base/_proc_shape(kind, threshold, threshold)*_proc_shape(kind, abs(inventory-i0), threshold)
    return max(1, int(round(base + shift if low else base-shift)))


def _proc_project(obs, action, cfg):
    farm, private = obs["farms"][int(obs["player"])], obs["private"]
    stock = _fund_stock(obs, action, cfg)
    seeds = dict(private["seeds"])
    units = [action.get("farmer", [])] + action.get("hands", [])
    positions = [farm["farmer"]] + farm["hands"]
    requests = {}
    for unit in units:
        if len(unit) > 1 and unit[0] == "PLANT":
            requests[unit[1]] = requests.get(unit[1], 0) + 1
    for pos, unit in zip(positions, units):
        if len(unit) > 1 and unit[0] == "PLANT" and farm["tiles"][pos[1]][pos[0]] is None:
            crop = unit[1]
            if requests[crop] <= private["seeds"].get(crop, 0):
                seeds[crop] = max(0, seeds.get(crop, 0)-1)
    inventory = dict(obs["market"]["inventory"])
    params = obs["market"].get("params", {}) or {}
    money = float(farm["money"])
    hires = int(farm.get("hires_today", 0))
    owned = len(farm["unlocked_quadrants"])
    capacity = int(cfg.get("shedCapacity", 100))
    for order in action.get("market", [])[:int(cfg.get("maxMarketOrdersPerTurn", 10))]:
        if not order:
            continue
        op = order[0]
        if op == "HIRE":
            cost = _fund_fib(hires)*int(cfg.get("farmHandCostMult", 1))
            if money >= cost:
                money -= cost
                hires += 1
        elif op == "BUY_LAND" and owned < 4:
            cost = (1000, 2000, 4000)[owned-1]
            if money >= cost:
                money -= cost
                owned += 1
        elif len(order) >= 3:
            item, quantity = order[1], max(0, int(order[2]))
            # Engine deposits, stock and available cash bound successful units.
            if op == "SELL" and item in _PROC_PARAMS:
                for _ in range(min(quantity, stock.get(item, 0))):
                    price = _proc_price(item, inventory[item], params)
                    money += price
                    stock[item] -= 1
                    if price > 1:
                        inventory[item] += 1
            elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                for _ in range(min(quantity, max(0, capacity-sum(stock.values())))):
                    price = _proc_price(item, inventory[item]-1, params)
                    if money < price:
                        break
                    money -= price
                    stock[item] = stock.get(item, 0)+1
                    inventory[item] -= 1
            elif op in ("BUY_ANIMAL", "BUY_SEED"):
                cost = (_FUND_ANIMAL if op == "BUY_ANIMAL" else _FUND_SEED).get(item)
                if cost is None:
                    continue
                bought = min(quantity, int(money//cost))
                if op == "BUY_ANIMAL":
                    bought = min(bought, max(0, capacity-sum(stock.values())))
                    stock[item] = stock.get(item, 0)+bought
                else:
                    seeds[item] = seeds.get(item, 0)+bought
                money -= cost*bought
    return stock, seeds, money


def _proc_apply(obs, action, configuration):
    step, cfg = int(obs["step"]), configuration or {}
    if step >= 718 or (step+1) % 24 == 0 or (step+1) % 72 == 0:
        return action
    tape = _fund_tape(obs)
    if tape is None:
        return action
    orders = list(action.get("market", []))
    max_orders = int(cfg.get("maxMarketOrdersPerTurn", 10))
    if len(orders) >= max_orders:
        return action
    farm = obs["farms"][int(obs["player"])]
    positions = [farm["farmer"]] + farm["hands"]
    units = [action.get("farmer", [])] + action.get("hands", [])
    upcoming = [tape[step+1].get("farmer", [])] + tape[step+1].get("hands", [])
    size = int(cfg.get("boardSize", 10))
    half = size//2
    animals, plants = {}, {}
    for idx, (pos, now) in enumerate(zip(positions, units)):
        if idx >= len(upcoming):
            continue
        nxt = upcoming[idx]
        if len(nxt) < 2:
            continue
        x, y = pos
        if now and now[0] in _PROC_MOVES:
            dx, dy = _PROC_MOVES[now[0]]
            if 0 <= x+dx < size and 0 <= y+dy < size:
                x, y = x+dx, y+dy
        if nxt[0] == "PICKUP" and nxt[1] in _FUND_ANIMAL and x in (half-1, half) and y in (half-1, half):
            animals[nxt[1]] = animals.get(nxt[1], 0)+max(0, int(nxt[2]) if len(nxt) > 2 else 1)
        elif nxt[0] == "PLANT" and nxt[1] in _FUND_SEED:
            tile = farm["tiles"][y][x]
            cleared = False
            if list(pos) == [x, y] and now:
                if now[0] == "DIG" and tile != "LOCKED" and not (isinstance(tile, dict) and "animal" in tile):
                    cleared = True
                elif now[0] == "HARVEST" and isinstance(tile, dict):
                    crop = tile.get("crop")
                    first = {"WHEAT": 2, "CARROT": 2, "MELON": 10}.get(crop)
                    cleared = first is not None and tile.get("yield_units", 0) > 0 and step//24-tile["planted_day"] >= first
            if tile is None or cleared:
                plants[nxt[1]] = plants.get(nxt[1], 0)+1
    if not animals and not plants:
        return action
    stock, seeds, money = _proc_project(obs, action, cfg)
    added = 0
    for needs, available, costs, operation, counter in (
        (animals, stock, _FUND_ANIMAL, "BUY_ANIMAL", "animal_units"),
        (plants, seeds, _FUND_SEED, "BUY_SEED", "seed_units"),
    ):
        for item, need in needs.items():
            missing = max(0, need-available.get(item, 0))
            if not missing or len(orders) >= max_orders or money < missing*costs[item]:
                continue
            if operation == "BUY_ANIMAL" and sum(stock.values())+missing > int(cfg.get("shedCapacity", 100)):
                continue
            orders.append([operation, item, missing])
            available[item] = available.get(item, 0)+missing
            money -= missing*costs[item]
            _PROC_STATS[counter] += missing
            added += missing
    if added:
        action["market"] = orders
        _PROC_STATS["repair_turns"] += 1
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        for key in _PROC_STATS:
            _PROC_STATS[key] = 0
    action = _PROC_PARENT(observation, configuration)
    try:
        return _proc_apply(observation, action, configuration)
    except Exception:
        _PROC_STATS["projection_errors"] += 1
        return action
    finally:
        _PROC_STATS["fund_turns"] = _FUND_STATS["fund_turns"]
        _PROC_STATS["fund_errors"] = _FUND_STATS["fund_errors"]


agent.telemetry = _PROC_STATS


def kaggle_procurement_repair_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
