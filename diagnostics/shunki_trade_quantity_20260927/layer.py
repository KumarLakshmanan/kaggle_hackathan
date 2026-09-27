"""Vary balanced product quantities with explicit current-turn forecasts."""
_QUANTITY_PARENT = agent
_QUANTITY_STATS = {"quantity_turns": 0, "quantity_proposals": 0,
                   "quantity_errors": 0, "quantity_predicted_gain": 0.0}


def _quantity_apply(obs, action, configuration):
    cfg = configuration or {}
    orders = action.get("market", [])
    proposals = []
    for item in ("WHEAT", "FERTILIZER"):
        buys = [i for i, o in enumerate(orders) if o[:2] == ["BUY_PRODUCT", item]]
        sells = [i for i, o in enumerate(orders) if o[:2] == ["SELL", item]]
        if not buys or not sells:
            continue
        bi, si = buys[0], sells[0]
        for delta in (4, 12, 24, -4, -12, -24):
            if min(orders[bi][2], orders[si][2])+delta <= 0:
                continue
            if max(orders[bi][2], orders[si][2])+delta > 100:
                continue
            proposed = [list(o) for o in orders]
            proposed[bi][2] += delta
            proposed[si][2] += delta
            proposals.append(proposed)
    if not proposals:
        return action
    stock = _queue_stock(obs, action, cfg)
    original = _QUEUE_PARENT(obs, configuration).get("market", [])
    forecasts = [[], orders]
    if original != orders:
        forecasts.append(original)
    controls = [_queue_simulate(obs, orders, rival, stock, cfg) for rival in forecasts]
    best_key, best_orders = (0, 0), orders
    for proposed in proposals:
        _QUANTITY_STATS["quantity_proposals"] += 1
        outcomes = []
        for rival, control in zip(forecasts, controls):
            result = _queue_simulate(obs, proposed, rival, stock, cfg)
            if result[2:] != control[2:] or result[0] < control[0]:
                break
            outcomes.append(result)
        if len(outcomes) != len(controls):
            continue
        gains = [(result[0]-result[1])-(control[0]-control[1])
                 for result, control in zip(outcomes[1:], controls[1:])]
        key = (min(gains), sum(gains))
        if key[0] >= 0 and key > best_key:
            best_key, best_orders = key, proposed
    if best_orders is not orders:
        action["market"] = best_orders
        _QUANTITY_STATS["quantity_turns"] += 1
        _QUANTITY_STATS["quantity_predicted_gain"] += best_key[0]
    return action


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        for key in _QUANTITY_STATS:
            _QUANTITY_STATS[key] = 0
    action = _QUANTITY_PARENT(observation, configuration)
    try:
        result = _quantity_apply(observation, action, configuration)
    except Exception:
        _QUANTITY_STATS["quantity_errors"] += 1
        result = action
    agent.telemetry.update(_QUEUE_STATS)
    agent.telemetry.update(_QUANTITY_STATS)
    return result


agent.telemetry = {}


def kaggle_trade_quantity_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
