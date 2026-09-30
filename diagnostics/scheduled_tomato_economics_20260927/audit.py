from collections import defaultdict,deque
from datetime import datetime,timezone
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.market_oracle_diagnostic_20260927.audit import apply_units
from kaggle_environments.envs.kaggriculture import kaggriculture as engine


def delivery(rows,seat,harvest,item):
    start=harvest['step'];actor=harvest['actor']
    for step in range(start+1,min((start//24+1)*24,719)):
        row=rows[step];f=row['observation']['farms'][seat]
        pos=f['farmer'] if actor==0 else f['hands'][actor-1]
        a=row['action'];cmd=a.get('farmer',['PASS']) if actor==0 else a.get('hands',[])[actor-1]
        if tuple(pos) in ((4,4),(5,4),(4,5),(5,5)):
            if cmd[0]=='DROP' or cmd[0]=='PLACE' and len(cmd)>1 and cmd[1]==item:
                return step,'daytime'
    return (start//24+1)*24,'midnight'


def audit(record,oldplots,newplots,cfg):
    raw=gzip.decompress(Path(record['trace_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==record['trace_sha256']
    trace=json.loads(raw);seat=record['candidate_seat'];rows=trace['traces'][seat]
    sources={p['step']:p for p in oldplots}
    deliveries=defaultdict(lambda:defaultdict(int));credits=defaultdict(int);delivery_rows=[]
    for plot in newplots:
        if plot['tomato_shops']<2:continue
        assert plot['feasible'] and plot['tomato_harvest']==4 and plot['strawberry_harvest']==8
        old=sources[plot['step']]
        credits[plot['step']]+=50
        for item,harvests in (('TOMATO',plot['harvests']),('STRAWBERRY',old['strawberry']['harvests'])):
            for h in harvests:
                step,kind=delivery(rows,seat,h,item)
                deliveries[step][item]+=h['units']
                delivery_rows.append(dict(item=item,harvest_step=h['step'],delivery_step=step,
                                          actor=h['actor'],units=h['units'],kind=kind))
    original_price=engine.market_price;original_commit=engine._commit_unit;original_refresh=engine._refresh_prices
    quote_queue=deque();group_id=0;quotes=[];farm_ids={}

    def price(item,inventory,params=None):
        nonlocal group_id
        if not quote_queue:group_id+=1
        value=original_price(item,inventory,params)
        quote_queue.append((group_id,item,inventory,value))
        return value

    def commit(op,item,value,farm,private,market,shed_capacity=100):
        entry=None
        if op in ('SELL','BUY_PRODUCT'):
            gid,qitem,inventory,qvalue=quote_queue.popleft()
            assert item==qitem and value==qvalue
            entry=dict(group=gid,player=farm_ids[id(farm)],op=op,item=item,quote_inventory=inventory,
                       quote=value,shed_before=private['shed'].get(item,0))
        success=original_commit(op,item,value,farm,private,market,shed_capacity)
        if entry is not None:
            entry['success']=success;quotes.append(entry)
        return success

    delta_inventory=defaultdict(int);cash_delta=[0.,0.];lost_stock=0;waiting_tom=0
    canceled=0;sold=0;delayed=[];min_cash=[float('inf'),float('inf')]
    item_changes=[defaultdict(float),defaultdict(float)];capacity_assumptions=[]
    try:
        engine.market_price=price;engine._commit_unit=commit
        engine._refresh_prices=lambda market:None
        for step in range(719):
            ts=[trace['traces'][p][step] for p in (0,1)]
            farms=copy.deepcopy(ts[0]['observation']['farms'])
            privates=[copy.deepcopy(t['observation']['private']) for t in ts]
            actions=[t['action'] for t in ts]
            apply_units(farms,privates,actions,step,cfg)
            mk=copy.deepcopy(ts[0]['observation']['market'])
            initial_shed_total=sum(privates[seat]['shed'].values())
            orders=[a.get('market',[]) for a in actions]
            quote_queue.clear();quotes.clear();group_id=0
            farm_ids={id(farms[p]):p for p in (0,1)}
            states=[SimpleNamespace(action=actions[p],observation=SimpleNamespace(farms=farms,private=privates[p],market=mk)) for p in (0,1)]
            engine._process_market(states,SimpleNamespace(configuration=cfg))
            assert not quote_queue
            expected=[trace['traces'][p][step+1]['observation']['farms'][p]['money'] if step<718
                      else trace['candidate_reward'] if p==seat else trace['opponent_reward'] for p in (0,1)]
            assert [f['money'] for f in farms]==expected,(record['episode_id'],step)
            cash_delta[seat]+=credits.get(step,0)
            incoming=deliveries.get(step,{})
            lost_stock+=incoming.get('STRAWBERRY',0)
            waiting_tom+=incoming.get('TOMATO',0)
            if incoming.get('TOMATO',0) and initial_shed_total+waiting_tom>int(cfg.get('shedCapacity',100)):
                capacity_assumptions.append(dict(step=step,factual_shed=initial_shed_total,extra_tom=waiting_tom))
            groups=defaultdict(list)
            for q in quotes:groups[q['group']].append(q)
            for units in groups.values():
                before=dict(delta_inventory);inventory_changes=defaultdict(int)
                for q in units:
                    if not q['success']:continue
                    p=q['player'];item=q['item'];op=q['op']
                    if p==seat and item=='STRAWBERRY' and op=='SELL' and q['shed_before']<=lost_stock:
                        assert lost_stock>0
                        lost_stock-=1;canceled+=1
                        change=-q['quote'];inventory_changes[item]-=1
                    else:
                        new_price=original_price(item,q['quote_inventory']+before.get(item,0),mk.get('params'))
                        change=(new_price-q['quote'])*(1 if op=='SELL' else -1)
                    cash_delta[p]+=change;item_changes[p][item]+=change
                for item,n in inventory_changes.items():delta_inventory[item]+=n
            if waiting_tom:
                if len(orders[seat])>=int(cfg.get('maxMarketOrdersPerTurn',10)):
                    delayed.append(dict(step=step,units=waiting_tom))
                else:
                    for _ in range(waiting_tom):
                        value=original_price('TOMATO',mk['inventory']['TOMATO']+delta_inventory['TOMATO'],mk.get('params'))
                        cash_delta[seat]+=value;item_changes[seat]['TOMATO']+=value
                        delta_inventory['TOMATO']+=1;sold+=1
                    waiting_tom=0
            for p in (0,1):min_cash[p]=min(min_cash[p],expected[p]+cash_delta[p])
    finally:
        engine.market_price=original_price;engine._commit_unit=original_commit;engine._refresh_prices=original_refresh
    relative=cash_delta[seat]-cash_delta[1-seat]
    return dict(episode_id=record['episode_id'],opponent=record['opponent'],source_trace_sha256=record['trace_sha256'],
                native_market_cash_parity_turns=719,factual_margin=record['margin'],
                own_cash_change=cash_delta[seat],rival_cash_change=cash_delta[1-seat],relative_change=relative,
                modeled_margin=record['margin']+relative,seed_credit=sum(credits.values()),
                item_changes_ours=dict(item_changes[seat]),item_changes_rival=dict(item_changes[1-seat]),
                added_tomato_sales=sold,canceled_strawberry_sales=canceled,residual_lost_strawberry_stock=lost_stock,
                unsold_tomatoes=waiting_tom,minimum_modeled_cash_ours=min_cash[seat],minimum_modeled_cash_rival=min_cash[1-seat],
                order_slot_delays=delayed,capacity_assumptions=capacity_assumptions,assumed_deliveries=delivery_rows,
                realized_game=False,independent_strength_evidence=False)


if __name__=='__main__':
    target=HERE/'audit.json';assert not target.exists()
    old=json.loads((ROOT/'diagnostics/scheduled_crop_substitution_20260927/audit.json').read_text())
    new=json.loads((ROOT/'diagnostics/scheduled_tomato_harvest_20260927/audit.json').read_text())
    ledgers=json.loads((ROOT/'diagnostics/disjoint_live_top100_cash_20260927/ledger.json').read_text())
    live=json.loads((ROOT/'diagnostics/disjoint_live_audit_20260927/cohort_1137.json').read_text())
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),complete=False,
             plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(),
             engine_sha256=hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest(),
             idealized_fixed_trade_diagnostic=True,saved_fertilizer_value_omitted=True,games=[])
    for game in new['games']:
        if not any(p['tomato_shops']>=2 for p in game['plots']):continue
        record=next(r for r in ledgers['games'] if r['episode_id']==game['episode_id'])
        before=next(r for r in old['games'] if r['episode_id']==game['episode_id'])
        source=next(r for r in live['games'] if r['episode_id']==game['episode_id'])
        cfg=json.loads(gzip.decompress(Path(source['replay_path']).read_bytes()))['configuration']
        result=audit(record,before['plots'],game['plots'],cfg);out['games'].append(result)
        target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
        print(result['opponent'],'own',result['own_cash_change'],'rival',result['rival_cash_change'],
              'relative',result['relative_change'],'modeled margin',result['modeled_margin'],flush=True)
    assert len(out['games'])==2
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),
               passed=all(g['minimum_modeled_cash_ours']>=0 and g['minimum_modeled_cash_rival']>=0 and
                          (g['relative_change']>0 if g['factual_margin']<0 else g['modeled_margin']>0) for g in out['games']))
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
