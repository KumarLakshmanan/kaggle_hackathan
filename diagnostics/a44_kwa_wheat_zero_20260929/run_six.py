"""One-shot sequential six-game fixed-tape diagnostic; refuses every resume."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import sys


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.stream_replay_io_20260928.fast_game_cached import play


RUN_ID = 'kwa_wheat_zero_six_game_001'
WORKERS = 1
RUN_DIR = HERE / 'runs' / 'six_game_run_001'
SHARED_LOCK_PATH = ROOT / 'diagnostics' / '.shared_game_run.lock'
EXPECTED_PARENT_SHA256 = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
EXPECTED_FIXTURES = ('live-114227779', 'live-114236633', 'live-114257327')
EXPECTED_SEATS = (0, 1)
CONTROL_FIELDS = (
    'result', 'margin', 'candidate_reward', 'opponent_reward',
    'candidate_status', 'opponent_status', 'frames',
)
REQUIRED_FILES = ('run_manifest.json', 'attempts.jsonl', 'outcomes.jsonl', 'outcome_receipt.json')


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def append_jsonl(path: Path, value: dict) -> None:
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8')
    with path.open('ab') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_once(path: Path, value: dict) -> None:
    data = (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def expected_inputs() -> dict:
    manifest = read_json(HERE / 'manifest.json')
    return {name: ROOT / Path(relative) for name, relative in manifest['bound_input_paths'].items()}


def verify_frozen() -> tuple[dict, dict, dict]:
    manifest_path = HERE / 'manifest.json'
    manifest = read_json(manifest_path)
    candidate_path = HERE / 'candidate.py'
    panel_path = HERE / 'target_panel.json'
    assert manifest['diagnostic_only'] and manifest['static_freeze_only']
    assert manifest['runner']['workers'] == WORKERS
    assert manifest['runner']['resume_allowed'] is False
    assert manifest['runner']['shared_lock_path'] == 'diagnostics/.shared_game_run.lock'
    assert manifest['runner']['append_only_receipts'] == ['attempts.jsonl', 'outcomes.jsonl']
    assert manifest['parent_candidate']['sha256'] == EXPECTED_PARENT_SHA256
    assert manifest['outcome_gates_frozen_before_run'] == {
        'all_six_games_done_done_720_clean': True,
        'kwa_both_seats_win_and_positive_margin': True,
        'kwa_both_seats_delta_margin_positive_vs_exact_6d_combined': True,
        'kwa_both_seats_route_113535489_and_647_active_turns': True,
        'four_wheat_positive_controls_do_not_activate': True,
        'four_controls_exact_match_6d_combined_outcomes': list(CONTROL_FIELDS),
    }
    assert sha256(candidate_path) == manifest['candidate_sha256']
    assert sha256(panel_path) == manifest['package_bindings']['target_panel.json']
    for name, digest in manifest['bound_inputs'].items():
        path = expected_inputs()[name]
        assert path.is_file() and sha256(path) == digest, name
    package_files = {
        'candidate.py': HERE / 'candidate.py',
        'wheat_zero_layer.py': HERE / 'wheat_zero_layer.py',
        'build_candidate.py': HERE / 'build_candidate.py',
        'static_preflight.py': HERE / 'static_preflight.py',
        'run_six.py': HERE / 'run_six.py',
        'target_panel.json': panel_path,
        'PLAN.md': HERE / 'PLAN.md',
    }
    for name, path in package_files.items():
        assert sha256(path) == manifest['package_bindings'][name], name
    preflight_path = HERE / 'preflight.json'
    preflight = read_json(preflight_path)
    assert preflight['complete'] and preflight['static_only']
    assert preflight['agent_calls'] == 0 and preflight['game_transitions'] == 0
    assert preflight['candidate_sha256'] == manifest['candidate_sha256']
    assert preflight['manifest_sha256'] == sha256(manifest_path)
    assert preflight['six_game_runner_static_proof']['runner_invocations'] == 0

    panel = read_json(panel_path)
    assert panel['complete'] and panel['workers'] == WORKERS
    assert panel['parent_6d_candidate_sha256'] == EXPECTED_PARENT_SHA256
    assert panel['fixture_ids'] == list(EXPECTED_FIXTURES)
    assert panel['seats'] == list(EXPECTED_SEATS)
    assert len(panel['fixtures']) == 3 and len(panel['jobs']) == 6
    assert [(job['fixture_id'], job['seat']) for job in panel['jobs']] == [
        (fixture_id, seat) for fixture_id in EXPECTED_FIXTURES for seat in EXPECTED_SEATS
    ]

    combined_path = expected_inputs()['parent_combined_results']
    combined = read_json(combined_path)
    assert combined['complete'] and combined['candidate_sha256'] == EXPECTED_PARENT_SHA256
    assert combined['panel_sha256'] == panel['parent_panel_sha256']
    rows = {(row['fixture_id'], int(row['candidate_seat'])): row for row in combined['games']}
    assert len(rows) == len(combined['games']) == 208
    for job in panel['jobs']:
        row = rows[(job['fixture_id'], job['seat'])]
        expected = job['baseline_6d']
        for field in expected:
            assert row.get(field) == expected[field], (job['fixture_id'], job['seat'], field)
    return manifest, panel, rows


def gate_result(row: dict, job: dict, baseline: dict) -> dict:
    telemetry = row.get('candidate_telemetry', {})
    errors = row.get('candidate_errors', {})
    target = job['expected_trigger']
    active = telemetry.get('a44_kwa_wheat_zero_active72') is True
    route = telemetry.get('a44_kwa_wheat_zero_route72', '')
    clean = (
        row.get('candidate_status') == 'DONE'
        and row.get('opponent_status') == 'DONE'
        and row.get('frames') == 720
        and not errors
    )
    telemetry_checks = {
        'source_branch': telemetry.get('a44_kwa_wheat_zero_branch72') == 'source',
        'public_key': telemetry.get('a44_kwa_wheat_zero_key72') == job['expected_public_key'],
        'rival_wheat_plots': telemetry.get('a44_kwa_wheat_zero_rival_wheat_plots72')
                             == job['expected_rival_wheat_plots'],
        'trigger_state': active == target,
        'route': route == job['expected_route'],
        'turn_count': telemetry.get('a44_kwa_wheat_zero_turns') == (647 if target else 0),
        'wrapper_errors': telemetry.get('a44_kwa_wheat_zero_errors', 0) == 0,
    }
    control_equal = all(row.get(field) == baseline.get(field) for field in CONTROL_FIELDS)
    if target:
        target_outcome = (
            row.get('result') == 'win'
            and float(row.get('margin', 0)) > 0
            and float(row.get('margin', 0)) - float(baseline.get('margin', 0)) > 0
        )
    else:
        target_outcome = True
    return {
        'clean': clean,
        'telemetry': telemetry_checks,
        'control_exact_6d_outcome_match': control_equal if not target else None,
        'kwa_target_win_positive_margin_and_positive_delta': target_outcome if target else None,
        'passed': clean and all(telemetry_checks.values())
                  and (control_equal if not target else target_outcome),
    }


def run_once() -> dict:
    if RUN_DIR.exists():
        raise SystemExit(f'run directory already exists; resume is forbidden: {RUN_DIR}')
    manifest, panel, baselines = verify_frozen()
    RUN_DIR.parent.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=False, exist_ok=False)
    assert not any((RUN_DIR / name).exists() for name in REQUIRED_FILES)

    run_manifest = {
        'run_id': RUN_ID,
        'diagnostic_only': True,
        'fixed_tape_only': True,
        'workers': WORKERS,
        'candidate_sha256': manifest['candidate_sha256'],
        'parent_6d_candidate_sha256': EXPECTED_PARENT_SHA256,
        'manifest_sha256': sha256(HERE / 'manifest.json'),
        'runner_sha256': sha256(HERE / 'run_six.py'),
        'target_panel_sha256': sha256(HERE / 'target_panel.json'),
        'static_preflight_receipt_sha256': sha256(HERE / 'preflight.json'),
        'parent_combined_results_sha256': panel['parent_combined_results_sha256'],
        'shared_lock_path': str(SHARED_LOCK_PATH),
        'jobs': panel['jobs'],
        'outcome_gates_frozen_before_run': manifest['outcome_gates_frozen_before_run'],
        'resume_allowed': False,
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    write_once(RUN_DIR / 'run_manifest.json', run_manifest)
    for name in ('attempts.jsonl', 'outcomes.jsonl'):
        with (RUN_DIR / name).open('xb'):
            pass

    candidate_path = HERE / 'candidate.py'
    candidate_sha = manifest['candidate_sha256']
    outcome_rows = []
    for index, job in enumerate(panel['jobs'], start=1):
        key = (job['fixture_id'], int(job['seat']))
        fixture = next(item for item in panel['fixtures'] if item['fixture_id'] == job['fixture_id'])
        baseline = baselines[key]
        append_jsonl(RUN_DIR / 'attempts.jsonl', {
            'event': 'job_started', 'run_id': RUN_ID, 'job_index': index,
            'fixture_id': key[0], 'seat': key[1],
            'started_at_utc': datetime.now(timezone.utc).isoformat(),
        })
        try:
            row = play(fixture, candidate_path, candidate_sha, key[1])
        except BaseException as exc:
            append_jsonl(RUN_DIR / 'attempts.jsonl', {
                'event': 'job_failed', 'run_id': RUN_ID, 'job_index': index,
                'fixture_id': key[0], 'seat': key[1],
                'exception_type': type(exc).__name__,
                'exception': str(exc),
                'failed_at_utc': datetime.now(timezone.utc).isoformat(),
            })
            raise
        row.update(
            run_id=RUN_ID,
            fixture_id=key[0],
            candidate_seat=key[1],
            panel=job['panel'],
            candidate_sha256=candidate_sha,
            parent_6d_candidate_sha256=EXPECTED_PARENT_SHA256,
            parent_6d_baseline=job['baseline_6d'],
            delta_margin=float(row['margin']) - float(baseline['margin']),
            outcome_gates=gate_result(row, job, baseline),
        )
        append_jsonl(RUN_DIR / 'outcomes.jsonl', row)
        append_jsonl(RUN_DIR / 'attempts.jsonl', {
            'event': 'job_finished', 'run_id': RUN_ID, 'job_index': index,
            'fixture_id': key[0], 'seat': key[1],
            'result': row.get('result'), 'margin': row.get('margin'),
            'gates_passed': row['outcome_gates']['passed'],
            'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        })
        outcome_rows.append(row)
        print('kwa_wheat_zero_six_game', index, '/ 6', key[0], key[1],
              row.get('result'), row.get('margin'),
              'gates', row['outcome_gates']['passed'], flush=True)

    assert len(outcome_rows) == 6
    assert {(r['fixture_id'], int(r['candidate_seat'])) for r in outcome_rows}
    assert all((r['fixture_id'], int(r['candidate_seat'])) ==
               (j['fixture_id'], j['seat']) for r, j in zip(outcome_rows, panel['jobs']))
    summary = {
        'complete': True,
        'diagnostic_only': True,
        'fixed_tape_only': True,
        'promotion': False,
        'run_id': RUN_ID,
        'candidate_sha256': candidate_sha,
        'parent_6d_candidate_sha256': EXPECTED_PARENT_SHA256,
        'manifest_sha256': sha256(HERE / 'manifest.json'),
        'runner_sha256': sha256(HERE / 'run_six.py'),
        'target_panel_sha256': sha256(HERE / 'target_panel.json'),
        'static_preflight_receipt_sha256': sha256(HERE / 'preflight.json'),
        'all_games_clean': all(row['outcome_gates']['clean'] for row in outcome_rows),
        'all_outcome_gates_passed': all(row['outcome_gates']['passed'] for row in outcome_rows),
        'games': [{
            'fixture_id': row['fixture_id'],
            'seat': row['candidate_seat'],
            'result': row.get('result'),
            'margin': row.get('margin'),
            'delta_margin_vs_6d': row.get('delta_margin'),
            'gates_passed': row['outcome_gates']['passed'],
        } for row in outcome_rows],
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    write_once(RUN_DIR / 'outcome_receipt.json', summary)
    return summary


def main() -> None:
    if RUN_DIR.exists():
        raise SystemExit(f'run directory already exists; no-resume policy: {RUN_DIR}')
    if not SHARED_LOCK_PATH.parent.is_dir():
        raise SystemExit(f'shared lock directory missing: {SHARED_LOCK_PATH.parent}')
    with exclusive_run(SHARED_LOCK_PATH):
        if RUN_DIR.exists():
            raise SystemExit(f'run directory appeared while waiting for lock: {RUN_DIR}')
        result = run_once()
        print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 1:
        raise SystemExit('This frozen one-shot runner accepts no arguments or resume mode.')
    main()
