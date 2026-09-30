"""Apply the frozen route search selection rule and freeze both-seat controls."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
from run_panel import HERE, sha

parser = argparse.ArgumentParser()
parser.add_argument('--directory', default='route_search', choices=('route_search', 'broad_routes'))
args = parser.parse_args()
d = HERE / args.directory
plan = HERE / ('ROUTE_SEARCH_PLAN.md' if args.directory == 'route_search' else 'BROAD_ROUTE_PLAN.md')
receipt = json.loads((d / 'screen_jobs_receipt.json').read_text())
assert receipt['complete'] and receipt['completed_games'] == receipt['planned_games']
rows = [json.loads(s) for s in (d / 'screen_jobs_results.jsonl').read_text().splitlines()]
assert all(r.get('candidate_status') == r.get('opponent_status') == 'DONE' and r.get('frames') == 720
           and not r.get('error') and not r.get('candidate_errors') for r in rows)
variants = json.loads((d / 'variants.json').read_text())
baseline = [json.loads(s) for s in (HERE / 'cb76_top100_jobs_results.jsonl').read_text().splitlines()]
entries = json.loads((HERE / 'fresh_top100_entries.json').read_text())
grouped = defaultdict(list)
for v in variants:
    vr = [r for r in rows if r['label'] == v['label']]
    grouped[v['pair']].append(v | dict(target_wins=sum(r['result'] == 'win' for r in vr),
                                      target_sum_margin=sum(r['margin'] for r in vr),
                                      target_ranks=sorted(r['rank'] for r in vr)))
selected = []
ranking = {}
for pair, options in sorted(grouped.items()):
    options.sort(key=lambda v: (-v['target_wins'], -v['target_sum_margin'], int(v['route'])))
    ranking[pair] = options
    selected.extend(v for v in options[:3] if v['target_wins'] > 0)
assert not (d / 'stage2_jobs.json').exists()
jobs = []
reused = []
for v in selected:
    ranks = {r['rank'] for r in baseline if r['candidate_telemetry']['minimal_route_pair144'] == v['pair']}
    for entry in entries:
        if entry['rank'] not in ranks:
            continue
        fixture = f"{entry['team_id']}:{entry['episode_id']}"
        for seat in (0, 1):
            job = dict(job_id=f"{v['label']}:{fixture}:{seat}", fixture_id=fixture, label=v['label'],
                       path=v['path'], candidate_sha256=v['candidate_sha256'], candidate_seat=seat,
                       rank=entry['rank'], team=entry['team'], team_id=entry['team_id'],
                       episode_id=entry['episode_id'], seed=entry['seed'],
                       action_sha256=entry['action_sha256'], replay_sha256=entry['replay_sha256'],
                       pair=v['pair'], route=v['route'], entry=entry)
            jobs.append(job)
            old = next((r for r in rows if r['job_id'] == job['job_id']), None)
            if old:
                assert all(old[k] == job[k] for k in ('candidate_sha256', 'action_sha256', 'replay_sha256', 'candidate_seat'))
                reused.append(old | dict(reused_from=str(d / 'screen_jobs_results.jsonl'),
                                         reused_ledger_sha256=sha(d / 'screen_jobs_results.jsonl')))
(d / 'stage1_ranking.json').write_text(json.dumps(ranking, indent=2), encoding='utf-8')
(d / 'stage2_selection.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
if jobs:
    (d / 'stage2_jobs.json').write_text(json.dumps(jobs, indent=2), encoding='utf-8')
    (d / 'stage2_jobs_results.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in reused), encoding='utf-8')
freeze = dict(at_utc=datetime.now(timezone.utc).isoformat(), selected_variants=len(selected),
              jobs=len(jobs), exact_reused_rows=len(reused), screen_results_sha256=sha(d / 'screen_jobs_results.jsonl'),
              stage2_jobs_sha256=sha(d / 'stage2_jobs.json') if jobs else None,
              plan_sha256=sha(plan), builder_sha256=sha(__file__),
              selection=[dict(pair=v['pair'], route=v['route'], wins=v['target_wins'], sum_margin=v['target_sum_margin']) for v in selected])
(d / 'stage2_freeze.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')
print(json.dumps(freeze, indent=2))
