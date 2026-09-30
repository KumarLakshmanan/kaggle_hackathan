"""One-shot native fixed-tape outcome runner for the Ghost + Kwa candidate."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
COMBO = HERE.parent
BASE6 = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
CANDIDATE = COMBO / 'candidate_v4.py'
PANEL_PATH = COMBO / 'panel_v4.json'
MANIFEST_PATH = HERE / 'frozen_manifest.json'
PREFLIGHT_PATH = HERE / 'static_preflight.json'
RESULTS_PATH = HERE / 'outcomes.jsonl'
RECEIPT_PATH = HERE / 'outcome_receipt.json'
RUN_MANIFEST_PATH = HERE / 'run_manifest.json'
OWN_LOCK_PATH = HERE / 'run.lock'
SHARED_LOCK_PATH = ROOT / 'diagnostics/.shared_game_run.lock'
EXPECTED_CANDIDATE_SHA = '7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2'
EXPECTED_PANEL_SHA = '8f9eec84d361de731d95de88d76c5e78bf2c6bab58012a376daa5bdf466d15bd'
PARENT_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
KWA_KEY = 'BRUNCH_SPOT|M8+|C<S|G0'
KWA_ROUTE = '113535489'
GHOST_KEY = 'ICE_CREAM_SHOP|M8+|C>S|G0'
GHOST_ROUTE = '113360743'
CONTROL_FIELDS = (
    'result', 'candidate_reward', 'opponent_reward', 'margin',
    'candidate_status', 'opponent_status', 'frames',
)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def outputs_absent():
    existing = [str(path) for path in
                (RESULTS_PATH, RECEIPT_PATH, RUN_MANIFEST_PATH)
                if path.exists()]
    require(not existing, f'runner is one-shot and refuses existing outputs: {existing}')


def verify_frozen():
    manifest = load(MANIFEST_PATH)
    preflight = load(PREFLIGHT_PATH)
    require(manifest.get('complete') is True and manifest.get('diagnostic_only') is True
            and manifest.get('fixed_tape_only') is True and manifest.get('promotion') is False
            and manifest.get('reactive_validation') is False,
            'frozen manifest metadata changed')
    require(manifest.get('candidate_sha256') == EXPECTED_CANDIDATE_SHA
            and sha(CANDIDATE) == EXPECTED_CANDIDATE_SHA,
            'combined candidate hash mismatch')
    require(manifest.get('panel_sha256') == EXPECTED_PANEL_SHA
            and sha(PANEL_PATH) == EXPECTED_PANEL_SHA,
            'combined panel hash mismatch')
    require(manifest.get('parent_6d_candidate_sha256') == PARENT_SHA,
            'exact 6d parent changed')
    bindings = manifest.get('bindings')
    require(isinstance(bindings, dict) and len(bindings) == manifest.get('binding_count'),
            'frozen bindings missing or malformed')
    mismatches = []
    for path_text, expected in bindings.items():
        path = Path(path_text)
        actual = sha(path) if path.is_file() else 'MISSING'
        if actual != expected:
            mismatches.append((path_text, actual, expected))
    require(not mismatches, f'frozen input hash mismatch: {mismatches[:5]}')
    require(manifest.get('runner_sha256') == sha(HERE / 'run.py')
            and manifest.get('preflight_builder_sha256') == sha(HERE / 'preflight.py')
            and manifest.get('plan_sha256') == sha(HERE / 'PLAN.md'),
            'runner, preflight, or plan differs from frozen manifest')
    require(preflight.get('passed') is True and preflight.get('static_only') is True
            and preflight.get('engine_transitions') == 0
            and preflight.get('policy_action_calls') == 0
            and preflight.get('manifest_sha256') == sha(MANIFEST_PATH)
            and preflight.get('runner_sha256') == sha(HERE / 'run.py'),
            'static preflight receipt does not pass or is misbound')

    panel = load(PANEL_PATH)
    require(panel.get('candidate_sha256') == EXPECTED_CANDIDATE_SHA
            and len(panel.get('games', [])) == 58
            and panel.get('fixture_count') == 29
            and panel.get('top20_fixture_count') == 20
            and panel.get('expected_control_seats') == 54
            and panel.get('top20_goal_metric') == 'both-seat fixture sweep'
            and panel.get('top20_min_winning_sweeps') == 18,
            'frozen panel size or counts changed')
    expected_order = [(fixture, seat) for fixture in panel['fixture_order'] for seat in (0, 1)]
    actual_order = [(row['fixture_id'], int(row['candidate_seat'])) for row in panel['games']]
    require(actual_order == expected_order, 'frozen row order changed')
    return manifest, panel


def telemetry_checks(actual, row):
    telemetry = actual.get('candidate_telemetry') or {}
    kwa = bool(row['expected_kwa_trigger'])
    ghost = bool(row['expected_ghost_trigger'])
    branch = row['expected_branch']
    source = branch == 'source'
    route = row.get('expected_parent_route')
    expected_goose_route = (GHOST_ROUTE if ghost else
                            str(route) if source and route is not None else '')
    expected_ghost_route = (expected_goose_route
                            if source and row['expected_key'] == GHOST_KEY else '')
    expected_goose_turns = 647 if expected_goose_route else 0
    expected = {
        'bridge_selected_branch': telemetry.get('bridge_selected') == branch,
        'bridge_errors_zero': telemetry.get('bridge_errors', 0) == 0,
        'kwa_branch': telemetry.get('a44_kwa_wheat_zero_branch72') == branch,
        'kwa_key': telemetry.get('a44_kwa_wheat_zero_key72') == (row['expected_key'] if source else ''),
        'kwa_activation': telemetry.get('a44_kwa_wheat_zero_active72') is kwa,
        'kwa_route': telemetry.get('a44_kwa_wheat_zero_route72') == (KWA_ROUTE if kwa else ''),
        'kwa_turns': telemetry.get('a44_kwa_wheat_zero_turns') == (647 if kwa else 0),
        'kwa_errors_zero': telemetry.get('a44_kwa_wheat_zero_errors', 0) == 0,
        'ghost_branch': telemetry.get('a44_ghost_wheat_branch72') == branch,
        'ghost_key': telemetry.get('a44_ghost_wheat_key72') == (row['expected_key'] if source else ''),
        'ghost_checked': telemetry.get('a44_ghost_wheat_checked72') is source,
            'ghost_activation': telemetry.get('a44_ghost_wheat_active72') is ghost,
        'ghost_route': telemetry.get('a44_ghost_wheat_route72') == expected_ghost_route,
        'goose4_branch': telemetry.get('a44_goose4_branch72') == (branch if source else ''),
        'goose4_key': telemetry.get('a44_goose4_key72') == (row['expected_key'] if source else ''),
        'goose4_route': telemetry.get('a44_goose4_route') == expected_goose_route,
        'goose4_turns': telemetry.get('a44_goose4_turns') == expected_goose_turns,
        'goose4_errors_zero': telemetry.get('a44_goose4_errors', 0) == 0,
    }
    kwa_plots = row['expected_kwa_wheat_plots_telemetry']
    expected['kwa_public_plot_count'] = (
        telemetry.get('a44_kwa_wheat_zero_rival_wheat_plots72') == kwa_plots)
    expected['ghost_stock'] = (
        telemetry.get('a44_ghost_wheat_stock72') == row['expected_ghost_wheat_telemetry'])
    return expected


def run_once():
    outputs_absent()
    manifest, panel = verify_frozen()
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run

    with exclusive_run(SHARED_LOCK_PATH):
        with exclusive_run(OWN_LOCK_PATH):
            outputs_absent()
            manifest, panel = verify_frozen()
            from diagnostics.stream_replay_io_20260928.fast_game_cached import play
            parent_panel = load(BASE6 / 'parent_panel.json')
            combined = load(BASE6 / 'combined_results.json')
            fixtures = {row['fixture_id']: row for row in parent_panel['fixtures']}
            baseline_rows = {(row['fixture_id'], int(row['candidate_seat'])): row
                             for row in combined['games']}
            with RUN_MANIFEST_PATH.open('x', encoding='utf-8', newline='\n') as out:
                json.dump({
                    'run_id': 'a44_ghost_kwa_combo_58seat_001',
                    'started_at_utc': datetime.now(timezone.utc).isoformat(),
                    'candidate_sha256': EXPECTED_CANDIDATE_SHA,
                    'panel_sha256': EXPECTED_PANEL_SHA,
                    'shared_lock_path': str(SHARED_LOCK_PATH),
                    'worker_count': 1,
                    'resume_allowed': False,
                    'diagnostic_only': True,
                    'fixed_tape_only': True,
                }, out, indent=2)
                out.write('\n')
            games = []
            with RESULTS_PATH.open('x', encoding='utf-8', newline='\n') as stream:
                for row in panel['games']:
                    fixture_id = row['fixture_id']
                    seat = int(row['candidate_seat'])
                    actual = play(fixtures[fixture_id], CANDIDATE,
                                  EXPECTED_CANDIDATE_SHA, seat, trace_path=None)
                    telemetry = telemetry_checks(actual, row)
                    clean = (actual.get('candidate_status') == 'DONE'
                             and actual.get('opponent_status') == 'DONE'
                             and actual.get('frames') == 720
                             and not actual.get('candidate_errors')
                             and not actual.get('opponent_errors'))
                    trigger = bool(row['expected_kwa_trigger'] or row['expected_ghost_trigger'])
                    baseline = baseline_rows[(fixture_id, seat)]
                    equal = {field: actual.get(field) == baseline.get(field)
                             for field in CONTROL_FIELDS}
                    target_win = (actual.get('result') == 'win'
                                  and float(actual.get('margin', 0)) > 0)
                    checks_pass = all(telemetry.values())
                    control_exact = not trigger and all(equal.values())
                    target_gate = target_win if trigger else None
                    record = {
                        'fixture_id': fixture_id,
                        'candidate_seat': seat,
                        'expected_kwa_trigger': bool(row['expected_kwa_trigger']),
                        'expected_ghost_trigger': bool(row['expected_ghost_trigger']),
                        'candidate_sha256': EXPECTED_CANDIDATE_SHA,
                        'clean_done_done_720': clean,
                        'telemetry_checks': telemetry,
                        'telemetry_passed': checks_pass,
                        'baseline_6d': {field: baseline.get(field) for field in CONTROL_FIELDS},
                        'actual_6d_field_checks': equal,
                        'control_exact': control_exact,
                        'target_win': target_gate,
                        'actual': actual,
                    }
                    games.append(record)
                    stream.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({key: record[key] for key in (
                        'fixture_id', 'candidate_seat', 'expected_kwa_trigger',
                        'expected_ghost_trigger', 'clean_done_done_720',
                        'telemetry_passed', 'control_exact', 'target_win')}
                        | {'result': actual.get('result'), 'margin': actual.get('margin')},
                        ensure_ascii=False), flush=True)

            targets = [game for game in games if game['expected_kwa_trigger']
                       or game['expected_ghost_trigger']]
            controls = [game for game in games if not game['expected_kwa_trigger']
                        and not game['expected_ghost_trigger']]
            clean_all = len(games) == 58 and all(game['clean_done_done_720'] for game in games)
            telemetry_all = len(games) == 58 and all(game['telemetry_passed'] for game in games)
            kwa_wins = [game for game in games if game['expected_kwa_trigger']]
            ghost_wins = [game for game in games if game['expected_ghost_trigger']]
            control_exact = len(controls) == 54 and all(game['control_exact'] for game in controls)
            targets_win = (len(kwa_wins) == 2 and len(ghost_wins) == 2
                           and all(game['target_win'] for game in kwa_wins + ghost_wins))
            top20_fixture_ids = {
                row['fixture_id'] for row in panel['games'] if row['panel'] == 'top20'}
            top20_results = {}
            for game in games:
                if game['fixture_id'] in top20_fixture_ids:
                    top20_results.setdefault(game['fixture_id'], []).append(game['actual'].get('result'))
            top20_winning_sweeps = sum(len(results) == 2 and all(result == 'win' for result in results)
                                       for results in top20_results.values())
            top20_goal = (len(top20_results) == 20
                          and top20_winning_sweeps >= int(panel['top20_min_winning_sweeps']))
            failures = []
            if not clean_all: failures.append('not all 58 games are clean DONE/DONE/720')
            if not telemetry_all: failures.append('one or more route activation telemetry checks failed')
            if not targets_win: failures.append('Kwa and Ghost target seats did not all win')
            if not control_exact: failures.append('one or more of 54 controls changed from exact 6d results')
            if not top20_goal: failures.append('candidate missed the frozen top20 two-seat sweep threshold')
            receipt = {
                'schema': 'a44-ghost-kwa-combo-fixed-outcome-v1',
                'complete': len(games) == 58,
                'diagnostic_only': True,
                'fixed_tape_only': True,
                'reactive_validation': False,
                'promotion': False,
                'candidate_sha256': EXPECTED_CANDIDATE_SHA,
                'parent_6d_candidate_sha256': PARENT_SHA,
                'panel_sha256': EXPECTED_PANEL_SHA,
                'game_count': len(games),
                'clean_58': clean_all,
                'telemetry_58': telemetry_all,
                'all_four_target_seats_win': targets_win,
                'all_four_activation_rows': len(kwa_wins) + len(ghost_wins) == 4,
                'fifty_four_controls_exact': control_exact,
                'top20_fixture_count': len(top20_results),
                'top20_winning_sweeps': top20_winning_sweeps,
                'top20_at_least_90_percent': top20_goal,
                'passed': not failures,
                'failures': failures,
                'games': games,
                'evidence_limit': 'Fixed replay tapes only; not reactive qualification or promotion evidence.',
                'completed_at_utc': datetime.now(timezone.utc).isoformat(),
            }
            with RECEIPT_PATH.open('x', encoding='utf-8', newline='\n') as out:
                json.dump(receipt, out, ensure_ascii=False, indent=2)
                out.write('\n')
            print(json.dumps({key: receipt[key] for key in (
                'complete', 'game_count', 'clean_58', 'telemetry_58',
                'all_four_target_seats_win', 'fifty_four_controls_exact',
                'top20_winning_sweeps', 'top20_at_least_90_percent', 'passed', 'failures')},
                indent=2), flush=True)
            return 0 if receipt['passed'] else 1


def main():
    if len(sys.argv) != 1:
        raise SystemExit('This runner takes no arguments and never resumes.')
    return run_once()


if __name__ == '__main__':
    raise SystemExit(main())
