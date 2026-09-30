"""Explain an already-scored reacting failure; not another strength test."""
from pathlib import Path
import gc
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import trace_paired_game_events as tracer
from diagnostics.local_target_20260928.run_lock import exclusive_run

original_loader = tracer._load_agent


def masked_loader(*args, **kwargs):
    agent, timed = original_loader(*args, **kwargs)
    if timed is not None:
        original = timed.function
        def masked(obs, cfg=None):
            visible = dict(cfg or {})
            visible['seed'] = None
            return original(obs, visible)
        timed.function = masked
        timed.accepts_configuration = True
    return agent, timed


def main():
    tracer._load_agent = masked_loader
    pilot = json.loads((HERE/'pilot.json').read_text(encoding='utf-8'))
    assert pilot['rejected'] and not pilot['passed']
    rows = [r for r in pilot['games'] if r['seed']==2908000 and r['candidate_seat']==0 and r['rival']=='market']
    assert len(rows)==2
    for row in rows:
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['candidate_sha256']
        assert hashlib.sha256(Path(row['opponent']).read_bytes()).hexdigest()==row['opponent_sha256']
        output = HERE / ('native_market_'+row['version']+'_s2908000_p0.json.gz')
        if output.exists():
            continue
        result=tracer.run(row['path'], row['opponent'],row['seed'],0)
        assert result['candidate_reward']==row['candidate_reward'] and result['opponent_reward']==row['opponent_reward']
        assert result['candidate_status']==result['opponent_status']=='DONE' and len(result['traces'][0])==719
        result.update(diagnostic_only=True,configuration_seed_masked=True,candidate_sha256=row['candidate_sha256'])
        with gzip.open(output,'wt',encoding='utf-8') as handle:
            json.dump(result,handle,separators=(',',':'))
        print(row['version'],'exact terminal parity',result['candidate_reward'],result['opponent_reward'],str(output),flush=True)
        del result
        gc.collect()


if __name__=='__main__':
    with exclusive_run(HERE/'native_trace.lock'):
        main()
