"""One freshly user-authorized upload of the exact experimental cb76fbc4 file."""
import ast
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
DIGEST = 'cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74'
MAIN_DIGEST = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
SOURCE = ROOT / 'main_candidate_minimal_repair_20260929_cb76fbc4.py'
CANDIDATE = HERE / 'main.py'
TESTS = ROOT / 'diagnostics/top100_regression_repair_20260929'
ENTRYPOINT = 'kaggle_minimal_route_repair_entrypoint'
AUTHORIZATION = 'upload that new candidate to the kaggle please.'
DESCRIPTION = ('cb76fbc4 minimal routes + planting repair; user-requested experimental main.py; '
               'saved top100 145/200; fresh 149W90D17L; older loss archive 3/30; both-seat loader verified')


def now(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path, value): Path(path).write_text(json.dumps(value, indent=2), encoding='utf-8')


def preflight():
    assert sha(SOURCE) == DIGEST
    assert sha(ROOT / 'main.py') == MAIN_DIGEST
    manifest = read(TESTS / 'manifest_v3.json')
    assert manifest['candidate_sha256'] == DIGEST and sha(manifest['candidate']) == DIGEST
    evidence = {}
    for receipt_name, ledger_name, expected_count in [
        ('saved_v3_full_receipt.json', 'saved_v3.jsonl', 200),
        ('reactive_v3_confirm_receipt.json', 'reactive_v3_confirm.jsonl', 512),
        ('native_checks_v3_receipt.json', 'native_checks_v3.jsonl', 14),
        ('archive_v3_receipt.json', 'archive_v3.jsonl', 102),
    ]:
        receipt, ledger = read(TESTS / receipt_name), TESTS / ledger_name
        assert receipt['complete'] and receipt['candidate_sha256'] == DIGEST
        assert sha(ledger) == receipt['results_sha256']
        rows = list(map(json.loads, ledger.read_text(encoding='utf-8').splitlines()))
        assert len(rows) == expected_count
        assert all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE'
                   and not r.get('error') and not r.get('candidate_errors') and not r.get('opponent_errors') for r in rows)
        evidence[receipt_name] = {'path': str(TESTS / receipt_name), 'sha256': sha(TESTS / receipt_name),
                                  'ledger_sha256': sha(ledger), 'games': len(rows)}
    loader = read(TESTS / 'loader_v3.json')
    assert loader['candidate_sha256'] == DIGEST and loader['passed'] and loader['action_reward_parity']
    assert loader['loaded_name'] == ENTRYPOINT and len(loader['rows']) == 4
    assert all(r['passed'] for r in loader['rows'])
    assert read(TESTS / 'native_checks_v3_receipt.json')['passed']
    evidence['loader_v3.json'] = {'path': str(TESTS / 'loader_v3.json'), 'sha256': sha(TESTS / 'loader_v3.json')}
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    assert [n.name for n in tree.body if isinstance(n, ast.FunctionDef)][-1] == ENTRYPOINT
    if not CANDIDATE.exists():
        with CANDIDATE.open('xb') as stream:
            stream.write(SOURCE.read_bytes())
    assert sha(CANDIDATE) == DIGEST
    write(HERE / 'package_provenance.json', dict(source=str(SOURCE), source_sha256=DIGEST,
          submission_file=str(CANDIDATE), submission_sha256=sha(CANDIDATE), entrypoint=ENTRYPOINT,
          research_promotion=False, experimental=True, created_at_utc=now()))
    return evidence


def submit_once():
    receipt_path = HERE / 'upload_receipt.json'
    assert not receipt_path.exists(), 'An upload attempt is already recorded; inspect without resubmitting.'
    evidence = preflight()
    before = _run_json(KAGGLE, ['competitions', 'submissions', COMPETITION, '--page-size', '10'])
    write(HERE / 'submissions_before.json', before)
    assert not any(r.get('description') == DESCRIPTION for r in before), 'Matching upload already exists.'
    previous_ids = {int(r['ref']) for r in before}
    receipt = dict(candidate=str(CANDIDATE), candidate_source=str(SOURCE), candidate_sha256=DIGEST,
        uploaded_file_name='main.py', competition=COMPETITION, entrypoint=ENTRYPOINT,
        description=DESCRIPTION, authorized_by_user=AUTHORIZATION, authorization_consumed=True,
        authorization_scope='One upload of the explicitly requested, tested cb76fbc4 candidate.',
        upload_attempt_count=1, upload_attempt_started_at_utc=now(),
        root_main_replaced=False, root_main_sha256_before=MAIN_DIGEST,
        experimental_upload=True, research_promotion=False, evidence=evidence,
        evidence_limits='Fresh 149/90/17 versus 4ee 147/90/19 is inconclusive; older loss archive 3/30 versus ae349 27/30. User requested upload after these limitations were reported.')
    with receipt_path.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    try:
        result = subprocess.run([KAGGLE, 'competitions', 'submit', COMPETITION,
            '-f', str(CANDIDATE), '-m', DESCRIPTION, '-q'],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
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
    matches = [r for r in following if int(r['ref']) not in previous_ids and r.get('description') == DESCRIPTION]
    if len(matches) == 1:
        receipt.update(submission_id=int(matches[0]['ref']), kaggle_submission=matches[0], verified_at_utc=now())
    receipt.update(root_main_sha256_after=sha(ROOT / 'main.py'), candidate_sha256_after=sha(CANDIDATE))
    write(receipt_path, receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'evidence'}, indent=2), flush=True)
    assert result.returncode == 0 and len(matches) == 1, 'Inspect saved attempt and status; never automatically retry.'
    assert receipt['root_main_sha256_after'] == MAIN_DIGEST and receipt['candidate_sha256_after'] == DIGEST


if __name__ == '__main__':
    if sys.argv[1:] == ['--submit-once']:
        submit_once()
    else:
        assert not sys.argv[1:]
        evidence = preflight()
        print(json.dumps(dict(preflight_passed=True, candidate_sha256=DIGEST,
            entrypoint=ENTRYPOINT, evidence_files_verified=len(evidence), upload_attempted=False), indent=2))
