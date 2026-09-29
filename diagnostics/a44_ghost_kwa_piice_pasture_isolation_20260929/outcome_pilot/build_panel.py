from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
PARENT_PANEL = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929/parent_panel.json'
TARGETS = ('live-114274897', 'public-win-114193811')
TARGET = 'live-114274897'
CONTROL = 'public-win-114193811'
PARENT_SHA = '8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62'
CANDIDATE_SHA = '6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc'
LEAF_KEY = 'BRUNCH_SPOT|M8+|C>S|G+'
LEAF_ROUTE = '113332529'
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
    assert not any((HERE / name).exists() for name in outputs), 'pilot is one-shot'

    static = read(STUDY / 'static_preflight.json')
    freeze = read(STUDY / 'freeze_receipt.json')
    static_manifest = read(STUDY / 'frozen_manifest.json')
    features = read(STUDY / 'feature_census.json')
    cached_inputs = read(ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json')
    assert static.get('all_static_gates_passed') is True
    assert static.get('candidate_sha256') == CANDIDATE_SHA
    assert static.get('parent_candidate_sha256') == PARENT_SHA
    assert static.get('selector_trigger_count') == 2
    assert static.get('public54_trigger_count') == 0
    assert static.get('top20_trigger_count') == 0
    assert static.get('public_win_trigger_count') == 0
    assert sha(STUDY / 'candidate.py') == CANDIDATE_SHA
    assert sha(STUDY / 'candidate_parent.py') == PARENT_SHA
    assert freeze.get('complete') and freeze.get('static_only')
    assert freeze.get('candidate_sha256') == CANDIDATE_SHA
    assert freeze.get('manifest_sha256') == sha(STUDY / 'frozen_manifest.json')
    assert len(features.get('rows', [])) == 208
    for path_text, expected in static_manifest.get('files', {}).items():
        assert sha(Path(path_text) if Path(path_text).is_absolute() else STUDY / path_text) == expected
    for path_text, expected in static_manifest.get('external_inputs', {}).items():
        assert sha(Path(path_text)) == expected
    for path_text, expected in static_manifest.get('trace_sha256_bindings', {}).items():
        assert sha(Path(path_text)) == expected

    parent_data = read(PARENT_PANEL)
    fixtures = {row['fixture_id']: row for row in parent_data['fixtures']}
    assert set(TARGETS).issubset(fixtures)
    census = {(row['fixture_id'], int(row['seat'])): row for row in features['rows']}
    jobs = []
    cached_replays = {row['source_replay_path']: row for row in cached_inputs['replays']}
    cached_fixtures = {row['fixture_id']: row['source_replay_path'] for row in cached_inputs['fixtures']}
    for fixture_id in TARGETS:
        fixture = fixtures[fixture_id]
        is_target = fixture_id == TARGET
        for seat in (0, 1):
            feature = census[(fixture_id, seat)]
            assert bool(feature['isolated_override_trigger']) is is_target
            assert int(feature['obs1_public_rival_hands']) == (5 if is_target else 6)
            assert int(feature['obs1_public_rival_pasture_count']) == 1
            assert (feature['obs72_public_leaf_key'] == LEAF_KEY) is is_target
            for field in ('source_replay_path', 'source_action_tape_path'):
                assert Path(fixture[field]).is_file(), fixture[field]
            replay = cached_replays[fixture['source_replay_path']]
            assert cached_fixtures[fixture_id] == fixture['source_replay_path']
            assert replay['source_replay_sha256'] == fixture['source_replay_sha256']
            assert sha(Path(fixture['source_replay_path'])) == replay['compressed_sha256']
            tape_data = json.loads(__import__('gzip').decompress(
                Path(fixture['source_action_tape_path']).read_bytes()))
            tape = tape_data['actions']
            import json as _json
            tape_hashes = [hashlib.sha256(_json.dumps(tape, sort_keys=sort_keys,
                separators=(',', ':')).encode()).hexdigest() for sort_keys in (False, True)]
            assert fixture['source_opponent_action_sha256'] in tape_hashes
            jobs.append({
                'fixture_id': fixture_id,
                'seat': seat,
                'role': 'THIRD' if is_target else 'ChrisTu control',
                'trigger': is_target,
                'expected': {
                    'rival_hands': 5 if is_target else 6,
                    'rival_pastures': 1,
                    'branch': 'source' if is_target else 'shared151',
                    'leaf_key': LEAF_KEY if is_target else '',
                    'leaf_route': LEAF_ROUTE if is_target else '',
                    'leaf_turns': 647 if is_target else 0,
                },
                'fixture': dict(fixture),
                'trace_path': feature['trace_path'],
                'trace_sha256': feature['trace_sha256'],
            })
    assert len(jobs) == 4

    panel = {
        'schema': 'a44-v5-isolated-pasture-four-seat-pilot-v1',
        'candidate_sha256': CANDIDATE_SHA,
        'parent_candidate_sha256': PARENT_SHA,
        'fixed_tape_only': True,
        'reactive_validation': False,
        'promotion': False,
        'fixture_count': 2,
        'seat_count': 4,
        'game_count_including_parent_pairs': 8,
        'jobs': jobs,
        'outcome_gate': {
            'clean_done_done_720': True,
            'target_both_seats_win_and_parent_both_seats_lose': True,
            'control_exact_to_parent': True,
        },
    }
    write_once(HERE / 'panel.json', panel)

    bound_paths = [
        HERE / 'PLAN.md', HERE / 'build_panel.py', HERE / 'run.py',
        HERE / 'panel.json', STUDY / 'candidate.py', STUDY / 'candidate_parent.py',
        STUDY / 'layer.py', STUDY / 'static_preflight.json',
        STUDY / 'frozen_manifest.json', STUDY / 'freeze_receipt.json',
        STUDY / 'feature_census.json', STUDY / 'build_preflight.py',
        PARENT_PANEL,
        ROOT / 'diagnostics/stream_replay_io_20260928/fast_game_cached.py',
        ROOT / 'diagnostics/stream_replay_io_20260928/cached_input.py',
        ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json',
        ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py',
        ROOT / 'diagnostics/physical_route_rollout_20260928/check.py',
        ROOT / 'diagnostics/local_target_20260928/run_lock.py',
        engine_path(),
    ]
    for job in jobs:
        bound_paths.extend((Path(job['fixture']['source_replay_path']),
                            Path(job['fixture']['source_action_tape_path']),
                            Path(job['trace_path'])))
    bindings = {str(path.resolve()): sha(path) for path in sorted(set(bound_paths), key=str)}
    manifest = {
        'schema': 'a44-v5-isolated-pasture-four-seat-freeze-v1',
        'complete': True,
        'diagnostic_only': True,
        'fixed_tape_only': True,
        'reactive_validation': False,
        'promotion': False,
        'candidate_sha256': CANDIDATE_SHA,
        'parent_candidate_sha256': PARENT_SHA,
        'panel_sha256': sha(HERE / 'panel.json'),
        'bindings': bindings,
        'binding_count': len(bindings),
        'shared_lock_path': str(ROOT / 'diagnostics/.shared_game_run.lock'),
        'worker_count': 1,
    }
    write_once(HERE / 'frozen_manifest.json', manifest)
    print(json.dumps({'complete': True, 'candidate_sha256': CANDIDATE_SHA,
                      'parent_candidate_sha256': PARENT_SHA,
                      'panel_sha256': manifest['panel_sha256'],
                      'binding_count': len(bindings), 'seat_count': 4,
                      'game_count_including_parent_pairs': 8}, indent=2))


if __name__ == '__main__':
    main()
