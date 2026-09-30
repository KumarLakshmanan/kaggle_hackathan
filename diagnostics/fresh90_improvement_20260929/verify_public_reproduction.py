"""Check the actual uploaded seat against all original public action streams."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
from run_panel import HERE, ROOT, sha

entries_path = ROOT / 'diagnostics/fresh90_refresh_20260929/routes/current_submission_56680167_opponents/summary.json'
entries = json.loads(entries_path.read_text(encoding='utf-8'))
receipt = json.loads((HERE / 'cb76_public27_jobs_receipt.json').read_text())
assert receipt['complete'] and receipt['completed_games'] == 54
rows = [json.loads(s) for s in (HERE / 'cb76_public27_jobs_results.jsonl').read_text().splitlines()]
index = {(r['episode_id'], r['candidate_seat']): r for r in rows}
results = []
for entry in entries:
    seat = entry['uploaded_agent_original_source_seat']
    row = index[entry['episode_id'], seat]
    with gzip.open(row['trace_path'], 'rt', encoding='utf-8') as f:
        actions = [json.loads(line)['action'] for line in f]
    digests = [hashlib.sha256(json.dumps(actions, sort_keys=flag, separators=(',', ':')).encode()).hexdigest() for flag in (False, True)]
    replay = json.loads(gzip.decompress(Path(entry['replay_path']).read_bytes()))
    expected_actions = [frame[seat].get('action') or {} for frame in replay['steps'][1:]]
    match = actions == expected_actions
    reward_match = row['candidate_reward'] == float(replay['rewards'][seat]) and row['opponent_reward'] == float(replay['rewards'][1 - seat])
    results.append(dict(episode=entry['episode_id'], original_seat=seat, actions=len(actions),
                        original_action_sha256=entry['uploaded_agent_action_sha256'], actual_canonical_sha256=digests[1],
                        actions_match=match, expected_hash_matches=entry['uploaded_agent_action_sha256'] in digests,
                        rewards_match=reward_match, result_match=row['result'] == entry['uploaded_agent_result'],
                        trace_sha256=sha(row['trace_path'])))
result = dict(at_utc=datetime.now(timezone.utc).isoformat(), games=len(results),
               candidate_sha256=sha(HERE / 'baseline_cb76fbc4.py'), entries_sha256=sha(entries_path),
               ledger_sha256=sha(HERE / 'cb76_public27_jobs_results.jsonl'),
               passed=all(r['actions_match'] and r['expected_hash_matches'] and r['rewards_match'] and r['result_match'] for r in results),
               rows=results, note='Exact uploaded-seat replay reproduction; not evidence that a changed policy will win.')
out = HERE / 'public27_reproduction.json'
assert not out.exists()
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(dict(passed=result['passed'], games=len(results), failures=[r for r in results if not all(r[k] for k in ('actions_match','expected_hash_matches','rewards_match','result_match'))]), indent=2))
