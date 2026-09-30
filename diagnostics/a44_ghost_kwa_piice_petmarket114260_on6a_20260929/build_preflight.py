from __future__ import annotations

import copy
import gzip
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PASTURE = ROOT / 'diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929'
BASELINE_DIR = PASTURE / 'goalpanel_100_retry_20260929'
PARENT_SOURCE = PASTURE / 'candidate.py'
PARENT_PANEL = BASELINE_DIR / 'panel.json'
PARENT_RECEIPT = BASELINE_DIR / 'outcome_receipt.json'
PARENT_MANIFEST = BASELINE_DIR / 'frozen_manifest.json'
FEATURES = PASTURE / 'feature_census.json'
PET_LAYER_SOURCE = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_fourseat_diagnostic_20260929/layer.py'
OLD_PET_RECEIPT = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_fourseat_diagnostic_20260929/outcome_receipt.json'
OLD_PET_PACKAGE = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_fourseat_diagnostic_20260929'
ROUTE_SOURCE = ROOT / 'diagnostics/public_90_research_20260928/candidates/PET_CAFE_113517834.py'
CONTROL_MANIFEST = ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json'
CONTROL_REPLAY_RECEIPT = ROOT / 'diagnostics/new_live_56609430_20260927/raw/episode-114192390-receipt.json'
TARGET = 'live-114260122'
CONTROL = 'public-win-114192390'
LEAF = 'PET_CAFE|M8+|C>S|G0'
ROUTE = '113517834'
PARENT_SHA = '6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc'
CANDIDATE_SHA = 'ebfbe6e91008cf39d1929d52a60e3cb140d2b1cffdd3fac8e06c122eb9876bbe'
ROUTE_SHA = 'a1a8034b190fc1b2a18af82c5ac4a800f31657e7bd52600eb8a542ce35b578e8'
FIELDS = ('result', 'candidate_reward', 'opponent_reward', 'margin',
          'candidate_status', 'opponent_status', 'frames')
PET_TELEMETRY = {
    'a44_pet_market_gate_key72',
    'a44_pet_market_gate_rival_melon72',
    'a44_pet_market_gate_wheat_stock72',
    'a44_pet_market_gate_active72',
    'a44_pet_market_gate_route72',
    'a44_pet_market_gate_turns',
    'a44_pet_market_gate_errors',
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path: Path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n',
                          encoding='utf-8', newline='\n')


