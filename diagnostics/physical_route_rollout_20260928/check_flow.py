"""Compare legal-observation inference to independent private-ledger truth."""
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928.observable_flow import infer_rival_net_sales,post_worker_private
from diagnostics.physical_route_rollout_20260928.check import sha


def legal_observation(frame,seat):
    public={key:frame[0]['observation'][key] for key in ('farms','market','town','day','hour','step')}
    return dict(public,player=seat,private=frame[seat]['observation']['private'])


def main():
    parity=json.loads((HERE/'parity.json').read_text(encoding='utf-8'))
    assert parity['complete'] and parity['passed']
    assert sha(HERE/'native_core.py')==parity['extracted_source_sha256']
    manifest_path=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
    assert sha(manifest_path)=='524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    fixtures={f['fixture_id']:f for f in manifest['live_losses']+manifest['current_top20']}
    rows=[]
    for prior in parity['fixtures']:
        fixture=fixtures[prior['fixture_id']]
        raw=gzip.decompress(Path(fixture['source_replay_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==prior['source_replay_sha256']
        replay=json.loads(raw);del raw
        cfg=dict(replay['configuration']);cfg['seed']=None
        for seat in (0,1):
            checked=skipped=active=known=censored=0;mismatch=None
            started=time.perf_counter()
            for step in range(719):
                frame,next_frame=replay['steps'][step:step+2]
                before,after=legal_observation(frame,seat),legal_observation(next_frame,seat)
                inferred=infer_rival_net_sales(before,next_frame[seat]['action'],after,cfg)
                if inferred is None:
                    skipped+=1;continue
                # Only this validation block sees the rival's private state/action.
                rival=1-seat
                rival_before=post_worker_private(legal_observation(frame,rival),next_frame[rival]['action'],cfg)['shed']
                rival_after=next_frame[rival]['observation']['private']['shed']
                expected={item:rival_before.get(item,0)-rival_after.get(item,0) for item in inferred}
                checked+=1;active+=int(any(value for value in inferred.values() if value is not None))
                known+=sum(value is not None for value in inferred.values())
                censored+=sum(value is None for value in inferred.values())
                if any(value!=expected[item] for item,value in inferred.items() if value is not None):
                    mismatch=dict(step=step,inferred=inferred,expected=expected);break
            row=dict(fixture_id=fixture['fixture_id'],seat=seat,checked=checked,skipped_midnight=skipped,
                active_flow_turns=active,known_product_transitions=known,censored_product_transitions=censored,
                mismatch=mismatch,seconds=time.perf_counter()-started,
                passed=checked==690 and skipped==29 and mismatch is None)
            rows.append(row);print(json.dumps(row),flush=True)
    coverage=sum(r['known_product_transitions'] for r in rows)/(9*sum(r['checked'] for r in rows))
    result=dict(complete=True,passed=all(r['passed'] for r in rows) and coverage>=.8,
        checked=sum(r['checked'] for r in rows),known_product_coverage=coverage,
        legal_observation_inference=True,known_rival_private_used_only_for_ground_truth=True,
        plan_sha256=sha(HERE/'FLOW_PLAN.md'),correction_sha256=sha(HERE/'FLOW_CORRECTION.md'),
        model_sha256=sha(HERE/'observable_flow.py'),
        completed_at_utc=datetime.now(timezone.utc).isoformat(),rows=rows)
    (HERE/'flow_parity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Exact observable net-flow inference:',result['passed'],result['checked'])


if __name__=='__main__':main()
