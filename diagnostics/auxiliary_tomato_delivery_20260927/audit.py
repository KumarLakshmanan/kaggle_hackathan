from datetime import datetime, timezone
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

from kaggle_environments.envs.kaggriculture import kaggriculture as engine

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.auxiliary_tomato_feasibility_20260927.audit import PLOTS
from diagnostics.market_oracle_diagnostic_20260927.audit import apply_units


def choose(farm,private,actor,targets,index,age):
    pos=farm['hands'][actor-1]
    harvest_day=age in (9,11)
    while index<len(targets):
        x,y=targets[index]
        if pos[0]!=x:return ['EAST' if pos[0]<x else 'WEST'],index
        if pos[1]!=y:return ['SOUTH' if pos[1]<y else 'NORTH'],index
        tile=farm['tiles'][y][x]
        if tile is None:
            assert age==0
            return ['PLANT','TOMATO'],index
        assert isinstance(tile,dict) and tile.get('crop')=='TOMATO'
        if harvest_day and tile['yield_units']>0:return ['HARVEST'],index
        if not harvest_day and not tile['watered_today']:return ['WATER'],index
        index+=1
    if harvest_day and sum(private['inventories'][actor].values()):
        if pos[0]!=5:return ['EAST' if pos[0]<5 else 'WEST'],index
        if pos[1]!=5:return ['SOUTH' if pos[1]<5 else 'NORTH'],index
        return ['DROP'],index
    return ['PASS'],index


def mechanical():
    farm=engine._new_farm(10,1000000)
    for _ in range(3):engine._do_buy_land(farm,10)
    private=engine._new_private();private['seeds']['TOMATO']=12
    rows=[];delivered=0;drop_hours={}
    for age in range(12):
        farm['hands']=[[4,4],[4,4]];private['inventories']=[{},{},{}]
        indices=[0,0];drops=[]
        for hour in range(3,24):
            for worker in (0,1):
                action,indices[worker]=choose(farm,private,worker+1,PLOTS[worker],indices[worker],age)
                before=private['shed']['TOMATO']
                engine._apply_unit_action(farm,private,worker+1,action,10,age,24,100)
                qty=private['shed']['TOMATO']-before
                if qty:
                    delivered+=qty;drops.append(dict(worker=worker,hour=hour,units=qty))
            engine._decay_plants(farm,age*24+hour)
        assert sum(sum(inv.values()) for inv in private['inventories'])==0,(age,'undelivered cargo')
        watered=sum(farm['tiles'][y][x]['watered_today'] for block in PLOTS for x,y in block)
        assert watered==(0 if age in (9,11) else 12)
        engine._daily_refresh_plants(farm,age,24)
        assert all(farm['tiles'][y][x].get('crop')=='TOMATO' for block in PLOTS for x,y in block)
        rows.append(dict(age=age,watered=watered,drops=drops,cumulative_delivered=delivered))
        if drops:drop_hours[str(age)]=[d['hour'] for d in drops]
    assert delivered==48 and private['shed']['TOMATO']==48
    return dict(synthetic=True,full_game=False,delivered=delivered,drop_hours=drop_hours,days=rows)


if __name__=='__main__':
    target=HERE/'audit.json';assert not target.exists()
    prior=json.loads((ROOT/'diagnostics/auxiliary_tomato_feasibility_20260927/audit.json').read_text())
    source_rows={g['episode_id']:g for folder in ('disjoint_live_top100_cash_20260927','disjoint_live_cash_1022_20260927')
                 for g in json.loads((ROOT/'diagnostics'/folder/'ledger.json').read_text())['games']}
    mechanical_result=mechanical()
    print('Mechanical delivery',mechanical_result['delivered'],mechanical_result['drop_hours'],flush=True)
    out=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),independent_strength_evidence=False,
             plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(),mechanical=mechanical_result,games=[])
    for g in prior['games']:
        source=source_rows[g['episode_id']]
        raw=gzip.decompress(Path(source['trace_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==source['trace_sha256']
        t=json.loads(raw);seat=source['candidate_seat'];starts=[]
        for original in g['starts']:
            record=copy.deepcopy(original);start=record['start_day']-1;slots=[]
            for age,hours in mechanical_result['drop_hours'].items():
                for worker,arrival in enumerate(hours):
                    options=[]
                    for hour in range(arrival,24):
                        step=(start+int(age))*24+hour
                        ts=[t['traces'][p][step] for p in (0,1)]
                        farms=copy.deepcopy(ts[0]['observation']['farms'])
                        privates=[copy.deepcopy(r['observation']['private']) for r in ts]
                        actions=[r['action'] for r in ts]
                        apply_units(farms,privates,actions,step,{})
                        room=100-sum(privates[seat]['shed'].values())
                        orders=len(actions[seat].get('market',[]))
                        if room>=12 and orders<10:
                            options.append(dict(step=step,hour=hour,room=room,baseline_market_orders=orders))
                    slots.append(dict(age=int(age),worker=worker,conservative_arrival=arrival,available_slots=options))
            record['daytime_delivery_slots']=slots
            record['all_four_deliveries_fit']=all(r['available_slots'] for r in slots)
            record['feasible_factual_design']=(record['tomato_shops']>=2 and record['land']==['NW','NE','SW']
                                               and record['all_regular_hires_by_hour1'] and record['reserve_2000_survives']
                                               and record['all_four_deliveries_fit'])
            starts.append(record)
        good=[r['start_day'] for r in starts if r['feasible_factual_design']]
        out['games'].append(dict(episode_id=g['episode_id'],opponent=g['opponent'],starts=starts,
                                feasible_start_days=good,policy_eligibility=False))
        print(g['opponent'],g['episode_id'],'feasible factual starts',good,flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat())
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
