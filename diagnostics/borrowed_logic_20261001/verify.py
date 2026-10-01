"""Read-only native and information-boundary checks before full games."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928.check import Box,state_from_frames
from diagnostics.physical_route_rollout_20260928 import native_core as core

MODES=('belief','feed','accounting','dynamic','endgame','combined')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(mode,suffix):
    path=HERE/f'candidate_{mode}.py';spec=importlib.util.spec_from_file_location('borrow_verify_'+mode+suffix,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    jobs=json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
    rows=[];maxima={};errors=[]
    for mode in MODES:
        a,b=load(mode,'_a'),load(mode,'_b');maximum=0.
        for rank in (1,8):
            fixture=next(j for j in jobs if j['rank']==rank and j['candidate_seat']==0)
            replay=json.loads(gzip.decompress(Path(fixture['entry']['replay_path']).read_bytes()))
            cfg=dict(replay['configuration'],seed=None)
            for step in (0,144,480,671,717,718):
                for seat in (0,1):
                    obs=copy.deepcopy(replay['steps'][step][seat]['observation']);obs['step']=step
                    altered=copy.deepcopy(obs);altered['remainingOverageTime']=987.0;altered['episode_id']='NOT_A_POLICY_INPUT'
                    stamp=json.dumps(obs,sort_keys=True)
                    tick=time.perf_counter();first=a.agent(obs,cfg);elapsed=time.perf_counter()-tick;maximum=max(maximum,elapsed)
                    second=b.agent(altered,dict(cfg,seed=2147483646))
                    assert first==second,(mode,rank,step,seat,'seed/metadata changed action')
                    assert json.dumps(obs,sort_keys=True)==stamp,'Input observation mutated'
                    if a._BORROW_CONTROLLER.stats['borrow_errors']:
                        errors.append({'mode':mode,'rank':rank,'step':step,'seat':seat,'error':a._BORROW_CONTROLLER.last_error})
                    assert isinstance(first,dict) and set(first)=={'farmer','hands','market'}
                    assert len(first['market'])<=int(cfg.get('maxMarketOrdersPerTurn',10))
                    state=state_from_frames(replay['steps'][step]);state[seat].action=copy.deepcopy(first)
                    state[1-seat].action={'farmer':['PASS'],'hands':[],'market':[]}
                    env=Box(configuration=Box(**cfg),info={'seed':11},done=False)
                    core.interpreter(state,env)
                    assert all(s.status in ('ACTIVE','DONE') for s in state)
                    rows.append({'mode':mode,'rank':rank,'step':step,'seat':seat,'seconds':elapsed,'passed':not errors})
            del replay
        maxima[mode]=maximum
        print(json.dumps({'mode':mode,'max_seconds':maximum,'errors':sum(e['mode']==mode for e in errors)}),flush=True)
        del a,b
    # Explicit survival deadline: wheat in the shed must first be picked up,
    # then the same carried unit must feed the animal before the day boundary.
    feed=load('feed','_focus');pack=feed._BORROW_PACKAGE;cfg={'boardSize':10,'turnsPerDay':24,'shedCapacity':100,'episodeSteps':720,
        'maxMarketOrdersPerTurn':10,'farmHandCostMult':1,'weedSpawnChance':0.}
    farm=core._new_farm(10,3000);other=core._new_farm(10,3000);private=core._new_private()
    farm['tiles'][4][4]=core._new_animal('GOOSE',0);farm['tiles'][4][4]['consecutive_unfed']=1
    private['shed']['WHEAT']=2
    obs={'farms':[farm,other],'private':private,'player':0,'step':142,'day':5,'hour':22,'market':core._new_market(),'town':core._new_town()}
    repaired,report=pack.scheduler.repair_feed_service(obs,cfg,{'farmer':['PASS'],'hands':[],'market':[]},return_report=True)
    assert repaired['farmer'][:2]==['PICKUP','WHEAT'],report
    w=pack.engine.make_world(obs,pack.engine.clean_config(cfg,obs),pack.engine.SCENARIOS[0])
    joint=[repaired,{'farmer':['PASS'],'hands':[],'market':[]}]
    for p in (0,1):w[0][p].action=joint[p]
    core.interpreter(*w)
    for entry in w[0]:entry.observation.step=143
    next_obs=copy.deepcopy(dict(w[0][0].observation))
    repaired,report=pack.scheduler.repair_feed_service(next_obs,cfg,{'farmer':['PASS'],'hands':[],'market':[]},return_report=True)
    assert repaired['farmer']==['FEED'],report
    # Terminal cargo must reach the shed and be sold, not merely harvested.
    terminal=copy.deepcopy(obs);terminal['step']=717;terminal['day']=29;terminal['hour']=21
    terminal['farms'][0]=core._new_farm(10,3000);terminal['farms'][0]['farmer']=[3,4]
    terminal['private']=core._new_private();terminal['private']['inventories'][0]={'MILK':2}
    path=[]
    world=pack.engine.make_world(terminal,pack.engine.clean_config(cfg,terminal),pack.engine.SCENARIOS[0])
    money=world[0][0].observation.farms[0]['money']
    for step in (717,718):
        visible=copy.deepcopy(dict(world[0][0].observation));visible['step']=step
        act=pack.scheduler.schedule(visible,cfg,'liquidate',{'focus':'liquidate'});path.append(act)
        world[0][0].action=act;world[0][1].action={'farmer':['PASS'],'hands':[],'market':[]}
        core.interpreter(*world)
        for entry in world[0]:entry.observation.step=step+1
    assert world[0][0].observation.farms[0]['money']>money,path
    receipt={'passed':not errors,'case_count':len(rows),'cases':rows,'errors':errors,'max_seconds':maxima,
        'focused':{'actual_pickup_then_feed':True,'terminal_deliver_then_sell':True},
        'candidate_hashes':{mode:sha(HERE/f'candidate_{mode}.py') for mode in MODES},
        'scope':'Engineering/synthetic native checks, not measured win rate.'}
    (HERE/'engineering_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='cases'},indent=2),flush=True)
    assert receipt['passed'],errors


if __name__=='__main__':main()
