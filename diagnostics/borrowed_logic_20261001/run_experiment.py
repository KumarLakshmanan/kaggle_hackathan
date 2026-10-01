"""Source-bound comparison with paired baseline rows and predeclared futility."""
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from diagnostics.executable_engine_20260930.run_experiment import execute
from diagnostics.local_target_20260928.run_lock import exclusive_run

MODES=('belief','feed','accounting','dynamic','endgame','combined')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2),encoding='utf-8')
def point(r):return {'win':1.,'draw':.5,'loss':0.}.get(r.get('result'),0.)
def clean(r):return not r.get('error') and not r.get('candidate_errors') and not r.get('opponent_errors') and r.get('frames')==720 and r.get('candidate_status')==r.get('opponent_status')=='DONE'
def pairkey(r):return (r.get('seed',r.get('fixture_id')),r['rival'],r['candidate_seat'])


def audit_execute(job):
    if job['kind']!='reactive':return execute(job)
    from diagnostics.physical_route_rollout_20260928 import native_core as core
    original_interpreter=core.interpreter;original_apply=core._apply_unit_action
    context={};counts={0:[0,0],1:[0,0]}
    def fingerprint(farm,private,index):
        pos=core._farmer_position(farm,index)
        tile=None if pos is None else farm['tiles'][pos[1]][pos[0]]
        inv=private['inventories'][index] if index<len(private['inventories']) else None
        return (None if pos is None else tuple(pos),copy.deepcopy(tile),copy.deepcopy(inv),
                dict(private['shed']),dict(private['seeds']),farm['money'])
    def apply(farm,private,index,command,*args):
        seat=context.get(id(farm))
        measure=seat is not None and isinstance(command,list) and command and command[0]!='PASS'
        before=fingerprint(farm,private,index) if measure else None
        result=original_apply(farm,private,index,command,*args)
        if measure:
            counts[seat][0]+=1;counts[seat][1]+=int(before==fingerprint(farm,private,index))
        return result
    def interpret(state,env):
        context.clear();context.update({id(f):p for p,f in enumerate(state[0].observation.farms)})
        return original_interpreter(state,env)
    core._apply_unit_action=apply;core.interpreter=interpret
    try:
        row=execute(job);seat=job['candidate_seat']
        row.update(candidate_nonpass_worker_calls=counts[seat][0],candidate_no_effect_worker_calls=counts[seat][1],
            opponent_nonpass_worker_calls=counts[1-seat][0],opponent_no_effect_worker_calls=counts[1-seat][1])
        return row
    finally:core.interpreter=original_interpreter;core._apply_unit_action=original_apply


def assess(rows,planned=None):
    base={pairkey(r):r for r in rows if r['version']=='baseline'};groups={};decisions={}
    for version in sorted({r['version'] for r in rows}):
        own=[r for r in rows if r['version']==version]
        g={'games':len(own),'wins':sum(r.get('result')=='win' for r in own),'draws':sum(r.get('result')=='draw' for r in own),
            'losses':sum(r.get('result')=='loss' for r in own),'points':sum(point(r) for r in own),'clean':all(clean(r) for r in own),
            'mean_margin':sum(r.get('margin',0) for r in own)/len(own),
            'max_call_seconds':max(r.get('max_candidate_call_seconds',r.get('candidate_timing',{}).get('max_ms',0)/1000) for r in own),
            'no_effect_worker_calls':sum(r.get('candidate_no_effect_worker_calls',0) for r in own)}
        groups[version]=g
        if version=='baseline':continue
        matched=[base[pairkey(r)] for r in own];gain=sum(point(r)-point(base[pairkey(r)]) for r in own)
        per={ref:sum(point(r)-point(base[pairkey(r)]) for r in own if r['rival']==ref) for ref in sorted({r['rival'] for r in own})}
        active={r.get('seed',r.get('fixture_id')) for r in own if r.get('margin')!=base[pairkey(r)].get('margin') or r.get('candidate_telemetry',{}).get('borrow_changed_turns',0)>0}
        expected=sum(j['version']==version for j in planned) if planned else len(own)
        decisions[version]={'point_gain':gain,'per_reference_gain':per,'complete':len(own)==expected,
            'matched_baseline':{'games':len(matched),'wins':sum(r.get('result')=='win' for r in matched),'draws':sum(r.get('result')=='draw' for r in matched),'losses':sum(r.get('result')=='loss' for r in matched),'points':sum(point(r) for r in matched)},
            'lost_prior_wins':sum(base[pairkey(r)].get('result')=='win' and r.get('result')!='win' for r in own),
            'activated_seeds':len(active),
            'screen_passed':len(own)==expected and g['clean'] and all(clean(r) for r in matched) and gain>0 and all(v>=0 for v in per.values()) and len(active)>=2,
            'replay_passed':len(own)==expected and g['clean'] and all(clean(r) for r in matched) and gain>=0}
    passing=[v for v,d in decisions.items() if d['screen_passed']]
    best=max(passing,key=lambda v:(groups[v]['points'],groups[v]['mean_margin'],-groups[v]['max_call_seconds'])) if passing else None
    return {'groups':groups,'decisions':decisions,'screen_survivor':best}


