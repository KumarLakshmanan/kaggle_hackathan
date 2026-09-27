from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module, TimedAgent, _timing_dict, make, engine_version
from diagnostics.shunki_funded_purchase_20260927.native import errors
from kaggle_environments.agent import get_last_callable

OLD = ROOT / 'main_uploaded_disjoint_integrated_20260927_c68fa46f.py'
OLD_HASH = 'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'


def play(job):
    manifest, seed, seat = job
    path = Path(manifest['candidate'])
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['candidate_sha256']
    assert hashlib.sha256(OLD.read_bytes()).hexdigest() == OLD_HASH
    candidate = _load_module(path, 'forecast4_pilot_candidate')
    rival = _load_module(OLD, 'forecast4_pilot_rival')
    entry = getattr(candidate, manifest['entrypoint'])
    def candidate_call(obs, cfg):
        visible = dict(cfg); visible['seed'] = None
        return entry(obs, visible)
    def rival_call(obs, cfg):
        visible = dict(cfg); visible['seed'] = None
        return rival.agent(obs, visible)
    a = TimedAgent(candidate_call, capture_step=72)
    b = TimedAgent(rival_call)
    started = time.perf_counter()
    try:
        env = make('kaggriculture', configuration={'episodeSteps':720, 'seed':seed}, debug=False)
        env.run([a,b] if seat == 0 else [b,a])
        final = env.steps[-1]
        own, other = float(final[seat].reward or 0), float(final[1-seat].reward or 0)
        return dict(seed=seed, candidate_seat=seat, candidate_reward=own, opponent_reward=other,
                    margin=own-other, result='win' if own>other else 'loss' if own<other else 'draw',
                    candidate_status=final[seat].status, opponent_status=final[1-seat].status,
                    frames=len(env.steps), wall_seconds=time.perf_counter()-started,
                    candidate_timing=_timing_dict(a), rival_timing=_timing_dict(b),
                    candidate_errors=errors(candidate), rival_errors=errors(rival),
                    candidate_telemetry=dict(getattr(entry,'telemetry',{}) or {}),
                    candidate_capture=a.capture, configuration_seed_visible=None,
                    report_counters={name:value for name,value in vars(candidate).items()
                                     if isinstance(value,dict) and ('REPORT' in name or 'STATS' in name)})
    finally:
        sys.modules.pop(candidate.__name__, None)
        sys.modules.pop(rival.__name__, None)


if __name__ == '__main__':
    manifest = json.loads((HERE / 'build_manifest.json').read_text())
    path = Path(manifest['candidate'])
    loaded = get_last_callable(path.read_text(encoding='utf8'), path=str(path)).__name__
    assert loaded == manifest['entrypoint']
    target = HERE / 'pilot.json'; assert not target.exists()
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(),
               candidate_sha256=manifest['candidate_sha256'], c68_sha256=OLD_HASH,
               entrypoint=loaded, engine_version=engine_version, complete=False, games=[])
    def save(): target.write_text(json.dumps(out, indent=2), encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(play, (manifest,seed,seat)) for seed in range(2706000,2706008) for seat in (0,1)]):
            g = future.result(); out['games'].append(g); save()
            print(f"{len(out['games'])}/16 seed={g['seed']} seat={g['candidate_seat']} {g['result']} {g['margin']:+.0f} errors={g['candidate_errors']}", flush=True)
    points = sum(1 if g['result']=='win' else .5 if g['result']=='draw' else 0 for g in out['games'])
    all_done = all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in out['games'])
    error_count = sum(sum(g['candidate_errors'].values())+sum(g['rival_errors'].values()) for g in out['games'])
    out.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(),
               points=points, all_done=all_done, errors=error_count,
               passed=points>=12 and all_done and error_count==0)
    save(); print('RESULT '+json.dumps({k:v for k,v in out.items() if k!='games'}), flush=True)
