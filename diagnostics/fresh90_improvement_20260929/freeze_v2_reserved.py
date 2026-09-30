"""Freeze V2 follow-ups only after both repeated development panels pass."""
from datetime import datetime, timezone
import json
from pathlib import Path
from run_panel import HERE, sha

manifest = json.loads((HERE / 'combined_v2_manifest.json').read_text())
candidate = manifest['candidate']
assert sha(candidate) == manifest['candidate_sha256']
gain = 0
evidence = {}
for panel in ('top100', 'public27'):
    comparison_path = HERE / f'combined_v2_{panel}_comparison.json'
    comparison = json.loads(comparison_path.read_text(encoding='utf-8'))
    assessment = comparison['candidate_assessment']['combined_v2']
    assert assessment['all']['all_clean'] and not comparison['lost_wins']
    assert comparison['candidate_sha256'] == [manifest['candidate_sha256']]
    if panel == 'top100':
        assert assessment['top20']['wins'] >= 36
    gain += comparison['delta_points']
    evidence[str(comparison_path)] = sha(comparison_path)
assert gain > 0

files = []
for dataset in ('reserved2', 'reserved3'):
    baseline_path = HERE / f'cb76_{dataset}_jobs.json'
    baseline = json.loads(baseline_path.read_text())
    assert len(baseline) == 200
    candidate_jobs = []
    for job in baseline:
        assert job['candidate_sha256'] == sha(HERE / 'baseline_cb76fbc4.py')
        row = dict(job, label='combined_v2', path=candidate,
                   candidate_sha256=manifest['candidate_sha256'])
        row['job_id'] = f"combined_v2:{row['fixture_id']}:{row['candidate_seat']}"
        candidate_jobs.append(row)
    output = HERE / f'combined_v2_{dataset}_jobs.json'
    assert not output.exists()
    output.write_text(json.dumps(candidate_jobs, indent=2), encoding='utf-8')
    for p in (baseline_path, output):
        files.append(dict(path=str(p), sha256=sha(p), games=200))

freeze = dict(at_utc=datetime.now(timezone.utc).isoformat(),
              candidate_sha256=manifest['candidate_sha256'],
              development_gate_passed=True, evidence=evidence, files=files,
              original_overlap_manifest_sha256=sha(HERE / 'combined_v1_followup_freeze.json'),
              caveat='Reserved tapes include known overlap and cannot independently validate a policy.')
out = HERE / 'combined_v2_reserved_freeze.json'
assert not out.exists()
out.write_text(json.dumps(freeze, indent=2), encoding='utf-8')
print(json.dumps(freeze, indent=2))
