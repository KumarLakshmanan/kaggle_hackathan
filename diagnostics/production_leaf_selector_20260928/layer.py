"""One predecision production leaf chooses a complete compatible schedule."""
_PRODUCTION_LEAF_ARM = ARM_VALUE
_PRODUCTION_LEAF_RULES = RULES_VALUE
_PRODUCTION_LEAF_BASE_MAP = dict(_DATA['route_map'])
_PRODUCTION_LEAF_BASE_FARMICE = _FARMICE_TAPE
_PRODUCTION_LEAF_PARENT = agent
_PRODUCTION_LEAF_STATS = {'production_leaf_key72': '', 'production_leaf_route': '',
                          'production_leaf_turns': 0, 'production_leaf_errors': 0}


def _production_leaf_key(observation):
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
    leaf = shops[0] + '|' + ('M8+' if melon >= 8 else 'M<8') + '|' + comparison
    if _PRODUCTION_LEAF_ARM == 'production_goose':
        leaf += '|G+' if goose > 0 else '|G0'
    return leaf


def _production_leaf_reset():
    global _FARMICE_TAPE
    _DATA['route_map'].clear()
    _DATA['route_map'].update(_PRODUCTION_LEAF_BASE_MAP)
    _FARMICE_TAPE = _PRODUCTION_LEAF_BASE_FARMICE
    _PRODUCTION_LEAF_STATS.update(production_leaf_key72='', production_leaf_route='',
                                   production_leaf_turns=0, production_leaf_errors=0)


def _production_leaf_commit(leaf, route):
    global _FARMICE_TAPE
    shop = leaf.split('|')[0]
    for key in list(_DATA['route_map']):
        if key.split('|')[0] == shop:
            _DATA['route_map'][key] = int(route)
    _DATA['route_map'][shop] = int(route)
    if shop == 'FARMERS_MARKET':
        _FARMICE_TAPE = _DATA['routes'][str(route)]


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _production_leaf_reset()
    if step == 72:
        leaf = _production_leaf_key(observation)
        _PRODUCTION_LEAF_STATS['production_leaf_key72'] = leaf
        route = _PRODUCTION_LEAF_RULES.get(leaf)
        if route is not None:
            _production_leaf_commit(leaf, route)
            _PRODUCTION_LEAF_STATS['production_leaf_route'] = str(route)
    result = _PRODUCTION_LEAF_PARENT(observation, configuration)
    if step >= 72 and _PRODUCTION_LEAF_STATS['production_leaf_route']:
        _PRODUCTION_LEAF_STATS['production_leaf_turns'] += 1
    agent.telemetry.update(getattr(_PRODUCTION_LEAF_PARENT, 'telemetry', {}))
    agent.telemetry.update(_PRODUCTION_LEAF_STATS)
    return result


agent.telemetry = {}


def kaggle_production_leaf_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
