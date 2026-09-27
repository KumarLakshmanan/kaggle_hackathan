"""Experimental one-turn procurement for recorded wheat pickups."""

_SUPPLY_PARENT = agent
_SUPPLY_STATS = {"supply_turns": 0, "supply_wheat": 0, "supply_errors": 0}
_SUPPLY_SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}


def _supply_tape(obs):
    shops = obs["town"]["unlocked_shops"]
    step = int(obs["step"])
    route = None
    for count in range(1, min(len(shops), 8) + 1):
        if step >= 72 * count:
            route = _DATA["route_map"].get("|".join(shops[:count]), route)
    return _DATA["routes"][str(route)] if route is not None else None


def _supply_fib(n):
    a, b = 0, 1
    for _ in range(max(0, int(n))):
        a, b = b, a + b
    return a


def _supply_add_wheat(obs, action, configuration):
    step = int(obs["step"])
    if step < 240 or step >= 718 or (step + 1) % 24 == 0:
        return action
    cfg = configuration or {}
    orders = action.get("market", [])
    if len(orders) >= int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    farm = obs["farms"][int(obs["player"])]
    money = float(farm["money"])
    if money < 2000 or any(order and order[0] in ("BUY_LAND", "BUY_ANIMAL") for order in orders):
        return action
    tape = _supply_tape(obs)
    if tape is None:
        return action
    nxt = tape[step + 1]
    requests = [nxt.get("farmer", [])] + nxt.get("hands", [])
    need = sum(max(0, int(unit[2]) if len(unit) > 2 else 1)
               for unit in requests if len(unit) > 1 and unit[:2] == ["PICKUP", "WHEAT"])
    if need <= 0:
        return action
    private = obs["private"]
    stock = dict(private["shed"])
    cap = int(cfg.get("shedCapacity", 100))
    center = int(cfg.get("boardSize", 10)) // 2
    positions = [farm["farmer"]] + farm["hands"]
    units = [action.get("farmer", [])] + action.get("hands", [])
    for pos, unit, inv in zip(positions, units, private["inventories"]):
        if abs(int(pos[0]) - center) + abs(int(pos[1]) - center) != 1 or not unit:
            continue
        if unit[0] == "PICKUP" and len(unit) >= 2:
            item = unit[1]
            qty = max(0, int(unit[2]) if len(unit) > 2 else 1)
            stock[item] = max(0, stock.get(item, 0) - qty)
        elif unit[0] == "DROP":
            for item, qty in inv.items():
                take = min(int(qty), max(0, cap - sum(stock.values())))
                stock[item] = stock.get(item, 0) + take
        elif unit[0] == "PLACE" and len(unit) >= 2 and unit[1] not in ("COW", "SHEEP", "GOOSE"):
            item = unit[1]
            take = min(int(inv.get(item, 0)), int(unit[2]) if len(unit) > 2 else 1,
                       max(0, cap - sum(stock.values())))
            stock[item] = stock.get(item, 0) + max(0, take)
    prices = obs["market"]["prices"]
    committed = 0.0
    hired = len(farm["hands"])
    for order in orders:
        if not order:
            continue
        op = order[0]
        if op == "HIRE":
            hired += 1
            committed += _supply_fib(hired)
        elif len(order) >= 3 and op == "BUY_SEED":
            committed += max(0, int(order[2])) * _SUPPLY_SEED_COST.get(order[1], 100)
        elif len(order) >= 3 and op == "BUY_PRODUCT":
            item, qty = order[1], max(0, int(order[2]))
            committed += qty * max(1, float(prices.get(item, 100))) * 1.5
            stock[item] = stock.get(item, 0) + min(qty, max(0, cap - sum(stock.values())))
        elif len(order) >= 3 and op == "SELL":
            stock[order[1]] = max(0, stock.get(order[1], 0) - max(0, int(order[2])))
    missing = max(0, need - stock.get("WHEAT", 0))
    price = max(1.0, float(prices.get("WHEAT", 25)))
    funded = max(0, int((money - committed - 500) / (1.5 * price)))
    buy = min(missing, max(0, cap - sum(stock.values())), funded)
    if buy <= 0:
        return action
    action["market"] = list(orders) + [["BUY_PRODUCT", "WHEAT", buy]]
    _SUPPLY_STATS["supply_turns"] += 1
    _SUPPLY_STATS["supply_wheat"] += buy
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _SUPPLY_STATS.update(supply_turns=0, supply_wheat=0, supply_errors=0)
    action = _SUPPLY_PARENT(observation, configuration)
    try:
        return _supply_add_wheat(observation, action, configuration)
    except Exception:
        _SUPPLY_STATS["supply_errors"] += 1
        return action


agent.telemetry = _SUPPLY_STATS


def kaggle_shunki_feed_supply_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
