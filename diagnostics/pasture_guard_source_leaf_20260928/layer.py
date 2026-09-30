"""Source-only previously frozen Brunch goose leaf, after a public pasture guard."""
_GUARD_LEAF_PARENT = _BRIDGE_SOURCE_AGENT
_GUARD_LEAF_BASE_MAP = dict(_DATA['route_map'])
_GUARD_LEAF_STATS = {'guard_leaf_key72':'', 'guard_leaf_route':'', 'guard_leaf_turns':0}


def _guard_rival_pastures(observation):
    rival = observation['farms'][1-int(observation['player'])]
    return sum(isinstance(tile,dict) and tile.get('kind')=='PASTURE'
               for row in rival['tiles'] for tile in row)


def _guard_leaf_key(observation):
    rival = observation['farms'][1-int(observation['player'])]
    melon = cow = sheep = goose = 0
    for row in rival['tiles']:
        for tile in row:
            if isinstance(tile,dict):
                melon += tile.get('crop')=='MELON'
                cow += tile.get('animal')=='COW'
                sheep += tile.get('animal')=='SHEEP'
                goose += tile.get('animal')=='GOOSE'
    comparison = 'C<S' if cow<sheep else 'C>S' if cow>sheep else 'C=S'
    return (observation['town']['unlocked_shops'][0]+'|'+('M8+' if melon>=8 else 'M<8')
            +'|'+comparison+('|G+' if goose>0 else '|G0'))


def _guard_leaf_reset():
    _DATA['route_map'].clear()
    _DATA['route_map'].update(_GUARD_LEAF_BASE_MAP)
    _GUARD_LEAF_STATS.update(guard_leaf_key72='',guard_leaf_route='',guard_leaf_turns=0)
    _BRIDGE_STATS['bridge_rival_pastures'] = 0


def _guard_leaf_commit():
    for key in list(_DATA['route_map']):
        if key.split('|')[0]=='BRUNCH_SPOT':
            _DATA['route_map'][key] = 113332529
    _DATA['route_map']['BRUNCH_SPOT'] = 113332529


def _guard_source_agent(observation, configuration=None):
    step = int(observation['step'])
    if step==0:
        _guard_leaf_reset()
    if step==72:
        leaf = _guard_leaf_key(observation)
        _GUARD_LEAF_STATS['guard_leaf_key72'] = leaf
        if leaf=='BRUNCH_SPOT|M8+|C>S|G+':
            _guard_leaf_commit()
            _GUARD_LEAF_STATS['guard_leaf_route'] = '113332529'
    result = _GUARD_LEAF_PARENT(observation,configuration)
    if step>=72 and _GUARD_LEAF_STATS['guard_leaf_route']:
        _GUARD_LEAF_STATS['guard_leaf_turns'] += 1
    agent.telemetry.update(_GUARD_LEAF_STATS)
    return result


_BRIDGE_SOURCE_AGENT = _guard_source_agent


def kaggle_pasture_guard_source_leaf_entrypoint(observation, configuration=None):
    return agent(observation,configuration)
