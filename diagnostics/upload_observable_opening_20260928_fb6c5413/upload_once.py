"""Upload the exact experimental file explicitly selected by the user once."""
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
CANDIDATE = ROOT / 'main_candidate_observable_opening_20260928_fb6c5413.py'
DIGEST = 'fb6c54136017eccc9df2652d2826a14346520c6c0d51ce855321ff51be6693f2'
DESCRIPTION = 'fb6c5413 observable opening selector; user-requested experimental upload; 2026-09-28'


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    receipt_path = HERE / 'upload_receipt.json'
    assert not receipt_path.exists(), 'An attempt is already recorded; inspect it without resubmitting.'
    raw = CANDIDATE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == DIGEST
    compile(raw, str(CANDIDATE), 'exec')
    entrypoint = get_last_callable(raw.decode('utf-8'), path=str(CANDIDATE)).__name__
    assert entrypoint == 'kaggle_observable_portfolio_entrypoint'
    integration = json.loads((ROOT / 'diagnostics/opening_probe_v2_20260928/integration.json').read_text(encoding='utf-8'))
    assert integration['passed'] and integration['candidate_sha256'] == DIGEST
    assert integration['game_count'] == 100 and integration['all_done'] and integration['no_errors']
    before = _run_json(KAGGLE, ['competitions', 'submissions', 'kaggriculture', '--page-size', '10'])
    (HERE / 'submissions_before.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    previous_ids = {int(row['ref']) for row in before}
    baseline_digest = hashlib.sha256((ROOT / 'main.py').read_bytes()).hexdigest()
    backup = HERE / CANDIDATE.name
    backup.write_bytes(raw)
    assert hashlib.sha256(backup.read_bytes()).hexdigest() == DIGEST
    receipt = dict(candidate=str(CANDIDATE), candidate_sha256=DIGEST, uploaded_file_name=CANDIDATE.name,
        backup=str(backup), main_sha256_before=baseline_digest, main_replaced=False,
        authorized_by_user='can you please upload it to the kaggle please (annotation on New candidate)',
        authorization_scope='One upload of the exact fb6c5413 candidate; no leaderboard/replay refresh.',
        authorization_consumed=True, description=DESCRIPTION, local_entrypoint=entrypoint,
        research_qualification='Rejected by native reference nonregression gate; user explicitly requests upload.',
        upload_attempt_started_at_utc=now(), upload_attempt_count=1)
    with receipt_path.open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, indent=2)
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
    receipt['main_sha256_after'] = hashlib.sha256((ROOT / 'main.py').read_bytes()).hexdigest()
    save()
    print(json.dumps(receipt, indent=2), flush=True)
    assert result.returncode == 0 and len(matches) == 1, 'Inspect the saved result and submissions before considering any retry.'


if __name__ == '__main__':
    main()
