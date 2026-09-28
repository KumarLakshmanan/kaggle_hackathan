"""Fresh whole-policy reacting qualification on preselected unconditional seeds."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import argparse
import importlib.metadata
import json
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.public_loss_route_pool_20260928.search import context, SOURCE, SOURCE_SHA, MAIN_SHA, read, write, sha, now, points
from diagnostics.local_target_20260928.run_lock import exclusive_run

REFS = {'4ee': (ROOT / 'main.py', MAIN_SHA),
        'market': (ROOT / 'public_market_smart_f6a756cf_20260927.py',
                   'f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2')}


def pkey(row):
    return row['rival'], row['seed'], row['candidate_seat']


def key(row):
    return row['version'], *pkey(row)


def subsets():
    return [('pooled', lambda row: True)] + [('reference:' + ref, lambda row, ref=ref: row['rival'] == ref) for ref in REFS]


def activated_seeds(rows):
    return {r['seed'] for r in rows if r['version'] == 'new' and r.get('candidate_telemetry', {}).get('loss_pool_turns', 0) > 0}


def impossible_bounds(rows, jobs, required_activation):
    failures = []
    for label, matches in subsets():
        actual = [r for r in rows if matches(r)]
        own = [r for r in actual if r['version'] == 'new']
        future = sum(j['version'] == 'new' and matches(j) for j in jobs) - len(own)
        maximum = sum(map(points, own)) + future
        for control in ('main', 'source'):
            minimum = sum(points(r) for r in actual if r['version'] == control)
            if maximum <= minimum if label == 'pooled' else maximum < minimum:
                failures.append(dict(subset=label, control=control, maximum_possible_new_points=maximum,
                                     already_recorded_control_points=minimum, remaining_new_games=future,
                                     strict_improvement_required=label == 'pooled'))
    done = {key(r) for r in rows}
    possible_seeds = activated_seeds(rows) | {j['seed'] for j in jobs if j['version'] == 'new' and key(j) not in done}
    if len(possible_seeds) < required_activation:
        failures.append(dict(subset='activation', maximum_distinct_active_seeds=len(possible_seeds), required=required_activation))
    return failures


def summaries(rows, jobs):
    report = []
    for label, matches in subsets():
        arms = {}
        for version in ('main', 'source', 'new'):
            actual = [r for r in rows if r['version'] == version and matches(r)]
            arms[version] = dict(games=len(actual), expected_games=sum(j['version'] == version and matches(j) for j in jobs),
                                 win_points=sum(map(points, actual)),
                                 WDL=[sum(r['result'] == outcome for r in actual) for outcome in ('win', 'draw', 'loss')])
        report.append(dict(subset=label, arms=arms))
    return report


def bootstrap(rows):
    indexed = {key(r): r for r in rows}; by_seed = {}
    for row in rows:
        if row['version'] != 'new':
            continue
        item = by_seed.setdefault(row['seed'], dict(games=0, main=0., source=0.))
        item['games'] += 1
        for control in ('main', 'source'):
            item[control] += points(row) - points(indexed[(control, *pkey(row))])
    seeds = sorted(by_seed); assert all(r['games'] == 4 for r in by_seed.values())
    rng = random.Random(2949999); draws = {'main': [], 'source': []}
    for _ in range(10000):
        sample = [by_seed[rng.choice(seeds)] for _ in seeds]
        denominator = sum(r['games'] for r in sample)
        for control in draws:
            draws[control].append(sum(r[control] for r in sample) / denominator)
    result = {}
    for control, values in draws.items():
        values.sort()
        result[control] = dict(lower=values[int(.025 * (len(values)-1))], upper=values[int(.975 * (len(values)-1))],
                               resamples=10000, distinct_seeds=len(seeds), unit='win-point difference per new-arm game')
    return result


def diagnostics(rows):
    indexed = {key(r): r for r in rows}; cash = {}
    for control in ('main', 'source'):
        paired = [r for r in rows if r['version'] == 'new' and (control, *pkey(r)) in indexed]
        cash[control] = dict(matched_games=len(paired),
            own_cash_delta=sum(r['candidate_reward'] - indexed[(control, *pkey(r))]['candidate_reward'] for r in paired),
            rival_cash_delta=sum(r['opponent_reward'] - indexed[(control, *pkey(r))]['opponent_reward'] for r in paired),
            paired_margin_delta=sum(r['margin'] - indexed[(control, *pkey(r))]['margin'] for r in paired))
    by_branch = {}
    for new in (r for r in rows if r['version'] == 'new'):
        branch = new['candidate_telemetry']['loss_pool_pair144']
        item = by_branch.setdefault(branch, {arm: [0, 0, 0] for arm in ('main', 'source', 'new')})
        for arm in item:
            row = indexed.get((arm, *pkey(new)))
            if row:
                item[arm][('win', 'draw', 'loss').index(row['result'])] += 1
    return dict(paired_cash=cash, branch_WDL_grouped_by_new_arm_public_pair=by_branch,
                distinct_active_seeds=sorted(activated_seeds(rows)))


def setup(phase):
    pool = context(); assert importlib.metadata.version('kaggle-environments') == '1.32.7'
    selected, full, seeds = read(HERE / 'selection.json'), read(HERE / 'native_full.json'), read(HERE / 'native_seeds.json')
    assert full['complete'] and full['passed'] and full['candidate_sha256'] == selected['candidate_sha256'] == sha(selected['candidate'])
    assert full['selection_sha256'] == sha(HERE / 'selection.json')
    assert full['qualify_helper_sha256'] == sha(HERE / 'qualify.py')
    assert all(sha(path) == digest for path, digest in REFS.values()) and sha(SOURCE) == SOURCE_SHA
    assert seeds['native_plan_sha256'] == pool['native_plan_sha256']
    checks = read(HERE / 'native_gate_checks.json')
    assert checks['passed'] and checks['native_helper_sha256'] == sha(__file__)
    bindings = dict(native_plan_sha256=pool['native_plan_sha256'], native_helper_sha256=sha(__file__),
                    native_game_helper_sha256=sha(ROOT / 'diagnostics/opening_probe_v2_20260928/qualify.py'),
                    native_seed_manifest_sha256=sha(HERE / 'native_seeds.json'), selection_sha256=sha(HERE / 'selection.json'),
                    selected_candidate_sha256=selected['candidate_sha256'], source_sha256=SOURCE_SHA)
    if phase == 'confirmation':
        pilot = read(HERE / 'native_pilot.json')
        assert pilot['complete'] and pilot['passed'] and all(pilot[k] == v for k, v in bindings.items())
    arms = {'main': (ROOT / 'main.py', MAIN_SHA), 'source': (SOURCE, SOURCE_SHA),
            'new': (Path(selected['candidate']), selected['candidate_sha256'])}
    jobs = [dict(version=version, rival=ref, seed=seed, candidate_seat=seat, path=str(path), candidate_sha256=digest,
                 opponent=str(REFS[ref][0]), opponent_sha256=REFS[ref][1], **bindings)
            for seed in seeds['panels'][phase] for ref in REFS for version, (path, digest) in arms.items() for seat in (0, 1)]
    assert len(jobs) == (384 if phase == 'pilot' else 768) and len({key(j) for j in jobs}) == len(jobs)
    return selected, bindings, jobs


def valid(row, replacements):
    if row['frames'] != 720 or row['candidate_status'] != 'DONE' or row['opponent_status'] != 'DONE':
        return False
    if row['candidate_errors'] or row['opponent_errors']:
        return False
    if row['version'] != 'new':
        return True
    telemetry = row['candidate_telemetry']; pair = telemetry.get('loss_pool_pair144')
    if not pair:
        return False
    if pair in replacements:
        return telemetry.get('loss_pool_turns', 0) > 0 and telemetry.get('loss_pool_route') == str(replacements[pair])
    return telemetry.get('loss_pool_turns') == 0 and telemetry.get('loss_pool_route') == ''


def strength(phase, workers):
    from diagnostics.opening_probe_v2_20260928.qualify import play
    selected, bindings, jobs = setup(phase)
    destination = HERE / ('native_' + phase + '.json'); assert not destination.exists()
    checkpoint = HERE / ('native_' + phase + '.jsonl')
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    expected = {key(j): j for j in jobs}; done = {key(r) for r in rows}; assert len(done) == len(rows)
    for row in rows:
        assert all(row[k] == v for k, v in expected[key(row)].items())
    pending = [j for j in jobs if key(j) not in done]
    required_activation = 4 if phase == 'pilot' else 8
    stopped = impossible_bounds(rows, jobs, required_activation)
    execution_failure = any(not valid(r, selected['selected_replacements']) for r in rows)
    print('Whole-policy', phase, len(rows), '/', len(jobs), flush=True)
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            if stopped or execution_failure:
                break
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(play, job) for job in pending[start:start+16]]
                for future in as_completed(futures):
                    if future.cancelled():
                        continue
                    row = future.result(); assert key(row) not in done
                    done.add(key(row)); rows.append(row)
                    output.write(json.dumps(row) + '\n'); output.flush()
                    execution_failure = execution_failure or not valid(row, selected['selected_replacements'])
                    stopped = impossible_bounds(rows, jobs, required_activation)
                    if stopped or execution_failure:
                        for waiting in futures:
                            waiting.cancel()
                    if len(rows) % 4 == 0:
                        print('Whole-policy', phase, len(rows), '/', len(jobs), row['version'], row['rival'], row['result'], flush=True)
    complete = len(rows) == len(jobs); report = summaries(rows, jobs)
    nonregression = all(item['arms']['new']['win_points'] >= item['arms'][control]['win_points']
                        for item in report[1:] for control in ('main', 'source'))
    pooled = report[0]['arms']
    positive = all(pooled['new']['win_points'] > pooled[c]['win_points'] for c in ('main', 'source'))
    activation = len(activated_seeds(rows)) >= required_activation
    intervals = bootstrap(rows) if phase == 'confirmation' and complete and not execution_failure else None
    ci_passed = phase == 'pilot' or bool(intervals and all(value['lower'] > 0 for value in intervals.values()))
    result = dict(complete=complete, passed=complete and not execution_failure and nonregression and positive and activation and ci_passed,
                  phase=phase, game_count=len(rows), planned_games=len(jobs), early_stop_bounds=stopped,
                  execution_or_activation_failure=execution_failure, distinct_activation_requirement=required_activation,
                  activation_gate=activation, per_reference_nonregression=nonregression, pooled_strict_improvement=positive,
                  bootstrap_intervals=intervals, summaries=report, diagnostics=diagnostics(rows), games=sorted(rows, key=key),
                  completed_at_utc=now(), **bindings)
    write(destination, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('games', 'diagnostics')}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('pilot', 'confirmation'))
    parser.add_argument('--workers', type=int, default=3); args = parser.parse_args()
    with exclusive_run(HERE / 'native.lock'):
        strength(args.phase, args.workers)
