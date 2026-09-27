"""Retry a recorded capital purchase after a temporary cash shortage."""
_LAND_PARENT = agent
_LAND_STATS = {"land_retries": 0, "land_errors": 0}
_LAND_INTENT = {}
_LAND_SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50,
                   "STRAWBERRY": 100, "MELON": 80}


def _land_route(obs):
    shops = obs["town"]["unlocked_shops"]
    step = int(obs["step"])
    route = None
    for count in range(1, min(len(shops), 8) + 1):
        if step >= 72 * count:
            route = _DATA["route_map"].get("|".join(shops[:count]), route)
    return str(route) if route is not None else None


def _land_fib(n):
    a, b = 0, 1
    for _ in range(max(0, int(n))):
        a, b = b, a + b
    return a


def _land_repair(obs, action, configuration):
    step = int(obs["step"])
    if step < 73 or step >= 600:
        return action
    cfg = configuration or {}
    orders = action.get("market", [])
    if len(orders) >= int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    if any(o and o[0] == "BUY_LAND" for o in orders):
        return action
    farm = obs["farms"][int(obs["player"])]
    owned = len(farm["unlocked_quadrants"])
    if owned >= 4:
        return action
    route = _land_route(obs)
    if route is None:
        return action
    if route not in _LAND_INTENT:
        totals, count = [], 1
        for turn in _DATA["routes"][route]:
            totals.append(count)
            count = min(4, count + sum(bool(o) and o[0] == "BUY_LAND"
                                       for o in turn.get("market", [])))
        _LAND_INTENT[route] = totals
    if _LAND_INTENT[route][step] <= owned:
        return action
    prices = obs["market"]["prices"]
    committed = 0.0
    hires = int(farm.get("hires_today", len(farm["hands"])))
    for order in orders:
        if not order:
            continue
        op = order[0]
        if op == "HIRE":
            committed += _land_fib(hires) * float(cfg.get("farmHandCostMultiplier", 1))
            hires += 1
        elif len(order) >= 3 and op == "BUY_SEED":
            committed += max(0, int(order[2])) * _LAND_SEED_COST.get(order[1], 100)
        elif len(order) >= 3 and op == "BUY_PRODUCT":
            committed += max(0, int(order[2])) * max(1, float(prices.get(order[1], 100))) * 1.5
        elif op == "BUY_ANIMAL":
            return action
    cost = (1000, 2000, 4000)[owned - 1]
    if float(farm["money"]) < cost + committed + 500:
        return action
    action["market"] = list(orders) + [["BUY_LAND"]]
    _LAND_STATS["land_retries"] += 1
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _LAND_STATS.update(land_retries=0, land_errors=0)
    action = _LAND_PARENT(observation, configuration)
    try:
        return _land_repair(observation, action, configuration)
    except Exception:
        _LAND_STATS["land_errors"] += 1
        return action


agent.telemetry = _LAND_STATS


def kaggle_shunki_land_retry_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
