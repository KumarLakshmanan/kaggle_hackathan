from __future__ import annotations
import copy,gc,gzip,hashlib,importlib.util,json,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import Box,state_from_frames,sha
from diagnostics.stream_replay_io_20260928.cached_input import load_fixture
from diagnostics.local_target_20260928.run_lock import exclusive_run

BASE=ROOT/'main_candidate_pet_source_guard_20260929_257f941d.py'
BASE_SHA='257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'
CAND=HERE/'candidate_257f_melon_delivery.py'
CAND_SHA='a8174509cd2679578869b3090a9137d136e22a4e752c2bc9dc822b86a1aade25'
PANEL=ROOT/'diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/panel.json'
PANEL_SHA='fee3b1d5f93cd295c28dd8d0c04ea672806dbb55e2b59999853a9f969c0fb90d'
BASE_RESULTS=ROOT/'diagnostics/pet_source_guard_20260929/preservation_outcomes.jsonl'
CENSUS=HERE/'incumbent_selector_census.json';PREFIX=HERE/'native_prefix_receipt.json';MANIFEST=HERE/'frozen_manifest.json'
OUT_ROWS=HERE/'treatment_outcomes.jsonl';OUT_RECEIPT=HERE/'outcome_receipt.json'
TARGETS={'live-114271958','top20-08-Unknown Mother-Goose-114272024'}


def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def make_game(fixture,seat):
    replay=load_fixture(fixture);cfg=dict(replay['configuration']);cfg['seed']=None
    assert cfg['episodeSteps']==720
    state=state_from_frames(replay['steps'][0]);env=Box(configuration=Box(**cfg),info={'seed':int(fixture['seed'])},done=False)
    tape=json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    hashes=[hashlib.sha256(json.dumps(tape,sort_keys=s,separators=(',',':')).encode()).hexdigest() for s in (False,True)]
    assert fixture['source_opponent_action_sha256'] in hashes and len(tape)==719
    return replay,cfg,state,env,tape


def expected_action(step,parent_action,hand_index):
    wanted=copy.deepcopy(parent_action)
    if step in (713,714,715):wanted['hands'][hand_index]=['EAST']
    elif step==716:
        wanted['hands'][hand_index]=['DROP'];wanted['market'].append(['SELL','MELON',12])
    return wanted


