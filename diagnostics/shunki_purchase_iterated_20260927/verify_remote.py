from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module, make
from kaggle_environments.agent import get_last_callable
from diagnostics.shunki_purchase_iterated_20260927.promote_upload import KAGGLE

if __name__ == '__main__':
    receipt_path = HERE/'promotion_receipt.json'
    receipt = json.loads(receipt_path.read_text())
    assert str(receipt['kaggle_submission']['status']).endswith('COMPLETE')
    episode = int(receipt['validation_episode_id'])
    target = HERE/f'episode-{episode}-replay.json'
    if not target.exists():
        subprocess.run([KAGGLE,'competitions','replay',str(episode),'-p',str(HERE),'-q'],
                       capture_output=True,text=True,encoding='utf8',check=True)
    remote = json.loads(target.read_text(encoding='utf8'))
    seed = int(remote['info']['seed'])
    path = Path(receipt['uploaded_backup'])
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt['candidate_sha256']
    assert hashlib.sha256((ROOT/'main.py').read_bytes()).hexdigest() == receipt['candidate_sha256']
    loaded = get_last_callable(path.read_text(encoding='utf8'),path=str(path)).__name__
    assert loaded == 'kaggle_purchase_iterated_entrypoint'
    rows = []
    for mode in ('file','direct'):
        modules = []
        if mode == 'file':
            agents = [str(path),str(path)]
        else:
            modules = [_load_module(path,f'purchase_iterated_remote_{seat}') for seat in (0,1)]
            agents = [module.agent for module in modules]
        try:
            env = make('kaggriculture',configuration={'episodeSteps':720,'seed':seed},debug=False)
            env.run(agents)
            cash = [float(x.reward) for x in env.steps[-1]]
            statuses = [x.status for x in env.steps[-1]]
            equal = [all(frame[seat].action == remote['steps'][step][seat]['action']
                         for step,frame in enumerate(env.steps[1:],1)) for seat in (0,1)]
            row = dict(mode=mode,cash=cash,statuses=statuses,all_actions_match_remote=equal,frames=len(env.steps))
            rows.append(row)
            print(json.dumps(row),flush=True)
            assert cash == remote['rewards'] and statuses == ['DONE','DONE'] and all(equal) and len(env.steps)==720
        finally:
            for module in modules:
                sys.modules.pop(module.__name__,None)
    out = dict(completed_at_utc=datetime.now(timezone.utc).isoformat(),submission_id=receipt['submission_id'],
               validation_episode_id=episode,candidate_sha256=receipt['candidate_sha256'],loaded_name=loaded,
               seed=seed,seed_source='Kaggle validation replay.info.seed',remote_cash=remote['rewards'],rows=rows,passed=True,
               remote_replay_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    (HERE/'validation_parity.json').write_text(json.dumps(out,indent=2),encoding='utf8')
    receipt.update(remote_parity_passed=True,remote_parity_evidence=str(HERE/'validation_parity.json'))
    receipt_path.write_text(json.dumps(receipt,indent=2),encoding='utf8')
