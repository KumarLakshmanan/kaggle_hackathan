from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
PARENT = STUDY / 'candidate_parent.py'
CANDIDATE = STUDY / 'candidate.py'
PANEL = HERE / 'panel.json'
MANIFEST = HERE / 'frozen_manifest.json'
RESULTS = HERE / 'outcomes.jsonl'
RECEIPT = HERE / 'outcome_receipt.json'
RUN_MANIFEST = HERE / 'run_manifest.json'
OWN_LOCK = HERE / 'run.lock'
SHARED_LOCK = ROOT / 'diagnostics/.shared_game_run.lock'
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


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify():
    manifest = read(MANIFEST)
    panel = read(PANEL)
    require(manifest.get('complete') is True and manifest.get('diagnostic_only') is True
            and manifest.get('fixed_tape_only') is True and manifest.get('promotion') is False,
            'manifest scope changed')
    require(sha(CANDIDATE) == manifest.get('candidate_sha256'), 'candidate hash mismatch')
    require(sha(PARENT) == manifest.get('parent_candidate_sha256'), 'parent hash mismatch')
    require(sha(PANEL) == manifest.get('panel_sha256'), 'panel hash mismatch')
    require(manifest.get('binding_count') == len(manifest.get('bindings', {})),
            'binding count mismatch')
    missing = []
    for path_text, expected in manifest['bindings'].items():
        path = Path(path_text)
        actual = sha(path) if path.is_file() else 'MISSING'
        if actual != expected:
            missing.append((path_text, actual, expected))
    require(not missing, f'frozen input mismatch: {missing[:5]}')
    static = read(STUDY / 'static_preflight.json')
    require(static.get('all_static_gates_passed') is True
            and static.get('candidate_sha256') == manifest['candidate_sha256']
            and static.get('selector_trigger_count') == 2
            and static.get('top20_trigger_count') == 0,
            'upstream 208-seat static preflight failed')
    require(panel.get('game_count_including_parent_pairs') == 8
            and len(panel.get('jobs', [])) == 4, 'panel shape changed')
    require(not any(path.exists() for path in (RESULTS, RECEIPT, RUN_MANIFEST, OWN_LOCK)),
            'one-shot runner refuses existing or partial outputs')
    return manifest, panel


def telemetry_checks(actual, job):
    telemetry = actual.get('candidate_telemetry') or {}
    expected = job['expected']
    checks = {
        'public_hands_step1': telemetry.get('iso_pasture_rival_hands_step1') == expected['rival_hands'],
        'public_pastures_step1': telemetry.get('iso_pasture_rival_pastures_step1') == expected['rival_pastures'],
        'trigger_latch': telemetry.get('iso_pasture_triggered_step1') is job['trigger'],
        'selected_bridge': telemetry.get('bridge_selected') == expected['branch'],
        'reported_bridge': telemetry.get('iso_pasture_branch_step1') == expected['branch'],
        'route_map_reset': telemetry.get('iso_pasture_reset_route_map_matches') is True,
        'leaf_key72': telemetry.get('iso_pasture_leaf_key72') == expected['leaf_key'],
        'leaf_route72': telemetry.get('iso_pasture_leaf_route72') == expected['leaf_route'],
        'leaf_turns': telemetry.get('iso_pasture_leaf_turns') == expected['leaf_turns'],
        'leaf_errors_zero': telemetry.get('iso_pasture_leaf_errors', 0) == 0,
        'ghost_inactive': not telemetry.get('a44_ghost_wheat_active72', False),
        'kwa_inactive': not telemetry.get('a44_kwa_wheat_zero_active72', False),
        'piice_inactive': not telemetry.get('piice_active144', False),
        'goose4_inactive': telemetry.get('a44_goose4_turns', 0) == 0
            and telemetry.get('a44_goose4_errors', 0) == 0,
    }
    errors = {key: value for key, value in telemetry.items()
              if ('error' in key.lower() or 'collision' in key.lower())
              and value not in (0, False, None, '')}
    checks['all_telemetry_errors_zero'] = not errors
    return checks, errors


