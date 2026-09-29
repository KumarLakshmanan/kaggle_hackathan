"""One freshly authorized repeat upload of exact ae349d83; prior upload 56666114."""
from datetime import datetime, timezone
import ast
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
DIGEST = 'ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb'
MAIN_DIGEST = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
SOURCE = ROOT / 'main_candidate_improved_20260929.py'
CANDIDATE = HERE / 'main.py'
TESTS = ROOT / 'diagnostics/combined_agent_257f_20260929'
ENTRYPOINT = 'kaggle_a44_pet_market_gate_entrypoint'
DESCRIPTION = 'ae349d83 user-requested repeat of 56666114; identical tested main.py; native loader verified; 2026-09-29'
AUTHORIZATION = 'can you upload the file again please'
BOUND = {
    'pizza_pilot/comparison_manifest_receipt.json': '1d8d4bd5a34afd6200e5f8e9ddd2cfcb1c87f52adf1fd8d70898a9571f65a820',
    'saved_panel/comparison_manifest_receipt.json': '218297125b45a782f903b2a7aaa178597b708a53f0ffac4f196b404f7b95ce2d',
    'saved_panel/comparison_manifest_results.jsonl': 'ebe9c97327a0086766f67c88213e2fe086ebfa8f89d8ba84db8f5ba918091562',
    'reactive/comparison_manifest_receipt.json': '53e0968303b1e26c4ec6dfc0681edb2f939d156b9635c5a1aaca5fb99233479e',
    'reactive/comparison_manifest_results.jsonl': 'db611d202ab6879666a60b49ce70cc2025b8dc380319f718ed05caba7e407be6',
    'loader_pensukesan_dieter_20260929/receipt.json': 'e6925bec83e3afa55c8339d02224fac1d2c0802fe9c788200c84bb96dc69915c',
    'loader_pensukesan_dieter_20260929/manifest.json': 'd1d92a2962c8f5a864b2d2c522e804883bcc62e96b3f29917b329f5eba3187f1',
}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def preflight():
    assert sha(SOURCE) == DIGEST, 'Candidate differs from tested file.'
    assert sha(ROOT / 'main.py') == MAIN_DIGEST, 'Research main has changed; inspect before uploading.'
    assert sha(ROOT / 'main_uploaded_backup_257f941d_20260929.py') == '257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'
    for relative, digest in BOUND.items():
        assert sha(TESTS / relative) == digest, f'Evidence mismatch: {relative}'
    for phase, cases in [('saved_panel', 102), ('reactive', 24)]:
        receipt = read(TESTS / phase / 'comparison_manifest_receipt.json')
        assert receipt['candidate']['sha256'] == DIGEST
        assert receipt['status'] == 'complete' and receipt['completed_cases'] == cases
        assert receipt['failure'] == '' and receipt['traceback'] == ''
        assert receipt['manifest_sha256'] == sha(TESTS / phase / 'comparison_manifest.json')
        assert receipt['rows_sha256'] == sha(TESTS / phase / 'comparison_manifest_results.jsonl')
    loader = read(TESTS / 'loader_pensukesan_dieter_20260929/receipt.json')
    assert loader['passed'] and loader['candidate_sha256'] == DIGEST
    assert loader['native_game_runs'] == 8 and loader['fixture_seats'] == 4
    assert loader['research_promotion'] is False
    assert all(loader[field] for field in (
        'all_direct_file_actions_rewards_telemetry_equal', 'all_runs_done_done_720',
        'all_runs_719_duration_logs_per_player',
        'all_runs_no_native_status_stderr_or_telemetry_errors',
        'all_runs_nonnegative_actual_native_overage'))
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    assert [node.name for node in tree.body if isinstance(node, ast.FunctionDef)][-1] == ENTRYPOINT
    if not CANDIDATE.exists():
        with CANDIDATE.open('xb') as stream:
            stream.write(SOURCE.read_bytes())
    assert sha(CANDIDATE) == DIGEST
    return {relative: {'path': str(TESTS / relative), 'sha256': digest} for relative, digest in BOUND.items()}


def submit_once():
    receipt_path = HERE / 'upload_receipt.json'
    assert not receipt_path.exists(), 'Attempt already recorded; inspect without resubmitting.'
    evidence = preflight()
    before = _run_json(KAGGLE, ['competitions', 'submissions', 'kaggriculture', '--page-size', '10'])
    write(HERE / 'submissions_before.json', before)
    assert not any(row.get('description') == DESCRIPTION for row in before), 'Matching upload already exists.'
    previous_ids = {int(row['ref']) for row in before}
    receipt = dict(
        candidate=str(CANDIDATE), candidate_source=str(SOURCE), candidate_sha256=DIGEST,
        uploaded_file_name='main.py', entrypoint=ENTRYPOINT, description=DESCRIPTION,
        authorized_by_user=AUTHORIZATION, authorization_consumed=True,
        authorization_scope='One freshly requested repeat upload of the exact ae349d83 file as main.py.',
        repeats_submission_id=56666114,
        upload_attempt_count=1, upload_attempt_started_at_utc=now(),
        root_main_replaced=False, root_main_sha256_before=MAIN_DIGEST,
        research_promotion=False, experimental_upload=True, evidence=evidence,
        evidence_limits='Saved margins improve while WDL remains unchanged: loss30 27/30 and top20 19/20 both-seat sweeps. Fresh reacting comparison remains 8W/14D/2L, with zero new-guard activations and no proven score or rank improvement.',
    )
    with receipt_path.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    try:
        result = subprocess.run(
            [KAGGLE, 'competitions', 'submit', 'kaggriculture', '-f', str(CANDIDATE), '-m', DESCRIPTION, '-q'],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180,
        )
        (HERE / 'submit_stdout.txt').write_text(result.stdout, encoding='utf-8')
        (HERE / 'submit_stderr.txt').write_text(result.stderr, encoding='utf-8')
        receipt.update(upload_returncode=result.returncode, upload_attempt_finished_at_utc=now())
    except Exception as error:
        receipt.update(upload_result_uncertain=True, upload_exception_type=type(error).__name__)
        write(receipt_path, receipt)
        raise
    write(receipt_path, receipt)
    following = _run_json(KAGGLE, ['competitions', 'submissions', 'kaggriculture', '--page-size', '10'])
    write(HERE / 'submissions_after.json', following)
    matches = [row for row in following if int(row['ref']) not in previous_ids and row.get('description') == DESCRIPTION]
    if len(matches) == 1:
        receipt.update(submission_id=int(matches[0]['ref']), kaggle_submission=matches[0], verified_at_utc=now())
    receipt['root_main_sha256_after'] = sha(ROOT / 'main.py')
    receipt['candidate_sha256_after'] = sha(CANDIDATE)
    write(receipt_path, receipt)
    print(json.dumps({key: value for key, value in receipt.items() if key != 'evidence'}, indent=2), flush=True)
    assert result.returncode == 0 and len(matches) == 1, 'Inspect saved attempt and status; never automatically retry.'
    assert receipt['root_main_sha256_after'] == MAIN_DIGEST
    assert receipt['candidate_sha256_after'] == DIGEST


if __name__ == '__main__':
    if '--submit-once' in sys.argv:
        submit_once()
    else:
        evidence = preflight()
        print(json.dumps({'preflight_passed': True, 'candidate_sha256': DIGEST,
                          'entrypoint': ENTRYPOINT, 'evidence_files_verified': len(evidence),
                          'upload_attempted': False}, indent=2))
