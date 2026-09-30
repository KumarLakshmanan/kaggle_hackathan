from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.opening_probe_v2_20260928.qualify import play,sha,MANIFEST,MANIFEST_SHA
from diagnostics.local_target_20260928.run_lock import exclusive_run


def key(row):return row['rival'],row['candidate_seat']


def main(phase,workers):
    pool=json.loads((HERE/'pool.json').read_text(encoding='utf-8'))
    screen=json.loads((HERE/'fast_screen.json').read_text(encoding='utf-8'))
    assert screen['complete'] and screen['passed'] and screen['pool_sha256']==sha(HERE/'pool.json')
    assert screen['plan_sha256']==pool['plan_sha256']==sha(HERE/'PLAN.md')
    candidate=next(v for v in pool['variants'] if v['version']==screen['selected'])
    assert sha(candidate['candidate'])==candidate['candidate_sha256']
    assert sha(ROOT/'main.py')=='4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
    assert sha(MANIFEST)==MANIFEST_SHA
    control={(r['fixture_id'],r['candidate_seat']):r for r in screen['games'] if r['version']==screen['selected']}
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    fixtures=pool['fixtures'] if phase=='parity' else manifest['live_losses']+manifest['current_top20']
    prior=[]
    if phase=='full':
        parity=json.loads((HERE/'native_parity.json').read_text(encoding='utf-8'))
        assert parity['complete'] and parity['passed'] and parity['candidate_sha256']==candidate['candidate_sha256']
        assert parity['plan_sha256']==pool['plan_sha256']
        prior=parity['games']
    jobs=[]
    for f in fixtures:
        for seat in (0,1):
            base=next(r for r in f['baseline_frozen_tape_both_seat_outcomes'] if r['seat']==seat)
            jobs.append(dict(version=screen['selected'],rival=f['fixture_id'],team=f['team'],
                panel='loss30' if f['fixture_id'].startswith('live-') else 'top20',
                seed=int(f['seed']),candidate_seat=seat,path=candidate['candidate'],candidate_sha256=candidate['candidate_sha256'],
                opponent='rawroute:'+f['source_action_tape_path'],opponent_action_sha256=f['source_opponent_action_sha256'],
                plan_sha256=pool['plan_sha256'],baseline_result=base['result'],baseline_margin=base['margin']))
    expected={key(j):j for j in jobs};assert len(expected)==len(jobs)
    checkpoint=HERE/('native_'+phase+'.jsonl')
    if checkpoint.exists():
        rows=[json.loads(s) for s in checkpoint.read_text(encoding='utf-8').splitlines()]
    else:
        rows=list(prior)
        if rows:checkpoint.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    for row in rows:assert all(row[k]==v for k,v in expected[key(row)].items())
    done={key(r) for r in rows};assert len(done)==len(rows)
    pending=[j for j in jobs if key(j) not in done]
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(pending),16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(play,j) for j in pending[start:start+16]]):
                    row=future.result();assert key(row) not in done
                    done.add(key(row));rows.append(row)
                    output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush()
                    if len(rows)%2==0:print(f'{phase} {len(rows)}/{len(jobs)} {row["team"]} {row["result"]} {row["margin"]:+.0f}',flush=True)
    clean=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' and not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    fields=('candidate_reward','opponent_reward','candidate_telemetry','frames','candidate_status','opponent_status')
    parity=all(all(r[k]==control[key(r)][k] for k in fields) for r in rows if key(r) in control)
    preserved=all(r['result']=='win' for r in rows if r['baseline_result']=='win')
    summaries=[];rescues=[]
    for panel in ('loss30','top20'):
        arm=[r for r in rows if r['panel']==panel];pairs={r['rival']:[] for r in arm}
        for row in arm:pairs[row['rival']].append(row)
        rescued=[rs[0]['team'] for rs in pairs.values() if all(r['result']=='win' for r in rs) and any(r['baseline_result']!='win' for r in rs)]
        rescues.extend(rescued)
        summaries.append(dict(panel=panel,fixtures=len(pairs),both_seat_wins=sum(all(r['result']=='win' for r in rs) for rs in pairs.values()),
                              WDL=[sum(r['result']==outcome for r in arm) for outcome in ('win','draw','loss')],rescued=rescued))
    result=dict(complete=len(rows)==len(jobs),passed=clean and parity and preserved and bool(rescues),
                phase=phase,candidate=candidate['candidate'],candidate_sha256=candidate['candidate_sha256'],
                plan_sha256=pool['plan_sha256'],fast_screen_sha256=sha(HERE/'fast_screen.json'),
                clean=clean,fast_native_parity=parity,incumbent_win_preservation=preserved,
                summaries=summaries,completed_at_utc=datetime.now(timezone.utc).isoformat(),games=sorted(rows,key=key))
    (HERE/('native_'+phase+'.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('parity','full'))
    parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
    with exclusive_run(HERE/'qualify.lock'):main(args.phase,args.workers)
