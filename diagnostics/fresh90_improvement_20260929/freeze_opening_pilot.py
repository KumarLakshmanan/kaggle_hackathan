"""Bind the three prospectively selected opening families to a bounded panel."""
from datetime import datetime, timezone
import json
from pathlib import Path
from run_panel import ROOT, HERE, sha

folder = ROOT / 'diagnostics/fresh90_current_opening_20260929'
validation_path = folder / 'candidate_validation.json'
validation = json.loads(validation_path.read_text())
assert len(validation['candidate_results']) == 3
assert validation['checks']['game_runs'] == 0
top20 = json.loads((HERE / 'fresh_top100_entries.json').read_text(encoding='utf-8'))[:20]
public_path = ROOT / 'diagnostics/fresh90_refresh_20260929/routes/current_submission_56680167_opponents/summary.json'
loss_ids = {115319884, 115315638, 115302829}
public_losses = [e for e in json.loads(public_path.read_text(encoding='utf-8')) if int(e['episode_id']) in loss_ids]
assert len(top20) == 20 and {e['rank'] for e in top20} == set(range(1, 21))
assert len(public_losses) == 3
entries = top20 + public_losses
jobs = []
for c in validation['candidate_results']:
    assert sha(c['path']) == c['sha256']
    label = f"opening_family{c['candidate_id']}"
    for e in entries:
        fixture = f"{e['team_id']}:{e['episode_id']}"
        for seat in (0, 1):
            jobs.append(dict(job_id=f'{label}:{fixture}:{seat}', fixture_id=fixture,
                label=label, path=c['path'], candidate_sha256=c['sha256'],
                candidate_seat=seat, rank=int(e['rank']), team=e['team'],
                team_id=int(e['team_id']), episode_id=int(e['episode_id']), seed=int(e['seed']),
                action_sha256=e['action_sha256'], replay_sha256=e['replay_sha256'],
                dataset='top20' if int(e['rank']) <= 20 else 'public_loss3', entry=e))
assert len(jobs) == 138
job_path = HERE / 'opening_pilot_jobs.json'
assert not job_path.exists()
job_path.write_text(json.dumps(jobs, indent=2), encoding='utf-8')
freeze = dict(at_utc=datetime.now(timezone.utc).isoformat(), games=len(jobs),
    jobs_sha256=sha(job_path), plan_sha256=sha(HERE / 'OPENING_PILOT_PLAN.md'),
    architecture_plan_sha256=sha(folder / 'PLAN.md'),
    validation_sha256=sha(validation_path), candidates=validation['candidate_results'])
(HERE / 'opening_pilot_freeze.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')
print(json.dumps(dict(games=len(jobs), jobs_sha256=sha(job_path), candidates=len(validation['candidate_results']))))
