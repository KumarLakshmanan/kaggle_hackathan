"""One observed donor151 pair, all affected saved50/public54 contexts."""
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import argparse
import copy
import gc
import gzip
import json
import sys

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OLD=ROOT/'diagnostics/adaptive_donor_pair_repair_20260928'
SOURCE=ROOT/'main_candidate_adaptive_donor_pair_repair_20260928_a44c8c2c.py'
SOURCE_SHA='a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
FULL_SHA='ea74d2be3b852acf83885a35ce55296b391eff8b33b1bd5f556fa6242fa1d732'
WINS=ROOT/'diagnostics/partial_planting_20260928/public_win_manifest.json'
WINS_SHA='f1cd25bbe3e058fec3bea3bb0cc470cd135780d2bb098e701908daf4053555de'
PAIR='BRUNCH_SPOT|PIZZA_SHOP';THIRD='live-114274897'
sys.path.insert(0,str(ROOT))
from diagnostics.adaptive_opening_bridge_20260928.build import read,write,sha,module
from diagnostics.stream_replay_io_20260928.fast_game_cached import play
from diagnostics.stream_replay_io_20260928.cached_input import load_fixture
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import Box,state_from_frames
from diagnostics.local_target_20260928.run_lock import exclusive_run


def key(row):return row['fixture_id'],row['candidate_seat']
def errors(stats):return {k:v for k,v in stats.items() if v and ('error' in k or 'collision' in k or k in ('bridge_common_failed','bridge_source_guard_failed'))}


def build(route):
    path=HERE/('candidate_'+route+'.py')
    code=SOURCE.read_bytes()+('\n_THIRD_PAIR_REPAIR = '+repr({PAIR:route})+'\n'
        "_BRIDGE_DONORS['shared151']['_DONOR_MAP'].update(_THIRD_PAIR_REPAIR)\n\n"
        'def kaggle_third_pair_repair_entrypoint(observation, configuration=None):\n'
        '    return agent(observation, configuration)\n').encode()
    compile(code,str(path),'exec')
    with path.open('xb') as out:out.write(code)
    old=module(SOURCE,'third_original');new=module(path,'third_changed')
    ns=new._BRIDGE_DONORS['shared151'];prior=old._BRIDGE_DONORS['shared151']
    assert new._DATA==old._DATA and ns['_DONOR_ROUTES']==prior['_DONOR_ROUTES']
    assert all(r[:151]==ns['_DONOR_ROUTES']['route0'][:151] for r in ns['_DONOR_ROUTES'].values())
    assert ns['_QUEUE_PARENT'] is ns['_donor_action'] and ns['_ITERATED_QUEUE_RAW'] is ns['_donor_action']
    assert all(ns[n].__globals__ is ns for n in ('_donor_action','_donor_schedule','_hire_recovery_schedule'))
    obs={'step':144,'town':{'unlocked_shops':PAIR.split('|')}}
    assert ns['_hire_recovery_schedule'](obs) is ns['_DONOR_ROUTES'][route]
    assert ns['_ITERATED_QUEUE_RAW'](obs)==ns['_DONOR_ROUTES'][route][144]
    del old,new;gc.collect()
    return dict(candidate=str(path),candidate_sha256=sha(path))


