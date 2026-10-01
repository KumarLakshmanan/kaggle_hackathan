"""Fresh paired development and conditional native validation of frozen v3."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; sys.path.insert(0,str(ROOT))
from diagnostics.executable_engine_20260930.run_experiment import execute
from diagnostics.professional_engine_20261001.run_experiment import assess
from diagnostics.local_target_20260928.run_lock import exclusive_run

BASE = ROOT/'diagnostics/professional_engine_20261001/candidate_market.py'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v): Path(p).write_text(json.dumps(v,indent=2),encoding='utf-8')


def build_jobs(phase,candidate):
    versions = {'baseline':BASE}
    if phase == 'screen':
        versions.update(wide=HERE/'candidate_wide_r3.py',guard=HERE/'candidate_guard_r3.py')
    else: versions['candidate'] = Path(candidate)
    refs = {'4ea':BASE,'bbff':ROOT/'diagnostics/professional_engine_20261001/baseline_main_bbffbe65.py',
        'v35':ROOT/'diagnostics/public_ahmed_v35_20260927/public_v35_main.py',
        'c95':ROOT/'diagnostics/public_rayk_top_meta/public_c95_main.py'}
    jobs = []
    if phase in ('top20','top100'):
        source = json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
        for fixture in source:
            if fixture['rank'] > (20 if phase == 'top20' else 100): continue
            for version,path in versions.items():
                jobs.append(dict(fixture,kind='replay',job_id=f'{version}:{fixture["fixture_id"]}:{fixture["candidate_seat"]}',
                    version=version,rival=fixture['team'],path=str(path),candidate_sha256=sha(path)))
    else:
        seeds = range(35000001,35000005) if phase == 'screen' else range(35000101,35000117)
        for seed in seeds:
            for rival,opponent in refs.items():
                for seat in (0,1):
                    for version,path in versions.items():
                        jobs.append(dict(job_id=f'{version}:{seed}:{rival}:{seat}',kind='reactive' if phase == 'screen' else 'native',
                            version=version,rival=rival,seed=seed,candidate_seat=seat,path=str(path),candidate_sha256=sha(path),
                            opponent=str(opponent),opponent_sha256=sha(opponent)))
    return jobs


def main():
    p = argparse.ArgumentParser(); p.add_argument('phase',choices=('screen','top20','top100','confirm'))
    p.add_argument('--candidate',type=Path); p.add_argument('--workers',type=int,default=4); args=p.parse_args()
    assert 1 <= args.workers <= 6
    assert sha(BASE) == '4ea1d89ac99758c6219bcd7d07b729de4dc5836260a25037ca973343b46c6289'
    assert json.loads((HERE/'engineering_receipt.json').read_text())['passed']
    assert json.loads((HERE/'parent_parity_receipt.json').read_text())['passed']
    assert json.loads((HERE/'funding_parity_receipt.json').read_text())['passed']
    if args.phase != 'screen':
        screen=json.loads((HERE/'screen_receipt.json').read_text()); survivor=screen['assessment']['screen_survivor']
        assert screen['complete'] and survivor is not None and sha(args.candidate)==screen['candidate_hashes'][survivor]
    if args.phase=='confirm':
        for phase in ('top20','top100'):
            receipt=json.loads((HERE/f'{phase}_receipt.json').read_text())
            assert receipt['complete'] and receipt['assessment']['decisions']['candidate']['replay_passed']
        loader=json.loads((HERE/'loader_receipt.json').read_text()); assert loader['passed'] and loader['candidate_sha256']==sha(args.candidate)
    paths=[HERE/'candidate_wide_r3.py',HERE/'candidate_guard_r3.py'] if args.phase=='screen' else [args.candidate]
    for path in paths:
        manifest=json.loads(Path(path).with_suffix('.manifest.json').read_text()); assert sha(path)==manifest['candidate_sha256']
        for source,digest in manifest['source_hashes'].items(): assert sha(source)==digest
    jobs=build_jobs(args.phase,args.candidate); freeze=HERE/f'{args.phase}_jobs.json'
    if freeze.exists(): assert json.loads(freeze.read_text())==jobs
    else: write(freeze,jobs)
    hashes={str(path):sha(path) for path in (Path(__file__),ROOT/'diagnostics/executable_engine_20260930/run_experiment.py',
        ROOT/'diagnostics/professional_engine_20261001/run_experiment.py',ROOT/'diagnostics/physical_route_rollout_20260928/fast_reactive.py',
        ROOT/'diagnostics/opening_probe_v2_20260928/qualify.py')}
    ledger=HERE/f'{args.phase}_results.jsonl'; receipt_path=HERE/f'{args.phase}_receipt.json'
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        rows=[json.loads(s) for s in ledger.read_text().splitlines()] if ledger.exists() else []
        lookup={j['job_id']:j for j in jobs}; done={r['job_id'] for r in rows}; assert len(done)==len(rows)
        for row in rows: assert row['candidate_sha256']==lookup[row['job_id']]['candidate_sha256']
        if receipt_path.exists(): assert json.loads(receipt_path.read_text())['source_hashes']==hashes
        if args.phase=='top100' and not ledger.exists():
            rows=[json.loads(s) for s in (HERE/'top20_results.jsonl').read_text().splitlines()];done={r['job_id'] for r in rows}
            ledger.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
        # Reuse exact completed old candidate saved controls; these are tapes,
        # not independent reacting runs. Source, seat and fixture must match.
        if args.phase in ('top20','top100'):
            prior=ROOT/f'diagnostics/professional_engine_20261001/{args.phase}_results.jsonl'
            for s in prior.read_text().splitlines():
                row=json.loads(s)
                if row['version']!='candidate': continue
                key=f'baseline:{row["fixture_id"]}:{row["candidate_seat"]}'
                if key in done: continue
                assert row['candidate_sha256']==sha(BASE)==lookup[key]['candidate_sha256']
                row=dict(row,version='baseline',job_id=key,reused_control=True)
                rows.append(row);done.add(key)
            ledger.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
        receipt={'complete':False,'started_at_utc':datetime.now(timezone.utc).isoformat(),'planned_games':len(jobs),
            'source_hashes':hashes,'candidate_hashes':{v:sha(next(j['path'] for j in jobs if j['version']==v)) for v in {j['version'] for j in jobs}},
            'jobs_sha256':sha(freeze)}
        write(receipt_path,receipt)
        with ledger.open('a',encoding='utf-8') as out:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                pending={pool.submit(execute,j):j for j in jobs if j['job_id'] not in done}
                for future in as_completed(pending):
                    row=future.result();rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
                    print(f'{len(rows)}/{len(jobs)} {row["job_id"]} {row.get("result",row.get("error_type"))}',flush=True)
        assessment=assess(rows)
        passing=[v for v,d in assessment['decisions'].items() if d['screen_passed']]
        if args.phase=='screen':
            assessment['screen_survivor']=max(passing,key=lambda v:(assessment['groups'][v]['points'],assessment['groups'][v]['mean_margin'],v=='wide')) if passing else None
        receipt.update(complete=len(rows)==len(jobs),completed_at_utc=datetime.now(timezone.utc).isoformat(),
            results_sha256=sha(ledger),assessment=assessment);write(receipt_path,receipt)
        print(json.dumps(receipt['assessment'],indent=2),flush=True)


if __name__=='__main__':main()
