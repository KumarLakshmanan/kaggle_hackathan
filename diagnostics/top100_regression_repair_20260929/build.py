"""Build a source-only rollback from the exact downloaded September 29 policy."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = ROOT / 'diagnostics/submission_top100_compare_20260929_1104'
SOURCE = PRIOR / 'downloaded/main_ae349d83.py'
BASE = PRIOR / 'downloaded/main_4eeac9c3.py'
SOURCE_SHA = 'ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb'
BASE_SHA = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    assert sha(SOURCE) == SOURCE_SHA and sha(BASE) == BASE_SHA
    source = SOURCE.read_text(encoding='utf-8')
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    replacements = []
    bridge = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'agent'
              and any(isinstance(x, ast.Global) and '_BRIDGE_SELECTED' in x.names for x in n.body)]
    assert len(bridge) == 1
    replacement = '''def agent(observation, configuration=None):
    """Keep the source schedule; rival worker count cannot switch the opening."""
    global _BRIDGE_SELECTED, _ISO_PASTURE_TRIGGERED
    step = int(observation['step'])
    player = int(observation['player'])
    if step == 0:
        _BRIDGE_SELECTED = 'source'
        _ISO_PASTURE_TRIGGERED = False
        _BRIDGE_STATS.update(bridge_selected='source', bridge_requested='source',
                            bridge_rival_hands=-1, bridge_common_failed=0,
                            bridge_guard_refusals=0, bridge_source_guard_failed=0,
                            bridge_errors=0)
        agent.telemetry.clear()
    elif step == 1:
        hands = len(observation['farms'][1-player]['hands'])
        _ISO_PASTURE_TRIGGERED = (hands == 5 and _iso_pasture_public_count(observation) == 1)
        _BRIDGE_STATS['bridge_rival_hands'] = hands
    result = _BRIDGE_SOURCE_AGENT(observation, configuration)
    agent.telemetry.update(_BRIDGE_STATS)
    return result
'''
    node = bridge[0]
    replacements.append((node.lineno - 1, node.end_lineno, replacement))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(t, ast.Name) and t.id == '_LOSS_POOL_REPLACEMENTS' for t in node.targets):
            mapping = ast.literal_eval(node.value)
            assert mapping.pop('BRUNCH_SPOT|PIZZA_SHOP') == 113413613
            replacements.append((node.lineno - 1, node.end_lineno,
                                 '_LOSS_POOL_REPLACEMENTS = ' + repr(mapping) + '\n'))
    assert len(replacements) == 2
    for start, end, value in sorted(replacements, reverse=True):
        lines[start:end] = [value]
    candidate = ''.join(lines)
    for line in ("_DATA['opening'][0] = copy.deepcopy(_BRIDGE_COMMON)\n",
                 "_DATA['opening'][1] = copy.deepcopy(_BRIDGE_SOURCE_ONE)\n"):
        assert candidate.count(line) == 1
        candidate = candidate.replace(line, '')
    candidate = candidate.replace("_BRIDGE_VARIANT = 'five_hand'", "_BRIDGE_VARIANT = 'source_only_repair'")
    ast.parse(candidate)
    destination = HERE / 'candidate_v1.py'
    assert not destination.exists()
    destination.write_text(candidate, encoding='utf-8', newline='\n')
    old, new = load(BASE, 'repair_base'), load(destination, 'repair_candidate')
    assert old._DATA['opening'] == new._DATA['opening']
    key = 'BRUNCH_SPOT|PIZZA_SHOP'
    assert key not in new._LOSS_POOL_REPLACEMENTS
    for route_key, route in old._DATA['route_map'].items():
        if route_key == key or route_key.startswith(key + '|'):
            assert new._DATA['route_map'][route_key] == route
    manifest = {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'candidate': str(destination), 'candidate_sha256': sha(destination),
        'source': str(SOURCE), 'source_sha256': SOURCE_SHA,
        'baseline': str(BASE), 'baseline_sha256': BASE_SHA,
        'plan_sha256': sha(HERE / 'PLAN.md'),
        'original_opening_restored': True, 'brunch_pizza_mapping_restored': True,
        'root_main_sha256': sha(ROOT / 'main.py'),
    }
    (HERE / 'manifest_v1.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
