from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from diagnostics.shunki_planned_funding_20260927 import native

PURCHASE = ROOT / 'main_candidate_purchase_queue_20260927_43d6f448.py'
PURCHASE_HASH = '43d6f44806f7ce7204aa92180584f96c894653d6cb36bb9442a0425e8fbef176'


def play(job):
    native.RIVALS['purchase43d'] = PURCHASE
    return native.play(job)


if __name__ == '__main__':
    manifest = json.loads((HERE / 'build_manifest.json').read_text())
    assert hashlib.sha256((HERE / 'PLAN.md').read_bytes()).hexdigest() == manifest['plan_sha256']
    assert hashlib.sha256(PURCHASE.read_bytes()).hexdigest() == PURCHASE_HASH
    references = {'c68': manifest['source_sha256'], 'purchase43d': PURCHASE_HASH}
    seeds = list(range(2708000, 2708008))
    jobs = [(manifest['candidate'], manifest['candidate_sha256'], 'new', ref, digest, seed, seat)
            for seed in seeds for ref, digest in references.items() for seat in (0, 1)]
    target = HERE / 'pilot.json'
    assert not target.exists()
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), candidate_sha256=manifest['candidate_sha256'],
               plan_sha256=manifest['plan_sha256'], native_helper_sha256=hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
               reference_hashes=references, seeds=seeds, configuration_seed_masked=True, complete=False, games=[])
    def save():
        target.write_text(json.dumps(out, indent=2), encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            row = future.result()
            out['games'].append(row)
            save()
            telemetry = row['candidate_telemetry']
            print(f"{len(out['games'])}/32 {row['rival']} seed={row['seed']} seat={row['candidate_seat']} "
                  f"{row['result']} {row['margin']:+.0f} active={telemetry.get('iterated_queue_turns',0)} "
                  f"second={telemetry.get('iterated_queue_second_pass_turns',0)}", flush=True)
    scores = {r: sum(native.point(g) for g in out['games'] if g['rival'] == r) for r in references}
    active, second = {}, {}
    for ref in references:
        active[ref], second[ref] = [], []
        for seed in seeds:
            pair = [g for g in out['games'] if g['rival'] == ref and g['seed'] == seed]
            assert len(pair) == 2
            if all(g['candidate_telemetry'].get('iterated_queue_turns',0) > 0 for g in pair):
                active[ref].append(seed)
            if all(g['candidate_telemetry'].get('iterated_queue_second_pass_turns',0) > 0 for g in pair):
                second[ref].append(seed)
    all_done = all(g['candidate_status'] == g['opponent_status'] == 'DONE' and g['frames'] == 720 for g in out['games'])
    errors = sum(sum(g['candidate_errors'].values())+sum(g['opponent_errors'].values()) for g in out['games'])
    passed = (scores['c68'] >= 12 and scores['purchase43d'] >= 9 and min(map(len, active.values())) >= 6
              and min(map(len, second.values())) >= 4 and all_done and errors == 0)
    out.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(), scores=scores,
               active_pairs=active, second_pass_pairs=second, all_done=all_done, errors=errors, passed=passed)
    save()
    print('RESULT '+json.dumps({k:v for k,v in out.items() if k != 'games'}), flush=True)
