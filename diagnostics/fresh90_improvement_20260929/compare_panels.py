"""Write paired case CSV/Markdown and hash-bound summaries from completed ledgers."""
import argparse
import csv
import json
from pathlib import Path
from run_panel import sha, assess

p = argparse.ArgumentParser()
p.add_argument('baseline', type=Path)
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--context', default='Fixed-replay development; not an online win-rate estimate.')
args = p.parse_args()
old = [json.loads(s) for s in args.baseline.read_text(encoding='utf-8').splitlines()]
new = [json.loads(s) for s in args.candidate.read_text(encoding='utf-8').splitlines()]
index = {(r['fixture_id'], r['candidate_seat']): r for r in old}
assert len(index) == len(old), 'Choose a single baseline variant'
new_index = {(r['fixture_id'], r['candidate_seat']): r for r in new}
assert len(new_index) == len(new), 'Choose a single candidate variant'
assert set(new_index) <= set(index), 'Every new row needs its own exact baseline'
points = {'win': 1, 'draw': .5, 'loss': 0}
pairs = []
for r in sorted(new, key=lambda r: (r['rank'], r['episode_id'], r['candidate_seat'])):
    b = index[r['fixture_id'], r['candidate_seat']]
    assert b['action_sha256'] == r['action_sha256'] and b['replay_sha256'] == r['replay_sha256']
    assert not r.get('error') and not b.get('error')
    pairs.append(dict(rank=r['rank'], team=r['team'], episode=r['episode_id'], seat=r['candidate_seat'],
                      baseline_result=b['result'], candidate_result=r['result'],
                      baseline_own=b['candidate_reward'], candidate_own=r['candidate_reward'],
                      baseline_rival=b['opponent_reward'], candidate_rival=r['opponent_reward'],
                      baseline_margin=b['margin'], candidate_margin=r['margin'],
                      delta_own=r['candidate_reward'] - b['candidate_reward'],
                      delta_rival=r['opponent_reward'] - b['opponent_reward'],
                      delta_margin=r['margin'] - b['margin'],
                      delta_points=points[r['result']] - points[b['result']],
                      candidate_sha256=r['candidate_sha256'], action_sha256=r['action_sha256'],
                      replay_sha256=r['replay_sha256']))
summary = dict(context=args.context, games=len(pairs),
               baseline_sha256=sorted({r['candidate_sha256'] for r in old}),
               candidate_sha256=sorted({r['candidate_sha256'] for r in new}),
               baseline_ledger_sha256=sha(args.baseline), candidate_ledger_sha256=sha(args.candidate),
               candidate_assessment=assess(new),
               baseline_assessment=assess([index[k] for k in new_index]),
               gained_wins=[r for r in pairs if r['candidate_result'] == 'win' and r['baseline_result'] != 'win'],
               lost_wins=[r for r in pairs if r['baseline_result'] == 'win' and r['candidate_result'] != 'win'],
               delta_points=sum(r['delta_points'] for r in pairs),
               mean_delta_margin=sum(r['delta_margin'] for r in pairs) / len(pairs))
csvpath = args.output.with_suffix('.csv')
jsonpath = args.output.with_suffix('.json')
mdpath = args.output.with_suffix('.md')
assert not any(path.exists() for path in (csvpath, jsonpath, mdpath))
with csvpath.open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(pairs[0]))
    writer.writeheader()
    writer.writerows(pairs)
jsonpath.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
lines = ['# Paired replay cases', '', args.context, '',
         f"Games: {len(pairs)}; gained winning seats: {len(summary['gained_wins'])}; lost winning seats: {len(summary['lost_wins'])}.", '',
         '| Rank/index | Team | Episode | Seat | Baseline | Candidate | Baseline margin | Candidate margin | Margin change |',
         '|---:|---|---:|---:|---|---|---:|---:|---:|']
for r in pairs:
    team = str(r['team']).replace('|', '\\|')
    lines.append(f"| {r['rank']} | {team} | {r['episode']} | {r['seat']} | {r['baseline_result']} | {r['candidate_result']} | {r['baseline_margin']:,.0f} | {r['candidate_margin']:,.0f} | {r['delta_margin']:+,.0f} |")
mdpath.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({k: summary[k] for k in ('games', 'delta_points', 'mean_delta_margin', 'candidate_assessment', 'baseline_assessment')}, indent=2))
print(json.dumps(dict(gained_wins=len(summary['gained_wins']), lost_wins=len(summary['lost_wins']), csv=str(csvpath), report=str(mdpath))))
