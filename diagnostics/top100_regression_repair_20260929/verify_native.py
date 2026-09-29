"""Native framework parity on repaired targets and fresh reacting scenarios."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
PRIOR=ROOT/'diagnostics/submission_top100_compare_20260929_1104'
sys.path.insert(0,str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def execute(job):
    from diagnostics.opening_probe_v2_20260928.qualify import play
    expected=job['expected']
    actual=play({key:value for key,value in job.items() if key!='expected'})
    fields=('candidate_reward','opponent_reward','result','frames','candidate_status','opponent_status','candidate_telemetry')
    actual['mismatches']=[k for k in fields if actual[k]!=expected[k]]
    actual['passed']=not actual['mismatches'] and not actual['candidate_errors'] and not actual['opponent_errors']
    actual.pop('expected',None)
    return actual

def main():
    parser=argparse.ArgumentParser();parser.add_argument('version');args=parser.parse_args()
    manifest=json.loads((HERE/f'manifest_{args.version}.json').read_text())
    assert sha(manifest['candidate'])==manifest['candidate_sha256']
    assert json.loads((HERE/f'saved_{args.version}_full_receipt.json').read_text())['regression_gate_passed']
    saved=[json.loads(s) for s in (HERE/f'saved_{args.version}.jsonl').read_text().splitlines()]
    entries={e['rank']:e for e in json.loads((PRIOR/'routes/summary.json').read_text(encoding='utf-8'))}
    jobs=[]
    for row in saved:
        if row['rank'] not in (5,7,25):continue
        e=entries[row['rank']]
        jobs.append(dict(job_id=f"saved:{row['rank']}:{row['candidate_seat']}",
            path=manifest['candidate'],candidate_sha256=manifest['candidate_sha256'],
            opponent='rawroute:'+e['path'],opponent_action_sha256=e['action_sha256'],
            seed=e['seed'],candidate_seat=row['candidate_seat'],expected=row))
    reactive=[json.loads(s) for s in (HERE/f'reactive_{args.version}_screen.jsonl').read_text().splitlines()]
    for row in reactive:
        if row['seed']==12929001 and row['rival'] in ('4ee','v35'):
            jobs.append({**{k:row[k] for k in ('job_id','path','candidate_sha256','opponent','opponent_sha256','seed','candidate_seat')},'expected':row})
    assert len(jobs)==14
    path=HERE/f'native_checks_{args.version}.jsonl'
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        rows=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
        done={r['job_id'] for r in rows}
        with path.open('a',encoding='utf-8',newline='\n') as stream:
            with ProcessPoolExecutor(max_workers=4) as pool:
                pending={pool.submit(execute,j):j for j in jobs if j['job_id'] not in done}
                for future in as_completed(pending):
                    row=future.result();rows.append(row)
                    stream.write(json.dumps(row,ensure_ascii=True)+'\n');stream.flush()
                    print(row['job_id'],row['passed'],row['mismatches'],flush=True)
        receipt=dict(complete=True,games=len(rows),passed=len(rows)==14 and all(r['passed'] for r in rows),
            candidate_sha256=manifest['candidate_sha256'],results_sha256=sha(path),
            completed_at_utc=datetime.now(timezone.utc).isoformat())
        (HERE/f'native_checks_{args.version}_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        print(json.dumps(receipt,indent=2),flush=True)

if __name__=='__main__':main()
