"""Export paired reacting cases without treating seats as independent seeds."""
import argparse
import csv
import json
from run_panel import HERE, sha

p = argparse.ArgumentParser()
p.add_argument('label')
p.add_argument('phase', choices=('screen', 'confirm'))
a = p.parse_args()
prefix = HERE / f'{a.label}_{a.phase}'
ledger = prefix.with_name(prefix.name + '_results.jsonl')
receipt_path = prefix.with_name(prefix.name + '_receipt.json')
receipt = json.loads(receipt_path.read_text())
assert receipt['complete'] and receipt['results_sha256'] == sha(ledger)
rows = [json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()]
groups = {}
for r in rows:
    groups.setdefault((r['seed'], r['rival'], r['candidate_seat']), {})[r['version']] = r
points = {'win': 1, 'draw': .5, 'loss': 0}
pairs = []
for (seed, rival, seat), pair in sorted(groups.items()):
    assert set(pair) == {'candidate', 'baseline'}
    b, c = pair['baseline'], pair['candidate']
    assert b['opponent_sha256'] == c['opponent_sha256'] and b['method'] == c['method']
    assert not b.get('error') and not c.get('error')
    pairs.append(dict(seed=seed, rival=rival, seat=seat, method=c['method'],
        baseline_result=b['result'], candidate_result=c['result'],
        baseline_own=b['candidate_reward'], candidate_own=c['candidate_reward'],
        baseline_rival=b['opponent_reward'], candidate_rival=c['opponent_reward'],
        baseline_margin=b['margin'], candidate_margin=c['margin'],
        delta_own=c['candidate_reward']-b['candidate_reward'],
        delta_rival=c['opponent_reward']-b['opponent_reward'],
        delta_margin=c['margin']-b['margin'],
        delta_points=points[c['result']]-points[b['result']],
        candidate_sha256=c['candidate_sha256'], baseline_sha256=b['candidate_sha256'],
        rival_sha256=c['opponent_sha256']))
path = prefix.with_name(prefix.name + '_paired_cases.csv')
assert not path.exists()
with path.open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
    writer.writeheader()
    writer.writerows(pairs)
print(json.dumps(dict(pairs=len(pairs), delta_points=sum(r['delta_points'] for r in pairs),
    csv=str(path), sha256=sha(path), assessment=receipt['assessment'])))
