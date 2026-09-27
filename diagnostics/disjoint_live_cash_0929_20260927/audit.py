from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run
from diagnostics.live_refresh_56530281_20260926.cash_ledger_close import ledger

MAIN = ROOT / 'main_uploaded_disjoint_integrated_20260927_c68fa46f.py'
SHA = 'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'


def audit(live):
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == SHA
    raw = gzip.decompress(Path(live['replay_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == live['replay_sha256']
    replay = json.loads(raw)
    seat = live['candidate_seat']
    eid = live['episode_id']
    route = HERE / 'routes' / f'{eid}.json.gz'
    actions = [frame[1-seat]['action'] for frame in replay['steps'][1:]]
    route.write_bytes(gzip.compress(json.dumps({'actions': actions}, separators=(',', ':')).encode()))
    data = run(str(MAIN), 'rawroute:' + str(route), int(live['seed']), seat)
    trace_path = HERE / 'traces' / f'{eid}.json.gz'
    trace_raw = json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    trace_path.write_bytes(gzip.compress(trace_raw))
    cash_match = [data['candidate_reward'], data['opponent_reward']] == [live['own_cash'], live['opponent_cash']]
    action_match = [t['action'] for t in data['traces'][seat]] == [f[seat]['action'] for f in replay['steps'][1:]]
    assert data['candidate_status'] == data['opponent_status'] == 'DONE'
    assert cash_match and action_match, f'Live parity failure in {eid}'
    own, rival = ledger(data, seat), ledger(data, 1-seat)
    items = sorted(set(own['net_market_by_item']) | set(rival['net_market_by_item']))
    differences = {item: own['net_market_by_item'].get(item, 0) - rival['net_market_by_item'].get(item, 0) for item in items}
    atomic = sum(own['atomic_cash'].values()) - sum(rival['atomic_cash'].values())
    other = own['other_cash'] - rival['other_cash']
    assert sum(differences.values()) + atomic + other == live['margin']
    failed = [e for e in data['events'] if e['phase'] == 'market_unit' and not e['success'] and e['operation'].startswith('BUY')]
    failures = {}
    for p, label in ((seat, 'ours'), (1-seat, 'rival')):
        rows = [e for e in failed if e['player'] == p]
        failures[label] = dict(counts=dict(Counter((e['operation'] + ':' + e['item'] + ':' + str(e['failure_reason'])) for e in rows)), events=rows)
    return dict(episode_id=eid, opponent=live['opponent'], candidate_seat=seat, margin=live['margin'],
                source_replay_sha256=live['replay_sha256'], source_cash_parity=cash_match,
                all_719_source_actions_match=action_match, ours=own, rival=rival,
                net_item_differences=differences, atomic_cash_difference=atomic, other_cash_difference=other,
                failed_purchases=failures, trace_path=str(trace_path), trace_sha256=hashlib.sha256(trace_raw).hexdigest())


if __name__ == '__main__':
    previous = json.loads((ROOT / 'diagnostics/disjoint_live_audit_20260927/cohort_0915.json').read_text())
    current = json.loads((ROOT / 'diagnostics/disjoint_live_audit_20260927/cohort_0929.json').read_text())
    old_ids = {g['episode_id'] for g in previous['games']}
    selected = [g for g in current['games'] if g['episode_id'] not in old_ids]
    assert len(selected) == 5
    for name in ('routes', 'traces'):
        (HERE / name).mkdir(exist_ok=True)
    target = HERE / 'ledger.json'
    assert not target.exists()
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), main_sha256=SHA,
               selection='All five newly listed games in 09:29 versus 09:15 snapshots',
               independent_strength_evidence=False, complete=False, games=[])
    def save():
        target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(audit, g) for g in selected]):
            row = future.result()
            out['games'].append(row)
            save()
            print(f"{len(out['games'])}/5 {row['episode_id']} {row['opponent']} margin={row['margin']:+} cash/action parity passed", flush=True)
    out.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat())
    save()
    for g in sorted(out['games'], key=lambda g: g['episode_id']):
        print(g['opponent'], g['margin'], 'net-item differences', g['net_item_differences'],
              'atomic', g['atomic_cash_difference'], 'unexplained', g['other_cash_difference'], flush=True)
