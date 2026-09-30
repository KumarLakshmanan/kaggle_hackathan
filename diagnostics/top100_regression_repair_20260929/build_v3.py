"""Minimal route repair from the exact 4ee source and existing planting repair."""
import ast
from datetime import datetime, timezone
import json
from build import HERE, ROOT, BASE, BASE_SHA, SOURCE, SOURCE_SHA, sha, load

SUFFIX = '''

# Select a complete compatible schedule after observing the first two shops.
_REPAIR_ROUTES = {'BRUNCH_SPOT|BRUNCH_SPOT': 113373693,
                  'BRUNCH_SPOT|SMOOTHIE_SHOP': 113557748,
                  'ICE_CREAM_SHOP|PET_CAFE': 113336042}
for _repair_pair, _repair_route in _REPAIR_ROUTES.items():
    for _repair_key in list(_DATA['route_map']):
        if _repair_key == _repair_pair or _repair_key.startswith(_repair_pair + '|'):
            _DATA['route_map'][_repair_key] = _repair_route
    _DATA['route_map'][_repair_pair] = _repair_route

_MINIMAL_REPAIR_PARENT = agent
_MINIMAL_REPAIR_STATS = {'minimal_route_pair144': '', 'minimal_route': '',
                         'minimal_route_turns': 0}


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _MINIMAL_REPAIR_STATS.update(minimal_route_pair144='', minimal_route='',
                                    minimal_route_turns=0)
    result = _MINIMAL_REPAIR_PARENT(observation, configuration)
    pair = '|'.join(observation['town']['unlocked_shops'][:2])
    if step == 144:
        _MINIMAL_REPAIR_STATS['minimal_route_pair144'] = pair
    if step >= 144 and pair in _REPAIR_ROUTES:
        _MINIMAL_REPAIR_STATS['minimal_route'] = str(_REPAIR_ROUTES[pair])
        _MINIMAL_REPAIR_STATS['minimal_route_turns'] += 1
    agent.telemetry.update(_MINIMAL_REPAIR_STATS)
    return result


agent.telemetry = {}


def kaggle_minimal_route_repair_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''


def main():
    assert sha(BASE) == BASE_SHA and sha(SOURCE) == SOURCE_SHA
    donor = SOURCE.read_text(encoding='utf-8')
    start = donor.index('_PLANT_CORE = {}')
    end = donor.index('"""Commit a compatible complete schedule while retaining the planting repair."""')
    partial = donor[start:end]
    assert '_PARTIAL_PARENT = agent' in partial
    source = BASE.read_text(encoding='utf-8') + '\n' + partial + SUFFIX
    ast.parse(source)
    destination = HERE / 'candidate_v3.py'
    assert not destination.exists()
    destination.write_text(source, encoding='utf-8', newline='\n')
    old, new = load(BASE, 'minimal_old'), load(destination, 'minimal_new')
    assert old._DATA['opening'] == new._DATA['opening']
    assert old._DATA['routes'] == new._DATA['routes']
    for pair, route in new._REPAIR_ROUTES.items():
        first = str(old._DATA['route_map'][pair.split('|')[0]])
        assert old._DATA['routes'][str(route)][72:144] == old._DATA['routes'][first][72:144]
    changes = {k: v for k, v in new._DATA['route_map'].items() if old._DATA['route_map'].get(k) != v}
    assert all(any(k == pair or k.startswith(pair + '|') for pair in new._REPAIR_ROUTES) for k in changes)
    manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
                    candidate=str(destination), candidate_sha256=sha(destination),
                    source=str(BASE), source_sha256=BASE_SHA,
                    baseline=str(BASE), baseline_sha256=BASE_SHA,
                    planting_source=str(SOURCE), planting_source_sha256=SOURCE_SHA,
                    plan_sha256=sha(HERE / 'PLAN_V3.md'),
                    expected_entrypoint='kaggle_minimal_route_repair_entrypoint',
                    changed_route_map=changes, schedule_prefix_compatible=True,
                    original_opening_and_route_tapes_preserved=True,
                    root_main_sha256=sha(ROOT / 'main.py'))
    (HERE / 'manifest_v3.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
