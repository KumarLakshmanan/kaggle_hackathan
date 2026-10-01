"""Verify candidate actions, native rewards, and Kaggle file loader in both seats."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from kaggriculture_engine.build_agent import sha
from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.fresh90_loss_audit_20260929.verify_combined_v2_operational import run_loader_one

def main():
    candidate=HERE/'candidate_v1.py';baseline=HERE/'baseline_4eeac9c3.py'
    manifest=json.loads(candidate.with_suffix('.manifest.json').read_text())
    assert sha(candidate)==manifest['candidate_sha256'] and sha(baseline)==manifest['baseline_sha256']
    from kaggle_environments.agent import get_last_callable
    entrypoint=get_last_callable(candidate.read_text(encoding='utf-8'),path=str(candidate)).__name__
    assert entrypoint==manifest['expected_entrypoint']
    pilot=[json.loads(s) for s in (HERE/'pilot_results.jsonl').read_text().splitlines()]
    selected={r['candidate_seat']:r for r in pilot if r['version']=='candidate' and r['seed']==33000001 and r['rival']=='4ee'}
    assert set(selected)=={0,1}
    rows=[];parity=[]
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        for seat in (0,1):
            pair=[]
            for mode in ('direct','file'):
                row=run_loader_one(candidate,baseline,33000001,seat,mode)
                expected=[selected[seat]['candidate_reward'],selected[seat]['opponent_reward']] if seat==0 else [selected[seat]['opponent_reward'],selected[seat]['candidate_reward']]
                row['fast_native_reward_match']=row['rewards']==expected
                row['passed']=row['passed'] and row['fast_native_reward_match']
                rows.append(row);pair.append(row)
                (HERE/'loader_progress.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
                print(json.dumps(dict(seat=seat,mode=mode,passed=row['passed'],rewards=row['rewards'],remaining=row['minimum_remaining_overage'])),flush=True)
            match=all(pair[0][field]==pair[1][field] for field in ('rewards','statuses','candidate_action_sha256','joint_action_sha256'))
            parity.append(dict(seat=seat,match=match))
        result=dict(passed=all(row['passed'] for row in rows) and all(p['match'] for p in parity),candidate_sha256=sha(candidate),
                    entrypoint=entrypoint,rows=rows,parity=parity,completed_at_utc=datetime.now(timezone.utc).isoformat())
        (HERE/'loader_receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    assert result['passed']
    print('Native/file loader parity passed in both seats.',flush=True)

if __name__=='__main__':main()
