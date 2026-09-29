"""Perform exactly one user-authorized experimental Kaggle upload of a44c8c2c."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _run_json
from kaggle_environments.agent import get_last_callable
from diagnostics.local_target_20260928.run_lock import exclusive_run

KAGGLE = r'C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe'
CANDIDATE = HERE / 'main.py'
BACKUP = ROOT / 'main_candidate_adaptive_donor_pair_repair_20260928_a44c8c2c.py'
DIGEST = 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
MAIN_DIGEST = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
DESCRIPTION = 'a44c8c2c adaptive donor opening + pair repair + animal liquidity; user-requested experimental main.py; 2026-09-28'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt_path = HERE / 'upload_receipt.json'
    assert not receipt_path.exists(), 'An attempt is already recorded; inspect it without resubmitting.'
    assert sha(CANDIDATE) == sha(BACKUP) == DIGEST and sha(ROOT / 'main.py') == MAIN_DIGEST
    raw = CANDIDATE.read_bytes()
    compile(raw, str(CANDIDATE), 'exec')
    entrypoint = get_last_callable(raw.decode('utf-8'), path=str(CANDIDATE)).__name__
    assert entrypoint == 'kaggle_donor_pair_repair_entrypoint'
    full_path = ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full_results.json'
    full = json.loads(full_path.read_text(encoding='utf-8'))
    assert sha(full_path) == 'ea74d2be3b852acf83885a35ce55296b391eff8b33b1bd5f556fa6242fa1d732'
    assert full['complete'] and full['passed'] and full['clean'] and len(full['games']) == 100
    assert all(r['candidate_sha256'] == DIGEST for r in full['games'])
    assert not full['regressions_vs32e'] and not full['regressions_vs_known_ceed']
    summary = full['panels']
    assert {r['panel']: r['both_seat_wins'] for r in summary} == {'top20':19, 'loss30':17}
    parity_path = HERE / 'loader_parity.json'
    parity = json.loads(parity_path.read_text(encoding='utf-8'))
    assert parity['passed'] and parity['candidate_sha256'] == DIGEST and parity['loaded_name'] == entrypoint
    assert parity['saved_panel_sha256'] == sha(full_path)
    assert parity['game_count'] == 8 and len(parity['rows']) == 4
    assert {(r['team'], r['seat']) for r in parity['rows']} == {
        (team, seat) for team in ('Yaroslav', 'Boey') for seat in (0, 1)}
    assert all(r['all_719_actions_both_players_equal'] for r in parity['rows'])
    before = _run_json(KAGGLE, ['competitions', 'submissions', 'kaggriculture', '--page-size', '10'])
    (HERE / 'submissions_before.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    assert not any(row.get('description') == DESCRIPTION for row in before), 'Matching upload already listed; inspect first.'
    previous_ids = {int(row['ref']) for row in before}
    receipt = dict(candidate=str(CANDIDATE), candidate_sha256=DIGEST, uploaded_file_name='main.py',
                   backup=str(BACKUP), main_sha256_before=MAIN_DIGEST, main_replaced=False,
                   authorized_by_user='upload the current updated main.py to the kaggle please',
                   authorization_scope='One upload of exact completed a44c8c2c as main.py; no leaderboard or replay refresh.',
                   authorization_consumed=True, description=DESCRIPTION, local_entrypoint=entrypoint,
                   evidence={'loader_parity': {'path': str(parity_path), 'sha256': sha(parity_path)},
                             'saved_panel': {'path': str(full_path), 'sha256': sha(full_path)}},
                   saved_panel_summary=summary,
                   research_qualification='Experimental upload. Saved tapes are development/regression diagnostics; broader54 preservation and reacting qualification are incomplete.',
                   upload_attempt_started_at_utc=now(), upload_attempt_count=1)
    with receipt_path.open('x', encoding='utf-8') as output:
        json.dump(receipt, output, indent=2)
    def save():
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    try:
        result = subprocess.run([KAGGLE, 'competitions', 'submit', 'kaggriculture', '-f', str(CANDIDATE),
                                 '-m', DESCRIPTION, '-q'], capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=180)
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
    matches = [row for row in following if int(row['ref']) not in previous_ids and row.get('description') == DESCRIPTION]
    if len(matches) == 1:
        receipt.update(submission_id=int(matches[0]['ref']), kaggle_submission=matches[0], verified_at_utc=now())
    receipt['main_sha256_after'] = sha(ROOT / 'main.py')
    save()
    print(json.dumps(receipt, indent=2), flush=True)
    assert result.returncode == 0 and len(matches) == 1, 'Inspect saved results and submissions before any retry.'
    assert receipt['main_sha256_after'] == MAIN_DIGEST


if __name__ == '__main__':
    with exclusive_run(HERE / 'upload.lock'):
        main()
