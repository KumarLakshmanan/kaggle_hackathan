from collections import Counter
from datetime import datetime, timezone
import copy
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from kaggle_environments.envs.kaggriculture import kaggriculture as engine

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def signature(farm, private):
    return (private, farm['hands'], farm['unlocked_quadrants'], farm.get('hires_today',0))


def apply_units(farms, privates, actions, step, cfg):
    tpd=max(1,int(cfg.get('turnsPerDay',24)))
    for player,action in enumerate(actions):
        units=[action.get('farmer',['PASS']), *action.get('hands',[])]
        demand=Counter(a[1] for a in units if isinstance(a,list) and len(a)>=2 and a[0]=='PLANT')
        blocked={crop for crop,n in demand.items() if n>privates[player]['seeds'].get(crop,0)}
        for actor,unit in enumerate(units):
            if isinstance(unit,list) and len(unit)>=2 and unit[0]=='PLANT' and unit[1] in blocked:
                unit=['PASS']
            engine._apply_unit_action(farms[player],privates[player],actor,unit,
                                      int(cfg.get('boardSize',10)),step//tpd,tpd,int(cfg.get('shedCapacity',100)))


def market(farms, privates, market_state, orders, cfg):
    fs,ps,mk=copy.deepcopy(farms),copy.deepcopy(privates),copy.deepcopy(market_state)
    states=[SimpleNamespace(action={'market':orders[p]},observation=SimpleNamespace(farms=fs,private=ps[p],market=mk)) for p in (0,1)]
    engine._process_market(states,SimpleNamespace(configuration=cfg))
    return fs,ps


def search(farms,privates,market_state,orders,cfg,seat,baseline):
    base_fs,base_ps=baseline
    base_money=[f['money'] for f in base_fs]
    base_sig=[signature(base_fs[p],base_ps[p]) for p in (0,1)]
    current=orders[seat]
    key=(0,0)
    seen={tuple(tuple(o) for o in current)}
    proposed=0;accepted=0;best_changes=[0,0]
    for _ in range(2):
        proposals=[]
        for i,order in enumerate(current):
            if not i or not order or order[0] not in ('SELL','BUY_PRODUCT'):
                continue
            for earlier in range(i):
                candidate=current[:earlier]+[order]+current[earlier:i]+current[i+1:]
                sig=tuple(tuple(o) for o in candidate)
                if sig not in seen:
                    seen.add(sig);proposals.append(candidate)
                if len(proposals)>=48:break
            if len(proposals)>=48:break
        best_orders=current
        for proposal in proposals:
            proposed+=1
            trial=orders.copy();trial[seat]=proposal
            fs,ps=market(farms,privates,market_state,trial,cfg)
            if [signature(fs[p],ps[p]) for p in (0,1)]!=base_sig:
                continue
            changes=[fs[p]['money']-base_money[p] for p in (0,1)]
            trial_key=(changes[seat]-changes[1-seat],changes[seat])
            if changes[seat]>=0 and trial_key[0]>0 and trial_key>key:
                key=trial_key;best_orders=proposal;best_changes=changes
        if best_orders is current:break
        current=best_orders;accepted+=1
    return dict(relative_gain=key[0],own_gain=best_changes[seat],rival_gain=best_changes[1-seat],
                accepted_passes=accepted,proposals=proposed,chosen_orders=current if accepted else None)


if __name__=='__main__':
    target=HERE/'audit_v2.json';assert not target.exists()
    source=ROOT/'diagnostics/disjoint_live_top100_cash_20260927/ledger.json'
    ledger=json.loads(source.read_text());assert ledger['complete']
    cohort={g['episode_id']:g for g in json.loads((ROOT/'diagnostics/disjoint_live_audit_20260927/cohort_1005.json').read_text())['games']}
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),complete=False,
             source_ledger_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             engine_sha256=hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest(),
             plan_sha256=hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest(),
             perfect_information_diagnostic=True,deployable=False,independent_strength_evidence=False,games=[])
    assert out['engine_sha256']=='bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e'
    def save():target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    for record in ledger['games']:
        trace_raw=gzip.decompress(Path(record['trace_path']).read_bytes())
        assert hashlib.sha256(trace_raw).hexdigest()==record['trace_sha256']
        trace=json.loads(trace_raw)
        live=cohort[record['episode_id']]
        replay=json.loads(gzip.decompress(Path(live['replay_path']).read_bytes()))
        cfg=replay['configuration'];seat=record['candidate_seat']
        turns={t['step']:t for t in trace['turns'] if t['players_before']}
        opportunities=[];evaluated=0
        for step in range(719):
            ts=[trace['traces'][p][step] for p in (0,1)]
            assert all(t['step']==step for t in ts)
            farms=copy.deepcopy(ts[0]['observation']['farms'])
            privates=[copy.deepcopy(t['observation']['private']) for t in ts]
            actions=[t['action'] for t in ts]
            apply_units(farms,privates,actions,step,cfg)
            orders=[a.get('market',[]) for a in actions]
            mk=ts[0]['observation']['market']
            base_fs,base_ps=market(farms,privates,mk,orders,cfg)
            # The passive ledger is captured after the complete native turn.
            # At a day boundary, workers retire and carried stock is dropped.
            # Normalize only the parity copy; search uses pre-refresh states.
            check_fs,check_ps=copy.deepcopy(base_fs),copy.deepcopy(base_ps)
            if (step+1)%max(1,int(cfg.get('turnsPerDay',24)))==0:
                for p in (0,1):
                    engine._drop_inventories_to_shed(check_ps[p],int(cfg.get('shedCapacity',100)))
                    check_fs[p]['hands']=[]
            for p in (0,1):
                expected=turns[step]['players_after'][p]
                actual=dict(cash=check_fs[p]['money'],shed=check_ps[p]['shed'],seeds=check_ps[p]['seeds'],
                            hands=len(check_fs[p]['hands']),unlocked_quadrants=check_fs[p]['unlocked_quadrants'])
                assert all(expected[k]==v for k,v in actual.items()),(record['episode_id'],step,p,actual,expected)
            if len(orders[seat])>=2:
                evaluated+=1
                result=search(farms,privates,mk,orders,cfg,seat,(base_fs,base_ps))
                opportunities.append(dict(step=step,**result))
        result=dict(episode_id=record['episode_id'],opponent=record['opponent'],factual_margin=record['margin'],
                    parity_turns=719,evaluated_turns=evaluated,positive_turns=sum(r['relative_gain']>0 for r in opportunities),
                    sum_local_relative_gains=sum(r['relative_gain'] for r in opportunities),
                    sum_local_own_gains=sum(r['own_gain'] for r in opportunities),
                    sum_local_rival_gains=sum(r['rival_gain'] for r in opportunities),
                    independent_state_opportunities=opportunities)
        out['games'].append(result);save()
        print(record['opponent'],'factual',record['margin'],'local opportunities',result['positive_turns'],
              'summed local relative gain',result['sum_local_relative_gains'],flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat());save()
