"""A compatible continuation selected after the second shop is visible."""
_PRODUCTION_PAIR_PARENT = agent
_PRODUCTION_PAIR_LEAF = LEAF_VALUE
_PRODUCTION_PAIR_DEFAULT = DEFAULT_VALUE
_PRODUCTION_PAIR_RULES = RULES_VALUE
_PRODUCTION_PAIR_STATS = {'production_pair144': '', 'production_pair_route': '',
                          'production_pair_turns': 0}


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _PRODUCTION_PAIR_STATS.update(production_pair144='', production_pair_route='',
                                       production_pair_turns=0)
    if step == 144 and _PRODUCTION_LEAF_STATS['production_leaf_key72'] == _PRODUCTION_PAIR_LEAF:
        pair = '|'.join(observation['town']['unlocked_shops'][:2])
        route = str(_PRODUCTION_PAIR_RULES.get(pair, _PRODUCTION_PAIR_DEFAULT))
        _production_leaf_commit(_PRODUCTION_PAIR_LEAF, route)
        _PRODUCTION_LEAF_STATS['production_leaf_route'] = route
        _PRODUCTION_PAIR_STATS.update(production_pair144=pair, production_pair_route=route)
    result = _PRODUCTION_PAIR_PARENT(observation, configuration)
    if step >= 144 and _PRODUCTION_PAIR_STATS['production_pair_route']:
        _PRODUCTION_PAIR_STATS['production_pair_turns'] += 1
    agent.telemetry.update(getattr(_PRODUCTION_PAIR_PARENT, 'telemetry', {}))
    agent.telemetry.update(_PRODUCTION_PAIR_STATS)
    return result


agent.telemetry = {}


def kaggle_production_pair_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
