"""Materialize every paired saved-top100 result without rerunning any games."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (HERE / 'top100_results.jsonl').read_text().splitlines()]
pairs = {}
for row in rows:
    pairs.setdefault((row['rank'], row['fixture_id'], row['candidate_seat']), {})[row['version']] = row
assert len(rows) == 400 and len(pairs) == 200
table = []
for key, pair in sorted(pairs.items()):
    assert set(pair) == {'baseline', 'candidate'}
    base, candidate = pair['baseline'], pair['candidate']
    table.append(dict(rank=key[0], team=candidate['rival'], fixture_id=key[1], seed=candidate['seed'],
                      seat=key[2], baseline_result=base['result'], candidate_result=candidate['result'],
                      baseline_own_coins=base['candidate_reward'], candidate_own_coins=candidate['candidate_reward'],
                      baseline_rival_coins=base['opponent_reward'], candidate_rival_coins=candidate['opponent_reward'],
                      baseline_margin=base['margin'], candidate_margin=candidate['margin'],
                      margin_gain=candidate['margin'] - base['margin']))
with (HERE / 'TOP100_PAIRED.csv').open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(table[0]))
    writer.writeheader()
    writer.writerows(table)
lines = ['# Every saved top100 matchup', '',
         'Snapshot: 2026-09-29 22:34:23 IST. Opponent actions are fixed tapes; this is not a live-policy win-rate estimate.', '',
         '| Rank | Team | Baseline wins / 2 seats | Engine wins / 2 seats | Mean paired margin gain |',
         '|---:|---|---:|---:|---:|']
for rank in sorted({r['rank'] for r in table}):
    cases = [r for r in table if r['rank'] == rank]
    assert len(cases) == 2
    team = cases[0]['team'].replace('|', '\\|')
    lines.append(f"| {rank} | {team} | {sum(r['baseline_result']=='win' for r in cases)}/2 | {sum(r['candidate_result']=='win' for r in cases)}/2 | {sum(r['margin_gain'] for r in cases)/2:+,.0f} |")
(HERE / 'TOP100_PAIRED.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Wrote all 200 paired seats and all 100 opponent summaries.')
