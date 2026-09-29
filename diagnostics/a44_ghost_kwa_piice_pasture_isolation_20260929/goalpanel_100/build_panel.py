from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
PARENT_PACKAGE = ROOT / 'diagnostics/a44_ghost_kwa_piice_goalpanel_20260929'
PARENT_PANEL = PARENT_PACKAGE / 'panel.json'
PARENT_RECEIPT = PARENT_PACKAGE / 'outcome_receipt.json'
PARENT_MANIFEST = PARENT_PACKAGE / 'frozen_manifest.json'
PARENT_HASH = '8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62'
CANDIDATE_HASH = '6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc'
LOSS_GOAL = 27
TOP20_GOAL = 18
FIELDS = ('result', 'candidate_reward', 'opponent_reward', 'margin',
          'candidate_status', 'opponent_status', 'frames')


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_once(path: Path, data):
    with Path(path).open('xb') as stream:
        stream.write((json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def engine_path() -> Path:
    spec = importlib.util.find_spec('kaggle_environments')
    assert spec and spec.origin, 'kaggle-environments is unavailable'
    assert importlib.metadata.version('kaggle-environments') == '1.32.7'
    path = Path(spec.origin).parent / 'envs' / 'kaggriculture' / 'kaggriculture.py'
    assert path.is_file(), path
    return path.resolve()


def main():
    outputs = ('panel.json', 'frozen_manifest.json', 'outcomes.jsonl',
               'outcome_receipt.json', 'run_manifest.json', 'run.lock')
    assert not any((HERE / name).exists() for name in outputs), 'runner is one-shot'
    parent_panel = read(PARENT_PANEL)
    parent_receipt = read(PARENT_RECEIPT)
    parent_manifest = read(PARENT_MANIFEST)
    static = read(STUDY / 'static_preflight.json')
    freeze = read(STUDY / 'freeze_receipt.json')
    static_manifest = read(STUDY / 'frozen_manifest.json')
    feature_census = read(STUDY / 'feature_census.json')

    assert parent_receipt.get('complete') is True
    assert parent_receipt.get('candidate_sha256') == PARENT_HASH
    assert parent_receipt.get('game_count') == 100
    assert parent_receipt.get('loss30_winning_sweeps') == 25
    assert parent_receipt.get('top20_winning_sweeps') == 19
    assert parent_receipt.get('panel_sha256') == sha(PARENT_PANEL)
    assert parent_manifest.get('candidate_sha256') == PARENT_HASH
    assert parent_manifest.get('panel_sha256') == sha(PARENT_PANEL)
    assert parent_manifest.get('complete') is True
    for path_text, expected in parent_manifest.get('bindings', {}).items():
        path = Path(path_text)
        assert path.is_file() and sha(path) == expected, f'V5 parent binding changed: {path}'

    assert static.get('all_static_gates_passed') is True
    assert static.get('candidate_sha256') == CANDIDATE_HASH
    assert static.get('parent_candidate_sha256') == PARENT_HASH
    assert static.get('selector_target_seats') == [
        {'fixture_id': 'live-114274897', 'seat': 0},
        {'fixture_id': 'live-114274897', 'seat': 1},
    ]
    assert static.get('selector_trigger_count') == 2
    assert static.get('top20_trigger_count') == static.get('public_win_trigger_count') == 0
    assert sha(STUDY / 'candidate.py') == CANDIDATE_HASH
    assert sha(STUDY / 'candidate_parent.py') == PARENT_HASH
    assert freeze.get('complete') and freeze.get('manifest_sha256') == sha(STUDY / 'frozen_manifest.json')
    assert len(feature_census.get('rows', [])) == 208

    for path_text, expected in static_manifest.get('files', {}).items():
        path = Path(path_text) if Path(path_text).is_absolute() else STUDY / path_text
        assert sha(path) == expected, f'static package input changed: {path}'
    for collection in ('external_inputs', 'trace_sha256_bindings'):
        for path_text, expected in static_manifest.get(collection, {}).items():
            path = Path(path_text)
            assert path.is_file() and sha(path) == expected, f'{collection} input changed: {path}'

    parent_rows = {(row['fixture_id'], int(row['candidate_seat'])): row
                   for row in parent_receipt['games']}
    census_rows = {(row['fixture_id'], int(row['seat'])): row
                   for row in feature_census['rows']}
    panel_rows = []
    for old in parent_panel['games']:
        key = (old['fixture_id'], int(old['candidate_seat']))
        baseline_row = parent_rows[key]
        baseline_actual = baseline_row['actual']
        feature = census_rows[key]
        is_trigger = bool(feature['isolated_override_trigger'])
        expected_trigger = key[0] == 'live-114274897'
        assert is_trigger is expected_trigger
        expected_branch = feature['isolated_branch']
        expected_leaf_key = feature['obs72_public_leaf_key'] if expected_branch == 'source' else ''
        assert baseline_row['candidate_sha256'] == PARENT_HASH
        assert baseline_actual['candidate_sha256'] == PARENT_HASH
        fixture = dict(old['source_fixture'])
        assert Path(fixture['source_replay_path']).is_file()
        assert Path(fixture['source_action_tape_path']).is_file()
        panel_rows.append({
            'fixture_id': key[0],
            'candidate_seat': key[1],
            'panel': old['panel'],
            'trigger': is_trigger,
            'expected': {
                'rival_hands': int(feature['obs1_public_rival_hands']),
                'rival_pastures': int(feature['obs1_public_rival_pasture_count']),
                'branch': expected_branch,
                'leaf_key': expected_leaf_key,
                'leaf_route': '113332529' if is_trigger else '',
                'leaf_turns': 647 if is_trigger else 0,
            },
            'fixture': fixture,
            'trace_path': feature['trace_path'],
            'trace_sha256': feature['trace_sha256'],
            'baseline_v5': {field: baseline_actual.get(field) for field in FIELDS},
            'baseline_v5_telemetry': baseline_actual.get('candidate_telemetry', {}),
        })
    assert len(panel_rows) == 100
    assert sum(row['panel'] == 'loss30' for row in panel_rows) == 60
    assert sum(row['panel'] == 'top20' for row in panel_rows) == 40
    assert sum(row['trigger'] for row in panel_rows) == 2

    panel = {
        'schema': 'a44-v5-isolated-pasture-100-seat-goal-panel-v1',
        'candidate_sha256': CANDIDATE_HASH,
        'parent_candidate_sha256': PARENT_HASH,
        'parent_panel_sha256': sha(PARENT_PANEL),
        'parent_receipt_sha256': sha(PARENT_RECEIPT),
        'fixed_tape_only': True,
        'reactive_validation': False,
        'promotion': False,
        'fixture_count': 50,
        'loss30_fixture_count': 30,
        'top20_fixture_count': 20,
        'game_count': 100,
        'expected_trigger_seats': 2,
        'loss30_min_winning_sweeps': LOSS_GOAL,
        'top20_min_winning_sweeps': TOP20_GOAL,
        'parent_loss30_winning_sweeps': 25,
        'parent_top20_winning_sweeps': 19,
        'games': panel_rows,
    }
    write_once(HERE / 'panel.json', panel)

    bound_paths = [
        HERE / 'PLAN.md', HERE / 'build_panel.py', HERE / 'run.py', HERE / 'panel.json',
        STUDY / 'candidate.py', STUDY / 'candidate_parent.py', STUDY / 'layer.py',
        STUDY / 'static_preflight.json', STUDY / 'frozen_manifest.json',
        STUDY / 'freeze_receipt.json', STUDY / 'feature_census.json',
        STUDY / 'build_preflight.py', PARENT_PANEL, PARENT_RECEIPT, PARENT_MANIFEST,
        ROOT / 'diagnostics/stream_replay_io_20260928/fast_game_cached.py',
        ROOT / 'diagnostics/stream_replay_io_20260928/cached_input.py',
        ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json',
        ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py',
        ROOT / 'diagnostics/physical_route_rollout_20260928/check.py',
        ROOT / 'diagnostics/local_target_20260928/run_lock.py', engine_path(),
    ]
    for row in panel_rows:
        bound_paths.extend((Path(row['fixture']['source_replay_path']),
                            Path(row['fixture']['source_action_tape_path']),
                            Path(row['trace_path'])))
    bindings = {str(path.resolve()): sha(path) for path in sorted(set(bound_paths), key=str)}
    manifest = {
        'schema': 'a44-v5-isolated-pasture-100-seat-freeze-v1',
        'complete': True, 'diagnostic_only': True, 'fixed_tape_only': True,
        'reactive_validation': False, 'promotion': False,
        'candidate_sha256': CANDIDATE_HASH,
        'parent_candidate_sha256': PARENT_HASH,
        'panel_sha256': sha(HERE / 'panel.json'),
        'parent_receipt_sha256': sha(PARENT_RECEIPT),
        'binding_count': len(bindings), 'bindings': bindings,
        'shared_lock_path': str(ROOT / 'diagnostics/.shared_game_run.lock'),
        'worker_count': 1,
    }
    write_once(HERE / 'frozen_manifest.json', manifest)
    print(json.dumps({'complete': True, 'candidate_sha256': CANDIDATE_HASH,
                      'parent_candidate_sha256': PARENT_HASH,
                      'panel_sha256': manifest['panel_sha256'],
                      'parent_receipt_sha256': manifest['parent_receipt_sha256'],
                      'binding_count': len(bindings), 'games': len(panel_rows),
                      'expected_trigger_seats': 2}, indent=2))


if __name__ == '__main__':
    main()
