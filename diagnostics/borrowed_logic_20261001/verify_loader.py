"""Exact direct/file framework actions and fast-native reward parity."""
import argparse
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.fresh90_loss_audit_20260929.verify_combined_v2_operational import run_loader_one
from run_experiment import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);args=p.parse_args()
    candidate=args.candidate.resolve();digest=sha(candidate)
    from kaggle_environments.agent import get_last_callable
    entry=get_last_callable(candidate.read_text(),path=str(candidate)).__name__
    assert entry=='kaggle_borrowed_logic_entrypoint'
    selected={};seed=None
    for phase in ('joint','screen'):
        ledger=HERE/f'{phase}_results.jsonl'
        if not ledger.exists():continue
        found=[json.loads(s) for s in ledger.read_text().splitlines()]
        found=[r for r in found if r['candidate_sha256']==digest and r['rival']=='bbff']
        if found:
            seed=min(r['seed'] for r in found);selected={r['candidate_seat']:r for r in found if r['seed']==seed};break
    assert set(selected)=={0,1}
    rows=[];parity=[]
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        for seat in (0,1):
            pair=[]
            for mode in ('direct','file'):
                row=run_loader_one(candidate,HERE/'baseline_bbffbe65.py',seed,seat,mode)
                expected=[selected[seat]['candidate_reward'],selected[seat]['opponent_reward']]
                if seat==1:expected.reverse()
                row['fast_native_reward_match']=row['rewards']==expected
                row['passed'] &= row['fast_native_reward_match'];rows.append(row);pair.append(row)
                (HERE/'loader_progress.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
                print(json.dumps({'seat':seat,'mode':mode,'passed':row['passed'],'rewards':row['rewards']}),flush=True)
            parity.append({'seat':seat,'match':all(pair[0][k]==pair[1][k] for k in ('rewards','statuses','candidate_action_sha256','joint_action_sha256'))})
    receipt={'candidate_sha256':digest,'entrypoint':entry,'seed':seed,'rows':rows,'parity':parity,
        'passed':all(r['passed'] for r in rows) and all(p['match'] for p in parity),'completed_at_utc':datetime.now(timezone.utc).isoformat()}
    (HERE/'loader_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');assert receipt['passed']

if __name__=='__main__':main()
