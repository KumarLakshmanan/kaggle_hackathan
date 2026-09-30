"""Frozen branch qualification against two reacting policies, offline only."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import importlib.metadata
import json
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.guarded_route_pool_20260928.search import context as pool_context, SOURCE, SOURCE_SHA, MAIN_SHA, read, write, sha
from diagnostics.physical_route_rollout_20260928.fast_reactive import play as fast_play, load_policy, errors
from diagnostics.local_target_20260928.run_lock import exclusive_run

REFS = {'4ee': (ROOT / 'main.py', MAIN_SHA),
        'market': (ROOT / 'public_market_smart_f6a756cf_20260927.py',
                   'f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2')}


def now():
    return datetime.now(timezone.utc).isoformat()


def pkey(row):
    return row['rival'], row['seed'], row['candidate_seat']


def gkey(row):
    return row['version'], *pkey(row)


def points(row):
    return 1.0 if row['result'] == 'win' else .5 if row['result'] == 'draw' else 0.0


def setup(phase):
    pool_context()
    assert importlib.metadata.version('kaggle-environments') == '1.32.7'
    selected, full = read(HERE / 'selection.json'), read(HERE / 'native_full.json')
    assert full['complete'] and full['passed'] and full['candidate_sha256'] == sha(selected['candidate']) == selected['candidate_sha256']
    assert full['selection_sha256'] == sha(HERE / 'selection.json')
    helper = ROOT / 'diagnostics/physical_route_rollout_20260928'
    engineering = read(helper / 'reactive_parity.json')
    assert engineering['complete'] and engineering['passed']
    for name, field, digest in (
        ('fast_reactive.py', 'helper_sha256', '4f6061926f07402c87112e44d8ee28551dc62773b8141a89cba1c5744a6ecba9'),
        ('native_core.py', 'core_sha256', '5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795'),
        ('initial_template.json', 'template_sha256', '7d300be7e59ecd210eb8df5ad503c3971f6d869dee593daeffec1b3224cee7e1')):
        assert sha(helper / name) == engineering[field] == digest
    assert all(sha(path) == digest for path, digest in REFS.values()) and sha(SOURCE) == SOURCE_SHA
    bindings = dict(native_plan_sha256=sha(HERE / 'NATIVE_PLAN.md'),
                    native_helper_sha256=sha(__file__),
                    qualification_scope_sha256=sha(HERE / 'QUALIFICATION_SCOPE.md'),
                    prefix_convention_sha256=sha(HERE / 'PREFIX_CONVENTION.md'),
                    selection_sha256=sha(HERE / 'selection.json'),
                    selected_candidate_sha256=selected['candidate_sha256'])
    if phase == 'confirmation':
        pilot = read(HERE / 'native_pilot.json')
        assert pilot['complete'] and pilot['passed'] and all(pilot[k] == v for k, v in bindings.items())
    arms = {'main': (ROOT / 'main.py', MAIN_SHA), 'source': (SOURCE, SOURCE_SHA),
            'new': (Path(selected['candidate']), selected['candidate_sha256'])}
    return selected, bindings, arms


def prefix_job(selected, bindings, ref, seed, seat):
    return dict(rival=ref, seed=seed, candidate_seat=seat, path=selected['candidate'],
                candidate_sha256=selected['candidate_sha256'], opponent=str(REFS[ref][0]),
                opponent_sha256=REFS[ref][1], **bindings)


def prefix_fast(job):
    row = fast_play(job, steps=145)
    assert row['frames'] == 146 and row['observed_step'] == 145
    assert row['candidate_status'] == row['opponent_status'] == 'ACTIVE'
    assert not row['candidate_errors'] and not row['opponent_errors']
    assert 'candidate_reward' not in row and 'opponent_reward' not in row
    return row


def prefix_native(job):
    from paired_benchmark import make, TimedAgent
    assert sha(job['path']) == job['candidate_sha256'] and sha(job['opponent']) == job['opponent_sha256']
    candidate = load_policy(job['path'], 'guarded_native_prefix_own')
    opponent = load_policy(job['opponent'], 'guarded_native_prefix_rival')
    capture = {}
    def own(obs, cfg):
        if int(obs['step']) == 144:
            capture['shops144'] = list(obs['town']['unlocked_shops'][:2])
        return candidate.agent(obs, dict(cfg, seed=None))
    def other(obs, cfg):
        return opponent.agent(obs, dict(cfg, seed=None))
    players = [TimedAgent(own), TimedAgent(other)]
    if job['candidate_seat'] == 1:
        players.reverse()
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': job['seed']}, debug=False)
    env.reset(2)
    runner = env._Environment__agent_runner(players)
    for _ in range(145):
        actions, logs = runner.act(); env.step(actions, logs)
    seat = job['candidate_seat']
    row = dict(job, frames=len(env.steps), observed_step=int(env.state[0].observation.step),
               candidate_status=env.state[seat].status, opponent_status=env.state[1-seat].status,
               candidate_telemetry=dict(candidate.agent.telemetry), opponent_telemetry=dict(getattr(opponent.agent, 'telemetry', {}) or {}),
               candidate_errors=errors(candidate), opponent_errors=errors(opponent),
               shops144=capture['shops144'], configuration_seed_visible=None)
    assert row['frames'] == 146 and row['candidate_status'] == row['opponent_status'] == 'ACTIVE'
    del candidate, opponent, env; gc.collect()
    return row


def branch(row, replacements):
    pair = '|'.join(row['shops144'])
    if pair not in replacements:
        return None
    assert row['candidate_telemetry']['guard_route_selected'] == str(replacements[pair])
    assert row['candidate_telemetry']['guard_route_turns'] > 0
    return pair


def scan(phase, workers):
    selected, bindings, _ = setup(phase)
    target_count = 4 if phase == 'pilot' else 8
    seeds = list(range(2928000, 2930048) if phase == 'pilot' else range(2931000, 2935096))
    replacements = selected['selected_replacements']
    destination = HERE / (phase + '_eligibility.json')
    assert not destination.exists(), 'Completed selection exists; read it without repeating the scan.'
    checkpoint = HERE / (phase + '_prefixes.jsonl')
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    keyed = {pkey(row): row for row in rows}; assert len(keyed) == len(rows)
    for row in rows:
        assert row['seed'] in seeds and all(row[k] == v for k, v in bindings.items())
        assert row['candidate_sha256'] == selected['candidate_sha256'] and row['opponent_sha256'] == REFS[row['rival']][1]
    def eligible(ref, pair):
        return [seed for seed in seeds if all((ref, seed, seat) in keyed
                and branch(keyed[(ref, seed, seat)], replacements) == pair for seat in (0, 1))]
    def execute(jobs, output):
        pending = [job for job in jobs if pkey(job) not in keyed]
        if not pending:
            return
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for future in as_completed([executor.submit(prefix_fast, job) for job in pending]):
                row = future.result(); assert pkey(row) not in keyed
                keyed[pkey(row)] = row; rows.append(row)
                output.write(json.dumps(row) + '\n'); output.flush()
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(seeds), 8):
            needed = {ref: {pair for pair in replacements if len(eligible(ref, pair)) < target_count} for ref in REFS}
            needed = {ref: pairs for ref, pairs in needed.items() if pairs}
            if not needed:
                break
            block = seeds[start:start+8]
            execute([prefix_job(selected, bindings, ref, seed, 0) for seed in block for ref in needed], output)
            execute([prefix_job(selected, bindings, ref, seed, 1) for seed in block for ref, pairs in needed.items()
                     if branch(keyed[(ref, seed, 0)], replacements) in pairs], output)
            print(phase, block[-1], {ref: {pair: len(eligible(ref, pair)) for pair in replacements} for ref in REFS}, flush=True)
    chosen = {ref: {pair: eligible(ref, pair)[:target_count] for pair in replacements} for ref in REFS}
    result = dict(complete=True, passed=all(len(v) == target_count for groups in chosen.values() for v in groups.values()),
                  selected=chosen, seed_range=[seeds[0], seeds[-1]], prefix_game_count=len(rows),
                  completed_at_utc=now(), **bindings)
    write(destination, result); print(json.dumps(result, indent=2), flush=True)


def verify(phase, workers):
    selected, bindings, _ = setup(phase)
    chosen = read(HERE / (phase + '_eligibility.json'))
    assert chosen['complete'] and chosen['passed'] and all(chosen[k] == v for k, v in bindings.items())
    prefixes = [json.loads(line) for line in (HERE / (phase + '_prefixes.jsonl')).read_text(encoding='utf-8').splitlines()]
    fast = {pkey(row): row for row in prefixes}
    jobs = [prefix_job(selected, bindings, ref, seed, seat) for ref, groups in chosen['selected'].items()
            for seeds in groups.values() for seed in seeds for seat in (0, 1)]
    expected = {pkey(job): job for job in jobs}; assert len(expected) == len(jobs)
    checkpoint = HERE / (phase + '_verified_prefixes.jsonl')
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    done = {pkey(row) for row in rows}; assert len(done) == len(rows)
    for row in rows:
        assert all(row[k] == v for k, v in expected[pkey(row)].items())
    fields = ('frames', 'observed_step', 'candidate_status', 'opponent_status', 'candidate_telemetry', 'opponent_telemetry', 'shops144')
    pending = [job for job in jobs if pkey(job) not in done]
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(prefix_native, job) for job in pending[start:start+16]]):
                    row = future.result(); control = fast[pkey(row)]
                    row['mismatches'] = [field for field in fields if row[field] != control[field]]
                    row['passed'] = not row['mismatches'] and not row['candidate_errors'] and not row['opponent_errors']
                    rows.append(row); output.write(json.dumps(row) + '\n'); output.flush()
                    print('Native prefix', len(rows), '/', len(jobs), row['passed'], row['mismatches'], flush=True)
    result = dict(complete=len(rows) == len(jobs), passed=all(row['passed'] for row in rows), games=rows,
                  completed_at_utc=now(), **bindings)
    write(HERE / (phase + '_prefix_verification.json'), result)


def game_jobs(selected, bindings, arms, chosen):
    jobs = []
    for ref, groups in chosen['selected'].items():
        for pair, seeds in groups.items():
            for seed in seeds:
                for version, (path, digest) in arms.items():
                    for seat in (0, 1):
                        jobs.append(dict(version=version, rival=ref, shop_pair=pair, seed=seed,
                                         candidate_seat=seat, path=str(path), candidate_sha256=digest,
                                         opponent=str(REFS[ref][0]), opponent_sha256=REFS[ref][1], **bindings))
    assert len({gkey(job) for job in jobs}) == len(jobs)
    return jobs


def subsets(jobs):
    result = [('pooled', lambda row: True)]
    for ref in REFS:
        result.append(('reference:' + ref, lambda row, ref=ref: row['rival'] == ref))
        pairs = sorted({job['shop_pair'] for job in jobs if job['rival'] == ref})
        for pair in pairs:
            result.append((ref + ':' + pair, lambda row, ref=ref, pair=pair: row['rival'] == ref and row['shop_pair'] == pair))
    return result


def impossible_bounds(rows, jobs):
    failures = []
    for label, matches in subsets(jobs):
        actual = [row for row in rows if matches(row)]
        own = [row for row in actual if row['version'] == 'new']
        future = sum(job['version'] == 'new' and matches(job) for job in jobs) - len(own)
        maximum = sum(map(points, own)) + future
        for control in ('main', 'source'):
            minimum_control = sum(points(row) for row in actual if row['version'] == control)
            impossible = maximum <= minimum_control if label == 'pooled' else maximum < minimum_control
            if impossible:
                failures.append(dict(subset=label, control=control, maximum_possible_new_points=maximum,
                                     already_recorded_control_points=minimum_control,
                                     remaining_new_games=future, strict_improvement_required=label == 'pooled'))
    return failures


def summaries(rows, jobs):
    reports = []
    for label, matches in subsets(jobs):
        actual = [row for row in rows if matches(row)]
        arms = {}
        for version in ('main', 'source', 'new'):
            group = [row for row in actual if row['version'] == version]
            arms[version] = dict(games=len(group), expected_games=sum(matches(job) and job['version'] == version for job in jobs),
                                 win_points=sum(map(points, group)),
                                 WDL=[sum(row['result'] == outcome for row in group) for outcome in ('win', 'draw', 'loss')])
        reports.append(dict(subset=label, arms=arms))
    return reports


def bootstrap(rows):
    indexed = {gkey(row): row for row in rows}
    by_seed = {}
    for row in rows:
        if row['version'] != 'new':
            continue
        record = by_seed.setdefault(row['seed'], dict(games=0, main=0., source=0.))
        record['games'] += 1
        for control in ('main', 'source'):
            record[control] += points(row) - points(indexed[(control, *pkey(row))])
    seeds = sorted(by_seed)
    rng = random.Random(2935099)
    draws = {'main': [], 'source': []}
    for _ in range(10000):
        sample = [by_seed[rng.choice(seeds)] for _ in seeds]
        denominator = sum(item['games'] for item in sample)
        for control in draws:
            draws[control].append(sum(item[control] for item in sample) / denominator)
    result = {}
    for control, values in draws.items():
        values.sort()
        result[control] = dict(lower=values[int(.025 * (len(values)-1))], upper=values[int(.975 * (len(values)-1))],
                               resamples=10000, distinct_seeds=len(seeds), unit='win-point difference per new-arm game')
    return result


def strength(phase, workers):
    from diagnostics.opening_probe_v2_20260928.qualify import play
    selected, bindings, arms = setup(phase)
    chosen, verified = read(HERE / (phase + '_eligibility.json')), read(HERE / (phase + '_prefix_verification.json'))
    for gate in (chosen, verified):
        assert gate['complete'] and gate['passed'] and all(gate[k] == v for k, v in bindings.items())
    destination = HERE / ('native_' + phase + '.json')
    assert not destination.exists(), 'A terminal result already exists; do not repeat a strength stage.'
    jobs = game_jobs(selected, bindings, arms, chosen)
    expected = {gkey(job): job for job in jobs}
    checkpoint = HERE / ('native_' + phase + '.jsonl')
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    done = {gkey(row) for row in rows}; assert len(done) == len(rows)
    for row in rows:
        assert all(row[k] == v for k, v in expected[gkey(row)].items())
    pending = [job for job in jobs if gkey(job) not in done]
    stopped = impossible_bounds(rows, jobs)
    def valid(row):
        return (row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
                and not row['candidate_errors'] and not row['opponent_errors']
                and (row['version'] != 'new' or (
                    row['candidate_telemetry'].get('guard_route_pair144') == row['shop_pair']
                    and row['candidate_telemetry'].get('guard_route_selected') == str(selected['selected_replacements'][row['shop_pair']])
                    and row['candidate_telemetry'].get('guard_route_turns', 0) > 0)))
    execution_failure = any(not valid(row) for row in rows)
    print('Native', phase, len(rows), '/', len(jobs), flush=True)
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            if stopped or execution_failure:
                break
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(play, job) for job in pending[start:start+16]]
                for future in as_completed(futures):
                    if future.cancelled():
                        continue
                    row = future.result(); assert gkey(row) not in done
                    done.add(gkey(row)); rows.append(row)
                    output.write(json.dumps(row) + '\n'); output.flush()
                    execution_failure = execution_failure or not valid(row)
                    stopped = impossible_bounds(rows, jobs)
                    if stopped or execution_failure:
                        for waiting in futures:
                            waiting.cancel()
                    if len(rows) % 2 == 0:
                        print('Native', phase, len(rows), '/', len(jobs), row['version'], row['rival'], row['shop_pair'], row['result'], flush=True)
    complete = len(rows) == len(jobs)
    report = summaries(rows, jobs)
    per_subset = all(item['arms']['new']['win_points'] >= item['arms'][control]['win_points']
                     for item in report if item['subset'] != 'pooled' for control in ('main', 'source'))
    pooled = report[0]['arms']
    positive = all(pooled['new']['win_points'] > pooled[control]['win_points'] for control in ('main', 'source'))
    intervals = bootstrap(rows) if phase == 'confirmation' and complete and not execution_failure else None
    ci_passed = intervals is None if phase == 'pilot' else bool(intervals and all(value['lower'] > 0 for value in intervals.values()))
    paired_cash = {}
    indexed = {gkey(row): row for row in rows}
    for control in ('main', 'source'):
        shared = [row for row in rows if row['version'] == 'new' and (control, *pkey(row)) in indexed]
        paired_cash[control] = dict(matched_seats=len(shared),
            margin_delta=sum(row['margin'] - indexed[(control, *pkey(row))]['margin'] for row in shared))
    result = dict(complete=complete, passed=complete and not execution_failure and per_subset and positive and ci_passed,
                  phase=phase, game_count=len(rows), planned_games=len(jobs), early_stop_bounds=stopped,
                  execution_or_activation_failure=bool(execution_failure), per_subset_nonregression=per_subset,
                  pooled_strict_improvement=positive, bootstrap_intervals=intervals,
                  paired_cash_diagnostics=paired_cash, summaries=report, games=sorted(rows, key=gkey),
                  completed_at_utc=now(), qualification_scope='Changed A/C branches only; source qualification and scope checks remain mandatory.',
                  **bindings)
    write(destination, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'games'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('pilot-scan', 'pilot-verify', 'pilot', 'confirmation-scan', 'confirmation-verify', 'confirmation'))
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    phase = 'confirmation' if args.command.startswith('confirmation') else 'pilot'
    with exclusive_run(HERE / 'native.lock'):
        if args.command.endswith('-scan'):
            scan(phase, args.workers)
        elif args.command.endswith('-verify'):
            verify(phase, args.workers)
        else:
            strength(phase, args.workers)
