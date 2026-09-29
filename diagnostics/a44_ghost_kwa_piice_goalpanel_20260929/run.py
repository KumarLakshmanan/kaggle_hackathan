"""Run the 100 saved-seat games for the frozen V4 + PIICE candidate."""
from datetime import datetime,timezone
import json
from pathlib import Path
import runpy,sys
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
CANDIDATE=HERE/'candidate.py'
COMBO_RUN=ROOT/'diagnostics/a44_ghost_kwa_combo_20260929/outcome_run_20260929'
PANEL=HERE/'panel.json';MANIFEST=HERE/'frozen_manifest.json';STATIC=HERE/'static_preflight.json'
RESULTS=HERE/'outcomes.jsonl';RECEIPT=HERE/'outcome_receipt.json';RUN_MANIFEST=HERE/'run_manifest.json'
SHARED_LOCK=ROOT/'diagnostics/.shared_game_run.lock';OWN_LOCK=HERE/'run.lock'
FIELDS=('result','candidate_reward','opponent_reward','margin','candidate_status','opponent_status','frames')
PIICE_PAIR='PIZZA_SHOP|ICE_CREAM_SHOP';PIICE_KEY='PIZZA_SHOP|M8+|C>S|G0';PIICE_ROUTE='113339524'

def sha(path):
 import hashlib
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def require(ok,msg):
 if not ok:raise AssertionError(msg)
def verify():
 m=read(MANIFEST);p=read(PANEL);s=read(STATIC)
 require(m.get('complete') and m.get('fixed_tape_only') and not m.get('promotion'),'manifest status')
 require(sha(CANDIDATE)==m.get('candidate_sha256') and sha(PANEL)==m.get('panel_sha256'),'candidate/panel hash')
 require(m.get('runner_sha256')==sha(HERE/'run.py') and m.get('builder_sha256')==sha(HERE/'build_panel.py')
         and m.get('plan_sha256')==sha(HERE/'PLAN.md'),'script hashes')
 require(s.get('passed') and s.get('engine_transitions')==0 and s.get('candidate_sha256')==m['candidate_sha256'],'static preflight')
 require(len(m['bindings'])==m.get('binding_count'),'binding count')
 bad=[]
 for path,digest in m['bindings'].items():
  pth=Path(path);actual=sha(pth) if pth.is_file() else 'MISSING'
  if actual!=digest:bad.append((path,actual,digest))
 require(not bad,f'frozen input mismatch {bad[:5]}')
 require(p.get('game_count')==100 and len(p.get('games',[]))==100
         and p.get('parent_v4_candidate_sha256')==m.get('parent_v4_candidate_sha256'),'panel size/parent')
 require(sum(bool(r['expected_piice_trigger']) for r in p['games'])==2
         and sum(r['panel']=='top20' and r['expected_piice_trigger'] for r in p['games'])==0,'PIICE trigger census')
 require(not any(x.exists() for x in (RESULTS,RECEIPT,RUN_MANIFEST)),'runner is one-shot; outputs already exist')
 return m,p

def piice_checks(actual,row):
 t=actual.get('candidate_telemetry') or {};trigger=bool(row['expected_piice_trigger'])
 key=row['expected_piice_key72'];pair=row['expected_piice_pair144']
 branch=row['expected_branch']
 return {
  'piice_key72':t.get('piice_key72')==(key if branch=='source' else ''),
  'piice_branch144':t.get('piice_branch144')==branch,
  'piice_key144':t.get('piice_key144')==(key if branch=='source' else ''),
  'piice_pair144':(t.get('piice_pair144')==pair if trigger
                   else isinstance(t.get('piice_pair144'),str)),
  'piice_active':t.get('piice_active144') is trigger,
  'piice_route':t.get('piice_route144')==(PIICE_ROUTE if trigger else ''),
  'piice_turns':t.get('piice_active_turns')==(575 if trigger else 0),
  'piice_errors_zero':t.get('piice_errors',0)==0,
  'ghost_inactive_if_piice':not trigger or not t.get('a44_ghost_wheat_active72',False),
  'kwa_inactive_if_piice':not trigger or not t.get('a44_kwa_wheat_zero_active72',False),
 }

