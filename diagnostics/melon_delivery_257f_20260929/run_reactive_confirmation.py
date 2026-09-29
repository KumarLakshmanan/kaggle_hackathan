from __future__ import annotations
import gc,hashlib,json,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from paired_benchmark import TimedAgent,_load_module,_timing_dict,engine_version,make
from diagnostics.local_target_20260928.run_lock import exclusive_run

CAND=HERE/'candidate_257f_melon_delivery.py'
CAND_SHA='a8174509cd2679578869b3090a9137d136e22a4e752c2bc9dc822b86a1aade25'
BASE=ROOT/'main_candidate_pet_source_guard_20260929_257f941d.py'
BASE_SHA='257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'
PANEL=ROOT/'diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/panel.json'
PANEL_SHA='fee3b1d5f93cd295c28dd8d0c04ea672806dbb55e2b59999853a9f969c0fb90d'
PANEL_RECEIPT=HERE/'outcome_receipt.json'
PANEL_ROWS=HERE/'treatment_outcomes.jsonl'
CENSUS=HERE/'incumbent_selector_census.json'
PREFIX=HERE/'native_prefix_receipt.json'
MANIFEST=HERE/'frozen_manifest.json'
SEEDS=(2026093001,2026093002,2026093003,2026093004)
OPPONENTS={
    'ahmed_v35':(ROOT/'diagnostics/public_ahmed_v35_20260927/public_v35_main.py',
                 '294e7e4d9d4b97413646960d318043e0f9116ce58f42fe02afd4716614a4e96d'),
    'c95':(ROOT/'diagnostics/public_rayk_top_meta/public_c95_main.py',
           '489f5d197527f107027626cce79d850fd2ca90edd43d94384b849b6511e27bdb'),
}
ROWS=HERE/'reactive_outcomes.jsonl'
RECEIPT=HERE/'reactive_receipt.json'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def errors(module):
    found={}
    reports={name:value for name,value in vars(module).items()
             if isinstance(value,dict) and ('STATS' in name or 'REPORT' in name)}
    reports['agent.telemetry']=getattr(module.agent,'telemetry',{}) or {}
    for name,report in reports.items():
        for key,value in report.items():
            if ('error' in str(key).lower() or 'collision' in str(key).lower()) and isinstance(value,(int,float)) and value:
                found[name+'.'+str(key)]=value
    return found


def policy(module,path,tag,capture=False):
    assert sha(path)==(CAND_SHA if path==CAND else BASE_SHA if path==BASE else OPPONENTS[tag][1])
    def call(obs,cfg):
        visible=dict(cfg)
        visible['seed']=None
        return module.agent(obs,visible)
    return TimedAgent(call,capture_step=1 if capture else None)


