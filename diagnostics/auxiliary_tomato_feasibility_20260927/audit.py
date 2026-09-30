from collections import Counter
from datetime import datetime, timezone
import copy
import gzip
import hashlib
import json
from pathlib import Path

from kaggle_environments.envs.kaggriculture import kaggriculture as engine

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PLOTS=[[(5,5),(6,5),(7,5),(7,6),(6,6),(5,6)],
       [(5,7),(6,7),(7,7),(7,8),(6,8),(5,8)]]


def unit_action(farm,actor,targets,index):
    pos=farm['hands'][actor-1]
    while index<len(targets):
        x,y=targets[index]
        if pos[0]!=x:return ['EAST' if pos[0]<x else 'WEST'],index
        if pos[1]!=y:return ['SOUTH' if pos[1]<y else 'NORTH'],index
        tile=farm['tiles'][y][x]
        if tile is None:return ['PLANT','TOMATO'],index
        if not isinstance(tile,dict) or tile.get('crop')!='TOMATO':
            raise AssertionError(('unexpected target tile',actor,x,y,tile))
        if tile['yield_units']>0:return ['HARVEST'],index
        if not tile['watered_today']:return ['WATER'],index
        index+=1
    return ['PASS'],index


def mechanical():
    farm=engine._new_farm(10,1000000)
    for _ in range(3):engine._do_buy_land(farm,10)
    private=engine._new_private();private['seeds']['TOMATO']=12
    rows=[];harvested=0
    for day in range(12):
        farm['hands']=[[4,4],[4,4]];private['inventories']=[{},{},{}]
        indices=[0,0];counts=[Counter(),Counter()]
        for hour in range(3,24):
            for worker in range(2):
                action,indices[worker]=unit_action(farm,worker+1,PLOTS[worker],indices[worker])
                before=private['inventories'][worker+1].get('TOMATO',0)
                engine._apply_unit_action(farm,private,worker+1,action,10,day,24,100)
                harvested+=private['inventories'][worker+1].get('TOMATO',0)-before
                counts[worker][action[0]]+=1
            engine._decay_plants(farm,day*24+hour)
        watered=sum(farm['tiles'][y][x].get('watered_today',False) for block in PLOTS for x,y in block)
        assert watered==12,(day,watered)
        engine._drop_inventories_to_shed(private,100)
        engine._daily_refresh_plants(farm,day,24)
        rows.append(dict(day=day,watered=watered,cumulative_harvest=harvested,
                         workers=[dict(c) for c in counts]))
    assert private['seeds']['TOMATO']==0 and harvested==48 and private['shed']['TOMATO']==48
    return dict(synthetic=True,full_game=False,plots=PLOTS,harvested=harvested,shed_units=private['shed']['TOMATO'],
                all_watered=True,all_planted=True,days=rows)


def finances(record):
    raw=gzip.decompress(Path(record['trace_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==record['trace_sha256']
    t=json.loads(raw);seat=record['candidate_seat'];rows=t['traces'][seat]
    daily=[]
    for day in range(30):
        subset=rows[day*24:min((day+1)*24,719)]
        hires=[r['step']%24 for r in subset if any(o and o[0]=='HIRE' for o in r['action'].get('market',[]))]
        n=max(len(r['observation']['farms'][seat]['hands']) for r in subset)
        daily.append(dict(day=day+1,hands=n,last_hire_hour=max(hires,default=-1),
                          extra_hire_cost=engine._hire_cost(n)+engine._hire_cost(n+1)))
    candidates=[]
    for start in range(12,18):
        step=start*24+2;o=rows[step]['observation'];farm=o['farms'][seat]
        shops=o['town']['unlocked_shops'];days=daily[start:start+12]
        paid=4600;minimum=float('inf');minimum_step=None
        for future in range(step,min((start+12)*24,719)):
            if future%24==2:paid+=daily[future//24]['extra_hire_cost']
            # The observation is before this turn's action: this subtracts the
            # extra payment immediately, a conservative phase for the stress check.
            remaining=rows[future]['observation']['farms'][seat]['money']-paid
            if remaining<minimum:minimum=remaining;minimum_step=future
        headroom=[]
        for production_age in range(8,12):
            next_day=start+production_age+1
            obs=rows[next_day*24]['observation']
            headroom.append(100-sum(obs['private']['shed'].values()))
        candidates.append(dict(start_day=start+1,observation_step=step,cash=farm['money'],
                               tomato_shops=sum(s in ('PIZZA_SHOP','FARMERS_MARKET') for s in shops),
                               total_shops=len(shops),land=farm['unlocked_quadrants'],
                               entire_extra_wages=sum(d['extra_hire_cost'] for d in days),
                               total_extra_cost=4600+sum(d['extra_hire_cost'] for d in days),
                               all_regular_hires_by_hour1=all(d['last_hire_hour']<=1 for d in days),
                               cash_stress_minimum=minimum,cash_stress_minimum_step=minimum_step,
                               reserve_2000_survives=minimum>=2000,recorded_harvest_midnight_headroom=headroom,
                               all_harvest_midnights_have_12_capacity=min(headroom)>=12))
    qualifying=[r for r in candidates if r['tomato_shops']>=2 and r['land']==['NW','NE','SW']
                and r['all_regular_hires_by_hour1'] and r['reserve_2000_survives'] and r['all_harvest_midnights_have_12_capacity']]
    return dict(episode_id=record['episode_id'],opponent=record['opponent'],trace_sha256=record['trace_sha256'],
                starts=candidates,first_factual_feasible_start=qualifying[0]['start_day'] if qualifying else None,
                daily_hire_schedule=daily,policy_eligibility=False)


if __name__=='__main__':
    target=HERE/'audit.json';assert not target.exists()
    out=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
             engine_sha256=hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest(),
             plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(),
             independent_strength_evidence=False,mechanical=mechanical(),games=[])
    print('Native mechanical yield',out['mechanical']['harvested'],'all plots watered daily',flush=True)
    for folder in ('disjoint_live_top100_cash_20260927','disjoint_live_cash_1022_20260927'):
        ledger=json.loads((ROOT/'diagnostics'/folder/'ledger.json').read_text());assert ledger['complete']
        for record in ledger['games']:
            row=finances(record);out['games'].append(row)
            print(row['opponent'],row['episode_id'],'first feasible recorded start',row['first_factual_feasible_start'],flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat())
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
