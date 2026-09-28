"""Commit a complete compatible schedule after the first public BRUNCH shop."""
_EARLY_BRUNCH_ROUTE = ROUTE_VALUE
for _early_brunch_key in list(_DATA['route_map']):
    if _early_brunch_key == 'BRUNCH_SPOT' or _early_brunch_key.startswith('BRUNCH_SPOT|'):
        _DATA['route_map'][_early_brunch_key] = _EARLY_BRUNCH_ROUTE

_EARLY_BRUNCH_PARENT = agent
_EARLY_BRUNCH_STATS = {'early_brunch_turns': 0, 'early_brunch_route': '', 'early_brunch_shop72': ''}


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _EARLY_BRUNCH_STATS.update(early_brunch_turns=0, early_brunch_route='', early_brunch_shop72='')
    result = _EARLY_BRUNCH_PARENT(observation, configuration)
    shops = observation['town']['unlocked_shops']
    if step == 72:
        _EARLY_BRUNCH_STATS['early_brunch_shop72'] = shops[0] if shops else ''
    if step >= 72 and shops and shops[0] == 'BRUNCH_SPOT':
        _EARLY_BRUNCH_STATS['early_brunch_turns'] += 1
        _EARLY_BRUNCH_STATS['early_brunch_route'] = str(_EARLY_BRUNCH_ROUTE)
    agent.telemetry.update(_EARLY_BRUNCH_STATS)
    return result


agent.telemetry = {}


def kaggle_early_brunch_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
