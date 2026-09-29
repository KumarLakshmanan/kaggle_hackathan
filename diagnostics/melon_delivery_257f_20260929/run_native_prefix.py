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

BASELINE=ROOT/'main_candidate_pet_source_guard_20260929_257f941d.py'
BASELINE_SHA='257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'
CANDIDATE=HERE/'candidate_257f_melon_delivery.py'
CANDIDATE_SHA='a8174509cd2679578869b3090a9137d136e22a4e752c2bc9dc822b86a1aade25'
PANEL=ROOT/'diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/panel.json'
PANEL_SHA='fee3b1d5f93cd295c28dd8d0c04ea672806dbb55e2b59999853a9f969c0fb90d'
OUT=HERE/'native_prefix_receipt.json'
TARGETS={'live-114271958','top20-08-Unknown Mother-Goose-114272024'}


def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def expected_diff(step,parent_action,hand_index,max_orders,obs,cfg):
    want=copy.deepcopy(parent_action)
    if step in (713,714,715):
        want['hands'][hand_index]=['EAST']
    elif step==716:
        want['hands'][hand_index]=['DROP']
        want['market'].append(['SELL','MELON',12])
    else: raise AssertionError(step)
    return want


def action_differences(a,b):
    diffs=[]
    keys=set(a)|set(b)
    for k in sorted(keys):
        if a.get(k)!=b.get(k):diffs.append(k)
    return diffs


def new_game(fixture,seat):
    replay=load_fixture(fixture)
    cfg=dict(replay['configuration']);cfg['seed']=None
    assert cfg['episodeSteps']==720
    state=state_from_frames(replay['steps'][0])
    env=Box(configuration=Box(**cfg),info={'seed':int(fixture['seed'])},done=False)
    tape=json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    hashes=[hashlib.sha256(json.dumps(tape,sort_keys=s,separators=(',',':')).encode()).hexdigest() for s in (False,True)]
    assert fixture['source_opponent_action_sha256'] in hashes and len(tape)==719
    return dict(fixture=fixture,cfg=cfg,state=state,env=env,tape=tape,seat=seat)


def trigger_info(obs,parent_action,cfg):
    player=int(obs['player']);farm=obs['farms'][player]
    hands=farm['hands'];inv=obs['private']['inventories'];actions=parent_action['hands']
    matching=[]
    for i,pos in enumerate(hands):
        if list(pos)==[1,4] and i<len(actions) and i+1<len(inv) and actions[i]==['WATER'] and int(inv[i+1].get('MELON',0))>=12:
            x,y=map(int,pos);distance=min(abs(x-sx)+abs(y-sy) for sx,sy in ((4,4),(5,4),(4,5),(5,5)))
            if distance<=3:matching.append(i)
    shed=obs['private']['shed'];shed_units=sum(map(int,shed.values()))
    return dict(player=player,hand_matches=matching,quote=int(obs['market']['prices'].get('MELON',0)),
        board_size=cfg.get('boardSize'),shed_capacity=cfg.get('shedCapacity'),max_orders=cfg.get('maxMarketOrdersPerTurn'),
        shed_units=shed_units)


