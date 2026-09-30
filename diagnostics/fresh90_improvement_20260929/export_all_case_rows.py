"""Export every logged case in this research folder without counting reuses as new games."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from run_panel import HERE, sha

fields = ['source_ledger', 'job_id', 'label', 'version', 'dataset', 'method', 'harness',
          'fixture_id', 'rank', 'team', 'team_id', 'episode_id', 'seed', 'candidate_seat',
          'rival', 'path', 'candidate_sha256', 'opponent', 'opponent_sha256',
          'action_sha256', 'replay_sha256', 'candidate_reward', 'opponent_reward', 'margin',
          'result', 'candidate_status', 'opponent_status', 'frames', 'candidate_errors',
          'opponent_errors', 'error', 'error_type', 'wall_seconds', 'max_candidate_call_seconds',
          'reused_from_results', 'reused_from_job_id']
output = HERE / 'ALL_CASE_ROWS.csv'
ledgers = []
count = 0
with output.open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for path in sorted(HERE.rglob('*results.jsonl')):
        raw = path.read_bytes()
        assert not raw or raw.endswith(b'\n'), f'Ledger write in progress: {path}'
        rows = [json.loads(s) for s in raw.decode('utf-8').splitlines() if s.strip()]
        for row in rows:
            exported = {k: row.get(k, '') for k in fields}
            exported['source_ledger'] = str(path)
            for k, value in exported.items():
                if isinstance(value, (dict, list)):
                    exported[k] = json.dumps(value, sort_keys=True, ensure_ascii=False)
            writer.writerow(exported)
        count += len(rows)
        ledgers.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), logged_rows=len(rows)))
index = dict(at_utc=datetime.now(timezone.utc).isoformat(), csv=str(output), csv_sha256=sha(output),
             logged_rows=count, ledgers=ledgers,
             caveat='An index of logged cases, not a count of unique new games. Ledgers can include exact reused rows, repeated controls, and development variants.')
(HERE / 'ALL_CASE_ROWS_INDEX.json').write_text(json.dumps(index, indent=2), encoding='utf-8')
print(json.dumps(dict(csv=str(output), logged_rows=count, ledgers=len(ledgers), sha256=sha(output))))
