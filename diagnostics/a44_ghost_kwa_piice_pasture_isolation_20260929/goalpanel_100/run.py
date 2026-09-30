from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
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
ISO_PREFIX = 'iso_pasture_'


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
    require(sha(PANEL) == manifest.get('panel_sha256'), 'panel hash mismatch')
    require(manifest.get('binding_count') == len(manifest.get('bindings', {})),
            'binding count mismatch')
    mismatches = []
    for path_text, expected in manifest['bindings'].items():
        path = Path(path_text)
        actual = sha(path) if path.is_file() else 'MISSING'
        if actual != expected:
            mismatches.append((path_text, actual, expected))
    require(not mismatches, f'frozen input mismatch: {mismatches[:5]}')
    require(panel.get('game_count') == 100 and len(panel.get('games', [])) == 100
            and sum(row['trigger'] for row in panel['games']) == 2,
            'frozen panel size or trigger census changed')
    require(not any(path.exists() for path in (RESULTS, RECEIPT, RUN_MANIFEST, OWN_LOCK)),
            'one-shot runner refuses existing or partial outputs')
    return manifest, panel


def telemetry_checks(actual, row):
    telemetry = actual.get('candidate_telemetry') or {}
    expected = row['expected']
    baseline_telemetry = row['baseline_v5_telemetry']
    non_isolated_telemetry = {key: value for key, value in telemetry.items()
                              if not key.startswith(ISO_PREFIX)}
    checks = {
        'hands_step1': telemetry.get('iso_pasture_rival_hands_step1') == expected['rival_hands'],
        'pastures_step1': telemetry.get('iso_pasture_rival_pastures_step1') == expected['rival_pastures'],
        'trigger_step1': telemetry.get('iso_pasture_triggered_step1') is row['trigger'],
        'bridge_branch': telemetry.get('bridge_selected') == expected['branch'],
        'reported_branch': telemetry.get('iso_pasture_branch_step1') == expected['branch'],
        'route_map_reset': telemetry.get('iso_pasture_reset_route_map_matches') is True,
        'leaf_key72': telemetry.get('iso_pasture_leaf_key72') == expected['leaf_key'],
        'leaf_route72': telemetry.get('iso_pasture_leaf_route72') == expected['leaf_route'],
        'leaf_turns': telemetry.get('iso_pasture_leaf_turns') == expected['leaf_turns'],
        'leaf_errors_zero': telemetry.get('iso_pasture_leaf_errors', 0) == 0,
    }
    if not row['trigger']:
        checks['v5_telemetry_preserved'] = non_isolated_telemetry == baseline_telemetry
    else:
        checks.update({
            'ghost_inactive_on_target': not telemetry.get('a44_ghost_wheat_active72', False),
            'kwa_inactive_on_target': not telemetry.get('a44_kwa_wheat_zero_active72', False),
            'piice_inactive_on_target': not telemetry.get('piice_active144', False),
            'goose4_inactive_on_target': telemetry.get('a44_goose4_turns', 0) == 0,
        })
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
    games = []
    started = datetime.now(timezone.utc).isoformat()
    with exclusive_run(SHARED_LOCK):
        with exclusive_run(OWN_LOCK):
            require(not any(path.exists() for path in (RESULTS, RECEIPT, RUN_MANIFEST)),
                    'run output appeared after verification')
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
                for row in panel['games']:
                    actual = play(row['fixture'], CANDIDATE,
                                  manifest['candidate_sha256'],
                                  int(row['candidate_seat']))
                    clean = (actual.get('candidate_status') == actual.get('opponent_status') == 'DONE'
                             and actual.get('frames') == 720
                             and not actual.get('candidate_errors'))
                    checks, errors = telemetry_checks(actual, row)
                    baseline = row['baseline_v5']
                    equal = {field: actual.get(field) == baseline.get(field) for field in FIELDS}
                    target_win = (actual.get('result') == 'win'
                                  and float(actual.get('margin', 0)) > 0)
                    record = {
                        'fixture_id': row['fixture_id'],
                        'candidate_seat': int(row['candidate_seat']),
                        'panel': row['panel'], 'trigger': row['trigger'],
                        'candidate_sha256': manifest['candidate_sha256'],
                        'clean_done_done_720': clean,
                        'telemetry_checks': checks, 'telemetry_errors': errors,
                        'telemetry_passed': all(checks.values()),
                        'baseline_v5': baseline, 'actual': actual,
                        'exact_v5_fields': equal,
                        'v5_preserved': all(equal.values()) if not row['trigger'] else None,
                        'target_win': target_win if row['trigger'] else None,
                        'delta_margin_vs_v5': actual['margin'] - baseline['margin'],
                    }
                    games.append(record)
                    stream.write(json.dumps(record, ensure_ascii=False,
                                             separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({key: record[key] for key in
                                      ('fixture_id', 'candidate_seat', 'panel', 'trigger',
                                       'clean_done_done_720', 'telemetry_passed',
                                       'v5_preserved', 'target_win')}
                                     | {'result': actual['result'], 'margin': actual['margin']},
                                     ensure_ascii=False), flush=True)

    loss_ids = sorted({row['fixture_id'] for row in games if row['panel'] == 'loss30'})
    top_ids = sorted({row['fixture_id'] for row in games if row['panel'] == 'top20'})
    by_key = {(row['fixture_id'], row['candidate_seat']): row for row in games}
    loss_sweeps = sum(all(by_key[(fixture_id, seat)]['actual']['result'] == 'win'
                          for seat in (0, 1)) for fixture_id in loss_ids)
    top_sweeps = sum(all(by_key[(fixture_id, seat)]['actual']['result'] == 'win'
                         for seat in (0, 1)) for fixture_id in top_ids)
    targets = [row for row in games if row['trigger']]
    controls = [row for row in games if not row['trigger']]
    receipt = {
        'schema': 'a44-v5-isolated-pasture-100-seat-outcome-v1',
        'complete': len(games) == 100, 'diagnostic_only': True,
        'fixed_tape_only': True, 'reactive_validation': False, 'promotion': False,
        'candidate_sha256': manifest['candidate_sha256'],
        'parent_candidate_sha256': manifest['parent_candidate_sha256'],
        'panel_sha256': manifest['panel_sha256'],
        'games': games, 'game_count': len(games),
        'clean_100': len(games) == 100 and all(row['clean_done_done_720'] for row in games),
        'telemetry_100': len(games) == 100 and all(row['telemetry_passed'] for row in games),
        'v5_exact_98_nontrigger_rows': len(controls) == 98
            and all(row['v5_preserved'] for row in controls),
        'both_third_seats_win': len(targets) == 2 and all(row['target_win'] for row in targets),
        'loss30_fixture_count': len(loss_ids),
        'loss30_winning_sweeps': loss_sweeps,
        'loss30_goal_27_of_30': len(loss_ids) == 30 and loss_sweeps >= 27,
        'top20_fixture_count': len(top_ids),
        'top20_winning_sweeps': top_sweeps,
        'top20_goal_18_of_20': len(top_ids) == 20 and top_sweeps >= 18,
        'parent_v5_loss30_winning_sweeps': panel['parent_loss30_winning_sweeps'],
        'parent_v5_top20_winning_sweeps': panel['parent_top20_winning_sweeps'],
        'combined_goal_passed': len(loss_ids) == 30 and loss_sweeps >= 27
            and len(top_ids) == 20 and top_sweeps >= 18,
        'passed': len(games) == 100
            and all(row['clean_done_done_720'] and row['telemetry_passed'] for row in games)
            and len(controls) == 98 and all(row['v5_preserved'] for row in controls)
            and len(targets) == 2 and all(row['target_win'] for row in targets)
            and len(loss_ids) == 30 and loss_sweeps >= 27
            and len(top_ids) == 20 and top_sweeps >= 18,
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    with RECEIPT.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'games'},
                     ensure_ascii=False, indent=2), flush=True)
    return receipt


if __name__ == '__main__':
    _, _ = verify()
    result = run_once()
    if not result['passed']:
        raise SystemExit(1)