def import_file(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_observations(path: Path, last_step=72):
    result = {}
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            step = int(row.get('step', -1))
            if 0 <= step <= last_step and 'observation' in row:
                result[step] = row['observation']
            if step == last_step:
                break
    assert set(result) == set(range(last_step + 1)), (str(path), sorted(result))
    return result


def gate_features(observation, parent):
    rival = observation['farms'][1 - int(observation['player'])]
    melons = sum(isinstance(tile, dict) and tile.get('crop') == 'MELON'
                 for row in rival.get('tiles', []) for tile in row)
    leaf = parent._a44_goose4_key(observation)
    wheat = int(observation['market']['inventory']['WHEAT'])
    return {'leaf72': leaf, 'rival_visible_melon_count72': melons,
            'public_wheat_inventory72': wheat,
            'trigger': leaf == LEAF and melons == 12 and wheat == 9975}


def action_digest(actions):
    return sha_bytes(json.dumps(actions, separators=(',', ':')).encode('utf-8'))


def verify_tape(fixture):
    raw = gzip.decompress(Path(fixture['source_replay_path']).read_bytes())
    replay_sha = sha_bytes(raw)
    assert replay_sha == fixture['source_replay_sha256']
    replay = json.loads(raw)
    assert replay['module_version'] == '1.32.7' and len(replay['steps']) == 720
    opponent_seat = 1 - int(fixture['source_candidate_seat'])
    extracted = [frame[opponent_seat].get('action') or {}
                 for frame in replay['steps'][1:]]
    tape = json.loads(gzip.decompress(
        Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    assert len(extracted) == len(tape) == 719 and extracted == tape
    assert action_digest(tape) == fixture['source_opponent_action_sha256']
    return {'source_replay_decompressed_sha256': replay_sha,
            'source_opponent_seat': opponent_seat,
            'source_action_count': len(tape),
            'source_opponent_action_sha256': action_digest(tape),
            'source_tape_exactly_matches_archived_replay': True,
            'source_tape_file_sha256': sha(Path(fixture['source_action_tape_path']))}


def build_candidate():
    parent_bytes = PARENT_SOURCE.read_bytes()
    layer_bytes = PET_LAYER_SOURCE.read_bytes()
    assert sha_bytes(parent_bytes) == PARENT_SHA
    candidate_bytes = parent_bytes + b'\n\n' + layer_bytes
    assert sha_bytes(candidate_bytes) == CANDIDATE_SHA
    compile(candidate_bytes, str(HERE / 'candidate.py'), 'exec')
    shutil.copyfile(PARENT_SOURCE, HERE / 'candidate_parent.py')
    shutil.copyfile(PET_LAYER_SOURCE, HERE / 'layer.py')
    (HERE / 'candidate.py').write_bytes(candidate_bytes)
    return sha_bytes(candidate_bytes)


def build_static_census(parent, candidate):
    source = read(FEATURES)
    rows = source['rows']
    assert len(rows) == 208
    census = []
    policy_call_count = 0
    focus_action_checks = []
    for feature in rows:
        fixture_id = feature['fixture_id']
        seat = int(feature['seat'])
        trace = Path(feature['trace_path'])
        trace_hash = sha(trace)
        assert trace_hash == feature['trace_sha256']
        observations = read_observations(trace, 72)
        features = gate_features(observations[72], parent)
        active_checks = []
        equal_before72 = []
        first_diff = None
        for step in range(73):
            obs = observations[step]
            parent_action = parent.agent(copy.deepcopy(obs))
            candidate_action = candidate.agent(copy.deepcopy(obs))
            policy_call_count += 2
            if parent_action == candidate_action:
                if step < 72:
                    equal_before72.append(step)
            elif first_diff is None:
                first_diff = step
            if step == 72:
                telemetry = dict(candidate.agent.telemetry)
                active_checks = [
                    telemetry.get('a44_pet_market_gate_key72') == features['leaf72'],
                    telemetry.get('a44_pet_market_gate_rival_melon72') == features['rival_visible_melon_count72'],
                    telemetry.get('a44_pet_market_gate_wheat_stock72') == features['public_wheat_inventory72'],
                    telemetry.get('a44_pet_market_gate_active72') is features['trigger'],
                    telemetry.get('a44_pet_market_gate_route72') == (ROUTE if features['trigger'] else ''),
                    telemetry.get('a44_pet_market_gate_errors') == 0,
                ]
                assert all(active_checks), (fixture_id, seat, telemetry, features)
        assert equal_before72 == list(range(72)), (fixture_id, seat, equal_before72)
        row = {
            'fixture_id': fixture_id, 'panel': feature.get('panel'), 'seat': seat,
            'trace_path': str(trace.resolve()), 'trace_sha256': trace_hash,
            **features, 'candidate_step72_telemetry_matches': all(active_checks),
            'parent_candidate_actions_equal_steps0_71': equal_before72 == list(range(72)),
            'first_action_difference_through_step72': first_diff,
            'source_selector': feature.get('isolated_override_trigger'),
        }
        census.append(row)
        if fixture_id in (TARGET, CONTROL):
            focus_action_checks.append({
                'fixture_id': fixture_id, 'seat': seat,
                'trace_sha256': trace_hash,
                'first_action_difference_through_step72': first_diff,
                'candidate_gate_active': features['trigger'],
            })
    hits = sorted((r['fixture_id'], r['seat']) for r in census if r['trigger'])
    expected = sorted([(TARGET, 0), (TARGET, 1), (CONTROL, 0), (CONTROL, 1)])
    top20_hits = [r for r in census if r['fixture_id'].startswith('top20-') and r['trigger']]
    assert hits == expected
    assert len(top20_hits) == 0
    assert len([r for r in census if r['fixture_id'].startswith('top20-')]) == 40
    assert len(focus_action_checks) == 4
    return {'schema': 'pet-market-6a-208-row-static-census-v1',
            'complete': True, 'candidate_sha256': CANDIDATE_SHA,
            'parent_candidate_sha256': PARENT_SHA,
            'row_count': len(census), 'rows': census,
            'trigger_count': len(hits),
            'trigger_seats': [{'fixture_id': f, 'seat': s} for f, s in hits],
            'top20_rows': 40, 'top20_trigger_count': len(top20_hits),
            'policy_action_calls': policy_call_count,
            'pre_step72_action_mismatches': 0,
            'focus_action_checks': focus_action_checks}


def build_panel(census):
    old_panel = read(PARENT_PANEL)
    old_receipt = read(PARENT_RECEIPT)
    assert old_panel['candidate_sha256'] == PARENT_SHA
    assert old_receipt['candidate_sha256'] == PARENT_SHA
    assert old_receipt['complete'] is True and old_receipt['game_count'] == 100
    assert old_receipt['loss30_winning_sweeps'] == 26
    assert old_receipt['top20_winning_sweeps'] == 19
    outcome_by_key = {(r['fixture_id'], int(r['candidate_seat'])): r
                      for r in old_receipt['games']}
    census_by_key = {(r['fixture_id'], int(r['seat'])): r for r in census['rows']}
    panel_rows = []
    for old in old_panel['games']:
        key = (old['fixture_id'], int(old['candidate_seat']))
        baseline = outcome_by_key[key]
        feature = census_by_key[key]
        assert baseline['candidate_sha256'] == PARENT_SHA
        assert baseline['clean_done_done_720'] and baseline['telemetry_passed']
        expected_trigger = key[0] == TARGET
        assert feature['trigger'] is expected_trigger
        actual = baseline['actual']
        panel_rows.append({
            'fixture_id': key[0], 'candidate_seat': key[1],
            'panel': old['panel'], 'trigger': expected_trigger,
            'expected_gate': {
                'leaf': feature['leaf72'],
                'rival_visible_melon_count': feature['rival_visible_melon_count72'],
                'public_wheat_inventory': feature['public_wheat_inventory72'],
                'active': expected_trigger,
                'route': ROUTE if expected_trigger else '',
                'active_calls': 647 if expected_trigger else 0,
            },
            'fixture': dict(old['fixture']),
            'trace_path': old['trace_path'], 'trace_sha256': old['trace_sha256'],
            'baseline_6a': {field: actual.get(field) for field in FIELDS},
            'baseline_6a_telemetry': actual.get('candidate_telemetry', {}),
        })
    assert len(panel_rows) == 100
    assert sum(row['panel'] == 'loss30' for row in panel_rows) == 60
    assert sum(row['panel'] == 'top20' for row in panel_rows) == 40
    assert sum(row['trigger'] for row in panel_rows) == 2
    assert all(row['baseline_6a']['result'] == 'loss' for row in panel_rows
               if row['fixture_id'] == TARGET)

    control_manifest = read(CONTROL_MANIFEST)
    control_source = next(row for row in control_manifest['fixtures']
                          if row['episode_id'] == 114192390)
    assert control_source['fixture_id'] == CONTROL
    control_tape_proof = verify_tape(control_source)
    control_trace_by_seat = {seat: census_by_key[(CONTROL, seat)] for seat in (0, 1)}
    controls = []
    for seat in (0, 1):
        feature = control_trace_by_seat[seat]
        assert feature['trigger']
        controls.append({
            'fixture_id': CONTROL, 'seat': seat,
            'role': 'control',
            'fixture': {key: control_source[key] for key in (
                'fixture_id', 'seed', 'source_replay_path', 'source_replay_sha256',
                'source_action_tape_path', 'source_opponent_action_sha256')},
            'trace_path': feature['trace_path'],
            'trace_sha256': feature['trace_sha256'],
            'trace_provenance': 'historical 145-step public-win prefix, not a new exact-6a episode',
            'source_tape_proof': control_tape_proof,
            'parent_control_baseline_required': True,
            'candidate_control_must_win': True,
            'control_margin_gate': False,
        })
    return {
        'schema': 'pet-market-6a-100-seat-plus-control-panel-v1',
        'candidate_sha256': CANDIDATE_SHA,
        'parent_candidate_sha256': PARENT_SHA,
        'baseline_panel_sha256': sha(PARENT_PANEL),
        'baseline_receipt_sha256': sha(PARENT_RECEIPT),
        'fixed_tape_only': True, 'reactive_validation': False, 'promotion': False,
        'fixture_count': 50, 'loss30_fixture_count': 30, 'top20_fixture_count': 20,
        'full_panel_candidate_runs': 100,
        'control_fixture_seats': 2,
        'control_parent_runs': 2, 'control_candidate_runs': 2,
        'native_game_runs_planned': 104,
        'baseline_loss30_sweeps': 26, 'baseline_top20_sweeps': 19,
        'loss30_min_winning_sweeps': 27, 'top20_min_winning_sweeps': 18,
        'expected_pet_trigger_seats_in_full100': [
            {'fixture_id': TARGET, 'seat': 0}, {'fixture_id': TARGET, 'seat': 1}],
        'static_208_census_path': str((HERE / 'feature_census.json').resolve()),
        'static_208_census_sha256': None,
        'games': panel_rows,
        'controls': controls,
        'outcome_gate': {
            'clean_done_done_720_and_zero_errors_for_all_104_runs': True,
            'candidate_pet_telemetry_all_102_runs': True,
            'both_114260122_target_seats_win': True,
            'loss30_both_seat_sweeps_at_least_27_of_30': True,
            'top20_both_seat_sweeps_at_least_18_of_20': True,
            'no_per_seat_wdl_regressions_vs_exact_6a_in_100': True,
            'both_114192390_parent_and_candidate_controls_win': True,
            'control_margin_is_report_only': True,
        },
        'output_paths': {
            'outcomes': str((HERE / 'outcomes.jsonl').resolve()),
            'receipt': str((HERE / 'outcome_receipt.json').resolve()),
            'run_manifest': str((HERE / 'run_manifest.json').resolve()),
            'run_lock': str((HERE / 'run.lock').resolve()),
        },
    }


def external_bindings(census):
    paths = [
        PARENT_SOURCE, PARENT_PANEL, PARENT_RECEIPT, PARENT_MANIFEST,
        BASELINE_DIR / 'PLAN.md', BASELINE_DIR / 'run.py',
        BASELINE_DIR / 'build_panel.py', PASTURE / 'static_preflight.json',
        PASTURE / 'frozen_manifest.json', PASTURE / 'freeze_receipt.json',
        PASTURE / 'static_preflight.json', PASTURE / 'feature_census.json',
        PASTURE / 'build_preflight.py', PASTURE / 'layer.py',
        PET_LAYER_SOURCE, OLD_PET_RECEIPT, OLD_PET_PACKAGE / 'candidate.py',
        OLD_PET_PACKAGE / 'candidate_parent.py', OLD_PET_PACKAGE / 'panel.json',
        OLD_PET_PACKAGE / 'frozen_manifest.json', OLD_PET_PACKAGE / 'static_preflight.json',
        ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_fourseat_diagnostic_20260929/run.py',
        ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_fourseat_diagnostic_20260929/PLAN.md',
        ROUTE_SOURCE, FEATURES, CONTROL_MANIFEST,
        ROOT / 'diagnostics/partial_planting_20260928/prepare_public_wins.py',
        ROOT / 'diagnostics/partial_planting_20260928/PUBLIC_WIN_PLAN.md',
        ROOT / 'diagnostics/partial_planting_20260928/public_win_tapes/win-114192390.json.gz',
        CONTROL_REPLAY_RECEIPT,
        ROOT / 'diagnostics/new_live_56609430_20260927/raw/episode-114192390-replay.json.gz',
        ROOT / 'diagnostics/stream_replay_io_20260928/fast_game_cached.py',
        ROOT / 'diagnostics/stream_replay_io_20260928/cached_input.py',
        ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json',
        ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py',
        ROOT / 'diagnostics/physical_route_rollout_20260928/check.py',
        ROOT / 'diagnostics/local_target_20260928/run_lock.py',
    ]
    for row in census:
        paths.append(Path(row['trace_path']))
    for row in (read(PARENT_PANEL)['games']):
        paths.extend((Path(row['fixture']['source_replay_path']),
                      Path(row['fixture']['source_action_tape_path'])))
    for row in read(CONTROL_MANIFEST)['fixtures']:
        if row['episode_id'] == 114192390:
            paths.extend((Path(row['source_replay_path']), Path(row['source_action_tape_path'])))
    return {str(Path(path).resolve()): sha(Path(path))
            for path in sorted(set(paths), key=str)}


def build():
    outputs = ('frozen_manifest.json',)
    assert not any((HERE / name).exists() for name in outputs), 'one-shot plan builder'
    if not all((HERE / name).is_file() for name in
               ('candidate.py', 'candidate_parent.py', 'layer.py')):
        candidate_sha = build_candidate()
    else:
        candidate_sha = sha(HERE / 'candidate.py')
        assert candidate_sha == CANDIDATE_SHA
        assert sha(HERE / 'candidate_parent.py') == PARENT_SHA
        assert (HERE / 'candidate.py').read_bytes() == (
            (HERE / 'candidate_parent.py').read_bytes() + b'\n\n' +
            (HERE / 'layer.py').read_bytes())
    assert candidate_sha == CANDIDATE_SHA
    parent = import_file(HERE / 'candidate_parent.py', 'petmarket_6a_parent')
    candidate = import_file(HERE / 'candidate.py', 'petmarket_6a_candidate')
    route = import_file(ROUTE_SOURCE, 'petmarket_route_113517834')
    assert parent._DATA['routes'][ROUTE] == route._DATA['routes'][ROUTE]
    route_hash = sha_bytes(json.dumps(parent._DATA['routes'][ROUTE], sort_keys=True,
                                      separators=(',', ':'), ensure_ascii=True).encode())
    assert route_hash == ROUTE_SHA
    if (HERE / 'feature_census.json').exists():
        census = read(HERE / 'feature_census.json')
        assert census['candidate_sha256'] == CANDIDATE_SHA
        assert census['parent_candidate_sha256'] == PARENT_SHA
        assert census['row_count'] == len(census['rows']) == 208
        assert census['top20_trigger_count'] == 0
        assert census['pre_step72_action_mismatches'] == 0
        assert len(census['trigger_seats']) == 4
        for row in census['rows']:
            assert sha(Path(row['trace_path'])) == row['trace_sha256']
    else:
        census = build_static_census(parent, candidate)
        write(HERE / 'feature_census.json', census)
    panel = build_panel(census)
    panel['static_208_census_sha256'] = sha(HERE / 'feature_census.json')
    write(HERE / 'panel.json', panel)
    static = {
        'schema': 'pet-market-6a-static-preflight-v1',
        'complete': True, 'static_only': True,
        'engine_transitions': 0, 'native_game_runs': 0,
        'candidate_sha256': candidate_sha,
        'parent_candidate_sha256': PARENT_SHA,
        'composition_exact_parent_plus_bound_layer': (
            (HERE / 'candidate.py').read_bytes() ==
            (HERE / 'candidate_parent.py').read_bytes() + b'\n\n' + (HERE / 'layer.py').read_bytes()),
        'route_source_sha256': sha(ROUTE_SOURCE),
        'route_schedule_canonical_sha256': route_hash,
        'route_schedule_matches_parent': True,
        'census_rows': census['row_count'],
        'trigger_count': census['trigger_count'],
        'trigger_seats': census['trigger_seats'],
        'top20_rows': census['top20_rows'],
        'top20_trigger_count': census['top20_trigger_count'],
        'pre_step72_action_mismatches': census['pre_step72_action_mismatches'],
        'policy_action_calls': census['policy_action_calls'],
        'parent_6a_baseline_panel_sha256': sha(PARENT_PANEL),
        'parent_6a_baseline_receipt_sha256': sha(PARENT_RECEIPT),
        'parent_loss30_sweeps': 26, 'parent_top20_sweeps': 19,
        'target_6a_baseline_rows': [
            {'seat': row['candidate_seat'], **row['baseline_6a']}
            for row in panel['games'] if row['fixture_id'] == TARGET],
        'control_tape_exact_match': all(
            row['source_tape_proof']['source_tape_exactly_matches_archived_replay']
            for row in panel['controls']),
        'static_gates_passed': True,
    }
    write(HERE / 'static_preflight.json', static)
    panel['static_preflight_sha256'] = sha(HERE / 'static_preflight.json')
    write(HERE / 'panel.json', panel)
    internal = ('PLAN.md', 'build_preflight.py', 'run.py', 'candidate.py',
                'candidate_parent.py', 'layer.py', 'feature_census.json',
                'static_preflight.json', 'panel.json')
    external = external_bindings(census['rows'])
    manifest = {
        'schema': 'pet-market-6a-100-seat-plus-control-frozen-plan-v1',
        'complete': True, 'diagnostic_only': True, 'fixed_tape_only': True,
        'reactive_validation': False, 'promotion': False,
        'candidate_sha256': CANDIDATE_SHA, 'parent_candidate_sha256': PARENT_SHA,
        'route_id': int(ROUTE), 'route_schedule_canonical_sha256': ROUTE_SHA,
        'panel_sha256': sha(HERE / 'panel.json'),
        'static_preflight_sha256': sha(HERE / 'static_preflight.json'),
        'baseline_receipt_sha256': sha(PARENT_RECEIPT),
        'internal_files': {name: sha(HERE / name) for name in internal},
        'external_inputs': external,
        'trace_sha256_bindings': {row['trace_path']: row['trace_sha256']
                                  for row in census['rows']},
        'output_paths': panel['output_paths'],
        'native_game_runs_before_freeze': 0,
        'native_game_runs_planned': 104,
        'root_release_required_before_any_run': True,
        'control_traces_are_new_6a_episodes': False,
    }
    write(HERE / 'frozen_manifest.json', manifest)
    return static, panel, manifest


def verify():
    manifest = read(HERE / 'frozen_manifest.json')
    panel = read(HERE / 'panel.json')
    static = read(HERE / 'static_preflight.json')
    assert manifest['complete'] and manifest['diagnostic_only'] and manifest['fixed_tape_only']
    assert not manifest['reactive_validation'] and not manifest['promotion']
    assert sha(HERE / 'candidate.py') == manifest['candidate_sha256'] == CANDIDATE_SHA
    assert sha(HERE / 'candidate_parent.py') == manifest['parent_candidate_sha256'] == PARENT_SHA
    assert (HERE / 'candidate.py').read_bytes() == (
        (HERE / 'candidate_parent.py').read_bytes() + b'\n\n' + (HERE / 'layer.py').read_bytes())
    assert sha(HERE / 'panel.json') == manifest['panel_sha256']
    assert sha(HERE / 'static_preflight.json') == manifest['static_preflight_sha256']
    assert sha(HERE / 'feature_census.json') == panel['static_208_census_sha256']
    for name, digest in manifest['internal_files'].items():
        assert sha(HERE / name) == digest, name
    for path_text, digest in manifest['external_inputs'].items():
        assert sha(Path(path_text)) == digest, path_text
    for path_text, digest in manifest['trace_sha256_bindings'].items():
        assert sha(Path(path_text)) == digest, path_text
    assert static['static_gates_passed'] and static['engine_transitions'] == 0
    assert static['native_game_runs'] == 0 and static['top20_trigger_count'] == 0
    assert static['census_rows'] == 208 and static['trigger_count'] == 4
    assert static['pre_step72_action_mismatches'] == 0
    assert panel['native_game_runs_planned'] == 104
    assert len(panel['games']) == 100 and len(panel['controls']) == 2
    assert panel['outcome_gate']['loss30_both_seat_sweeps_at_least_27_of_30']
    assert panel['outcome_gate']['top20_both_seat_sweeps_at_least_18_of_20']
    assert manifest['root_release_required_before_any_run'] is True
    output_paths = [Path(path) for path in manifest['output_paths'].values()]
    assert not any(path.exists() for path in output_paths), 'one-shot outputs already exist'
    return manifest, panel, static


if __name__ == '__main__':
    if '--verify' in sys.argv:
        manifest, panel, static = verify()
        print(json.dumps({'verified': True, 'frozen': True,
                          'candidate_sha256': manifest['candidate_sha256'],
                          'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                          'census_rows': static['census_rows'],
                          'trigger_count': static['trigger_count'],
                          'top20_trigger_count': static['top20_trigger_count'],
                          'pre_step72_action_mismatches': static['pre_step72_action_mismatches'],
                          'planned_native_game_runs': manifest['native_game_runs_planned'],
                          'native_game_runs_now': 0, 'engine_transitions_now': 0}, indent=2))
    else:
        static, panel, manifest = build()
        print(json.dumps({'complete': True, 'candidate_sha256': CANDIDATE_SHA,
                          'parent_candidate_sha256': PARENT_SHA,
                          'panel_sha256': manifest['panel_sha256'],
                          'static_preflight_sha256': manifest['static_preflight_sha256'],
                          'trigger_count': static['trigger_count'],
                          'top20_trigger_count': static['top20_trigger_count'],
                          'planned_native_game_runs': manifest['native_game_runs_planned'],
                          'native_game_runs_now': 0}, indent=2))
