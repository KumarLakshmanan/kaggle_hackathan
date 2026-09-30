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
SOURCE_STAGE = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_static_20260929'
SOURCE_PANEL = ROOT / 'diagnostics/a44_ghost_kwa_piice_goalpanel_20260929'
PARENT_SOURCE = ROOT / 'diagnostics/a44_ghost_kwa_piice_combo_20260929/candidate.py'
FEATURES = ROOT / 'diagnostics/pasture_guard_source_leaf_20260928/feature_rows.json'
TARGET = 'live-114260122'
CONTROL = 'public-win-114192390'
LEAF = 'PET_CAFE|M8+|C>S|G0'
ROUTE = '113517834'
PARENT_SHA = '8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62'
CANDIDATE_SHA = '8d97d7297f2f7c6a550b3397d98825e2a96da76c5ea060cbdf9a94defda5efb9'
ROUTE_SHA = 'a1a8034b190fc1b2a18af82c5ac4a800f31657e7bd52600eb8a542ce35b578e8'
FIELDS = ('result', 'candidate_reward', 'opponent_reward', 'margin',
          'candidate_status', 'opponent_status', 'frames')


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path: Path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8', newline='\n')


def import_file(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def action_digest(actions):
    return sha_bytes(json.dumps(actions, separators=(',', ':')).encode('utf-8'))


def check_tape(fixture):
    replay_path = Path(fixture['source_replay_path'])
    tape_path = Path(fixture['source_action_tape_path'])
    raw = gzip.decompress(replay_path.read_bytes())
    assert sha_bytes(raw) == fixture['source_replay_sha256']
    replay = json.loads(raw)
    assert replay['module_version'] == '1.32.7' and len(replay['steps']) == 720
    original_candidate_seat = int(fixture['source_candidate_seat'])
    opponent_seat = 1 - original_candidate_seat
    actions = [frame[opponent_seat].get('action') or {} for frame in replay['steps'][1:]]
    payload = json.loads(gzip.decompress(tape_path.read_bytes()))
    assert len(actions) == len(payload['actions']) == 719
    assert actions == payload['actions']
    assert action_digest(actions) == fixture['source_opponent_action_sha256']
    if 'source_candidate_reward' in fixture:
        candidate_reward = float(fixture['source_candidate_reward'])
        opponent_reward = float(fixture['source_opponent_reward'])
    else:
        source_row = next(row for row in fixture['source_public_game_both_seat_outcomes']
                          if int(row['seat']) == original_candidate_seat)
        candidate_reward = float(source_row['candidate_reward'])
        opponent_reward = float(source_row['opponent_reward'])
    assert float(replay['rewards'][original_candidate_seat]) == candidate_reward
    assert float(replay['rewards'][opponent_seat]) == opponent_reward
    return {
        'source_replay_sha256': fixture['source_replay_sha256'],
        'decompressed_source_replay_sha256': sha_bytes(raw),
        'source_action_tape_sha256': sha(tape_path),
        'source_opponent_action_sha256': action_digest(actions),
        'recorded_opponent_seat': opponent_seat,
        'recorded_opponent_actions': len(actions),
        'exact_replay_action_match': True,
        'source_module_version': replay['module_version'],
        'source_frames': len(replay['steps']),
    }


def read_trace(path: Path):
    observations = {}
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if isinstance(row.get('step'), int) and 'observation' in row:
                observations[row['step']] = row['observation']
    return observations


def public_gate(observation, parent):
    rival = observation['farms'][1 - int(observation['player'])]
    melons = sum(isinstance(tile, dict) and tile.get('crop') == 'MELON'
                 for row in rival.get('tiles', []) for tile in row)
    leaf = parent._a44_goose4_key(observation)
    wheat = int(observation['market']['inventory']['WHEAT'])
    return {'leaf': leaf, 'rival_visible_melon_count': melons,
            'public_wheat_inventory': wheat,
            'trigger': leaf == LEAF and melons == 12 and wheat == 9975}


def build_panel_and_static():
    parent_bytes = PARENT_SOURCE.read_bytes()
    assert sha_bytes(parent_bytes) == PARENT_SHA
    shutil.copyfile(PARENT_SOURCE, HERE / 'candidate_parent.py')
    shutil.copyfile(SOURCE_STAGE / 'candidate.py', HERE / 'candidate.py')
    shutil.copyfile(SOURCE_STAGE / 'layer.py', HERE / 'layer.py')
    assert sha(HERE / 'candidate.py') == CANDIDATE_SHA
    assert sha(HERE / 'candidate_parent.py') == PARENT_SHA
    assert (HERE / 'candidate.py').read_bytes() == (
        parent_bytes + b'\n\n' + (HERE / 'layer.py').read_bytes())

    parent = import_file(HERE / 'candidate_parent.py', 'pet_market_diagnostic_parent')
    candidate = import_file(HERE / 'candidate.py', 'pet_market_diagnostic_candidate')
    route_source_path = ROOT / 'diagnostics/public_90_research_20260928/candidates/PET_CAFE_113517834.py'
    route_source = import_file(route_source_path, 'pet_market_diagnostic_route_source')
    assert parent._DATA['routes'][ROUTE] == route_source._DATA['routes'][ROUTE]
    canonical_route = json.dumps(parent._DATA['routes'][ROUTE], sort_keys=True,
                                 separators=(',', ':'), ensure_ascii=True).encode()
    assert sha_bytes(canonical_route) == ROUTE_SHA

    source_static = read(SOURCE_STAGE / 'static_preflight.json')
    source_stage_manifest = read(SOURCE_STAGE / 'stage_manifest.json')
    assert source_static['candidate_sha256'] == CANDIDATE_SHA
    assert source_static['parent_candidate_sha256'] == PARENT_SHA
    assert source_static['engine_transitions'] == 0 and source_static['native_games'] == 0
    census = source_static['census']
    assert len(census) == 208
    observed = []
    for row in census:
        trace_path = Path(row['trace_path'])
        assert sha(trace_path) == row['trace_sha256']
        trace = read_trace(trace_path)
        assert 72 in trace
        gate = public_gate(trace[72], parent)
        assert gate['leaf'] == row['leaf72']
        assert gate['rival_visible_melon_count'] == row['rival_visible_melon_count72']
        assert gate['public_wheat_inventory'] == row['public_wheat_inventory72']
        assert gate['trigger'] is row['trigger']
        observed.append((row['fixture_id'], int(row['seat']), gate['trigger']))
    hits = sorted((fixture, seat) for fixture, seat, hit in observed if hit)
    expected_hits = sorted([(TARGET, 0), (TARGET, 1), (CONTROL, 0), (CONTROL, 1)])
    top20_hits = [(fixture, seat) for fixture, seat in hits if fixture.startswith('top20-')]
    assert hits == expected_hits
    assert not top20_hits

    panel = read(SOURCE_PANEL / 'panel.json')
    outcomes = {}
    with (SOURCE_PANEL / 'outcomes.jsonl').open('r', encoding='utf-8-sig') as stream:
        for line in stream:
            row = json.loads(line)
            if row.get('fixture_id') == TARGET:
                outcomes[int(row['candidate_seat'])] = row
    assert set(outcomes) == {0, 1}
    for seat, row in outcomes.items():
        assert row['candidate_sha256'] == PARENT_SHA
        assert row['clean_done_done_720'] and row['telemetry_passed']
        telemetry = row['actual']['candidate_telemetry']
        assert telemetry['a44_goose4_key72'] == LEAF
        assert telemetry['a44_ghost_wheat_stock72'] == 9975
        assert row['actual']['result'] == 'loss'
        assert row['actual']['candidate_reward'] == 90989.0
        assert row['actual']['opponent_reward'] == 123017.0
        assert row['actual']['margin'] == -32028.0
        assert row['actual']['candidate_status'] == row['actual']['opponent_status'] == 'DONE'
        assert row['actual']['frames'] == 720

    features = read(FEATURES)
    feature_by_key = {(r['provenance']['fixture_id'],
                       int(r['provenance']['candidate_seat'])): r
                      for r in features['rows']}
    pool = read(ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full_pool.json')
    target_fixture = next(f for f in pool['fixtures'] if f['fixture_id'] == TARGET)
    public_manifest = read(ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json')
    control_fixture = next(f for f in public_manifest['fixtures'] if f['episode_id'] == 114192390)
    assert control_fixture['fixture_id'] == CONTROL

    jobs = []
    for fixture_id, fixture_source, role in (
        (TARGET, target_fixture, 'target'), (CONTROL, control_fixture, 'control')):
        tape_proof = check_tape(fixture_source)
        for seat in (0, 1):
            feature = feature_by_key[(fixture_id, seat)]
            provenance = feature['provenance']
            trace = Path(provenance['trace_path'])
            assert sha(trace) == provenance['trace_sha256']
            job = {
                'fixture_id': fixture_id,
                'seat': seat,
                'role': role,
                'seed': int(fixture_source['seed']),
                'fixture': {key: fixture_source[key] for key in (
                    'fixture_id', 'seed', 'source_replay_path',
                    'source_replay_sha256', 'source_action_tape_path',
                    'source_opponent_action_sha256')},
                'trace_path': str(trace.resolve()),
                'trace_sha256': provenance['trace_sha256'],
                'trace_provenance': 'historical research trace; not a fresh exact-8f episode',
                'source_tape_proof': tape_proof,
            }
            if role == 'target':
                actual = outcomes[seat]['actual']
                job['parent_baseline'] = {field: actual[field] for field in FIELDS}
                job['parent_panel_sha256'] = sha(SOURCE_PANEL / 'outcomes.jsonl')
                job['source_target_trace_kind'] = 'full 719-observation historical research trace'
            else:
                job['historical_source_episode_outcome'] = {
                    'candidate_seat': control_fixture['source_candidate_seat'],
                    'candidate_reward': control_fixture['source_candidate_reward'],
                    'opponent_reward': control_fixture['source_opponent_reward'],
                    'historical_result': 'win',
                    'interpretation': 'metadata only; not the direct-parent 8f control baseline',
                }
                job['source_target_trace_kind'] = 'historical 145-observation public-win prefix'
            jobs.append(job)

    result_panel = {
        'schema': 'a44-v5-pet-market-114260-four-seat-diagnostic-panel-v1',
        'candidate_sha256': CANDIDATE_SHA,
        'parent_candidate_sha256': PARENT_SHA,
        'diagnostic_only': True,
        'fixed_tape_only': True,
        'reactive_validation': False,
        'promotion': False,
        'seat_fixture_count': len(jobs),
        'native_game_runs': 8,
        'gate': {'leaf': LEAF, 'rival_visible_melon_count': 12,
                 'public_wheat_inventory': 9975, 'route': ROUTE},
        'trigger_census': {
            'source_static_preflight_sha256': sha(SOURCE_STAGE / 'static_preflight.json'),
            'rows': len(census), 'hit_seats': [
                {'fixture_id': fixture, 'seat': seat} for fixture, seat in hits],
            'top20_rows': sum(row['fixture_id'].startswith('top20-') for row in census),
            'top20_trigger_count': len(top20_hits),
        },
        'jobs': jobs,
        'pass_criteria': {
            'all_eight_runs_clean_done_done_720': True,
            'all_four_candidate_gate_telemetry_matches_and_is_error_free': True,
            'parent_target_runs_exactly_match_bound_8f_panel': True,
            'both_candidate_target_seats_win': True,
            'both_candidate_control_seats_exactly_match_paired_8f_parent': True,
        },
    }
    write(HERE / 'panel.json', result_panel)

    static = {
        'schema': 'a44-v5-pet-market-114260-four-seat-static-preflight-v1',
        'complete': True,
        'static_only': True,
        'engine_transitions': 0,
        'native_game_runs': 0,
        'candidate_sha256': sha(HERE / 'candidate.py'),
        'parent_candidate_sha256': sha(HERE / 'candidate_parent.py'),
        'route_source_sha256': sha(route_source_path),
        'route_schedule_canonical_sha256': ROUTE_SHA,
        'route_schedule_equal_to_parent': True,
        'trace_census_rows': len(census),
        'trigger_count': len(hits),
        'trigger_seats': [{'fixture_id': fixture, 'seat': seat}
                          for fixture, seat in hits],
        'top20_seats_checked': result_panel['trigger_census']['top20_rows'],
        'top20_trigger_count': len(top20_hits),
        'target_8f_panel_sha256': sha(SOURCE_PANEL / 'outcomes.jsonl'),
        'target_8f_direct_parent_rows': [
            {'seat': seat, **{field: outcomes[seat]['actual'][field] for field in FIELDS},
             'leaf72': outcomes[seat]['actual']['candidate_telemetry']['a44_goose4_key72'],
             'public_wheat72': outcomes[seat]['actual']['candidate_telemetry']['a44_ghost_wheat_stock72']}
            for seat in (0, 1)],
        'fixed_tapes_match_archived_replay_actions': True,
        'target_trace_provenance': 'historical research traces; exact 8f target baseline comes from the bound 8f panel',
        'control_trace_provenance': 'historical 145-step prefixes; control tape is separately verified from the archived public replay',
        'control_is_new_8f_episode': False,
        'gates_passed': True,
    }
    write(HERE / 'static_preflight.json', static)
    return result_panel, static, source_stage_manifest, control_fixture, target_fixture


def input_bindings(census, target_fixture, control_fixture):
    paths = [
        SOURCE_STAGE / 'candidate.py', SOURCE_STAGE / 'candidate_parent.py',
        SOURCE_STAGE / 'layer.py', SOURCE_STAGE / 'build_preflight.py',
        SOURCE_STAGE / 'static_preflight.json', SOURCE_STAGE / 'stage_manifest.json',
        SOURCE_STAGE / 'PLAN.md', SOURCE_PANEL / 'candidate.py', SOURCE_PANEL / 'panel.json',
        SOURCE_PANEL / 'outcomes.jsonl', SOURCE_PANEL / 'frozen_manifest.json',
        SOURCE_PANEL / 'outcome_receipt.json', SOURCE_PANEL / 'static_preflight.json',
        SOURCE_PANEL / 'run.py', SOURCE_PANEL / 'build_panel.py', SOURCE_PANEL / 'PLAN.md',
        ROOT / 'diagnostics/a44_ghost_kwa_piice_combo_20260929/candidate.py',
        ROOT / 'diagnostics/a44_ghost_kwa_piice_combo_20260929/frozen_manifest.json',
        ROOT / 'diagnostics/a44_ghost_kwa_piice_combo_20260929/outcome_receipt.json',
        ROOT / 'diagnostics/public_90_research_20260928/candidates/PET_CAFE_113517834.py',
        ROOT / 'diagnostics/pasture_guard_source_leaf_20260928/feature_rows.json',
        ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full_pool.json',
        ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json',
        ROOT / 'diagnostics/partial_planting_20260928/prepare_public_wins.py',
        ROOT / 'diagnostics/partial_planting_20260928/PUBLIC_WIN_PLAN.md',
        ROOT / 'diagnostics/partial_planting_20260928/public_win_tapes/win-114192390.json.gz',
        ROOT / 'diagnostics/new_live_56609430_20260927/raw/episode-114192390-replay.json.gz',
        ROOT / 'diagnostics/new_live_56609430_20260927/raw/episode-114192390-receipt.json',
        ROOT / 'diagnostics/loss_class_20260927/routes/episode-114260122-seat1.json.gz',
        ROOT / 'diagnostics/new_live_56609430_20260927/raw/episode-114260122-replay.json.gz',
        ROOT / 'diagnostics/stream_replay_io_20260928/fast_game_cached.py',
        ROOT / 'diagnostics/stream_replay_io_20260928/cached_input.py',
        ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json',
        ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py',
        ROOT / 'diagnostics/physical_route_rollout_20260928/check.py',
        ROOT / 'diagnostics/local_target_20260928/run_lock.py',
        PARENT_SOURCE,
    ]
    for row in census:
        paths.append(Path(row['trace_path']))
    for fixture in (target_fixture, control_fixture):
        paths.extend((Path(fixture['source_replay_path']),
                      Path(fixture['source_action_tape_path'])))
    return {str(Path(path).resolve()): sha(Path(path))
            for path in sorted(set(paths), key=str)}


def build():
    outputs = ('panel.json', 'static_preflight.json', 'frozen_manifest.json',
               'diagnostic_status.json')
    assert not any((HERE / name).exists() for name in outputs), 'diagnostic plan is one-shot'
    panel, static, source_manifest, control_fixture, target_fixture = build_panel_and_static()
    source_static = read(SOURCE_STAGE / 'static_preflight.json')
    external = input_bindings(source_static['census'], target_fixture, control_fixture)
    internal_names = ('PLAN.md', 'candidate.py', 'candidate_parent.py', 'layer.py',
                      'panel.json', 'static_preflight.json', 'build_preflight.py', 'run.py')
    manifest = {
        'schema': 'a44-v5-pet-market-114260-four-seat-diagnostic-freeze-v1',
        'complete': True,
        'diagnostic_only': True,
        'fixed_tape_only': True,
        'reactive_validation': False,
        'promotion': False,
        'candidate_sha256': CANDIDATE_SHA,
        'parent_candidate_sha256': PARENT_SHA,
        'route_id': int(ROUTE),
        'route_schedule_canonical_sha256': ROUTE_SHA,
        'panel_sha256': sha(HERE / 'panel.json'),
        'static_preflight_sha256': sha(HERE / 'static_preflight.json'),
        'internal_files': {name: sha(HERE / name) for name in internal_names},
        'external_inputs': external,
        'trace_sha256_bindings': {row['trace_path']: row['trace_sha256']
                                  for row in source_static['census']},
        'top20_trigger_count': 0,
        'native_game_runs_before_freeze': 0,
        'native_game_runs_planned': 8,
        'control_trace_is_new_8f_episode': False,
    }
    write(HERE / 'frozen_manifest.json', manifest)
    status = {
        'complete': True,
        'frozen_diagnostic_plan': True,
        'diagnostic_only': True,
        'static_preflight_passed': True,
        'engine_transitions': 0,
        'native_game_runs': 0,
        'candidate_sha256': CANDIDATE_SHA,
        'parent_candidate_sha256': PARENT_SHA,
        'panel_sha256': manifest['panel_sha256'],
        'frozen_manifest_sha256': sha(HERE / 'frozen_manifest.json'),
        'historical_control_provenance_caveat': True,
    }
    write(HERE / 'diagnostic_status.json', status)
    return status


def verify_manifest(check_outputs=False):
    manifest = read(HERE / 'frozen_manifest.json')
    panel = read(HERE / 'panel.json')
    static = read(HERE / 'static_preflight.json')
    assert manifest['complete'] and manifest['diagnostic_only'] and manifest['fixed_tape_only']
    assert not manifest['reactive_validation'] and not manifest['promotion']
    assert sha(HERE / 'candidate.py') == manifest['candidate_sha256'] == CANDIDATE_SHA
    assert sha(HERE / 'candidate_parent.py') == manifest['parent_candidate_sha256'] == PARENT_SHA
    assert (HERE / 'candidate.py').read_bytes() == (
        (HERE / 'candidate_parent.py').read_bytes() + b'\n\n' +
        (HERE / 'layer.py').read_bytes())
    parent = import_file(HERE / 'candidate_parent.py', 'pet_market_frozen_parent')
    route_source = import_file(
        ROOT / 'diagnostics/public_90_research_20260928/candidates/PET_CAFE_113517834.py',
        'pet_market_frozen_route_source')
    assert parent._DATA['routes'][ROUTE] == route_source._DATA['routes'][ROUTE]
    route_bytes = json.dumps(parent._DATA['routes'][ROUTE], sort_keys=True,
                             separators=(',', ':'), ensure_ascii=True).encode()
    assert sha_bytes(route_bytes) == ROUTE_SHA
    assert sha(HERE / 'panel.json') == manifest['panel_sha256']
    assert sha(HERE / 'static_preflight.json') == manifest['static_preflight_sha256']
    for name, expected in manifest['internal_files'].items():
        assert sha(HERE / name) == expected, name
    for path_text, expected in manifest['external_inputs'].items():
        assert sha(Path(path_text)) == expected, path_text
    for path_text, expected in manifest['trace_sha256_bindings'].items():
        assert sha(Path(path_text)) == expected, path_text
    assert static['gates_passed'] and static['engine_transitions'] == 0
    assert static['native_game_runs'] == 0 and static['top20_trigger_count'] == 0
    assert static['trace_census_rows'] == 208 and static['trigger_count'] == 4
    assert manifest['top20_trigger_count'] == 0
    assert panel['native_game_runs'] == 8 and len(panel['jobs']) == 4
    assert [job['role'] for job in panel['jobs']].count('target') == 2
    assert [job['role'] for job in panel['jobs']].count('control') == 2
    if check_outputs:
        outputs = (HERE / 'outcomes.jsonl', HERE / 'outcome_receipt.json',
                   HERE / 'run_manifest.json', HERE / 'run.lock')
        assert not any(path.exists() for path in outputs), 'diagnostic is one-shot; output exists'
    return manifest, panel, static


if __name__ == '__main__':
    if '--verify' in sys.argv:
        manifest, panel, static = verify_manifest(check_outputs=True)
        print(json.dumps({'verified': True, 'frozen': True,
                          'diagnostic_only': True,
                          'candidate_sha256': manifest['candidate_sha256'],
                          'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                          'trigger_seats': static['trigger_count'],
                          'top20_trigger_count': static['top20_trigger_count'],
                          'planned_native_game_runs': manifest['native_game_runs_planned'],
                          'engine_transitions_now': 0,
                          'native_game_runs_now': 0}, indent=2))
    else:
        print(json.dumps(build(), indent=2))
