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
PET_FIELDS = {
    'a44_pet_market_gate_key72', 'a44_pet_market_gate_rival_melon72',
    'a44_pet_market_gate_wheat_stock72', 'a44_pet_market_gate_active72',
    'a44_pet_market_gate_route72', 'a44_pet_market_gate_turns',
    'a44_pet_market_gate_errors',
}
RANK = {'loss': 0, 'draw': 1, 'win': 2}


def read(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def telemetry_check(actual, expected, baseline_telemetry=None, require_baseline=False):
    telemetry = actual.get('candidate_telemetry') or {}
    checks = {
        'leaf72': telemetry.get('a44_pet_market_gate_key72') == expected['leaf'],
        'rival_melons72': telemetry.get('a44_pet_market_gate_rival_melon72') == expected['rival_visible_melon_count'],
        'public_wheat72': telemetry.get('a44_pet_market_gate_wheat_stock72') == expected['public_wheat_inventory'],
        'active72': telemetry.get('a44_pet_market_gate_active72') is expected['active'],
        'route72': telemetry.get('a44_pet_market_gate_route72') == expected['route'],
        'active_calls': telemetry.get('a44_pet_market_gate_turns') == expected['active_calls'],
        'pet_gate_errors_zero': telemetry.get('a44_pet_market_gate_errors') == 0,
    }
    if require_baseline:
        underlay = {key: value for key, value in telemetry.items() if key not in PET_FIELDS}
        checks['exact_6a_underlay_telemetry'] = underlay == baseline_telemetry
    errors = {key: value for key, value in telemetry.items()
              if ('error' in key.lower() or 'collision' in key.lower())
              and value not in (0, False, None, '')}
    checks['all_telemetry_errors_zero'] = not errors
    checks['candidate_errors_empty'] = not actual.get('candidate_errors')
    return checks, errors


def clean(actual):
    return (actual.get('candidate_status') == actual.get('opponent_status') == 'DONE'
            and actual.get('frames') == 720
            and not actual.get('candidate_errors'))


def run_once():
    from build_preflight import verify
    manifest, panel, static = verify()
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    from diagnostics.stream_replay_io_20260928.fast_game_cached import play

    rows = []
    started = datetime.now(timezone.utc).isoformat()
    with exclusive_run(SHARED_LOCK):
        with exclusive_run(OWN_LOCK):
            require(not any(path.exists() for path in
                            (RESULTS, RECEIPT, RUN_MANIFEST)),
                    'one-shot run refuses existing or partial outputs')
            with RUN_MANIFEST.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump({'started_at_utc': started,
                           'candidate_sha256': manifest['candidate_sha256'],
                           'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                           'panel_sha256': manifest['panel_sha256'],
                           'baseline_receipt_sha256': manifest['baseline_receipt_sha256'],
                           'fixed_tape_only': True, 'diagnostic_only': True,
                           'worker_count': 1, 'resume_allowed': False,
                           'shared_lock_path': str(SHARED_LOCK)}, stream, indent=2)
                stream.write('\n')
            with RESULTS.open('x', encoding='utf-8', newline='\n') as stream:
                for job in panel['games']:
                    actual = play(job['fixture'], CANDIDATE,
                                  manifest['candidate_sha256'],
                                  int(job['candidate_seat']))
                    checks, errors = telemetry_check(
                        actual, job['expected_gate'], job['baseline_6a_telemetry'],
                        require_baseline=not job['trigger'])
                    baseline = job['baseline_6a']
                    baseline_rank = RANK[baseline['result']]
                    actual_rank = RANK[actual['result']]
                    row = {
                        'fixture_id': job['fixture_id'],
                        'candidate_seat': int(job['candidate_seat']),
                        'panel': job['panel'], 'trigger': job['trigger'],
                        'candidate_sha256': manifest['candidate_sha256'],
                        'clean_done_done_720': clean(actual),
                        'telemetry_checks': checks, 'telemetry_errors': errors,
                        'telemetry_passed': all(checks.values()),
                        'baseline_6a': baseline,
                        'actual': actual,
                        'baseline_result_rank': baseline_rank,
                        'candidate_result_rank': actual_rank,
                        'no_outcome_regression': actual_rank >= baseline_rank,
                        'target_win': (actual['result'] == 'win' and actual['margin'] > 0)
                            if job['trigger'] else None,
                        'delta_margin_vs_6a': actual['margin'] - baseline['margin'],
                    }
                    rows.append(row)
                    stream.write(json.dumps(row, ensure_ascii=True, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({key: row[key] for key in (
                        'fixture_id', 'candidate_seat', 'panel', 'trigger',
                        'clean_done_done_720', 'telemetry_passed',
                        'no_outcome_regression', 'target_win')}
                        | {'result': actual['result'], 'margin': actual['margin']},
                        ensure_ascii=True), flush=True)

                for job in panel['controls']:
                    fixture = job['fixture']
                    seat = int(job['seat'])
                    parent_actual = play(fixture, PARENT,
                                         manifest['parent_candidate_sha256'], seat)
                    candidate_actual = play(fixture, CANDIDATE,
                                            manifest['candidate_sha256'], seat)
                    candidate_checks, candidate_errors = telemetry_check(
                        candidate_actual, {
                            'leaf': 'PET_CAFE|M8+|C>S|G0',
                            'rival_visible_melon_count': 12,
                            'public_wheat_inventory': 9975,
                            'active': True, 'route': '113517834',
                            'active_calls': 647,
                        })
                    parent_errors = {key: value for key, value in
                                     (parent_actual.get('candidate_telemetry') or {}).items()
                                     if ('error' in key.lower() or 'collision' in key.lower())
                                     and value not in (0, False, None, '')}
                    parent_clean = clean(parent_actual) and not parent_errors
                    candidate_clean = clean(candidate_actual)
                    row = {
                        'fixture_id': job['fixture_id'], 'seat': seat,
                        'role': 'historical_public_win_control',
                        'candidate_sha256': manifest['candidate_sha256'],
                        'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                        'parent_clean_done_done_720': parent_clean,
                        'candidate_clean_done_done_720': candidate_clean,
                        'parent_telemetry_errors': parent_errors,
                        'candidate_telemetry_checks': candidate_checks,
                        'candidate_telemetry_errors': candidate_errors,
                        'candidate_telemetry_passed': all(candidate_checks.values()),
                        'parent': {field: parent_actual.get(field) for field in FIELDS},
                        'candidate': {field: candidate_actual.get(field) for field in FIELDS},
                        'parent_control_win': parent_actual.get('result') == 'win',
                        'candidate_control_win': candidate_actual.get('result') == 'win',
                        'delta_margin_report_only': candidate_actual['margin'] - parent_actual['margin'],
                    }
                    rows.append(row)
                    stream.write(json.dumps(row, ensure_ascii=True, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({key: row[key] for key in (
                        'fixture_id', 'seat', 'role', 'parent_clean_done_done_720',
                        'candidate_clean_done_done_720', 'candidate_telemetry_passed',
                        'parent_control_win', 'candidate_control_win',
                        'delta_margin_report_only')}, ensure_ascii=True), flush=True)

    full_rows = [row for row in rows if 'panel' in row]
    control_rows = [row for row in rows if row.get('role') == 'historical_public_win_control']
    by_key = {(row['fixture_id'], row['candidate_seat']): row for row in full_rows}
    loss_ids = sorted({row['fixture_id'] for row in full_rows if row['panel'] == 'loss30'})
    top_ids = sorted({row['fixture_id'] for row in full_rows if row['panel'] == 'top20'})
    loss_sweeps = sum(all(by_key[(fid, seat)]['actual']['result'] == 'win' for seat in (0, 1))
                      for fid in loss_ids)
    top_sweeps = sum(all(by_key[(fid, seat)]['actual']['result'] == 'win' for seat in (0, 1))
                     for fid in top_ids)
    targets = [row for row in full_rows if row['trigger']]
    controls_exact = len(control_rows) == 2 and all(
        row['parent_control_win'] and row['candidate_control_win'] for row in control_rows)
    clean_all = (len(full_rows) == 100 and len(control_rows) == 2
                 and all(row['clean_done_done_720'] for row in full_rows)
                 and all(row['parent_clean_done_done_720'] and row['candidate_clean_done_done_720']
                         for row in control_rows))
    telemetry_all = (len(full_rows) == 100 and len(control_rows) == 2
                     and all(row['telemetry_passed'] for row in full_rows)
                     and all(row['candidate_telemetry_passed'] for row in control_rows))
    no_regressions = len(full_rows) == 100 and all(row['no_outcome_regression'] for row in full_rows)
    loss_goal = len(loss_ids) == 30 and loss_sweeps >= 27
    top_goal = len(top_ids) == 20 and top_sweeps >= 18
    targets_win = len(targets) == 2 and all(row['target_win'] for row in targets)
    receipt = {
        'schema': 'pet-market-6a-100-seat-plus-control-outcome-v1',
        'complete': len(full_rows) == 100 and len(control_rows) == 2,
        'diagnostic_only': True, 'fixed_tape_only': True,
        'reactive_validation': False, 'promotion': False,
        'candidate_sha256': manifest['candidate_sha256'],
        'parent_candidate_sha256': manifest['parent_candidate_sha256'],
        'panel_sha256': manifest['panel_sha256'],
        'baseline_receipt_sha256': manifest['baseline_receipt_sha256'],
        'games': rows, 'full_panel_game_count': len(full_rows),
        'control_fixture_seats': len(control_rows),
        'native_game_runs': len(full_rows) + 2 * len(control_rows),
        'all_runs_clean_done_done_720': clean_all,
        'all_candidate_telemetry_passed': telemetry_all,
        'no_per_seat_outcome_regressions_vs_6a': no_regressions,
        'both_114260122_target_seats_win': targets_win,
        'loss30_fixture_count': len(loss_ids), 'loss30_winning_sweeps': loss_sweeps,
        'loss30_goal_27_of_30': loss_goal,
        'top20_fixture_count': len(top_ids), 'top20_winning_sweeps': top_sweeps,
        'top20_goal_18_of_20': top_goal,
        'both_114192390_parent_and_candidate_controls_win': controls_exact,
        'control_margins_are_report_only': True,
        'passed': (clean_all and telemetry_all and no_regressions and targets_win
                   and loss_goal and top_goal and controls_exact),
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
