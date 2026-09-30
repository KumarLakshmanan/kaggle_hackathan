"""One-shot promotion/upload under the user's current explicit request."""
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

if __name__ == '__main__':
    manifest = json.loads((HERE / 'build_manifest.json').read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(HERE / 'PLAN.md') == manifest['plan_sha256']
    evidence = {}
    for name in ('pilot','panels','confirmation','loader_parity'):
        path = HERE / (name + '.json')
        document = json.loads(path.read_text())
        assert document['passed'] and document['candidate_sha256'] == manifest['candidate_sha256'], name
        assert document.get('complete', True), name
        evidence[name] = {'path': str(path), 'sha256': sha(path)}
    candidate, main = Path(manifest['candidate']), ROOT / 'main.py'
    assert sha(candidate) == sha(Path(manifest['backup'])) == manifest['candidate_sha256']
    assert sha(main) == manifest['incumbent_sha256']
    receipt_path = HERE / 'promotion_receipt.json'
    assert not receipt_path.exists(), 'Never repeat an existing upload attempt automatically'
    previous = _run_json(KAGGLE, ['competitions','submissions','kaggriculture','--page-size','5'])
    (HERE / 'submissions_before_upload.json').write_text(json.dumps(previous,indent=2),encoding='utf8')
    previous_ids = {int(row['ref']) for row in previous}
    backup = ROOT / 'main_before_purchase_iterated_20260927_c68fa46f.py'
    if backup.exists():
        assert sha(backup) == manifest['incumbent_sha256']
    else:
        backup.write_bytes(main.read_bytes())
    raw = candidate.read_bytes()
    compile(raw, str(main), 'exec')
    main.write_bytes(raw)
    assert sha(main) == manifest['candidate_sha256']
    uploaded_backup = ROOT / f'main_uploaded_purchase_iterated_20260927_{manifest["candidate_sha256"][:8]}.py'
    assert not uploaded_backup.exists()
    uploaded_backup.write_bytes(raw)
    message = f'{manifest["candidate_sha256"][:8]} purchase + two-pass queue; fresh reactive and recent top100 qualified; 2026-09-27'
    receipt = dict(promoted_at_utc=datetime.now(timezone.utc).isoformat(),
                   authorized_by_user='please check and update it also please',
                   candidate_sha256=manifest['candidate_sha256'], previous_main_sha256=manifest['incumbent_sha256'],
                   main=str(main), previous_main_backup=str(backup), uploaded_backup=str(uploaded_backup),
                   evidence=evidence, description=message, authorization_consumed=True,
                   upload_attempt_started_at_utc=datetime.now(timezone.utc).isoformat())
    def save():
        receipt_path.write_text(json.dumps(receipt,indent=2),encoding='utf8')
    save()
    response = subprocess.run([KAGGLE,'competitions','submit','kaggriculture','-f',str(main),'-m',message,'-q'],
                              capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180)
    (HERE / 'submit_stdout.txt').write_text(response.stdout,encoding='utf8')
    (HERE / 'submit_stderr.txt').write_text(response.stderr,encoding='utf8')
    receipt.update(upload_returncode=response.returncode, upload_attempt_finished_at_utc=datetime.now(timezone.utc).isoformat())
    save()
    following = _run_json(KAGGLE,['competitions','submissions','kaggriculture','--page-size','5'])
    (HERE / 'submissions_after_upload.json').write_text(json.dumps(following,indent=2),encoding='utf8')
    matches = [row for row in following if int(row['ref']) not in previous_ids and row.get('description') == message]
    if len(matches) == 1:
        receipt.update(submission_id=int(matches[0]['ref']), kaggle_submission=matches[0])
        save()
    print(json.dumps(receipt,indent=2),flush=True)
    assert response.returncode == 0 and len(matches) == 1, 'Inspect receipts before any retry'