def jobs_for(phase,candidate=None,solo=None,bbff_extra=False):
    refs={'4ea':HERE/'baseline_4ea1d89a.py','bbff':HERE/'baseline_bbffbe65.py','v35':ROOT/'diagnostics/public_ahmed_v35_20260927/public_v35_main.py'}
    versions={'baseline':HERE/'baseline_4ea1d89a.py'}
    if phase=='screen':versions.update({m:HERE/f'candidate_{m}.py' for m in MODES})
    elif phase=='joint':versions.update(candidate=Path(candidate),solo=Path(solo))
    else:versions['candidate']=Path(candidate)
    if bbff_extra:versions['incumbent']=HERE/'baseline_bbffbe65.py'
    if phase=='confirm':refs['c95']=ROOT/'diagnostics/public_rayk_top_meta/public_c95_main.py'
    jobs=[]
    if phase in ('top20','top100'):
        source=json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
        for fixture in source:
            if fixture['rank']>(20 if phase=='top20' else 100):continue
            for v,p in versions.items():jobs.append(dict(fixture,kind='replay',version=v,rival=fixture['team'],path=str(p),candidate_sha256=sha(p),job_id=f'{v}:{fixture["fixture_id"]}:{fixture["candidate_seat"]}'))
    else:
        seeds=range(36000001,36000005) if phase=='screen' else range(36000011,36000015) if phase=='joint' else range(36000101,36000117)
        for v,p in versions.items():
            for seed in seeds:
                for ref,opponent in refs.items():
                    for seat in (0,1):jobs.append({'job_id':f'{v}:{seed}:{ref}:{seat}','kind':'native' if phase=='confirm' else 'reactive','version':v,'rival':ref,'seed':seed,'candidate_seat':seat,'path':str(p),'candidate_sha256':sha(p),'opponent':str(opponent),'opponent_sha256':sha(opponent)})
    return jobs


