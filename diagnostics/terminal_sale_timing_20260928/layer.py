"""Sell uncommitted existing product stock near the end of the episode."""
_TERMINAL_SALE_HORIZON = HORIZON_VALUE
_TERMINAL_SALE_PARENT = agent
_TERMINAL_SALE_PRODUCTS = ('MILK', 'WOOL', 'EGG', 'STRAWBERRY', 'CARROT', 'TOMATO', 'MELON')
_TERMINAL_SALE_STATS = {'terminal_sale_turns': 0, 'terminal_sale_units': 0,
                        'terminal_sale_errors': 0}


def _terminal_sale_apply(obs, action, cfg):
    step = int(obs['step'])
    last = int(cfg.get('episodeSteps', 720)) - 2
    if step < last - _TERMINAL_SALE_HORIZON:
        return action
    orders = action.get('market', [])
    room = int(cfg.get('maxMarketOrdersPerTurn', 10)) - len(orders)
    if room <= 0:
        return action
    schedule = _hire_recovery_schedule(obs)
    reserved = set()
    for future in schedule[step + 1:last + 1]:
        for unit in [future.get('farmer', []), *future.get('hands', [])]:
            if len(unit) > 1 and unit[0] == 'PICKUP':
                reserved.add(unit[1])
    stock = _queue_stock(obs, action, cfg)
    current = {}
    for order in orders:
        if len(order) >= 3 and order[0] == 'SELL':
            current[order[1]] = current.get(order[1], 0) + max(0, int(order[2]))
    extras = []
    for item in _TERMINAL_SALE_PRODUCTS:
        if item in reserved:
            continue
        qty = min(int(obs['private']['shed'].get(item, 0)),
                  int(stock.get(item, 0)) - current.get(item, 0))
        if qty > 0:
            extras.append(['SELL', item, qty])
            if len(extras) == room:
                break
    if extras:
        action['market'] = orders + extras
        _TERMINAL_SALE_STATS['terminal_sale_turns'] += 1
        _TERMINAL_SALE_STATS['terminal_sale_units'] += sum(o[2] for o in extras)
    return action


def agent(observation, configuration=None):
    if int(observation['step']) == 0:
        for key in _TERMINAL_SALE_STATS:
            _TERMINAL_SALE_STATS[key] = 0
    result = _TERMINAL_SALE_PARENT(observation, configuration)
    try:
        result = _terminal_sale_apply(observation, result, configuration or {})
    except Exception:
        _TERMINAL_SALE_STATS['terminal_sale_errors'] += 1
    agent.telemetry.update(getattr(_TERMINAL_SALE_PARENT, 'telemetry', {}))
    agent.telemetry.update(_TERMINAL_SALE_STATS)
    return result


agent.telemetry = {}


def kaggle_terminal_sale_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
