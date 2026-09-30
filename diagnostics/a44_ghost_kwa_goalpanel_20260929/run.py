"""One-shot full frozen loss30 run, paired with the prior top20 receipt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
COMBO = ROOT / 'diagnostics/a44_ghost_kwa_combo_20260929'
COMBO_RUN = COMBO / 'outcome_run_20260929'
CANDIDATE = COMBO / 'candidate_v4.py'
PANEL_PATH = HERE / 'panel.json'
MANIFEST_PATH = HERE / 'frozen_manifest.json'
PREFLIGHT_PATH = HERE / 'static_preflight.json'
RESULTS_PATH = HERE / 'outcomes.jsonl'
RECEIPT_PATH = HERE / 'outcome_receipt.json'
RUN_MANIFEST_PATH = HERE / 'run_manifest.json'
OWN_LOCK_PATH = HERE / 'run.lock'
SHARED_LOCK_PATH = ROOT / 'diagnostics/.shared_game_run.lock'
EXPECTED_CANDIDATE_SHA = '7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2'
EXPECTED_PANEL_SHA = 'dd11014aa8b9423a43a5f8fd6bf1af592881b940845d032c406a8d86cc1e6ea7'
TOP20_RECEIPT_SHA = 'c576c106f4e40b009fba58cc2642d73c70571880bd940f75ca3b128a85cc51c9'
BASE6_CANDIDATE_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
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
    present = [str(path) for path in
               (RESULTS_PATH, RECEIPT_PATH, RUN_MANIFEST_PATH)
               if path.exists()]
    require(not present, f'runner is one-shot; output already exists: {present}')


def verify_frozen():
    manifest = load(MANIFEST_PATH)
    static = load(PREFLIGHT_PATH)
    require(manifest.get('complete') is True
            and manifest.get('diagnostic_only') is True
            and manifest.get('fixed_tape_only') is True
            and manifest.get('promotion') is False
            and manifest.get('candidate_sha256') == EXPECTED_CANDIDATE_SHA
            and sha(CANDIDATE) == EXPECTED_CANDIDATE_SHA
            and manifest.get('panel_sha256') == EXPECTED_PANEL_SHA
            and sha(PANEL_PATH) == EXPECTED_PANEL_SHA,
            'frozen candidate or panel mismatch')
    require(manifest.get('binding_count') == len(manifest.get('bindings', {})),
            'frozen binding count mismatch')
    mismatches = []
    for path_text, expected in manifest['bindings'].items():
        path = Path(path_text)
        actual = sha(path) if path.is_file() else 'MISSING'
        if actual != expected:
            mismatches.append((path_text, actual, expected))
    require(not mismatches, f'frozen input hash mismatch: {mismatches[:5]}')
    require(manifest.get('runner_sha256') == sha(HERE / 'run.py')
            and manifest.get('preflight_sha256') == sha(HERE / 'preflight.py')
            and manifest.get('builder_sha256') == sha(HERE / 'build_panel.py')
            and manifest.get('plan_sha256') == sha(HERE / 'PLAN.md'),
            'runner, preflight, builder, or plan changed')
    require(static.get('passed') is True and static.get('static_only') is True
            and static.get('engine_transitions') == 0
            and static.get('policy_action_calls') == 0
            and static.get('outcome_games_run') == 0
            and static.get('manifest_sha256') == sha(MANIFEST_PATH)
            and static.get('runner_sha256') == sha(HERE / 'run.py'),
            'static preflight receipt failed or changed')
    panel = load(PANEL_PATH)
    require(panel.get('candidate_sha256') == EXPECTED_CANDIDATE_SHA
            and panel.get('parent_6d_candidate_sha256') == BASE6_CANDIDATE_SHA
            and panel.get('game_count') == 60
            and panel.get('loss30_fixture_count') == 30
            and panel.get('top20_fixture_count') == 20
            and panel.get('loss30_min_winning_sweeps') == 27
            and panel.get('top20_min_winning_sweeps') == 18
            and panel.get('expected_control_seats') == 56,
            'frozen panel counts or goals changed')
    rows = panel['games']
    order = [(fid, seat) for fid in panel['fixture_order'] for seat in (0, 1)]
    require([(row['fixture_id'], int(row['candidate_seat'])) for row in rows] == order,
            'frozen 60-seat row order changed')
    require(len(set(panel['fixture_order'])) == 30,
            'frozen loss30 fixture list has duplicates')
    return manifest, panel


def run_once():
    outputs_absent()
    verify_frozen()
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    telemetry_checks = runpy.run_path(str(COMBO_RUN / 'run.py'))['telemetry_checks']
    top20_receipt = load(COMBO_RUN / 'outcome_receipt.json')
    require(sha(COMBO_RUN / 'outcome_receipt.json') == TOP20_RECEIPT_SHA
            and top20_receipt.get('candidate_sha256') == EXPECTED_CANDIDATE_SHA
            and top20_receipt.get('passed') is True,
            'prior top20 result is not the frozen passing run')

    with exclusive_run(SHARED_LOCK_PATH):
        with exclusive_run(OWN_LOCK_PATH):
            outputs_absent()
            manifest, panel = verify_frozen()
            from diagnostics.stream_replay_io_20260928.fast_game_cached import play
            parent_panel = load(ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929/parent_panel.json')
            fixtures = {row['fixture_id']: row for row in parent_panel['fixtures']}
            baseline_panel = load(ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929/combined_results.json')
            baseline = {(row['fixture_id'], int(row['candidate_seat'])): row
                        for row in baseline_panel['games']}
            with RUN_MANIFEST_PATH.open('x', encoding='utf-8', newline='\n') as out:
                json.dump({
                    'run_id': 'a44_ghost_kwa_full_loss30_001',
                    'started_at_utc': datetime.now(timezone.utc).isoformat(),
                    'candidate_sha256': EXPECTED_CANDIDATE_SHA,
                    'panel_sha256': EXPECTED_PANEL_SHA,
                    'top20_reference_receipt_sha256': TOP20_RECEIPT_SHA,
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
                    trigger = bool(row['expected_kwa_trigger']
                                   or row['expected_ghost_trigger'])
                    base = baseline[(fixture_id, seat)]
                    exact = {field: actual.get(field) == base.get(field)
                             for field in CONTROL_FIELDS}
                    target_win = (actual.get('result') == 'win'
                                  and float(actual.get('margin', 0)) > 0)
                    record = {
                        'fixture_id': fixture_id,
                        'candidate_seat': seat,
                        'candidate_sha256': EXPECTED_CANDIDATE_SHA,
                        'expected_kwa_trigger': bool(row['expected_kwa_trigger']),
                        'expected_ghost_trigger': bool(row['expected_ghost_trigger']),
                        'clean_done_done_720': clean,
                        'telemetry_checks': telemetry,
                        'telemetry_passed': all(telemetry.values()),
                        'control_exact': not trigger and all(exact.values()),
                        'actual_6d_field_checks': exact,
                        'target_win': target_win if trigger else None,
                        'baseline_6d': {field: base.get(field) for field in CONTROL_FIELDS},
                        'actual': actual,
                    }
                    games.append(record)
                    stream.write(json.dumps(record, ensure_ascii=False,
                                            separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({key: record[key] for key in (
                        'fixture_id', 'candidate_seat', 'expected_kwa_trigger',
                        'expected_ghost_trigger', 'clean_done_done_720',
                        'telemetry_passed', 'control_exact', 'target_win')}
                        | {'result': actual.get('result'), 'margin': actual.get('margin')},
                        ensure_ascii=False), flush=True)

            loss_by_fixture = {}
            for game in games:
                loss_by_fixture.setdefault(game['fixture_id'], []).append(game['actual'].get('result'))
            loss_sweeps = sum(len(results) == 2 and all(value == 'win' for value in results)
                              for results in loss_by_fixture.values())
            targets = [game for game in games if game['expected_kwa_trigger']
                       or game['expected_ghost_trigger']]
            controls = [game for game in games if not game['expected_kwa_trigger']
                        and not game['expected_ghost_trigger']]
            clean_all = len(games) == 60 and all(game['clean_done_done_720'] for game in games)
            telemetry_all = len(games) == 60 and all(game['telemetry_passed'] for game in games)
            target_gate = (len(targets) == 4 and all(game['target_win'] for game in targets))
            controls_gate = len(controls) == 56 and all(game['control_exact'] for game in controls)

            top20_panel = load(COMBO / 'panel_v4.json')
            top20_ids = {row['fixture_id'] for row in top20_panel['games']
                         if row['panel'] == 'top20'}
            top20_game_rows = [game for game in top20_receipt['games']
                               if game['fixture_id'] in top20_ids]
            top20_grouped = {}
            for game in top20_game_rows:
                top20_grouped.setdefault(game['fixture_id'], []).append(game['actual'].get('result'))
            top20_sweeps = sum(len(values) == 2 and all(value == 'win' for value in values)
                               for values in top20_grouped.values())
            top20_gate = (len(top20_grouped) == 20 and top20_sweeps >= 18
                          and top20_receipt.get('passed') is True)
            loss_gate = len(loss_by_fixture) == 30 and loss_sweeps >= 27
            failures = []
            if not clean_all: failures.append('one or more of 60 loss games were not clean DONE/DONE/720')
            if not telemetry_all: failures.append('one or more loss-game telemetry checks failed')
            if not target_gate: failures.append('one or more of four route target seats did not win')
            if not controls_gate: failures.append('one or more of 56 inactive controls changed from 6d')
            if not top20_gate: failures.append('prior top20 reference did not meet 18/20 sweeps')
            if not loss_gate: failures.append('full loss30 result missed the 27/30 sweep goal')
            receipt = {
                'schema': 'a44-ghost-kwa-full-goal-outcome-v1',
                'complete': len(games) == 60,
                'diagnostic_only': True,
                'fixed_tape_only': True,
                'reactive_validation': False,
                'promotion': False,
                'candidate_sha256': EXPECTED_CANDIDATE_SHA,
                'parent_6d_candidate_sha256': BASE6_CANDIDATE_SHA,
                'panel_sha256': EXPECTED_PANEL_SHA,
                'game_count': len(games),
                'clean_60': clean_all,
                'telemetry_60': telemetry_all,
                'all_four_target_seats_win': target_gate,
                'fifty_six_controls_exact': controls_gate,
                'loss30_fixture_count': len(loss_by_fixture),
                'loss30_winning_sweeps': loss_sweeps,
                'loss30_goal_27_of_30': loss_gate,
                'loss30_parent_6d_sweeps': panel['loss30_parent_6d_winning_sweeps'],
                'top20_reference_receipt_sha256': TOP20_RECEIPT_SHA,
                'top20_fixture_count': len(top20_grouped),
                'top20_winning_sweeps': top20_sweeps,
                'top20_goal_18_of_20': top20_gate,
                'combined_50_fixture_goal_passed': loss_gate and top20_gate,
                'passed': not failures,
                'failures': failures,
                'games': games,
                'evidence_limit': 'Exact frozen saved tapes only; not reactive qualification or promotion evidence.',
                'completed_at_utc': datetime.now(timezone.utc).isoformat(),
            }
            with RECEIPT_PATH.open('x', encoding='utf-8', newline='\n') as out:
                json.dump(receipt, out, ensure_ascii=False, indent=2)
                out.write('\n')
            print(json.dumps({key: receipt[key] for key in (
                'complete', 'game_count', 'clean_60', 'telemetry_60',
                'all_four_target_seats_win', 'fifty_six_controls_exact',
                'loss30_winning_sweeps', 'loss30_goal_27_of_30',
                'top20_winning_sweeps', 'top20_goal_18_of_20',
                'combined_50_fixture_goal_passed', 'passed', 'failures')}, indent=2), flush=True)
            return 0 if receipt['passed'] else 1


def main():
    if len(sys.argv) != 1:
        raise SystemExit('This runner takes no arguments and never resumes.')
    return run_once()


if __name__ == '__main__':
    raise SystemExit(main())
