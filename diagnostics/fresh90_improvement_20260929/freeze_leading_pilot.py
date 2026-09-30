"""Freeze exactly three rank-selected raw controls against the existing pilot fixtures."""
import ast
from datetime import datetime, timezone
import json
from run_panel import HERE, ROOT, sha

folder = ROOT / 'diagnostics/fresh90_leading_openings_20260930'
expected = {
    1: '2bac6d8e7b4bb8fa39247b796ab6c78c514059002f27b0461c788361a04841ce',
    2: '85296f8e66a2c8e09723a17efbd611a284c3b6442694cf86790ec757e1bf75c9',
    3: '6434d82e990f930e82d22f43e42d5057a675642be80f73e313740417e206899c',
}
template = [j for j in json.loads((HERE / 'opening_pilot_jobs.json').read_text())
            if j['label'] == 'opening_family1']
assert len(template) == 46
jobs, candidates = [], []
for rank, digest in expected.items():
    path = folder / f'candidate_top_rank_{rank}.py'
    assert sha(path) == digest
    ast.parse(path.read_text(encoding='utf-8'))
    candidates.append(dict(candidate_id=rank, path=str(path), sha256=digest))
    label = f'leading_rank{rank}'
    for prior in template:
        row = dict(prior, path=str(path), candidate_sha256=digest, label=label)
        row['job_id'] = f"{label}:{row['fixture_id']}:{row['candidate_seat']}"
        jobs.append(row)
out = HERE / 'leading_pilot_jobs.json'
assert not out.exists()
out.write_text(json.dumps(jobs, indent=2), encoding='utf-8')
freeze = dict(at_utc=datetime.now(timezone.utc).isoformat(), games=len(jobs),
    jobs_sha256=sha(out), plan_sha256=sha(HERE / 'LEADING_OPENING_PILOT_PLAN.md'),
    architecture_plan_sha256=sha(folder / 'PLAN.md'),
    source_manifest_sha256=sha(folder / 'candidate_manifest.json'), candidates=candidates)
(HERE / 'leading_pilot_freeze.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')

# Preserve the old assessor, and derive an explicit separate copy for identical
# predeclared thresholds with the new names and plan path only.
old = HERE / 'assess_opening_pilot.py'
source = old.read_text(encoding='utf-8').replace('opening_pilot', 'leading_pilot')
source = source.replace('opening_family', 'leading_rank').replace('OPENING_PILOT_PLAN.md', 'LEADING_OPENING_PILOT_PLAN.md')
source = source.replace('opening families', 'leading single-tape controls')
destination = HERE / 'assess_leading_pilot.py'
assert not destination.exists()
ast.parse(source)
destination.write_text(source, encoding='utf-8', newline='\n')
print(json.dumps(dict(games=len(jobs), jobs_sha256=sha(out), assessor_sha256=sha(destination))))
