from collections import Counter
from pathlib import Path
import copy
import gzip
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import sha


def analyze(meta):
    assert sha(meta['trace_path'])==meta['trace_sha256']
    with gzip.open(meta['trace_path'],'rt',encoding='utf-8') as source:
        rows=[json.loads(line) for line in source]
    assert len(rows)==719
    seat=meta['candidate_seat']
    noops=Counter();changed=Counter();plant_failures=[];land=[];daily=[];animal_escapes=[]
    for row in rows:
        step=row['step'];obs=row['observation'];action=row['action']
        farm=copy.deepcopy(obs['farms'][seat]);private=copy.deepcopy(obs['private'])
        requested=[action.get('farmer',['PASS']),*action.get('hands',[])]
        demand=Counter(u[1] for u in requested if len(u)>=2 and u[0]=='PLANT')
        blocked={crop for crop,n in demand.items() if n>private['seeds'].get(crop,0)}
        for index,unit in enumerate(requested):
            if not unit or unit[0]=='PASS' or index>len(farm['hands']):continue
            pos=copy.deepcopy(farm['farmer'] if index==0 else farm['hands'][index-1])
            tile=copy.deepcopy(farm['tiles'][pos[1]][pos[0]])
            before=copy.deepcopy((farm,private))
            actual=['PASS'] if len(unit)>=2 and unit[0]=='PLANT' and unit[1] in blocked else unit
            core._apply_unit_action(farm,private,index,actual,10,step//24,24,100)
            if before!=(farm,private):changed[unit[0]]+=1;continue
            kind=tile.get('kind') if isinstance(tile,dict) else 'EMPTY'
            reason=('atomic_seed_shortage' if actual!=unit else 'locked_tile'
                    if core._quadrant_of(*pos,10) not in farm['unlocked_quadrants'] else str(kind))
            noops[unit[0]+':'+reason]+=1
            if unit[0]=='PLANT':plant_failures.append(dict(step=step,worker=index,pos=pos,command=unit,reason=reason))
        if any(order and order[0]=='BUY_LAND' for order in action.get('market',[])):
            next_land=(rows[step+1]['observation']['farms'][seat]['unlocked_quadrants'] if step<718 else None)
            land.append(dict(step=step,money_before=obs['farms'][seat]['money'],
                before=obs['farms'][seat]['unlocked_quadrants'],after=next_land))
        if step%24==0:
            own=obs['farms'][seat];rival=obs['farms'][1-seat]
            counts=Counter(tile.get('animal',tile.get('crop',tile.get('kind'))) for rr in own['tiles'] for tile in rr if isinstance(tile,dict))
            daily.append(dict(day=step//24,own=own['money'],rival=rival['money'],land=own['unlocked_quadrants'],counts=dict(counts),shops=obs['town']['unlocked_shops']))
            if step:
                prior=rows[step-1]['observation']['farms'][seat]
                for y,tiles in enumerate(prior['tiles']):
                    for x,tile in enumerate(tiles):
                        after=own['tiles'][y][x]
                        if isinstance(tile,dict) and tile.get('animal') and (not isinstance(after,dict) or not after.get('animal')):
                            animal_escapes.append(dict(day=step//24,x=x,y=y,animal=tile['animal']))
    return dict(version=meta['version'],seat=seat,own=meta['candidate_reward'],rival=meta['opponent_reward'],margin=meta['margin'],
        nochange_counts=dict(noops),changed_counts=dict(changed),plant_failures=plant_failures,
        land_orders=land,daily=daily,animal_disappearances_at_midnight=animal_escapes)


def main():
    traces=json.loads((HERE/'mhw_traces.json').read_text(encoding='utf-8'))
    assert traces['complete'] and all(r['native_terminal_parity'] for r in traces['games'])
    games=[analyze(row) for row in traces['games']]
    result=dict(complete=True,diagnostic_only=True,games=games)
    (HERE/'mhw_analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    for row in games:
        print(json.dumps({k:v for k,v in row.items() if k!='daily'},ensure_ascii=False))
    for seat in (0,1):
        old=next(r for r in games if r['version']=='old' and r['seat']==seat)
        new=next(r for r in games if r['version']=='new' and r['seat']==seat)
        print('paired mechanism',seat,dict(delta_own=new['own']-old['own'],delta_rival=new['rival']-old['rival'],
            delta_margin=new['margin']-old['margin'],first_shop_path_difference=next((n['day'] for o,n in zip(old['daily'],new['daily']) if o['shops']!=n['shops']),None)))


if __name__=='__main__':main()
