"""Build and statically verify the isolated 6d pasture derivative."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SIXD_DIR = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
PASTURE_DIR = ROOT / 'diagnostics/pasture_guard_source_leaf_20260928'
SOURCE = SIXD_DIR / 'candidate.py'
PAIR_ROWS = SIXD_DIR / 'pair_rows.json'
SIXD_FEATURES = SIXD_DIR / 'feature_rows.json'
PARENT_PANEL = SIXD_DIR / 'parent_panel.json'
PASTURE_FEATURES = PASTURE_DIR / 'feature_rows.json'
LAYER = HERE / 'layer.py'
PLAN = HERE / 'PLAN.md'
CANDIDATE = HERE / 'candidate.py'
DIFF = HERE / 'candidate.diff.txt'
STATIC = HERE / 'static_preflight.json'

SOURCE_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
A44_SHA = 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
LEAF_KEY = 'BRUNCH_SPOT|M8+|C>S|G+'
LEAF_ROUTE = 113332529
TARGETS = {'live-114274897', 'public-win-114193811'}
# Match the actual frozen line exactly; a guard below diagnoses source drift.
OLD_SELECTOR = (
    b"        branch = 'shared151' if hands>=5 else "
    b"('shared150' if _BRIDGE_VARIANT=='five_or_zero' and hands==0 else 'source')"
)
NEW_SELECTOR = (
    b"        rival_pastures = _pasture_rival_pastures(observation)\n"
    b"        branch = 'shared151' if hands>=5 and rival_pastures == 0 else 'source'"
)
FORCED_SOURCE_SELECTOR = b"        branch = 'source'"


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump_new(path: Path, value) -> None:
    raw = (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(raw)


def expected_candidate_bytes() -> tuple[bytes, bytes]:
    source = SOURCE.read_bytes()
    if sha_bytes(source) != SOURCE_SHA:
        raise AssertionError('the exact 6d parent bytes or hash changed')
    if source.count(OLD_SELECTOR) != 1:
        raise AssertionError('the frozen 6d step-1 selector line is not unique')
    patched = source.replace(OLD_SELECTOR, NEW_SELECTOR, 1)
    if patched.count(NEW_SELECTOR) != 1 or patched.replace(NEW_SELECTOR, OLD_SELECTOR, 1) != source:
        raise AssertionError('the selector patch cannot be reversed to the exact 6d parent')
    layer = LAYER.read_bytes()
    if not layer.endswith(b'\n'):
        raise AssertionError('the source-only layer must end with a newline')
    candidate = patched + b'\n' + layer
    return candidate, patched


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot load static policy module {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_selector_ast(source: str) -> dict:
    tree = ast.parse(source)
    assignments = []
    bridge_functions = [node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == 'agent']
    for bridge in bridge_functions:
        for node in ast.walk(bridge):
            if isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == 'branch'
                    for target in node.targets):
                if any(isinstance(child, ast.Name) and child.id == 'hands'
                       for child in ast.walk(node.value)):
                    assignments.append((bridge, node))
    relevant = [node for _, node in assignments]
    if len(relevant) != 1:
        raise AssertionError('expected one hand-conditioned bridge selector')
    node = relevant[0]
    bridge = next(function for function, assignment in assignments if assignment is node)
    rendered = ast.unparse(node.value)
    if rendered != "'shared151' if hands >= 5 and rival_pastures == 0 else 'source'":
        raise AssertionError(f'unexpected selector expression: {rendered}')
    pastures_assignment = [item for item in ast.walk(bridge)
                           if isinstance(item, ast.Assign)
                           and any(isinstance(target, ast.Name)
                                   and target.id == 'rival_pastures'
                                   for target in item.targets)]
    if len(pastures_assignment) != 1 or ast.unparse(pastures_assignment[0].value) != (
            '_pasture_rival_pastures(observation)'):
        raise AssertionError('selector does not count public rival pasture tiles')
    return {'expression': rendered,
            'pasture_count_expression': ast.unparse(pastures_assignment[0].value)}


def count_public_pastures(observation: dict, seat: int) -> int:
    rival = observation['farms'][1 - int(seat)]
    return sum(isinstance(tile, dict) and tile.get('kind') == 'PASTURE'
               for row in rival['tiles'] for tile in row)


def verify_route_map(module) -> dict:
    base = deepcopy(module._A44_GOOSE4_BASE_ROUTE_MAP)
    current = deepcopy(module._DATA['route_map'])
    if current != base:
        raise AssertionError('import-time source route map differs from the Goose4 reset map')
    route_key = str(LEAF_ROUTE)
    route = module._DATA['routes'].get(route_key)
    if route is None or len(route) != 719:
        raise AssertionError('the frozen Brunch route must resolve to a 719-action schedule')
    if module._A44_PASTURE_BRUNCH_KEY != LEAF_KEY:
        raise AssertionError('appended source leaf key differs from the frozen Brunch key')
    if module._A44_PASTURE_BRUNCH_ROUTE != LEAF_ROUTE:
        raise AssertionError('appended source leaf route differs from the frozen route')

    module._a44_goose4_commit(LEAF_KEY, LEAF_ROUTE)
    changed = sorted(key for key in set(base) | set(module._DATA['route_map'])
                     if base.get(key) != module._DATA['route_map'].get(key))
    expected = sorted({key for key in base if key.split('|', 1)[0] == 'BRUNCH_SPOT'}
                      | {'BRUNCH_SPOT'})
    if changed != expected:
        raise AssertionError(f'Brunch commit changed an unexpected route-map set: {changed}')
    if any(module._DATA['route_map'].get(key) != LEAF_ROUTE for key in expected):
        raise AssertionError('Brunch commit did not assign the frozen route to every descendant')
    for key in set(base) - set(expected):
        if module._DATA['route_map'].get(key) != base[key]:
            raise AssertionError(f'Brunch commit changed another route: {key}')

    module._a44_goose4_reset()
    if module._DATA['route_map'] != base:
        raise AssertionError('Goose4 reset does not restore the original source route map')
    return {'base_route_map_sha256': sha_bytes(json.dumps(
                base, sort_keys=True, separators=(',', ':')).encode('utf-8')),
            'brunch_descendants_changed': changed,
            'reset_restores_base': True,
            'route_id': LEAF_ROUTE,
            'route_action_count': len(route)}


def census() -> dict:
    pair = read_json(PAIR_ROWS)
    features = read_json(PASTURE_FEATURES)
    sixd_features = read_json(SIXD_FEATURES)
    panel = read_json(PARENT_PANEL)
    if not pair.get('complete') or len(pair.get('rows', [])) != 208:
        raise AssertionError('6d pair row receipt is not complete at 208 rows')
    if pair.get('source_a44_sha256') != A44_SHA or pair.get('source_feature_rows_sha256') != sha(SIXD_FEATURES):
        raise AssertionError('6d pair rows are not bound to their feature rows and a44 source')
    if not sixd_features.get('complete') or len(sixd_features.get('rows', [])) != 208:
        raise AssertionError('6d source feature receipt is not complete at 208 rows')
    if sixd_features.get('source_a44_sha256') != A44_SHA:
        raise AssertionError('6d features are not from the exact a44 source lineage')
    if features.get('row_count') != 208 or len(features.get('rows', [])) != 208:
        raise AssertionError('pasture public feature receipt is not complete at 208 rows')
    if len(panel.get('fixtures', [])) != 104:
        raise AssertionError('the 6d parent panel does not bind 104 fixtures')

    pasture_by_key = {}
    for row in features['rows']:
        prov = row['provenance']
        key = (prov['fixture_id'], int(prov['candidate_seat']))
        if key in pasture_by_key:
            raise AssertionError(f'duplicate pasture public feature row {key}')
        pasture_by_key[key] = row
    sixd_by_key = {(row['fixture_id'], int(row['seat'])): row
                   for row in sixd_features['rows']}
    if len(sixd_by_key) != 208:
        raise AssertionError('6d feature rows are not unique')
    parent_by_id = {row['fixture_id']: row for row in panel['fixtures']}
    if len(parent_by_id) != 104:
        raise AssertionError('6d parent fixture IDs are not unique')
    if set(parent_by_id) != {key[0] for key in pasture_by_key}:
        raise AssertionError('6d parent fixture set differs from the 208-row feature set')

    rows = []
    branch_counts = Counter()
    source_leaf_counts = Counter()
    changed = []
    for row in sorted(pair['rows'], key=lambda item: (item['fixture_id'], int(item['seat']))):
        key = (row['fixture_id'], int(row['seat']))
        if key not in pasture_by_key or key not in sixd_by_key:
            raise AssertionError(f'joined feature row is missing: {key}')
        pasture = pasture_by_key[key]
        features_public = pasture['selector_features']
        hands = int(row['rival_hands_step1'])
        pasture_count = int(row['rival_pasture_count_step1'])
        if (hands != int(features_public['obs1_rival_hands'])
                or pasture_count != int(features_public['obs1_rival_pasture_count'])):
            raise AssertionError(f'public step-1 inputs disagree across frozen rows: {key}')
        old = row['bridge_branch']
        expected_old = 'shared151' if hands >= 5 else 'source'
        if old != expected_old:
            raise AssertionError(f'6d observed branch disagrees with its five-hand selector: {key}')
        new = 'shared151' if hands >= 5 and pasture_count == 0 else 'source'
        branch_counts[(old, new)] += 1
        leaf_key = row['rule_key']
        projected_leaf = new == 'source' and leaf_key == LEAF_KEY
        source_leaf_counts[(new, bool(projected_leaf))] += 1
        if old != new:
            changed.append(key)
        fixture = parent_by_id[key[0]]
        if fixture.get('source_action_tape_path') is None:
            raise AssertionError(f'fixture lacks a frozen opponent action tape: {key[0]}')
        if row.get('trace_path') is None or row.get('trace_sha256') is None:
            raise AssertionError(f'feature row lacks bound trace provenance: {key}')
        rows.append({
            'fixture_id': key[0], 'seat': key[1], 'panel': row['panel'],
            'seed': int(fixture['seed']),
            'old_branch': old, 'guarded_branch': new,
            'rival_hands_step1': hands,
            'rival_pasture_count_step1': pasture_count,
            'parent_branch_step72_key_provenance_only': leaf_key,
            'projected_leaf_eligibility_unverified_until_source_prefix': bool(projected_leaf),
            'smoothie_rule_active_in_parent_trace': bool(row.get('smoothie_rule_active')),
            'parent_selected_route': row.get('selected_route'),
            'trace_path': row['trace_path'], 'trace_sha256': row['trace_sha256'],
            'source_replay_path': fixture['source_replay_path'],
            'source_replay_sha256': fixture['source_replay_sha256'],
            'action_tape_path': fixture['source_action_tape_path'],
            'source_opponent_action_sha256': fixture['source_opponent_action_sha256'],
        })

    expected_changed = {
        ('live-114274897', 0), ('live-114274897', 1),
        ('public-win-114193811', 0), ('public-win-114193811', 1),
    }
    if set(changed) != expected_changed:
        raise AssertionError(f'guard branch transitions exceed or miss planned rows: {changed}')
    if branch_counts != Counter({('source', 'source'): 190,
                                 ('shared151', 'shared151'): 14,
                                 ('shared151', 'source'): 4}):
        raise AssertionError(f'unexpected 208-row branch census: {branch_counts}')
    # These are source-leaf hypotheses taken from parent shared151 traces only.
    # Runtime step-72 keys are freshly generated by the prefix jobs.
    if source_leaf_counts[("source", True)] != 2:
        raise AssertionError('parent public-feature projection no longer identifies only the two THIRD seats')
    if any(row['projected_leaf_eligibility_unverified_until_source_prefix']
           for row in rows if row['fixture_id'] not in TARGETS):
        raise AssertionError('a nontarget row projects a source Brunch leaf trigger')
    return {
        'row_count': len(rows),
        'fixture_count': len(parent_by_id),
        'branch_transition_counts': {f'{a}->{b}': n for (a, b), n in sorted(branch_counts.items())},
        'source_leaf_projection_counts': {
            f'{branch}/eligible={eligible}': count
            for (branch, eligible), count in sorted(source_leaf_counts.items())},
        'changed_rows': [f'{fid}/seat{seat}' for fid, seat in sorted(changed)],
        'changed_fixture_ids': sorted({fid for fid, _ in changed}),
        'source_leaf_projection_scope': [f'{fid}/seat{seat}' for fid, seat in sorted(
            key for key in expected_changed if key[0] == 'live-114274897')],
        'rows': rows,
    }


def preflight_payload() -> dict:
    candidate_bytes, patched = expected_candidate_bytes()
    if not CANDIDATE.is_file():
        raise FileNotFoundError('candidate.py must be generated by build before static preflight')
    if CANDIDATE.read_bytes() != candidate_bytes:
        raise AssertionError('candidate bytes are not exact parent + one selector patch + layer')
    source_text = patched.decode('utf-8')
    selector_check = check_selector_ast(source_text)
    parent = load_module(SOURCE, '_pasture_6d_parent_static')
    candidate = load_module(CANDIDATE, '_pasture_6d_candidate_static')
    if (parent._BRIDGE_VARIANT != 'five_hand'
            or candidate._BRIDGE_VARIANT != 'five_hand'):
        raise AssertionError('parent or derivative bridge variant drifted from five_hand')
    donors = sorted(parent._BRIDGE_DONORS)
    if donors != sorted(candidate._BRIDGE_DONORS):
        raise AssertionError('donor namespaces differ from the frozen parent')
    for name in donors:
        for member in ('_DONOR_MAP', '_DONOR_ROUTES'):
            if parent._BRIDGE_DONORS[name][member] != candidate._BRIDGE_DONORS[name][member]:
                raise AssertionError(f'donor {name} {member} changed')
    route_check = verify_route_map(candidate)
    census_data = census()
    return {
        'schema': 'a44-goose4-smoothie-pasture-static-preflight-v1',
        'passed': True,
        'static_only': True,
        'simulator_jobs_run': 0,
        'native_transitions': 0,
        'full_game_outcomes_run': False,
        'parent_candidate_path': str(SOURCE.resolve()),
        'parent_candidate_sha256': SOURCE_SHA,
        'candidate_path': str(CANDIDATE.resolve()),
        'candidate_sha256': sha_bytes(candidate_bytes),
        'candidate_is_exact_parent_patch_plus_layer': True,
        'selector_patch_count': 1,
        'selector_check': selector_check,
        'layer_path': str(LAYER.resolve()),
        'layer_sha256': sha(LAYER),
        'plan_path': str(PLAN.resolve()),
        'plan_sha256': sha(PLAN),
        'donor_namespaces_byte_source_preserved': donors,
        'route_map_static_check': route_check,
        'census_inputs': {
            'pair_rows_path': str(PAIR_ROWS.resolve()), 'pair_rows_sha256': sha(PAIR_ROWS),
            '6d_feature_rows_path': str(SIXD_FEATURES.resolve()), '6d_feature_rows_sha256': sha(SIXD_FEATURES),
            'pasture_public_feature_rows_path': str(PASTURE_FEATURES.resolve()), 'pasture_public_feature_rows_sha256': sha(PASTURE_FEATURES),
            'parent_panel_path': str(PARENT_PANEL.resolve()), 'parent_panel_sha256': sha(PARENT_PANEL),
        },
        'census': census_data,
        'source_step72_key_limit': ('parent feature keys are provenance only; the four prefix jobs must compute their own keys under forced-source 6d'),
    }


def build() -> None:
    if any(path.exists() for path in (CANDIDATE, DIFF, STATIC)):
        raise FileExistsError('derivative artifacts already exist; refusing to overwrite')
    candidate, patched = expected_candidate_bytes()
    with CANDIDATE.open('xb') as stream:
        stream.write(candidate)
    diff = (
        'Parent SHA-256: ' + SOURCE_SHA + '\n'
        'Parent bytes: ' + str(SOURCE.stat().st_size) + '\n'
        'Exact selector replacement (one occurrence):\n'
        + OLD_SELECTOR.decode('ascii') + '\n=>\n'
        + NEW_SELECTOR.decode('ascii') + '\n'
        'Appended layer: layer.py sha256=' + sha(LAYER) + '\n'
        'Reversing the selector replacement and removing the appended layer '
        'reproduces the parent bytes exactly.\n'
    ).encode('utf-8')
    with DIFF.open('xb') as stream:
        stream.write(diff)
    payload = preflight_payload()
    dump_new(STATIC, payload)
    print(json.dumps({'built': True, 'candidate_sha256': sha(CANDIDATE),
                      'static_preflight_sha256': sha(STATIC),
                      'rows': payload['census']['row_count'],
                      'changed_rows': payload['census']['changed_rows'],
                      'simulator_jobs_run': 0}, indent=2))


def verify() -> None:
    payload = preflight_payload()
    frozen = read_json(STATIC)
    if frozen != payload:
        raise AssertionError('static preflight is stale or does not reproduce from bound files')
    if DIFF.read_bytes().count(OLD_SELECTOR) != 1:
        raise AssertionError('candidate diff no longer binds the exact selector replacement')
    print(json.dumps({'verified': True, 'candidate_sha256': sha(CANDIDATE),
                      'static_preflight_sha256': sha(STATIC),
                      'changed_rows': payload['census']['changed_rows'],
                      'simulator_jobs_run': 0}, indent=2))


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('build', 'verify'))
    args = parser.parse_args()
    if args.phase == 'build':
        build()
    else:
        verify()


if __name__ == '__main__':
    main()
