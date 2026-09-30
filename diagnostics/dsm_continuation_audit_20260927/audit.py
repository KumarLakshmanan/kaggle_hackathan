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

CANDIDATE = ROOT / 'main_candidate_dsm_frontloaded_bank_20260927_dd420938.py'
CANDIDATE_SHA = 'dd4209389689bc8ecd33ac19124b754054cfc9439abc4f27bae3faf682abceff'
RIVAL = ROOT / 'main_uploaded_disjoint_integrated_20260927_c68fa46f.py'
RIVAL_SHA = 'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'


def audit(prior):
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_SHA
    assert hashlib.sha256(RIVAL.read_bytes()).hexdigest() == RIVAL_SHA
    seat, seed = prior['candidate_seat'], prior['seed']
    data = run(str(CANDIDATE), str(RIVAL), seed, seat)
    raw = json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    target = HERE / 'traces' / f'seed-{seed}-seat-{seat}.json.gz'
    target.write_bytes(gzip.compress(raw))
    assert data['candidate_status'] == data['opponent_status'] == 'DONE'
    assert [data['candidate_reward'], data['opponent_reward']] == [prior['candidate_reward'], prior['opponent_reward']]
    own, other = ledger(data, seat), ledger(data, 1-seat)
    assert own['other_cash'] == other['other_cash'] == 0
    failures = [e for e in data['events'] if e['phase']=='market_unit' and e['player']==seat and not e['success'] and e['operation'].startswith('BUY')]
    unchanged = [e for e in data['events'] if e['phase']=='unit_action' and e['player']==seat and not e['changed'] and e['action'] and e['action'][0]!='PASS']
    return dict(seed=seed, candidate_seat=seat, margin=prior['margin'], baseline_cash_match=True,
                ours=own, rival=other, failed_purchases=failures,
                failed_purchase_counts=dict(Counter(e['operation']+':'+e['item']+':'+str(e['failure_reason']) for e in failures)),
                unchanged_command_counts=dict(Counter(e['action'][0] for e in unchanged)),
                unchanged_commands=unchanged, trace_path=str(target), trace_sha256=hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    source = ROOT / 'diagnostics/dsm_frontloaded_bank_20260927/pilot.json'
    previous = json.loads(source.read_text())
    assert previous['complete'] and not previous['passed']
    all_seeds = sorted({g['seed'] for g in previous['games']})
    worst = min(all_seeds, key=lambda seed: sum(g['margin'] for g in previous['games'] if g['seed']==seed))
    selected = sorted({all_seeds[0], worst})
    assert len(selected) == 2
    jobs = [g for g in previous['games'] if g['seed'] in selected]
    assert len(jobs) == 4
    (HERE / 'traces').mkdir(exist_ok=True)
    target = HERE / 'audit.json'; assert not target.exists()
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(),
               selection='First and worst-margin paired seed from the rejected pilot, both seats',
               seeds=selected, original_pilot_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               candidate_sha256=CANDIDATE_SHA, rival_sha256=RIVAL_SHA,
               independent_strength_evidence=False, complete=False, games=[])
    def save(): target.write_text(json.dumps(out, indent=2), encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(audit,g) for g in jobs]):
            row=future.result();out['games'].append(row);save()
            print(f"{len(out['games'])}/4 seed={row['seed']} seat={row['candidate_seat']} margin={row['margin']:+} failed={row['failed_purchase_counts']}",flush=True)
    out.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat())
    save();print('COMPLETE',flush=True)
