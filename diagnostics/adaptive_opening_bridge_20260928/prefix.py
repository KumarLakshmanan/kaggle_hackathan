"""Frozen 24-turn engineering prefixes; no terminal game outcome evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import copy
import gc
import gzip
import importlib.util
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.adaptive_opening_bridge_20260928.build import read,write,sha
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import Box,state_from_frames
from diagnostics.stream_replay_io_20260928.cached_input import load_fixture
from diagnostics.local_target_20260928.run_lock import exclusive_run


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def positive(d):return {k:int(v) for k,v in d.items() if v}


def physical(farm,private,permutation=False):
    copied={k:copy.deepcopy(v) for k,v in farm.items() if k!='money'}
    inventories=[positive(v) for v in private['inventories']]
    if permutation and len(copied['hands'])==5:
        order=(4,1,2,3,5)
        copied['hands']=[copied['hands'][k-1] for k in order]
        inventories=[inventories[0]]+[inventories[k] for k in order]
    return dict(farm=copied,shed=positive(private['shed']),seeds=positive(private['seeds']),inventories=inventories)


def policy_errors(module):
    answer={}
    for name,value in vars(module).items():
        if isinstance(value,dict) and ('STATS' in name or 'REPORT' in name):
            for key,number in value.items():
                if ('error' in key.lower() or 'collision' in key.lower()) and isinstance(number,(int,float)) and number:
                    answer[name+'.'+key]=number
    for name,namespace in getattr(module,'_BRIDGE_DONORS',{}).items():
        for key,value in namespace['agent'].telemetry.items():
            if ('error' in key.lower() or 'collision' in key.lower()) and isinstance(value,(int,float)) and value:
                answer[name+'.'+key]=value
    return answer


def run_one(candidate_path,expected_sha,opponent,seat,is_bridge):
    assert sha(candidate_path)==expected_sha
    fixture=opponent['fixture'];cached=load_fixture(fixture)
    state=state_from_frames(cached['steps'][0]);cfg=dict(cached['configuration'],seed=None)
    env=Box(configuration=Box(**cfg),info={'seed':int(fixture['seed'])},done=False)
    del cached
    candidate=load(candidate_path,'prefix_candidate')
    rival=None;tape=None
    if opponent['kind']=='policy':
        assert sha(opponent['path'])==opponent['sha256']
        rival=load(opponent['path'],'prefix_rival')
    elif opponent['kind']=='tape':
        tape=json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    rows=[];common_ok=procurement_ok=None
    for step in range(24):
        actions=[]
        for player in (0,1):
            obs=copy.deepcopy(dict(state[player].observation,remainingOverageTime=60.0))
            if player==seat:
                action=candidate.agent(obs,cfg)
            elif rival is not None:
                action=rival.agent(obs,cfg)
            elif tape is not None:
                action=copy.deepcopy(tape[step])
            else:
                action={'farmer':['PASS'],'hands':[],'market':[]}
            actions.append(action)
            state[player].action=action
        core.interpreter(state,env)
        for item in state:item.observation.step=step+1
        own=state[seat].observation
        selected=getattr(candidate,'_BRIDGE_SELECTED','control')
        if is_bridge and step in (0,1):
            branch='common' if step==0 else selected
            equal=candidate._bridge_physical(own.farms[seat],own.private)==candidate._bridge_expected(branch,cfg)
            if step==0:common_ok=equal
            else:procurement_ok=equal
        rows.append(dict(step=step,actions=copy.deepcopy(actions),
                         physical=physical(own.farms[seat],own.private,is_bridge and selected=='shared150'),
                         own_cash=own.farms[seat]['money'],rival_cash=own.farms[1-seat]['money'],
                         market=copy.deepcopy(own.market),town=copy.deepcopy(own.town),
                         telemetry=copy.deepcopy(dict(candidate.agent.telemetry))))
    errors=policy_errors(candidate)
    if rival is not None:errors.update({'rival.'+k:v for k,v in policy_errors(rival).items()})
    result=dict(trace=rows,errors=errors,common_procurement_ok=common_ok,turn1_procurement_ok=procurement_ok,
                candidate_sha256=expected_sha,telemetry=copy.deepcopy(dict(candidate.agent.telemetry)))
    del candidate,rival,state,tape
    gc.collect()
    return result


def mismatches(left,right):
    return [key for key in left if left[key]!=right[key]]


def main():
    pool=read(HERE/'pool.json')
    assert all(sha(path)==digest for path,digest in pool['bindings'].items())
    assert read(HERE/'preflight.json')['passed'] and read(HERE/'preflight.json')['pool_sha256']==sha(HERE/'pool.json')
    assert not (HERE/'prefix_results.json').exists()
    checkpoint=HERE/'prefix_results.jsonl'
    prior=[json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    done={(r['variant'],r['class'],r['seat']) for r in prior}
    assert len(done)==len(prior)
    assert all(r['pool_sha256']==sha(HERE/'pool.json') for r in prior)
    rows=list(prior)
    with checkpoint.open('a',encoding='utf-8') as stream:
        for variant,arm in pool['arms'].items():
            for opponent in pool['classes']:
                for seat in (0,1):
                    if (variant,opponent['name'],seat) in done:continue
                    current=run_one(arm['candidate'],arm['candidate_sha256'],opponent,seat,True)
                    requested=current['telemetry']['bridge_requested'];selected=current['telemetry']['bridge_selected']
                    control=(dict(candidate=pool['source'],candidate_sha256=pool['source_sha256']) if requested=='source' else pool['donor_arms'][requested])
                    baseline=run_one(control['candidate'],control['candidate_sha256'],opponent,seat,False)
                    join=8 if requested=='shared151' else 1
                    first=mismatches(current['trace'][join]['physical'],baseline['trace'][join]['physical'])
                    end=mismatches(current['trace'][23]['physical'],baseline['trace'][23]['physical'])
                    trace_path=HERE/(variant+'_'+opponent['name']+'_seat'+str(seat)+'.json.gz')
                    assert not trace_path.exists()
                    with gzip.open(trace_path,'wt',encoding='utf-8') as out:json.dump(dict(bridge=current,original_branch=baseline),out,separators=(',',':'))
                    telemetry=current['telemetry']
                    passed=(selected==requested and current['common_procurement_ok'] and current['turn1_procurement_ok']
                            and not current['errors'] and not baseline['errors'] and not first and not end
                            and not telemetry['bridge_common_failed'] and not telemetry['bridge_guard_refusals']
                            and not telemetry['bridge_source_guard_failed'])
                    row=dict(variant=variant,**{'class':opponent['name']},seat=seat,requested=requested,selected=selected,
                             rival_hands=telemetry['bridge_rival_hands'],common_procurement_ok=current['common_procurement_ok'],
                             turn1_procurement_ok=current['turn1_procurement_ok'],guard_refusals=telemetry['bridge_guard_refusals'],
                             source_guard_failed=telemetry['bridge_source_guard_failed'],join_step=join,join_mismatches=first,day_end_mismatches=end,
                             candidate_errors=current['errors'],control_errors=baseline['errors'],
                             own_cash_delta=current['trace'][23]['own_cash']-baseline['trace'][23]['own_cash'],
                             rival_cash_delta=current['trace'][23]['rival_cash']-baseline['trace'][23]['rival_cash'],
                             passed=passed,trace_path=str(trace_path),trace_sha256=sha(trace_path),pool_sha256=sha(HERE/'pool.json'))
                    rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                    print('Bridge prefix',len(rows),'/32',variant,opponent['name'],seat,requested,selected,passed,
                          'join',first,'end',end,flush=True)
    summaries=[]
    for variant in pool['arms']:
        selected=[r for r in rows if r['variant']==variant]
        required={'source','shared151'} | ({'shared150'} if variant=='five_or_zero' else set())
        activated={r['selected'] for r in selected}
        summaries.append(dict(variant=variant,complete=len(selected)==16,passed=len(selected)==16 and all(r['passed'] for r in selected) and required<=activated,
                              passed_prefixes=sum(r['passed'] for r in selected),required_branches=sorted(required),activated=sorted(activated)))
    result=dict(complete=len(rows)==32,engineering_only=True,full_games=0,prefix_turns=24,paired_prefix_count=len(rows),
                summaries=summaries,rows=rows,pool_sha256=sha(HERE/'pool.json'),helper_sha256=sha(__file__),
                completed_at_utc=datetime.now(timezone.utc).isoformat())
    write(HERE/'prefix_results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__':
    with exclusive_run(HERE/'prefix.lock'):main()
