from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.scheduled_crop_substitution_20260927.audit import commands
from kaggle_environments.envs.kaggriculture import kaggriculture as engine


def simulate(rows,seat,plot):
    start=plot['step'];pos=plot['position'];x,y=pos
    farm=engine._new_farm(10,1000000)
    farm['tiles']=[['LOCKED']*10 for _ in range(10)]
    farm['tiles'][y][x]=None;farm['farmer']=list(pos)
    private=engine._new_private();private['seeds']['TOMATO']=1
    harvests=[];changes=[];fert=0;death=None
    for step in range(start,719):
        row=rows[step];age=step//24-start//24
        local=[(actor,cmd) for actor,p,cmd in commands(row,seat) if p==pos]
        if step>start and any(c[0] in ('DIG','PLANT','BUILD_COOP','BUILD_PASTURE') for actor,c in local):
            break
        for actor,command in local:
            if command[0] not in ('PLANT','WATER','FERTILIZE','HARVEST'):
                continue
            inv=row['observation']['private']['inventories'][actor]
            private['inventories'][0]={'FERTILIZER':inv.get('FERTILIZER',0)}
            tile=farm['tiles'][y][x]
            if step==start and command[0]=='PLANT':
                command=['PLANT','TOMATO']
            elif isinstance(tile,dict) and tile.get('crop')=='TOMATO' and tile.get('yield_units',0)>0:
                if command[0]=='FERTILIZE' and 8<=age<=10 or command[0]=='WATER' and age==11:
                    changes.append(dict(step=step,age=age,actor=actor,old=command,new=['HARVEST']))
                    command=['HARVEST']
            before=private['inventories'][0].get('FERTILIZER',0)
            engine._apply_unit_action(farm,private,0,command,10,step//24,24,100)
            after=private['inventories'][0]
            fert+=before-after.get('FERTILIZER',0)
            if after.get('TOMATO',0):
                harvests.append(dict(step=step,age=age,actor=actor,units=after['TOMATO']))
        engine._decay_plants(farm,step)
        if (step+1)%24==0:
            engine._daily_refresh_plants(farm,step//24,24)
        if death is None and isinstance(farm['tiles'][y][x],dict) and farm['tiles'][y][x].get('kind')=='WEED':
            death=step+1
    total=sum(h['units'] for h in harvests)
    return dict(step=start,position=pos,tomato_shops=plot['tomato_shops'],
                strawberry_harvest=plot['strawberry']['total_harvest'],tomato_harvest=total,
                harvests=harvests,changes=changes,fertilizer_used=fert,weed_observed_step=death,
                feasible=total>=4 and max((h['age'] for h in harvests),default=100)<=11)


if __name__=='__main__':
    target=HERE/'audit.json';assert not target.exists()
    previous=ROOT/'diagnostics/scheduled_crop_substitution_20260927/audit.json'
    old=json.loads(previous.read_text());assert old['complete']
    traces={g['episode_id']:g for folder in ('disjoint_live_top100_cash_20260927','disjoint_live_cash_1022_20260927')
            for g in json.loads((ROOT/'diagnostics'/folder/'ledger.json').read_text())['games']}
    out=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),independent_strength_evidence=False,
             plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(),
             prior_audit_sha256=hashlib.sha256(previous.read_bytes()).hexdigest(),games=[])
    for game in old['games']:
        rec=traces[game['episode_id']];raw=gzip.decompress(Path(rec['trace_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==rec['trace_sha256']==game['trace_sha256']
        trace=json.loads(raw);seat=rec['candidate_seat'];rows=trace['traces'][seat]
        results=[simulate(rows,seat,p) for p in game['plots']]
        eligible=[p for p in results if p['tomato_shops']>=2]
        out['games'].append(dict(episode_id=game['episode_id'],opponent=game['opponent'],plots=results))
        print(game['opponent'],'allplots',len(results),'demand eligible',len(eligible),
              'fullyield',sum(p['feasible'] for p in eligible),flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat())
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
