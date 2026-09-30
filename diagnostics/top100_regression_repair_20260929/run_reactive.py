"""Prospectively frozen multi-policy reacting screen and native confirmation."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIOR=ROOT/'diagnostics/submission_top100_compare_20260929_1104'
sys.path.insert(0,str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def points(row): return {'win':1.0,'draw':0.5,'loss':0.0}[row['result']]

def execute(job):
    try:
        if job['method']=='native':
            from diagnostics.opening_probe_v2_20260928.qualify import play
        else:
            from diagnostics.physical_route_rollout_20260928.fast_reactive import play
        return play(job)
    except Exception as error:
        return dict(job,error_type=type(error).__name__,error=str(error))

def make_jobs(manifest,stage):
    opponents={
        '4ee':PRIOR/'downloaded/main_4eeac9c3.py',
        'ae349':PRIOR/'downloaded/main_ae349d83.py',
        'v35':ROOT/'diagnostics/public_ahmed_v35_20260927/public_v35_main.py',
        'c95':ROOT/'diagnostics/public_rayk_top_meta/public_c95_main.py',
    }
    versions={'candidate':Path(manifest['candidate']),'4ee':Path(manifest['baseline'])}
    seeds=range(12929001,12929009) if stage=='screen' else range(12929101,12929117)
    jobs=[]
    for seed in seeds:
        for rival,opponent in opponents.items():
            for seat in (0,1):
                for version,path in versions.items():
                    jobs.append(dict(job_id=f'{seed}:{rival}:{seat}:{version}',version=version,
                        rival=rival,opponent_id=rival,seed=seed,candidate_seat=seat,
                        path=str(path),candidate_sha256=sha(path),opponent=str(opponent),
                        opponent_sha256=sha(opponent),method='fast_native_transitions' if stage=='screen' else 'native',
                        configuration_seed_visible=None,original_shop_seeded_episode=True,fixed_tape=False))
    return jobs

def assess(rows,stage):
    clean=all(not r.get('error') and not r.get('candidate_errors') and not r.get('opponent_errors')
              and r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' for r in rows)
    per_opponent={}
    for rival in sorted({r['rival'] for r in rows}):
        block={}
        for version in ('candidate','4ee'):
            chosen=[r for r in rows if r['rival']==rival and r['version']==version]
            block[version]=dict(games=len(chosen),points=sum(points(r) for r in chosen),
                wdl={k:sum(r['result']==k for r in chosen) for k in ('win','draw','loss')},
                mean_margin=sum(r['margin'] for r in chosen)/len(chosen))
        block['delta']=block['candidate']['points']-block['4ee']['points']
        per_opponent[rival]=block
    seed_deltas=[]
    for seed in sorted({r['seed'] for r in rows}):
        totals={v:sum(points(r) for r in rows if r['seed']==seed and r['version']==v) for v in ('candidate','4ee')}
        seed_deltas.append(dict(seed=seed,**totals,delta=totals['candidate']-totals['4ee']))
    deltas=[s['delta'] for s in seed_deltas]
    rng=random.Random(29092026)
    draws=sorted(sum(rng.choice(deltas) for _ in deltas)/(len(deltas)*8) for _ in range(10000))
    interval=[draws[249],draws[9749]]
    checks={'all_clean':clean,'no_per_opponent_point_regression':all(x['delta']>=0 for x in per_opponent.values()),
            'positive_total_point_delta':sum(deltas)>0}
    if stage=='screen': checks['six_of_eight_nonnegative_seed_deltas']=sum(d>=0 for d in deltas)>=6
    else: checks['positive_95pct_whole_seed_bootstrap_lower_bound']=interval[0]>0
    return dict(per_opponent=per_opponent,seed_deltas=seed_deltas,total_point_delta=sum(deltas),
                paired_win_point_rate_delta=sum(deltas)/(len(deltas)*8),
                paired_whole_seed_bootstrap_95pct=interval,checks=checks,passed=all(checks.values()))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('version');parser.add_argument('stage',choices=('screen','confirm'))
    args=parser.parse_args()
    manifest=json.loads((HERE/f'manifest_{args.version}.json').read_text())
    assert sha(manifest['candidate'])==manifest['candidate_sha256']
    saved=json.loads((HERE/f'saved_{args.version}_full_receipt.json').read_text())
    assert saved['regression_gate_passed']
    if args.stage=='confirm':
        assert json.loads((HERE/f'reactive_{args.version}_screen_receipt.json').read_text())['assessment']['passed']
        assert json.loads((HERE/f'native_checks_{args.version}_receipt.json').read_text())['passed']
        assert json.loads((HERE/f'loader_{args.version}.json').read_text())['passed']
    jobs=make_jobs(manifest,args.stage)
    freeze=HERE/f'reactive_{args.version}_{args.stage}_jobs.json'
    if freeze.exists(): assert json.loads(freeze.read_text())==jobs
    else: freeze.write_text(json.dumps(jobs,indent=2),encoding='utf-8')
    path=HERE/f'reactive_{args.version}_{args.stage}.jsonl'
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        rows=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
        byid={r['job_id']:r for r in rows}
        assert len(rows)==len(byid)
        jobmap={j['job_id']:j for j in jobs}
        assert all(all(r[k]==jobmap[r['job_id']][k] for k in ('candidate_sha256','opponent_sha256','method')) for r in rows)
        started=datetime.now(timezone.utc).isoformat()
        with path.open('a',encoding='utf-8',newline='\n') as stream:
            with ProcessPoolExecutor(max_workers=6 if args.stage=='confirm' else 4) as pool:
                pending={pool.submit(execute,j):j for j in jobs if j['job_id'] not in byid}
                for future in as_completed(pending):
                    row=future.result();rows.append(row)
                    stream.write(json.dumps(row,ensure_ascii=True)+'\n');stream.flush()
                    if len(rows)%8==0: print(f"{len(rows)}/{len(jobs)} {row['job_id']} {row.get('result',row.get('error_type'))}",flush=True)
        assert len(rows)==len(jobs)
        if any(r.get('error') for r in rows):
            assessment={'passed':False,'errors':[r for r in rows if r.get('error')]}
        else: assessment=assess(rows,args.stage)
        receipt=dict(complete=True,started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),
            candidate_sha256=manifest['candidate_sha256'],jobs_sha256=sha(freeze),
            results_sha256=sha(path),games=len(rows),stage=args.stage,
            workers=6 if args.stage=='confirm' else 4,assessment=assessment)
        (HERE/f'reactive_{args.version}_{args.stage}_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        print(json.dumps(assessment,indent=2),flush=True)

if __name__=='__main__':main()
