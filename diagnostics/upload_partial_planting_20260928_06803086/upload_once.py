"""One authorized upload of immutable 06803086; preserve local research main."""
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

KAGGLE = r'C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe'
CANDIDATE = ROOT / 'main_candidate_partial_planting_20260928_06803086.py'
DIGEST = '068030868689db5eb1e9a4a4427bededa8fbc13cae14e1003eb6be5440a6da42'
MAIN_DIGEST = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
DESCRIPTION = '06803086 partial planting + compatible route; user-requested experimental upload; 2026-09-28'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt_path = HERE / 'upload_receipt.json'
    assert not receipt_path.exists(), 'An attempt is already recorded; inspect it without resubmitting.'
    assert sha(CANDIDATE) == DIGEST and sha(ROOT / 'main.py') == MAIN_DIGEST
    raw = CANDIDATE.read_bytes()
    compile(raw, str(CANDIDATE), 'exec')
    entrypoint = get_last_callable(raw.decode('utf-8'), path=str(CANDIDATE)).__name__
    assert entrypoint == 'kaggle_partial_planting_entrypoint'
    full_path = ROOT / 'diagnostics/partial_planting_20260928/native_full.json'
    full = json.loads(full_path.read_text(encoding='utf-8'))
    assert full['complete'] and full['passed'] and full['clean'] and len(full['games']) == 100
    assert full['candidate_sha256'] == DIGEST
    parity_path = HERE / 'loader_parity.json'
    parity = json.loads(parity_path.read_text(encoding='utf-8'))
    assert parity['passed'] and parity['candidate_sha256'] == DIGEST and parity['loaded_name'] == entrypoint
    assert parity['native_full_sha256'] == sha(full_path)
    assert [row['seat'] for row in parity['rows']] == [0, 1]
    assert all(row['all_719_actions_both_players_equal'] for row in parity['rows'])
    before = _run_json(KAGGLE, ['competitions', 'submissions', 'kaggriculture', '--page-size', '10'])
    (HERE / 'submissions_before.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    assert not any(row.get('description') == DESCRIPTION for row in before), 'Matching upload already listed; inspect first.'
    previous_ids = {int(row['ref']) for row in before}
    backup = HERE / CANDIDATE.name
    with backup.open('xb') as output:
        output.write(raw)
    assert sha(backup) == DIGEST
    receipt = dict(candidate=str(CANDIDATE), candidate_sha256=DIGEST, uploaded_file_name=CANDIDATE.name,
                   backup=str(backup), main_sha256_before=MAIN_DIGEST, main_replaced=False,
                   authorized_by_user='upload it to online (annotation on backed-up 06803086 candidate); to kaggle submissions',
                   authorization_scope='One upload of exact 06803086; no leaderboard or replay refresh.',
                   authorization_consumed=True, description=DESCRIPTION, local_entrypoint=entrypoint,
                   evidence={'loader_parity': {'path': str(parity_path), 'sha256': sha(parity_path)},
                             'native_saved_panel': {'path': str(full_path), 'sha256': sha(full_path)}},
                   research_qualification='18/20 top-team saved sweeps; 0/30 public-loss sweeps. Reacting qualification incomplete.',
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
    main()
