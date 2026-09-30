"""Explain the saved development trace; no new games or policy decisions."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import gzip
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.animal_liquidity_20260928.screen import read, write, sha


def traces(path):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        return [json.loads(line) for line in stream]


def physical(frame):
    obs = frame['observation']
    farm = obs['farms'][int(obs['player'])]
    tiles = [t for row in farm['tiles'] for t in row if isinstance(t, dict)]
    animals = [t for t in tiles if t.get('animal')]
    return dict(crops=dict(Counter(t['crop'] for t in tiles if t.get('kind') == 'PLANT')),
                animals=dict(Counter(t['animal'] for t in animals)), fed=sum(bool(t['fed_today']) for t in animals),
                seeds=obs['private']['seeds'], wheat=obs['private']['shed'].get('WHEAT', 0), money=farm['money'])


def main():
    result = read(HERE / 'screen.json')
    assert result['complete']
    rows = []
    for row in result['games']:
        source = ROOT / 'diagnostics/observed_hire_recovery_20260928' / ('integrated_' + row['fixture_id'] + '_seat' + str(row['candidate_seat']) + '.jsonl.gz')
        current = Path(row['trace_path'])
        old, new = traces(source), traces(current)
        assert len(old) == len(new) == 719
        diffs = [dict(step=a['step'], old=a['action'], new=b['action']) for a,b in zip(old,new) if a['action'] != b['action']]
        shop_diffs = [a['step'] for a,b in zip(old,new) if a['observation']['town'] != b['observation']['town']]
        seed_diffs = [a['step'] for a,b in zip(old,new) if a['observation']['private']['seeds'] != b['observation']['private']['seeds']]
        crop_diffs = [a['step'] for a,b in zip(old,new) if physical(a)['crops'] != physical(b)['crops']]
        days = [dict(step=step, old=physical(old[step]), new=physical(new[step])) for step in range(23, 719, 24)
                if physical(old[step]) != physical(new[step])]
        rows.append(dict(fixture_id=row['fixture_id'], team=row['team'], seat=row['candidate_seat'],
                         result=row['result'], candidate_reward=row['candidate_reward'], opponent_reward=row['opponent_reward'],
                         margin=row['margin'], delta_own=row['delta_own'], delta_rival=row['delta_rival'], delta_margin=row['delta_margin'],
                         telemetry={k:v for k,v in row['candidate_telemetry'].items() if k.startswith('animal_cash')},
                         action_changes=diffs, future_shop_difference_steps=shop_diffs,
                         seed_difference_steps=seed_diffs, crop_count_difference_steps=crop_diffs, day_physical_differences=days,
                         parent_trace_sha256=sha(source), candidate_trace_sha256=sha(current)))
    write(HERE / 'mechanism.json', dict(games=rows, screen_sha256=sha(HERE / 'screen.json'),
                                       completed_at_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps([dict(team=r['team'],seat=r['seat'],margin=r['margin'],delta_own=r['delta_own'],delta_rival=r['delta_rival'],
                           changes=len(r['action_changes']),shop_diffs=len(r['future_shop_difference_steps']),
                           seed_diffs=len(r['seed_difference_steps']),crop_diffs=len(r['crop_count_difference_steps']),
                           telemetry=r['telemetry']) for r in rows], indent=2))


if __name__ == '__main__':
    main()
