"""Commit to complete schedules at the first observed shop."""
_EARLY_PUBLIC_REPLACEMENTS = REPLACEMENTS_VALUE
for _early_public_key in list(_DATA['route_map']):
    _early_public_shop = _early_public_key.split('|')[0]
    if _early_public_shop in _EARLY_PUBLIC_REPLACEMENTS:
        _DATA['route_map'][_early_public_key] = _EARLY_PUBLIC_REPLACEMENTS[_early_public_shop]
for _early_public_shop, _early_public_route in _EARLY_PUBLIC_REPLACEMENTS.items():
    _DATA['route_map'][_early_public_shop] = _early_public_route
if 'FARMERS_MARKET' in _EARLY_PUBLIC_REPLACEMENTS:
    _FARMICE_TAPE = _DATA['routes'][str(_EARLY_PUBLIC_REPLACEMENTS['FARMERS_MARKET'])]

_EARLY_PUBLIC_PARENT = agent
_EARLY_PUBLIC_STATS = {'early_public_shop72': '', 'early_public_turns': 0,
                       'early_public_route': ''}


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _EARLY_PUBLIC_STATS.update(early_public_shop72='', early_public_turns=0,
                                   early_public_route='')
    result = _EARLY_PUBLIC_PARENT(observation, configuration)
    shops = observation['town']['unlocked_shops']
    if step == 72:
        _EARLY_PUBLIC_STATS['early_public_shop72'] = shops[0]
    if step >= 72 and shops and shops[0] in _EARLY_PUBLIC_REPLACEMENTS:
        _EARLY_PUBLIC_STATS['early_public_turns'] += 1
        _EARLY_PUBLIC_STATS['early_public_route'] = str(_EARLY_PUBLIC_REPLACEMENTS[shops[0]])
    agent.telemetry.update(getattr(_EARLY_PUBLIC_PARENT, 'telemetry', {}))
    agent.telemetry.update(_EARLY_PUBLIC_STATS)
    return result


agent.telemetry = {}


def kaggle_early_public_commitment_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
