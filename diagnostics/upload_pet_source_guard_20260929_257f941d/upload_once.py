"""One explicitly requested experimental upload; never retry an uncertain attempt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _run_json
from diagnostics.local_target_20260928.run_lock import exclusive_run

KAGGLE = r'C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe'
DIGEST = '257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'
MAIN_DIGEST = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
CANDIDATE = HERE / 'main.py'
BACKUP = ROOT / 'main_candidate_pet_source_guard_20260929_257f941d.py'
PRESERVATION = ROOT / 'diagnostics/pet_source_guard_20260929/preservation_receipt.json'
PILOT = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_reactive_20260929/outcome_receipt.json'
OLD_PANEL = ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full_results.json'
DESCRIPTION = '257f941d guarded route repairs; experimental main.py; saved loss30 27/30 top20 19/20; native loader verified; 2026-09-29'
AUTHORIZATION = 'yes so can you review this code and submit it to the kaggle again please. and please make sure to submit the working and winning code that is better thatn the previous version'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def preflight():
    import verify_loader
    manifest, jobs, loaded_name = verify_loader.verify_bindings()
    assert sha(CANDIDATE) == sha(BACKUP) == DIGEST
    assert sha(ROOT / 'main.py') == MAIN_DIGEST
    assert loaded_name == 'kaggle_a44_pet_market_gate_entrypoint'
    freeze_path = HERE / 'package_freeze_receipt.json'
    freeze = read(freeze_path)
    assert freeze['schema'] == 'pet-source-guard-loader-package-static-freeze-v1'
    assert freeze['candidate_sha256'] == DIGEST and freeze['entrypoint'] == loaded_name
    assert freeze['package_manifest_sha256'] == sha(HERE / 'package_manifest.json')
    assert freeze['manifest_builder_sha256'] == sha(HERE / 'build_manifest.py')
    assert freeze['loader_checker_sha256'] == sha(HERE / 'verify_loader.py')
    assert freeze['preservation']['status'] == 'passed'
    assert freeze['preservation']['receipt_sha256'] == sha(PRESERVATION)
    preserved = read(PRESERVATION)
    assert preserved['complete'] and preserved['passed'] and len(preserved['games']) == 102
    assert preserved['candidate_sha256'] == DIGEST
    assert preserved['research_promotion'] is False and preserved['fixed_tape_only'] is True
    assert preserved['winning_sweeps'] == {'loss30': 27, 'top20': 19}
    assert sha(OLD_PANEL) == 'ea74d2be3b852acf83885a35ce55296b391eff8b33b1bd5f556fa6242fa1d732'
    old = read(OLD_PANEL)
    assert old['complete'] and old['passed'] and old['clean'] and len(old['games']) == 100
    old_rows = {(r['fixture_id'], r['candidate_seat']): r for r in old['games']}
    panel_rows = [r for r in preserved['games'] if r['panel'] in ('top20', 'loss30')]
    assert len(panel_rows) == 100
    points = {'win': 1, 'draw': 0.5, 'loss': 0}
    deltas = [points[r['actual']['result']] - points[old_rows[(r['fixture_id'], r['candidate_seat'])]['result']]
              for r in panel_rows]
    assert all(delta >= 0 for delta in deltas) and sum(delta > 0 for delta in deltas) == 20
    loader_path = HERE / 'loader_parity.json'
    loader = read(loader_path)
    assert loader['passed'] and loader['candidate_sha256'] == DIGEST
    assert loader['loaded_name'] == loaded_name
    assert loader['native_game_runs'] == 12 and loader['fixture_seats'] == len(jobs) == 6
    assert loader['package_manifest_sha256'] == sha(HERE / 'package_manifest.json')
    assert loader['preservation_receipt_sha256'] == sha(PRESERVATION)
    assert loader['operational_only'] is True and loader['research_promotion'] is False
    assert loader['all_runs_done_done_720'] and loader['all_runs_no_policy_or_telemetry_errors']
    assert loader['all_direct_file_719_action_pairs_equal']
    assert {(r['fixture_id'], r['seat']) for r in loader['rows']} == {
        (fid, seat) for fid in ('live-114260122', 'live-114274897', 'top20-20-Densike-114270616')
        for seat in (0, 1)
    }
    assert all(r['all_719_actions_both_players_equal'] and r['candidate_sha256'] == DIGEST for r in loader['rows'])
    assert sha(PILOT) == '86d70abbf809baf29c6227141036624131856bed40b7f04664f13ba7093693c9'
    pilot = read(PILOT)
    assert pilot['complete'] and pilot['passed'] is False and pilot['promotion'] is False
    evidence = {label: {'path': str(path), 'sha256': sha(path)} for label, path in {
        'preservation': PRESERVATION,
        'loader_parity': loader_path,
        'package_manifest': HERE / 'package_manifest.json',
        'package_static_freeze': freeze_path,
        'parent_reactive_pilot': PILOT,
        'last_uploaded_saved_panel': OLD_PANEL,
    }.items()}
    return loaded_name, evidence


def submit_once():
    receipt_path = HERE / 'upload_receipt.json'
    assert not receipt_path.exists(), 'An attempt is recorded; inspect it without submitting again.'
    loaded_name, evidence = preflight()
    before = _run_json(KAGGLE, ['competitions', 'submissions', 'kaggriculture', '--page-size', '10'])
    (HERE / 'submissions_before.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    assert not any(r.get('description') == DESCRIPTION for r in before), 'Matching upload already exists.'
    previous_ids = {int(r['ref']) for r in before}
    receipt = dict(
        candidate=str(CANDIDATE), candidate_sha256=DIGEST, uploaded_file_name='main.py',
        backup=str(BACKUP), root_main_replaced=False, root_main_sha256_before=MAIN_DIGEST,
        authorized_by_user=AUTHORIZATION, authorization_consumed=True,
        authorization_scope='One upload of the reviewed corrected candidate as main.py.',
        upload_attempt_count=1, upload_attempt_started_at_utc=now(),
        description=DESCRIPTION, entrypoint=loaded_name, evidence=evidence,
        research_promotion=False, experimental_upload=True,
        evidence_limits='Saved fixed-tape outcomes improve versus a44 (27/30 versus 17/30 losses; top20 remains 19/20). Parent ebf reactive pilot had identical outcomes to a44, failed strict gain/timing gates, and does not establish a rating improvement. Corrected source guard passed separate preservation and loader checks.',
    )
    with receipt_path.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)

    def save():
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')

    try:
        result = subprocess.run(
            [KAGGLE, 'competitions', 'submit', 'kaggriculture', '-f', str(CANDIDATE), '-m', DESCRIPTION, '-q'],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180,
        )
        (HERE / 'submit_stdout.txt').write_text(result.stdout, encoding='utf-8')
        (HERE / 'submit_stderr.txt').write_text(result.stderr, encoding='utf-8')
        receipt.update(upload_returncode=result.returncode, upload_attempt_finished_at_utc=now())
        save()
    except Exception as error:
        receipt.update(upload_result_uncertain=True, upload_exception_type=type(error).__name__)
        save()
        raise
    following = _run_json(KAGGLE, ['competitions', 'submissions', 'kaggriculture', '--page-size', '10'])
    (HERE / 'submissions_after.json').write_text(json.dumps(following, indent=2), encoding='utf-8')
    matches = [r for r in following if int(r['ref']) not in previous_ids and r.get('description') == DESCRIPTION]
    if len(matches) == 1:
        receipt.update(submission_id=int(matches[0]['ref']), kaggle_submission=matches[0], verified_at_utc=now())
    receipt['root_main_sha256_after'] = sha(ROOT / 'main.py')
    save()
    print(json.dumps({k: v for k, v in receipt.items() if k != 'evidence'}, indent=2), flush=True)
    assert result.returncode == 0 and len(matches) == 1, 'Inspect saved attempt and submission list before any retry.'
    assert receipt['root_main_sha256_after'] == MAIN_DIGEST


if __name__ == '__main__':
    if '--submit-once' in sys.argv:
        with exclusive_run(HERE / 'upload.lock'):
            submit_once()
    else:
        entrypoint, evidence = preflight()
        print(json.dumps({'preflight_passed': True, 'candidate_sha256': DIGEST,
                          'entrypoint': entrypoint, 'evidence': evidence, 'upload_attempted': False}, indent=2))
