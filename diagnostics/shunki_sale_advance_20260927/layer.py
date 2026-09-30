"""Sell already-delivered scheduled cash products up to four turns early."""
_SALE_PARENT = agent
_SALE_ITEMS = {"CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"}
_SALE_STATS = {"sale_advance_turns": 0, "sale_advance_units": 0,
               "sale_queue_turns": 0, "sale_errors": 0}
_SALE_DEBTS = {}


def _sale_stock(obs, action, cfg):
    farm = obs["farms"][int(obs["player"])]
    private = obs["private"]
    stock = dict(private["shed"])
    half = int(cfg.get("boardSize", 10)) // 2
    cap = int(cfg.get("shedCapacity", 100))
    positions = [farm["farmer"]] + farm["hands"]
    units = [action.get("farmer", [])] + action.get("hands", [])
    for pos, unit, inv in zip(positions, units, private["inventories"]):
        if not unit or pos[0] not in (half - 1, half) or pos[1] not in (half - 1, half):
            continue
        if unit[0] == "PICKUP" and len(unit) > 1:
            item = unit[1]
            qty = max(0, int(unit[2]) if len(unit) > 2 else 1)
            stock[item] = max(0, stock.get(item, 0) - qty)
        elif unit[0] == "DROP":
            for item, qty in inv.items():
                stock[item] = stock.get(item, 0) + min(max(0, int(qty)), max(0, cap - sum(stock.values())))
        elif unit[0] == "PLACE" and len(unit) > 1 and unit[1] not in ("COW", "GOOSE", "SHEEP"):
            item = unit[1]
            qty = max(0, int(unit[2]) if len(unit) > 2 else 1)
            stock[item] = stock.get(item, 0) + min(qty, int(inv.get(item, 0)), max(0, cap - sum(stock.values())))
    return stock


def _sale_advance(obs, action, configuration):
    step = int(obs["step"])
    if step < 144:
        return action
    cfg = configuration or {}
    cap = int(cfg.get("maxMarketOrdersPerTurn", 10))
    original = [list(o) for o in action.get("market", [])]
    stock = _sale_stock(obs, action, cfg)
    debt = dict(_SALE_DEBTS.pop(step, {}))
    orders, selling = [], {}
    for order in original[:cap]:
        if len(order) >= 3 and order[0] == "SELL" and order[1] in _SALE_ITEMS:
            item = order[1]
            qty = max(0, int(order[2]))
            paid = min(qty, debt.get(item, 0))
            debt[item] = debt.get(item, 0) - paid
            qty = min(qty - paid, max(0, stock.get(item, 0) - selling.get(item, 0)))
            if qty <= 0:
                continue
            order[2] = qty
            selling[item] = selling.get(item, 0) + qty
        orders.append(order)
    route = _land_route(obs)
    advanced = 0
    if route is not None:
        tape = _DATA["routes"][route]
        for future in range(step + 1, min(step + 4, 718) + 1):
            if future // 72 != step // 72:
                break
            booked = _SALE_DEBTS.setdefault(future, {})
            planned = {}
            for order in tape[future].get("market", []):
                if len(order) >= 3 and order[0] == "SELL" and order[1] in _SALE_ITEMS:
                    planned[order[1]] = planned.get(order[1], 0) + max(0, int(order[2]))
            for item, qty in planned.items():
                qty = min(max(0, qty - booked.get(item, 0)), max(0, stock.get(item, 0) - selling.get(item, 0)))
                if qty <= 0 or float(obs["market"]["prices"].get(item, 0)) <= 1:
                    continue
                hit = next((o for o in orders if len(o) >= 3 and o[:2] == ["SELL", item]), None)
                if hit is None:
                    if len(orders) >= cap:
                        continue
                    orders.append(["SELL", item, qty])
                else:
                    hit[2] += qty
                booked[item] = booked.get(item, 0) + qty
                selling[item] = selling.get(item, 0) + qty
                advanced += qty
    front = [o for o in orders if len(o) >= 3 and o[0] == "SELL" and o[1] in _SALE_ITEMS]
    other = [o for o in orders if not (len(o) >= 3 and o[0] == "SELL" and o[1] in _SALE_ITEMS)]
    revised = front + other
    if advanced:
        _SALE_STATS["sale_advance_turns"] += 1
        _SALE_STATS["sale_advance_units"] += advanced
    if revised != original:
        _SALE_STATS["sale_queue_turns"] += 1
        action["market"] = revised
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _SALE_DEBTS.clear()
        for key in _SALE_STATS:
            _SALE_STATS[key] = 0
    action = _SALE_PARENT(observation, configuration)
    try:
        action = _sale_advance(observation, action, configuration)
    except Exception:
        _SALE_STATS["sale_errors"] += 1
    _SALE_STATS.update(_LAND_STATS)
    return action


agent.telemetry = _SALE_STATS


def kaggle_shunki_sale_advance_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
