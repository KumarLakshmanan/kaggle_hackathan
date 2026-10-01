"""Fresh state/reset checks for the frozen union of passing additions."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
from run_experiment import sha,ROOT
from diagnostics.physical_route_rollout_20260928.check import state_from_frames,Box
from diagnostics.physical_route_rollout_20260928 import native_core as core
HERE=Path(__file__).resolve().parent

def load(suffix):
    spec=importlib.util.spec_from_file_location('joint_probe_'+suffix,HERE/'candidate_joint.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    a,b=load('a'),load('b');rows=[]
    jobs=json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
    for rank in (1,8):
        j=next(j for j in jobs if j['rank']==rank)
        tape=json.loads(gzip.decompress(Path(j['entry']['replay_path']).read_bytes()));cfg=dict(tape['configuration'],seed=None)
        for step in (0,144,480,671,717,718):
            for seat in (0,1):
                obs=copy.deepcopy(tape['steps'][step][seat]['observation']);obs['step']=step
                original=copy.deepcopy(obs);altered=copy.deepcopy(obs);altered['episode_id']='UNUSED';altered['remainingOverageTime']=999.
                action=a.agent(obs,cfg);other=b.agent(altered,dict(cfg,seed=555))
                assert action==other and obs==original
                assert not a._BORROW_CONTROLLER.stats['borrow_errors'] and not b._BORROW_CONTROLLER.stats['borrow_errors']
                state=state_from_frames(tape['steps'][step]);state[seat].action=action;state[1-seat].action={'farmer':['PASS'],'hands':[],'market':[]}
                core.interpreter(state,Box(configuration=Box(**cfg),info={'seed':11},done=False))
                assert all(s.status in ('ACTIVE','DONE') for s in state)
                rows.append({'rank':rank,'step':step,'seat':seat,'passed':True})
    (HERE/'joint_engineering_receipt.json').write_text(json.dumps({'passed':True,'candidate_sha256':sha(HERE/'candidate_joint.py'),'cases':rows},indent=2),encoding='utf-8')

if __name__=='__main__':main()
