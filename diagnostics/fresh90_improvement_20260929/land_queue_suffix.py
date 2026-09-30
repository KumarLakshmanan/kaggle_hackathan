
# Fulfil an already-scheduled land purchase after its same-turn liquidation.
_FUNDED_LAND_PARENT = agent
_FUNDED_LAND_STATS = {'funded_land_turns': 0, 'funded_land_proposals': 0,
                      'funded_land_errors': 0}


def _funded_land_apply(obs, action, cfg):
    orders = action.get('market', [])
    if not 2 <= len(orders) <= int(cfg.get('maxMarketOrdersPerTurn', 10)):
        return action
    indices = [i for i, order in enumerate(orders) if order and order[0] == 'BUY_LAND']
    if len(indices) != 1 or indices[0] == len(orders) - 1:
        return action
    farm = obs['farms'][int(obs['player'])]
    quadrants = tuple(farm['unlocked_quadrants'])
    extra = len(quadrants) - 1
    if not 0 <= extra < 3:
        return action
    cost = _QUEUE_ENGINE['LAND_PRICES'][extra]
    desired = quadrants + (_QUEUE_ENGINE['LAND_ORDER'][extra],)
    stock = _queue_stock(obs, action, cfg)
    index = indices[0]
    proposed = orders[:index] + orders[index + 1:] + [orders[index]]
    _FUNDED_LAND_STATS['funded_land_proposals'] += 1
    for rival in ([], orders):
        before = _queue_simulate(obs, orders, rival, stock, cfg)
        after = _queue_simulate(obs, proposed, rival, stock, cfg)
        oldsig, newsig = before[2], after[2]
        if oldsig[3] != quadrants or newsig[3] != desired:
            return action
        if oldsig[:3] != newsig[:3] or oldsig[4:] != newsig[4:]:
            return action
        if after[3] != before[3] or after[1] > before[1] or after[0] < before[0] - cost:
            return action
    action['market'] = proposed
    _FUNDED_LAND_STATS['funded_land_turns'] += 1
    return action


def agent(observation, configuration=None):
    if int(observation['step']) == 0:
        for key in _FUNDED_LAND_STATS:
            _FUNDED_LAND_STATS[key] = 0
    result = _FUNDED_LAND_PARENT(observation, configuration)
    try:
        result = _funded_land_apply(observation, result, configuration or {})
    except Exception:
        _FUNDED_LAND_STATS['funded_land_errors'] += 1
    agent.telemetry.update(_FUNDED_LAND_STATS)
    return result


agent.telemetry = {}


def kaggle_funded_land_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
