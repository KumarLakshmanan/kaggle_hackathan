"""Deterministically append the kwa wheat-zero layer to exact integrated 6d."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PARENT_REL = Path('diagnostics/a44_goose4_smoothie_source_20260929/candidate.py')
PARENT_SHA256 = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
MANIFEST_NAME = 'manifest.json'
TARGET_FIXTURE_IDS = (
    'live-114227779',
    'live-114236633',
    'live-114257327',
)
EXPECTED_WHEAT_PLOTS = {
    'live-114227779': 0,
    'live-114236633': 4,
    'live-114257327': 6,
}

INPUTS = {
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


def root_path(relative: str) -> Path:
    return ROOT / Path(relative)


def assemble_candidate() -> bytes:
    parent = root_path(str(PARENT_REL))
    actual = sha256(parent)
    if actual != PARENT_SHA256:
        raise SystemExit(f'exact 6d parent hash mismatch: {actual}')
    parent_bytes = parent.read_bytes()
    layer_bytes = (HERE / 'wheat_zero_layer.py').read_bytes()
    separator = b'' if parent_bytes.endswith(b'\n') else b'\n'
    return parent_bytes + separator + b'\n' + layer_bytes


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
                    encoding='utf-8')


def build_target_panel(candidate_sha: str) -> dict:
    parent_panel = json.loads(root_path(INPUTS['parent_panel']).read_text(encoding='utf-8'))
    combined = json.loads(root_path(INPUTS['parent_combined_results']).read_text(encoding='utf-8'))
    parent_manifest = json.loads(root_path(INPUTS['parent_manifest']).read_text(encoding='utf-8'))
    assert parent_panel['fixture_count'] == 104
    assert combined['complete'] and combined['candidate_sha256'] == PARENT_SHA256
    assert combined['panel_sha256'] == parent_manifest['full_panel_sha256']
    fixture_rows = {row['fixture_id']: row for row in parent_panel['fixtures']}
    assert len(fixture_rows) == 104
    combined_rows = {(row['fixture_id'], int(row['candidate_seat'])): row for row in combined['games']}
    assert len(combined_rows) == 208
    fixtures = []
    jobs = []
    for fixture_id in TARGET_FIXTURE_IDS:
        fixture = fixture_rows[fixture_id]
        assert fixture['panel'] == 'loss30'
        fixtures.append(fixture)
        for seat in (0, 1):
            baseline = combined_rows[(fixture_id, seat)]
            jobs.append({
                'fixture_id': fixture_id,
                'seat': seat,
                'panel': 'loss30',
                'expected_trigger': fixture_id == 'live-114227779',
                'expected_public_key': 'BRUNCH_SPOT|M8+|C<S|G0',
                'expected_rival_wheat_plots': EXPECTED_WHEAT_PLOTS[fixture_id],
                'expected_route': '113535489' if fixture_id == 'live-114227779' else '',
                'baseline_6d': {key: baseline.get(key) for key in (
                    'candidate_sha256', 'decision_equivalence_reuse',
                    'reused_parent_candidate_sha256', 'result', 'margin',
                    'candidate_reward', 'opponent_reward', 'candidate_status',
                    'opponent_status', 'frames', 'candidate_errors', 'clean',
                )},
            })
    assert len(jobs) == 6
    return {
        'complete': True,
        'diagnostic_only': True,
        'fixed_tape_only': True,
        'candidate_sha256': candidate_sha,
        'parent_6d_candidate_sha256': PARENT_SHA256,
        'parent_panel_sha256': sha256(root_path(INPUTS['parent_panel'])),
        'parent_combined_results_sha256': sha256(root_path(INPUTS['parent_combined_results'])),
        'fixture_ids': list(TARGET_FIXTURE_IDS),
        'seats': [0, 1],
        'workers': 1,
        'fixtures': fixtures,
        'jobs': jobs,
    }


def build_manifest(candidate_sha: str) -> dict:
    parent_manifest_path = root_path(INPUTS['parent_manifest'])
    parent_manifest = json.loads(parent_manifest_path.read_text(encoding='utf-8'))
    if parent_manifest.get('candidate_sha256') != PARENT_SHA256:
        raise SystemExit('6d parent manifest does not bind the exact candidate')
    bindings = {name: sha256(root_path(path)) for name, path in INPUTS.items()}
    package_paths = {
        'wheat_zero_layer.py': HERE / 'wheat_zero_layer.py',
        'candidate.py': HERE / 'candidate.py',
        'build_candidate.py': HERE / 'build_candidate.py',
        'static_preflight.py': HERE / 'static_preflight.py',
        'run_six.py': HERE / 'run_six.py',
        'target_panel.json': HERE / 'target_panel.json',
        'PLAN.md': HERE / 'PLAN.md',
    }
    package_bindings = {name: sha256(path) for name, path in package_paths.items()}
    feature_rows = json.loads(root_path(INPUTS['feature_rows_208']).read_text(encoding='utf-8'))
    return {
        'artifact_id': 'a44_kwa_wheat_zero_20260929',
        'diagnostic_only': True,
        'static_freeze_only': True,
        'simulation_or_game_run': False,
        'parent_candidate': {'path': str(PARENT_REL).replace('\\', '/'), 'sha256': PARENT_SHA256},
        'candidate_sha256': candidate_sha,
        'source_a44_sha256': parent_manifest['source_a44_sha256'],
        'trigger': {
            'step': 72,
            'bridge_branch': 'source',
            'public_leaf': 'BRUNCH_SPOT|M8+|C<S|G0',
            'rival_wheat_plots': 0,
            'route_id': 113535489,
            'fixture_identity_used': False,
        },
        'frozen_static_gates': {
            'bound_feature_rows': 208,
            'panel_counts': {'loss30': 60, 'top20': 40, 'public-win': 108},
            'expected_trigger_rows': 2,
            'expected_trigger_fixture': 'live-114227779',
            'expected_trigger_seats': [0, 1],
            'expected_top20_triggers': 0,
            'expected_public_win_triggers': 0,
            'same_leaf_winning_controls_must_not_trigger': True,
        },
        'runner': {
            'path': 'run_six.py',
            'workers': 1,
            'shared_lock_path': 'diagnostics/.shared_game_run.lock',
            'run_directory': 'diagnostics/a44_kwa_wheat_zero_20260929/runs/six_game_run_001',
            'resume_allowed': False,
            'append_only_receipts': ['attempts.jsonl', 'outcomes.jsonl'],
        },
        'outcome_gates_frozen_before_run': {
            'all_six_games_done_done_720_clean': True,
            'kwa_both_seats_win_and_positive_margin': True,
            'kwa_both_seats_delta_margin_positive_vs_exact_6d_combined': True,
            'kwa_both_seats_route_113535489_and_647_active_turns': True,
            'four_wheat_positive_controls_do_not_activate': True,
            'four_controls_exact_match_6d_combined_outcomes': [
                'result', 'margin', 'candidate_reward', 'opponent_reward',
                'candidate_status', 'opponent_status', 'frames',
            ],
        },
        'bound_inputs': bindings,
        'bound_input_paths': INPUTS,
        'package_bindings': package_bindings,
    }


def main() -> None:
    candidate_bytes = assemble_candidate()
    candidate_path = HERE / 'candidate.py'
    candidate_path.write_bytes(candidate_bytes)
    candidate_sha = sha256(candidate_path)
    target_panel = build_target_panel(candidate_sha)
    write_json(HERE / 'target_panel.json', target_panel)
    manifest = build_manifest(candidate_sha)
    (HERE / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )
    print(f'candidate_sha256={candidate_sha}')
    print(f'manifest_sha256={sha256(HERE / MANIFEST_NAME)}')


if __name__ == '__main__':
    main()
