import copy, gzip, hashlib, importlib.util, json, pathlib
ROOT=pathlib.Path(r'H:\hackathan')
BASE=ROOT/'diagnostics'/'fresh90_improvement_20260929'
OUT=ROOT/'diagnostics'/'fresh90_loss_audit_20260929'
mod_path=BASE/'candidate_funded_land_v1.py'
spec=importlib.util.spec_from_file_location('funded_land_candidate',mod_path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
CFG={'boardSize':10,'maxMarketOrdersPerTurn':10,'shedCapacity':100,'farmHandCostMult':1}
p=BASE/'cb76_top20_jobs_traces'/'rank10_ep115317514_s0.jsonl.gz'
with gzip.open(p,'rt',encoding='utf8') as f:
    r=next(json.loads(s) for s in f if json.loads(s).get('step')==242)
obs=r['observation']; orders=r['action']['market']; stock=mod._queue_stock(obs,r['action'],CFG); proposed=copy.deepcopy(orders); proposed.append(proposed.pop(2))
scenarios={}
for label,rival in [('idle',[]),('mirror',orders)]:
  old=mod._queue_simulate(obs,orders,rival,stock,CFG); new=mod._queue_simulate(obs,proposed,rival,stock,CFG)
  scenarios[label]={'old_own_cash':old[0],'new_own_cash':new[0],'own_cash_delta':new[0]-old[0], 'old_rival_cash':old[1],'new_rival_cash':new[1],'rival_cash_delta':new[1]-old[1], 'own_quadrants_before':old[2][3],'own_quadrants_after':new[2][3], 'own_signature_nonland_unchanged':old[2][:3]+old[2][4:]==new[2][:3]+new[2][4:], 'rival_signature_unchanged':old[3]==new[3]}
# Exact evidence hashes and source action identifiers.
paths=[mod_path, BASE/'baseline_cb76fbc4.py', BASE/'cb76_top20_jobs_results.jsonl', p, p.with_name('rank10_ep115317514_s1.jsonl.gz')]
def sha(path):
 h=hashlib.sha256();
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
result={'step242_market_observation':obs['market'],'farms':obs['farms'],'private':obs['private'],'action':r['action'],'idle_and_mirror_simulation':scenarios,'hashes':{str(x.relative_to(ROOT)):sha(x) for x in paths}}
(OUT/'funded_land_step242_native_controls.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'market':obs['market'],'cash':obs['farms'][0]['money'],'queues':r['action']['market'],'controls':scenarios,'hashes':result['hashes']},indent=2))
