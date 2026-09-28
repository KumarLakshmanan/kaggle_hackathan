"""Prospective activation scans and paired reacting tests for complete routes."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import json
import random
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from paired_benchmark import _load_module, TimedAgent, make, engine_version
from diagnostics.opening_probe_v2_20260928.qualify import play,sha,errors,points
from diagnostics.local_target_20260928.run_lock import exclusive_run

REFS={
    '4ee':(ROOT/'main.py','4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'),
    'market':(ROOT/'public_market_smart_f6a756cf_20260927.py','f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2'),
}


def game_key(row):return row['version'],row['rival'],row['seed'],row['candidate_seat']
def prefix_key(row):return row['rival'],row['seed'],row['candidate_seat']


def prefix(job):
    assert sha(REFS['4ee'][0])==REFS['4ee'][1] and sha(job['opponent'])==job['opponent_sha256']
    candidate=_load_module(REFS['4ee'][0],'compatible_prefix_incumbent')
    opponent=None
    try:
        opponent=_load_module(Path(job['opponent']),'compatible_prefix_rival')
        captured={}
        def own_call(obs,cfg):
            visible=dict(cfg);visible['seed']=None
            if int(obs['step'])==144:captured['shops']=list(obs['town']['unlocked_shops'][:2])
            return candidate.agent(obs,visible)
        def rival_call(obs,cfg):
            visible=dict(cfg);visible['seed']=None
            return opponent.agent(obs,visible)
        own,other=TimedAgent(own_call),TimedAgent(rival_call)
        env=make('kaggriculture',configuration={'episodeSteps':720,'seed':job['seed']},debug=False)
        env.reset(2)
        runner=env._Environment__agent_runner([own,other] if job['candidate_seat']==0 else [other,own])
        for step in range(145):
            actions,logs=runner.act()
            if step<144:env.step(actions,logs)
        assert len(env.steps)==145 and all(s.status=='ACTIVE' for s in env.state)
        assert len(captured['shops'])==2
        own_errors,rival_errors=errors(candidate),errors(opponent)
        assert not own_errors and not rival_errors
        return dict(job,shops=captured['shops'],candidate_errors=own_errors,opponent_errors=rival_errors,
                    observed_step=144,frames=145,episode_steps=720,configuration_seed_visible=None)
    finally:
        sys.modules.pop(candidate.__name__,None)
        if opponent is not None:sys.modules.pop(opponent.__name__,None)
        gc.collect()


def context(phase):
    assert engine_version=='1.32.7'
    selection=json.loads((HERE/'selection.json').read_text(encoding='utf-8'))
    full=json.loads((HERE/'full_panel.json').read_text(encoding='utf-8'))
    plan_sha=sha(HERE/'NATIVE_PLAN.md')
    assert selection['passed'] and full['complete'] and full['passed']
    assert full['candidate_sha256']==selection['candidate_sha256']==sha(selection['candidate'])
    assert full['plan_sha256']==plan_sha
    assert all(sha(path)==digest for path,digest in REFS.values())
    if phase=='confirmation':
        pilot=json.loads((HERE/'native_pilot.json').read_text(encoding='utf-8'))
        assert pilot['complete'] and pilot['passed'] and pilot['candidate_sha256']==selection['candidate_sha256']
        assert pilot['plan_sha256']==plan_sha
    return selection,plan_sha


def scan(phase,workers):
    selection,plan_sha=context(phase)
    selected_pairs=set(selection['selected_replacements'])
    target_count=4 if phase=='pilot' else 8
    seed_range=list(range(2909000,2909256) if phase=='pilot' else range(2910000,2910512))
    checkpoint=HERE/(phase+'_prefixes.jsonl')
    rows=[json.loads(s) for s in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    keyed={prefix_key(r):r for r in rows};assert len(keyed)==len(rows)
    for row in rows:
        assert row['plan_sha256']==plan_sha and row['seed'] in seed_range
        assert row['opponent_sha256']==REFS[row['rival']][1]
        assert row['incumbent_sha256']==REFS['4ee'][1]
    def eligible(ref):
        return [seed for seed in seed_range if all((ref,seed,seat) in keyed
            and '|'.join(keyed[(ref,seed,seat)]['shops']) in selected_pairs for seat in (0,1))]
    def job(ref,seed,seat):
        path,digest=REFS[ref]
        return dict(rival=ref,seed=seed,candidate_seat=seat,opponent=str(path),opponent_sha256=digest,
                    incumbent_sha256=REFS['4ee'][1],plan_sha256=plan_sha)
    def execute(jobs,output):
        pending=[j for j in jobs if prefix_key(j) not in keyed]
        if not pending:return
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for future in as_completed([executor.submit(prefix,j) for j in pending]):
                row=future.result();assert prefix_key(row) not in keyed
                keyed[prefix_key(row)]=row;rows.append(row)
                output.write(json.dumps(row)+'\n');output.flush()
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(seed_range),8):
            needed=[ref for ref in REFS if len(eligible(ref))<target_count]
            if not needed:break
            block=seed_range[start:start+8]
            execute([job(ref,seed,0) for seed in block for ref in needed],output)
            execute([job(ref,seed,1) for seed in block for ref in needed
                     if '|'.join(keyed[(ref,seed,0)]['shops']) in selected_pairs],output)
            print(f'{phase} prefixes through {block[-1]}: '+json.dumps({r:len(eligible(r)) for r in REFS}),flush=True)
    selected={ref:eligible(ref)[:target_count] for ref in REFS}
    passed=all(len(v)==target_count for v in selected.values())
    coverage={ref:dict(seat0_scanned=sum(r['rival']==ref and r['candidate_seat']==0 for r in rows),
                       both_seat_eligible=len(eligible(ref))) for ref in REFS}
    result=dict(complete=True,passed=passed,phase=phase,selection_rule='First activated seeds in ascending bounded range; no final outcomes viewed.',
                candidate_sha256=selection['candidate_sha256'],plan_sha256=plan_sha,selected_seeds=selected,
                selected_pairs=sorted(selected_pairs),coverage=coverage,prefix_game_count=len(rows),
                seed_range=[seed_range[0],seed_range[-1]],completed_at_utc=datetime.now(timezone.utc).isoformat())
    (HERE/(phase+'_eligibility.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


def strength(phase,workers):
    selection,plan_sha=context(phase)
    eligibility=json.loads((HERE/(phase+'_eligibility.json')).read_text())
    assert eligibility['complete'] and eligibility['passed']
    assert eligibility['candidate_sha256']==selection['candidate_sha256'] and eligibility['plan_sha256']==plan_sha
    versions={'old':REFS['4ee'],'new':(Path(selection['candidate']),selection['candidate_sha256'])}
    jobs=[dict(version=v,rival=ref,seed=seed,candidate_seat=seat,path=str(path),candidate_sha256=digest,
               opponent=str(REFS[ref][0]),opponent_sha256=REFS[ref][1],plan_sha256=plan_sha)
          for ref,seeds in eligibility['selected_seeds'].items() for seed in seeds
          for v,(path,digest) in versions.items() for seat in (0,1)]
    expected={game_key(j):j for j in jobs};assert len(expected)==len(jobs)
    checkpoint=HERE/('native_'+phase+'.jsonl')
    rows=[json.loads(s) for s in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    for row in rows:assert all(row[k]==v for k,v in expected[game_key(row)].items())
    done={game_key(r) for r in rows};assert len(done)==len(rows)
    pending=[j for j in jobs if game_key(j) not in done]
    irreversible=[]
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(pending),16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(play,j) for j in pending[start:start+16]]):
                    row=future.result();assert game_key(row) not in done
                    done.add(game_key(row));rows.append(row)
                    output.write(json.dumps(row)+'\n');output.flush()
                    if len(rows)%4==0:print(f'{phase} {len(rows)}/{len(jobs)} {row["version"]} vs {row["rival"]} {row["result"]} {row["margin"]:+.0f}',flush=True)
            for ref,seeds in eligibility['selected_seeds'].items():
                new=[r for r in rows if r['rival']==ref and r['version']=='new']
                old=[r for r in rows if r['rival']==ref and r['version']=='old']
                ceiling=sum(points(r) for r in new)+2*len(seeds)-len(new)
                if ceiling<sum(points(r) for r in old):irreversible.append(dict(reference=ref,candidate_max_final=ceiling,baseline_already=sum(points(r) for r in old)))
            if irreversible:break
    complete=len(rows)==len(jobs)
    all_done=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' for r in rows)
    no_errors=all(not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    active=all(r['candidate_telemetry'].get('compatible_pool_turns',0)>0 for r in rows if r['version']=='new')
    scores={ref:{v:sum(points(r) for r in rows if r['rival']==ref and r['version']==v) for v in versions} for ref in REFS}
    nonregression=all(s['new']>=s['old'] for s in scores.values())
    seeds=sorted({r['seed'] for r in rows})
    blocks=[dict(seed=seed,delta=sum(points(r)*(1 if r['version']=='new' else -1) for r in rows if r['seed']==seed),
                 games=sum(r['seed']==seed and r['version']=='new' for r in rows)) for seed in seeds]
    passed=complete and all_done and no_errors and active and nonregression and sum(b['delta'] for b in blocks)>0
    result=dict(complete=complete,passed=bool(passed),phase=phase,candidate_sha256=selection['candidate_sha256'],plan_sha256=plan_sha,
                intended_games=len(jobs),game_count=len(rows),scores=scores,all_done=all_done,no_errors=no_errors,
                every_candidate_game_active=active,reference_nonregression=nonregression,seed_blocks=blocks,
                irreversible_failures=irreversible,completed_at_utc=datetime.now(timezone.utc).isoformat(),games=sorted(rows,key=game_key))
    if phase=='confirmation' and complete:
        rng=random.Random(2910599);bootstrap=[]
        for _ in range(10000):
            sampled=rng.choices(blocks,k=len(blocks))
            bootstrap.append(sum(b['delta'] for b in sampled)/sum(b['games'] for b in sampled))
        bootstrap.sort();interval=[bootstrap[250],bootstrap[9749]]
        result['paired_seed_bootstrap_95']=interval
        result['passed']=bool(passed and interval[0]>0)
    (HERE/('native_'+phase+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('pilot-scan','pilot','confirmation-scan','confirmation'))
    parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
    with exclusive_run(HERE/'native.lock'):
        scan(args.phase.replace('-scan',''),args.workers) if args.phase.endswith('-scan') else strength(args.phase,args.workers)
