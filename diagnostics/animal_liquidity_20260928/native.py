"""Fresh independent qualification for the complete animal-liquidity candidate."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import importlib.metadata
import json
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.animal_liquidity_20260928.screen import read, write, sha, validate_bindings

PARENTS = {"main": (ROOT / "main.py", "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"),
           "integrated": (ROOT / "main_candidate_hire_recovery_integrated_20260928_367d2e76.py", "367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0")}
from diagnostics.local_target_20260928.run_lock import exclusive_run

CANDIDATES = ('animal_cash',)
COMPARISONS = {'animal_cash': ('main', 'source')}
REFS = {'4ee': PARENTS['main'], 'market': (ROOT / 'public_market_smart_f6a756cf_20260927.py',
          'f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2')}


def points(row):
    return {'win': 1., 'draw': .5, 'loss': 0.}[row['result']]


def pair_key(row):
    return row['rival'], row['seed'], row['candidate_seat']


def key(row):
    return row['version'], *pair_key(row)


def valid(row):
    return row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE' and not row['candidate_errors'] and not row['opponent_errors']


def active_seeds(rows, candidate):
    return {r['seed'] for r in rows if r['version'] == candidate and r.get('candidate_telemetry', {}).get('animal_cash_turns', 0) > 0}


def needed_versions(candidates):
    return set(candidates) | {control for c in candidates for control in COMPARISONS[c]}


def bounds(rows, jobs, candidate, required_activation):
    failures = []
    roles = {candidate, *COMPARISONS[candidate]}
    invalid = [key(r) for r in rows if r['version'] in roles and not valid(r)]
    if invalid:
        failures.append(dict(gate='execution', invalid_games=invalid))
    for reference in (None, *REFS):
        selected = [r for r in rows if reference is None or r['rival'] == reference]
        actual = [r for r in selected if r['version'] == candidate]
        future = sum(j['version'] == candidate and (reference is None or j['rival'] == reference) for j in jobs) - len(actual)
        maximum = sum(map(points, actual)) + future
        for control in COMPARISONS[candidate]:
            minimum = sum(points(r) for r in selected if r['version'] == control)
            failed = maximum <= minimum if reference is None else maximum < minimum
            if failed:
                failures.append(dict(gate='pooled_strict_improvement' if reference is None else 'reference_nonregression',
                                     reference=reference, control=control, maximum_new_points=maximum,
                                     minimum_control_points=minimum, remaining_candidate_games=future))
    done = {key(r) for r in rows}
    possible = active_seeds(rows, candidate) | {j['seed'] for j in jobs if j['version'] == candidate and key(j) not in done}
    if len(possible) < required_activation:
        failures.append(dict(gate='activation', possible_distinct_seeds=len(possible), required=required_activation))
    return failures


def bootstrap(rows, candidate):
    indexed = {key(r): r for r in rows}; clustered = {}
    for row in rows:
        if row['version'] != candidate:
            continue
        cluster = clustered.setdefault(row['seed'], dict(games=0, **{c: 0. for c in COMPARISONS[candidate]}))
        cluster['games'] += 1
        for control in COMPARISONS[candidate]:
            cluster[control] += points(row) - points(indexed[(control, *pair_key(row))])
    assert clustered and all(c['games'] == 4 for c in clustered.values())
    seeds = sorted(clustered); rng = random.Random(2989999)
    samples = {c: [] for c in COMPARISONS[candidate]}
    for _ in range(20000):
        selected = [clustered[rng.choice(seeds)] for _ in seeds]
        denominator = 4 * len(selected)
        for control in samples:
            samples[control].append(sum(c[control] for c in selected) / denominator)
    answer = {}
    for control, values in samples.items():
        values.sort()
        answer[control] = dict(lower=values[int(.0125 * (len(values)-1))], upper=values[int(.9875 * (len(values)-1))],
                               resamples=20000, distinct_seeds=len(seeds), interval_percent=97.5,
                               unit='win-point difference per candidate game')
    return answer


def assess(rows, jobs, candidate, phase):
    roles = {candidate, *COMPARISONS[candidate]}
    complete = all(sum(r['version'] == role for r in rows) == sum(j['version'] == role for j in jobs) for role in roles)
    clean = all(valid(r) for r in rows if r['version'] in roles)
    required = 2 if phase == 'pilot' else 4
    summaries = []
    for reference in (None, *REFS):
        arms = {}
        for role in sorted(roles):
            selected = [r for r in rows if r['version'] == role and (reference is None or r['rival'] == reference)]
            arms[role] = dict(games=len(selected), win_points=sum(map(points, selected)),
                              WDL=[sum(r['result'] == s for r in selected) for s in ('win', 'draw', 'loss')])
        summaries.append(dict(reference=reference, arms=arms))
    nonregression = all(s['arms'][candidate]['win_points'] >= s['arms'][c]['win_points'] for s in summaries[1:] for c in COMPARISONS[candidate])
    pooled = summaries[0]['arms']
    strict = all(pooled[candidate]['win_points'] > pooled[c]['win_points'] for c in COMPARISONS[candidate])
    activation = len(active_seeds(rows, candidate)) >= required
    intervals = bootstrap(rows, candidate) if phase == 'confirmation' and complete and clean else None
    interval_pass = phase == 'pilot' or bool(intervals and all(v['lower'] > 0 for v in intervals.values()))
    indexed = {key(r): r for r in rows}; deltas = {}
    for control in COMPARISONS[candidate]:
        paired = [r for r in rows if r['version'] == candidate and (control, *pair_key(r)) in indexed]
        deltas[control] = dict(matched_games=len(paired),
            own_cash_delta=sum(r['candidate_reward']-indexed[(control, *pair_key(r))]['candidate_reward'] for r in paired),
            rival_cash_delta=sum(r['opponent_reward']-indexed[(control, *pair_key(r))]['opponent_reward'] for r in paired),
            paired_margin_delta=sum(r['margin']-indexed[(control, *pair_key(r))]['margin'] for r in paired))
    stats = {name: sum(r.get('candidate_telemetry', {}).get(name, 0) for r in rows if r['version'] == candidate)
             for name in ('animal_cash_turns', 'animal_cash_proposals', 'animal_cash_units', 'animal_cash_errors')}
    return dict(candidate=candidate, complete=complete, clean=clean, activation_gate=activation,
                distinct_active_seeds=sorted(active_seeds(rows, candidate)), required_active_seeds=required,
                per_reference_nonregression=nonregression, strict_pooled_improvement=strict, bootstrap_intervals=intervals,
                passed=complete and clean and activation and nonregression and strict and interval_pass,
                summaries=summaries, paired_cash=deltas, animal_cash_telemetry=stats)


def setup(phase):
    assert importlib.metadata.version('kaggle-environments') == '1.32.7'
    pool, full, seeds = validate_bindings(), read(HERE / 'native_full.json'), read(HERE / 'native_seeds.json')
    assert full['complete'] and full['passed'] and full['clean'] and full['pool_sha256'] == sha(HERE / 'pool.json')
    assert full['helper_sha256'] == sha(HERE / 'qualify.py') and full['screen_sha256'] == sha(HERE / 'screen.json')
    assert seeds['native_plan_sha256'] == sha(HERE / 'NATIVE_PLAN.md')
    checks = read(HERE / 'native_gate_checks.json')
    assert checks['passed'] and checks['native_helper_sha256'] == sha(__file__)
    assert all(sha(p) == digest for p, digest in PARENTS.values()) and all(sha(p) == digest for p, digest in REFS.values())
    backup = ROOT / ('main_candidate_animal_liquidity_20260928_' + pool['candidate_sha256'][:8] + '.py')
    assert sha(backup) == pool['candidate_sha256']
    arms = {'main': PARENTS['main'], 'source': PARENTS['integrated'],
            'animal_cash': (Path(pool['candidate']), pool['candidate_sha256'])}
    bindings = dict(native_plan_sha256=sha(HERE / 'NATIVE_PLAN.md'), native_seed_manifest_sha256=sha(HERE / 'native_seeds.json'),
                    native_helper_sha256=sha(__file__), native_game_helper_sha256=sha(ROOT / 'diagnostics/opening_probe_v2_20260928/qualify.py'),
                    pool_sha256=sha(HERE / 'pool.json'), native_full_sha256=sha(HERE / 'native_full.json'))
    candidates = list(CANDIDATES)
    if phase == 'confirmation':
        pilot = read(HERE / 'native_pilot.json')
        assert pilot['terminal'] and all(pilot[k] == v for k,v in bindings.items())
        candidates = [r['candidate'] for r in pilot['candidate_results'] if r['passed']]
        assert candidates == list(CANDIDATES)
    jobs = [dict(version=version, rival=ref, seed=seed, candidate_seat=seat, path=str(path), candidate_sha256=digest,
                 opponent=str(REFS[ref][0]), opponent_sha256=REFS[ref][1], **bindings)
            for seed in seeds['panels'][phase] for ref in REFS for version,(path,digest) in arms.items() for seat in (0,1)]
    assert len({key(j) for j in jobs}) == len(jobs)
    assert len(seeds['panels'][phase]) == (32 if phase == 'pilot' else 64)
    return candidates, bindings, jobs


def run(phase, workers):
    from diagnostics.opening_probe_v2_20260928.qualify import play
    candidates, bindings, jobs = setup(phase)
    destination = HERE / ('native_' + phase + '.json'); assert not destination.exists()
    checkpoint = HERE / ('native_' + phase + '.jsonl')
    rows = [json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    expected = {key(j): j for j in jobs}; done = {key(r) for r in rows}; assert len(done) == len(rows)
    for row in rows:
        assert all(row[k] == v for k, v in expected[key(row)].items())
    rejected = {}; required = 2 if phase == 'pilot' else 4

    def refresh():
        for candidate in candidates:
            if candidate not in rejected:
                failures = bounds(rows, jobs, candidate, required)
                if failures:
                    rejected[candidate] = failures
        return [c for c in candidates if c not in rejected]

    print('Animal liquidity native', phase, len(rows), '/', len(jobs), flush=True)
    with checkpoint.open('a', encoding='utf-8') as out:
        while True:
            active = refresh()
            needed = needed_versions(active)
            pending = [j for j in jobs if key(j) not in done and j['version'] in needed]
            if not active or not pending:
                break
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(play, j): j for j in pending[:16]}
                for future in as_completed(futures):
                    if future.cancelled():
                        continue
                    row = future.result(); assert key(row) not in done
                    done.add(key(row)); rows.append(row); out.write(json.dumps(row) + '\n'); out.flush()
                    still_needed = needed_versions(refresh())
                    for task, job in futures.items():
                        if job['version'] not in still_needed:
                            task.cancel()
                    if len(rows) % 4 == 0:
                        print('Animal liquidity native', phase, len(rows), '/', len(jobs), row['version'], row['rival'], row['result'], flush=True)
    results = [assess(rows, jobs, c, phase) for c in candidates]
    for result in results:
        result['early_rejection'] = rejected.get(result['candidate'], [])
        if result['early_rejection']:
            assert not result['passed']
    report = dict(terminal=True, complete=len(rows) == len(jobs), phase=phase, planned_games=len(jobs), game_count=len(rows),
                  passed_any=any(r['passed'] for r in results), candidate_results=results, games=sorted(rows, key=key),
                  completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings)
    write(destination, report)
    print(json.dumps({k:v for k,v in report.items() if k != 'games'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('pilot', 'confirmation'))
    parser.add_argument('--workers', type=int, default=1); args = parser.parse_args()
    with exclusive_run(HERE / 'native.lock'):
        run(args.phase, args.workers)
