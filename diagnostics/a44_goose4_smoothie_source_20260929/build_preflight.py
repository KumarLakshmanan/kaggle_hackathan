"""Build and verify the exact-a44 + Goose4 + Smoothie static freeze."""
from collections import Counter
from pathlib import Path
import ast, copy, gzip, hashlib, importlib.util, json, shutil
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
UP=ROOT/'diagnostics/a44_source_bridge_goose_4leaf_20260929'
SMOOTH=ROOT/'diagnostics/smoothie_pair_continuations_20260928'
PASTURE=ROOT/'diagnostics/pasture_guard_source_leaf_20260928'
TARGET=ROOT/'diagnostics/adaptive_donor_pair_repair_20260928'
SOURCE_PUBLIC=UP/'source_public.json'
BASE_SHA='c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632'
A44_SHA='a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
SMOOTH_KEY='SMOOTHIE_SHOP|M8+|C>S|G0'; STEP72_ROUTE=113470868
ROUTES={'SMOOTHIE_SHOP|BAKERY':113639519,'SMOOTHIE_SHOP|BRUNCH_SPOT':113340658,
'SMOOTHIE_SHOP|FARMERS_MARKET':113639519,'SMOOTHIE_SHOP|ICE_CREAM_SHOP':113340658,
'SMOOTHIE_SHOP|PIZZA_SHOP':113618016,'SMOOTHIE_SHOP|SMOOTHIE_SHOP':113639519}
WANT={'live-114211346','live-114223338','public-win-114216671','public-win-114217947','public-win-114248439','public-win-114258739'}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def steps(path):
 got={}
 with gzip.open(path,'rt',encoding='utf-8') as f:
  for line in f:
   x=json.loads(line)
   if x.get('step') in (72,144):
    got[x['step']]=x
    if len(got)==2:break
 assert set(got)=={72,144},path
 return got
def static_layer(text):
 tree=ast.parse(text); agents=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='agent']
 assert len(agents)==1
 calls=[n for n in ast.walk(agents[0]) if isinstance(n,ast.Call)]
 assert sum(isinstance(c.func,ast.Name) and c.func.id=='_A44_SMOOTHIE_PARENT' for c in calls)==1
 assert sum(isinstance(c.func,ast.Name) and c.func.id=='_a44_smoothie_commit' for c in calls)==2
 assigns=[n for n in ast.walk(agents[0]) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='result' for t in n.targets)]
 assert len(assigns)==1
 assert not any(isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='observation' and isinstance(n.slice,ast.Constant) and n.slice.value=='private' for n in ast.walk(tree))
 assert not any(s in text for s in ("['private']","['money']","['seed']",'fixture_id','opponent_id','coordinate'))
 return {'parent_call_count':1,'returns_parent_action_unchanged':True,'route_commit_sites':2,'private_or_identity_selector':False}
