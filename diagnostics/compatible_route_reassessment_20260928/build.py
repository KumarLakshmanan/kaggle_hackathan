from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE_SHA = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
REPLACEMENTS = {
    'BRUNCH_SPOT|BRUNCH_SPOT': (113371344, 113365392),
    'YARN_STORE|FARMERS_MARKET': (113661901, 113660799),
    'SMOOTHIE_SHOP|ICE_CREAM_SHOP': (113441389, 113772818),
}


def main():
    original = (ROOT / 'main.py').read_bytes()
    assert hashlib.sha256(original).hexdigest() == SOURCE_SHA
    spec = importlib.util.spec_from_file_location('compatible_route_source', ROOT / 'main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    changed = {}
    for pair, (incumbent, alternate) in REPLACEMENTS.items():
        old, new = module._DATA['routes'][str(incumbent)], module._DATA['routes'][str(alternate)]
        assert len(old) == len(new) == 719 and old[:144] == new[:144]
        assert module._DATA['route_map'][pair] == incumbent
        changed[pair] = sum(k == pair or k.startswith(pair + '|') for k in module._DATA['route_map'])
    layer = '''

# A complete alternative is committed at the second publicly revealed shop.
_COMPAT_ROUTES = ROUTES_VALUE
for _compat_key in list(_DATA["route_map"]):
    for _compat_prefix, _compat_route in _COMPAT_ROUTES.items():
        if _compat_key == _compat_prefix or _compat_key.startswith(_compat_prefix + "|"):
            _DATA["route_map"][_compat_key] = _compat_route

_COMPAT_PARENT = agent
_COMPAT_STATS = {"compatible_route_turns": 0, "compatible_route": ""}

def agent(observation, configuration=None):
    step = int(observation["step"])
    if step == 0:
        _COMPAT_STATS.update(compatible_route_turns=0, compatible_route="")
    result = _COMPAT_PARENT(observation, configuration)
    pair = "|".join(observation["town"]["unlocked_shops"][:2])
    if step >= 144 and pair in _COMPAT_ROUTES:
        _COMPAT_STATS["compatible_route_turns"] += 1
        _COMPAT_STATS["compatible_route"] = str(_COMPAT_ROUTES[pair])
    agent.telemetry.update(_COMPAT_STATS)
    return result

agent.telemetry = {}

def kaggle_compatible_complete_route_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''.replace('ROUTES_VALUE', repr({k: v[1] for k,v in REPLACEMENTS.items()}))
    target = HERE / 'candidate.py'
    blob = original + layer.encode()
    compile(blob, str(target), 'exec')
    target.write_bytes(blob)
    manifest = {'candidate': str(target), 'candidate_sha256': hashlib.sha256(blob).hexdigest(),
                'source_sha256': SOURCE_SHA, 'plan_sha256': hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(),
                'replacements': REPLACEMENTS, 'map_entries_changed': changed}
    (HERE/'candidate_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
