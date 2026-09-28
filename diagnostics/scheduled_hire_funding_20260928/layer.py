"""Recover existing scheduled hires without sacrificing an animal's feed."""
_HIRE_FUND_PARENT = agent
_HIRE_FUND_STATS = {'hire_fund_turns': 0, 'hire_fund_hands': 0,
                    'hire_fund_wheat_sacrificed': 0, 'hire_fund_errors': 0}


def _hire_fund_apply(obs, action, configuration):
    cfg = configuration or {}
    if int(obs['step']) % int(cfg.get('turnsPerDay', 24)):
        return action
    orders = action.get('market', [])
    wheat = next((i for i, order in enumerate(orders) if order[:2] == ['BUY_PRODUCT', 'WHEAT']), None)
    hires = [order for order in orders if order == ['HIRE']]
    if wheat is None or not hires or not any(order == ['HIRE'] for order in orders[wheat+1:]):
        return action
    if len(orders) > int(cfg.get('maxMarketOrdersPerTurn', 10)):
        return action
    remainder = [order for order in orders if order != ['HIRE']]
    insert = next(i for i, order in enumerate(remainder) if order[:2] == ['BUY_PRODUCT', 'WHEAT'])
    proposal = remainder[:insert] + hires + remainder[insert:]
    own = obs['farms'][int(obs['player'])]
    desired = len(own['hands']) + len(hires)
    feed = sum(isinstance(tile, dict) and bool(tile.get('animal')) and not tile.get('fed_today', False)
               for row in own['tiles'] for tile in row)
    stock = _queue_stock(obs, action, cfg)
    raw = _ITERATED_QUEUE_RAW(obs, configuration).get('market', [])
    forecasts = [[], orders] + ([raw] if raw != orders else [])
    gains = []; sacrifice = []
    for rival in forecasts:
        old = _queue_simulate(obs, orders, rival, stock, cfg)
        new = _queue_simulate(obs, proposal, rival, stock, cfg)
        old_sig, new_sig = old[2], new[2]
        old_stock, new_stock = dict(old_sig[0]), dict(new_sig[0])
        before_wheat, after_wheat = old_stock.pop('WHEAT', 0), new_stock.pop('WHEAT', 0)
        if len(new_sig[2]) != desired or len(new_sig[2]) <= len(old_sig[2]):
            return action
        if old_sig[1] != new_sig[1] or old_sig[3] != new_sig[3] or old_stock != new_stock:
            return action
        if not 0 <= before_wheat - after_wheat <= 1 or after_wheat < feed:
            return action
        gains.append(len(new_sig[2]) - len(old_sig[2])); sacrifice.append(before_wheat - after_wheat)
    action['market'] = proposal
    _HIRE_FUND_STATS['hire_fund_turns'] += 1
    _HIRE_FUND_STATS['hire_fund_hands'] += min(gains)
    _HIRE_FUND_STATS['hire_fund_wheat_sacrificed'] += max(sacrifice)
    return action


def agent(observation, configuration=None):
    if int(observation['step']) == 0:
        for key in _HIRE_FUND_STATS:
            _HIRE_FUND_STATS[key] = 0
    result = _HIRE_FUND_PARENT(observation, configuration)
    try:
        result = _hire_fund_apply(observation, result, configuration)
    except Exception:
        _HIRE_FUND_STATS['hire_fund_errors'] += 1
    agent.telemetry.update(getattr(_HIRE_FUND_PARENT, 'telemetry', {}))
    agent.telemetry.update(_HIRE_FUND_STATS)
    return result


agent.telemetry = {}


def kaggle_scheduled_hire_funding_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