def import_module(path):
 spec=importlib.util.spec_from_file_location('a44_goose4_smoothie_static',path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 # Allow a deterministic static rebuild until the outcome runner has created
 # any ledger/receipt; never let the builder rewrite completed game evidence.
 if any((HERE/name).exists() for name in ('candidate.jsonl','candidate.json','combined_results.json')):
  raise SystemExit('outcome evidence exists; refusing to rebuild frozen inputs')
 pm=read(UP/'frozen_manifest.json');assert pm['complete'] and pm['candidate_sha256']==BASE_SHA and pm['source_a44_sha256']==A44_SHA
 for name,digest in pm['bindings'].items():assert Path(name).exists() and sha(name)==digest, name
 shutil.copyfile(UP/'frozen_manifest.json',HERE/'goose4_parent_manifest.json')
 shutil.copyfile(UP/'panel.json',HERE/'parent_panel.json')
 shutil.copyfile(UP/'feature_rows.json',HERE/'feature_rows.json')
 base=HERE/'candidate_goose4_base.py';layer=HERE/'smoothie_layer.py'
 assert sha(base)==BASE_SHA
 raw=base.read_bytes();lay=layer.read_bytes();candidate=raw.rstrip(b'\r\n')+b'\n\n'+lay
 compile(candidate,str(HERE/'candidate.py'),'exec');(HERE/'candidate.py').write_bytes(candidate)
 cand_sha=sha(HERE/'candidate.py');assert candidate[:len(raw)]==raw
 layer_checks=static_layer(lay.decode('utf-8'));m=import_module(HERE/'candidate.py')
 assert sha(UP/'source_a44.py')==A44_SHA
 goose_rules={'FARMERS_MARKET|M<8|C>S|G0':113535489,'ICE_CREAM_SHOP|M8+|C<S|G0':113535489,'ICE_CREAM_SHOP|M8+|C>S|G0':113470868,'PIZZA_SHOP|M8+|C<S|G0':113470868}
 assert m._A44_GOOSE4_RULES==goose_rules and m._A44_SMOOTHIE_KEY72==SMOOTH_KEY
 assert m._A44_SMOOTHIE_ROUTE72==STEP72_ROUTE and m._A44_SMOOTHIE_PAIR_ROUTES==ROUTES
 base_map=copy.deepcopy(m._A44_GOOSE4_BASE_ROUTE_MAP);base_farmice=copy.deepcopy(m._A44_GOOSE4_BASE_FARMICE)
 assert m._A44_SMOOTHIE_BASE_ROUTE_MAP==base_map and m._A44_SMOOTHIE_BASE_FARMICE==base_farmice and m._DATA['route_map']==base_map
 features=read(HERE/'feature_rows.json');assert features['complete'] and features['source_a44_sha256']==A44_SHA
 assert len(features['rows'])==208 and len({(x['fixture_id'],int(x['seat'])) for x in features['rows']})==208
 assert len({x['fixture_id'] for x in features['rows']})==104
 pf=read(PASTURE/'feature_rows.json');past={(x['provenance']['fixture_id'],int(x['provenance']['candidate_seat'])):x['selector_features'] for x in pf['rows']};assert len(past)==208
 parent_panel=read(HERE/'parent_panel.json');fmeta={f['fixture_id']:f for f in parent_panel['fixtures']};assert len(fmeta)==104
 pair_rows=[];trigger=[]
 for r in features['rows']:
  k=(r['fixture_id'],int(r['seat']));p=Path(r['trace_path']);assert p.exists() and sha(p)==r['trace_sha256']
  st=steps(p);o72=st[72]['observation'];o144=st[144]['observation'];key=m._a44_smoothie_rule_key(o72);assert key==r['rule_key']
  pair='|'.join(o144['town']['unlocked_shops'][:2]);q=past[k]
  active=m._a44_smoothie_rule_active(72,r['bridge_branch'],key)
  z={'fixture_id':r['fixture_id'],'panel':r['panel'],'seat':int(r['seat']),'bridge_branch':r['bridge_branch'],'rule_key':key,
    'public_step72':{'first_shop':o72['town']['unlocked_shops'][0],'rival_melon_tiles':r['melon_count'],'rival_cow_tiles':r['cow_count'],'rival_sheep_tiles':r['sheep_count'],'rival_goose_tiles':r['goose_count']},
    'public_step144_shops':o144['town']['unlocked_shops'][:2],'shop_pair_key':pair,'smoothie_rule_active':active,
    'selected_route':(ROUTES.get(pair,STEP72_ROUTE) if active else None),'rival_hands_step1':q['obs1_rival_hands'],
    'rival_pasture_count_step1':q['obs1_rival_pasture_count'],'trace_path':r['trace_path'],'trace_sha256':r['trace_sha256']}
  pair_rows.append(z)
  if active:trigger.append(z)
 assert len(pair_rows)==208 and len(trigger)==12 and len({x['fixture_id'] for x in trigger})==6 and {x['fixture_id'] for x in trigger}==WANT
 assert all(x['bridge_branch']=='source' and x['rule_key']==SMOOTH_KEY for x in trigger)
 assert all(x['rival_hands_step1']==0 and x['rival_pasture_count_step1']==0 for x in trigger)
 assert not any(x['panel']=='top20' for x in trigger)
 assert Counter(x['panel'] for x in trigger)=={'loss30':4,'public-win':8}
 assert all(x['shop_pair_key'] in ROUTES for x in trigger)
 assert set(m._A44_GOOSE4_RULES).isdisjoint({SMOOTH_KEY})
 dump(HERE/'pair_rows.json',{'complete':True,'source_a44_sha256':A44_SHA,'source_feature_rows_sha256':sha(HERE/'feature_rows.json'),'rows':pair_rows})
 # Fixed replay evidence is bound separately; confirm selected route rows for all trigger seats.
 selection=read(SMOOTH/'selection.json');assert selection['selected'][0]['rules']=={k:str(v) for k,v in ROUTES.items()}
 screen=read(SMOOTH/'screen.json');assert screen['complete'] and screen['clean'] and len(screen['games'])==132
 sg={(x['fixture_id'],int(x['candidate_seat']),str(x['route'])):x for x in screen['games']};screen_expected=[]
 for x in trigger:
  route=str(x['selected_route']);g=sg[(x['fixture_id'],x['seat'],route)]
  assert g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 and not g['candidate_errors'] and g['result']=='win'
  screen_expected.append({'fixture_id':x['fixture_id'],'seat':x['seat'],'pair':x['shop_pair_key'],'route':route,'screen_candidate_sha256':g['candidate_sha256'],'screen_margin':g['margin'],'screen_result':g['result']})
 # Guard exclusivity, reset, route descendants and actual source schedule helper resolution.
 donor={n:{'map':copy.deepcopy(v['_DONOR_MAP']),'routes':copy.deepcopy(v['_DONOR_ROUTES'])} for n,v in m._BRIDGE_DONORS.items()}
 assert m._a44_smoothie_rule_active(72,'source',SMOOTH_KEY)
 assert all(not m._a44_smoothie_rule_active(s,b,k) for s,b,k in [(71,'source',SMOOTH_KEY),(73,'source',SMOOTH_KEY),(72,'shared151',SMOOTH_KEY),(72,'shared150',SMOOTH_KEY),(72,'source','PIZZA_SHOP|M8+|C<S|G0')])
 assert m._a44_smoothie_pair_active(144,'source',True)
 assert all(not m._a44_smoothie_pair_active(s,b,a) for s,b,a in [(144,'shared151',True),(143,'source',True),(144,'source',False)])
 route_checks=[]
 for gkey,gr in goose_rules.items():
  shop=gkey.split('|',1)[0];desc=[k for k in base_map if k.split('|',1)[0]==shop]
  for pair,sr in ROUTES.items():
   m._a44_goose4_reset();m._a44_smoothie_reset_state();m._a44_goose4_commit(gkey,gr)
   gstate={k:m._DATA['route_map'][k] for k in desc+[shop] if k in m._DATA['route_map']};farm=copy.deepcopy(m._FARMICE_TAPE)
   m._a44_smoothie_commit(sr);sdesc=[k for k in base_map if k.split('|',1)[0]=='SMOOTHIE_SHOP']
   assert all(m._DATA['route_map'][k]==gr for k in desc) and all(m._DATA['route_map'][k]==sr for k in sdesc)
   assert m._DATA['route_map']['SMOOTHIE_SHOP']==sr and {k:m._DATA['route_map'][k] for k in gstate}==gstate
   assert m._FARMICE_TAPE==farm
   assert m._hire_recovery_schedule({'step':144,'town':{'unlocked_shops':pair.split('|')}})==m._DATA['routes'][str(sr)]
   assert {n:{'map':v['_DONOR_MAP'],'routes':v['_DONOR_ROUTES']} for n,v in m._BRIDGE_DONORS.items()}==donor
   route_checks.append({'goose_key':gkey,'goose_route':gr,'pair':pair,'smoothie_route':sr,'goose_descendants_preserved':len(desc),'smoothie_descendants_updated':len(sdesc)})
   m._a44_goose4_reset();m._a44_smoothie_reset_state();assert m._DATA['route_map']==base_map and m._FARMICE_TAPE==base_farmice and not m._A44_SMOOTHIE_ACTIVE
 m._a44_goose4_reset();m._a44_smoothie_reset_state();m._a44_smoothie_commit(STEP72_ROUTE)
 assert m._hire_recovery_schedule({'step':72,'town':{'unlocked_shops':['SMOOTHIE_SHOP']}})==m._DATA['routes'][str(STEP72_ROUTE)]
 for pair,sr in ROUTES.items():
  m._a44_smoothie_commit(sr);assert m._hire_recovery_schedule({'step':144,'town':{'unlocked_shops':pair.split('|')}})==m._DATA['routes'][str(sr)]
 assert {n:{'map':v['_DONOR_MAP'],'routes':v['_DONOR_ROUTES']} for n,v in m._BRIDGE_DONORS.items()}==donor
 m._a44_goose4_reset();m._a44_smoothie_reset_state();assert m._DATA['route_map']==base_map and m._FARMICE_TAPE==base_farmice
 # Parent Goose4 outcome receipt is clean; independently normalize its route telemetry before reuse.
 gr=read(UP/'candidate.json');gl=[json.loads(x) for x in (UP/'candidate.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
 assert gr['complete'] and gr['clean'] and gr['candidate_sha256']==BASE_SHA and len(gr['games'])==208
 rows={(x['fixture_id'],int(x['candidate_seat'])):x for x in gr['games']};ledger={(x['fixture_id'],int(x['candidate_seat'])):x for x in gl}
 assert len(rows)==len(ledger)==208 and rows.keys()==ledger.keys()
 featmap={(x['fixture_id'],int(x['seat'])):x for x in features['rows']};trigger_keys={(x['fixture_id'],x['seat']) for x in trigger}
 raw_false=[];reuse=[]
 for key,g in rows.items():
  f=featmap[key];t=g['candidate_telemetry'];eb=f['bridge_branch'] if f['bridge_branch']=='source' else '';ek=f['rule_key'] if f['bridge_branch']=='source' else ''
  er=str(f['selected_route']) if f['selected_route'] is not None else '';et=647 if er else ''
  normalized=(t.get('a44_goose4_branch72','')==eb and t.get('a44_goose4_key72','')==ek and str(t.get('a44_goose4_route',''))==er and t.get('a44_goose4_turns',0)==(et if er else 0) and t.get('a44_goose4_errors',0)==0)
  assert normalized and g['clean'] and g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 and not g.get('candidate_errors')
  if not g.get('activation_passed'):
   raw_false.append(key);assert f['selected_route'] is not None and type(f['selected_route']) is int and t.get('a44_goose4_route')==str(f['selected_route'])
  if key not in trigger_keys:
   reuse.append({'fixture_id':key[0],'candidate_seat':key[1],'panel':f['panel'],'candidate_sha256':g['candidate_sha256'],
     'result':g['result'],'margin':g['margin'],'candidate_reward':g['candidate_reward'],'opponent_reward':g['opponent_reward'],
     'candidate_status':g['candidate_status'],'opponent_status':g['opponent_status'],'frames':g['frames'],'clean':True,
     'candidate_errors':{},'normalized_goose4_activation_passed':True,'smoothie_rule_active':False,
     'parent_receipt_activation_flag':g.get('activation_passed')})
 assert len(raw_false)==20 and len(reuse)==196 and all(x['normalized_goose4_activation_passed'] for x in reuse)
 dump(HERE/'reuse_rows.json',{'complete':True,'parent_candidate_sha256':BASE_SHA,
  'parent_candidate_receipt_sha256':sha(UP/'candidate.json'),'parent_candidate_ledger_sha256':sha(UP/'candidate.jsonl'),
  'parent_stored_activation_false_rows':20,'normalized_activation_passed':True,'rows':reuse,
  'excluded_trigger_keys':[{'fixture_id':f,'candidate_seat':s} for f,s in sorted(trigger_keys)]})
 # Exact-a44 controls: 100 target rows plus 108 public source rows.
 target=read(TARGET/'full_results.json');public=read(SOURCE_PUBLIC);assert target['complete'] and target['clean'] and public['complete'] and public['clean']
 controls=[x for x in target['games'] if x.get('candidate_sha256')==A44_SHA]+[x for x in public['games'] if x.get('candidate_sha256')==A44_SHA]
 ctrl={(x['fixture_id'],int(x['candidate_seat'])):x for x in controls};assert len(ctrl)==len(controls)==208
 dump(HERE/'a44_controls.json',{'complete':True,'candidate_sha256':A44_SHA,
  'target_receipt_sha256':sha(TARGET/'full_results.json'),'public_receipt_sha256':sha(SOURCE_PUBLIC),
  'rows':[{k:x[k] for k in ('fixture_id','candidate_seat','candidate_sha256','candidate_reward','opponent_reward','margin','result','candidate_status','opponent_status','frames')} for _,x in sorted(ctrl.items())]})
 parent_fx={x['fixture_id']:x for x in parent_panel['fixtures']};six=[];expected=[]
 for fid in sorted(WANT):
  x=parent_fx[fid];six.append({k:x[k] for k in ('fixture_id','panel','seed','source_replay_path','source_replay_sha256','source_action_tape_path','source_opponent_action_sha256')})
 for x in sorted(trigger,key=lambda a:(a['fixture_id'],a['seat'])):
  a44row=ctrl[x['fixture_id'],x['seat']]
  expected.append({'fixture_id':x['fixture_id'],'seat':x['seat'],'panel':x['panel'],'bridge_branch':x['bridge_branch'],
   'rule_key':x['rule_key'],'public_step72':x['public_step72'],'public_step144_shops':x['public_step144_shops'],
   'shop_pair_key':x['shop_pair_key'],'route72':str(STEP72_ROUTE),'selected_route':str(x['selected_route']),
   'a44_baseline':{k:a44row[k] for k in ('result','margin','candidate_reward','opponent_reward')}})
 dump(HERE/'panel.json',{'candidate':'exact a44 + Goose4 + source-only Smoothie continuation',
  'fixture_count':6,'candidate_games':12,'fixture_order':'fixture_id sorted; seats 0 then 1',
  'comparison':'exact a44 controls; reuse Goose4 outcomes only for statically equivalent nontrigger seats',
  'fixtures':six,'expected_seats':expected})
 pre={'schema':'a44-goose4-smoothie-static-preflight-v1','passed':True,'static_only':True,'games_run':0,
  'experiment_completed':False,'promotion':False,'source_a44_sha256':A44_SHA,'goose4_candidate_sha256':BASE_SHA,
  'candidate_sha256':cand_sha,'smoothie_layer_sha256':sha(layer),'feature_rows':208,'fixture_count':104,
  'trigger_seats':12,'reusable_parent_seats':196,'trigger_fixtures':6,'trigger_fixture_ids':sorted(WANT),
  'trigger_rows_by_panel':dict(Counter(x['panel'] for x in trigger)),'top20_trigger_seats':0,
  'smoothie_pair_coverage':dict(Counter(x['shop_pair_key'] for x in trigger)),
  'goose4_key_overlap_seats':0,'pasture_guard_overlap_seats':0,'eligible_source_branch':True,
  'eligible_rival_hands_step1':0,'eligible_rival_pastures_step1':0,'all_pairs_supported':True,
  'candidate_prefix_byte_equal':True,'candidate_prefix_sha256':sha(base),'layer_static_checks':layer_checks,
  'route_map_reset_isolation':{'passed':True,'goose4_rules_preserved_under_all_pair_commits':True,
    'smoothie_descendants_only':True,'farmice_reset_unchanged':True,'donor_maps_structurally_unchanged':True,
    'helper_step72_route':STEP72_ROUTE,'helper_all_step144_routes':True,'route_checks':route_checks},
  'decision_equivalence_for_nontrigger_seats':{'passed':True,'seats':196,
    'basis':'Exact prefix plus guarded wrapper: on every nontrigger feature row the source+key step72 guard is false; active stays false, step144 is a no-op, and the wrapper returns the frozen Goose4 parent action unchanged. New telemetry is the only output difference.'},
  'reuse_audit':{'parent_rows':208,'unique_rows':208,'clean_rows':208,'reusable_nontrigger_rows':196,
    'newly_tested_rows':12,'normalized_activation_passed':True,'normalized_activation_pass_rows':208,
    'stored_activation_false_rows':20,'stored_false_reason':'route ID int in feature table vs string telemetry; all other checks pass'},
  'selected_route_member_screen':screen_expected,'parent_goose_stored_activation_caveat':'Original receipt left unchanged; 20 stored false gates are only type mismatches, independently normalized across all 208 rows.',
  'candidate_panel':{'fixtures':6,'seats_per_fixture':[0,1],'games':12,'staged_command':'python -X utf8 diagnostics/a44_goose4_smoothie_source_20260929/run_six.py candidate'},
  'reactive_validation':False}
 dump(HERE/'preflight.json',pre)
 # Freeze dependencies. Parent manifest transitively binds all 208 source traces and replay tapes.
 external=[UP/'source_a44.py',UP/'candidate.py',UP/'preflight.json',UP/'frozen_manifest.json',UP/'feature_rows.json',UP/'panel.json',UP/'source_public.json',UP/'candidate.json',UP/'candidate.jsonl',UP/'run_study.py',UP/'build_preflight.py',UP/'RESULTS.md',
  TARGET/'full_results.json',TARGET/'full_pool.json',ROOT/'diagnostics/production_leaf_selector_20260928/candidate_production_goose.py',ROOT/'diagnostics/production_leaf_selector_20260928/full.json',ROOT/'diagnostics/production_leaf_selector_20260928/selection.json',ROOT/'diagnostics/production_leaf_selector_20260928/pool.json',ROOT/'diagnostics/production_leaf_selector_20260928/RESULTS.md',
  SMOOTH/'PLAN.md',SMOOTH/'RESULTS.md',SMOOTH/'pool.json',SMOOTH/'preflight.json',SMOOTH/'screen.jsonl',SMOOTH/'screen.json',SMOOTH/'selection.json',SMOOTH/'candidate_selected_family0.py',SMOOTH/'candidates/family0_113639519.py',SMOOTH/'candidates/family0_113340658.py',SMOOTH/'candidates/family0_113618016.py',ROOT/'diagnostics/production_leaf_selector_20260928/candidates/production_eda72aac9c_113470868.py',
  PASTURE/'feature_rows.json',PASTURE/'static_preflight.json',PASTURE/'pool.json',PASTURE/'candidate_pasture_guard_source_leaf.py',PASTURE/'PLAN.md',ROOT/'diagnostics/goal90_20260928/BASELINE.md',ROOT/'diagnostics/goal90_20260928/BASELINE.json',ROOT/'diagnostics/stream_replay_io_20260928/fast_game_cached.py',ROOT/'diagnostics/stream_replay_io_20260928/cached_input.py',ROOT/'diagnostics/stream_replay_io_20260928/cached_helper_manifest.json',ROOT/'diagnostics/stream_replay_io_20260928/cached_helper_parity.json',ROOT/'diagnostics/physical_route_rollout_20260928/native_core.py',ROOT/'diagnostics/physical_route_rollout_20260928/check.py',ROOT/'diagnostics/local_target_20260928/run_lock.py',ROOT/'diagnostics/adaptive_third_pair_repair_20260928/discovery.json']
 ext={str(p.resolve()):sha(p) for p in external};assert len(ext)==len(external)
 internal=[HERE/x for x in ('candidate_goose4_base.py','smoothie_layer.py','candidate.py','build_preflight.py','run_six.py','PLAN.md','goose4_parent_manifest.json','parent_panel.json','feature_rows.json','pair_rows.json','reuse_rows.json','a44_controls.json','panel.json','preflight.json')]
 bindings={str(p.resolve()):sha(p) for p in internal};bindings.update(ext)
 manifest={'complete':True,'diagnostic_only':True,'source_a44_sha256':A44_SHA,'goose4_candidate_sha256':BASE_SHA,'candidate_sha256':cand_sha,
  'full_panel_sha256':sha(HERE/'parent_panel.json'),'panel_sha256':sha(HERE/'panel.json'),'feature_rows_sha256':sha(HERE/'feature_rows.json'),
  'pair_rows_sha256':sha(HERE/'pair_rows.json'),'reuse_rows_sha256':sha(HERE/'reuse_rows.json'),'a44_controls_sha256':sha(HERE/'a44_controls.json'),
  'preflight_sha256':sha(HERE/'preflight.json'),'parent_manifest_sha256':sha(HERE/'goose4_parent_manifest.json'),
  'trace_count':208,'reused_parent_rows':196,'new_candidate_rows':12,'bindings':bindings}
 dump(HERE/'frozen_manifest.json',manifest)
 for name,digest in bindings.items():assert Path(name).exists() and sha(name)==digest,name
 for name,digest in pm['bindings'].items():assert Path(name).exists() and sha(name)==digest,name
 print(json.dumps({'preflight_sha256':sha(HERE/'preflight.json'),'manifest_sha256':sha(HERE/'frozen_manifest.json'),
  'candidate_sha256':cand_sha,'candidate_bytes':(HERE/'candidate.py').stat().st_size,'panel_sha256':sha(HERE/'panel.json'),
  'pair_rows_sha256':sha(HERE/'pair_rows.json'),'reuse_rows_sha256':sha(HERE/'reuse_rows.json'),
  'a44_controls_sha256':sha(HERE/'a44_controls.json'),'bindings':len(bindings),'parent_bindings_verified':len(pm['bindings']),
  'trigger_seats':12,'reused_seats':196,'games_run':0,'stored_parent_activation_false_rows':20,'normalized_parent_activation_passed':True},indent=2))
if __name__=='__main__':main()
