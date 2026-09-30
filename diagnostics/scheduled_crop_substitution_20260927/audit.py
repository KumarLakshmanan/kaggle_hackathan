from datetime import datetime, timezone
import copy
import gzip
import hashlib
import json
from pathlib import Path
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def commands(row,seat):
    farm=row['observation']['farms'][seat]
    yield 0, farm['farmer'], row['action'].get('farmer',['PASS'])
    actions=row['action'].get('hands',[])
    for i,pos in enumerate(farm['hands']):
        yield i+1,pos,actions[i] if i<len(actions) else ['PASS']


def replay(rows,seat,start,pos,crop,check=False):
    x,y=pos
    farm=engine._new_farm(10,1000000)
    farm['tiles']=[['LOCKED']*10 for _ in range(10)]
    farm['tiles'][y][x]=None
    farm['farmer']=list(pos)
    private=engine._new_private()
    private['seeds'][crop]=1
    harvests=[];fert=0;death=None;last=start
    for step in range(start,719):
        row=rows[step]
        actual=row['observation']['farms'][seat]['tiles'][y][x]
        if check:
            assert farm['tiles'][y][x]==actual,(start,step,pos,farm['tiles'][y][x],actual)
        local=[(a,c) for a,p,c in commands(row,seat) if tuple(p)==tuple(pos)]
        if step>start and any(c[0] in ('DIG','PLANT','BUILD_COOP','BUILD_PASTURE') for a,c in local):
            break
        for actor,command in local:
            if command[0] not in ('PLANT','WATER','FERTILIZE','HARVEST'):
                continue
            inv=row['observation']['private']['inventories'][actor]
            private['inventories'][0]={'FERTILIZER':inv.get('FERTILIZER',0)}
            if step==start and command[0]=='PLANT':
                command=['PLANT',crop]
            before=private['inventories'][0].get('FERTILIZER',0)
            engine._apply_unit_action(farm,private,0,command,10,step//24,24,100)
            after=private['inventories'][0]
            fert+=before-after.get('FERTILIZER',0)
            units=after.get(crop,0)
            if units:
                harvests.append(dict(step=step,actor=actor,units=units,
                                     factual_quote=row['observation']['market']['prices'][crop]))
        engine._decay_plants(farm,step)
        if (step+1)%24==0:
            engine._daily_refresh_plants(farm,step//24,24)
        if death is None and isinstance(farm['tiles'][y][x],dict) and farm['tiles'][y][x].get('kind')=='WEED':
            death=step+1
        last=step
    return dict(crop=crop,total_harvest=sum(h['units'] for h in harvests),harvests=harvests,
                factual_quote_value=sum(h['units']*h['factual_quote'] for h in harvests),
                fertilizer_used=fert,weed_observed_step=death,last_step=last,baseline_parity=check)


def audit(record):
    raw=gzip.decompress(Path(record['trace_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==record['trace_sha256']
    trace=json.loads(raw);seat=record['candidate_seat'];rows=trace['traces'][seat]
    plots=[]
    for step in range(12*24,18*24):
        row=rows[step]
        for actor,pos,cmd in commands(row,seat):
            if cmd[:2]!=['PLANT','STRAWBERRY']:
                continue
            x,y=pos
            before=row['observation']['farms'][seat]['tiles'][y][x]
            after=rows[step+1]['observation']['farms'][seat]['tiles'][y][x]
            if before is not None or not isinstance(after,dict) or after.get('crop')!='STRAWBERRY' or after['planted_day']!=step//24:
                continue
            old=replay(rows,seat,step,pos,'STRAWBERRY',True)
            new=replay(rows,seat,step,pos,'TOMATO',False)
            shops=row['observation']['town']['unlocked_shops']
            plots.append(dict(step=step,day=step//24+1,position=pos,shops=shops,
                              tomato_shops=sum(s in ('FARMERS_MARKET','PIZZA_SHOP') for s in shops),
                              strawberry=old,tomato=new))
    return dict(episode_id=record['episode_id'],opponent=record['opponent'],trace_sha256=record['trace_sha256'],plots=plots)


if __name__=='__main__':
    target=HERE/'audit.json';assert not target.exists()
    out=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),independent_strength_evidence=False,
             plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(),
             engine_sha256=hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest(),games=[])
    for folder in ('disjoint_live_top100_cash_20260927','disjoint_live_cash_1022_20260927'):
        ledger=json.loads((ROOT/'diagnostics'/folder/'ledger.json').read_text());assert ledger['complete']
        for record in ledger['games']:
            result=audit(record);out['games'].append(result)
            eligible=[p for p in result['plots'] if p['tomato_shops']>=2 and p['tomato']['total_harvest']>=4]
            print(result['opponent'],'plots',len(result['plots']),'mechanically eligible',len(eligible),
                  'harvest old/new',sum(p['strawberry']['total_harvest'] for p in eligible),sum(p['tomato']['total_harvest'] for p in eligible),flush=True)
            target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat())
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
