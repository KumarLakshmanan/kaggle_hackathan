"""Source-bound, resumable candidate versus baseline games for this experiment."""
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(path,v):Path(path).write_text(json.dumps(v,indent=2),encoding='utf-8')

def execute(job):
    try:
        if job['kind']=='reactive':
            from diagnostics.physical_route_rollout_20260928.fast_reactive import play
            return play(job)
        if job['kind']=='native':
            from diagnostics.opening_probe_v2_20260928.qualify import play
            return play(job)
        sys.path.insert(0,str(ROOT/'diagnostics/submission_top100_compare_20260929_1104'))
        from fast_game_current import play
        entry=job['entry']
        fixture=dict(fixture_id=job['fixture_id'],seed=entry['seed'],source_replay_path=entry['replay_path'],
                     source_replay_sha256=entry['replay_sha256'],source_action_tape_path=entry['path'],
                     source_opponent_action_sha256=entry['action_sha256'])
        return dict(job,**{k:v for k,v in play(fixture,job['path'],job['candidate_sha256'],job['candidate_seat']).items() if k not in job})
    except Exception as error:
        return dict(job,error_type=type(error).__name__,error=str(error))

def assess(rows):
    groups={}
    for r in rows:
        v=r['version'];g=groups.setdefault(v,dict(games=0,wins=0,draws=0,losses=0,points=0.,margin=0.,changes=0,nodes=0,max_seconds=0.,clean=True))
        g['games']+=1
        result=r.get('result','error');g['wins']+=result=='win';g['draws']+=result=='draw';g['losses']+=result=='loss'
        g['points']+={'win':1.,'draw':.5,'loss':0.,'error':0.}[result]
        g['margin']+=r.get('margin',0)
        t=r.get('candidate_telemetry',{})
        g['changes']+=t.get('engine_changed_turns',0);g['nodes']+=t.get('engine_nodes',0)
        g['max_seconds']=max(g['max_seconds'],r.get('max_candidate_call_seconds',0))
        g['clean'] &= not r.get('error') and not r.get('candidate_errors') and not r.get('opponent_errors') and r.get('frames')==720 and r.get('candidate_status')==r.get('opponent_status')=='DONE'
    for g in groups.values():g['mean_margin']=g.pop('margin')/g['games']
    if set(groups)!={'candidate','baseline'}:return dict(groups=groups,passed=False)
    rivals={}
    for rival in sorted({r['rival'] for r in rows}):
        totals={v:sum({'win':1.,'draw':.5,'loss':0.}.get(r.get('result'),0) for r in rows if r['rival']==rival and r['version']==v) for v in groups}
        rivals[rival]=dict(totals,delta=totals['candidate']-totals['baseline'])
    activated={r.get('seed') for r in rows if r['version']=='candidate' and r.get('candidate_telemetry',{}).get('engine_changed_turns',0)>0}
    gain=groups['candidate']['points']-groups['baseline']['points']
    passed=all(g['clean'] for g in groups.values()) and gain>0 and all(v['delta']>=0 for v in rivals.values()) and len(activated)>=2
    return dict(groups=groups,per_opponent=rivals,point_gain=gain,activated_seeds=len(activated),passed=passed)

