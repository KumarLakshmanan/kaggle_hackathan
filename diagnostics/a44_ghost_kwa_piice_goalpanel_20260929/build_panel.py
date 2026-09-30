"""Freeze the 100-seat loss30 + top20 panel for the exact V4+PIICE candidate."""
from collections import defaultdict
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
CANDIDATE_SOURCE=ROOT/'diagnostics/a44_ghost_kwa_piice_combo_20260929/candidate.py'
COMBO=ROOT/'diagnostics/a44_ghost_kwa_combo_20260929'
COMBO_RUN=COMBO/'outcome_run_20260929'
OLD_LOSS=ROOT/'diagnostics/a44_ghost_kwa_goalpanel_20260929'
PIICE=ROOT/'diagnostics/a44_ghost_kwa_piice_combo_20260929'
PAIR_PATH=PIICE/'pair_rows.json'
V4_SHA='7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2'
CANDIDATE_SHA='8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62'
PAIR='PIZZA_SHOP|ICE_CREAM_SHOP'
KEY72='PIZZA_SHOP|M8+|C>S|G0'
ROUTE=113339524
FIELDS=('result','candidate_reward','opponent_reward','margin','candidate_status','opponent_status','frames')


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
 return h.hexdigest()


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def dump(path,data): Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def fields(row): return {key:row.get(key) for key in FIELDS}

