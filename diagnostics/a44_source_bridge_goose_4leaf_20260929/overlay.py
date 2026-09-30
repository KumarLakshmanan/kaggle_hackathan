"""Four public production leaves, restricted to the exact a44 source bridge."""

_A44_GOOSE4_RULES = {
    'FARMERS_MARKET|M<8|C>S|G0': 113535489,
    'ICE_CREAM_SHOP|M8+|C<S|G0': 113535489,
    'ICE_CREAM_SHOP|M8+|C>S|G0': 113470868,
    'PIZZA_SHOP|M8+|C<S|G0': 113470868,
}
_A44_GOOSE4_BASE_ROUTE_MAP = copy.deepcopy(_DATA['route_map'])
_A44_GOOSE4_BASE_FARMICE = copy.deepcopy(_FARMICE_TAPE)
_A44_GOOSE4_PARENT = agent
_A44_GOOSE4_STATS = {
    'a44_goose4_branch72': '',
    'a44_goose4_key72': '',
    'a44_goose4_route': '',
    'a44_goose4_turns': 0,
    'a44_goose4_errors': 0,
}


def _a44_goose4_key(observation):
    shops = observation['town']['unlocked_shops']
    rival = observation['farms'][1-int(observation['player'])]
    melon = cow = sheep = goose = 0
    for row in rival['tiles']:
        for tile in row:
            if isinstance(tile, dict):
                melon += tile.get('crop') == 'MELON'
                cow += tile.get('animal') == 'COW'
                sheep += tile.get('animal') == 'SHEEP'
                goose += tile.get('animal') == 'GOOSE'
    comparison = 'C<S' if cow < sheep else 'C>S' if cow > sheep else 'C=S'
    return shops[0] + '|' + ('M8+' if melon >= 8 else 'M<8') + '|' + comparison + ('|G+' if goose > 0 else '|G0')


def _a44_goose4_active(step, bridge_branch):
    return int(step) == 72 and bridge_branch == 'source'


def _a44_goose4_reset():
    global _FARMICE_TAPE
    _DATA['route_map'].clear()
    _DATA['route_map'].update(copy.deepcopy(_A44_GOOSE4_BASE_ROUTE_MAP))
    _FARMICE_TAPE = copy.deepcopy(_A44_GOOSE4_BASE_FARMICE)
    _A44_GOOSE4_STATS.update(a44_goose4_branch72='', a44_goose4_key72='',
                             a44_goose4_route='', a44_goose4_turns=0,
                             a44_goose4_errors=0)


def _a44_goose4_commit(leaf, route):
    global _FARMICE_TAPE
    shop = leaf.split('|', 1)[0]
    route = int(route)
    for key in list(_DATA['route_map']):
        if key.split('|', 1)[0] == shop:
            _DATA['route_map'][key] = route
    _DATA['route_map'][shop] = route
    if shop == 'FARMERS_MARKET':
        _FARMICE_TAPE = _DATA['routes'][str(route)]


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _a44_goose4_reset()
    if _a44_goose4_active(step, _BRIDGE_SELECTED):
        branch = _BRIDGE_SELECTED
        _A44_GOOSE4_STATS['a44_goose4_branch72'] = branch
        leaf = _a44_goose4_key(observation)
        _A44_GOOSE4_STATS['a44_goose4_key72'] = leaf
        route = _A44_GOOSE4_RULES.get(leaf)
        if route is not None:
            try:
                _a44_goose4_commit(leaf, route)
                _A44_GOOSE4_STATS['a44_goose4_route'] = str(route)
            except Exception:
                _A44_GOOSE4_STATS['a44_goose4_errors'] += 1
    if step >= 72 and _A44_GOOSE4_STATS['a44_goose4_route']:
        _A44_GOOSE4_STATS['a44_goose4_turns'] += 1
    result = _A44_GOOSE4_PARENT(observation, configuration)
    agent.telemetry.update(getattr(_A44_GOOSE4_PARENT, 'telemetry', {}))
    agent.telemetry.update(_A44_GOOSE4_STATS)
    return result


agent.telemetry = {}


def kaggle_a44_source_bridge_goose4_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
