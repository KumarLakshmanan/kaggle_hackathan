"""Exact standalone file-loader parity in both seats against a reacting policy."""
from datetime import datetime, timezone
import argparse
import gc
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def json_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def run(path,baseline,seat,mode):
    from paired_benchmark import make, _load_module, TimedAgent
    from diagnostics.opening_probe_v2_20260928.qualify import errors
    modules=[]
    try:
        paths=[path,baseline] if seat==0 else [baseline,path]
        if mode=='direct':
            modules=[_load_module(Path(p),f'repair_loader_{i}') for i,p in enumerate(paths)]
            def wrap(module):
                def call(obs,cfg):return module.agent(obs,dict(cfg,seed=None))
                return TimedAgent(call)
            agents=[wrap(m) for m in modules]
        else:agents=paths
        env=make('kaggriculture',configuration={'episodeSteps':720,'seed':12929001},debug=False)
        env.run(agents)
        final=env.steps[-1]
        bad=[(step,p,s.status) for step,frame in enumerate(env.steps) for p,s in enumerate(frame)
             if s.status in ('ERROR','INVALID','TIMEOUT')]
        stderr=[(step,p,str(log.get('stderr',''))) for step,logs in enumerate(env.logs) for p,log in enumerate(logs)
                if str(log.get('stderr','')).strip()]
        calls=[sum(len(logs)>p and 'duration' in logs[p] for logs in env.logs) for p in (0,1)]
        actions=[[frame[p].action for p in (0,1)] for frame in env.steps[1:]]
        row=dict(mode=mode,seat=seat,statuses=[s.status for s in final],frames=len(env.steps),
            rewards=[float(s.reward) for s in final],actions_sha256=json_sha(actions),
            native_calls=calls,bad_statuses=bad,stderr=stderr,
            minimum_remaining_overage=min(float(frame[seat].observation.remainingOverageTime) for frame in env.steps),
            policy_errors=[errors(m) for m in modules])
        row['passed']=(row['statuses']==['DONE','DONE'] and row['frames']==720 and calls==[719,719]
                       and not bad and not stderr and not any(row['policy_errors']) and row['minimum_remaining_overage']>=0)
        return row
    finally:
        for module in modules:sys.modules.pop(module.__name__,None)
        gc.collect()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('version');args=parser.parse_args()
    manifest=json.loads((HERE/f'manifest_{args.version}.json').read_text())
    assert sha(manifest['candidate'])==manifest['candidate_sha256']
    from kaggle_environments.agent import get_last_callable
    function=get_last_callable(Path(manifest['candidate']).read_text(encoding='utf-8'),path=manifest['candidate']).__name__
    assert function==manifest.get('expected_entrypoint','kaggle_a44_pet_market_gate_entrypoint')
    rows=[]
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        for seat in (0,1):
            pair=[]
            for mode in ('direct','file'):
                row=run(manifest['candidate'],manifest['baseline'],seat,mode);rows.append(row);pair.append(row)
                print(mode,seat,row['passed'],row['rewards'],flush=True)
            assert pair[0]['rewards']==pair[1]['rewards'] and pair[0]['actions_sha256']==pair[1]['actions_sha256']
        assert sha(manifest['candidate'])==manifest['candidate_sha256']
        result=dict(candidate_sha256=manifest['candidate_sha256'],loaded_name=function,rows=rows,
            passed=all(r['passed'] for r in rows),action_reward_parity=True,completed_at_utc=datetime.now(timezone.utc).isoformat())
        (HERE/f'loader_{args.version}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')

if __name__=='__main__':main()