def main():
 outputs=('outcomes.jsonl','outcome_receipt.json','run_manifest.json','run.lock')
 assert not any((HERE/name).exists() for name in outputs),'run output exists'
 assert sha(CANDIDATE_SOURCE)==CANDIDATE_SHA
 (HERE/'candidate.py').write_bytes(CANDIDATE_SOURCE.read_bytes())
 small=read(PIICE/'frozen_manifest.json')
 assert small['complete'] and small['candidate_sha256']==CANDIDATE_SHA
 for p,d in small['bindings'].items(): assert Path(p).is_file() and sha(p)==d,p
 loss_panel=read(OLD_LOSS/'panel.json')
 loss_receipt=read(OLD_LOSS/'outcome_receipt.json')
 top_panel=read(COMBO/'panel_v4.json')
 top_receipt=read(COMBO_RUN/'outcome_receipt.json')
 assert loss_receipt['candidate_sha256']==V4_SHA and loss_receipt['complete']
 assert top_receipt['candidate_sha256']==V4_SHA and top_receipt['passed']
 assert top_receipt['top20_winning_sweeps']==19
 pair_doc=read(PAIR_PATH)
 pair_by_key={(row['fixture_id'],int(row['seat'])):row for row in pair_doc['rows']}
 assert len(pair_by_key)==208
 loss_actual={(row['fixture_id'],int(row['candidate_seat'])):row['actual'] for row in loss_receipt['games']}
 top_ids={row['fixture_id'] for row in top_panel['games'] if row['panel']=='top20'}
 top_actual={(row['fixture_id'],int(row['candidate_seat'])):row['actual']
             for row in top_receipt['games'] if row['fixture_id'] in top_ids}
 assert len(loss_actual)==60 and len(top_ids)==20 and len(top_actual)==40
 old_loss={(row['fixture_id'],int(row['candidate_seat'])):row for row in loss_panel['games']}
 top_panel_rows={(row['fixture_id'],int(row['candidate_seat'])):row
                 for row in top_panel['games'] if row['panel']=='top20'}
 games=[]
 for source_rows,actuals,old_rows in ((loss_panel['games'],loss_actual,old_loss),
                                        ([r for r in top_panel['games'] if r['panel']=='top20'],top_actual,top_panel_rows)):
  for old in source_rows:
   key=(old['fixture_id'],int(old['candidate_seat']))
   feature=pair_by_key[key]
   baseline=actuals[key]
   branch=old['expected_branch']
   key72=old['expected_key'] if branch=='source' else ''
   pair=feature['step144_pair']
   trigger=(branch=='source' and key72==KEY72 and pair==PAIR)
   games.append({
    'fixture_id':key[0],'candidate_seat':key[1],'panel':old['panel'],
    'expected_branch':branch,'expected_key':old['expected_key'],
    'expected_kwa_trigger':bool(old['expected_kwa_trigger']),
    'expected_ghost_trigger':bool(old['expected_ghost_trigger']),
    'expected_parent_route':old.get('expected_parent_route'),
    'expected_ghost_wheat':old.get('expected_ghost_wheat'),
    'expected_kwa_wheat_plots':old.get('expected_kwa_wheat_plots'),
    'expected_ghost_wheat_telemetry':old.get('expected_ghost_wheat_telemetry'),
    'expected_kwa_wheat_plots_telemetry':old.get('expected_kwa_wheat_plots_telemetry'),
    'expected_piice_key72':key72,'expected_piice_pair144':pair,
    'expected_piice_trigger':trigger,
    'baseline_v4':fields(baseline),'baseline_v4_sha256':V4_SHA,
    'baseline_6d':old['baseline_6d'],
    'feature_trace_path':old['feature_trace_path'],
    'feature_trace_sha256':old['feature_trace_sha256'],
    'source_fixture':old['source_fixture'],
   })
 games.sort(key=lambda row:(0 if row['panel']=='loss30' else 1,
                            (loss_panel['fixture_order'].index(row['fixture_id'])
                             if row['panel']=='loss30' else sorted(top_ids).index(row['fixture_id'])),
                            row['candidate_seat']))
 assert len(games)==100
 assert len({(r['fixture_id'],r['candidate_seat']) for r in games})==100
 assert sum(r['panel']=='loss30' for r in games)==60
 assert sum(r['panel']=='top20' for r in games)==40
 assert sum(r['expected_kwa_trigger'] for r in games)==2
 assert sum(r['expected_ghost_trigger'] for r in games)==2
 assert sum(r['expected_piice_trigger'] for r in games)==2
 assert not any(r['expected_piice_trigger'] and (r['expected_kwa_trigger'] or r['expected_ghost_trigger']) for r in games)
 assert not any(r['panel']=='top20' and r['expected_piice_trigger'] for r in games)
 assert all((r['fixture_id']=='live-114238112') == r['expected_piice_trigger'] for r in games if r['panel']=='loss30')
 fixture_order=list(loss_panel['fixture_order'])+sorted(top_ids)
 v4_loss_sweeps=sum(all(loss_actual[(fid,s)]['result']=='win' for s in (0,1)) for fid in loss_panel['fixture_order'])
 v4_top_sweeps=sum(all(top_actual[(fid,s)]['result']=='win' for s in (0,1)) for fid in top_ids)
 loss6d_sweeps=loss_panel['loss30_parent_6d_winning_sweeps']
 assert v4_loss_sweeps==24 and v4_top_sweeps==19 and loss6d_sweeps==22
 panel={
  'schema':'a44-v4-piice-100-seat-goal-panel-v1',
  'candidate_path':str(CANDIDATE_SOURCE.resolve()),'candidate_sha256':CANDIDATE_SHA,
  'parent_v4_candidate_sha256':V4_SHA,'parent_v4_loss_receipt_sha256':sha(OLD_LOSS/'outcome_receipt.json'),
  'parent_v4_top20_receipt_sha256':sha(COMBO_RUN/'outcome_receipt.json'),
  'fixture_count':50,'loss30_fixture_count':30,'top20_fixture_count':20,'game_count':100,
  'loss30_min_winning_sweeps':27,'top20_min_winning_sweeps':18,
  'parent_v4_loss30_winning_sweeps':v4_loss_sweeps,
  'parent_v4_top20_winning_sweeps':v4_top_sweeps,
  'parent_6d_loss30_winning_sweeps':loss6d_sweeps,
  'ghost_target_seats':2,'kwa_target_seats':2,'piice_target_seats':2,
  'expected_piice_top20_trigger_seats':0,'parent_exact_rows_expected':98,
  'fixture_order':fixture_order,'games':games,
 }
 dump(HERE/'panel.json',panel)
 static={
  'schema':'a44-v4-piice-100-seat-static-preflight-v1','passed':True,'static_only':True,
  'engine_transitions':0,'policy_action_calls':0,
  'candidate_sha256':CANDIDATE_SHA,'parent_v4_sha256':V4_SHA,
  'seat_rows':100,'loss30_rows':60,'top20_rows':40,
  'kwa_trigger_seats':2,'ghost_trigger_seats':2,'piice_trigger_seats':2,
  'piice_triggers_in_top20':0,'parent_loss30_sweeps':24,'parent_top20_sweeps':19,
  'loss30_goal':27,'top20_goal':18,'reactive_validation':False,'promotion':False,
 }
 dump(HERE/'static_preflight.json',static)
 external=set(small['bindings'])
 external.update({str(p.resolve()) for p in (
  COMBO/'candidate_v4.py',COMBO/'panel_v4.json',COMBO_RUN/'frozen_manifest.json',
  COMBO_RUN/'outcome_receipt.json',OLD_LOSS/'panel.json',OLD_LOSS/'frozen_manifest.json',
  OLD_LOSS/'outcome_receipt.json',OLD_LOSS/'static_preflight.json',
  CANDIDATE_SOURCE,PAIR_PATH,PIICE/'outcome_receipt.json',PIICE/'frozen_manifest.json',
  ROOT/'diagnostics/stream_replay_io_20260928/fast_game_cached.py',
  ROOT/'diagnostics/stream_replay_io_20260928/cached_input.py',
  ROOT/'diagnostics/physical_route_rollout_20260928/native_core.py',
  ROOT/'diagnostics/physical_route_rollout_20260928/check.py',
  ROOT/'diagnostics/local_target_20260928/run_lock.py',ROOT/'main.py')})
 for r in games:
  external.add(str(Path(r['source_fixture']['source_replay_path']).resolve()))
  external.add(str(Path(r['source_fixture']['source_action_tape_path']).resolve()))
 bindings={}
 for path in sorted(external):
  p=Path(path);assert p.is_file(),f'missing input {p}';bindings[path]=sha(p)
 for name in ('PLAN.md','build_panel.py','run.py','candidate.py','panel.json','static_preflight.json'):
  p=HERE/name;bindings[str(p.resolve())]=sha(p)
 manifest={
  'complete':True,'diagnostic_only':True,'fixed_tape_only':True,'reactive_validation':False,'promotion':False,
  'candidate_sha256':CANDIDATE_SHA,'parent_v4_candidate_sha256':V4_SHA,
  'panel_sha256':sha(HERE/'panel.json'),'static_preflight_sha256':sha(HERE/'static_preflight.json'),
  'builder_sha256':sha(HERE/'build_panel.py'),'runner_sha256':sha(HERE/'run.py'),
  'plan_sha256':sha(HERE/'PLAN.md'),'binding_count':len(bindings),'bindings':bindings,
  'global_lock_path':'diagnostics/.shared_game_run.lock','game_count':100,
 }
 dump(HERE/'frozen_manifest.json',manifest)
 print(json.dumps({'candidate_sha256':CANDIDATE_SHA,'panel_sha256':manifest['panel_sha256'],
                   'binding_count':len(bindings),'loss30_parent_sweeps':v4_loss_sweeps,
                   'top20_parent_sweeps':v4_top_sweeps,'targets':{'kwa':2,'ghost':2,'piice':2}},indent=2))

if __name__=='__main__': main()
