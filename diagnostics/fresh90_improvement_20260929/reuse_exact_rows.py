"""Seed a new manifest ledger only with exact source/replay/action/seat matches."""
import argparse
import json
from pathlib import Path
from run_panel import sha

p = argparse.ArgumentParser()
p.add_argument('jobs', type=Path)
p.add_argument('source', type=Path)
a = p.parse_args()
jobs = json.loads(a.jobs.read_text(encoding='utf-8'))
rows = [json.loads(s) for s in a.source.read_text(encoding='utf-8').splitlines()]
fields = ('fixture_id', 'candidate_seat', 'candidate_sha256', 'action_sha256', 'replay_sha256')
old = {tuple(r[k] for k in fields): r for r in rows}
assert len(old) == len(rows)
out = a.jobs.with_name(a.jobs.stem + '_results.jsonl')
assert not out.exists()
reused = []
for j in jobs:
    r = old.get(tuple(j[k] for k in fields))
    if r is None:
        continue
    assert sha(j['path']) == j['candidate_sha256']
    rr = dict(r)
    rr.update({k: v for k, v in j.items() if k not in ('entry', 'trace_path')})
    rr.update(reused_from=str(a.source.resolve()), reused_ledger_sha256=sha(a.source))
    reused.append(rr)
out.write_text(''.join(json.dumps(r) + '\n' for r in reused), encoding='utf-8')
print(json.dumps(dict(reused=len(reused), output=str(out), jobs_sha256=sha(a.jobs), source_sha256=sha(a.source))))