def build_jobs(phase,candidate):
    versions={'candidate':candidate,'baseline':HERE/'baseline_4eeac9c3.py'}
    rivals={'4ee':versions['baseline'],'cb76':ROOT/'main_candidate_minimal_repair_20260929_cb76fbc4.py'}
    if phase=='confirm':
        rivals.update(v35=ROOT/'diagnostics/public_ahmed_v35_20260927/public_v35_main.py',c95=ROOT/'diagnostics/public_rayk_top_meta/public_c95_main.py')
    jobs=[]
    if phase in ('top20','top100'):
        source=json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
        for fixture in source:
            if fixture['rank']>(20 if phase=='top20' else 100):continue
            for version,path in versions.items():
                jobs.append(dict(fixture,job_id=f'{version}:{fixture["fixture_id"]}:{fixture["candidate_seat"]}',
                                 kind='replay',rival=fixture['team'],version=version,path=str(path),candidate_sha256=sha(path)))
    else:
        seeds=range(33000001,33000005) if phase=='pilot' else range(33000101,33000117)
        for seed in seeds:
            for rival,opponent in rivals.items():
                for seat in (0,1):
                    for version,path in versions.items():
                        jobs.append(dict(job_id=f'{version}:{seed}:{rival}:{seat}',kind='native' if phase=='confirm' else 'reactive',
                                         version=version,rival=rival,seed=seed,candidate_seat=seat,path=str(path),
                                         candidate_sha256=sha(path),opponent=str(opponent),opponent_sha256=sha(opponent)))
    return jobs

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=('pilot','top20','top100','confirm'));p.add_argument('--workers',type=int,default=4)
    p.add_argument('--candidate',type=Path,default=HERE/'candidate_v1.py');args=p.parse_args()
    assert 1<=args.workers<=6
    candidate=args.candidate.resolve();assert candidate.exists()
    manifest=json.loads(candidate.with_suffix('.manifest.json').read_text())
    assert sha(candidate)==manifest['candidate_sha256']
    assert sha(ROOT/'kaggriculture_engine/engine.py')==manifest['engine_sha256']
    assert sha(ROOT/'kaggriculture_engine/native_core.py')==manifest['simulator_sha256']
    if not (HERE/'baseline_4eeac9c3.py').exists():
        with (HERE/'baseline_4eeac9c3.py').open('xb') as f:f.write((ROOT/'main.py').read_bytes())
    assert sha(HERE/'baseline_4eeac9c3.py')=='4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
    if args.phase=='confirm':
        pilot=json.loads((HERE/'pilot_receipt.json').read_text())
        assert pilot['candidate_sha256']==sha(candidate) and pilot['assessment']['passed']
        top=json.loads((HERE/'top20_receipt.json').read_text())
        assert top['candidate_sha256']==sha(candidate)
        assert top['assessment']['point_gain']>=0 and all(g['clean'] for g in top['assessment']['groups'].values())
        loader=json.loads((HERE/'loader_receipt.json').read_text())
        assert loader['candidate_sha256']==sha(candidate) and loader['passed']
    jobs=build_jobs(args.phase,candidate);freeze=HERE/f'{args.phase}_jobs.json'
    if freeze.exists():assert json.loads(freeze.read_text())==jobs
    else:write(freeze,jobs)
    source_hashes={str(path):sha(path) for path in (Path(__file__),ROOT/'kaggriculture_engine/engine.py',ROOT/'kaggriculture_engine/native_core.py',
                   ROOT/'diagnostics/physical_route_rollout_20260928/fast_reactive.py')}
    ledger=HERE/f'{args.phase}_results.jsonl';receipt_path=HERE/f'{args.phase}_receipt.json'
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        previous=[json.loads(s) for s in ledger.read_text().splitlines()] if ledger.exists() else []
        lookup={j['job_id']:j for j in jobs};done={r['job_id'] for r in previous};assert len(done)==len(previous)
        for row in previous:assert row['candidate_sha256']==lookup[row['job_id']]['candidate_sha256']
        if receipt_path.exists():assert json.loads(receipt_path.read_text())['source_hashes']==source_hashes
        if args.phase=='top100' and not ledger.exists() and (HERE/'top20_receipt.json').exists():
            subset=json.loads((HERE/'top20_receipt.json').read_text());assert subset['complete'] and subset['candidate_sha256']==sha(candidate)
            for line in (HERE/'top20_results.jsonl').read_text().splitlines():
                row=json.loads(line);assert row['candidate_sha256']==lookup[row['job_id']]['candidate_sha256']
                previous.append(row);done.add(row['job_id'])
            ledger.write_text(''.join(json.dumps(r)+'\n' for r in previous),encoding='utf-8')
        receipt=dict(complete=False,started_at_utc=now(),candidate_sha256=sha(candidate),jobs_sha256=sha(freeze),source_hashes=source_hashes,planned_games=len(jobs))
        write(receipt_path,receipt);rows=list(previous)
        with ledger.open('a',encoding='utf-8') as stream:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                pending={pool.submit(execute,j):j for j in jobs if j['job_id'] not in done}
                for future in as_completed(pending):
                    row=future.result();rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                    print(f'{len(rows)}/{len(jobs)} {row["job_id"]} {row.get("result",row.get("error_type"))} nodes={row.get("candidate_telemetry",{}).get("engine_nodes",0)} changes={row.get("candidate_telemetry",{}).get("engine_changed_turns",0)}',flush=True)
        receipt.update(complete=len(rows)==len(jobs),completed_at_utc=now(),results_sha256=sha(ledger),assessment=assess(rows))
        write(receipt_path,receipt);print(json.dumps(receipt['assessment'],indent=2),flush=True)

if __name__=='__main__':main()
