"""Bounded actual-shop donor repair; immutable controls and one cached worker."""
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import argparse
import copy
import gc
import gzip
import importlib.util
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OLD=ROOT/'diagnostics/adaptive_opening_bridge_20260928'
SOURCE=OLD/'candidate_five_hand.py'
SOURCE_SHA='ceed697f9af3927fe4abc5b62e9e1e0ad7358361b3581a087da86558c8294d46'
OLD_RECEIPT_SHA='224cae4a3f69ac480ee2979db33df1d21aaaa5ff3ba2cfa3f2c3183fbdd91605'
sys.path.insert(0,str(ROOT))
from diagnostics.adaptive_opening_bridge_20260928.build import read,write,sha,module
from diagnostics.stream_replay_io_20260928.fast_game_cached import play
from diagnostics.stream_replay_io_20260928.cached_input import load_fixture
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import Box,state_from_frames
from diagnostics.local_target_20260928.run_lock import exclusive_run


def key(row):return row['fixture_id'],row['candidate_seat']


def build(path,mapping):
    assert sha(SOURCE)==SOURCE_SHA
    addition=('\n_DONOR_PAIR_REPAIR = '+repr(mapping)+'\n'
              "_BRIDGE_DONORS['shared151']['_DONOR_MAP'].update(_DONOR_PAIR_REPAIR)\n\n"
              'def kaggle_donor_pair_repair_entrypoint(observation, configuration=None):\n'
              '    return agent(observation, configuration)\n')
    code=SOURCE.read_bytes()+addition.encode()
    compile(code,str(path),'exec')
    with path.open('xb') as stream:stream.write(code)
    original=module(SOURCE,'pair_source');changed=module(path,'pair_changed')
    ns=changed._BRIDGE_DONORS['shared151'];old=original._BRIDGE_DONORS['shared151']
    assert changed._DATA==original._DATA and changed._BRIDGE_COMMON==original._BRIDGE_COMMON
    assert ns['_DONOR_ROUTES']==old['_DONOR_ROUTES']
    first=ns['_DONOR_ROUTES']['route0'][:151]
    assert all(route[:151]==first for route in ns['_DONOR_ROUTES'].values())
    assert ns['_QUEUE_PARENT'] is ns['_donor_action'] and ns['_ITERATED_QUEUE_RAW'] is ns['_donor_action']
    assert all(ns[name].__globals__ is ns for name in ('_donor_action','_donor_schedule','_hire_recovery_schedule'))
    for pair,route in mapping.items():
        obs={'step':144,'town':{'unlocked_shops':pair.split('|')}}
        assert ns['_hire_recovery_schedule'](obs) is ns['_DONOR_ROUTES'][route]
        assert ns['_ITERATED_QUEUE_RAW'](obs)==ns['_DONOR_ROUTES'][route][144]
    del original,changed;gc.collect()
    return dict(candidate=str(path),candidate_sha256=sha(path),mapping=mapping)


