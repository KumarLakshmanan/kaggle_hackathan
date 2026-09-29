"""One-shot fixed-tape outcome runner for the Ghost wheat derivative.
Run only after root review and shared-lock coordination. Never resumes outputs.
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GHOST = ROOT / 'diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929'
BASE6 = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
CACHE_DIR = ROOT / 'diagnostics/stream_replay_io_20260928'
CANDIDATE = GHOST / 'candidate.py'
PANEL_PATH = HERE / 'panel.json'
MANIFEST_PATH = HERE / 'frozen_manifest.json'
PREFLIGHT_PATH = HERE / 'preflight.json'
RESULTS_PATH = HERE / 'candidate.jsonl'
RECEIPT_PATH = HERE / 'run_receipt.json'
OWN_LOCK_PATH = HERE / 'run.lock'
SHARED_LOCK_PATH = ROOT / 'diagnostics/.shared_game_run.lock'
CANDIDATE_SHA = '228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767'
PARENT_CANDIDATE_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
GOOSE4_SHA = 'c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632'
A44_SHA = 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
GHOST_PREFLIGHT_SHA = 'aefa68e3126e9eb6554cdfe426d023953e90524a72f8da49c4986240c6f801fc'
GHOST_MANIFEST_SHA = '3a3cd881a7d2972e93c57dbc747ff16ca0c335b773b3ebafaa7f63eb440aa4d2'
GHOST_PANEL_SHA = '545c038fb0ab95530a53e58847e23233ddc3a0202fc36dae72f500ef185cbbf6'
BASE6_RESULTS_SHA = '5463a0efa37aebad2c11559cbcd2c39bf2a9a63ec5b2279f409d6360c61ff40d'
BASE6_PARENT_PANEL_SHA = '7407b5f610457d2c00837a3c82e51ae2deaa225b20f2145e01dfaa92dba1db51'
ICE_KEY = 'ICE_CREAM_SHOP|M8+|C>S|G0'
FIXTURE_ORDER = (
    'live-114255779', 'live-114258293', 'live-114288168',
    'public-win-114209881', 'public-win-114221853', 'public-win-114245470',
)
EXPECTED_BASELINE_FIELDS = ('result', 'candidate_reward', 'opponent_reward', 'margin')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def key(path):
    return str(Path(path).resolve())


def assert_absent_outputs():
    existing = [str(path) for path in (RESULTS_PATH, RECEIPT_PATH) if path.exists()]
    if existing:
        raise FileExistsError(f'outcome files already exist; this runner never resumes: {existing}')


def verify_frozen_package():
    manifest = load(MANIFEST_PATH)
    if not (manifest.get('complete') is True and manifest.get('diagnostic_only') is True
            and manifest.get('fixed_tape_only') is True and manifest.get('promotion') is False
            and manifest.get('reactive_validation') is False
            and manifest.get('experiment_completed') is False
            and manifest.get('outcome_games_run') == 0
            and manifest.get('candidate_sha256') == CANDIDATE_SHA
            and manifest.get('parent_candidate_sha256') == PARENT_CANDIDATE_SHA
            and manifest.get('goose4_candidate_sha256') == GOOSE4_SHA
            and manifest.get('source_a44_sha256') == A44_SHA
            and manifest.get('ghost_preflight_sha256') == GHOST_PREFLIGHT_SHA
            and manifest.get('ghost_static_manifest_sha256') == GHOST_MANIFEST_SHA
            and manifest.get('accepted_combined_results_sha256') == BASE6_RESULTS_SHA
            and manifest.get('parent_panel_sha256') == BASE6_PARENT_PANEL_SHA):
        raise ValueError('frozen manifest does not match the reviewed experiment')
    bindings = manifest.get('bindings')
    if not isinstance(bindings, dict) or len(bindings) != manifest.get('binding_count'):
        raise ValueError('frozen manifest bindings are missing or malformed')
    mismatches = []
    for path, expected in bindings.items():
        actual_path = Path(path)
        if not actual_path.is_file():
            mismatches.append((path, 'missing', expected))
        else:
            actual = sha(actual_path)
            if actual != expected:
                mismatches.append((path, actual, expected))
    if mismatches:
        raise ValueError(f'frozen binding mismatches: {mismatches[:8]}')

    required = {
        CANDIDATE: CANDIDATE_SHA,
        GHOST / 'preflight.json': GHOST_PREFLIGHT_SHA,
        GHOST / 'frozen_manifest.json': GHOST_MANIFEST_SHA,
        GHOST / 'panel.json': GHOST_PANEL_SHA,
        BASE6 / 'candidate.py': PARENT_CANDIDATE_SHA,
        BASE6 / 'combined_results.json': BASE6_RESULTS_SHA,
        BASE6 / 'parent_panel.json': BASE6_PARENT_PANEL_SHA,
        HERE / 'panel.json': GHOST_PANEL_SHA,
        HERE / 'run.py': manifest.get('runner_sha256'),
        HERE / 'PLAN.md': manifest.get('plan_sha256'),
        HERE / 'preflight.py': manifest.get('preflight_builder_sha256'),
        PREFLIGHT_PATH: manifest.get('static_preflight_sha256'),
    }
    for path, expected in required.items():
        actual = sha(path)
        if not expected or actual != expected or bindings.get(key(path)) != actual:
            raise ValueError(f'required binding mismatch: {path} {actual} != {expected}')

    receipt = load(PREFLIGHT_PATH)
    if not (receipt.get('passed') is True and receipt.get('static_only') is True
            and receipt.get('experiment_completed') is False
            and receipt.get('outcome_games_run') == 0
            and receipt.get('engine_transitions') == 0
            and receipt.get('policy_action_calls') == 0
            and receipt.get('candidate_sha256') == CANDIDATE_SHA
            and receipt.get('parent_candidate_sha256') == PARENT_CANDIDATE_SHA
            and receipt.get('source_a44_sha256') == A44_SHA
            and receipt.get('fixed_tape_only') is True
            and receipt.get('reactive_validation') is False):
        raise ValueError('outcome static preflight receipt did not pass or reports a game run')
    if receipt.get('bindings') != {p: h for p, h in bindings.items() if p != key(PREFLIGHT_PATH)}:
        raise ValueError('static preflight binding census differs from the frozen manifest')

    panel = load(PANEL_PATH)
    ghost_panel = load(GHOST / 'panel.json')
    if panel != ghost_panel or panel.get('candidate_sha256') != CANDIDATE_SHA:
        raise ValueError('outcome panel is not the exact Ghost derivative panel')
    if (panel.get('accepted_combined_results_sha256') != BASE6_RESULTS_SHA
            or panel.get('full_panel_sha256') != BASE6_PARENT_PANEL_SHA
            or len(panel.get('games', [])) != 12):
        raise ValueError('outcome panel baseline or row count changed')

    combined = load(BASE6 / 'combined_results.json')
    parent_panel = load(BASE6 / 'parent_panel.json')
    if (combined.get('complete') is not True or combined.get('candidate_sha256') != PARENT_CANDIDATE_SHA
            or combined.get('panel_sha256') != BASE6_PARENT_PANEL_SHA
            or len(combined.get('games', [])) != 208):
        raise ValueError('6d combined baseline is not complete or is misbound')
    base_rows = {(r['fixture_id'], int(r['candidate_seat'])): r for r in combined['games']}
    if len(base_rows) != 208:
        raise ValueError('6d combined results contain duplicate fixture/seat rows')
    fixtures = {r['fixture_id']: r for r in parent_panel['fixtures']}
    if len(fixtures) != 104:
        raise ValueError('104-fixture parent panel is malformed')

    rows = panel['games']
    expected = [(fixture_id, seat) for fixture_id in FIXTURE_ORDER for seat in (0, 1)]
    actual = [(r['fixture_id'], int(r['candidate_seat'])) for r in rows]
    if actual != expected:
        raise ValueError('outcome rows differ from frozen order')
    triggered = []
    for row in rows:
        fixture_id, seat = row['fixture_id'], int(row['candidate_seat'])
        fixture = fixtures.get(fixture_id)
        base = base_rows.get((fixture_id, seat))
        if fixture is None or base is None:
            raise ValueError(f'fixture or exact 6d baseline row missing: {fixture_id}/{seat}')
        if not base.get('decision_equivalence_reuse') or base.get('candidate_sha256') != GOOSE4_SHA:
            raise ValueError(f'baseline row is not the exact accepted source parent reuse: {fixture_id}/{seat}')
        if (row.get('accepted_6d_result') != base.get('result')
                or float(row.get('accepted_6d_margin')) != float(base.get('margin'))
                or row.get('accepted_6d_result_row_candidate_sha256') != base.get('candidate_sha256')):
            raise ValueError(f'panel 6d result differs from combined receipt: {fixture_id}/{seat}')
        if row.get('source_trace_sha256') != bindings.get(key(row['source_trace_path'])):
            raise ValueError(f'step-72 feature trace is not frozen: {fixture_id}/{seat}')
        if row.get('step72_branch') != 'source' or row.get('step72_public_key') != ICE_KEY:
            raise ValueError(f'public step-72 key/branch changed: {fixture_id}/{seat}')
        expected_trigger = fixture_id == 'live-114288168'
        if bool(row.get('expected_trigger')) != expected_trigger:
            raise ValueError(f'trigger census changed: {fixture_id}/{seat}')
        expected_route = 113360743 if expected_trigger else 113470868
        if (row.get('expected_derivative_route') != expected_route
                or row.get('expected_parent_goose4_route') != 113470868
                or (int(row['step72_public_wheat']) <= 9975) != expected_trigger):
            raise ValueError(f'public threshold/route changed: {fixture_id}/{seat}')
        if fixture['source_replay_sha256'] == '' or fixture['source_opponent_action_sha256'] == '':
            raise ValueError(f'source fixture input metadata absent: {fixture_id}')
        if expected_trigger:
            triggered.append((fixture_id, seat))
    if triggered != [('live-114288168', 0), ('live-114288168', 1)]:
        raise ValueError('exactly both Ghost seats must be the only activations')
    return manifest, receipt, panel, fixtures, base_rows


def telemetry_checks(row, expected_trigger):
    t = row.get('candidate_telemetry') or {}
    source = {
        'a44_ghost_wheat_branch72': 'source',
        'a44_ghost_wheat_key72': ICE_KEY,
        'a44_ghost_wheat_checked72': True,
        'a44_ghost_wheat_stock72': int(row['step72_public_wheat']),
        'a44_ghost_wheat_active72': bool(expected_trigger),
        'a44_ghost_wheat_route72': str(row['expected_derivative_route']),
        'a44_goose4_branch72': 'source',
        'a44_goose4_key72': ICE_KEY,
        'a44_goose4_route': str(row['expected_derivative_route']),
        'a44_goose4_turns': 647,
        'a44_goose4_errors': 0,
        'bridge_errors': 0,
    }
    return {name: {'expected': value, 'actual': t.get(name), 'passed': t.get(name) == value}
            for name, value in source.items()}


def execute_outcomes(panel, fixtures, base_rows):
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run

    with exclusive_run(SHARED_LOCK_PATH):
        with exclusive_run(OWN_LOCK_PATH):
            assert_absent_outputs()
            verify_frozen_package()
            # Importing the native harness is deferred until the shared and local locks are both held.
            from diagnostics.stream_replay_io_20260928.fast_game_cached import play

            completed = []
            with RESULTS_PATH.open('x', encoding='utf-8', newline='\n') as stream:
                for panel_row in panel['games']:
                    fixture_id = panel_row['fixture_id']
                    seat = int(panel_row['candidate_seat'])
                    fixture = fixtures[fixture_id]
                    baseline = base_rows[(fixture_id, seat)]
                    actual = play(fixture, CANDIDATE, CANDIDATE_SHA, seat, trace_path=None)
                    expected_trigger = bool(panel_row['expected_trigger'])
                    checks = telemetry_checks(panel_row, expected_trigger)
                    clean = (actual.get('candidate_status') == 'DONE'
                             and actual.get('opponent_status') == 'DONE'
                             and actual.get('frames') == 720
                             and not actual.get('candidate_errors'))
                    telemetry_passed = all(item['passed'] for item in checks.values())
                    exact_baseline = {name: actual.get(name) == baseline.get(name)
                                      for name in EXPECTED_BASELINE_FIELDS}
                    control_exact = (not expected_trigger and all(exact_baseline.values()))
                    ghost_win = (expected_trigger and actual.get('result') == 'win')
                    record = dict(
                        fixture_id=fixture_id,
                        candidate_seat=seat,
                        expected_trigger=expected_trigger,
                        candidate_sha256=CANDIDATE_SHA,
                        clean=clean,
                        telemetry_checks=checks,
                        telemetry_passed=telemetry_passed,
                        exact_6d_baseline=baseline,
                        exact_6d_field_checks=exact_baseline,
                        false_trigger_control_exact=control_exact,
                        ghost_target_win=ghost_win,
                        result=actual,
                    )
                    completed.append(record)
                    stream.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({k: record[k] for k in ('fixture_id', 'candidate_seat',
                                   'expected_trigger', 'clean', 'telemetry_passed',
                                   'false_trigger_control_exact', 'ghost_target_win', 'result')
                                      if k != 'result'} | {
                                          'result': actual.get('result'),
                                          'margin': actual.get('margin')}, ensure_ascii=False), flush=True)

            clean_all = len(completed) == 12 and all(r['clean'] for r in completed)
            telemetry_all = len(completed) == 12 and all(r['telemetry_passed'] for r in completed)
            ghost_wins = [r for r in completed if r['expected_trigger']]
            ghost_both_win = (len(ghost_wins) == 2 and all(r['ghost_target_win'] for r in ghost_wins))
            controls = [r for r in completed if not r['expected_trigger']]
            controls_exact = (len(controls) == 10 and all(r['false_trigger_control_exact'] for r in controls))
            gate_failures = []
            if not clean_all: gate_failures.append('not all 12 games clean DONE/DONE/720')
            if not telemetry_all: gate_failures.append('expected public-step-72 telemetry did not match')
            if not ghost_both_win: gate_failures.append('both live-114288168 seats did not win')
            if not controls_exact: gate_failures.append('one or more of ten false-trigger controls changed 6d result/rewards/margin')
            receipt = dict(
                schema='ghost-wheat-outcome-run-receipt/v1',
                complete=len(completed) == 12,
                diagnostic_only=True,
                fixed_tape_only=True,
                reactive_validation=False,
                promotion=False,
                candidate_sha256=CANDIDATE_SHA,
                parent_candidate_sha256=PARENT_CANDIDATE_SHA,
                source_a44_sha256=A44_SHA,
                accepted_combined_results_sha256=BASE6_RESULTS_SHA,
                parent_panel_sha256=BASE6_PARENT_PANEL_SHA,
                game_count=len(completed),
                clean_12=clean_all,
                telemetry_12=telemetry_all,
                ghost_both_seats_win=ghost_both_win,
                false_trigger_controls_exact=controls_exact,
                gate_passed=not gate_failures,
                gate_failures=gate_failures,
                games=completed,
                evidence_note='Saved opponent action tapes and pure native transitions; not reactive validation or promotion evidence.',
            )
            with RECEIPT_PATH.open('x', encoding='utf-8', newline='\n') as out:
                out.write(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
            print(json.dumps({k: receipt[k] for k in ('complete', 'game_count', 'clean_12',
                          'telemetry_12', 'ghost_both_seats_win', 'false_trigger_controls_exact',
                          'gate_passed', 'gate_failures', 'promotion', 'reactive_validation')}, indent=2))
            return 0 if receipt['gate_passed'] else 1


def main():
    if len(sys.argv) != 1:
        raise SystemExit('This frozen runner accepts no arguments and never resumes.')
    assert_absent_outputs()
    package = verify_frozen_package()
    return execute_outcomes(package[2], package[3], package[4])


if __name__ == '__main__':
    raise SystemExit(main())
