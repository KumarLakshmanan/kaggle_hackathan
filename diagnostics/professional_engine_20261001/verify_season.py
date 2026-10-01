"""Production units, full native season and partial-budget decision boundaries."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; sys.path.insert(0,str(ROOT))
from kaggriculture_engine import native_core as core
from kaggriculture_engine.pro import season
from kaggriculture_engine.pro.beliefs import RivalBelief
from kaggriculture_engine.pro.scenarios import generate
from kaggriculture_engine.pro.simulation import make_world, TransitionCache


def main():
    payload = json.loads((HERE/'example_input.json').read_text()); obs = payload['observation']; cfg = payload['configuration']
    source_hashes = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'kaggriculture_engine/pro/season.py',ROOT/'kaggriculture_engine/pro/portfolio.py',
        ROOT/'kaggriculture_engine/pro/scheduler.py',ROOT/'kaggriculture_engine/pro/scenarios.py',ROOT/'kaggriculture_engine/pro/simulation.py',
        ROOT/'kaggriculture_engine/native_core.py',HERE/'example_input.json']}
    belief = RivalBelief().update(obs,cfg)
    report = season.search(obs,cfg,belief,max_transitions=28000)
    assert not report['partial'] and report['transitions'] <= 28000
    assert all(r['terminal'] for r in report['baseline'])
    assert all(c['complete'] and all(r['terminal'] for r in c['outcomes']) for c in report['cases'])
    assert all(r['margin'] == r['own_coins']-r['rival_coins'] for c in report['cases'] for r in c['outcomes'])
    assert all(isinstance(q,int) and q >= 0 for c in report['cases'] for r in c['outcomes'] for q in r['harvested_units'].values())
    partial = season.search(obs,cfg,belief,max_transitions=10)
    assert partial['partial'] and partial['selected'] is None and partial['transitions'] == 0
    # Two workers ask to harvest the same plant: native executes it exactly once.
    probe = copy.deepcopy(obs); probe['player']=0; probe['day']=4; probe['hour']=0; probe['step']=96
    farm = core._new_farm(10,3000); farm['hands']=[[4,4]]
    tile=core._new_plant('WHEAT',0,24); tile['yield_units']=4; farm['tiles'][4][4]=tile
    probe['farms'][0]=farm; probe['private']=core._new_private(); probe['private']['inventories'].append({})
    act={'farmer':['HARVEST'],'hands':[['HARVEST']],'market':[]}
    ledger=season.harvest_ledger(probe,act,cfg); assert ledger['WHEAT']==4
    world=make_world(probe,cfg,generate(probe,RivalBelief().update(probe,cfg))[0])
    after=TransitionCache(0).advance(world,[act,{'farmer':['PASS']}])
    assert sum(i.get('WHEAT',0) for i in after[0][0].observation.private['inventories'])==ledger['WHEAT']
    report.update(source_hashes=source_hashes,verified_at_utc=datetime.now(timezone.utc).isoformat())
    (HERE/'offline_all_products_verified.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    receipt={'passed':True,'source_hashes':source_hashes,'transitions':report['transitions'],'horizon':report['horizon'],
        'complete_scenario_seasons':len(report['baseline'])+sum(len(c['outcomes']) for c in report['cases']),
        'partial_budget_cannot_select':True,'double_harvest_native_units':ledger['WHEAT'],'selected':report['selected'],
        'cases':[{'name':c['name'],'relative_coin_gain':c['relative_coin_gain'],'viable':c['viable']} for c in report['cases']]}
    (HERE/'all_products_verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
