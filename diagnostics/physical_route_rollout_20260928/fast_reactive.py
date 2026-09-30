"""Memory-bounded two-policy diagnostics; framework checks remain separate."""
from pathlib import Path
import copy
import gc
import importlib.util
import json
import time

from . import native_core as core
from .check import Box,state_from_frames,sha

HERE=Path(__file__).resolve().parent


def load_policy(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def errors(module):
    reports={name:value for name,value in vars(module).items() if isinstance(value,dict) and ('STATS' in name or 'REPORT' in name)}
    reports['agent.telemetry']=getattr(module.agent,'telemetry',{})
    return {name+'.'+str(k):v for name,d in reports.items() for k,v in d.items()
            if ('error' in str(k).lower() or 'collision' in str(k).lower()) and isinstance(v,(int,float)) and v}


def play(job,steps=719):
    assert 1<=steps<=719
    assert sha(job['path'])==job['candidate_sha256'] and sha(job['opponent'])==job['opponent_sha256']
    template=json.loads((HERE/'initial_template.json').read_text(encoding='utf-8'))
    state=state_from_frames(template['frame'])
    cfg=dict(template['configuration']);cfg['seed']=None
    env=Box(configuration=Box(**cfg),info={'seed':int(job['seed'])},done=False)
    modules=[None,None];seat=int(job['candidate_seat'])
    modules[seat]=load_policy(job['path'],'fast_reacting_candidate')
    modules[1-seat]=load_policy(job['opponent'],'fast_reacting_reference')
    timings=[0.,0.];maxima=[0.,0.];shops144=None
    started=time.perf_counter()
    try:
        for step in range(steps):
            if step==144:shops144=list(state[0].observation.town['unlocked_shops'][:2])
            for player,module in enumerate(modules):
                obs=copy.deepcopy(dict(state[player].observation,remainingOverageTime=60.0))
                tick=time.perf_counter();state[player].action=module.agent(obs,cfg);duration=time.perf_counter()-tick
                timings[player]+=duration;maxima[player]=max(maxima[player],duration)
            core.interpreter(state,env)
            for item in state:item.observation.step=step+1
        if steps==144:shops144=list(state[0].observation.town['unlocked_shops'][:2])
        result=dict(job,frames=steps+1,observed_step=steps,candidate_status=state[seat].status,opponent_status=state[1-seat].status,
                    candidate_telemetry=dict(getattr(modules[seat].agent,'telemetry',{}) or {}),
                    opponent_telemetry=dict(getattr(modules[1-seat].agent,'telemetry',{}) or {}),
                    candidate_errors=errors(modules[seat]),opponent_errors=errors(modules[1-seat]),
                    configuration_seed_visible=None,wall_seconds=time.perf_counter()-started,
                    candidate_call_seconds=timings[seat],max_candidate_call_seconds=maxima[seat],shops144=shops144,
                    engine='Pure native core; not framework schema/timeouts/file loader')
        if steps==719:
            own=float(state[seat].reward);rival=float(state[1-seat].reward)
            result.update(candidate_reward=own,opponent_reward=rival,margin=own-rival,
                          result='win' if own>rival else 'loss' if own<rival else 'draw')
        assert sha(job['path'])==job['candidate_sha256'] and sha(job['opponent'])==job['opponent_sha256']
        return result
    finally:
        del modules,state
        gc.collect()
