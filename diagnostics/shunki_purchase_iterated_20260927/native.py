from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from diagnostics.shunki_planned_funding_20260927 import native as engine_runner

REFS = {
    'c68': ROOT / 'main_uploaded_disjoint_integrated_20260927_c68fa46f.py',
    '43d': ROOT / 'main_candidate_purchase_queue_20260927_43d6f448.py',
    '3bd': ROOT / 'main_candidate_iterated_queue_20260927_3bd78d06.py',
    '1f': ROOT / 'exp_shunki_visible_repair_20260927.py',
}
EXPECTED = {
    'c68': 'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad',
    '43d': '43d6f44806f7ce7204aa92180584f96c894653d6cb36bb9442a0425e8fbef176',
    '3bd': '3bd78d06e46010be28891c2ec30ca9604757e5424e22a3a2bb8224d3d9e0c0de',
    '1f': '1f22192297821ab5205b8cdcbd22bd1fab30d546860f3c61e8096a2a4355446b',
}

def play(job):
    engine_runner.RIVALS.update(REFS)
    return engine_runner.play(job)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('pilot', 'confirmation'))
    phase = parser.parse_args().phase
    manifest = json.loads((HERE / 'build_manifest.json').read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(HERE / 'PLAN.md') == manifest['plan_sha256']
    assert all(sha(path) == EXPECTED[name] for name, path in REFS.items())
    if phase == 'confirmation':
        gate = json.loads((HERE / 'panels.json').read_text())
        assert gate['complete'] and gate['passed'] and gate['candidate_sha256'] == manifest['candidate_sha256']
    seeds = list(range(2712000, 2712008) if phase == 'pilot' else range(2713000, 2713016))
    references = list(REFS)[:3] if phase == 'pilot' else list(REFS)
    versions = {'new': (manifest['candidate'], manifest['candidate_sha256'])}
    if phase == 'confirmation':
        versions['old'] = (str(REFS['c68']), EXPECTED['c68'])
    jobs = [(path, digest, version, ref, EXPECTED[ref], seed, seat)
            for seed in seeds for ref in references for version, (path, digest) in versions.items() for seat in (0, 1)]
    target = HERE / (phase + '.json')
    assert not target.exists()
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), phase=phase,
               candidate_sha256=manifest['candidate_sha256'], plan_sha256=manifest['plan_sha256'],
               runner_sha256=sha(Path(engine_runner.__file__)), script_sha256=sha(Path(__file__)),
               reference_hashes={r: EXPECTED[r] for r in references}, seeds=seeds,
               configuration_seed_masked=True, engine_version=engine_runner.engine_version,
               workers=4 if phase == 'pilot' else 6,
               complete=False, intended_games=len(jobs), games=[])
    def save():
        target.write_text(json.dumps(out, indent=2), encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=out['workers']) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            row = future.result()
            out['games'].append(row)
            save()
            if len(out['games']) % 8 == 0 or len(out['games']) == len(jobs):
                print(f'{phase}: {len(out["games"])}/{len(jobs)} games complete', flush=True)
    games = out['games']
    scores = {r: {v: sum(engine_runner.point(g) for g in games if g['rival'] == r and g['version'] == v)
                  for v in versions} for r in references}
    both_active, second_active = {}, {}
    for ref in references:
        both_active[ref], second_active[ref] = [], []
        for seed in seeds:
            pair = [g for g in games if g['rival'] == ref and g['seed'] == seed and g['version'] == 'new']
            assert len(pair) == 2
            if all(g['candidate_telemetry'].get('purchase_queue_turns', 0) > 0
                   and g['candidate_telemetry'].get('iterated_queue_turns', 0) > 0 for g in pair):
                both_active[ref].append(seed)
            if all(g['candidate_telemetry'].get('iterated_queue_second_pass_turns', 0) > 0 for g in pair):
                second_active[ref].append(seed)
    all_done = all(g['candidate_status'] == g['opponent_status'] == 'DONE' and g['frames'] == 720 for g in games)
    errors = sum(sum(g['candidate_errors'].values()) + sum(g['opponent_errors'].values()) for g in games)
    passed = all_done and errors == 0
    if phase == 'pilot':
        passed = passed and scores['c68']['new'] >= 12 and scores['43d']['new'] >= 9 and scores['3bd']['new'] >= 9
        passed = passed and min(map(len, both_active.values())) >= 6 and min(map(len, second_active.values())) >= 4
    else:
        deltas = [sum(engine_runner.point(g) * (1 if g['version'] == 'new' else -1)
                      for g in games if g['seed'] == seed) / (2 * len(references)) for seed in seeds]
        rng = random.Random(2713099)
        bootstrap = sorted(statistics.fmean(rng.choices(deltas, k=len(deltas))) for _ in range(10000))
        ci = [bootstrap[250], bootstrap[9749]]
        nonregression = all(s['new'] >= s['old'] for s in scores.values())
        passed = passed and scores['c68']['new'] >= 24 and scores['43d']['new'] >= 16 and scores['3bd']['new'] >= 16
        passed = passed and nonregression and ci[0] > 0 and min(map(len, both_active.values())) >= 8
        out.update(seed_win_point_deltas=deltas, paired_seed_bootstrap_95=ci, reference_nonregression=nonregression)
    out.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(), scores=scores,
               both_component_pairs=both_active, second_pass_pairs=second_active, all_done=all_done,
               errors=errors, passed=bool(passed))
    save()
    print('RESULT ' + json.dumps({k: v for k, v in out.items() if k != 'games'}), flush=True)