def prepare():
    assert sha(SOURCE)==SOURCE_SHA and sha(OLD/'development_results.json')==OLD_RECEIPT_SHA
    old_pool=read(OLD/'development_pool.json');old=read(OLD/'development_results.json')
    assert old['complete'] and all(r['clean'] for r in old['games'])
    controls=[r for r in old['games'] if r['variant']=='five_hand']
    assert len(controls)==24
    priorities=['top20-03-Boey-114266440','live-114279308'];pairs=[]
    for fid in priorities:
        rows=[r for r in controls if r['fixture_id']==fid]
        observed={r['candidate_telemetry']['donor_pair144'] for r in rows}
        assert len(rows)==2 and len(observed)==1
        pair=observed.pop()
        if pair not in pairs:pairs.append(pair)
    assert len(pairs)<=2
    arms=[]
    for index,pair in enumerate(pairs):
        affected=[r for r in controls if r['candidate_telemetry'].get('bridge_selected')=='shared151'
                  and r['candidate_telemetry'].get('donor_pair144')==pair]
        original_routes={r['candidate_telemetry']['donor_selected'] for r in affected};assert len(original_routes)==1
        original_route=original_routes.pop()
        for route in ('route0','route1','route2'):
            arm=dict(pair=pair,route=route,affected=[list(key(r)) for r in affected],control_reuse=route==original_route)
            if arm['control_reuse']:arm.update(candidate=str(SOURCE),candidate_sha256=SOURCE_SHA)
            else:arm.update(build(HERE/('candidate_pair'+str(index)+'_'+route+'.py'),{pair:route}))
            arms.append(arm)
    bindings=dict(old_pool['bindings'])
    for path in (HERE/'PLAN.md',Path(__file__),OLD/'development_pool.json',OLD/'development_results.json'):
        bindings[str(path)]=sha(path)
    for arm in arms:bindings[arm['candidate']]=arm['candidate_sha256']
    for row in controls:
        assert sha(row['trace_path'])==row['trace_sha256']
        bindings[row['trace_path']]=row['trace_sha256']
    write(HERE/'pool.json',dict(source=str(SOURCE),source_sha256=SOURCE_SHA,source_receipt_sha256=OLD_RECEIPT_SHA,
        pairs=pairs,arms=arms,controls=controls,fixtures=old_pool['fixtures'],bindings=bindings,
        preflight_passed=True,created_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Pair repair prepared',pairs,'new games',sum(len(a['affected']) for a in arms if not a['control_reuse']),sha(HERE/'pool.json'),flush=True)


def validate():
    pool=read(HERE/'pool.json')
    assert all(sha(path)==digest for path,digest in pool['bindings'].items())
    return pool


def prefix_job(job):
    fixture=job['fixture'];cached=load_fixture(fixture);state=state_from_frames(cached['steps'][0])
    cfg=dict(cached['configuration'],seed=None);seat=job['candidate_seat']
    env=Box(configuration=Box(**cfg),info={'seed':int(fixture['seed'])},done=False)
    candidate=module(job['candidate'],'pair_prefix')
    tape=json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    assert sha(job['control']['trace_path'])==job['control']['trace_sha256']
    with gzip.open(job['control']['trace_path'],'rt',encoding='utf-8') as trace:
        for step in range(144):
            expected=json.loads(next(trace));obs=copy.deepcopy(dict(state[seat].observation,remainingOverageTime=60.0))
            action=candidate.agent(obs,cfg)
            assert expected['step']==step and expected['observation']==obs and expected['action']==action,(job['pair'],job['route'],seat,step)
            state[seat].action=action;state[1-seat].action=copy.deepcopy(tape[step]);core.interpreter(state,env)
            for item in state:item.observation.step=step+1
        expected144=json.loads(next(trace))
        actual144=copy.deepcopy(dict(state[seat].observation,remainingOverageTime=60.0))
        assert actual144==expected144['observation']
        assert '|'.join(actual144['town']['unlocked_shops'][:2])==job['pair']
    result=dict(pair=job['pair'],route=job['route'],fixture_id=fixture['fixture_id'],candidate_seat=seat,
        candidate_sha256=job['candidate_sha256'],passed=True,transitions=144,exact_observations=145,exact_actions=144,
        control_trace_sha256=job['control']['trace_sha256'])
    del candidate,state,tape;gc.collect();return result


def make_jobs(pool):
    controls={key(r):r for r in pool['controls']};fixtures={f['fixture_id']:f for f in pool['fixtures']};jobs=[]
    for index,arm in enumerate(pool['arms']):
        if arm['control_reuse']:continue
        for fid,seat in arm['affected']:
            jobs.append(dict(**arm,fixture=fixtures[fid],candidate_seat=seat,control=controls[fid,seat],
                trace_path=str(HERE/('pair'+str(index)+'_'+str(fixtures[fid]['episode_id'])+'_seat'+str(seat)+'.jsonl.gz'))))
    return jobs


def prefixes():
    pool=validate();assert not (HERE/'prefix_results.json').exists()
    with ProcessPoolExecutor(max_workers=1) as executor:rows=list(executor.map(prefix_job,make_jobs(pool)))
    write(HERE/'prefix_results.json',dict(passed=all(r['passed'] for r in rows),games=rows,pool_sha256=sha(HERE/'pool.json'),completed_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Prefix proof passed',len(rows),'candidate-fixture-seats; receipt',sha(HERE/'prefix_results.json'),flush=True)


def worker(job):
    row=play(job['fixture'],job['candidate'],job['candidate_sha256'],job['candidate_seat'],job['trace_path'])
    control=job['control'];stats=row['candidate_telemetry']
    row.update(pair=job.get('pair'),route=job.get('route'),control_reuse=False,
        source_result=control['source_result'],source_margin=control['source_margin'],
        ceed_result=control['result'],ceed_margin=control['margin'],
        delta_own=row['candidate_reward']-control['candidate_reward'],delta_rival=row['opponent_reward']-control['opponent_reward'],
        delta_margin=row['margin']-control['margin'],trace_path=job['trace_path'],trace_sha256=sha(job['trace_path']))
    row['clean']=(row['frames']==720 and row['candidate_status']==row['opponent_status']=='DONE' and not row['candidate_errors']
                  and not stats.get('bridge_common_failed',0) and not stats.get('bridge_source_guard_failed',0))
    return row


def screen():
    pool=validate();prefix=read(HERE/'prefix_results.json');assert prefix['passed'] and prefix['pool_sha256']==sha(HERE/'pool.json')
    assert not (HERE/'screen.json').exists()
    controls={key(r):r for r in pool['controls']};rows=[]
    for arm in pool['arms']:
        if arm['control_reuse']:
            for fid,seat in arm['affected']:
                control=controls[fid,seat]
                row=dict(control,pair=arm['pair'],route=arm['route'],control_reuse=True,
                    ceed_result=control['result'],ceed_margin=control['margin'],delta_own=0,delta_rival=0,delta_margin=0,
                    reused_candidate_sha256=SOURCE_SHA,reused_receipt_sha256=OLD_RECEIPT_SHA)
                rows.append(row)
    checkpoint=HERE/'screen_new.jsonl'
    prior=[json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    done={(r['pair'],r['route'],*key(r)) for r in prior};assert len(done)==len(prior)
    for row in prior:assert sha(row['trace_path'])==row['trace_sha256']
    rows+=prior
    pending=[j for j in make_jobs(pool) if (j['pair'],j['route'],j['fixture']['fixture_id'],j['candidate_seat']) not in done]
    with checkpoint.open('a',encoding='utf-8') as stream:
        for start in range(0,len(pending),8):
            with ProcessPoolExecutor(max_workers=1) as executor:
                for row in executor.map(worker,pending[start:start+8]):
                    rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                    print('Pair repair',row['pair'],row['route'],row['fixture_id'],row['candidate_seat'],row['result'],row['margin'],flush=True)
    choices={};summaries=[]
    for pair in pool['pairs']:
        choices_for_pair=[]
        for route in ('route0','route1','route2'):
            games=[r for r in rows if r['pair']==pair and r['route']==route]
            fids={r['fixture_id'] for r in games};assert len(games)==len(fids)*2
            regressions=[list(key(r)) for r in games if (r['source_result']=='win' or r['ceed_result']=='win') and r['result']!='win']
            rescues=[fid for fid in fids if all(r['result']=='win' for r in games if r['fixture_id']==fid)
                     and any(r['ceed_result']!='win' for r in games if r['fixture_id']==fid)]
            summary=dict(pair=pair,route=route,eligible=all(r['clean'] for r in games) and not regressions,
                regressions=regressions,rescues=rescues,points=sum(1 if r['result']=='win' else .5 if r['result']=='draw' else 0 for r in games),
                mean_delta_margin=sum(r['delta_margin'] for r in games)/len(games))
            summaries.append(summary)
            if summary['eligible']:choices_for_pair.append(summary)
        if choices_for_pair:
            chosen=sorted(choices_for_pair,key=lambda s:(-len(s['rescues']),-s['points'],-s['mean_delta_margin'],s['route']))[0]
            choices[pair]=chosen['route']
    boey_pair=pool['pairs'][0]
    passed=boey_pair in choices
    result=dict(complete=len(rows)==sum(len(a['affected']) for a in pool['arms']),passed=passed,choices=choices,
        summaries=summaries,games=rows,pool_sha256=sha(HERE/'pool.json'),prefix_sha256=sha(HERE/'prefix_results.json'),
        completed_at_utc=datetime.now(timezone.utc).isoformat())
    write(HERE/'screen.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2),flush=True)
    if passed:
        effective={pair:route for pair,route in choices.items()
                   if not next(a for a in pool['arms'] if a['pair']==pair and a['route']==route)['control_reuse']}
        combined=build(HERE/'candidate_combined.py',effective)
        write(HERE/'combined_binding.json',dict(**combined,screen_sha256=sha(HERE/'screen.json'),pool_sha256=sha(HERE/'pool.json')))


def combined():
    pool=validate();screen_result=read(HERE/'screen.json');binding=read(HERE/'combined_binding.json')
    assert screen_result['complete'] and screen_result['passed'] and binding['screen_sha256']==sha(HERE/'screen.json')
    assert sha(binding['candidate'])==binding['candidate_sha256'];assert not (HERE/'combined_results.json').exists()
    controls={key(r):r for r in pool['controls']};jobs=[]
    for fixture in pool['fixtures']:
        for seat in (0,1):jobs.append(dict(**binding,fixture=fixture,candidate_seat=seat,control=controls[fixture['fixture_id'],seat],
            trace_path=str(HERE/('combined_'+str(fixture['episode_id'])+'_seat'+str(seat)+'.jsonl.gz'))))
    checkpoint=HERE/'combined_results.jsonl';rows=[json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    done={key(r) for r in rows};assert len(done)==len(rows)
    for row in rows:assert row['candidate_sha256']==binding['candidate_sha256'] and sha(row['trace_path'])==row['trace_sha256']
    pending=[j for j in jobs if (j['fixture']['fixture_id'],j['candidate_seat']) not in done]
    with checkpoint.open('a',encoding='utf-8') as stream:
        for start in range(0,len(pending),8):
            with ProcessPoolExecutor(max_workers=1) as executor:
                for row in executor.map(worker,pending[start:start+8]):
                    rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                    print('Combined pair repair',len(rows),'/24',row['fixture_id'],row['candidate_seat'],row['result'],row['margin'],flush=True)
    expected={key(r):r for r in pool['controls']}
    for row in screen_result['games']:
        if binding['mapping'].get(row['pair'])==row['route']:expected[key(row)]=row
    fields=('candidate_reward','opponent_reward','frames','candidate_status','opponent_status','candidate_telemetry')
    mismatches=[dict(key=list(key(r)),fields=[f for f in fields if r[f]!=expected[key(r)][f]]) for r in rows if any(r[f]!=expected[key(r)][f] for f in fields)]
    regressions=[list(key(r)) for r in rows if (r['source_result']=='win' or r['ceed_result']=='win') and r['result']!='win']
    boey=[r for r in rows if r['fixture_id']=='top20-03-Boey-114266440']
    passed=len(rows)==24 and all(r['clean'] for r in rows) and not regressions and not mismatches and len(boey)==2 and all(r['result']=='win' for r in boey)
    result=dict(complete=len(rows)==24,passed=passed,regressions=regressions,expected_mismatches=mismatches,
        WDL=[sum(r['result']==label for r in rows) for label in ('win','draw','loss')],games=rows,
        candidate_sha256=binding['candidate_sha256'],binding_sha256=sha(HERE/'combined_binding.json'),
        completed_at_utc=datetime.now(timezone.utc).isoformat())
    write(HERE/'combined_results.json',result)
    if passed:
        backup=HERE/('main_candidate_donor_pair_repair_'+binding['candidate_sha256'][:8]+'.py')
        with backup.open('xb') as stream:stream.write(Path(binding['candidate']).read_bytes())
        assert sha(backup)==binding['candidate_sha256']
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('prepare','prefix','screen','combined'));args=parser.parse_args()
    with exclusive_run(HERE/'study.lock'):
        {'prepare':prepare,'prefix':prefixes,'screen':screen,'combined':combined}[args.phase]()
