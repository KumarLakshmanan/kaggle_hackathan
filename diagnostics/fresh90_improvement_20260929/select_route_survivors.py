"""Adjudicate the predeclared both-seat complete-route control gates."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from run_panel import HERE, sha

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
args = p.parse_args()
d = args.directory.resolve()
assert not (d / 'survivors.json').exists()
receipt = json.loads((d / 'stage2_jobs_receipt.json').read_text())
assert receipt['complete']
rows = [json.loads(s) for s in (d / 'stage2_jobs_results.jsonl').read_text().splitlines()]
selection = json.loads((d / 'stage2_selection.json').read_text())
baseline = [json.loads(s) for s in (HERE / 'cb76_top100_jobs_results.jsonl').read_text().splitlines()]
lookup = {(r['fixture_id'], r['candidate_seat']): r for r in baseline}
point = {'win': 1, 'draw': .5, 'loss': 0}
out = []
for variant in selection:
    rr = [r for r in rows if r['label'] == variant['label']]
    clean = all(r.get('candidate_status') == r.get('opponent_status') == 'DONE' and r.get('frames') == 720
                and not r.get('candidate_errors') and not r.get('error') for r in rr)
    lost = [r for r in rr if lookup[r['fixture_id'], r['candidate_seat']]['result'] == 'win' and r['result'] != 'win']
    gained = [r for r in rr if r['result'] == 'win' and lookup[r['fixture_id'], r['candidate_seat']]['result'] != 'win']
    delta = sum(point[r['result']] - point[lookup[r['fixture_id'], r['candidate_seat']]['result']] for r in rr)
    targets = [r for r in rr if r['rank'] in variant['target_ranks']]
    result = variant | dict(clean=clean, wins=sum(r['result'] == 'win' for r in rr), games=len(rr),
                             point_gain=delta, lost_baseline_wins=[dict(rank=r['rank'], seat=r['candidate_seat'], margin=r['margin']) for r in lost],
                             gained_wins=[dict(rank=r['rank'], seat=r['candidate_seat'], margin=r['margin']) for r in gained],
                             min_target_margin=min(r['margin'] for r in targets), sum_margin=sum(r['margin'] for r in rr),
                             passes=clean and not lost and delta > 0)
    out.append(result)
passing = defaultdict(list)
for r in out:
    if r['passes']:
        passing[r['pair']].append(r)
survivors = []
for pair, options in sorted(passing.items()):
    options.sort(key=lambda r: (-r['wins'], -r['min_target_margin'], -r['sum_margin'], int(r['route'])))
    survivors.append(options[0])
(d / 'stage2_adjudication.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
(d / 'survivors.json').write_text(json.dumps(survivors, indent=2), encoding='utf-8')
freeze = dict(at_utc=datetime.now(timezone.utc).isoformat(), result_sha256=sha(d / 'stage2_jobs_results.jsonl'),
              selected=len(survivors), survivors_sha256=sha(d / 'survivors.json'),
              decisions=[dict(pair=r['pair'], route=r['route'], passes=r['passes'], point_gain=r['point_gain'],
                              lost_baseline_wins=r['lost_baseline_wins'], gained_wins=r['gained_wins']) for r in out],
              winning_rules={r['pair']: r['route'] for r in survivors}, promotion=False)
(d / 'stage2_decision.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')
print(json.dumps(freeze, indent=2))
