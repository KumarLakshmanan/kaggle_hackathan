import copy, gzip, hashlib, importlib.util, json, pathlib
ROOT = pathlib.Path(r'H:\hackathan')
BASE = ROOT / 'diagnostics' / 'fresh90_improvement_20260929'
OUT = ROOT / 'diagnostics' / 'fresh90_loss_audit_20260929'
CAND = BASE / 'candidate_funded_land_v1.py'
RESULTS = BASE / 'cb76_top20_jobs_results.jsonl'
TRACE_DIR = BASE / 'cb76_top20_jobs_traces'
CFG = {'boardSize': 10, 'maxMarketOrdersPerTurn': 10, 'shedCapacity': 100, 'farmHandCostMult': 1}

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

spec=importlib.util.spec_from_file_location('funded_land_candidate', CAND)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
rows=[json.loads(s) for s in RESULTS.read_text(encoding='utf-8').splitlines() if s.strip()]
rows=[r for r in rows if r.get('label')=='cb76']
all_attempts=[]
accepted=[]
case_stats=[]
for r in rows:
    tp=ROOT / pathlib.Path(r['trace_path'])
    trace=[json.loads(s) for s in gzip.open(tp,'rt',encoding='utf-8') if s.strip()]
    episode=[]
    for idx, rec in enumerate(trace):
        obs=rec['observation']; action=rec['action']; orders=action.get('market',[])
        inds=[i for i,o in enumerate(orders) if o and o[0]=='BUY_LAND']
        if not inds: continue
        next_obs=trace[idx+1]['observation'] if idx+1<len(trace) else None
        changed_quads=(next_obs is not None and next_obs['farms'][int(obs['player'])]['unlocked_quadrants'] != obs['farms'][int(obs['player'])]['unlocked_quadrants'])
        event={'rank':r['rank'],'team':r['team'],'episode':r['episode_id'],'seat':r['candidate_seat'],'step':rec['step'],'day':obs.get('day'),'cash':obs['farms'][int(obs['player'])]['money'],'quadrants':obs['farms'][int(obs['player'])]['unlocked_quadrants'],'orders':orders,'next_cash':None if next_obs is None else next_obs['farms'][int(obs['player'])]['money'],'next_quadrants':None if next_obs is None else next_obs['farms'][int(obs['player'])]['unlocked_quadrants'],'land_changed_next':changed_quads}
        all_attempts.append(event); episode.append(event)
        action_copy=copy.deepcopy(action)
        result=mod._funded_land_apply(obs, action_copy, CFG)
        if result.get('market') != orders:
            accepted_event=dict(event)
            accepted_event['proposed_orders']=result['market']
            accepted.append(accepted_event)
    case_stats.append({'rank':r['rank'],'team':r['team'],'episode':r['episode_id'],'seat':r['candidate_seat'],'rows':len(trace),'land_attempts':len(episode),'eligible_attempts':sum(2<=len(e['orders'])<=10 and len([o for o in e['orders'] if o and o[0]=='BUY_LAND'])==1 and e['orders'].index(next(o for o in e['orders'] if o and o[0]=='BUY_LAND')) < len(e['orders'])-1 for e in episode),'failed_attempts':sum(not e['land_changed_next'] for e in episode)})
report={'candidate_sha256':sha(CAND),'results_sha256':sha(RESULTS),'trace_count':len(rows),'unique_fixtures':len(set(r['fixture_id'] for r in rows)),'config':CFG,'attempts':all_attempts,'accepted':accepted,'case_stats':case_stats,'stats':{'land_orders':len(all_attempts),'failed_next_observation':sum(not e['land_changed_next'] for e in all_attempts),'eligible_to_reorder':sum(2<=len(e['orders'])<=10 and len([o for o in e['orders'] if o and o[0]=='BUY_LAND'])==1 and e['orders'].index(next(o for o in e['orders'] if o and o[0]=='BUY_LAND')) < len(e['orders'])-1 for e in all_attempts),'accepted':len(accepted)}}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'funded_land_trace_census.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'stats':report['stats'],'accepted':accepted,'rank10': [e for e in all_attempts if e['rank']==10]},indent=2))
