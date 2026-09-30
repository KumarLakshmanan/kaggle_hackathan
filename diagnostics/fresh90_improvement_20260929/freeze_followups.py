"""Freeze public and reserved evaluations after exact combined development passes."""
from datetime import datetime, timezone
import json
from run_panel import HERE, ROOT, sha

manifest = json.loads((HERE / 'combined_v1_manifest.json').read_text())
candidate = manifest['candidate']
assert sha(candidate) == manifest['candidate_sha256']
receipt = json.loads((HERE / 'combined_v1_top100_jobs_receipt.json').read_text())
assert receipt['complete'] and receipt['completed_games'] == 200
def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines()]
old = rows(HERE / 'cb76_top100_jobs_results.jsonl')
land = rows(HERE / 'funded_land_top100_jobs_results.jsonl')
new = rows(HERE / 'combined_v1_top100_jobs_results.jsonl')
index = {(r['fixture_id'], r['candidate_seat']): r for r in new}
assert receipt['assessment']['combined_v1']['all']['all_clean']
for r in old + (land if manifest['use_funded_land'] else []):
    if r['result'] == 'win':
        assert index[r['fixture_id'], r['candidate_seat']]['result'] == 'win'
assert sum(r['result'] == 'win' for r in new) > sum(r['result'] == 'win' for r in (land if manifest['use_funded_land'] else old))
datasets = {'public27': ROOT / 'diagnostics/fresh90_refresh_20260929/routes/current_submission_56680167_opponents/summary.json',
            'reserved2': ROOT / 'diagnostics/fresh90_refresh_20260929/routes/episode_2/summary.json',
            'reserved3': ROOT / 'diagnostics/fresh90_refresh_20260929/routes/episode_3/summary.json'}
versions = {'cb76': HERE / 'baseline_cb76fbc4.py', 'combined_v1': candidate}
files = []
development_episodes = {r['episode_id'] for r in old}
overlap = {}
for dataset, path in datasets.items():
    entries = json.loads(path.read_text(encoding='utf-8'))
    episodes = {e['episode_id'] for e in entries}
    overlap[dataset] = dict(fixtures=len(entries), distinct_episodes=len(episodes),
                             episodes_also_in_development=sorted(episodes & development_episodes))
    for label, source in versions.items():
        output = HERE / f'{label}_{dataset}_jobs.json'
        if output.exists():
            assert dataset == 'public27' and label == 'cb76'
            continue
        jobs = []
        for entry in sorted(entries, key=lambda e: (int(e['rank']), int(e['episode_id']))):
            fixture = f"{entry['team_id']}:{entry['episode_id']}"
            for seat in (0, 1):
                jobs.append(dict(job_id=f'{label}:{fixture}:{seat}', fixture_id=fixture,
                    label=label, path=str(source), candidate_sha256=sha(source),
                    candidate_seat=seat, rank=int(entry['rank']), team=entry['team'],
                    team_id=int(entry['team_id']), episode_id=int(entry['episode_id']), seed=int(entry['seed']),
                    action_sha256=entry['action_sha256'], replay_sha256=entry['replay_sha256'],
                    dataset=dataset, entry=entry))
        output.write_text(json.dumps(jobs, indent=2), encoding='utf-8')
        files.append(dict(path=str(output), sha256=sha(output), games=len(jobs)))
freeze = dict(at_utc=datetime.now(timezone.utc).isoformat(), candidate_sha256=sha(candidate),
              development_gate_passed=True, files=files, overlap=overlap,
              note='Reserved replay controls are correlated diagnostics; not independent policy validation.')
(HERE / 'combined_v1_followup_freeze.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')
print(json.dumps(freeze, indent=2))