def prepare():
    assert sha(SOURCE)==SOURCE_SHA and sha(OLD/'full_results.json')==FULL_SHA and sha(WINS)==WINS_SHA
    original=read(OLD/'full_pool.json');full=read(OLD/'full_results.json');wins=read(WINS)
    assert full['complete'] and full['passed'] and len(full['games'])==100 and len(wins['fixtures'])==54
    assert all(sha(p)==v for p,v in original['bindings'].items())
    affected={r['fixture_id'] for r in full['games'] if r['candidate_telemetry'].get('bridge_selected')=='shared151'
              and r['candidate_telemetry'].get('donor_pair144')==PAIR}
    assert THIRD in affected
    targets=[f for f in original['fixtures'] if f['fixture_id'] in affected]
    controls=[r for r in full['games'] if r['fixture_id'] in affected]
    assert all(r['candidate_telemetry'].get('donor_selected')=='route0' for r in controls)
    arms={'route0':dict(candidate=str(SOURCE),candidate_sha256=SOURCE_SHA)}
    arms.update({route:build(route) for route in ('route1','route2')})
    bindings=dict(original['bindings'])
    for path in (HERE/'PLAN.md',Path(__file__),OLD/'full_pool.json',OLD/'full_results.json',WINS,SOURCE):bindings[str(path)]=sha(path)
    for arm in arms.values():bindings[arm['candidate']]=arm['candidate_sha256']
    for f in wins['fixtures']:bindings[f['source_action_tape_path']]=sha(f['source_action_tape_path'])
    for row in controls:bindings[row['trace_path']]=row['trace_sha256'];assert sha(row['trace_path'])==row['trace_sha256']
    write(HERE/'pool.json',dict(arms=arms,target_fixtures=targets,target_controls=controls,public_fixtures=wins['fixtures'],
        bindings=bindings,source_full_sha256=FULL_SHA,preflight_passed=True,created_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Third prepared; affected targets',sorted(affected),'public discovery108prefixes; pool',sha(HERE/'pool.json'),flush=True)


def validate():
    p=read(HERE/'pool.json');assert all(sha(f)==v for f,v in p['bindings'].items());return p


def prefix_worker(job):
    fixture=job['fixture'];seat=job['candidate_seat'];cached=load_fixture(fixture)
    state=state_from_frames(cached['steps'][0]);cfg=dict(cached['configuration'],seed=None)
    env=Box(configuration=Box(**cfg),info={'seed':int(fixture['seed'])},done=False)
    candidate=module(job['candidate'],'third_prefix')
    tape=json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    comparison=gzip.open(job['control_trace'],'rt',encoding='utf-8') if job.get('control_trace') else None
    output=gzip.open(job['trace_path'],'wt',encoding='utf-8') if job.get('trace_path') else None
    try:
        for step in range(144):
            obs=copy.deepcopy(dict(state[seat].observation,remainingOverageTime=60.0));action=candidate.agent(obs,cfg)
            record=dict(step=step,observation=obs,action=action)
            if comparison:assert json.loads(next(comparison))==record,(fixture['fixture_id'],seat,step)
            if output:output.write(json.dumps(record,separators=(',',':'))+'\n')
            state[seat].action=action;state[1-seat].action=copy.deepcopy(tape[step]);core.interpreter(state,env)
            for item in state:item.observation.step=step+1
        obs=copy.deepcopy(dict(state[seat].observation,remainingOverageTime=60.0))
        if comparison:assert json.loads(next(comparison))['observation']==obs
        if output:output.write(json.dumps(dict(step=144,observation=obs),separators=(',',':'))+'\n')
        stats=dict(candidate.agent.telemetry);err=errors(stats)
        result=dict(fixture_id=fixture['fixture_id'],candidate_seat=seat,candidate_sha256=job['candidate_sha256'],
            branch=stats.get('bridge_selected'),pair='|'.join(obs['town']['unlocked_shops'][:2]),passed=not err,errors=err,
            exact_actions=144 if comparison else None,exact_observations=145 if comparison else None)
        assert not err,result
    finally:
        if comparison:comparison.close()
        if output:output.close()
    if job.get('trace_path'):result.update(trace_path=job['trace_path'],trace_sha256=sha(job['trace_path']))
    if job.get('route'):result['route']=job['route']
    del candidate,state,tape;gc.collect();return result


def discover():
    p=validate();assert not (HERE/'discovery.json').exists();checkpoint=HERE/'discovery.jsonl'
    rows=[json.loads(s) for s in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    done={key(r) for r in rows};assert len(done)==len(rows)
    for r in rows:assert r['candidate_sha256']==SOURCE_SHA and sha(r['trace_path'])==r['trace_sha256']
    jobs=[dict(candidate=str(SOURCE),candidate_sha256=SOURCE_SHA,fixture=f,candidate_seat=seat,
            trace_path=str(HERE/('prefix_'+str(f['episode_id'])+'_seat'+str(seat)+'.jsonl.gz')))
          for f in p['public_fixtures'] for seat in (0,1) if (f['fixture_id'],seat) not in done]
    with checkpoint.open('a',encoding='utf-8') as stream:
        for start in range(0,len(jobs),8):
            with ProcessPoolExecutor(max_workers=1) as ex:
                for row in ex.map(prefix_worker,jobs[start:start+8]):
                    rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                    if len(rows)%8==0 or row['branch']=='shared151' and row['pair']==PAIR:
                        print('Public54 prefixes',len(rows),'/108',row['fixture_id'],row['candidate_seat'],row['branch'],row['pair'],flush=True)
    affected={r['fixture_id'] for r in rows if r['branch']=='shared151' and r['pair']==PAIR}
    write(HERE/'discovery.json',dict(complete=len(rows)==108,passed=all(r['passed'] for r in rows),rows=rows,
        affected_public_fixture_ids=sorted(affected),pool_sha256=sha(HERE/'pool.json'),completed_at_utc=datetime.now(timezone.utc).isoformat()))
    fixtures=p['target_fixtures']+[f for f in p['public_fixtures'] if f['fixture_id'] in affected]
    proofs=[];controls={key(r):r for r in p['target_controls']};controls.update({key(r):r for r in rows})
    for f in fixtures:
        for seat in (0,1):
            control=controls[f['fixture_id'],seat]
            for route in ('route1','route2'):proofs.append(dict(**p['arms'][route],route=route,fixture=f,candidate_seat=seat,control_trace=control['trace_path']))
    with ProcessPoolExecutor(max_workers=1,max_tasks_per_child=8) as ex:checks=list(ex.map(prefix_worker,proofs))
    bindings={str(HERE/'pool.json'):sha(HERE/'pool.json'),str(HERE/'discovery.json'):sha(HERE/'discovery.json')}
    for f in fixtures:
        for seat in (0,1):
            c=controls[f['fixture_id'],seat];bindings[c['trace_path']]=c['trace_sha256']
    write(HERE/'scope.json',dict(fixtures=fixtures,affected_public_fixture_ids=sorted(affected),proofs=checks,
        passed=all(r['passed'] for r in checks),bindings=bindings,created_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Frozen affected scope',len(fixtures),'fixtures;',len(affected),'public54; new fullgames',len(fixtures)*4+len(affected)*2,
          'scope',sha(HERE/'scope.json'),flush=True)


def full_worker(job):
    row=play(job['fixture'],job['candidate'],job['candidate_sha256'],job['candidate_seat'],job['trace_path'])
    row.update(route=job['route'],panel='public54' if job['fixture']['fixture_id'].startswith('public-win-') else 'target50',
        trace_path=job['trace_path'],trace_sha256=sha(job['trace_path']),reused=False)
    row['clean']=row['frames']==720 and row['candidate_status']==row['opponent_status']=='DONE' and not errors(row['candidate_telemetry'])
    return row


def screen():
    p=validate();scope=read(HERE/'scope.json');assert scope['passed'] and all(sha(f)==v for f,v in scope['bindings'].items())
    assert not (HERE/'screen.json').exists();rows=[]
    for r in p['target_controls']:rows.append(dict(r,route='route0',panel='target50',reused=True,reused_receipt_sha256=FULL_SHA))
    checkpoint=HERE/'screen_new.jsonl';prior=[json.loads(s) for s in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    done={(r['route'],*key(r)) for r in rows+prior};assert len(done)==len(rows)+len(prior)
    for r in prior:assert sha(r['trace_path'])==r['trace_sha256'] and r['candidate_sha256']==p['arms'][r['route']]['candidate_sha256']
    rows+=prior;jobs=[]
    for route,arm in p['arms'].items():
        for fixture in scope['fixtures']:
            for seat in (0,1):
                if (route,fixture['fixture_id'],seat) in done:continue
                jobs.append(dict(**arm,route=route,fixture=fixture,candidate_seat=seat,
                    trace_path=str(HERE/(route+'_'+fixture['fixture_id']+'_seat'+str(seat)+'.jsonl.gz'))))
    with checkpoint.open('a',encoding='utf-8') as stream:
        for start in range(0,len(jobs),8):
            with ProcessPoolExecutor(max_workers=1) as ex:
                for row in ex.map(full_worker,jobs[start:start+8]):
                    rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                    print('Third members',row['route'],row['fixture_id'],row['candidate_seat'],row['result'],row['margin'],flush=True)
    controls={key(r):r for r in rows if r['route']=='route0'};summaries=[]
    for row in rows:
        c=controls[key(row)];row.update(source_result=c['result'],source_margin=c['margin'],delta_own=row['candidate_reward']-c['candidate_reward'],
            delta_rival=row['opponent_reward']-c['opponent_reward'],delta_margin=row['margin']-c['margin'])
    for route in p['arms']:
        games=[r for r in rows if r['route']==route];assert len(games)==len(scope['fixtures'])*2
        groups={f['fixture_id']:[r for r in games if r['fixture_id']==f['fixture_id']] for f in scope['fixtures']}
        regressions=[list(key(r)) for r in games if r['source_result']=='win' and r['result']!='win']
        public_failures=[list(key(r)) for r in games if r['panel']=='public54' and r['result']!='win']
        rescue=all(r['result']=='win' for r in groups[THIRD])
        rescued=[fid for fid,pair in groups.items() if all(r['result']=='win' for r in pair) and any(r['source_result']!='win' for r in pair)]
        summaries.append(dict(route=route,eligible=all(r['clean'] for r in games) and not regressions and not public_failures and rescue,
            source_win_regressions=regressions,affected_public_failures=public_failures,third_rescued=rescue,rescued=rescued,
            points=sum(1 if r['result']=='win' else .5 if r['result']=='draw' else 0 for r in games),mean_delta_margin=sum(r['delta_margin'] for r in games)/len(games)))
    eligible=[s for s in summaries if s['eligible']]
    selected=sorted(eligible,key=lambda s:(-len(s['rescued']),-s['points'],-s['mean_delta_margin'],s['route']))[0]['route'] if eligible else None
    write(HERE/'screen.json',dict(complete=True,passed=selected is not None,selected_route=selected,summaries=summaries,games=rows,
        scope_sha256=sha(HERE/'scope.json'),pool_sha256=sha(HERE/'pool.json'),completed_at_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps({'selected':selected,'summaries':summaries},indent=2),flush=True)
    if selected:
        arm=p['arms'][selected];path=HERE/'candidate_combined.py'
        with path.open('xb') as out:out.write(Path(arm['candidate']).read_bytes())
        write(HERE/'combined_binding.json',dict(candidate=str(path),candidate_sha256=sha(path),route=selected,screen_sha256=sha(HERE/'screen.json'),scope_sha256=sha(HERE/'scope.json')))


def combined():
    p=validate();scope=read(HERE/'scope.json');screen=read(HERE/'screen.json');binding=read(HERE/'combined_binding.json')
    assert screen['passed'] and binding['screen_sha256']==sha(HERE/'screen.json') and binding['scope_sha256']==sha(HERE/'scope.json')
    assert sha(binding['candidate'])==binding['candidate_sha256'];assert not (HERE/'combined_results.json').exists()
    jobs=[dict(**binding,fixture=f,candidate_seat=seat,trace_path=str(HERE/('combined_'+f['fixture_id']+'_seat'+str(seat)+'.jsonl.gz')))
          for f in scope['fixtures'] for seat in (0,1)]
    with ProcessPoolExecutor(max_workers=1,max_tasks_per_child=8) as ex:rows=list(ex.map(full_worker,jobs))
    expected={key(r):r for r in screen['games'] if r['route']==binding['route']};fields=('candidate_reward','opponent_reward','candidate_status','opponent_status','frames','candidate_telemetry')
    mismatches=[dict(key=list(key(r)),fields=[k for k in fields if r[k]!=expected[key(r)][k]]) for r in rows if any(r[k]!=expected[key(r)][k] for k in fields)]
    regressions=[list(key(r)) for r in rows if expected[key(r)]['source_result']=='win' and r['result']!='win']
    passed=all(r['clean'] for r in rows) and not mismatches and not regressions and all(r['result']=='win' for r in rows)
    write(HERE/'combined_results.json',dict(complete=True,passed=passed,expected_mismatches=mismatches,source_win_regressions=regressions,
        games=rows,candidate_sha256=binding['candidate_sha256'],binding_sha256=sha(HERE/'combined_binding.json'),completed_at_utc=datetime.now(timezone.utc).isoformat()))
    if passed:
        with (HERE/('main_candidate_third_pair_'+binding['candidate_sha256'][:8]+'.py')).open('xb') as out:out.write(Path(binding['candidate']).read_bytes())
    print('Exact affected combined',passed,'games',len(rows),'candidate',binding['candidate_sha256'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('prepare','discover','screen','combined'));args=parser.parse_args()
    with exclusive_run(HERE/'study.lock'):{'prepare':prepare,'discover':discover,'screen':screen,'combined':combined}[args.phase]()
