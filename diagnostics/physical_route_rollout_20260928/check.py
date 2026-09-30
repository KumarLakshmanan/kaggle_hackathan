"""Extract pure native transitions and verify complete recorded continuations."""
from datetime import datetime, timezone
from pathlib import Path
import ast
import copy
import gzip
import hashlib
import importlib.util
import json
import time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Box(dict):
    def __getattr__(self,name):
        try:return self[name]
        except KeyError:raise AttributeError(name) from None
    def __setattr__(self,name,value):self[name]=value


def extract():
    engine=Path(importlib.util.find_spec('kaggle_environments').origin).parent/'envs/kaggriculture/kaggriculture.py'
    source=engine.read_text(encoding='utf-8')
    syntax=ast.parse(source)
    kept=[]
    for node in syntax.body:
        if isinstance(node,ast.Assign) and node.lineno<121:
            names=[n.id for n in node.targets if isinstance(n,ast.Name)]
            if names and all(name.isupper() for name in names):kept.append(node)
        elif isinstance(node,ast.FunctionDef) and node.name!='_initialize' and node.lineno<968:
            kept.append(node)
    text='"""Pure Kaggriculture 1.32.7 transitions; initialized-state use only."""\nimport math\nimport random\n\n'
    text+='\n\n'.join(ast.get_source_segment(source,node) for node in kept)
    text+='\n\ndef _initialize(state, env):\n    raise ValueError("An initialized observation is required")\n'
    target=HERE/'native_core.py'
    if target.exists():assert target.read_text(encoding='utf-8')==text
    else:target.write_text(text,encoding='utf-8')
    namespace={}
    exec(compile(text,str(target),'exec'),namespace)
    return namespace,dict(engine_source=str(engine),engine_source_sha256=sha(engine),
                          extracted_source=str(target),extracted_source_sha256=sha(target))


def state_from_frames(frame):
    public=copy.deepcopy({key:frame[0]['observation'][key] for key in ('farms','market','town','day','hour','step')})
    return [Box(status='ACTIVE',reward=0,action={},observation=Box(**public,player=seat,
                private=copy.deepcopy(frame[seat]['observation']['private']))) for seat in (0,1)]


def compare(state,frame):
    expected0=frame[0]['observation']
    mismatches=[key for key in ('farms','market','town','day','hour','step') if state[0].observation[key]!=expected0[key]]
    for seat in (0,1):
        if state[seat].observation.private!=frame[seat]['observation']['private']:
            mismatches.append('private'+str(seat))
    return mismatches


def main():
    manifest_path=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
    assert sha(manifest_path)=='524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    assert sha(ROOT/'main.py')=='4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    fixtures=[manifest['live_losses'][0],next(f for f in manifest['live_losses'] if f['team']=='mhw')]
    fixtures.extend(next(f for f in manifest['current_top20'] if f['team']==team) for team in ('DECEM','Vadim Vasilenko'))
    core,provenance=extract()
    rows=[]
    for fixture in fixtures:
        raw=gzip.decompress(Path(fixture['source_replay_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==fixture['source_replay_sha256']
        replay=json.loads(raw);del raw
        assert replay['module_version']=='1.32.7' and len(replay['steps'])==720
        state=state_from_frames(replay['steps'][144])
        env=Box(configuration=Box(**replay['configuration']),info={'seed':fixture['seed']},done=False)
        assert not compare(state,replay['steps'][144])
        started=time.perf_counter();mismatch=None;transitions=0
        for step in range(144,719):
            for seat in (0,1):state[seat].action=copy.deepcopy(replay['steps'][step+1][seat].get('action') or {})
            core['interpreter'](state,env)
            for item in state:item.observation.step=step+1
            transitions+=1
            bad=compare(state,replay['steps'][step+1])
            if bad:
                mismatch=dict(step=step,next_observation=step+1,fields=bad)
                break
        elapsed=time.perf_counter()-started
        rewards=[r.reward for r in state]
        expected=[float(r) for r in replay['rewards']]
        result=dict(fixture_id=fixture['fixture_id'],team=fixture['team'],source_replay_sha256=fixture['source_replay_sha256'],
            seed=fixture['seed'],start_step=144,transitions=transitions,mismatch=mismatch,
            statuses=[r.status for r in state],rewards=rewards,expected_rewards=expected,
            seconds_including_comparisons=elapsed,ms_per_transition=elapsed*1000/transitions)
        result['passed']=mismatch is None and transitions==575 and result['statuses']==['DONE','DONE'] and rewards==expected
        rows.append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
        del replay,state
    payload=dict(complete=True,passed=all(r['passed'] for r in rows),diagnostic_only=True,
        uses_known_seed_and_both_private_states=True,plan_sha256=sha(HERE/'PLAN.md'),
        completed_at_utc=datetime.now(timezone.utc).isoformat(),**provenance,fixtures=rows)
    (HERE/'parity.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Engineering parity pass:',payload['passed'])


if __name__=='__main__':main()
