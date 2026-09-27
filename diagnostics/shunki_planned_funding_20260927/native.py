from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT))
from paired_benchmark import _load_module, TimedAgent, _timing_dict, make, engine_version

OLD = ROOT/'main_uploaded_disjoint_integrated_20260927_c68fa46f.py'
RIVALS = {
    'c68': OLD,
    '1f': ROOT/'exp_shunki_visible_repair_20260927.py',
    '489': ROOT/'main_uploaded_mirror_straw24_20260926_489fe8e4.py',
    'C95': ROOT/'diagnostics/public_rayk_top_meta/public_c95_main.py',
}


def errors(module):
    found={}
    for name,value in vars(module).items():
        if isinstance(value,dict) and ('STATS' in name or 'REPORT' in name):
            for key,count in value.items():
                if isinstance(key,str) and ('error' in key.lower() or 'collision' in key.lower()) and isinstance(count,(int,float)):
                    if count:found[name+'.'+key]=count
    return found


def play(job):
    path,digest,version,rival,rival_digest,seed,seat=job
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    assert hashlib.sha256(RIVALS[rival].read_bytes()).hexdigest()==rival_digest
    candidate=_load_module(Path(path),'funding_native_candidate')
    opponent=_load_module(RIVALS[rival],'funding_native_rival')
    def candidate_call(obs,cfg):
        visible=dict(cfg);visible['seed']=None
        return candidate.agent(obs,visible)
    def opponent_call(obs,cfg):
        visible=dict(cfg);visible['seed']=None
        return opponent.agent(obs,visible)
    c=TimedAgent(candidate_call,capture_step=144)
    o=TimedAgent(opponent_call)
    try:
        started=time.perf_counter()
        env=make('kaggriculture',configuration={'episodeSteps':720,'seed':seed},debug=False)
        env.run([c,o] if seat==0 else [o,c])
        last=env.steps[-1]
        own,other=float(last[seat].reward or 0),float(last[1-seat].reward or 0)
        margin=own-other
        return dict(version=version,rival=rival,seed=seed,candidate_seat=seat,
                    candidate_reward=own,opponent_reward=other,margin=margin,
                    result='win' if margin>0 else 'loss' if margin<0 else 'draw',
                    candidate_status=last[seat].status,opponent_status=last[1-seat].status,
                    frames=len(env.steps),wall_seconds=time.perf_counter()-started,
                    candidate_timing=_timing_dict(c),opponent_timing=_timing_dict(o),
                    candidate_capture=c.capture,candidate_telemetry=dict(getattr(candidate.agent,'telemetry',{}) or {}),
                    candidate_errors=errors(candidate),opponent_errors=errors(opponent),configuration_seed_visible=None)
    finally:
        sys.modules.pop(candidate.__name__,None)
        sys.modules.pop(opponent.__name__,None)


def point(g):
    return 1.0 if g['result']=='win' else .5 if g['result']=='draw' else 0.0


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('screening','confirmation'))
    args=parser.parse_args()
    manifest=json.loads((HERE/'build_manifest.json').read_text())
    preceding='development.json' if args.phase=='screening' else 'panels.json'
    gate=json.loads((HERE/preceding).read_text())
    assert gate['complete'] and gate['passed'] and gate['candidate_sha256']==manifest['candidate_sha256']
    output=HERE/(args.phase+'.json')
    assert not output.exists()
    seeds=list(range(2700000,2700008) if args.phase=='screening' else range(2701000,2701016))
    hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in RIVALS.items()}
    assert hashes['c68']=='c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'
    versions={'old':(str(OLD),hashes['c68']),'new':(manifest['candidate'],manifest['candidate_sha256'])}
    jobs=[(path,digest,version,rival,hashes[rival],seed,seat)
          for seed in seeds for rival in RIVALS for version,(path,digest) in versions.items() for seat in (0,1)]
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),phase=args.phase,
             candidate_sha256=manifest['candidate_sha256'],rival_hashes=hashes,
             seeds=seeds,engine_version=engine_version,configuration_seed_masked=True,complete=False,games=[])
    def save():
        output.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play,j) for j in jobs]):
            row=future.result();out['games'].append(row)
            out['games'].sort(key=lambda g:(g['seed'],g['rival'],g['version'],g['candidate_seat']))
            save()
            print(f"{len(out['games'])}/{len(jobs)} {row['version']} vs {row['rival']} seed={row['seed']} "
                  f"seat={row['candidate_seat']} {row['result']} {row['margin']:+.0f} "
                  f"active={row['candidate_telemetry'].get('planned_funding_turns',0)}",flush=True)
    games=out['games']
    scores={r:{v:sum(point(g) for g in games if g['rival']==r and g['version']==v) for v in versions} for r in RIVALS}
    active={(g['seed'],g['rival']) for g in games if g['version']=='new' and g['candidate_telemetry'].get('planned_funding_turns',0)>0}
    references={r for s,r in active}
    all_done=all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in games)
    error_count=sum(sum(g['candidate_errors'].values())+sum(g['opponent_errors'].values()) for g in games)
    deltas=[sum(point(g)*(1 if g['version']=='new' else -1) for g in games if g['seed']==seed)/8 for seed in seeds]
    nonregression=all(s['new']>=s['old'] for s in scores.values())
    passed=all_done and error_count==0 and len(references)>=2 and nonregression and sum(deltas)>0
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),scores=scores,
               all_done=all_done,errors=error_count,activated_pairs=[list(v) for v in sorted(active)],
               activated_references=sorted(references),seed_win_point_deltas=deltas,reference_nonregression=nonregression)
    if args.phase=='screening':
        passed=passed and len(active)>=4
    else:
        rng=random.Random(2701099)
        boots=sorted(statistics.fmean(rng.choices(deltas,k=len(deltas))) for _ in range(10000))
        ci=[boots[250],boots[9749]]
        out['paired_seed_bootstrap_95']=ci
        passed=passed and len(active)>=8 and ci[0]>0
    out['passed']=bool(passed)
    save()
    print('RESULT '+json.dumps({k:v for k,v in out.items() if k!='games'}),flush=True)
