from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from paired_benchmark import run_game

OLD=ROOT/'main_uploaded_disjoint_integrated_20260927_c68fa46f.py'


def play(job):
    path,digest,version,record,seat=job
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    g=run_game(path,'rawroute:'+record['route'],record['seed'],seat,False,144,{})
    return dict(version=version,episode_id=record['episode_id'],opponent=record['opponent'],provenance='new_native_tape_run',**g)


if __name__=='__main__':
    manifest=json.loads((HERE/'build_manifest.json').read_text())
    assert hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest()==manifest['plan_sha256']
    assert hashlib.sha256(OLD.read_bytes()).hexdigest()==manifest['source_sha256']
    target=HERE/'development.json';assert not target.exists()
    records=[];reused=[];source_hashes={}
    for folder in ('disjoint_live_top100_cash_20260927','disjoint_live_cash_1022_20260927'):
        source=ROOT/'diagnostics'/folder/'ledger.json'
        ledger=json.loads(source.read_text());assert ledger['complete']
        source_hashes[str(source)]=hashlib.sha256(source.read_bytes()).hexdigest()
        for g in ledger['games']:
            assert g['source_cash_parity'] and g['all_719_source_actions_match']
            raw=gzip.decompress(Path(g['trace_path']).read_bytes())
            assert hashlib.sha256(raw).hexdigest()==g['trace_sha256']
            trace=json.loads(raw);assert trace['engine_version']=='1.32.7'
            route=ROOT/'diagnostics'/folder/'routes'/f"{g['episode_id']}.json.gz"
            assert route.exists()
            record=dict(episode_id=g['episode_id'],opponent=g['opponent'],seed=trace['seed'],
                        original_seat=g['candidate_seat'],route=str(route))
            records.append(record)
            margin=g['margin']
            reused.append(dict(version='old',episode_id=g['episode_id'],opponent=g['opponent'],seed=trace['seed'],
                               candidate_seat=g['candidate_seat'],candidate_reward=trace['candidate_reward'],
                               opponent_reward=trace['opponent_reward'],margin=margin,
                               result='win' if margin>0 else 'loss' if margin<0 else 'draw',
                               candidate_status=trace['candidate_status'],opponent_status=trace['opponent_status'],frames=720,
                               candidate_telemetry={},provenance='reused_verified_cash_and_action_parity_trace',
                               source_trace_sha256=g['trace_sha256']))
    assert len(records)==len(reused)==9
    jobs=[]
    for r in records:
        jobs.append((str(OLD),manifest['source_sha256'],'old',r,1-r['original_seat']))
        jobs.extend((manifest['candidate'],manifest['candidate_sha256'],'new',r,seat) for seat in (0,1))
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),complete=False,candidate_sha256=manifest['candidate_sha256'],
             plan_sha256=manifest['plan_sha256'],source_ledger_hashes=source_hashes,records=records,
             reused_old_original_seat_games=9,planned_new_games=27,games=reused)
    def save():target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(play,j) for j in jobs]):
            g=f.result();out['games'].append(g);save()
            s=g.get('candidate_telemetry') or {}
            print(f"{len(out['games'])}/36 {g['version']} {g['opponent']} seat={g['candidate_seat']} "
                  f"{g['result']} {g['margin']:+.0f} active={s.get('aux_started',0)} "
                  f"plant/harvest/drop={s.get('aux_planted',0)}/{s.get('aux_harvested',0)}/{s.get('aux_dropped',0)} "
                  f"errors={s.get('aux_errors',0)}",flush=True)
    new=[g for g in out['games'] if g['version']=='new']
    old={(g['episode_id'],g['candidate_seat']):g for g in out['games'] if g['version']=='old'}
    lost=[dict(episode_id=g['episode_id'],seat=g['candidate_seat'],old_margin=old[g['episode_id'],g['candidate_seat']]['margin'],new_margin=g['margin'])
          for g in new if old[g['episode_id'],g['candidate_seat']]['result']=='win' and g['result']!='win']
    gained=[dict(episode_id=g['episode_id'],seat=g['candidate_seat'],old_margin=old[g['episode_id'],g['candidate_seat']]['margin'],new_margin=g['margin'])
            for g in new if old[g['episode_id'],g['candidate_seat']]['result']=='loss' and g['result']=='win']
    active=[g for g in new if (g.get('candidate_telemetry') or {}).get('aux_started')]
    active_pairs=[r['episode_id'] for r in records if len([g for g in active if g['episode_id']==r['episode_id']])==2]
    errors=[dict(episode_id=g['episode_id'],seat=g['candidate_seat'],key=k,value=v) for g in new
            for k,v in (g.get('candidate_telemetry') or {}).items() if isinstance(v,(int,float)) and v and ('error' in k.lower() or 'collision' in k.lower())]
    production=all((g['candidate_telemetry'].get('aux_planted'),g['candidate_telemetry'].get('aux_harvested'),g['candidate_telemetry'].get('aux_dropped'))==(12,48,48) for g in active)
    all_done=all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in out['games'])
    scores={v:dict(wins=sum(g['result']=='win' for g in out['games'] if g['version']==v),
                   draws=sum(g['result']=='draw' for g in out['games'] if g['version']==v),
                   losses=sum(g['result']=='loss' for g in out['games'] if g['version']==v)) for v in ('old','new')}
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),scores=scores,lost_winning_seats=lost,
               gained_winning_seats=gained,activated_pairs=active_pairs,all_activated_production_complete=production,
               all_done=all_done,errors=errors,passed=not lost and bool(gained) and len(active_pairs)>=2 and production and all_done and not errors)
    save();print('RESULT '+json.dumps({k:v for k,v in out.items() if k not in ('games','records')}),flush=True)