def run_fixture_pair(fixture,fixture_id,panel_name):
    games={s:new_game(fixture,s) for s in (0,1)}
    base=load_module(BASELINE,'prefix_parent_'+fixture_id.replace('-','_'))
    cand=load_module(CANDIDATE,'prefix_candidate_'+fixture_id.replace('-','_'))
    rows=[];checks=[]
    try:
        for step in range(717):
            for seat in (0,1):
                game=games[seat];state=game['state'];cfg=game['cfg']
                obs=copy.deepcopy(dict(state[seat].observation,remainingOverageTime=60.0))
                assert int(obs['step'])==step and int(obs['player'])==seat
                parent_action=base.agent(copy.deepcopy(obs),cfg)
                candidate_action=cand.agent(copy.deepcopy(obs),cfg)
                if step<713:
                    ok=candidate_action==parent_action
                    assert ok, f'pre-trigger action mismatch at {fixture_id} seat{seat} step{step}'
                elif step<=716:
                    info=trigger_info(obs,parent_action,cfg)
                    hand_index=5
                    if step==713:
                        assert info['hand_matches']==[hand_index], (fixture_id,seat,step,info)
                        assert info['quote']>=100 and info['board_size']==10
                    else:
                        assert info['board_size']==10
                    inv=obs['private']['inventories'][hand_index+1]
                    expected_position=[[1,4],[2,4],[3,4],[4,4]][step-713]
                    assert list(obs['farms'][seat]['hands'][hand_index])==expected_position
                    assert inv=={'MELON':12,'FERTILIZER':1},(fixture_id,seat,step,inv)
                    if step==713:
                        assert info['shed_capacity']>=info['shed_units']+sum(inv.values())
                        assert info['max_orders']>=1
                    if step==716:
                        orders=parent_action.get('market',[])
                        duplicate=any(isinstance(o,list) and len(o)>=2 and o[0]=='SELL' and o[1]=='MELON' for o in orders)
                        own_units=[parent_action.get('farmer',[])]+parent_action.get('hands',[])
                        competing=any(j!=hand_index+1 and isinstance(u,list) and u and u[0] in ('DROP','PLACE') for j,u in enumerate(own_units))
                        assert not duplicate and len(orders)+1<=info['max_orders'] and not competing,(fixture_id,seat,orders,competing)
                        assert info['shed_units']+sum(inv.values())<=info['shed_capacity']
                    want=expected_diff(step,parent_action,hand_index,info['max_orders'],obs,cfg)
                    assert candidate_action==want,(fixture_id,seat,step,candidate_action,parent_action,want)
                    assert cand._P257_MELON_ROUTE_STATE.get(seat,{}).get('hand_index')==hand_index if step<716 else seat not in cand._P257_MELON_ROUTE_STATE
                    rows.append(dict(fixture_id=fixture_id,panel=panel_name,seat=seat,step=step,trigger=info,
                        parent_action=parent_action,candidate_action=candidate_action))
                state[seat].action=candidate_action
                state[1-seat].action=copy.deepcopy(game['tape'][step])
                before_money=float(obs['farms'][seat]['money'])
                before_shed=copy.deepcopy(obs['private']['shed'])
                core.interpreter(state,game['env'])
                for item in state:item.observation.step=step+1
                if step==716:
                    after=copy.deepcopy(dict(state[seat].observation))
                    after_farm=after['farms'][seat]
                    after_inv=after['private']['inventories'][hand_index+1]
                    after_shed=after['private']['shed']
                    assert list(after_farm['hands'][hand_index])==[4,4]
                    assert not after_inv, (fixture_id,seat,after_inv)
                    assert after_shed.get('MELON',0)==before_shed.get('MELON',0), (fixture_id,seat,before_shed,after_shed)
                    assert float(after_farm['money'])>before_money,(fixture_id,seat,before_money,after_farm['money'])
                    assert seat not in cand._P257_MELON_ROUTE_STATE
                    assert cand.agent.telemetry.get('melon_delivery_drop_sell_step716',0)>=1
                    checks.append(dict(fixture_id=fixture_id,seat=seat,step716_drop_applied=True,
                        hand_inventory_after=after_inv,shed_before=before_shed,shed_after=after_shed,
                        money_before=before_money,money_after=after_farm['money'],
                        route_state_cleared=seat not in cand._P257_MELON_ROUTE_STATE))
            if step==0: assert not cand._P257_MELON_ROUTE_STATE
            if step==713:
                assert set(cand._P257_MELON_ROUTE_STATE)=={0,1}
            if step in (714,715):
                assert set(cand._P257_MELON_ROUTE_STATE)=={0,1}
            if step==716: assert not cand._P257_MELON_ROUTE_STATE
        errors={k:v for k,v in cand.agent.telemetry.items() if 'error' in k and v}
        assert not errors,errors
        return dict(fixture_id=fixture_id,panel=panel_name,steps_validated_through=716,interleaved_seats=True,
            candidate_sha256=CANDIDATE_SHA,baseline_sha256=BASELINE_SHA,actions=rows,post_drop_checks=checks,
            candidate_telemetry=cand.agent.telemetry,errors=errors,passed=True)
    finally:
        del base,cand,games
        gc.collect()


def main():
    assert sha(BASELINE)==BASELINE_SHA and sha(CANDIDATE)==CANDIDATE_SHA and sha(PANEL)==PANEL_SHA
    panel=json.loads(PANEL.read_text(encoding='utf-8'))
    rows=[r for r in panel['games'] if r['fixture_id'] in TARGETS]
    fixtures={r['fixture_id']:r['fixture'] for r in rows}
    assert set(fixtures)==TARGETS and all(sum(x['fixture_id']==fid for x in rows)==2 for fid in TARGETS)
    results=[]
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        with exclusive_run(HERE/'prefix_run.lock'):
            for fid in sorted(TARGETS):
                panel_name=next(r['panel'] for r in rows if r['fixture_id']==fid)
                result=run_fixture_pair(fixtures[fid],fid,panel_name);results.append(result)
                print(json.dumps({'fixture':fid,'passed':result['passed'],'seats':2,'steps':717},ensure_ascii=False),flush=True)
            receipt=dict(schema='257f-melon-native-prefix-v1',complete=len(results)==2,
                through_step=716,interleaved_seats=True,no_terminal_rewards_or_margins_read=True,
                candidate_sha256=CANDIDATE_SHA,baseline_sha256=BASELINE_SHA,plan_sha256=sha(HERE/'PLAN.md'),
                manifest_sha256=sha(HERE/'frozen_manifest.json'),passed=all(r['passed'] for r in results),fixtures=results)
            with OUT.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=True,indent=2)
            print(json.dumps({k:v for k,v in receipt.items() if k!='fixtures'},indent=2),flush=True)
            if not receipt['passed']:raise SystemExit('Native prefix gate failed; no treatment outcomes.')

if __name__=='__main__':main()