def run_once():
    manifest, panel = verify()
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    from diagnostics.stream_replay_io_20260928.fast_game_cached import play
    completed = []
    started = datetime.now(timezone.utc).isoformat()
    with exclusive_run(SHARED_LOCK):
        with exclusive_run(OWN_LOCK):
            require(not any(path.exists() for path in (RESULTS, RECEIPT, RUN_MANIFEST)),
                    'outputs appeared after verification')
            with RUN_MANIFEST.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump({'started_at_utc': started,
                           'candidate_sha256': manifest['candidate_sha256'],
                           'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                           'panel_sha256': manifest['panel_sha256'],
                           'shared_lock_path': str(SHARED_LOCK),
                           'worker_count': 1, 'resume_allowed': False,
                           'fixed_tape_only': True}, stream, indent=2)
                stream.write('\n')
            with RESULTS.open('x', encoding='utf-8', newline='\n') as stream:
                for job in panel['jobs']:
                    fixture = job['fixture']
                    seat = int(job['seat'])
                    parent = play(fixture, PARENT, manifest['parent_candidate_sha256'], seat)
                    candidate = play(fixture, CANDIDATE, manifest['candidate_sha256'], seat)
                    clean = all(row.get('candidate_status') == row.get('opponent_status') == 'DONE'
                                and row.get('frames') == 720 and not row.get('candidate_errors')
                                for row in (parent, candidate))
                    telemetry, telemetry_errors = telemetry_checks(candidate, job)
                    equal = {field: parent.get(field) == candidate.get(field) for field in FIELDS}
                    target_win = (candidate.get('result') == 'win'
                                  and float(candidate.get('margin', 0)) > 0
                                  and parent.get('result') == 'loss')
                    control_exact = (not job['trigger'] and all(equal.values()))
                    row = {
                        'fixture_id': job['fixture_id'], 'seat': seat, 'role': job['role'],
                        'trigger': job['trigger'],
                        'candidate_sha256': manifest['candidate_sha256'],
                        'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                        'clean_done_done_720': clean,
                        'telemetry_checks': telemetry,
                        'telemetry_errors': telemetry_errors,
                        'telemetry_passed': all(telemetry.values()),
                        'parent': {field: parent.get(field) for field in FIELDS},
                        'candidate': {field: candidate.get(field) for field in FIELDS},
                        'parent_telemetry': parent.get('candidate_telemetry', {}),
                        'candidate_telemetry': candidate.get('candidate_telemetry', {}),
                        'target_win_over_parent': target_win if job['trigger'] else None,
                        'control_exact_to_parent': control_exact if not job['trigger'] else None,
                        'field_equality': equal,
                        'delta_margin': candidate['margin'] - parent['margin'],
                    }
                    completed.append(row)
                    stream.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({'fixture_id': job['fixture_id'], 'seat': seat,
                                      'role': job['role'], 'clean': clean,
                                      'telemetry_passed': all(telemetry.values()),
                                      'parent_result': parent['result'],
                                      'candidate_result': candidate['result'],
                                      'candidate_margin': candidate['margin']},
                                     ensure_ascii=False), flush=True)

    target = [row for row in completed if row['trigger']]
    controls = [row for row in completed if not row['trigger']]
    receipt = {
        'schema': 'a44-v5-isolated-pasture-four-seat-outcome-v1',
        'complete': len(completed) == 4,
        'diagnostic_only': True, 'fixed_tape_only': True,
        'reactive_validation': False, 'promotion': False,
        'candidate_sha256': manifest['candidate_sha256'],
        'parent_candidate_sha256': manifest['parent_candidate_sha256'],
        'panel_sha256': manifest['panel_sha256'],
        'games': completed, 'game_count': len(completed),
        'clean_all': len(completed) == 4 and all(row['clean_done_done_720'] for row in completed),
        'telemetry_all': len(completed) == 4 and all(row['telemetry_passed'] for row in completed),
        'target_seats': len(target),
        'target_both_seats_win_over_parent': len(target) == 2 and all(row['target_win_over_parent'] for row in target),
        'chris_control_seats': len(controls),
        'chris_controls_exact_to_parent': len(controls) == 2 and all(row['control_exact_to_parent'] for row in controls),
        'passed': (len(completed) == 4
                   and all(row['clean_done_done_720'] and row['telemetry_passed'] for row in completed)
                   and len(target) == 2 and all(row['target_win_over_parent'] for row in target)
                   and len(controls) == 2 and all(row['control_exact_to_parent'] for row in controls)),
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    with RECEIPT.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'games'}, indent=2), flush=True)
    return receipt


if __name__ == '__main__':
    _, _ = verify()
    result = run_once()
    if not result['passed']:
        raise SystemExit(1)
