"""Reconcile the original upload receipt with verified remote evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt_path = ROOT / 'diagnostics/shunki_purchase_iterated_20260927/promotion_receipt.json'
parity_path = HERE / 'validation_parity.json'
cohort_path = max(HERE.glob('cohort_*.json'), key=lambda p: p.stem)
cohort = json.loads(cohort_path.read_text(encoding='utf8'))
snapshot_path = Path(cohort['snapshot_path']) / 'summary.json'

receipt = json.loads(receipt_path.read_text(encoding='utf8'))
snapshot = json.loads(snapshot_path.read_text(encoding='utf8'))
parity = json.loads(parity_path.read_text(encoding='utf8'))
assert receipt['submission_id'] == snapshot['submission_id'] == 56609430
assert snapshot['submission']['status'] == 'SubmissionStatus.COMPLETE'
assert receipt['candidate_sha256'] == parity['submitted_file_sha256']
assert hashlib.sha256(Path(receipt['uploaded_backup']).read_bytes()).hexdigest() == receipt['candidate_sha256']
assert parity['passed'] and cohort['complete'] and not cohort['failures']
receipt.update(kaggle_submission=snapshot['submission'],
               latest_status_snapshot=str(snapshot_path.resolve()),
               validation_episode_id=parity['episode_id'],
               remote_parity_passed=True,
               remote_parity_evidence=str(parity_path.resolve()),
               live_audit_evidence=str(cohort_path.resolve()),
               live_public_wins=cohort['wins'], live_public_losses=cohort['losses'],
               live_public_draws=cohort['draws'],
               live_rank_at_snapshot=snapshot['our_team']['Rank'])
receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding='utf8')
print(f"Updated {receipt_path}: COMPLETE, parity PASS, {cohort['wins']}W/{cohort['losses']}L", flush=True)
