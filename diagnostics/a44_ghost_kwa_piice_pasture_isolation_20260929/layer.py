# Isolated public step-1 pasture trigger and Brunch goose leaf.
_ISO_PASTURE_TRIGGERED = False
_ISO_PASTURE_PARENT_AGENT = agent
_ISO_PASTURE_KEY72 = 'BRUNCH_SPOT|M8+|C>S|G+'
_ISO_PASTURE_ROUTE72 = 113332529
_ISO_PASTURE_STATS = {
    'iso_pasture_rival_hands_step1': -1,
    'iso_pasture_rival_pastures_step1': -1,
    'iso_pasture_triggered_step1': False,
    'iso_pasture_branch_step1': '',
    'iso_pasture_reset_route_map_matches': False,
    'iso_pasture_leaf_key72': '',
    'iso_pasture_leaf_route72': '',
    'iso_pasture_leaf_turns': 0,
    'iso_pasture_leaf_errors': 0,
}

def _iso_pasture_public_count(observation):
    rival = observation['farms'][1 - int(observation['player'])]
    return sum(
        isinstance(tile, dict) and tile.get('kind') == 'PASTURE'
        for row in rival.get('tiles', [])
        for tile in row
    )

def _iso_pasture_reset():
    global _ISO_PASTURE_TRIGGERED
    _ISO_PASTURE_TRIGGERED = False
    _ISO_PASTURE_STATS.update(
        iso_pasture_rival_hands_step1=-1,
        iso_pasture_rival_pastures_step1=-1,
        iso_pasture_triggered_step1=False,
        iso_pasture_branch_step1='',
        iso_pasture_reset_route_map_matches=False,
        iso_pasture_leaf_key72='',
        iso_pasture_leaf_route72='',
        iso_pasture_leaf_turns=0,
        iso_pasture_leaf_errors=0,
    )

def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _iso_pasture_reset()

    if step == 72:
        branch = _BRIDGE_SELECTED
        key = _a44_goose4_key(observation) if branch == 'source' else ''
        _ISO_PASTURE_STATS['iso_pasture_leaf_key72'] = key
        if (_ISO_PASTURE_TRIGGERED and branch == 'source'
                and key == _ISO_PASTURE_KEY72):
            try:
                _a44_goose4_commit(_ISO_PASTURE_KEY72, _ISO_PASTURE_ROUTE72)
                _ISO_PASTURE_STATS['iso_pasture_leaf_route72'] = str(
                    _ISO_PASTURE_ROUTE72)
            except Exception:
                _ISO_PASTURE_STATS['iso_pasture_leaf_errors'] += 1

    result = _ISO_PASTURE_PARENT_AGENT(observation, configuration)

    if step == 0:
        _ISO_PASTURE_STATS['iso_pasture_reset_route_map_matches'] = (
            _DATA['route_map'] == _PIICE_BASE_ROUTE_MAP)
    elif step == 1:
        rival_hands = len(observation['farms'][1 - int(observation['player'])]['hands'])
        rival_pastures = _iso_pasture_public_count(observation)
        _ISO_PASTURE_STATS.update(
            iso_pasture_rival_hands_step1=rival_hands,
            iso_pasture_rival_pastures_step1=rival_pastures,
            iso_pasture_triggered_step1=bool(_ISO_PASTURE_TRIGGERED),
            iso_pasture_branch_step1=str(_BRIDGE_SELECTED),
        )
    elif step >= 72 and _ISO_PASTURE_STATS['iso_pasture_leaf_route72']:
        _ISO_PASTURE_STATS['iso_pasture_leaf_turns'] += 1

    agent.telemetry.update(getattr(_ISO_PASTURE_PARENT_AGENT, 'telemetry', {}))
    agent.telemetry.update(_ISO_PASTURE_STATS)
    return result

agent.telemetry = {}

def kaggle_a44_isolated_pasture_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