def run_game(job,baseline):
    fixture=job['fixture'];seat=job['seat'];fid=job['fixture_id'];panel_name=job['panel'];is_target=fid in TARGETS
    replay,cfg,state,env,tape=make_game(fixture,seat)
    candidate=load_module(CAND,f'candidate_treatment_{job["index"]}')
    parent=load_module(BASE,f'parent_control_{job["index"]}')
    trace_path=None;trace=None
    if is_target:
        safe='offhand' if fid=='live-114271958' else 'unknown_mother_goose'
        trace_path=HERE/f'treatment_trace_{safe}_seat{seat}.jsonl.gz'
        trace=gzip.open(trace_path,'wt',encoding='utf-8')
    calls=0.;max_call=0.;parent_calls=0.;start=time.perf_counter();frames=1;action_mismatches=[];telemetry_mismatches=[]
    try:
        for step in range(719):
            obs=copy.deepcopy(dict(state[seat].observation,remainingOverageTime=60.0))
            parent_obs=copy.deepcopy(obs)
            t0=time.perf_counter();parent_action=parent.agent(parent_obs,cfg);parent_calls+=time.perf_counter()-t0
            t0=time.perf_counter();candidate_action=candidate.agent(copy.deepcopy(obs),cfg);dur=time.perf_counter()-t0
            calls+=dur;max_call=max(max_call,dur)
            candidate_parent_telemetry={k:v for k,v in dict(getattr(candidate.agent,'telemetry',{}) or {}).items() if not k.startswith('melon_delivery_')}
            direct_parent_telemetry=dict(getattr(parent.agent,'telemetry',{}) or {})
            if candidate_parent_telemetry!=direct_parent_telemetry:
                telemetry_mismatches.append({'step':step,'candidate_parent_telemetry':candidate_parent_telemetry,
                    'direct_parent_telemetry':direct_parent_telemetry})
            planned=(is_target and 713<=step<=716)
            want=expected_action(step,parent_action,5) if planned else parent_action
            if candidate_action!=want:
                action_mismatches.append({'step':step,'planned_transform':planned,'candidate_action':candidate_action,'parent_action':parent_action,'expected_action':want})
            if is_target:
                player=int(obs['player']);route_map=getattr(candidate,'_P257_MELON_ROUTE_STATE',{})
                if step<713 or step>=717:
                    if player in route_map: action_mismatches.append({'step':step,'route_latch_leaked':True})
                elif step<716:
                    if route_map.get(player,{}).get('hand_index')!=5 or route_map.get(player,{}).get('next_step')!=step+1:
                        action_mismatches.append({'step':step,'bad_route_latch':route_map.get(player)})
                elif player in route_map:
                    action_mismatches.append({'step':step,'route_latch_not_cleared':True})
                if trace:
                    trace.write(json.dumps({'step':step,'observation':obs,'parent_action':parent_action,
                                            'candidate_action':candidate_action,'route_state':route_map.get(player)},separators=(',',':'))+'\n')
            state[seat].action=candidate_action;state[1-seat].action=copy.deepcopy(tape[step])
            core.interpreter(state,env)
            for item in state:item.observation.step=step+1
            frames+=1
        telemetry=dict(getattr(candidate.agent,'telemetry',{}) or {})
        errors={k:v for k,v in telemetry.items() if ('error' in k or 'collision' in k) and v}
        own=float(state[seat].reward);rival=float(state[1-seat].reward)
        actual=dict(fixture_id=fid,candidate_seat=seat,candidate_sha256=CAND_SHA,candidate_reward=own,
            opponent_reward=rival,margin=own-rival,result='win' if own>rival else 'loss' if own<rival else 'draw',
            candidate_status=state[seat].status,opponent_status=state[1-seat].status,frames=frames,
            candidate_telemetry=telemetry,candidate_errors=errors,candidate_action_mismatches=action_mismatches,
            candidate_parent_telemetry_mismatches=telemetry_mismatches,
            policy_action_steps=719,candidate_call_seconds=calls,max_candidate_call_seconds=max_call,
            parent_reference_call_seconds=parent_calls,wall_seconds=time.perf_counter()-start,
            comparison='Exact 257f parent recomputed on each same native observation; candidate runs against frozen rival tape')
        old=baseline[(fid,seat)]
        # Target fixtures are explicitly allowed to change both rewards and margin;
        # their frozen gate preserves W/D/L and clean completion only. Untouched
        # rows must also retain exact rewards and margin, alongside action parity.
        preservation_fields=('result','candidate_status','opponent_status','frames')
        actual['preserves_old_result']=all(actual[k]==old[k] for k in preservation_fields)
        actual['preserves_non_target_rewards']=(is_target or all(actual[k]==old[k] for k in ('candidate_reward','opponent_reward','margin')))
        old_telemetry=old.get('candidate_telemetry',{})
        same_observation_parent_telemetry_pass=not telemetry_mismatches
        actual['same_observation_parent_telemetry_pass']=same_observation_parent_telemetry_pass
        actual['preserves_prior_telemetry']=same_observation_parent_telemetry_pass and (is_target or
            {k:v for k,v in telemetry.items() if not k.startswith('melon_delivery_')}==old_telemetry)
        actual['telemetry_reference']='same-observation exact 257f parent'+(' and saved baseline' if not is_target else '')
        actual['action_parity_pass']=not action_mismatches
        actual['clean']=state[seat].status==state[1-seat].status=='DONE' and frames==720 and not errors
        actual['trace_path']=str(trace_path.relative_to(ROOT)) if trace_path else None
        actual['passed_row']=actual['preserves_old_result'] and actual['preserves_non_target_rewards'] and actual['action_parity_pass'] and actual['clean'] and actual['preserves_prior_telemetry'] is True
        return actual
    finally:
        if trace:trace.close()
        del candidate,parent,state,replay
        gc.collect()


