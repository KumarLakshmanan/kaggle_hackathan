"""Advance earmarked sales only to prevent a recorded land purchase failure."""
import math as _fund_math

_FUND_PARENT = agent
_FUND_STATS = {"fund_turns": 0, "fund_units": 0, "fund_errors": 0}
_FUND_DEBTS = {}
_FUND_SEED = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
_FUND_ANIMAL = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
_FUND_ITEMS = {"CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"}


def _fund_tape(obs):
    step, shops = int(obs["step"]), obs["town"]["unlocked_shops"]
    route = None
    for count in range(1, min(8, len(shops)) + 1):
        if step >= 72 * count:
            route = _DATA["route_map"].get("|".join(shops[:count]), route)
    return _DATA["routes"][str(route)] if route is not None else None


def _fund_fib(n):
    a, b = 1, 1
    for _ in range(max(0, int(n))):
        a, b = b, a + b
    return a


def _fund_stock(obs, action, cfg):
    farm, private = obs["farms"][int(obs["player"])], obs["private"]
    stock = dict(private["shed"])
    half, cap = int(cfg.get("boardSize", 10)) // 2, int(cfg.get("shedCapacity", 100))
    positions = [farm["farmer"]] + farm["hands"]
    units = [action.get("farmer", [])] + action.get("hands", [])
    for pos, unit, inv in zip(positions, units, private["inventories"]):
        if not unit or pos[0] not in (half - 1, half) or pos[1] not in (half - 1, half):
            continue
        if unit[0] == "PICKUP" and len(unit) > 1:
            item, qty = unit[1], max(0, int(unit[2]) if len(unit) > 2 else 1)
            stock[item] = max(0, stock.get(item, 0) - qty)
        elif unit[0] == "DROP":
            for item, qty in inv.items():
                stock[item] = stock.get(item, 0) + min(max(0, int(qty)), max(0, cap - sum(stock.values())))
        elif unit[0] == "PLACE" and len(unit) > 1 and unit[1] not in _FUND_ANIMAL:
            item, qty = unit[1], max(0, int(unit[2]) if len(unit) > 2 else 1)
            stock[item] = stock.get(item, 0) + min(qty, int(inv.get(item, 0)), max(0, cap - sum(stock.values())))
    return stock


def _fund_apply(obs, action, configuration):
    step, cfg = int(obs["step"]), configuration or {}
    orders, debt = [], dict(_FUND_DEBTS.pop(step, {}))
    for raw in action.get("market", []):
        order = list(raw)
        if len(order) >= 3 and order[0] == "SELL" and debt.get(order[1], 0):
            paid = min(max(0, int(order[2])), debt[order[1]])
            debt[order[1]] -= paid
            order[2] -= paid
            if order[2] <= 0:
                continue
        orders.append(order)
    action["market"] = orders
    if not any(o and o[0] == "BUY_LAND" for o in orders):
        return action
    cap = int(cfg.get("maxMarketOrdersPerTurn", 10))
    if len(orders) >= cap:
        return action
    farm = obs["farms"][int(obs["player"])]
    owned = len(farm["unlocked_quadrants"])
    if owned >= 4:
        return action
    tape = _fund_tape(obs)
    if tape is None:
        return action
    prices, stock = obs["market"]["prices"], _fund_stock(obs, action, cfg)
    projected, money = dict(stock), float(farm["money"])
    hires, shortfall = int(farm.get("hires_today", 0)), 0.0
    for order in orders:
        if not order:
            continue
        op = order[0]
        if op == "BUY_LAND":
            shortfall = (1000, 2000, 4000)[owned - 1] - money
            break
        if op == "HIRE":
            money -= _fund_fib(hires) * float(cfg.get("farmHandCostMult", 1))
            hires += 1
        elif len(order) >= 3:
            item, qty = order[1], max(0, int(order[2]))
            if op == "SELL":
                sold = min(qty, projected.get(item, 0))
                projected[item] = projected.get(item, 0) - sold
                money += sold * float(prices.get(item, 0))
            elif op == "BUY_SEED":
                money -= qty * _FUND_SEED.get(item, 100)
            elif op == "BUY_ANIMAL":
                money -= qty * _FUND_ANIMAL.get(item, 500)
            elif op == "BUY_PRODUCT":
                money -= qty * (float(prices.get(item, 100)) + 1)
    if shortfall <= 0:
        return action
    excluded = {o[1] for o in orders if len(o) > 1 and o[0] in ("BUY_PRODUCT", "BUY_ANIMAL")}
    for order in orders:
        if len(order) >= 3 and order[0] == "SELL":
            stock[order[1]] = max(0, stock.get(order[1], 0) - max(0, int(order[2])))
    protected, additions, bookings = set(), {}, []
    proceeds = 0.0
    for future in range(step + 1, min(step + 8, 718) + 1):
        if future // 24 != step // 24:
            break
        turn = tape[future]
        for unit in [turn.get("farmer", [])] + turn.get("hands", []):
            if len(unit) > 1 and unit[0] == "PICKUP":
                protected.add(unit[1])
        for sale in turn.get("market", []):
            if len(sale) < 3 or sale[0] != "SELL":
                continue
            item = sale[1]
            if item not in _FUND_ITEMS or item in protected or item in excluded:
                continue
            price = float(prices.get(item, 0))
            if price <= 1 or (item not in additions and len(orders) + len(additions) >= cap):
                continue
            future_left = max(0, int(sale[2]) - _FUND_DEBTS.get(future, {}).get(item, 0))
            qty = min(stock.get(item, 0), future_left,
                      max(0, int(_fund_math.ceil((shortfall - proceeds) / price))))
            if qty <= 0:
                continue
            stock[item] -= qty
            additions[item] = additions.get(item, 0) + qty
            bookings.append((future, item, qty))
            proceeds += qty * price
        if proceeds >= shortfall:
            break
    if proceeds < shortfall:
        return action
    for future, item, qty in bookings:
        future_debt = _FUND_DEBTS.setdefault(future, {})
        future_debt[item] = future_debt.get(item, 0) + qty
    action["market"] = [["SELL", item, qty] for item, qty in additions.items()] + orders
    _FUND_STATS["fund_turns"] += 1
    _FUND_STATS["fund_units"] += sum(additions.values())
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _FUND_DEBTS.clear()
        _FUND_STATS.update(fund_turns=0, fund_units=0, fund_errors=0)
    action = _FUND_PARENT(observation, configuration)
    try:
        return _fund_apply(observation, action, configuration)
    except Exception:
        _FUND_STATS["fund_errors"] += 1
        return action


agent.telemetry = _FUND_STATS


def kaggle_land_prefund_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
