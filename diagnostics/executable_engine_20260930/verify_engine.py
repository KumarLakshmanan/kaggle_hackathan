"""Check generated-action search against the installed native transition code."""
import ast
import copy
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from kaggriculture_engine import engine as e
from kaggriculture_engine import native_core as core
from diagnostics.physical_route_rollout_20260928.check import state_from_frames

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    specification=importlib.util.find_spec('kaggle_environments')
    installed=Path(specification.origin).parent/'envs/kaggriculture/kaggriculture.py'
    source=installed.read_text(encoding='utf-8');tree=ast.parse(source)
    frozen=ast.parse((ROOT/'kaggriculture_engine/native_core.py').read_text(encoding='utf-8'))
    live_functions={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
    copied_functions={n.name:ast.dump(n,include_attributes=False) for n in frozen.body if isinstance(n,ast.FunctionDef) and n.name!='_initialize'}
    assert all(live_functions[k]==v for k,v in copied_functions.items())
    # Execute installed functions without importing visualization/render dependencies.
    namespace={'math':__import__('math'),'random':__import__('random')}
    allowed=[n for n in tree.body if isinstance(n,ast.FunctionDef) or
             (isinstance(n,ast.Assign) and any(isinstance(target,ast.Name) and target.id.isupper() for target in n.targets))]
    exec(compile(ast.Module(body=allowed,type_ignores=[]),str(installed),'exec'),namespace)
    jobs=json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
    fixtures=[j for j in jobs if j['rank'] in (1,8,10) and j['candidate_seat']==0]
    rows=[]
    for job in fixtures:
        replay=json.loads(gzip.decompress(Path(job['entry']['replay_path']).read_bytes()))
        for step in (0,143,144,239,478,718):
            for seat in (0,1):
                obs=copy.deepcopy(replay['steps'][step][seat]['observation'])
                obs['step']=step
                action=copy.deepcopy(replay['steps'][step+1][seat]['action'])
                cfg=dict(replay['configuration']);cfg['seed']=987654321
                chosen,report=e.optimize_market(obs,action,cfg,e.SearchConfig(max_nodes=12,depth=2))
                assert report['nodes']<=12
                assert chosen['farmer']==action['farmer'] and chosen.get('hands')==action.get('hands')
                cfg2=dict(cfg,seed=123456789)
                chosen2,report2=e.optimize_market(obs,action,cfg2,e.SearchConfig(max_nodes=12,depth=2))
                assert chosen==chosen2, 'Policy leaked an episode seed'
                for scenario in e.DEFAULT_SCENARIOS:
                    world=e.make_world(obs,cfg,scenario)
                    projected=e.advance(world,seat,chosen,action,scenario)
                    state,env=copy.deepcopy(world)
                    state[seat].action=copy.deepcopy(chosen)
                    state[1-seat].action=e.rival_action(state,seat,action,scenario)
                    namespace['interpreter'](state,env)
                    for item in state:item.observation.step=step+1
                    assert e.canonical(projected[0])==e.canonical(state)
                    control=e.advance(world,seat,action,action,scenario)
                    assert e.signature(projected[0])==e.signature(control[0])
                    assert e.cash_margin(projected,seat)>=e.cash_margin(control,seat)
                rows.append(dict(rank=job['rank'],step=step,seat=seat,nodes=report['nodes'],accepted=report['accepted'],passed=True))
    # A generated multi-turn recommendation must be executable and causal.
    initial=json.loads((ROOT/'diagnostics/physical_route_rollout_20260928/initial_template.json').read_text())
    payload=dict(observation=initial['frame'][0]['observation'],configuration=initial['configuration'])
    payload['observation']['step']=0
    (HERE/'example_observation.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    spec=importlib.util.spec_from_file_location('search_verification_baseline',ROOT/'main.py')
    baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
    def continuation(obs,cfg):return copy.deepcopy(baseline._DATA['opening'][int(obs['step'])])
    suggestion=e.search_plan(payload['observation'],payload['configuration'],continuation,horizon=4,width=2,max_nodes=400,seconds=30.)
    assert suggestion['completed_depth']==4 and suggestion['nodes']<=400
    assert not suggestion['uses_hidden_rival_state'] and not suggestion['uses_episode_seed']
    (HERE/'example_plan.json').write_text(json.dumps(suggestion,indent=2),encoding='utf-8')
    receipt=dict(passed=True,checked_cases=len(rows),scenario_transitions=len(rows)*3,
                 functions_matched=len(copied_functions),rows=rows,engine_sha256=sha(ROOT/'kaggriculture_engine/engine.py'),
                 core_sha256=sha(ROOT/'kaggriculture_engine/native_core.py'),installed_source_sha256=sha(installed),
                 completed_at_utc=datetime.now(timezone.utc).isoformat(),plan_nodes=suggestion['nodes'])
    (HERE/'engineering_checks.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