def main():
    assert sha(BASE)==BASE_SHA and sha(CAND)==CAND_SHA and sha(PANEL)==PANEL_SHA
    frozen=json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert frozen['frozen_before_outcomes'] and frozen['outcomes_run'] is False
    for entry in frozen['files'].values():
        bound=ROOT/entry['path']
        assert sha(bound)==entry['sha256'], str(bound)
    assert sha(ROOT/'main.py')=='4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
    census=json.loads(CENSUS.read_text(encoding='utf-8'))
    prefix=json.loads(PREFIX.read_text(encoding='utf-8'))
    expected_activations={(fid,seat) for fid in TARGETS for seat in (0,1)}
    observed_activations={(r['fixture_id'],int(r['seat'])) for r in census.get('activation_rows',[])}
    assert census['schema']=='257f-incumbent-melon-trigger-census-v1'
    assert census['candidate_sha256']==BASE_SHA and census['panel_sha256']==PANEL_SHA
    assert census['baseline_only'] and census['no_intervention'] and census['no_outcomes']
    assert census['complete'] and census['exactly_expected_activations'] and observed_activations==expected_activations
    assert len(census['rows'])==102 and len({(r['fixture_id'],int(r['candidate_seat'])) for r in census['rows']})==102
    assert prefix['schema']=='257f-melon-native-prefix-v1'
    assert prefix['complete'] and prefix['through_step']==716 and prefix['interleaved_seats']
    assert prefix['no_terminal_rewards_or_margins_read'] and prefix['passed']
    assert prefix['candidate_sha256']==CAND_SHA and prefix['baseline_sha256']==BASE_SHA
    assert prefix['plan_sha256']==sha(HERE/'PLAN.md') and prefix['manifest_sha256']==sha(MANIFEST)
    prefix_fixtures=prefix.get('fixtures',[])
    assert len(prefix_fixtures)==2 and {r['fixture_id'] for r in prefix_fixtures}==TARGETS
    for fixture_result in prefix_fixtures:
        assert fixture_result['passed'] and fixture_result['steps_validated_through']==716 and fixture_result['interleaved_seats']
        assert fixture_result['candidate_sha256']==CAND_SHA and fixture_result['baseline_sha256']==BASE_SHA
        assert fixture_result['errors']=={}
        assert {(int(r['seat']),int(r['step'])) for r in fixture_result['actions']}=={(s,t) for s in (0,1) for t in range(713,717)}
        assert {int(r['seat']) for r in fixture_result['post_drop_checks']}=={0,1}
        assert all(r['step716_drop_applied'] and r['route_state_cleared'] for r in fixture_result['post_drop_checks'])
    panel=json.loads(PANEL.read_text(encoding='utf-8'))
    jobs=[dict(fixture=r['fixture'],fixture_id=r['fixture_id'],seat=int(r['candidate_seat']),panel=r['panel']) for r in panel['games']]
    jobs += [dict(fixture=r['fixture'],fixture_id=r['fixture_id'],seat=int(r['seat']),panel='public_win_control') for r in panel['controls']]
    assert len(jobs)==102 and len({(j['fixture_id'],j['seat']) for j in jobs})==102
    baseline={}
    for line in BASE_RESULTS.read_text(encoding='utf-8').splitlines():
        row=json.loads(line);baseline[(row['fixture_id'],int(row['candidate_seat']))]=row['actual']
    assert len(baseline)==102
    assert not OUT_ROWS.exists() and not OUT_RECEIPT.exists()
    rows=[]
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
      with exclusive_run(HERE/'outcome_run.lock'):
       with OUT_ROWS.open('x',encoding='utf-8') as output:
        for n,job in enumerate(jobs,1):
            job['index']=n
            actual=run_game(job,baseline);actual['panel']=job['panel'];rows.append(actual)
            output.write(json.dumps(actual,ensure_ascii=True)+'\n');output.flush()
            print(json.dumps({'completed':n,'planned':102,'fixture':job['fixture_id'],'seat':job['seat'],
                'result':actual['result'],'margin':actual['margin'],'action_parity':actual['action_parity_pass'],
                'preserves':actual['preserves_old_result']},ensure_ascii=True),flush=True)
       sweeps={}
       for panel_name in ('loss30','top20'):
            selected=[r for r in rows if r['panel']==panel_name]
            ids={r['fixture_id'] for r in selected};index={(r['fixture_id'],r['candidate_seat']):r for r in selected}
            sweeps[panel_name]=sum(all(index[(fid,s)]['result']=='win' for s in (0,1)) for fid in ids)
       target_rows={}
       for fid in sorted(TARGETS):
            target_rows[fid]=[]
            for seat in (0,1):
                row=next(r for r in rows if r['fixture_id']==fid and r['candidate_seat']==seat)
                old=baseline[(fid,seat)];row['margin_delta_vs_257f']=row['margin']-old['margin']
                row['paired_margin_delta']=row['margin_delta_vs_257f']
                target_rows[fid].append({'seat':seat,'baseline_margin':old['margin'],'candidate_margin':row['margin'],
                    'margin_delta':row['margin_delta_vs_257f'],'result':row['result'],'own_delta':row['candidate_reward']-old['candidate_reward'],
                    'rival_delta':row['opponent_reward']-old['opponent_reward']})
       offhand_ok=all(x['result']=='win' and x['margin_delta']>0 for x in target_rows['live-114271958'])
       umg_ok=all(x['result']=='win' and x['margin_delta']>=0 for x in target_rows['top20-08-Unknown Mother-Goose-114272024'])
       required_sweeps_pass=sweeps.get('loss30',0)>=27 and sweeps.get('top20',0)>=19
       receipt=dict(schema='257f-melon-treatment-panel-v1',candidate_sha256=CAND_SHA,baseline_sha256=BASE_SHA,
          panel_sha256=PANEL_SHA,frozen_manifest_sha256=sha(MANIFEST),plan_sha256=sha(HERE/'PLAN.md'),
          census_sha256=sha(CENSUS),prefix_sha256=sha(PREFIX),complete=len(rows)==102,
          fixed_tape_only=True,research_promotion=False,score_or_rank_not_estimated=True,
          action_parity_all_rows=all(r['action_parity_pass'] for r in rows),
          prior_results_preserved=all(r['preserves_old_result'] for r in rows),
          prior_telemetry_preserved=all(r['preserves_prior_telemetry'] is True for r in rows),
          same_observation_parent_telemetry_parity=all(r['same_observation_parent_telemetry_pass'] for r in rows),
          non_target_rewards_preserved=all(r['preserves_non_target_rewards'] for r in rows),
          preserved_sweeps=sweeps,required_sweeps_pass=required_sweeps_pass,
          clean_games=all(r['clean'] for r in rows),offhand_strict_margin_gate=offhand_ok,
          unknown_mother_goose_margin_gate=umg_ok,target_results=target_rows,
          all_rows_pass=all(r['passed_row'] for r in rows) and required_sweeps_pass and offhand_ok and umg_ok,
          rows_path=str(OUT_ROWS.relative_to(ROOT)),rows_sha256=sha(OUT_ROWS),games=rows)
       with OUT_RECEIPT.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=True,indent=2)
       print(json.dumps({k:v for k,v in receipt.items() if k!='games'},indent=2),flush=True)
       if not receipt['all_rows_pass']:raise SystemExit('Frozen outcome gate failed; keep candidate experimental and do not promote.')

if __name__=='__main__':main()
