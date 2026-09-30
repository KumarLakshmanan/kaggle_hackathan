"""Seal the failed promotion decision and verify preserved deliverables."""
from datetime import datetime, timezone
import json
from run_panel import HERE, ROOT, sha

manifest = json.loads((HERE / 'combined_v2_manifest.json').read_text())
source = manifest['candidate']
delivery = ROOT / 'main_candidate_fresh_replay_20260930_4802aa95.py'
assert sha(source) == sha(delivery) == manifest['candidate_sha256']
screen = json.loads((HERE / 'combined_v2_screen_receipt.json').read_text())
assert screen['complete'] and not screen['assessment']['screen_passed']
assert screen['candidate_sha256'] == manifest['candidate_sha256']
for name in ('combined_v2_operational_receipt.json', 'combined_v2_confirm_receipt.json'):
    assert not (HERE / name).exists(), f'Unexpected conditional result: {name}'
assert not (ROOT / 'diagnostics/.shared_game_run.lock').exists(), 'A benchmark is still running'
assert sha(ROOT / 'main.py') == '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
decision = dict(completed_at_utc=datetime.now(timezone.utc).isoformat(),
    decision='Rejected for promotion: reacting screen regression; greater-than90 percent remains unmet.',
    candidate_sha256=sha(source), candidate_source=source, preserved_root_copy=str(delivery),
    root_main_sha256=sha(ROOT / 'main.py'), latest_uploaded_submission_id=56680167,
    upload_performed=False, native_operational_games_run=False, confirmation_games_run=False,
    conditional_checks_skipped_because='Frozen reacting screen failed before operational/confirmation gates.',
    screen_receipt_sha256=sha(HERE / 'combined_v2_screen_receipt.json'),
    reserved_point_gain=6, reserved_seats_per_version=400,
    next_research_constraint='Any revision informed by these screen outcomes needs a new frozen independent comparison; keep the untouched confirmation seeds reserved.')
output = HERE / 'FINAL_DECISION.json'
assert not output.exists()
output.write_text(json.dumps(decision, indent=2), encoding='utf-8')
print(json.dumps(decision, indent=2))
