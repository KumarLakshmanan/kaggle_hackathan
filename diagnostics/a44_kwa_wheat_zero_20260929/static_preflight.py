"""Read-only static/hash preflight; never invokes an agent or game engine."""
from __future__ import annotations

import ast
import copy
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PARENT_SHA256 = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
KEY = 'BRUNCH_SPOT|M8+|C<S|G0'
ROUTE = 113535489
INPUT_PATHS = {
    'parent_candidate': 'diagnostics/a44_goose4_smoothie_source_20260929/candidate.py',
    'parent_manifest': 'diagnostics/a44_goose4_smoothie_source_20260929/frozen_manifest.json',
    'feature_rows_208': 'diagnostics/a44_goose4_smoothie_source_20260929/feature_rows.json',
    'a44_control_rows_208': 'diagnostics/a44_goose4_smoothie_source_20260929/a44_controls.json',
    'parent_panel': 'diagnostics/a44_goose4_smoothie_source_20260929/parent_panel.json',
    'parent_combined_results': 'diagnostics/a44_goose4_smoothie_source_20260929/combined_results.json',
    'a44_source': 'diagnostics/a44_source_bridge_goose_4leaf_20260929/source_a44.py',
    'exclusive_run_lock_utility': 'diagnostics/local_target_20260928/run_lock.py',
    'native_replay_adapter': 'diagnostics/stream_replay_io_20260928/fast_game_cached.py',
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def root_path(relative: str) -> Path:
    return ROOT / Path(relative)


def frozen_step72(trace_path: Path) -> dict:
    with gzip.open(trace_path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            record = json.loads(line)
            if int(record.get('step', -1)) == 72:
                return record
    raise AssertionError(f'no observation-72 row in {trace_path}')


def public_leaf(observation: dict) -> tuple[str, dict, int]:
    shops = observation['town']['unlocked_shops']
    assert shops, 'step 72 must expose at least one shop'
    rival = observation['farms'][1 - int(observation['player'])]
    counts = {'MELON': 0, 'COW': 0, 'SHEEP': 0, 'GOOSE': 0}
    wheat_plots = 0
    for row in rival['tiles']:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            crop = tile.get('crop')
            animal = tile.get('animal')
            if crop == 'MELON':
                counts['MELON'] += 1
            if crop == 'WHEAT':
                wheat_plots += 1
            for name in ('COW', 'SHEEP', 'GOOSE'):
                if animal == name:
                    counts[name] += 1
    comparison = ('C<S' if counts['COW'] < counts['SHEEP'] else
                  'C>S' if counts['COW'] > counts['SHEEP'] else 'C=S')
    key = shops[0] + '|' + ('M8+' if counts['MELON'] >= 8 else 'M<8') + '|'
    key += comparison + ('|G+' if counts['GOOSE'] > 0 else '|G0')
    return key, counts, wheat_plots


def load_candidate_without_call(candidate_path: Path) -> ModuleType:
    # Import is limited to module definitions and embedded route data. This
    # preflight never calls candidate.agent or imports/starts Kaggle.
    spec = importlib.util.spec_from_file_location('_kwa_wheat_zero_static_candidate', candidate_path)
    if spec is None or spec.loader is None:
        raise AssertionError('could not load candidate definitions')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_parent_call_and_predicate(candidate_path: Path, layer_path: Path) -> dict:
    source = candidate_path.read_text(encoding='utf-8')
    layer = layer_path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    wrappers = [node for node in functions if node.name == 'agent']
    assert wrappers and wrappers[-1].lineno > wrappers[-2].lineno
    wrapper = wrappers[-1]
    parent_calls = []
    for statement in wrapper.body:
        calls = [node for node in ast.walk(statement)
                 if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name)
                 and node.func.id == '_A44_KWA_WHEAT_ZERO_PARENT']
        if calls:
            parent_calls.extend((statement, call) for call in calls)
    assert len(parent_calls) == 1, 'outer wrapper must call the frozen parent once'
    call_statement, _ = parent_calls[0]
    assert isinstance(call_statement, ast.Assign), 'parent call must be a direct wrapper statement'
    assert isinstance(call_statement.value, ast.Call)
    assert call_statement.value.func.id == '_A44_KWA_WHEAT_ZERO_PARENT'
    assert any(isinstance(node, ast.Return) and isinstance(node.value, ast.Name)
               and node.value.id == 'result' for node in wrapper.body)
    assert '_a44_kwa_wheat_zero_commit()' in layer
    assert layer.count('_a44_kwa_wheat_zero_commit()') == 2  # one definition and one guarded call
    assert 'int(step) == 72' in layer
    assert "bridge_branch == 'source'" in layer
    assert "public_key == _A44_KWA_WHEAT_ZERO_KEY" in layer
    assert 'int(rival_wheat_plots) == 0' in layer
    assert "_A44_KWA_WHEAT_ZERO_KEY = '" + KEY + "'" in layer
    assert '_A44_KWA_WHEAT_ZERO_ROUTE = ' + str(ROUTE) in layer
    assert 'fixture_id' not in layer and 'live-' not in layer
    reset_fn = next(n for n in functions if n.name == '_a44_kwa_wheat_zero_reset_state')
    reset_names = {n.id for n in ast.walk(reset_fn) if isinstance(n, ast.Name)}
    assert not ({'_DATA', '_FARMICE_TAPE', '_a44_goose4_commit'} & reset_names)
    return {
        'outer_parent_call_count': 1,
        'parent_call_is_unconditional_direct_statement': True,
        'wrapper_returns_parent_result': True,
        'trigger_literals_verified': True,
        'fixture_identity_references': 0,
        'local_reset_does_not_write_parent_route_state': True,
    }


def check_runner_structure(runner_path: Path, manifest: dict, panel: dict) -> dict:
    source = runner_path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    assert "RUN_ID = 'kwa_wheat_zero_six_game_001'" in source
    assert 'WORKERS = 1' in source
    assert "EXPECTED_FIXTURES = ('live-114227779', 'live-114236633', 'live-114257327')" in source
    assert 'EXPECTED_SEATS = (0, 1)' in source
    assert "RUN_DIR = HERE / 'runs' / 'six_game_run_001'" in source
    assert "ROOT / 'diagnostics' / '.shared_game_run.lock'" in source
    assert "exclusive_run(SHARED_LOCK_PATH)" in source
    assert "path.open('ab')" in source and "path.open('xb')" in source
    assert "'attempts.jsonl', 'outcomes.jsonl'" in source
    assert "if RUN_DIR.exists():" in source and 'resume is forbidden' in source
    assert 'play(fixture, candidate_path, candidate_sha, key[1])' in source
    forbidden_parallel = {'ThreadPoolExecutor', 'ProcessPoolExecutor', 'multiprocessing', 'asyncio'}
    assert not any(isinstance(node, ast.Name) and node.id in forbidden_parallel for node in ast.walk(tree))
    assert manifest['runner']['workers'] == 1
    assert manifest['runner']['resume_allowed'] is False
    assert manifest['runner']['shared_lock_path'] == 'diagnostics/.shared_game_run.lock'
    assert panel['workers'] == 1 and len(panel['jobs']) == 6
    assert [job['fixture_id'] for job in panel['jobs']] == [
        fixture_id for fixture_id in ('live-114227779', 'live-114236633', 'live-114257327')
        for _ in (0, 1)
    ]
    assert [job['seat'] for job in panel['jobs']] == [0, 1, 0, 1, 0, 1]
    assert not (HERE / 'runs' / 'six_game_run_001').exists(), 'runner must not have been invoked'
    gates = manifest['outcome_gates_frozen_before_run']
    assert gates == {
        'all_six_games_done_done_720_clean': True,
        'kwa_both_seats_win_and_positive_margin': True,
        'kwa_both_seats_delta_margin_positive_vs_exact_6d_combined': True,
        'kwa_both_seats_route_113535489_and_647_active_turns': True,
        'four_wheat_positive_controls_do_not_activate': True,
        'four_controls_exact_match_6d_combined_outcomes': [
            'result', 'margin', 'candidate_reward', 'opponent_reward',
            'candidate_status', 'opponent_status', 'frames',
        ],
    }
    return {
        'workers': 1,
        'exclusive_shared_lock': manifest['runner']['shared_lock_path'],
        'no_resume': True,
        'append_only_receipts': ['attempts.jsonl', 'outcomes.jsonl'],
        'jobs': [(job['fixture_id'], job['seat']) for job in panel['jobs']],
        'outcome_gates_frozen': True,
        'runner_invocations': 0,
    }


def check_route_map_scope(module: ModuleType) -> dict:
    before_map = copy.deepcopy(module._DATA['route_map'])
    before_farmice = copy.deepcopy(module._FARMICE_TAPE)
    expected = copy.deepcopy(before_map)
    changed_scope = set()
    for key in list(expected):
        if key.split('|', 1)[0] == 'BRUNCH_SPOT':
            expected[key] = ROUTE
            changed_scope.add(key)
    expected['BRUNCH_SPOT'] = ROUTE
    changed_scope.add('BRUNCH_SPOT')

    module._a44_kwa_wheat_zero_commit()
    assert module._DATA['route_map'] == expected
    assert module._FARMICE_TAPE == before_farmice
    assert all(
        module._DATA['route_map'][key] == value
        for key, value in before_map.items()
        if key.split('|', 1)[0] != 'BRUNCH_SPOT'
    )
    mutated_map = copy.deepcopy(module._DATA['route_map'])

    # The exact integrated parent reset restores its module-load route map and
    # FARMICE tape; the new wrapper's reset only clears its own state.
    module._a44_goose4_reset()
    assert module._DATA['route_map'] == before_map
    assert module._FARMICE_TAPE == before_farmice
    module._A44_KWA_WHEAT_ZERO_ACTIVE = True
    module._A44_KWA_WHEAT_ZERO_STATS['a44_kwa_wheat_zero_active72'] = True
    module._a44_kwa_wheat_zero_reset_state()
    assert module._A44_KWA_WHEAT_ZERO_ACTIVE is False
    assert module._A44_KWA_WHEAT_ZERO_STATS['a44_kwa_wheat_zero_active72'] is False
    assert module._DATA['route_map'] == before_map
    return {
        'brunch_descendant_keys_in_scope': sorted(changed_scope),
        'map_after_commit_sha256': hashlib.sha256(
            json.dumps(mutated_map, sort_keys=True, separators=(',', ':')).encode('utf-8')
        ).hexdigest(),
        'other_shop_keys_unchanged': True,
        'brunch_farmice_unchanged': True,
        'parent_step0_reset_restores_route_map_and_farmice': True,
        'wrapper_step0_reset_scope': 'local active flag and telemetry only',
    }


def main() -> None:
    manifest_path = HERE / 'manifest.json'
    manifest = read_json(manifest_path)
    candidate_path = HERE / 'candidate.py'
    parent_path = root_path(INPUT_PATHS['parent_candidate'])
    layer_path = HERE / 'wheat_zero_layer.py'
    feature_path = root_path(INPUT_PATHS['feature_rows_208'])
    controls_path = root_path(INPUT_PATHS['a44_control_rows_208'])

    assert sha256(parent_path) == PARENT_SHA256
    assert sha256(candidate_path) == manifest['candidate_sha256']
    assert manifest['parent_candidate']['sha256'] == PARENT_SHA256
    assert manifest['trigger']['route_id'] == ROUTE
    assert manifest['trigger']['public_leaf'] == KEY
    assert manifest['bound_input_paths'] == INPUT_PATHS
    for name, relative in INPUT_PATHS.items():
        assert sha256(root_path(relative)) == manifest['bound_inputs'][name], name
    for name, path in {
        'wheat_zero_layer.py': layer_path,
        'candidate.py': candidate_path,
        'build_candidate.py': HERE / 'build_candidate.py',
        'static_preflight.py': HERE / 'static_preflight.py',
        'run_six.py': HERE / 'run_six.py',
        'target_panel.json': HERE / 'target_panel.json',
        'PLAN.md': HERE / 'PLAN.md',
    }.items():
        assert sha256(path) == manifest['package_bindings'][name], name

    parent_manifest = read_json(root_path(INPUT_PATHS['parent_manifest']))
    assert parent_manifest['candidate_sha256'] == PARENT_SHA256
    assert manifest['source_a44_sha256'] == parent_manifest['source_a44_sha256']
    target_panel = read_json(HERE / 'target_panel.json')
    assert target_panel['candidate_sha256'] == manifest['candidate_sha256']
    assert target_panel['parent_6d_candidate_sha256'] == PARENT_SHA256
    assert target_panel['parent_combined_results_sha256'] == manifest['bound_inputs']['parent_combined_results']
    assert target_panel['fixture_ids'] == ['live-114227779', 'live-114236633', 'live-114257327']
    assert len(target_panel['fixtures']) == 3 and len(target_panel['jobs']) == 6
    combined = read_json(root_path(INPUT_PATHS['parent_combined_results']))
    assert combined['complete'] and combined['candidate_sha256'] == PARENT_SHA256
    assert combined['panel_sha256'] == parent_manifest['full_panel_sha256']
    combined_rows = {(row['fixture_id'], int(row['candidate_seat'])): row for row in combined['games']}
    assert len(combined_rows) == 208
    for job in target_panel['jobs']:
        actual = combined_rows[(job['fixture_id'], int(job['seat']))]
        assert {key: actual.get(key) for key in job['baseline_6d']} == job['baseline_6d']
    target_baselines = [combined_rows[('live-114227779', seat)] for seat in (0, 1)]
    control4 = [combined_rows[(fixture, seat)] for fixture in ('live-114236633', 'live-114257327')
                for seat in (0, 1)]
    assert all(row['result'] == 'loss' and row['margin'] == -3858.0 for row in target_baselines)
    assert all(row['result'] == 'win' for row in control4)
    runner_proof = check_runner_structure(HERE / 'run_six.py', manifest, target_panel)
    parent_bytes = parent_path.read_bytes()
    layer_bytes = layer_path.read_bytes()
    separator = b'' if parent_bytes.endswith(b'\n') else b'\n'
    assert candidate_path.read_bytes() == parent_bytes + separator + b'\n' + layer_bytes

    feature_doc = read_json(feature_path)
    control_doc = read_json(controls_path)
    assert feature_doc['complete'] is True
    assert control_doc['complete'] is True
    assert len(feature_doc['rows']) == len(control_doc['rows']) == 208
    controls = {}
    for row in control_doc['rows']:
        key = (row['fixture_id'], int(row['candidate_seat']))
        assert key not in controls
        assert row['candidate_sha256'] == manifest['source_a44_sha256']
        controls[key] = row

    panel_counts = Counter(row['panel'] for row in feature_doc['rows'])
    assert dict(panel_counts) == {'loss30': 60, 'top20': 40, 'public-win': 108}
    assert len({(r['fixture_id'], int(r['seat']), r['panel']) for r in feature_doc['rows']}) == 208

    analyzed = []
    trace_hashes = {}
    for row in feature_doc['rows']:
        trace_path = Path(row['trace_path'])
        assert trace_path.is_file(), str(trace_path)
        actual_trace_sha = sha256(trace_path)
        assert actual_trace_sha == row['trace_sha256'], row['fixture_id']
        trace_hashes[f"{row['fixture_id']}:{row['seat']}"] = actual_trace_sha
        record = frozen_step72(trace_path)
        obs = record['observation']
        assert int(obs['step']) == int(row['step']) == 72
        public_key, counts, wheat_plots = public_leaf(obs)
        shop = obs['town']['unlocked_shops'][0]
        assert shop == row['shop']
        assert public_key == row['rule_key']
        assert counts['MELON'] == row['melon_count']
        assert counts['COW'] == row['cow_count']
        assert counts['SHEEP'] == row['sheep_count']
        assert counts['GOOSE'] == row['goose_count']
        control = controls[(row['fixture_id'], int(row['seat']))]
        if row.get('a44_source_result') is not None:
            assert row['a44_source_result'] == control['result']
        trigger = (
            row['bridge_branch'] == 'source'
            and public_key == KEY
            and wheat_plots == 0
        )
        analyzed.append({
            'fixture_id': row['fixture_id'],
            'seat': int(row['seat']),
            'panel': row['panel'],
            'branch': row['bridge_branch'],
            'public_key': public_key,
            'rival_wheat_plots': wheat_plots,
            'a44_result': control['result'],
            'trigger': trigger,
        })

    trigger_rows = [r for r in analyzed if r['trigger']]
    assert [(r['fixture_id'], r['seat'], r['panel']) for r in trigger_rows] == [
        ('live-114227779', 0, 'loss30'),
        ('live-114227779', 1, 'loss30'),
    ]
    assert all(r['a44_result'] == 'loss' for r in trigger_rows)
    assert not any(r['trigger'] for r in analyzed if r['panel'] == 'top20')
    assert not any(r['trigger'] for r in analyzed if r['panel'] == 'public-win')

    same_leaf = [r for r in analyzed if r['public_key'] == KEY]
    winning_controls = [r for r in same_leaf if r['a44_result'] == 'win']
    assert winning_controls, 'expected same-leaf winning controls in frozen corpus'
    assert not any(r['trigger'] for r in winning_controls)
    control_fixtures = sorted({r['fixture_id'] for r in winning_controls})
    assert {'live-114236633', 'live-114257327'} <= set(control_fixtures)

    call_proof = check_parent_call_and_predicate(candidate_path, layer_path)
    candidate_module = load_candidate_without_call(candidate_path)
    map_proof = check_route_map_scope(candidate_module)

    report = {
        'complete': True,
        'diagnostic_only': True,
        'static_only': True,
        'agent_calls': 0,
        'game_transitions': 0,
        'candidate_sha256': sha256(candidate_path),
        'parent_candidate_sha256': PARENT_SHA256,
        'manifest_sha256': sha256(manifest_path),
        'feature_rows_sha256': sha256(feature_path),
        'a44_controls_sha256': sha256(controls_path),
        'trace_count_and_hashes_verified': len(trace_hashes),
        'panel_counts': dict(panel_counts),
        'trigger_rows': trigger_rows,
        'top20_trigger_count': sum(r['trigger'] for r in analyzed if r['panel'] == 'top20'),
        'public_win_trigger_count': sum(r['trigger'] for r in analyzed if r['panel'] == 'public-win'),
        'same_leaf_winning_control_rows': winning_controls,
        'same_leaf_winning_control_fixtures': control_fixtures,
        'parent_call_proof': call_proof,
        'route_map_reset_scope_proof': map_proof,
        'six_game_runner_static_proof': runner_proof,
        'six_game_baseline_6d_sha256': sha256(root_path(INPUT_PATHS['parent_combined_results'])),
    }
    (HERE / 'preflight.json').write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )
    print(json.dumps({
        'complete': report['complete'],
        'candidate_sha256': report['candidate_sha256'],
        'manifest_sha256': report['manifest_sha256'],
        'trigger_rows': report['trigger_rows'],
        'top20_trigger_count': report['top20_trigger_count'],
        'public_win_trigger_count': report['public_win_trigger_count'],
        'same_leaf_winning_control_fixtures': report['same_leaf_winning_control_fixtures'],
        'agent_calls': 0,
        'game_transitions': 0,
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
