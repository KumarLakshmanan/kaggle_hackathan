"""Memory-bounded diagnostic engine. Native validation remains mandatory."""
from pathlib import Path
import copy
import gc
import gzip
import importlib.util
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import Box,state_from_frames,sha


def play(fixture,path,digest,seat,trace_path=None):
    assert sha(path)==digest
    import hashlib
    raw=gzip.decompress(Path(fixture['source_replay_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==fixture['source_replay_sha256']
    replay=json.loads(raw);del raw
    state=state_from_frames(replay['steps'][0])
    cfg=dict(replay['configuration']);cfg['seed']=None
    assert cfg['episodeSteps']==720
    env=Box(configuration=Box(**cfg),info={'seed':int(fixture['seed'])},done=False)
    del replay;gc.collect()
    tape=json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    hashes=[hashlib.sha256(json.dumps(tape,sort_keys=s,separators=(',',':')).encode()).hexdigest() for s in (False,True)]
    assert fixture['source_opponent_action_sha256'] in hashes and len(tape)==719
    spec=importlib.util.spec_from_file_location('fast_diagnostic_candidate',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    elapsed_calls=0.;max_call=0.;frames=1
    output=gzip.open(trace_path,'wt',encoding='utf-8') if trace_path else None
    started=time.perf_counter()
    try:
        for step in range(719):
            obs=copy.deepcopy(dict(state[seat].observation,remainingOverageTime=60.0))
            tick=time.perf_counter();action=module.agent(obs,cfg);duration=time.perf_counter()-tick
            elapsed_calls+=duration;max_call=max(max_call,duration)
            state[seat].action=action
            state[1-seat].action=copy.deepcopy(tape[step])
            if output:
                output.write(json.dumps(dict(step=step,observation=obs,action=action),separators=(',',':'))+'\n')
            core.interpreter(state,env)
            for item in state:item.observation.step=step+1
            frames+=1
        telemetry=dict(getattr(module.agent,'telemetry',{}) or {})
        errors={key:value for key,value in telemetry.items() if ('error' in key or 'collision' in key) and value}
        own=float(state[seat].reward);rival=float(state[1-seat].reward)
        result=dict(fixture_id=fixture['fixture_id'],candidate_seat=seat,candidate_sha256=digest,
            candidate_reward=own,opponent_reward=rival,margin=own-rival,
            result='win' if own>rival else 'loss' if own<rival else 'draw',
            candidate_status=state[seat].status,opponent_status=state[1-seat].status,frames=frames,
            candidate_telemetry=telemetry,candidate_errors=errors,configuration_seed_visible=None,
            wall_seconds=time.perf_counter()-started,candidate_call_seconds=elapsed_calls,max_candidate_call_seconds=max_call,
            harness='Pure native transitions; excludes framework schema/timeout/file-loader checks')
        assert sha(path)==digest
        return result
    finally:
        if output:output.close()
        del module,state
        gc.collect()


def main():
    folder=ROOT/'diagnostics/bakery_pizza_pool_20260928'
    selection=json.loads((folder/'selection.json').read_text(encoding='utf-8'))
    native=json.loads((folder/'screen.json').read_text(encoding='utf-8'))
    pool=json.loads((folder/'pool.json').read_text(encoding='utf-8'))
    assert selection['passed'] and native['complete'] and native['all_done'] and native['no_errors']
    assert sha(folder/'screen.json')==selection['screen_sha256']
    route=str(selection['selected_replacements']['BAKERY|PIZZA_SHOP'])
    controls={(r['rival'],r['candidate_seat']):r for r in native['games'] if r['version']==route}
    rows=[]
    for fixture in pool['fixtures']:
        for seat in (0,1):
            row=play(fixture,selection['candidate'],selection['candidate_sha256'],seat)
            control=controls[(fixture['fixture_id'],seat)]
            fields=('candidate_reward','opponent_reward','candidate_status','opponent_status','frames','candidate_telemetry')
            mismatches=[k for k in fields if row[k]!=control[k]]
            row['native_mismatches']=mismatches;row['passed']=not mismatches and not row['candidate_errors']
            rows.append(row)
            print(json.dumps({k:v for k,v in row.items() if k!='candidate_telemetry'}),flush=True)
    result=dict(complete=True,passed=all(r['passed'] for r in rows),diagnostic_only=True,
        candidate_sha256=selection['candidate_sha256'],plan_sha256=sha(HERE/'FAST_AGENT_PLAN.md'),
        core_sha256=sha(HERE/'native_core.py'),games=rows)
    (HERE/'fast_agent_parity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Full policy parity:',result['passed'])


if __name__=='__main__':main()
