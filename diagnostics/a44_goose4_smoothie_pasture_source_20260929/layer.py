"""Public pasture guard and source-only Brunch goose route for exact 6d."""

_A44_PASTURE_BRUNCH_PARENT = agent
_A44_PASTURE_BRUNCH_KEY = 'BRUNCH_SPOT|M8+|C>S|G+'
_A44_PASTURE_BRUNCH_ROUTE = 113332529
_A44_PASTURE_BRUNCH_STATS = {
    'pasture_guard_rival_hands_step1': -1,
    'pasture_guard_rival_pastures_step1': -1,
    'pasture_guard_requested_step1': '',
    'pasture_guard_selected_step1': '',
    'pasture_guard_reset_route_map_matches': False,
    'pasture_brunch_branch72': '',
    'pasture_brunch_key72': '',
    'pasture_brunch_route72': '',
    'pasture_brunch_turns': 0,
    'pasture_brunch_errors': 0,
}


def _pasture_rival_pastures(observation):
    rival = observation['farms'][1-int(observation['player'])]
    return sum(isinstance(tile, dict) and tile.get('kind') == 'PASTURE'
               for row in rival['tiles'] for tile in row)


def _pasture_brunch_reset():
    _A44_PASTURE_BRUNCH_STATS.update(
        pasture_guard_rival_hands_step1=-1,
        pasture_guard_rival_pastures_step1=-1,
        pasture_guard_requested_step1='',
        pasture_guard_selected_step1='',
        pasture_guard_reset_route_map_matches=False,
        pasture_brunch_branch72='',
        pasture_brunch_key72='',
        pasture_brunch_route72='',
        pasture_brunch_turns=0,
        pasture_brunch_errors=0)


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _pasture_brunch_reset()

    if step == 72:
        branch = _BRIDGE_SELECTED
        key = _a44_goose4_key(observation) if branch == 'source' else ''
        _A44_PASTURE_BRUNCH_STATS.update(
            pasture_brunch_branch72=branch,
            pasture_brunch_key72=key)
        if branch == 'source' and key == _A44_PASTURE_BRUNCH_KEY:
            try:
                _a44_goose4_commit(_A44_PASTURE_BRUNCH_KEY,
                                   _A44_PASTURE_BRUNCH_ROUTE)
                _A44_PASTURE_BRUNCH_STATS['pasture_brunch_route72'] = str(
                    _A44_PASTURE_BRUNCH_ROUTE)
            except Exception:
                _A44_PASTURE_BRUNCH_STATS['pasture_brunch_errors'] += 1

    result = _A44_PASTURE_BRUNCH_PARENT(observation, configuration)

    if step == 0:
        _A44_PASTURE_BRUNCH_STATS['pasture_guard_reset_route_map_matches'] = (
            _DATA['route_map'] == _A44_GOOSE4_BASE_ROUTE_MAP)
    elif step == 1:
        rival_hands = len(observation['farms'][1-int(observation['player'])]['hands'])
        rival_pastures = _pasture_rival_pastures(observation)
        _A44_PASTURE_BRUNCH_STATS.update(
            pasture_guard_rival_hands_step1=rival_hands,
            pasture_guard_rival_pastures_step1=rival_pastures,
            pasture_guard_requested_step1=_BRIDGE_STATS.get('bridge_requested', ''),
            pasture_guard_selected_step1=_BRIDGE_SELECTED)
    elif step >= 72 and _A44_PASTURE_BRUNCH_STATS['pasture_brunch_route72']:
        _A44_PASTURE_BRUNCH_STATS['pasture_brunch_turns'] += 1

    agent.telemetry.update(getattr(_A44_PASTURE_BRUNCH_PARENT, 'telemetry', {}))
    agent.telemetry.update(_A44_PASTURE_BRUNCH_STATS)
    return result


agent.telemetry = {}


def kaggle_a44_goose4_smoothie_pasture_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