def futility(version,rows,jobs):
    own=[r for r in rows if r['version']==version];base=[r for r in rows if r['version']=='baseline']
    if not all(clean(r) for r in own):return {'reason':'Operational gate irreversibly failed'}
    refs={r['rival'] for r in base};upper={}
    for ref in refs:
        n=sum(j['version']==version and j['rival']==ref for j in jobs)
        tested=[r for r in own if r['rival']==ref];target=sum(point(r) for r in base if r['rival']==ref)
        maximum=sum(point(r) for r in tested)+n-len(tested);upper[ref]={'maximum_points':maximum,'baseline_points':target}
    if any(v['maximum_points']<v['baseline_points'] for v in upper.values()):return {'reason':'Even all remaining wins cannot avoid reference-level regression','bounds':upper}
    if sum(v['maximum_points'] for v in upper.values())<=sum(point(r) for r in base):return {'reason':'Even all remaining wins cannot produce positive pooled gain','bounds':upper}
    return None


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('screen','joint','top20','top100','confirm'))
    parser.add_argument('--candidate',type=Path);parser.add_argument('--solo',type=Path);parser.add_argument('--bbff-extra',action='store_true');parser.add_argument('--workers',type=int,default=6);args=parser.parse_args()
    assert 1<=args.workers<=6
    assert json.loads((HERE/'engineering_receipt.json').read_text())['passed']
    paths=[HERE/f'candidate_{m}.py' for m in MODES] if args.phase=='screen' else [args.candidate]
    for p in paths:
        manifest=json.loads(Path(p).with_suffix('.manifest.json').read_text());assert manifest['candidate_sha256']==sha(p)
        for source,digest in manifest['source_hashes'].items():assert sha(source)==digest
    jobs=jobs_for(args.phase,args.candidate,args.solo,args.bbff_extra);freeze=HERE/f'{args.phase}_jobs.json'
    if freeze.exists():assert json.loads(freeze.read_text())==jobs
    else:write(freeze,jobs)
    ledger=HERE/f'{args.phase}_results.jsonl';receipt_path=HERE/f'{args.phase}_receipt.json'
    source_hashes={str(p):sha(p) for p in (Path(__file__),ROOT/'diagnostics/executable_engine_20260930/run_experiment.py',ROOT/'diagnostics/physical_route_rollout_20260928/fast_reactive.py',ROOT/'diagnostics/opening_probe_v2_20260928/qualify.py')}
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        rows=[json.loads(s) for s in ledger.read_text().splitlines()] if ledger.exists() else []
        lookup={j['job_id']:j for j in jobs};done={r['job_id'] for r in rows};assert len(rows)==len(done)
        for r in rows:assert r['candidate_sha256']==lookup[r['job_id']]['candidate_sha256']
        if receipt_path.exists():assert json.loads(receipt_path.read_text())['source_hashes']==source_hashes
        if args.phase in ('top20','top100'):
            prior=ROOT/f'diagnostics/professional_engine_20261001/{args.phase}_results.jsonl'
            for line in prior.read_text().splitlines():
                r=json.loads(line)
                if r['version']!='candidate':continue
                key=f'baseline:{r["fixture_id"]}:{r["candidate_seat"]}'
                if key in done:continue
                assert r['candidate_sha256']==lookup[key]['candidate_sha256']
                rows.append(dict(r,version='baseline',job_id=key,reused_control=True));done.add(key)
            if args.phase=='top100':
                for line in (HERE/'top20_results.jsonl').read_text().splitlines():
                    r=json.loads(line)
                    if r['job_id'] in done:continue
                    assert r['candidate_sha256']==lookup[r['job_id']]['candidate_sha256'];rows.append(r);done.add(r['job_id'])
            ledger.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
        receipt={'complete':False,'started_at_utc':datetime.now(timezone.utc).isoformat(),'planned_games':len(jobs),'source_hashes':source_hashes,
            'candidate_hashes':{v:sha(next(j['path'] for j in jobs if j['version']==v)) for v in {j['version'] for j in jobs}},'jobs_sha256':sha(freeze),'futility_stops':{}}
        write(receipt_path,receipt)
        with ledger.open('a',encoding='utf-8') as out:
            def run_batch(selected):
                pending_jobs=[j for j in selected if j['job_id'] not in done]
                with ProcessPoolExecutor(max_workers=args.workers) as pool:
                    pending={pool.submit(audit_execute,j):j for j in pending_jobs}
                    for future in as_completed(pending):
                        r=future.result();rows.append(r);done.add(r['job_id']);out.write(json.dumps(r)+'\n');out.flush()
                        print(f'{len(rows)}/{len(jobs)} {r["job_id"]} {r.get("result",r.get("error_type"))}',flush=True)
            if args.phase=='screen':
                run_batch([j for j in jobs if j['version']=='baseline'])
                run_batch([j for j in jobs if j['version']!='baseline' and j['seed']<36000003])
                eligible=[]
                for mode in MODES:
                    stop=futility(mode,rows,jobs)
                    if stop:receipt['futility_stops'][mode]=stop;print(json.dumps({'rejected':mode,**stop}),flush=True)
                    else:eligible.append(mode)
                run_batch([j for j in jobs if j['version'] in eligible and j['seed']>=36000003])
            else:run_batch(jobs)
        stopped=set(receipt['futility_stops']);skipped=[j['job_id'] for j in jobs if j['job_id'] not in done]
        assert all(lookup[key]['version'] in stopped for key in skipped)
        receipt.update(complete=True,all_planned_games_executed=not skipped,executed_games=len(rows),skipped_jobs=skipped,
            completed_at_utc=datetime.now(timezone.utc).isoformat(),results_sha256=sha(ledger),assessment=assess(rows,jobs));write(receipt_path,receipt)
        print(json.dumps(receipt['assessment'],indent=2),flush=True)


if __name__=='__main__':main()
