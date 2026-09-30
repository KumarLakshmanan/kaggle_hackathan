from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.shunki_planned_funding_20260927.native import play, point, RIVALS, OLD


if __name__=='__main__':
    manifest=json.loads((HERE/'build_manifest.json').read_text())
    gate=json.loads((HERE/'panels.json').read_text())
    assert gate['complete'] and gate['passed'] and gate['candidate_sha256']==manifest['candidate_sha256']
    assert hashlib.sha256((HERE/'PLAN.md').read_bytes()).hexdigest()==manifest['plan_sha256']
    target=HERE/'confirmation.json';assert not target.exists()
    seeds=list(range(2709000,2709016))
    hashes={k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in RIVALS.items()}
    assert hashes['c68']==manifest['source_sha256']
    versions={'old':(str(OLD),hashes['c68']),'new':(manifest['candidate'],manifest['candidate_sha256'])}
    jobs=[(p,h,v,r,hashes[r],seed,seat) for seed in seeds for r in RIVALS for v,(p,h) in versions.items() for seat in (0,1)]
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),candidate_sha256=manifest['candidate_sha256'],
             plan_sha256=manifest['plan_sha256'],seeds=seeds,reference_hashes=hashes,configuration_seed_masked=True,complete=False,games=[])
    def save():target.write_text(json.dumps(out,indent=2),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(play,j) for j in jobs]):
            g=f.result();out['games'].append(g);save()
            print(f"{len(out['games'])}/256 {g['version']} vs{g['rival']} seed={g['seed']} seat={g['candidate_seat']} {g['result']} {g['margin']:+.0f}",flush=True)
    games=out['games']
    scores={r:{v:sum(point(g) for g in games if g['rival']==r and g['version']==v) for v in versions} for r in RIVALS}
    deltas=[sum(point(g)*(1 if g['version']=='new' else -1) for g in games if g['seed']==s)/8 for s in seeds]
    rng=random.Random(2709099)
    boots=sorted(statistics.fmean(rng.choices(deltas,k=len(deltas))) for _ in range(10000))
    ci=[boots[250],boots[9749]]
    all_done=all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in games)
    errors=sum(sum(g['candidate_errors'].values())+sum(g['opponent_errors'].values()) for g in games)
    nonregression=all(s['new']>=s['old'] for s in scores.values())
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),scores=scores,
               paired_seed_win_point_deltas=deltas,paired_seed_bootstrap_95=ci,all_done=all_done,errors=errors,
               reference_nonregression=nonregression,
               passed=all_done and errors==0 and nonregression and scores['c68']['new']>=24 and ci[0]>0)
    save();print('RESULT '+json.dumps({k:v for k,v in out.items() if k!='games'}),flush=True)
