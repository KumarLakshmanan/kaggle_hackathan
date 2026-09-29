"""One-shot paired 8-game native fixed-tape diagnostic for V4 + PIICE."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CANDIDATE = HERE / 'candidate.py'
PARENT = HERE / 'candidate_parent.py'
PANEL_PATH = HERE / 'panel.json'
MANIFEST_PATH = HERE / 'frozen_manifest.json'
PREFLIGHT_PATH = HERE / 'static_preflight.json'
PARENT_RECEIPTS = HERE / 'parent_receipts.json'
RESULTS_PATH = HERE / 'outcomes.jsonl'
RECEIPT_PATH = HERE / 'outcome_receipt.json'
RUN_MANIFEST_PATH = HERE / 'run_manifest.json'
OWN_LOCK_PATH = HERE / 'run.lock'
SHARED_LOCK_PATH = ROOT / 'diagnostics/.shared_game_run.lock'
CONTROL_FIELDS = ('result', 'candidate_reward', 'opponent_reward', 'margin',
                  'candidate_status', 'opponent_status', 'frames')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_frozen():
    manifest = read(MANIFEST_PATH)
    static = read(PREFLIGHT_PATH)
    require(manifest.get('complete') is True and manifest.get('diagnostic_only') is True
            and manifest.get('fixed_tape_only') is True and manifest.get('promotion') is False,
            'manifest metadata changed')
    require(sha(CANDIDATE) == manifest.get('candidate_sha256')
            and sha(PARENT) == manifest.get('parent_candidate_sha256'),
            'candidate/parent SHA mismatch')
    require(sha(PANEL_PATH) == manifest.get('panel_sha256'), 'panel hash mismatch')
    require(manifest.get('runner_sha256') == sha(HERE / 'run.py')
            and manifest.get('builder_sha256') == sha(HERE / 'build_preflight.py')
            and manifest.get('plan_sha256') == sha(HERE / 'PLAN.md'),
            'runner, builder, or plan differs from frozen manifest')
    require(static.get('passed') is True and static.get('static_only') is True
            and static.get('engine_transitions') == 0
            and static.get('candidate_sha256') == manifest['candidate_sha256']
            and static.get('focus_prefix_actions_equal_steps_0_to_143') is True,
            'static preflight failed or changed')
    bindings = manifest.get('bindings', {})
    require(len(bindings) == manifest.get('binding_count'), 'binding count mismatch')
    mismatches = []
    for path_text, expected in bindings.items():
        path = Path(path_text)
        actual = sha(path) if path.is_file() else 'MISSING'
        if actual != expected:
            mismatches.append((path_text, actual, expected))
    require(not mismatches, f'frozen input hash mismatch: {mismatches[:5]}')
    panel = read(PANEL_PATH)
    require(panel.get('candidate_sha256') == manifest['candidate_sha256']
            and panel.get('parent_candidate_sha256') == manifest['parent_candidate_sha256']
            and panel.get('game_count') == 8 and len(panel.get('expected_seats', [])) == 8,
            'panel identity or size mismatch')
    rows = panel['expected_seats']
    require(sum(bool(row['trigger']) for row in rows) == 2
            and sum(not bool(row['trigger']) for row in rows) == 6,
            'trigger/control counts changed')
    require(not any(path.exists() for path in
                    (RESULTS_PATH, RECEIPT_PATH, RUN_MANIFEST_PATH)),
            'one-shot runner refuses existing output')
    return manifest, panel


def activation_checks(row, expected):
    t = row.get('candidate_telemetry', {})
    trigger = bool(expected['trigger'])
    checks = {
        'clean_done_720': row['candidate_status'] == row['opponent_status'] == 'DONE'
                          and row['frames'] == 720 and not row.get('candidate_errors'),
        'piice_key72': t.get('piice_key72') == expected['key72'],
        'piice_branch144': t.get('piice_branch144') == expected['bridge_branch'],
        'piice_key144': t.get('piice_key144') == expected['key72'],
        'piice_pair144': t.get('piice_pair144') == expected['pair'],
        'piice_activation': t.get('piice_active144') is trigger,
        'piice_route': t.get('piice_route144') == (str(expected['route']) if trigger else ''),
        'piice_active_turns': t.get('piice_active_turns') == (575 if trigger else 0),
        'piice_errors_zero': t.get('piice_errors', 0) == 0,
        'ghost_inactive': not t.get('a44_ghost_wheat_active72', False),
        'kwa_inactive': not t.get('a44_kwa_wheat_zero_active72', False),
        'bridge_source': t.get('bridge_selected') == expected['bridge_branch'],
        'bridge_errors_zero': t.get('bridge_errors', 0) == 0,
        'ghost_errors_zero': t.get('a44_goose4_errors', 0) == 0
                             and t.get('a44_smoothie_errors', 0) == 0,
        'kwa_errors_zero': t.get('a44_kwa_wheat_zero_errors', 0) == 0,
    }
    return checks


def outputs_absent():
    present = [str(path) for path in (RESULTS_PATH, RECEIPT_PATH, RUN_MANIFEST_PATH)
               if path.exists()]
    require(not present, f'one-shot runner refuses existing outputs: {present}')


def run_once():
    manifest, panel = verify_frozen()
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    from diagnostics.stream_replay_io_20260928.fast_game_cached import play
    expected_by_key = {(row['fixture_id'], int(row['seat'])): row
                       for row in panel['expected_seats']}
    fixture_by_id = {row['fixture_id']: row for row in panel['fixtures']}
    started = datetime.now(timezone.utc).isoformat()
    games = []
    with exclusive_run(SHARED_LOCK_PATH):
        with exclusive_run(OWN_LOCK_PATH):
            outputs_absent()
            with RUN_MANIFEST_PATH.open('x', encoding='utf-8', newline='\n') as out:
                json.dump({'started_at_utc': started,
                           'candidate_sha256': manifest['candidate_sha256'],
                           'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                           'panel_sha256': manifest['panel_sha256'],
                           'pid': __import__('os').getpid()}, out, indent=2)
                out.write('\n')
            with RESULTS_PATH.open('x', encoding='utf-8', newline='\n') as stream:
                for expected in panel['expected_seats']:
                    key = (expected['fixture_id'], int(expected['seat']))
                    fixture = fixture_by_id[key[0]]
                    parent = play(fixture, PARENT, manifest['parent_candidate_sha256'], key[1])
                    candidate = play(fixture, CANDIDATE, manifest['candidate_sha256'], key[1])
                    clean = (parent['candidate_status'] == parent['opponent_status'] == 'DONE'
                             and candidate['candidate_status'] == candidate['opponent_status'] == 'DONE'
                             and parent['frames'] == candidate['frames'] == 720
                             and not parent.get('candidate_errors') and not candidate.get('candidate_errors'))
                    activation = activation_checks(candidate, expected)
                    trigger = bool(expected['trigger'])
                    parent_fields = {field: parent[field] for field in CONTROL_FIELDS}
                    candidate_fields = {field: candidate[field] for field in CONTROL_FIELDS}
                    exact_parent = parent_fields == candidate_fields
                    target_win = trigger and candidate['result'] == 'win' and parent['result'] == 'loss'
                    control_preserved = (not trigger) and exact_parent
                    row = {
                        'fixture_id': key[0], 'candidate_seat': key[1],
                        'trigger': trigger, 'candidate_sha256': manifest['candidate_sha256'],
                        'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                        'parent': parent_fields, 'candidate': candidate_fields,
                        'parent_telemetry': parent.get('candidate_telemetry', {}),
                        'candidate_telemetry': candidate.get('candidate_telemetry', {}),
                        'clean': clean, 'activation_checks': activation,
                        'activation_passed': all(activation.values()),
                        'parent_outcome_exact': exact_parent,
                        'target_win_over_parent': target_win if trigger else None,
                        'control_exact_to_parent': control_preserved if not trigger else None,
                        'delta_margin': candidate['margin'] - parent['margin'],
                        'parent_wall_seconds': parent['wall_seconds'],
                        'candidate_wall_seconds': candidate['wall_seconds'],
                    }
                    games.append(row)
                    stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                    stream.flush()
                    print(json.dumps({'fixture_id': key[0], 'seat': key[1],
                                      'trigger': trigger, 'parent': parent['result'],
                                      'candidate': candidate['result'],
                                      'margin': candidate['margin'],
                                      'clean': clean,
                                      'activation_passed': all(activation.values()),
                                      'control_exact': exact_parent if not trigger else None},
                                     ensure_ascii=False), flush=True)
            targets = [row for row in games if row['trigger']]
            controls = [row for row in games if not row['trigger']]
            receipt = {
                'schema': 'a44-v4-piice-paired-outcome-v1',
                'complete': len(games) == 8,
                'diagnostic_only': True, 'fixed_tape_only': True,
                'reactive_validation': False, 'promotion': False,
                'candidate_sha256': manifest['candidate_sha256'],
                'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                'panel_sha256': manifest['panel_sha256'],
                'all_8_clean': len(games) == 8 and all(row['clean'] for row in games),
                'all_8_activation_checks_passed': len(games) == 8 and all(row['activation_passed'] for row in games),
                'both_target_seats_win_over_parent': len(targets) == 2 and all(row['target_win_over_parent'] for row in targets),
                'six_controls_exact_to_parent': len(controls) == 6 and all(row['control_exact_to_parent'] for row in controls),
                'target_parent_margins': [row['parent']['margin'] for row in targets],
                'target_candidate_margins': [row['candidate']['margin'] for row in targets],
                'games': games, 'completed_at_utc': datetime.now(timezone.utc).isoformat(),
            }
            receipt['passed'] = all(receipt[key] for key in (
                'complete', 'all_8_clean', 'all_8_activation_checks_passed',
                'both_target_seats_win_over_parent', 'six_controls_exact_to_parent'))
            with RECEIPT_PATH.open('x', encoding='utf-8', newline='\n') as out:
                json.dump(receipt, out, ensure_ascii=False, indent=2)
                out.write('\n')
            print(json.dumps({key: value for key, value in receipt.items() if key != 'games'},
                             ensure_ascii=False, indent=2), flush=True)
    return receipt


if __name__ == '__main__':
    _, _ = verify_frozen()
    result = run_once()
    if not result['passed']:
        raise SystemExit(1)
