"""Explain where the submitted 4ee and 257 policies differ on matched tapes."""
import json
from collections import Counter, defaultdict
from pathlib import Path

here = Path(__file__).resolve().parent
rows = [json.loads(s) for s in (here / 'local_results.jsonl').read_text(encoding='utf-8').splitlines()]
by_key = {(r['rank'], r['candidate_seat'], r['label']): r for r in rows}
out = []
for rank in range(1, 101):
    for seat in (0, 1):
        old = by_key[rank, seat, '4eeac9c3']
        new = by_key[rank, seat, '257f941d']
        if (old['candidate_reward'], old['opponent_reward']) == (new['candidate_reward'], new['opponent_reward']):
            continue
        t = new['candidate_telemetry']
        active = {k: v for k, v in t.items() if (k.endswith('_turns') or k.endswith('_active72') or k.endswith('_triggered_step1')) and bool(v)}
        selected = {k: v for k, v in t.items() if (k.endswith('_selected') or k.endswith('_route') or k.endswith('_route72') or k.endswith('_route144') or k.endswith('_branch72') or k.endswith('_branch144')) and v not in ('', None, 'source')}
        out.append({'rank': rank, 'team': old['team'], 'seat': seat,
                    'old': old['result'], 'new': new['result'],
                    'old_margin': old['margin'], 'new_margin': new['margin'],
                    'delta_margin': new['margin'] - old['margin'],
                    'old_cash': old['candidate_reward'], 'new_cash': new['candidate_reward'],
                    'old_rival': old['opponent_reward'], 'new_rival': new['opponent_reward'],
                    'active': active, 'selected': selected})
out.sort(key=lambda r: (r['rank'], r['seat']))
def branch(row):
    a, s = row['active'], row['selected']
    if s.get('bridge_selected') == 'shared151':
        return 'donor/bridge shared151 ' + str(s.get('donor_selected', ''))
    for key in ('loss_pool', 'compatible_pool', 'guard_route', 'a44_goose4',
                'a44_ghost_wheat', 'a44_smoothie', 'a44_kwa_wheat_zero',
                'piice', 'iso_pasture', 'a44_pet_market_gate', 'hire_recovery',
                'partial_plant'):
        if a.get(key + '_turns'):
            return key + ' ' + str(s.get(key + '_route', s.get(key + '_route72', s.get(key + '_selected', ''))))
    return 'other'

for row in out:
    row['branch'] = branch(row)
summary = {
    'changed_seats': len(out), 'changed_teams': len({r['rank'] for r in out}),
    'old_to_new': dict(Counter(f"{r['old']}->{r['new']}" for r in out)),
    'branch_by_outcome': dict(Counter(f"{r['branch']} | {r['old']}->{r['new']}" for r in out)),
    'flipped_teams': [{k: v for k, v in row.items() if k in
                      ('rank', 'team', 'seat', 'old', 'new', 'old_margin', 'new_margin',
                       'delta_margin', 'branch')}
                      for row in out if row['seat'] == 0 and row['old'] != row['new']],
    'rows': out,
}
(here / 'delta_explanation.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, indent=2))
