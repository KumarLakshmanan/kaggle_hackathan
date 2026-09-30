"""Commit a compatible complete schedule while retaining the planting repair."""
_AC_ROUTE_REPLACEMENTS = REPLACEMENTS_VALUE
for _ac_key in list(_DATA['route_map']):
    for _ac_pair, _ac_route in _AC_ROUTE_REPLACEMENTS.items():
        if _ac_key == _ac_pair or _ac_key.startswith(_ac_pair + '|'):
            _DATA['route_map'][_ac_key] = _ac_route

_AC_ROUTE_PARENT = agent
_AC_ROUTE_STATS = {'guard_route_turns': 0, 'guard_route_selected': '', 'guard_route_pair144': ''}


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _AC_ROUTE_STATS.update(guard_route_turns=0, guard_route_selected='', guard_route_pair144='')
    result = _AC_ROUTE_PARENT(observation, configuration)
    pair = '|'.join(observation['town']['unlocked_shops'][:2])
    if step == 144:
        _AC_ROUTE_STATS['guard_route_pair144'] = pair
    if step >= 144 and pair in _AC_ROUTE_REPLACEMENTS:
        _AC_ROUTE_STATS['guard_route_turns'] += 1
        _AC_ROUTE_STATS['guard_route_selected'] = str(_AC_ROUTE_REPLACEMENTS[pair])
    agent.telemetry.update(_AC_ROUTE_STATS)
    return result


agent.telemetry = {}


def kaggle_guarded_route_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