def run_once():
 m,p=verify();sys.path.insert(0,str(ROOT))
 from diagnostics.local_target_20260928.run_lock import exclusive_run
 from diagnostics.stream_replay_io_20260928.fast_game_cached import play
 combo_checks=runpy.run_path(str(COMBO_RUN/'run.py'))['telemetry_checks']
 started=datetime.now(timezone.utc).isoformat();games=[]
 with exclusive_run(SHARED_LOCK):
  with exclusive_run(OWN_LOCK):
   require(not any(x.exists() for x in (RESULTS,RECEIPT,RUN_MANIFEST)),'existing output')
   with RUN_MANIFEST.open('x',encoding='utf-8',newline='\n') as out:
    json.dump({'started_at_utc':started,'candidate_sha256':m['candidate_sha256'],
      'parent_v4_candidate_sha256':m['parent_v4_candidate_sha256'],'panel_sha256':m['panel_sha256'],
      'shared_lock_path':str(SHARED_LOCK),'worker_count':1,'resume_allowed':False},out,indent=2);out.write('\n')
   with RESULTS.open('x',encoding='utf-8',newline='\n') as stream:
    for row in p['games']:
     actual=play(row['source_fixture'],CANDIDATE,m['candidate_sha256'],int(row['candidate_seat']))
     checks=combo_checks(actual,row);checks.update(piice_checks(actual,row))
     clean=actual.get('candidate_status')==actual.get('opponent_status')=='DONE' and actual.get('frames')==720 and not actual.get('candidate_errors')
     baseline=row['baseline_v4'];exact={f:actual.get(f)==baseline.get(f) for f in FIELDS}
     piice=bool(row['expected_piice_trigger'])
     trigger=bool(row['expected_kwa_trigger'] or row['expected_ghost_trigger'] or piice)
     target_win=actual.get('result')=='win' and float(actual.get('margin',0))>0
     record={'fixture_id':row['fixture_id'],'candidate_seat':row['candidate_seat'],'panel':row['panel'],
       'candidate_sha256':m['candidate_sha256'],'expected_kwa_trigger':row['expected_kwa_trigger'],
       'expected_ghost_trigger':row['expected_ghost_trigger'],'expected_piice_trigger':piice,
       'clean_done_done_720':clean,'telemetry_checks':checks,'telemetry_passed':all(checks.values()),
       'exact_v4_fields':exact,'v4_preserved':(all(exact.values()) if not piice else None),
       'piice_target_win':target_win if piice else None,'any_route_target_win':target_win if trigger else None,
       'baseline_v4':baseline,'actual':actual,'delta_margin_vs_v4':actual['margin']-baseline['margin']}
     games.append(record);stream.write(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n');stream.flush()
     print(json.dumps({k:record[k] for k in ('fixture_id','candidate_seat','panel','expected_piice_trigger','clean_done_done_720','telemetry_passed','v4_preserved','piice_target_win')}|{'result':actual['result'],'margin':actual['margin']},ensure_ascii=False),flush=True)
  def grouped(panel_name):
   ids=sorted({g['fixture_id'] for g in games if g['panel']==panel_name})
   by={fid:[g['actual']['result'] for g in games if g['fixture_id']==fid] for fid in ids}
   return ids,by,sum(len(by[fid])==2 and all(x=='win' for x in by[fid]) for fid in ids)
  loss_ids,loss_by,loss_sweeps=grouped('loss30');top_ids,top_by,top_sweeps=grouped('top20')
  piice=[g for g in games if g['expected_piice_trigger']]
  kwa=[g for g in games if g['expected_kwa_trigger']]
  ghost=[g for g in games if g['expected_ghost_trigger']]
  exact_rows=[g for g in games if not g['expected_piice_trigger']]
  all_clean=len(games)==100 and all(g['clean_done_done_720'] for g in games)
  all_tel=len(games)==100 and all(g['telemetry_passed'] for g in games)
  exact_gate=len(exact_rows)==98 and all(g['v4_preserved'] for g in exact_rows)
  piice_gate=len(piice)==2 and all(g['piice_target_win'] for g in piice)
  gk_gate=len(kwa)==2 and len(ghost)==2 and all(g['actual']['result']=='win' for g in kwa+ghost)
  loss_gate=len(loss_ids)==30 and loss_sweeps>=27
  top_gate=len(top_ids)==20 and top_sweeps>=18
  receipt={'schema':'a44-v4-piice-100-seat-outcome-v1','complete':len(games)==100,
   'diagnostic_only':True,'fixed_tape_only':True,'reactive_validation':False,'promotion':False,
   'candidate_sha256':m['candidate_sha256'],'parent_v4_candidate_sha256':m['parent_v4_candidate_sha256'],
   'panel_sha256':m['panel_sha256'],'games':games,'game_count':len(games),
   'clean_100':all_clean,'telemetry_100':all_tel,'parent_v4_exact_98_nonpiice_rows':exact_gate,
   'both_piice_target_seats_win':piice_gate,'four_ghost_kwa_target_seats_win':gk_gate,
   'loss30_fixture_count':len(loss_ids),'loss30_winning_sweeps':loss_sweeps,'loss30_goal_27_of_30':loss_gate,
   'top20_fixture_count':len(top_ids),'top20_winning_sweeps':top_sweeps,'top20_goal_18_of_20':top_gate,
   'parent_v4_loss30_winning_sweeps':p['parent_v4_loss30_winning_sweeps'],
   'parent_v4_top20_winning_sweeps':p['parent_v4_top20_winning_sweeps'],
   'parent_6d_loss30_winning_sweeps':p['parent_6d_loss30_winning_sweeps'],
   'combined_goal_passed':loss_gate and top_gate,'completed_at_utc':datetime.now(timezone.utc).isoformat()}
  receipt['passed']=all(receipt[k] for k in ('complete','clean_100','telemetry_100','parent_v4_exact_98_nonpiice_rows','both_piice_target_seats_win','four_ghost_kwa_target_seats_win','loss30_goal_27_of_30','top20_goal_18_of_20'))
  with RECEIPT.open('x',encoding='utf-8',newline='\n') as out:json.dump(receipt,out,ensure_ascii=False,indent=2);out.write('\n')
  print(json.dumps({k:v for k,v in receipt.items() if k!='games'},ensure_ascii=False,indent=2),flush=True)
 return receipt

if __name__=='__main__':
 _,_=verify();result=run_once()
 if not result['passed']:raise SystemExit(1)
