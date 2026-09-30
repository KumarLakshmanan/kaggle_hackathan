import copy, gzip, hashlib, importlib.util, json, pathlib, collections
ROOT=pathlib.Path(r'H:\hackathan')
REFRESH=ROOT/'diagnostics'/'fresh90_refresh_20260929'
SUMMARY=REFRESH/'routes'/'current_submission_56680167_opponents'/'summary.json'
OUT=ROOT/'diagnostics'/'fresh90_loss_audit_20260929'
IDS={115319884,115315638,115302829}
CAND=ROOT/'diagnostics'/'fresh90_improvement_20260929'/'candidate_funded_land_v1.py'
CFG={'boardSize':10,'episodeSteps':720,'farmHandCostMult':1,'maxMarketOrdersPerTurn':10,'shedCapacity':100,'turnsPerDay':24,'townCenterSellInterval':24,'townShopSellInterval':4,'townShopUnlockInterval':3,'weedSpawnChance':0.005}
spec=importlib.util.spec_from_file_location('funded_land_candidate',CAND); helper=importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def canonical_sha(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()
def tile_summary(farm):
 crops=collections.Counter(); crop_yield=collections.Counter(); animals=collections.Counter(); structures=collections.Counter()
 for row in farm['tiles']:
  for t in row:
   if not isinstance(t,dict): continue
   k=t.get('kind')
   if k=='PLANT':
    crop=t.get('crop','?'); crops[crop]+=1; crop_yield[crop]+=int(t.get('yield_units',0))
   elif k in ('PASTURE','COOP'):
    structures[k]+=1
    a=t.get('animal')
    if a: animals[a]+=1
 return {'plants':dict(sorted(crops.items())),'plant_yield_units':dict(sorted(crop_yield.items())),'animals_on_tiles':dict(sorted(animals.items())),'structures':dict(sorted(structures.items()))}
def snap(obs,seat):
 own=obs['farms'][seat]; rival=obs['farms'][1-seat]
 return {'cash':own['money'],'rival_cash':rival['money'],'cash_margin':own['money']-rival['money'],'own_quadrants':own['unlocked_quadrants'],'rival_quadrants':rival['unlocked_quadrants'],'hands':len(own['hands']),'rival_hands':len(rival['hands']),'own_hires_today':own.get('hires_today'),'crops':tile_summary(own),'rival_crops':tile_summary(rival),'seeds':dict(obs['private'].get('seeds',{})),'shed':dict(obs['private'].get('shed',{})),'shops':obs.get('town',{}).get('unlocked_shops',[]),'prices':{k:v for k,v in obs['market'].get('prices',{}).items()}}
def plants_attempts(obs, action, seat):
 farm=obs['farms'][seat]; units=[action.get('farmer',[])]+action.get('hands',[]); positions=[farm['farmer']]+farm['hands']; out=[]
 for idx,(pos,u) in enumerate(zip(positions,units)):
  if not u or u[0]!='PLANT': continue
  crop=u[1] if len(u)>1 else '?'; x,y=pos; tile=farm['tiles'][y][x]
  seeds=obs['private'].get('seeds',{}).get(crop,0)
  locked=tile=='LOCKED'
  out.append({'unit':idx,'pos':pos,'crop':crop,'seeds_before_farm_actions':seeds,'locked':locked,'tile':tile})
 return out

def load_raw(ep):
 p=REFRESH/'raw_archive'/f'episode-{ep}-replay.json.gz'
 return p,json.load(gzip.open(p,'rt',encoding='utf8'))
rows=json.load(open(SUMMARY,encoding='utf8'))
selected=[r for r in rows if r['episode_id'] in IDS]
report={'summary_sha256':sha(SUMMARY),'helper_source':str(CAND.relative_to(ROOT)),'helper_source_sha256':sha(CAND),'episodes':[]}
for meta in sorted(selected,key=lambda r:r['episode_id']):
 rp,d=load_raw(meta['episode_id']); seat=int(meta['uploaded_agent_original_source_seat']); opp=1-seat
 steps=d['steps']; end=d.get('rewards',[])
 candidate_tape=[frame[seat].get('action') or {'farmer':['PASS'],'hands':[],'market':[]} for frame in steps[1:]]
 candidate_tape_sha256=canonical_sha(candidate_tape)
 ep={'team':meta['team'],'episode_id':meta['episode_id'],'seed':meta['seed'],'candidate_seat':seat,'candidate_result':meta['uploaded_agent_wdl_result'],'candidate_reward':end[seat] if len(end)>seat else None,'rival_reward':end[opp] if len(end)>opp else None,'reward_margin':(end[seat]-end[opp]) if len(end)>opp else None,'archive_sha256':sha(rp),'archive_replay_sha256':meta['replay_sha256'],'rival_route_path':meta['path'],'rival_action_sha256':meta['action_sha256'],'candidate_action_sha256':meta['uploaded_agent_action_sha256'],'selected_cand_seat_source_sha256':meta['uploaded_agent_action_sha256'],'source_seat':meta['source_seat'],'funded_land_activations':[],'land_orders':[],'funded_orders':[],'zero_seed_plants':[],'day_end':[],'major_events':[],'action_counts':{},'terminal':None}
 ep['candidate_tape_recomputed_sha256']=candidate_tape_sha256
 ep['candidate_tape_hash_matches_summary']=candidate_tape_sha256==meta['uploaded_agent_action_sha256']
 counts=collections.Counter(); land=[]; funded=[]; zero_seed=[]; day_end={}
 for i in range(min(719,len(steps)-1)):
  s=steps[i][seat]; o=s.get('observation') or {}
  # Live policy action from the next replay frame; this aligns the action tape with observation i.
  a=steps[i+1][seat].get('action') or {}
  nobs=steps[i+1][seat].get('observation') or {}
  frame=int(o.get('step') if isinstance(o.get('step'),int) else i)
  day=int(o.get('day',frame//24)); farm=o['farms'][seat]; nxt=nobs['farms'][seat] if nobs else {}
  for order in a.get('market',[]):
   if order: counts[order[0]+(':'+str(order[1]) if len(order)>1 else '')]+=int(order[2]) if len(order)>2 and isinstance(order[2],int) else 1
   if order and order[0]=='BUY_LAND':
    land.append({'step':frame,'day':day,'cash_before':farm['money'],'quadrants_before':list(farm['unlocked_quadrants']),'market':a.get('market',[]),'cash_after':nxt.get('money'),'quadrants_after':list(nxt.get('unlocked_quadrants',[])),'success':len(nxt.get('unlocked_quadrants',[]))>len(farm['unlocked_quadrants'])})
  for order in a.get('market',[]):
   if order and order[0] in ('HIRE','BUY_LAND','BUY_SEED','BUY_ANIMAL','BUY_PRODUCT'):
    funded.append({'step':frame,'day':day,'order':order,'cash_before':farm['money'],'hands_before':len(farm['hands']),'hands_after':len(nxt.get('hands',[])),'hires_today_before':farm.get('hires_today'),'hires_today_after':nxt.get('hires_today'),'quadrants_before':list(farm['unlocked_quadrants']),'quadrants_after':list(nxt.get('unlocked_quadrants',[])),'seed_before':dict(o.get('private',{}).get('seeds',{})),'seed_after':dict(nobs.get('private',{}).get('seeds',{})),'shed_before':dict(o.get('private',{}).get('shed',{})),'shed_after':dict(nobs.get('private',{}).get('shed',{}))})
  zp=plants_attempts(o,a,seat)
  for z in zp:
   if z['seeds_before_farm_actions']==0 or z['locked']:
    zero_seed.append({'step':frame,'day':day,**z})
  if day not in day_end or (o.get('hour',0)>=day_end[day][0]):
   day_end[day]=(o.get('hour',0),{'step':frame,'day':day,**snap(o,seat)})
  # Store first few candidate farm plan events, including route-defining plant attempts.
  if a.get('market') or zp:
   if len(ep['major_events'])<240:
    ep['major_events'].append({'step':frame,'day':day,'hour':o.get('hour'),'cash':farm['money'],'rival_cash':o['farms'][opp]['money'],'cash_margin':farm['money']-o['farms'][opp]['money'],'farm_action':a.get('farmer'),'hands_actions':a.get('hands',[]),'market':a.get('market',[]),'plant_attempts':zp,'pre':snap(o,seat),'post_cash':nxt.get('money') if nxt else None,'post_hands':len(nxt.get('hands',[])) if nxt else None,'post_quadrants':nxt.get('unlocked_quadrants') if nxt else None})
  # Static exact helper census: no action is executed, only a proposal is checked.
  acopy=copy.deepcopy(a)
  try: result=helper._funded_land_apply(o,acopy,CFG)
  except Exception as ex: result=a; ep.setdefault('land_helper_errors',[]).append({'step':frame,'error':str(ex)})
  if result.get('market')!=a.get('market',[]):
   ep['funded_land_activations'].append({'step':frame,'day':day,'cash':farm['money'],'quadrants':farm['unlocked_quadrants'],'before':a.get('market',[]),'after':result.get('market',[])})
 for day,(_,v) in sorted(day_end.items()):ep['day_end'].append(v)
 ep['action_counts']=dict(counts); ep['land_orders']=land; ep['funded_orders']=funded; ep['zero_seed_plants']=zero_seed
 if len(steps)>0:
  terminal=steps[-1][seat].get('observation') or {}
  ep['terminal']={'step':terminal.get('step'),'day':terminal.get('day'),'cash':terminal.get('farms',[{},{}])[seat].get('money'),'rival_cash':terminal.get('farms',[{},{}])[opp].get('money'),'cash_margin':terminal.get('farms',[{},{}])[seat].get('money',0)-terminal.get('farms',[{},{}])[opp].get('money',0),'own':tile_summary(terminal.get('farms',[{},{}])[seat]),'rival':tile_summary(terminal.get('farms',[{},{}])[opp]),'seeds':terminal.get('private',{}).get('seeds'),'shed':terminal.get('private',{}).get('shed'),'quadrants':terminal.get('farms',[{},{}])[seat].get('unlocked_quadrants')}
 ep['action_sha_candidate_hash_check']='matched' if ep['candidate_tape_hash_matches_summary'] else 'mismatch'
 report['episodes'].append(ep)
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'latest_public_losses_56680167_static.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
# Compact inspection output.
for e in report['episodes']:
 print('EP',e['episode_id'],e['team'],'seat',e['candidate_seat'],'rewards',e['candidate_reward'],e['rival_reward'],'margin',e['reward_margin'],'funded_land',e['funded_land_activations'])
 print('LAND',e['land_orders'])
 print('ACT COUNTS',e['action_counts'])
 print('TERMINAL',e['terminal'])
 print('DAY_END',[(d['day'],round(d['cash']),round(d['rival_cash']),round(d['cash_margin']),d['hands'],d['crops']['plants'],d['rival_crops']['plants'],d['own_quadrants']) for d in e['day_end']])
 print('ZERO_SEED_PLANT',e['zero_seed_plants'][:30], 'count',len(e['zero_seed_plants']))
 print('FIRST FUNDED EVENTS',e['funded_orders'][:12])