def run_game(job):
    arm_path=CAND if job['arm']=='treatment' else BASE
    arm_sha=CAND_SHA if job['arm']=='treatment' else BASE_SHA
    opponent_path,opponent_sha=OPPONENTS[job['opponent_id']]
    assert sha(arm_path)==arm_sha and sha(opponent_path)==opponent_sha
    candidate_module=_load_module(arm_path,'melon_reactive_arm')
    opponent_module=_load_module(opponent_path,'melon_reactive_opponent')
    try:
        candidate=policy(candidate_module,arm_path,'candidate',capture=True)
        opponent=policy(opponent_module,opponent_path,job['opponent_id'])
        env=make('kaggriculture',configuration={'episodeSteps':720,'seed':job['seed']},debug=False)
        seat=job['candidate_seat'];started=time.perf_counter()
        env.run([candidate,opponent] if seat==0 else [opponent,candidate])
        wall=time.perf_counter()-started
        final=env.steps[-1]
        own=float(final[seat].reward or 0);rival=float(final[1-seat].reward or 0);margin=own-rival
        telemetry=dict(getattr(candidate_module.agent,'telemetry',{}) or {})
        opponent_telemetry=dict(getattr(opponent_module.agent,'telemetry',{}) or {})
        candidate_errors=errors(candidate_module);opponent_errors=errors(opponent_module)
        bad_statuses=[{'frame':i,'seat':s,'status':str(state.status)}
                      for i,frame in enumerate(env.steps) for s,state in enumerate(frame)
                      if state.status in {'ERROR','INVALID','TIMEOUT'}]
        candidate_timing=_timing_dict(candidate)
        row=dict(job,arm_sha256=arm_sha,opponent_sha256=opponent_sha,
            candidate_reward=own,opponent_reward=rival,margin=margin,
            result='win' if margin>0 else 'loss' if margin<0 else 'draw',
            frames=len(env.steps),candidate_status=str(final[seat].status),
            opponent_status=str(final[1-seat].status),wall_seconds=wall,
            candidate_timing=candidate_timing,opponent_timing=_timing_dict(opponent),
            candidate_capture=candidate.capture,candidate_telemetry=telemetry,
            opponent_telemetry=opponent_telemetry,candidate_errors=candidate_errors,
            opponent_errors=opponent_errors,bad_statuses=bad_statuses,
            activation_count=int(telemetry.get('melon_delivery_activated',0) or 0),
            seed_masked=True,environment_version=engine_version,
            explicit_configuration={'episodeSteps':720,'seed':job['seed']},
            native_stderr_events=[{'frame':i,'seat':s,'stderr':str(log.get('stderr',''))}
                for i,frame_logs in enumerate(env.logs) for s,log in enumerate(frame_logs)
                if str(log.get('stderr','')).strip()])
        row['clean']=(row['frames']==720 and row['candidate_status']==row['opponent_status']=='DONE'
                      and not bad_statuses and not candidate_errors and not opponent_errors)
        row['candidate_timing_pass']=(job['arm']!='treatment' or candidate_timing['max_ms']<1000)
        return row
    finally:
        for module in (candidate_module,opponent_module):
            sys.modules.pop(module.__name__,None)
        del candidate_module,opponent_module
        gc.collect()


