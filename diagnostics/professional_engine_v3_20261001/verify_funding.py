"""Adversarial plant-blocking, full-shed and sale-funded native controls."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def main():
    spec=importlib.util.spec_from_file_location('v3_funding_probe',HERE/'candidate_guard_r3.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    proj=sys.modules[m._PRO_PACKAGE_NAME+'.pro.projection'];core=sys.modules[m._PRO_PACKAGE_NAME+'.native_core']
    sim=sys.modules[m._PRO_PACKAGE_NAME+'.pro.simulation']
    template=json.loads((ROOT/'diagnostics/physical_route_rollout_20260928/initial_template.json').read_text())
    obs=copy.deepcopy(template['frame'][0]['observation']);obs['step']=0;obs['player']=0
    obs['farms'][0]['hands']=[[3,4],[4,3]]
    obs['private']['inventories']=[{}, {}, {}];obs['private']['seeds']['WHEAT']=1
    obs['private']['shed']={p:0 for p in obs['private']['shed']};obs['private']['shed']['FERTILIZER']=100
    cfg=dict(template['configuration'],seed=None)
    scenario={'stock':{},'future_seed':77}
    action={'farmer':['PLANT','WHEAT'],'hands':[['PLANT','WHEAT'],['PLANT','WHEAT']]}
    rival={'farmer':['PASS'],'hands':[],'market':[]};rows=[]
    for name,queue in [('blocked_plant',[['BUY_SEED','WHEAT',2]]),
        ('full_shed',[['BUY_PRODUCT','WHEAT',3],['BUY_ANIMAL','GOOSE',1]]),
        ('sale_funded',[['SELL','FERTILIZER',2],['BUY_ANIMAL','GOOSE',1],[]])]:
        own=dict(action,market=queue);world=sim.make_world(obs,cfg,scenario)
        prepared=proj.prepare(world,[own,rival]);projected=proj.project(prepared,[queue,[]])
        captured=[];original=core._process_market
        def capture(state,env):
            original(state,env);captured.append(copy.deepcopy(state))
        direct=copy.deepcopy(world);direct[0][0].action=own;direct[0][1].action=rival
        core._process_market=capture
        try:core.interpreter(*direct)
        finally:core._process_market=original
        assert projected[0].observation.farms==captured[0][0].observation.farms
        assert [s.observation.private for s in projected]==[s.observation.private for s in captured[0]]
        assert not any(isinstance(t,dict) and t.get('kind')=='PLANT' for row in prepared[0][0].observation.farms[0]['tiles'] for t in row)
        if name=='full_shed':assert projected[0].observation.private['shed'].get('GOOSE',0)==0
        if name=='sale_funded':assert projected[0].observation.private['shed']['GOOSE']==1
        rows.append({'name':name,'passed':True})
    (HERE/'funding_parity_receipt.json').write_text(json.dumps({'passed':True,'cases':rows},indent=2),encoding='utf-8')
    print(json.dumps(rows),flush=True)


if __name__=='__main__':main()
