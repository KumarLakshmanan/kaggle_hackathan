# Isolated exact market-phase acceleration for the inherited generated search.
# End-of-day transitions retain the original full interpreter path.
_FAST_PROJECTOR = _pro_sys.modules[_PRO_PACKAGE_NAME+'.pro.projection']
_FAST_ORIGINAL_ADVANCE = _SEARCH_ENGINE['advance']
_FAST_REFERENCE = None
_FAST_PREPARED = {}
_FAST_STATS = {'parent_factored_calls': 0, 'parent_factored_preparations': 0, 'parent_full_fallbacks': 0}


def _fast_parent_advance(world, seat, action, reference, scenario):
    global _FAST_REFERENCE, _FAST_PREPARED
    cfg = world[1].configuration
    tpd = max(1, int(cfg.get('turnsPerDay', 24)))
    same_workers = (action.get('farmer', ['PASS']) == reference.get('farmer', ['PASS']) and
                    action.get('hands', []) == reference.get('hands', []))
    if (int(world[0][0].observation.step)+1)%tpd == 0 or not same_workers:
        _FAST_STATS['parent_full_fallbacks'] += 1
        return _FAST_ORIGINAL_ADVANCE(world, seat, action, reference, scenario)
    if _FAST_REFERENCE is not reference:
        _FAST_REFERENCE = reference
        _FAST_PREPARED = {}
    key = (id(world), seat, scenario['name'])
    entry = _FAST_PREPARED.get(key)
    if entry is None or entry[0] is not world:
        rival = _SEARCH_ENGINE['rival_action'](world[0], seat, reference, scenario)
        joint = [None, None]; joint[seat] = reference; joint[1-seat] = rival
        prepared = _FAST_PROJECTOR.prepare(world, joint)
        entry = (world, prepared, rival.get('market', []))
        _FAST_PREPARED[key] = entry
        _FAST_STATS['parent_factored_preparations'] += 1
    queues = [None, None]; queues[seat] = action.get('market', []); queues[1-seat] = entry[2]
    result = _FAST_PROJECTOR.project(entry[1], queues)
    _FAST_STATS['parent_factored_calls'] += 1
    return result, entry[1][1]


_SEARCH_ENGINE['advance'] = _fast_parent_advance
