"""Prospective stratified prefix selection and original-framework strength."""
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
import argparse
import importlib.metadata
import json
import random
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_reactive import play as fast_play,errors,load_policy
from diagnostics.physical_route_rollout_20260928.check import sha
from diagnostics.local_target_20260928.run_lock import exclusive_run

VERSIONS={
    'main':(ROOT/'main.py','4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'),
    'route':(ROOT/'diagnostics/compatible_route_pool_20260928/candidates/B_113349962.py',
             'd271754e609f1f089ea80d60186c24b4d14e357720ace34a47aa584c081504ed'),
    'new':(HERE/'candidate_route.py','068030868689db5eb1e9a4a4427bededa8fbc13cae14e1003eb6be5440a6da42'),
}
REFS={
    '4ee':VERSIONS['main'],
    'market':(ROOT/'public_market_smart_f6a756cf_20260927.py',
              'f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2'),
}


def pkey(row):return row['rival'],row['seed'],row['candidate_seat']
def gkey(row):return row['version'],row['rival'],row['seed'],row['candidate_seat']
def points(row):return 1 if row['result']=='win' else .5 if row['result']=='draw' else 0


def context(phase):
    assert importlib.metadata.version('kaggle-environments')=='1.32.7'
    full=json.loads((HERE/'native_full.json').read_text(encoding='utf-8'))
    assert full['complete'] and full['passed'] and full['candidate_sha256']==VERSIONS['new'][1]
    for path,digest in list(VERSIONS.values())+list(REFS.values()):assert sha(path)==digest,(path,sha(path),digest)
    p=ROOT/'diagnostics/physical_route_rollout_20260928'
    engineering=json.loads((p/'reactive_parity.json').read_text(encoding='utf-8'))
    assert engineering['complete'] and engineering['passed']
    for name,field,digest in (
        ('fast_reactive.py','helper_sha256','4f6061926f07402c87112e44d8ee28551dc62773b8141a89cba1c5744a6ecba9'),
        ('native_core.py','core_sha256','5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795'),
        ('initial_template.json','template_sha256','7d300be7e59ecd210eb8df5ad503c3971f6d869dee593daeffec1b3224cee7e1')):
        assert engineering[field]==sha(p/name)==digest
    plan_sha=sha(HERE/'NATIVE_PLAN.md')
    if phase=='confirmation':
        pilot=json.loads((HERE/'native_pilot.json').read_text(encoding='utf-8'))
        assert pilot['complete'] and pilot['passed'] and pilot['candidate_sha256']==VERSIONS['new'][1]
        assert pilot['plan_sha256']==plan_sha
    return plan_sha


def classify(row):
    if row['shops144']==['YARN_STORE','FARMERS_MARKET']:return 'route'
    if row['candidate_telemetry'].get('partial_plant_turns',0)>0:return 'guard'
    return None


def prefix_fast(job):
    row=fast_play(job,336)
    assert row['frames']==337 and row['candidate_status']==row['opponent_status']=='ACTIVE'
    assert not row['candidate_errors'] and not row['opponent_errors']
    assert 'candidate_reward' not in row and 'opponent_reward' not in row
    return row


def prefix_native(job):
    from paired_benchmark import make,TimedAgent
    assert sha(job['path'])==job['candidate_sha256'] and sha(job['opponent'])==job['opponent_sha256']
    candidate=load_policy(job['path'],'partial_native_prefix_own')
    rival=load_policy(job['opponent'],'partial_native_prefix_other')
    capture={}
    def own(obs,cfg):
        if int(obs['step'])==144:capture['shops144']=list(obs['town']['unlocked_shops'][:2])
        return candidate.agent(obs,dict(cfg,seed=None))
    def other(obs,cfg):return rival.agent(obs,dict(cfg,seed=None))
    players=[TimedAgent(own),TimedAgent(other)]
    if job['candidate_seat']==1:players.reverse()
    env=make('kaggriculture',configuration={'episodeSteps':720,'seed':job['seed']},debug=False);env.reset(2)
    runner=env._Environment__agent_runner(players)
    for _ in range(336):
        actions,logs=runner.act();env.step(actions,logs)
    seat=job['candidate_seat']
    return dict(job,frames=len(env.steps),observed_step=int(env.state[0].observation.step),
        candidate_status=env.state[seat].status,opponent_status=env.state[1-seat].status,
        candidate_telemetry=dict(getattr(candidate.agent,'telemetry',{}) or {}),
        opponent_telemetry=dict(getattr(rival.agent,'telemetry',{}) or {}),
        candidate_errors=errors(candidate),opponent_errors=errors(rival),shops144=capture['shops144'],configuration_seed_visible=None)


