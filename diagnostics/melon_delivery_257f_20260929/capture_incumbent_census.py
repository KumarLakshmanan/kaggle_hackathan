from __future__ import annotations
import copy, gc, gzip, hashlib, importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import Box,state_from_frames,sha
from diagnostics.stream_replay_io_20260928.cached_input import load_fixture
from diagnostics.local_target_20260928.run_lock import exclusive_run

CANDIDATE=ROOT/'main_candidate_pet_source_guard_20260929_257f941d.py'
CANDIDATE_SHA='257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'
PANEL=ROOT/'diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/panel.json'
PANEL_SHA='fee3b1d5f93cd295c28dd8d0c04ea672806dbb55e2b59999853a9f969c0fb90d'
OUT=HERE/'incumbent_selector_census.json'
ACCESS=((4,4),(5,4),(4,5),(5,5))


def load_agent(path):
    spec=importlib.util.spec_from_file_location('incumbent_257f_selector_census',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def inspect_job(fixture,fixture_id,seat,panel_name):
    replay=load_fixture(fixture)
    cfg=dict(replay['configuration']);cfg['seed']=None
    assert cfg['episodeSteps']==720
    state=state_from_frames(replay['steps'][0])
    env=Box(configuration=Box(**cfg),info={'seed':int(fixture['seed'])},done=False)
    tape=json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    action_hashes=[hashlib.sha256(json.dumps(tape,sort_keys=s,separators=(',',':')).encode()).hexdigest() for s in (False,True)]
    assert fixture['source_opponent_action_sha256'] in action_hashes and len(tape)==719
    module=load_agent(CANDIDATE)
    try:
        for step in range(714):
            obs=copy.deepcopy(dict(state[seat].observation,remainingOverageTime=60.0))
            action=module.agent(obs,cfg)
            if step==713:
                player=int(obs['player']);farm=obs['farms'][player]
                positions=farm.get('hands',[]);hand_actions=action.get('hands',[])
                inventories=obs.get('private',{}).get('inventories',[])
                quote=int(obs.get('market',{}).get('prices',{}).get('MELON',0))
                matches=[]
                for i,pos in enumerate(positions):
                    if i>=len(hand_actions) or i+1>=len(inventories) or list(pos)!=[1,4]: continue
                    inventory=inventories[i+1]
                    if not isinstance(inventory,dict) or hand_actions[i]!=['WATER'] or int(inventory.get('MELON',0))<12: continue
                    x,y=map(int,pos)
                    distance=min(abs(x-sx)+abs(y-sy) for sx,sy in ACCESS)
                    if distance<=3: matches.append({'hand_index':i,'inventory':inventory,'distance':distance})
                shed=obs.get('private',{}).get('shed',{})
                shed_units=sum(int(v) for v in shed.values()) if isinstance(shed,dict) else None
                matched_units=sum(int(v) for v in matches[0]['inventory'].values()) if len(matches)==1 else None
                capacity=int(cfg.get('shedCapacity',-1))
                max_orders=int(cfg.get('maxMarketOrdersPerTurn',-1))
                qualifies=(len(matches)==1 and quote>=100 and cfg.get('boardSize')==10 and
                           shed_units is not None and capacity>=shed_units+matched_units and max_orders>=1)
                return dict(fixture_id=fixture_id,panel=panel_name,candidate_seat=seat,step=step,player=player,
                    quote=quote,board_size=cfg.get('boardSize'),shed_capacity=capacity,shed_units=shed_units,
                    max_market_orders_per_turn=max_orders,base_action=action,matching_hands=matches,
                    selector_qualified=bool(qualifies),action_order_count=len(action.get('market',[])))
            state[seat].action=action
            state[1-seat].action=copy.deepcopy(tape[step])
            core.interpreter(state,env)
            for item in state:item.observation.step=step+1
        raise AssertionError('step 713 not captured')
    finally:
        del module,state,replay
        gc.collect()


def main():
    assert sha(CANDIDATE)==CANDIDATE_SHA
    assert sha(PANEL)==PANEL_SHA
    panel=json.loads(PANEL.read_text(encoding='utf-8'))
    jobs=[(r['fixture'],r['fixture_id'],int(r['candidate_seat']),r['panel']) for r in panel['games']]
    jobs.extend((r['fixture'],r['fixture_id'],int(r['seat']),'public_win_control') for r in panel['controls'])
    assert len(jobs)==102 and len({(x[1],x[2]) for x in jobs})==102
    rows=[]
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        with exclusive_run(HERE/'selector_census.lock'):
            for n,(fixture,fid,seat,panel_name) in enumerate(jobs,1):
                row=inspect_job(fixture,fid,seat,panel_name);rows.append(row)
                print(json.dumps({'completed':n,'planned':len(jobs),'fixture':fid,'seat':seat,
                    'qualified':row['selector_qualified'],'price':row['quote']},ensure_ascii=True),flush=True)
            active=[(r['fixture_id'],r['candidate_seat']) for r in rows if r['selector_qualified']]
            targets={( 'live-114271958',0),('live-114271958',1),
                     ('top20-08-Unknown Mother-Goose-114272024',0),
                     ('top20-08-Unknown Mother-Goose-114272024',1)}
            receipt=dict(schema='257f-incumbent-melon-trigger-census-v1',candidate_sha256=CANDIDATE_SHA,
                panel_sha256=PANEL_SHA,baseline_only=True,no_intervention=True,no_outcomes=True,
                complete=len(rows)==102,activation_rows=[{'fixture_id':a,'seat':b} for a,b in active],
                exactly_expected_activations=set(active)==targets,rows=rows)
            with OUT.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=True,indent=2)
            print(json.dumps({k:v for k,v in receipt.items() if k!='rows'},indent=2),flush=True)
            if not receipt['exactly_expected_activations']:raise SystemExit('Unexpected trigger incidence; stop before intervention outcomes.')

if __name__=='__main__':main()
