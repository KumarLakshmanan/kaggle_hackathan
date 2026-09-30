"""One freshly authorized upload of exact experimental candidate 4802aa95."""
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

KAGGLE = r'C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe'
COMPETITION = 'kaggriculture'
DIGEST = '4802aa95c1b960f6bdba3ac313870a847dba8e93dce7d22edfeaca4cee7c19f4'
MAIN_DIGEST = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
SOURCE = ROOT / 'main_candidate_fresh_replay_20260930_4802aa95.py'
CANDIDATE = HERE / 'main.py'
ENTRYPOINT = 'kaggle_fresh_execution_schedule_entrypoint'
AUTHORIZATION = 'ok so can you upload that new candidate to the kaggle please'
DESCRIPTION = ('4802aa95 experimental complete routes + funded land; saved top100 156/200 top20 36/40; '
               'reacting 34W26D4L; both-seat loader verified')

def now(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path, data): Path(path).write_text(json.dumps(data, indent=2), encoding='utf-8')

def preflight():
    assert sha(SOURCE) == sha(CANDIDATE) == DIGEST
    assert sha(ROOT / 'main.py') == MAIN_DIGEST
    loader = read(HERE / 'loader_parity.json')
    assert loader['candidate_sha256'] == DIGEST and loader['loaded_name'] == ENTRYPOINT
    assert loader['passed'] and loader['action_reward_parity'] and len(loader['rows']) == 8
    assert all(row['passed'] for row in loader['rows'])
    decision = ROOT / 'diagnostics/fresh90_improvement_20260929/FINAL_DECISION.json'
    assert read(decision)['candidate_sha256'] == DIGEST
    evidence_paths = [HERE / 'loader_parity.json', HERE / 'package_provenance.json', decision,
                      ROOT / 'diagnostics/fresh90_improvement_20260929/RESULTS.md']
    return {str(path): sha(path) for path in evidence_paths}

def submit_once():
    receipt_path = HERE / 'upload_receipt.json'
    assert not receipt_path.exists(), 'An attempt already exists. Inspect without resubmitting.'
    evidence = preflight()
    before = _run_json(KAGGLE, ['competitions', 'submissions', COMPETITION, '--page-size', '10'])
    write(HERE / 'submissions_before.json', before)
    assert not any(DIGEST[:8] in r.get('description', '') for r in before), 'Candidate already listed; inspect first.'
    previous_ids = {int(row['ref']) for row in before}
    receipt = dict(candidate=str(CANDIDATE), candidate_source=str(SOURCE), candidate_sha256=DIGEST,
                   competition=COMPETITION, uploaded_file_name='main.py', entrypoint=ENTRYPOINT,
                   description=DESCRIPTION, authorized_by_user=AUTHORIZATION, authorization_consumed=True,
                   authorization_scope='One upload of the explicitly requested experimental 4802aa95 candidate.',
                   upload_attempt_count=1, upload_attempt_started_at_utc=now(),
                   root_main_replaced=False, root_main_sha256_before=MAIN_DIGEST,
                   experimental_upload=True, research_promotion=False, evidence=evidence,
                   evidence_limits='Saved top100 78% and top20 90%; reacting screen added four losses and failed the promotion gate. User requested experimental upload after disclosure.')
    with receipt_path.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    try:
        result = subprocess.run([KAGGLE, 'competitions', 'submit', COMPETITION, '-f', str(CANDIDATE),
                                 '-m', DESCRIPTION, '-q'], capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=180)
        (HERE / 'submit_stdout.txt').write_text(result.stdout, encoding='utf-8')
        (HERE / 'submit_stderr.txt').write_text(result.stderr, encoding='utf-8')
        receipt.update(upload_returncode=result.returncode, upload_attempt_finished_at_utc=now())
    except Exception as error:
        receipt.update(upload_result_uncertain=True, upload_exception_type=type(error).__name__)
        write(receipt_path, receipt)
        raise
    write(receipt_path, receipt)
    following = _run_json(KAGGLE, ['competitions', 'submissions', COMPETITION, '--page-size', '10'])
    write(HERE / 'submissions_after.json', following)
    matches = [row for row in following if int(row['ref']) not in previous_ids and row.get('description') == DESCRIPTION]
    if len(matches) == 1:
        receipt.update(submission_id=int(matches[0]['ref']), kaggle_submission=matches[0], verified_at_utc=now())
    receipt.update(root_main_sha256_after=sha(ROOT / 'main.py'), candidate_sha256_after=sha(CANDIDATE))
    write(receipt_path, receipt)
    print(json.dumps({key: value for key, value in receipt.items() if key != 'evidence'}, indent=2), flush=True)
    assert result.returncode == 0 and len(matches) == 1, 'Inspect the saved attempt and status; never automatically retry.'
    assert receipt['root_main_sha256_after'] == MAIN_DIGEST and receipt['candidate_sha256_after'] == DIGEST

if __name__ == '__main__':
    if sys.argv[1:] == ['--submit-once']:
        submit_once()
    else:
        assert not sys.argv[1:]
        print(json.dumps(dict(preflight_passed=bool(preflight()), candidate_sha256=DIGEST, upload_attempted=False)), flush=True)