def scan(phase,workers):
    plan_sha=context(phase)
    count=2 if phase=='pilot' else 4
    seeds=list(range(2920000,2922048) if phase=='pilot' else range(2923000,2927096))
    checkpoint=HERE/(phase+'_prefixes.jsonl')
    rows=[json.loads(l) for l in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    keyed={pkey(r):r for r in rows};assert len(keyed)==len(rows)
    for row in rows:
        assert row['plan_sha256']==plan_sha and row['seed'] in seeds
        assert row['candidate_sha256']==VERSIONS['new'][1] and row['opponent_sha256']==REFS[row['rival']][1]
    def eligible(ref,kind):
        return [seed for seed in seeds if all((ref,seed,seat) in keyed and classify(keyed[(ref,seed,seat)])==kind for seat in (0,1))]
    def job(ref,seed,seat):
        return dict(rival=ref,seed=seed,candidate_seat=seat,path=str(VERSIONS['new'][0]),candidate_sha256=VERSIONS['new'][1],
                    opponent=str(REFS[ref][0]),opponent_sha256=REFS[ref][1],plan_sha256=plan_sha)
    def execute(jobs,output):
        pending=[j for j in jobs if pkey(j) not in keyed]
        if not pending:return
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for future in as_completed([executor.submit(prefix_fast,j) for j in pending]):
                row=future.result();assert pkey(row) not in keyed
                keyed[pkey(row)]=row;rows.append(row)
                output.write(json.dumps(row)+'\n');output.flush()
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(seeds),8):
            needed={ref:{kind for kind in ('route','guard') if len(eligible(ref,kind))<count} for ref in REFS}
            needed={ref:kinds for ref,kinds in needed.items() if kinds}
            if not needed:break
            block=seeds[start:start+8]
            execute([job(ref,seed,0) for seed in block for ref in needed],output)
            execute([job(ref,seed,1) for seed in block for ref,kinds in needed.items()
                     if classify(keyed[(ref,seed,0)]) in kinds],output)
            print(phase,block[-1],{ref:{kind:len(eligible(ref,kind)) for kind in ('route','guard')} for ref in REFS},flush=True)
    selected={ref:{kind:eligible(ref,kind)[:count] for kind in ('route','guard')} for ref in REFS}
    passed=all(len(v)==count for groups in selected.values() for v in groups.values())
    result=dict(complete=True,passed=passed,phase=phase,candidate_sha256=VERSIONS['new'][1],plan_sha256=plan_sha,
                selected=selected,prefix_game_count=len(rows),seed_range=[seeds[0],seeds[-1]],
                completed_at_utc=datetime.now(timezone.utc).isoformat())
    (HERE/(phase+'_eligibility.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


def verify(phase,workers):
    plan_sha=context(phase)
    selection=json.loads((HERE/(phase+'_eligibility.json')).read_text(encoding='utf-8'))
    assert selection['complete'] and selection['passed'] and selection['plan_sha256']==plan_sha
    prefixes=[json.loads(l) for l in (HERE/(phase+'_prefixes.jsonl')).read_text(encoding='utf-8').splitlines()]
    keyed={pkey(r):r for r in prefixes}
    keys=[(ref,seed,seat) for ref,groups in selection['selected'].items() for seeds in groups.values() for seed in seeds for seat in (0,1)]
    jobs=[{k:keyed[key][k] for k in ('rival','seed','candidate_seat','path','candidate_sha256','opponent','opponent_sha256','plan_sha256')} for key in keys]
    checkpoint=HERE/(phase+'_verified_prefixes.jsonl')
    rows=[json.loads(l) for l in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    for row in rows:assert pkey(row) in keys and row['plan_sha256']==plan_sha
    done={pkey(r) for r in rows};assert len(done)==len(rows)
    pending=[j for j in jobs if pkey(j) not in done]
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(pending),16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(prefix_native,j) for j in pending[start:start+16]]):
                    row=future.result();control=keyed[pkey(row)]
                    fields=('frames','observed_step','candidate_status','opponent_status','candidate_telemetry','opponent_telemetry','shops144')
                    row['mismatches']=[k for k in fields if row[k]!=control[k]]
                    row['passed']=not row['mismatches'] and not row['candidate_errors'] and not row['opponent_errors']
                    rows.append(row);output.write(json.dumps(row)+'\n');output.flush()
                    print('verify',len(rows),'/',len(jobs),row['passed'],row['mismatches'],flush=True)
    result=dict(complete=len(rows)==len(jobs),passed=all(r['passed'] for r in rows),plan_sha256=plan_sha,
                candidate_sha256=VERSIONS['new'][1],games=rows)
    (HERE/(phase+'_prefix_verification.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')


def full_game(job):
    from diagnostics.opening_probe_v2_20260928.qualify import play
    return play(job)


def strength(phase,workers):
    plan_sha=context(phase)
    selection=json.loads((HERE/(phase+'_eligibility.json')).read_text(encoding='utf-8'))
    verification=json.loads((HERE/(phase+'_prefix_verification.json')).read_text(encoding='utf-8'))
    assert selection['complete'] and selection['passed'] and verification['complete'] and verification['passed']
    assert selection['plan_sha256']==verification['plan_sha256']==plan_sha
    jobs=[dict(version=v,rival=ref,stratum=kind,seed=seed,candidate_seat=seat,path=str(path),candidate_sha256=digest,
               opponent=str(REFS[ref][0]),opponent_sha256=REFS[ref][1],plan_sha256=plan_sha)
          for ref,groups in selection['selected'].items() for kind,seeds in groups.items() for seed in seeds
          for v,(path,digest) in VERSIONS.items() for seat in (0,1)]
    expected={gkey(j):j for j in jobs};assert len(expected)==len(jobs)
    checkpoint=HERE/('native_'+phase+'.jsonl')
    rows=[json.loads(l) for l in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    for row in rows:assert all(row[k]==v for k,v in expected[gkey(row)].items())
    done={gkey(r) for r in rows};assert len(done)==len(rows)
    pending=[j for j in jobs if gkey(j) not in done];irreversible=[]
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(pending),16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(full_game,j) for j in pending[start:start+16]]):
                    row=future.result();assert gkey(row) not in done
                    done.add(gkey(row));rows.append(row)
                    output.write(json.dumps(row)+'\n');output.flush()
                    if len(rows)%4==0:print(phase,len(rows),'/',len(jobs),row['version'],row['rival'],row['result'],row['margin'],flush=True)
            for ref in REFS:
                new=[r for r in rows if r['rival']==ref and r['version']=='new']
                target=sum(j['rival']==ref and j['version']=='new' for j in jobs)
                ceiling=sum(points(r) for r in new)+target-len(new)
                for control in ('main','route'):
                    earned=sum(points(r) for r in rows if r['rival']==ref and r['version']==control)
                    if ceiling<earned:irreversible.append(dict(reference=ref,control=control,candidate_max=ceiling,control_already=earned))
            if irreversible:break
    complete=len(rows)==len(jobs)
    clean=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' and not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    active=all(r['candidate_telemetry'].get('partial_plant_turns' if r['stratum']=='guard' else 'compatible_pool_turns',0)>0 for r in rows if r['version']=='new')
    scores={ref:{v:sum(points(r) for r in rows if r['rival']==ref and r['version']==v) for v in VERSIONS} for ref in REFS}
    nonreg=all(s['new']>=s[v] for s in scores.values() for v in ('main','route'))
    gains={v:sum(s['new']-s[v] for s in scores.values()) for v in ('main','route')}
    passed=complete and clean and active and nonreg and all(g>0 for g in gains.values())
    summaries=[]
    for ref in REFS:
        for kind in ('route','guard'):
            summaries.append(dict(reference=ref,stratum=kind,WDL={v:[sum(r['rival']==ref and r['stratum']==kind and r['version']==v and r['result']==outcome for r in rows) for outcome in ('win','draw','loss')] for v in VERSIONS}))
    result=dict(complete=complete,passed=bool(passed),phase=phase,candidate_sha256=VERSIONS['new'][1],plan_sha256=plan_sha,
                intended_games=len(jobs),game_count=len(rows),clean=clean,activation_verified=active,scores=scores,
                reference_nonregression=nonreg,pooled_gains=gains,irreversible_failures=irreversible,strata=summaries,
                completed_at_utc=datetime.now(timezone.utc).isoformat(),games=sorted(rows,key=gkey))
    if phase=='confirmation' and complete:
        rng=random.Random(2927099);seeds=sorted({r['seed'] for r in rows})
        blocks=[dict(seed=seed,games=sum(r['seed']==seed and r['version']=='new' for r in rows),
                delta={v:sum(points(r)* (1 if r['version']=='new' else -1) for r in rows if r['seed']==seed and r['version'] in ('new',v)) for v in ('main','route')}) for seed in seeds]
        intervals={}
        for control in ('main','route'):
            values=[]
            for _ in range(10000):
                sampled=rng.choices(blocks,k=len(blocks));values.append(sum(b['delta'][control] for b in sampled)/sum(b['games'] for b in sampled))
            values.sort();intervals[control]=[values[250],values[9749]]
        result.update(seed_blocks=blocks,paired_seed_bootstrap_95=intervals)
        result['passed']=bool(passed and all(interval[0]>0 for interval in intervals.values()))
    (HERE/('native_'+phase+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('pilot-scan','pilot-verify','pilot','confirmation-scan','confirmation-verify','confirmation'))
    parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
    phase=args.phase.split('-')[0]
    with exclusive_run(HERE/'native.lock'):
        if args.phase.endswith('-scan'):scan(phase,args.workers)
        elif args.phase.endswith('-verify'):verify(phase,args.workers)
        else:strength(phase,args.workers)
