"""Commit compatible complete schedules for prospectively selected branches."""
_LOSS_POOL_REPLACEMENTS = REPLACEMENTS_VALUE
for _loss_pool_key in list(_DATA['route_map']):
    for _loss_pool_pair, _loss_pool_route in _LOSS_POOL_REPLACEMENTS.items():
        if _loss_pool_key == _loss_pool_pair or _loss_pool_key.startswith(_loss_pool_pair + '|'):
            _DATA['route_map'][_loss_pool_key] = _loss_pool_route
for _loss_pool_pair, _loss_pool_route in _LOSS_POOL_REPLACEMENTS.items():
    _DATA['route_map'][_loss_pool_pair] = _loss_pool_route

_LOSS_POOL_PARENT = agent
_LOSS_POOL_STATS = {'loss_pool_turns': 0, 'loss_pool_route': '', 'loss_pool_pair144': ''}


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _LOSS_POOL_STATS.update(loss_pool_turns=0, loss_pool_route='', loss_pool_pair144='')
    result = _LOSS_POOL_PARENT(observation, configuration)
    pair = '|'.join(observation['town']['unlocked_shops'][:2])
    if step == 144:
        _LOSS_POOL_STATS['loss_pool_pair144'] = pair
    if step >= 144 and pair in _LOSS_POOL_REPLACEMENTS:
        _LOSS_POOL_STATS['loss_pool_turns'] += 1
        _LOSS_POOL_STATS['loss_pool_route'] = str(_LOSS_POOL_REPLACEMENTS[pair])
    agent.telemetry.update(_LOSS_POOL_STATS)
    return result


agent.telemetry = {}


def kaggle_public_loss_pool_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
