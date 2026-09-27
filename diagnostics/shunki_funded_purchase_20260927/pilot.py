from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.shunki_planned_funding_20260927.native import play, point


if __name__=='__main__':
    manifest=json.loads((HERE/'build_manifest.json').read_text())
    gate=json.loads((HERE/'development.json').read_text())
    assert gate['complete'] and gate['passed'] and gate['candidate_sha256']==manifest['candidate_sha256']
    target=HERE/'pilot.json';assert not target.exists()
    seeds=list(range(2702000,2702008))
    jobs=[(manifest['candidate'],manifest['candidate_sha256'],'new','c68',
           'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad',seed,seat)
          for seed in seeds for seat in (0,1)]
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),candidate_sha256=manifest['candidate_sha256'],
             seeds=seeds,configuration_seed_masked=True,complete=False,games=[])
    def save():target.write_text(json.dumps(out,indent=2),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(play,j) for j in jobs]):
            g=f.result();out['games'].append(g)
            out['games'].sort(key=lambda g:(g['seed'],g['candidate_seat']));save()
            print(f"{len(out['games'])}/16 seed={g['seed']} seat={g['candidate_seat']} "
                  f"{g['result']} margin={g['margin']:+.0f} "
                  f"purchase={g['candidate_telemetry'].get('purchase_queue_turns',0)} "
                  f"funding={g['candidate_telemetry'].get('planned_funding_turns',0)}",flush=True)
    games=out['games'];points=sum(point(g) for g in games)
    active={g['seed'] for g in games if g['candidate_telemetry'].get('purchase_queue_turns',0)>0}
    all_done=all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in games)
    errors=sum(sum(g['candidate_errors'].values())+sum(g['opponent_errors'].values()) for g in games)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),points=points,
               wins=sum(g['result']=='win' for g in games),losses=sum(g['result']=='loss' for g in games),
               draws=sum(g['result']=='draw' for g in games),active_purchase_pairs=sorted(active),
               all_done=all_done,errors=errors,passed=points>=12 and len(active)>=6 and all_done and errors==0)
    save();print('RESULT '+json.dumps({k:v for k,v in out.items() if k!='games'}),flush=True)
