"""Exact-a44 source-only Smoothie continuation, composed after frozen Goose4."""
_A44_SMOOTHIE_KEY72 = 'SMOOTHIE_SHOP|M8+|C>S|G0'
_A44_SMOOTHIE_ROUTE72 = 113470868
_A44_SMOOTHIE_PAIR_ROUTES = {
    'SMOOTHIE_SHOP|BAKERY': 113639519,
    'SMOOTHIE_SHOP|BRUNCH_SPOT': 113340658,
    'SMOOTHIE_SHOP|FARMERS_MARKET': 113639519,
    'SMOOTHIE_SHOP|ICE_CREAM_SHOP': 113340658,
    'SMOOTHIE_SHOP|PIZZA_SHOP': 113618016,
    'SMOOTHIE_SHOP|SMOOTHIE_SHOP': 113639519,
}
_A44_SMOOTHIE_DEFAULT_ROUTE = 113470868
_A44_SMOOTHIE_BASE_ROUTE_MAP = copy.deepcopy(_A44_GOOSE4_BASE_ROUTE_MAP)
_A44_SMOOTHIE_BASE_FARMICE = copy.deepcopy(_A44_GOOSE4_BASE_FARMICE)
_A44_SMOOTHIE_PARENT = agent
_A44_SMOOTHIE_ACTIVE = False
_A44_SMOOTHIE_STATS = {
    'a44_smoothie_branch72': '',
    'a44_smoothie_key72': '',
    'a44_smoothie_active72': False,
    'a44_smoothie_route72': '',
    'a44_smoothie_pair144': '',
    'a44_smoothie_route144': '',
    'a44_smoothie_turns': 0,
    'a44_smoothie_errors': 0,
}


def _a44_smoothie_rule_key(observation):
    # _a44_goose4_key reads only the unlocked shop and rival public tiles.
    return _a44_goose4_key(observation)


def _a44_smoothie_rule_active(step, bridge_branch, key):
    return (int(step) == 72 and bridge_branch == 'source'
            and key == _A44_SMOOTHIE_KEY72)


def _a44_smoothie_pair_active(step, bridge_branch, active):
    return int(step) == 144 and bridge_branch == 'source' and bool(active)


def _a44_smoothie_reset_state():
    global _A44_SMOOTHIE_ACTIVE
    _A44_SMOOTHIE_ACTIVE = False
    _A44_SMOOTHIE_STATS.update(a44_smoothie_branch72='', a44_smoothie_key72='',
        a44_smoothie_active72=False, a44_smoothie_route72='',
        a44_smoothie_pair144='', a44_smoothie_route144='',
        a44_smoothie_turns=0, a44_smoothie_errors=0)


def _a44_smoothie_commit(route):
    # The existing source map helper changes this first shop and all its descendants;
    # it does not enter either donor namespace or alter FARMICE for this shop.
    _a44_goose4_commit(_A44_SMOOTHIE_KEY72, int(route))


def agent(observation, configuration=None):
    global _A44_SMOOTHIE_ACTIVE
    step = int(observation['step'])
    branch = _BRIDGE_SELECTED
    if step == 0:
        _a44_smoothie_reset_state()
    if step == 72:
        _A44_SMOOTHIE_STATS['a44_smoothie_branch72'] = branch
        key = _a44_smoothie_rule_key(observation) if branch == 'source' else ''
        _A44_SMOOTHIE_STATS['a44_smoothie_key72'] = key
        if _a44_smoothie_rule_active(step, branch, key):
            try:
                _a44_smoothie_commit(_A44_SMOOTHIE_ROUTE72)
                _A44_SMOOTHIE_ACTIVE = True
                _A44_SMOOTHIE_STATS.update(a44_smoothie_active72=True,
                    a44_smoothie_route72=str(_A44_SMOOTHIE_ROUTE72))
            except Exception:
                _A44_SMOOTHIE_STATS['a44_smoothie_errors'] += 1
    if _a44_smoothie_pair_active(step, branch, _A44_SMOOTHIE_ACTIVE):
        try:
            pair = '|'.join(observation['town']['unlocked_shops'][:2])
            route = _A44_SMOOTHIE_PAIR_ROUTES.get(pair, _A44_SMOOTHIE_DEFAULT_ROUTE)
            _a44_smoothie_commit(route)
            _A44_SMOOTHIE_STATS.update(a44_smoothie_pair144=pair,
                                       a44_smoothie_route144=str(route))
        except Exception:
            _A44_SMOOTHIE_STATS['a44_smoothie_errors'] += 1
    result = _A44_SMOOTHIE_PARENT(observation, configuration)
    if step >= 144 and _A44_SMOOTHIE_ACTIVE:
        _A44_SMOOTHIE_STATS['a44_smoothie_turns'] += 1
    agent.telemetry.update(getattr(_A44_SMOOTHIE_PARENT, 'telemetry', {}))
    agent.telemetry.update(_A44_SMOOTHIE_STATS)
    return result


agent.telemetry = {}


def kaggle_a44_goose4_smoothie_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
