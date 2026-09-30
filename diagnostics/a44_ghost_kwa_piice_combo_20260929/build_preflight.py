"""Freeze and statically audit V4 + the public Pizza/Ice Cream route layer."""
from collections import Counter
from pathlib import Path
import copy
import gzip
import hashlib
import importlib.util
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
COMBO = ROOT / 'diagnostics/a44_ghost_kwa_combo_20260929'
COMBO_CANDIDATE = COMBO / 'candidate_v4.py'
COMBO_RUN = COMBO / 'outcome_run_20260929'
GOAL = ROOT / 'diagnostics/a44_ghost_kwa_goalpanel_20260929'
PIICE = ROOT / 'diagnostics/a44_pizza_icecream_pair_20260929'
BASE6 = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
TARGET = 'live-114238112'
PAIR = 'PIZZA_SHOP|ICE_CREAM_SHOP'
KEY72 = 'PIZZA_SHOP|M8+|C>S|G0'
ROUTE = 113339524
PARENT_SHA = '7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2'
FOCUS = {
    TARGET: PAIR,
    'public-win-114233677': 'PIZZA_SHOP|PIZZA_SHOP',
    'public-win-114251368': 'PIZZA_SHOP|BAKERY',
    'public-win-114288078': 'PIZZA_SHOP|YARN_STORE',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def import_candidate(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observations_through_144(path):
    result = {}
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            step = int(row.get('step', -1))
            if step <= 144:
                result[step] = row['observation']
            if step == 144:
                break
    assert set(result) == set(range(145)), (path, sorted(result))
    return result


def main():
    output_names = ('outcomes.jsonl', 'outcome_receipt.json', 'run_manifest.json', 'run.lock')
    assert not any((HERE / name).exists() for name in output_names), 'outcome output already exists'
    assert sha(COMBO_CANDIDATE) == PARENT_SHA

    piice_manifest = read(PIICE / 'frozen_manifest.json')
    assert piice_manifest['complete'] and piice_manifest['candidate_sha256'] == '4065aba7ca94e83000da473510bb9416ca53571abae0c0f2766cc02fe6da7b17'
    for path_text, digest in piice_manifest['bindings'].items():
        assert Path(path_text).is_file() and sha(path_text) == digest, path_text

    parent_bytes = COMBO_CANDIDATE.read_bytes().rstrip(b'\r\n')
    layer_bytes = (PIICE / 'layer.py').read_bytes()
    candidate_bytes = parent_bytes + b'\n\n' + layer_bytes
    candidate_path = HERE / 'candidate.py'
    (HERE / 'candidate_parent.py').write_bytes(parent_bytes + b'\n')
    (HERE / 'layer.py').write_bytes(layer_bytes)
    candidate_path.write_bytes(candidate_bytes)
    compile(candidate_bytes, str(candidate_path), 'exec')
    candidate_sha = sha(candidate_path)
    assert sha(HERE / 'candidate_parent.py') == PARENT_SHA

    old_panel = read(PIICE / 'panel.json')
    assert len(old_panel['fixtures']) == 4 and len(old_panel['expected_seats']) == 8
    fixtures = old_panel['fixtures']
    expected = old_panel['expected_seats']
    assert [(row['fixture_id'], int(row['seat'])) for row in expected] == [
        (fixture['fixture_id'], seat) for fixture in fixtures for seat in (0, 1)
    ]
    source_features = read(BASE6 / 'feature_rows.json')
    assert len(source_features['rows']) == 208
    pair_rows = []
    for row in source_features['rows']:
        obs = observations_through_144(row['trace_path'])
        shops = obs[144].get('town', {}).get('unlocked_shops', []) or []
        pair = '|'.join(shops[:2])
        pair_rows.append({
            'fixture_id': row['fixture_id'], 'panel': row['panel'], 'seat': int(row['seat']),
            'bridge_branch': row['bridge_branch'], 'step72_rule_key': row['rule_key'],
            'step144_pair': pair, 'trace_path': row['trace_path'],
            'trace_sha256': row['trace_sha256'],
        })
    triggers = [row for row in pair_rows
                if row['bridge_branch'] == 'source' and row['step144_pair'] == PAIR]
    assert len(triggers) == 2
    assert {(row['fixture_id'], row['seat']) for row in triggers} == {(TARGET, 0), (TARGET, 1)}
    assert not any(row['panel'] == 'top20' for row in triggers)
    focus_rows = [row for row in pair_rows if row['fixture_id'] in FOCUS]
    assert len(focus_rows) == 8
    assert all(row['bridge_branch'] == 'source' and row['step72_rule_key'] == KEY72 for row in focus_rows)
    assert all(row['step144_pair'] == FOCUS[row['fixture_id']] for row in focus_rows)
    pair_counts = Counter(row['step144_pair'] for row in pair_rows)
    dump(HERE / 'pair_rows.json', {
        'complete': True, 'source_parent_candidate_sha256': PARENT_SHA,
        'source_6d_feature_rows_sha256': sha(BASE6 / 'feature_rows.json'),
        'step144_pair_census': dict(sorted(pair_counts.items())),
        'trigger_rows': triggers, 'rows': pair_rows,
    })

    panel = {
        'schema': 'a44-v4-piice-eight-seat-panel-v1',
        'candidate': 'Ghost + Kwa V4 plus step-144 public Pizza/Ice Cream continuation',
        'candidate_sha256': candidate_sha,
        'parent_candidate_sha256': PARENT_SHA,
        'fixture_count': len(fixtures), 'game_count': 8,
        'fixtures': fixtures, 'expected_seats': expected,
        'source_panel_sha256': sha(PIICE / 'panel.json'),
    }
    dump(HERE / 'panel.json', panel)

    goal_receipt = read(GOAL / 'outcome_receipt.json')
    assert goal_receipt['candidate_sha256'] == PARENT_SHA and goal_receipt['complete']
    goal_targets = [row for row in goal_receipt['games'] if row['fixture_id'] == TARGET]
    assert len(goal_targets) == 2 and all(row['actual']['result'] == 'loss' for row in goal_targets)
    assert all(row['actual']['margin'] == -8178.0 for row in goal_targets)
    top_receipt = read(COMBO_RUN / 'outcome_receipt.json')
    assert top_receipt['candidate_sha256'] == PARENT_SHA and top_receipt['top20_winning_sweeps'] == 19
    parent_6d_receipt = read(PIICE / 'parent_receipts.json')
    assert len(parent_6d_receipt['baseline_rows']) == 8
    dump(HERE / 'parent_receipts.json', {
        'complete': True, 'direct_parent_to_be_run': PARENT_SHA,
        'v4_target_rows': [row['actual'] for row in goal_targets],
        'prior_top20_receipt_sha256': sha(COMBO_RUN / 'outcome_receipt.json'),
        'prior_top20_both_seat_sweeps': 19,
        '6d_reference': parent_6d_receipt,
        'note': 'All eight V4 outcomes are re-run directly by run.py before candidate comparison.',
    })

    # Policy calls over saved observations only: no engine transitions.
    prefix_results = []
    for source in sorted(focus_rows, key=lambda row: (row['fixture_id'], row['seat'])):
        observations = observations_through_144(source['trace_path'])
        seat = int(source['seat'])
        parent = import_candidate(HERE / 'candidate_parent.py', f'v4_parent_{source["fixture_id"]}_{seat}')
        candidate = import_candidate(candidate_path, f'v4_piice_{source["fixture_id"]}_{seat}')
        for step in range(144):
            parent_action = parent.agent(copy.deepcopy(observations[step]))
            candidate_action = candidate.agent(copy.deepcopy(observations[step]))
            assert candidate_action == parent_action, (source['fixture_id'], seat, step)
        parent_route_before = copy.deepcopy(parent._DATA['route_map'])
        candidate_route_base = copy.deepcopy(candidate._PIICE_BASE_ROUTE_MAP)
        parent_action = parent.agent(copy.deepcopy(observations[144]))
        candidate_action = candidate.agent(copy.deepcopy(observations[144]))
        telemetry = dict(candidate.agent.telemetry)
        assert candidate._BRIDGE_SELECTED == 'source'
        assert telemetry.get('piice_key72') == KEY72 and telemetry.get('piice_key144') == KEY72
        assert telemetry.get('piice_branch144') == 'source'
        assert telemetry.get('piice_pair144') == FOCUS[source['fixture_id']]
        assert telemetry.get('piice_errors') == 0
        changed = {key for key in set(candidate_route_base) | set(candidate._DATA['route_map'])
                   if candidate_route_base.get(key) != candidate._DATA['route_map'].get(key)}
        trigger = source['fixture_id'] == TARGET
        if trigger:
            assert changed == {PAIR}
            assert candidate._DATA['route_map'].get(PAIR) == ROUTE
            assert telemetry.get('piice_active144') is True
            assert telemetry.get('piice_route144') == str(ROUTE)
            assert telemetry.get('piice_active_turns') == 1
            assert candidate_action != parent_action
        else:
            assert not changed and candidate._DATA['route_map'] == parent_route_before
            assert telemetry.get('piice_active144') is False
            assert telemetry.get('piice_route144') == ''
            assert telemetry.get('piice_active_turns') == 0
            assert candidate_action == parent_action
        assert not telemetry.get('a44_ghost_wheat_active72')
        assert not telemetry.get('a44_kwa_wheat_zero_active72')
        assert candidate._FARMICE_TAPE == parent._FARMICE_TAPE
        prefix_results.append({
            'fixture_id': source['fixture_id'], 'seat': seat,
            'trace_sha256': source['trace_sha256'], 'trigger': trigger,
            'parent_equal_actions_steps_0_to_143': True,
            'step144_action_equal': candidate_action == parent_action,
            'changed_route_keys_step144': sorted(changed),
            'candidate_step144_action_sha256': hashlib.sha256(json.dumps(candidate_action, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'parent_step144_action_sha256': hashlib.sha256(json.dumps(parent_action, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'piice_telemetry': telemetry,
            'ghost_and_kwa_inactive': True,
        })
    dump(HERE / 'prefix_probe.json', {
        'complete': True, 'static_agent_calls_only': True, 'engine_transitions': 0,
        'parent_candidate_sha256': PARENT_SHA, 'candidate_sha256': candidate_sha,
        'focus_rows': prefix_results,
    })

    # Bind the input provenance chain, the policy/runtime sources, and every saved trace/tape.
    external = set(piice_manifest['bindings'])
    external.update({
        str(COMBO_CANDIDATE.resolve()),
        str((COMBO_RUN / 'frozen_manifest.json').resolve()),
        str((COMBO / 'panel_v4.json').resolve()),
        str((COMBO_RUN / 'outcome_receipt.json').resolve()),
        str((GOAL / 'outcome_receipt.json').resolve()),
        str((GOAL / 'panel.json').resolve()),
        str((BASE6 / 'feature_rows.json').resolve()),
        str((BASE6 / 'frozen_manifest.json').resolve()),
        str((PIICE / 'frozen_manifest.json').resolve()),
        str((PIICE / 'panel.json').resolve()),
        str((PIICE / 'parent_receipts.json').resolve()),
        str((PIICE / 'pair_rows.json').resolve()),
        str((PIICE / 'prefix_probe.json').resolve()),
        str((PIICE / 'preflight.json').resolve()),
        str((PIICE / 'layer.py').resolve()),
        str((ROOT / 'main.py').resolve()),
        str((ROOT / 'diagnostics/stream_replay_io_20260928/fast_game_cached.py').resolve()),
        str((ROOT / 'diagnostics/stream_replay_io_20260928/cached_input.py').resolve()),
        str((ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py').resolve()),
        str((ROOT / 'diagnostics/physical_route_rollout_20260928/check.py').resolve()),
        str((ROOT / 'diagnostics/local_target_20260928/run_lock.py').resolve()),
    })
    for row in source_features['rows']:
        external.add(str(Path(row['trace_path']).resolve()))
    for fixture in fixtures:
        external.add(str(Path(fixture['source_replay_path']).resolve()))
        external.add(str(Path(fixture['source_action_tape_path']).resolve()))
    bindings = {}
    for path_text in sorted(external):
        path = Path(path_text)
        assert path.is_file(), f'missing frozen source: {path}'
        bindings[path_text] = sha(path)
    for name in ('PLAN.md', 'build_preflight.py', 'run.py', 'candidate_parent.py',
                 'candidate.py', 'layer.py', 'panel.json', 'pair_rows.json',
                 'prefix_probe.json', 'parent_receipts.json'):
        path = HERE / name
        bindings[str(path.resolve())] = sha(path)
    preflight = {
        'schema': 'a44-v4-piice-static-preflight-v1', 'passed': True,
        'static_only': True, 'engine_transitions': 0,
        'policy_action_calls': 8 * 145 * 2,
        'parent_candidate_sha256': PARENT_SHA, 'candidate_sha256': candidate_sha,
        'source_feature_seats': len(pair_rows), 'pair_trigger_seats': len(triggers),
        'target_trigger_seats': 2, 'same_key_control_seats': 6,
        'top20_trigger_seats': sum(row['panel'] == 'top20' and row['step144_pair'] == PAIR for row in pair_rows),
        'focus_prefix_actions_equal_steps_0_to_143': all(row['parent_equal_actions_steps_0_to_143'] for row in prefix_results),
        'target_step144_changed_route_scope': PAIR,
        'control_step144_actions_equal_parent': all(row['step144_action_equal'] for row in prefix_results if not row['trigger']),
        'target_step144_actions_differ_from_parent': all(not row['step144_action_equal'] for row in prefix_results if row['trigger']),
        'ghost_kwa_inactive_on_focus_rows': all(row['ghost_and_kwa_inactive'] for row in prefix_results),
        'v4_target_parent_outcome': [row['actual']['result'] for row in goal_targets],
        'top20_parent_both_seat_sweeps': top_receipt['top20_winning_sweeps'],
        'promotion': False,
    }
    dump(HERE / 'static_preflight.json', preflight)
    bindings[str((HERE / 'static_preflight.json').resolve())] = sha(HERE / 'static_preflight.json')
    manifest = {
        'complete': True, 'diagnostic_only': True, 'fixed_tape_only': True,
        'reactive_validation': False, 'promotion': False,
        'parent_candidate_sha256': PARENT_SHA, 'candidate_sha256': candidate_sha,
        'panel_sha256': sha(HERE / 'panel.json'),
        'static_preflight_sha256': sha(HERE / 'static_preflight.json'),
        'runner_sha256': sha(HERE / 'run.py'),
        'builder_sha256': sha(HERE / 'build_preflight.py'),
        'plan_sha256': sha(HERE / 'PLAN.md'),
        'binding_count': len(bindings), 'bindings': bindings,
        'global_lock_path': 'diagnostics/.shared_game_run.lock',
        'game_count': 8, 'parent_candidate_runs': 8,
        'composed_candidate_runs': 8,
    }
    dump(HERE / 'frozen_manifest.json', manifest)
    print(json.dumps({'candidate_sha256': candidate_sha, 'binding_count': len(bindings),
                      'preflight': preflight, 'manifest_sha256': sha(HERE / 'frozen_manifest.json')}, indent=2))


if __name__ == '__main__':
    main()
