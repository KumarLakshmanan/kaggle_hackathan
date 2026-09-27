from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a+b
    return a


def command(row, actor):
    if actor == 0:
        return row['action'].get('farmer', ['PASS'])
    hands = row['action'].get('hands', [])
    return hands[actor-1] if actor <= len(hands) else ['PASS']


def empty(tile):
    return tile is None or isinstance(tile, dict) and tile.get('kind') == 'WEED'


def audit(record):
    raw = gzip.decompress(Path(record['trace_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == record['trace_sha256']
    trace = json.loads(raw)
    seat = record['candidate_seat']
    rows = trace['traces'][seat]
    assert len(rows) == 719
    days = []
    for day in range(12, 30):
        subset = rows[day*24:min((day+1)*24,719)]
        n = max(len(r['observation']['farms'][seat]['hands']) for r in subset)
        windows = []
        for actor in range(n+1):
            first = len(subset)
            for i in range(len(subset)-1, -1, -1):
                farm = subset[i]['observation']['farms'][seat]
                if actor > len(farm['hands']) or command(subset[i], actor)[0] != 'PASS':
                    break
                first = i
            if len(subset)-first < 4:
                continue
            obs = subset[first]['observation']
            farm = obs['farms'][seat]
            pos = farm['farmer'] if actor == 0 else farm['hands'][actor-1]
            windows.append(dict(actor=actor, first_hour=first, actions=len(subset)-first,
                                position=pos, inventory=obs['private']['inventories'][actor]))
        days.append(dict(day=day+1, hands=n, one_extra_wage=fib(n),
                         two_extra_wage=fib(n)+fib(n+1), windows=windows))
    starts = []
    for start in range(12,18):
        obs = rows[start*24+2]['observation']
        farm = obs['farms'][seat]
        current = [(x,y) for y in range(10) for x in range(10) if empty(farm['tiles'][y][x])]
        persistent = [(x,y) for x,y in current if all(empty(r['observation']['farms'][seat]['tiles'][y][x])
                       for r in rows[start*24+2:(start+12)*24])]
        # Rectangular six-cell blocks make an explicit compact working area.
        blocks = []
        available = set(persistent)
        for w,h in ((2,3),(3,2)):
            for x in range(11-w):
                for y in range(11-h):
                    block = {(x+dx,y+dy) for dx in range(w) for dy in range(h)}
                    if block <= available:
                        blocks.append(sorted(block))
        dd = [r for r in days if start+1 <= r['day'] <= start+12]
        starts.append(dict(start_day=start+1,
                           tomato_shops=sum(s in ('FARMERS_MARKET','PIZZA_SHOP') for s in obs['town']['unlocked_shops']),
                           current_free=current, persistent_free=persistent, six_cell_blocks=blocks,
                           min_hands=min(d['hands'] for d in dd), max_hands=max(d['hands'] for d in dd),
                           one_worker_wages=sum(d['one_extra_wage'] for d in dd),
                           two_worker_wages=sum(d['two_extra_wage'] for d in dd),
                           days_with_idle_windows=sum(bool(d['windows']) for d in dd),
                           minimum_daily_total_idle_actions=min(sum(w['actions'] for w in d['windows']) for d in dd)))
    return dict(episode_id=record['episode_id'], opponent=record['opponent'],
                trace_sha256=record['trace_sha256'], starts=starts, days=days)


if __name__ == '__main__':
    target = HERE/'audit.json'
    assert not target.exists()
    out = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), independent_strength_evidence=False,
               plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(), games=[])
    for folder in ('disjoint_live_top100_cash_20260927','disjoint_live_cash_1022_20260927'):
        source = json.loads((ROOT/'diagnostics'/folder/'ledger.json').read_text())
        assert source['complete']
        for record in source['games']:
            result = audit(record)
            out['games'].append(result)
            print(result['opponent'], [(s['start_day'],len(s['persistent_free']),len(s['six_cell_blocks']),
                                       s['minimum_daily_total_idle_actions']) for s in result['starts']], flush=True)
    out.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat())
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
