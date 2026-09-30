from pathlib import Path
from collections import Counter, defaultdict
import gzip
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.v43_decem_mechanism_20260928.analyze_traces import state_at, market_totals, daily_events


def main():
    output={}
    for label in ('old','new'):
        data=json.loads(gzip.decompress((HERE/f'native_market_{label}_s2908000_p0.json.gz').read_bytes()))
        totals=market_totals(data)
        assert totals[0]['net_cash_delta']==data['candidate_reward']-3000
        assert totals[1]['net_cash_delta']==data['opponent_reward']-3000
        failures=Counter();fills=defaultdict(Counter);feed=Counter();land=[]
        for e in data['events']:
            if e.get('player')!=0:continue
            if e['phase']=='market_unit':
                if e['success']:fills[e['operation']][e['item']]+=1
                else:failures[(e['operation'],e['item'],e['failure_reason'])]+=1
            elif e['phase']=='unit_action' and e['action'] and e['action'][0]=='FEED':
                feed['changed' if e['changed'] else 'no_state_change']+=1
            elif e['phase']=='market_atomic' and e['operation']=='BUY_LAND':
                land.append({k:e[k] for k in ('step','success','cash_before','cash_after')})
        vanished=[];previous={}
        for row in data['traces'][0]:
            farm=row['observation']['farms'][0]
            animals={(x,y):t['animal'] for y,line in enumerate(farm['tiles']) for x,t in enumerate(line)
                     if isinstance(t,dict) and t.get('animal')}
            for position,animal in previous.items():
                if animals.get(position)!=animal:vanished.append({'step':row['step'],'position':position,'animal':animal})
            previous=animals
        checkpoints={str(day):state_at(data,0,min(day*24,718),0) for day in (3,6,10,18,24,29)}
        output[label]=dict(candidate_reward=data['candidate_reward'],opponent_reward=data['opponent_reward'],margin=data['margin'],
            market_totals=totals,successful_unit_fills={op:dict(counts) for op,counts in fills.items()},
            rejected_market_unit_events=[dict(operation=k[0],item=k[1],reason=k[2],count=v) for k,v in failures.items()],
            feed_action_events=dict(feed),land_orders=land,animal_disappearances=vanished,checkpoints=checkpoints,
            shops=data['traces'][0][-1]['observation']['town']['unlocked_shops'])
    (HERE/'native_failure_ledger.json').write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding='utf-8')
    for label,d in output.items():
        print(label,json.dumps({k:v for k,v in d.items() if k not in ('market_totals','checkpoints')},ensure_ascii=False))
        print('own net / sales',d['market_totals'][0])
        print('checkpoints',[(day,len(v['land']),v['cash'],v['animals'],v['crops']) for day,v in d['checkpoints'].items()])


if __name__=='__main__':main()
