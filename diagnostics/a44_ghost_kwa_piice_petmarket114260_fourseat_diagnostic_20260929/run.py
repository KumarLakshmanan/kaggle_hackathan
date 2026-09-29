from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PARENT = HERE / 'candidate_parent.py'
CANDIDATE = HERE / 'candidate.py'
PANEL = HERE / 'panel.json'
MANIFEST = HERE / 'frozen_manifest.json'
RESULTS = HERE / 'outcomes.jsonl'
RECEIPT = HERE / 'outcome_receipt.json'
RUN_MANIFEST = HERE / 'run_manifest.json'
OWN_LOCK = HERE / 'run.lock'
SHARED_LOCK = ROOT / 'diagnostics/.shared_game_run.lock'
FIELDS = ('result', 'candidate_reward', 'opponent_reward', 'margin',
          'candidate_status', 'opponent_status', 'frames')


def read(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def telemetry_checks(actual):
    telemetry = actual.get('candidate_telemetry') or {}
    checks = {
        'gate_leaf': telemetry.get('a44_pet_market_gate_key72') == 'PET_CAFE|M8+|C>S|G0',
        'rival_melons': telemetry.get('a44_pet_market_gate_rival_melon72') == 12,
        'public_wheat': telemetry.get('a44_pet_market_gate_wheat_stock72') == 9975,
        'gate_active': telemetry.get('a44_pet_market_gate_active72') is True,
        'route': telemetry.get('a44_pet_market_gate_route72') == '113517834',
        'active_calls': telemetry.get('a44_pet_market_gate_turns') == 648,
        'gate_errors_zero': telemetry.get('a44_pet_market_gate_errors') == 0,
    }
    nonzero = {key: value for key, value in telemetry.items()
               if ('error' in key.lower() or 'collision' in key.lower())
               and value not in (0, False, None, '')}
    checks['all_telemetry_errors_zero'] = not nonzero
    return checks, nonzero


def run_once():
    from build_preflight import verify_manifest
    manifest, panel, static = verify_manifest(check_outputs=True)
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    from diagnostics.stream_replay_io_20260928.fast_game_cached import play

    started = datetime.now(timezone.utc).isoformat()
    games = []
    with exclusive_run(SHARED_LOCK):
        with exclusive_run(OWN_LOCK):
            require(not any(path.exists() for path in (RESULTS, RECEIPT, RUN_MANIFEST)),
                    'diagnostic is one-shot; outputs already exist')
            with RUN_MANIFEST.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump({
                    'started_at_utc': started,
                    'candidate_sha256': manifest['candidate_sha256'],
                    'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                    'panel_sha256': manifest['panel_sha256'],
                    'shared_lock_path': str(SHARED_LOCK),
                    'worker_count': 1,
                    'resume_allowed': False,
                    'fixed_tape_only': True,
                    'diagnostic_only': True,
                }, stream, indent=2)
                stream.write('\n')
            with RESULTS.open('x', encoding='utf-8', newline='\n') as stream:
                for job in panel['jobs']:
                    fixture = job['fixture']
                    seat = int(job['seat'])
                    parent = play(fixture, PARENT, manifest['parent_candidate_sha256'], seat)
                    candidate = play(fixture, CANDIDATE, manifest['candidate_sha256'], seat)
                    parent_clean = (parent.get('candidate_status') == 'DONE'
                                    and parent.get('opponent_status') == 'DONE'
                                    and parent.get('frames') == 720
                                    and not parent.get('candidate_errors'))
                    candidate_clean = (candidate.get('candidate_status') == 'DONE'
                                       and candidate.get('opponent_status') == 'DONE'
                                       and candidate.get('frames') == 720
                                       and not candidate.get('candidate_errors'))
                    parent_errors = {key: value for key, value in
                                     (parent.get('candidate_telemetry') or {}).items()
                                     if ('error' in key.lower() or 'collision' in key.lower())
                                     and value not in (0, False, None, '')}
                    parent_clean = parent_clean and not parent_errors
                    checks, telemetry_errors = telemetry_checks(candidate)
                    equal = {field: parent.get(field) == candidate.get(field)
                             for field in FIELDS}
                    if job['role'] == 'target':
                        baseline_equal = {field: parent.get(field) == job['parent_baseline'].get(field)
                                          for field in FIELDS}
                        target_win = (candidate.get('result') == 'win'
                                      and float(candidate.get('margin', 0)) > 0)
                        control_equal = None
                    else:
                        baseline_equal = None
                        target_win = None
                        control_equal = all(equal.values())
                    row = {
                        'fixture_id': job['fixture_id'],
                        'seat': seat,
                        'role': job['role'],
                        'candidate_sha256': manifest['candidate_sha256'],
                        'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                        'parent_clean_done_done_720': parent_clean,
                        'candidate_clean_done_done_720': candidate_clean,
                        'parent_telemetry_errors': parent_errors,
                        'candidate_telemetry_checks': checks,
                        'candidate_telemetry_errors': telemetry_errors,
                        'candidate_telemetry_passed': all(checks.values()),
                        'parent': {field: parent.get(field) for field in FIELDS},
                        'candidate': {field: candidate.get(field) for field in FIELDS},
                        'target_candidate_won': target_win,
                        'target_parent_matches_8f_panel': baseline_equal,
                        'control_matches_direct_parent': control_equal,
                        'field_equality_parent_candidate': equal,
                        'delta_margin': float(candidate['margin']) - float(parent['margin']),
                    }
                    games.append(row)
                    stream.write(json.dumps(row, ensure_ascii=True, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({
                        'fixture_id': job['fixture_id'], 'seat': seat,
                        'role': job['role'], 'parent_clean': parent_clean,
                        'candidate_clean': candidate_clean,
                        'telemetry_passed': all(checks.values()),
                        'parent_result': parent.get('result'),
                        'candidate_result': candidate.get('result'),
                        'candidate_margin': candidate.get('margin'),
                    }, ensure_ascii=True), flush=True)

    targets = [row for row in games if row['role'] == 'target']
    controls = [row for row in games if row['role'] == 'control']
    complete = len(games) == 4
    clean = complete and all(row['parent_clean_done_done_720']
                             and row['candidate_clean_done_done_720'] for row in games)
    telemetry = complete and all(row['candidate_telemetry_passed'] for row in games)
    parent_target = (len(targets) == 2 and all(
        all(row['target_parent_matches_8f_panel'].values()) for row in targets))
    target_wins = (len(targets) == 2 and all(row['target_candidate_won'] for row in targets))
    control_exact = (len(controls) == 2 and all(
        row['control_matches_direct_parent'] for row in controls))
    receipt = {
        'schema': 'a44-v5-pet-market-114260-four-seat-diagnostic-outcome-v1',
        'complete': complete,
        'diagnostic_only': True,
        'fixed_tape_only': True,
        'reactive_validation': False,
        'promotion': False,
        'candidate_sha256': manifest['candidate_sha256'],
        'parent_candidate_sha256': manifest['parent_candidate_sha256'],
        'panel_sha256': manifest['panel_sha256'],
        'games': games,
        'game_count': len(games),
        'native_game_runs': len(games) * 2,
        'all_runs_clean_done_done_720': clean,
        'all_candidate_telemetry_passed': telemetry,
        'parent_targets_match_bound_8f_panel': parent_target,
        'both_target_seats_win': target_wins,
        'both_control_seats_exact_to_parent': control_exact,
        'passed': complete and clean and telemetry and parent_target and target_wins and control_exact,
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    with RECEIPT.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=True, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'games'},
                     ensure_ascii=True, indent=2), flush=True)
    return receipt


if __name__ == '__main__':
    result = run_once()
    if not result['passed']:
        raise SystemExit(1)