def main():
    if sys.flags.optimize:
        raise SystemExit('Run without Python optimization; frozen safety assertions must remain enabled.')
    assert sha(CAND)==CAND_SHA and sha(BASE)==BASE_SHA
    assert engine_version=='1.32.7',engine_version
    frozen=json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert frozen['frozen_before_outcomes'] and frozen['outcomes_run'] is False
    assert frozen.get('reactive_seed_block')==list(SEEDS)
    frozen_opponents=frozen.get('reactive_opponents',{})
    assert set(frozen_opponents)==set(OPPONENTS)
    for name,(path,digest) in OPPONENTS.items():
        assert frozen_opponents[name]=={'path':str(path.relative_to(ROOT)),'sha256':digest}
    for entry in frozen['files'].values():
        p=ROOT/entry['path']
        assert sha(p)==entry['sha256'],str(p)
    panel=json.loads(PANEL_RECEIPT.read_text(encoding='utf-8'))
    assert panel['candidate_sha256']==CAND_SHA and panel['baseline_sha256']==BASE_SHA
    assert panel['schema']=='257f-melon-treatment-panel-v1' and panel['complete']
    assert sha(PANEL)==PANEL_SHA and panel['panel_sha256']==PANEL_SHA
    assert panel['plan_sha256']==sha(HERE/'PLAN.md')
    assert panel['frozen_manifest_sha256']==sha(MANIFEST)
    assert panel['census_sha256']==sha(CENSUS) and panel['prefix_sha256']==sha(PREFIX)
    assert panel['rows_path']==str(PANEL_ROWS.relative_to(ROOT)) and panel['rows_sha256']==sha(PANEL_ROWS)
    assert panel['fixed_tape_only'] and panel['research_promotion'] is False
    assert panel['all_rows_pass'] and panel['required_sweeps_pass'] and panel['clean_games']
    assert panel['action_parity_all_rows'] and panel['prior_results_preserved']
    assert panel['prior_telemetry_preserved'] and panel['same_observation_parent_telemetry_parity']
    assert panel['offhand_strict_margin_gate'] and panel['unknown_mother_goose_margin_gate']
    for name,(path,digest) in OPPONENTS.items(): assert sha(path)==digest,name
    jobs=[]
    for opponent_id in OPPONENTS:
        for seed in SEEDS:
            for seat in (0,1):
                for arm in ('incumbent','treatment'):
                    jobs.append(dict(index=len(jobs)+1,arm=arm,opponent_id=opponent_id,
                                     seed=seed,candidate_seat=seat))
    assert len(jobs)==32 and not ROWS.exists() and not RECEIPT.exists()
    rows=[]
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
      with exclusive_run(HERE/'reactive_run.lock'):
       with ROWS.open('x',encoding='utf-8') as output:
        for job in jobs:
            row=run_game(job);rows.append(row)
            output.write(json.dumps(row,ensure_ascii=True)+'\n');output.flush()
            print(json.dumps({'completed':len(rows),'planned':32,'arm':row['arm'],
                'opponent':row['opponent_id'],'seed':row['seed'],'seat':row['candidate_seat'],
                'result':row['result'],'margin':row['margin'],'activation_count':row['activation_count'],
                'clean':row['clean'],'candidate_max_ms':row['candidate_timing']['max_ms']},ensure_ascii=True),flush=True)
       indexed={(r['arm'],r['opponent_id'],int(r['seed']),int(r['candidate_seat'])):r for r in rows}
       assert len(indexed)==32
       pairs=[]
       for opponent_id in OPPONENTS:
        for seed in SEEDS:
         for seat in (0,1):
          base=indexed[('incumbent',opponent_id,seed,seat)]
          treatment=indexed[('treatment',opponent_id,seed,seat)]
          bp=1 if base['result']=='win' else .5 if base['result']=='draw' else 0
          tp=1 if treatment['result']=='win' else .5 if treatment['result']=='draw' else 0
          pairs.append(dict(opponent_id=opponent_id,seed=seed,candidate_seat=seat,
              incumbent_result=base['result'],treatment_result=treatment['result'],
              incumbent_margin=base['margin'],treatment_margin=treatment['margin'],
              paired_margin_delta=treatment['margin']-base['margin'],
              paired_points_delta=tp-bp,nonregression=tp>=bp))
       activation_count=sum(r['activation_count'] for r in rows if r['arm']=='treatment')
       all_clean=all(r['clean'] for r in rows)
       timing_pass=all(r['candidate_timing_pass'] for r in rows)
       no_result_regression=all(p['nonregression'] for p in pairs)
       aggregate_margin_delta=sum(p['paired_margin_delta'] for p in pairs)
       receipt=dict(schema='257f-melon-reactive-original-shop-v1',candidate_sha256=CAND_SHA,
          baseline_sha256=BASE_SHA,opponents={k:{'path':str(v[0].relative_to(ROOT)),
              'sha256':v[1]} for k,v in OPPONENTS.items()},seed_block=list(SEEDS),
          environment_version=engine_version,explicit_configuration={'episodeSteps':720},
          games=rows,pairs=pairs,complete=len(rows)==32,all_games_clean=all_clean,
          candidate_timing_under_1000ms=timing_pass,no_pairwise_wdl_regression=no_result_regression,
          aggregate_paired_margin_delta=aggregate_margin_delta,
          nonnegative_aggregate_margin=aggregate_margin_delta>=0,
          selector_activation_count=activation_count,
          inconclusive_no_activation=activation_count==0,
          fixed_seed_diagnostic_only=True,promotion=False,score_or_rank_not_estimated=True,
          saved_panel_receipt_sha256=sha(PANEL_RECEIPT),frozen_manifest_sha256=sha(MANIFEST),
          rows_sha256=sha(ROWS),passed=(len(rows)==32 and all_clean and timing_pass
              and no_result_regression and aggregate_margin_delta>=0 and activation_count>0))
       with RECEIPT.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=True,indent=2)
       print(json.dumps({k:v for k,v in receipt.items() if k not in ('games','pairs')},indent=2),flush=True)
       if not receipt['passed']:
        raise SystemExit('Reactive diagnostic did not clear its frozen screen; candidate remains experimental.')


if __name__=='__main__':main()
