"""A finite first-shop schedule screen; saved tapes are development only."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import argparse
import gc
import importlib.util
import json
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.public_loss_route_pool_20260928.search import (
    SOURCE, SOURCE_SHA, MAIN_SHA, TARGETS, WINS, FULL, COVERAGE, assert_sources,
    sha, read, write, now, action_hash, points, play)
from diagnostics.local_target_20260928.run_lock import exclusive_run

TARGET = 'top20-01-DECEM-114267880'


def candidate(route, path):
    source = SOURCE.read_bytes(); assert sha(SOURCE) == SOURCE_SHA and b'_EARLY_BRUNCH_PARENT' not in source
    layer = (HERE / 'layer.py').read_text(encoding='utf-8').replace('ROUTE_VALUE', str(int(route)))
    blob = source + b'\n' + layer.encode('utf-8'); compile(blob, str(path), 'exec')
    with path.open('xb') as stream:
        stream.write(blob)
    return sha(path)


def prepare():
    assert_sources(); assert not (HERE / 'pool.json').exists()
    rng = random.Random(2959099)
    seeds = dict(created_at_utc=now(), native_plan_sha256=sha(HERE / 'NATIVE_PLAN.md'), rng=2959099,
                 panels=dict(pilot=sorted(rng.sample(range(2950000, 2954096), 32)),
                             confirmation=sorted(rng.sample(range(2955000, 2959096), 64))),
                 outcome_or_prefix_inspection=False)
    if (HERE / 'native_seeds.json').exists():
        prior = read(HERE / 'native_seeds.json')
        assert prior['panels'] == seeds['panels'] and prior['native_plan_sha256'] == seeds['native_plan_sha256']
    else:
        write(HERE / 'native_seeds.json', seeds)
    targets, full = read(TARGETS), read(FULL); assert full['complete'] and full['passed']
    all_fixtures = targets['live_losses'] + targets['current_top20'] + read(WINS)['fixtures']
    results = {(r['rival'], r['candidate_seat']): r for r in full['games']}
    prefixes = {(r['fixture_id'], r['candidate_seat']): r for r in read(COVERAGE)['prefixes']}
    fixtures = []
    for fixture in all_fixtures:
        fid = fixture['fixture_id']
        shops = [prefixes[(fid, seat)]['shops144'][0] if fid.startswith('public-win-') else
                 results[(fid, seat)]['candidate_telemetry']['guard_route_pair144'].split('|')[0] for seat in (0, 1)]
        assert shops[0] == shops[1]
        if shops[0] == 'BRUNCH_SPOT':
            fixtures.append(fixture)
    assert len(fixtures) == 16 and sum(f['fixture_id'].startswith('public-win-') for f in fixtures) == 6
    assert TARGET in {f['fixture_id'] for f in fixtures}
    spec = importlib.util.spec_from_file_location('early_brunch_source', SOURCE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    raw_source = str(module._DATA['route_map']['BRUNCH_SPOT'])
    opening = module._DATA['routes'][raw_source][:72]
    assert opening == module._DATA['opening'][:72]
    seen, variants = set(), []; folder = HERE / 'candidates'; folder.mkdir(exist_ok=True)
    for route, actions in sorted(module._DATA['routes'].items()):
        digest = action_hash(actions)
        if actions[:72] == opening and digest not in seen:
            assert len(actions) == 719
            seen.add(digest); path = folder / (str(route) + '.py')
            variants.append(dict(version=str(route), route=str(route), candidate=str(path),
                                 candidate_sha256=candidate(route, path), route_sha256=digest))
    del module; gc.collect(); assert len(variants) == 91
    pool = dict(created_at_utc=now(), source_sha256=SOURCE_SHA, main_sha256=MAIN_SHA,
                source_route=raw_source, target=TARGET, fixtures=fixtures, variants=variants,
                plan_sha256=sha(HERE / 'PLAN.md'), native_plan_sha256=sha(HERE / 'NATIVE_PLAN.md'),
                seed_manifest_sha256=sha(HERE / 'native_seeds.json'), helper_sha256=sha(__file__),
                layer_sha256=sha(HERE / 'layer.py'), source_full_sha256=sha(FULL),
                coverage_sha256=sha(COVERAGE), target_manifest_sha256=sha(TARGETS), public_manifest_sha256=sha(WINS),
                fast_helper_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                core_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py'))
    write(HERE / 'pool.json', pool)
    print(json.dumps(dict(variants=91, fixtures=16, controls=24, target_games=182, pool_sha256=sha(HERE / 'pool.json')), indent=2), flush=True)


def context():
    assert_sources(); pool = read(HERE / 'pool.json')
    for field, path in (('plan_sha256', HERE / 'PLAN.md'), ('native_plan_sha256', HERE / 'NATIVE_PLAN.md'),
                        ('seed_manifest_sha256', HERE / 'native_seeds.json'), ('helper_sha256', Path(__file__)),
                        ('layer_sha256', HERE / 'layer.py'),
                        ('fast_helper_sha256', ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                        ('core_sha256', ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py')):
        assert pool[field] == sha(path)
    assert all(sha(v['candidate']) == v['candidate_sha256'] for v in pool['variants'])
    return pool


def key(row):
    return row['version'], row['fixture_id'], row['candidate_seat']


def jobs_for(pool, phase):
    if phase == 'controls':
        variants = [dict(version='control-main', candidate=str(ROOT / 'main.py'), candidate_sha256=MAIN_SHA),
                    dict(version='control-source', candidate=str(SOURCE), candidate_sha256=SOURCE_SHA)]
        fixtures = [f for f in pool['fixtures'] if f['fixture_id'].startswith('public-win-')]
    elif phase == 'target':
        variants = pool['variants']; fixtures = [f for f in pool['fixtures'] if f['fixture_id'] == TARGET]
    else:
        selected = read(HERE / 'shortlist.json')
        assert selected['complete'] and selected['passed'] and selected['target_sha256'] == sha(HERE / 'target.json')
        assert selected['pool_sha256'] == sha(HERE / 'pool.json')
        variants = [v for v in pool['variants'] if v['version'] in selected['versions']]
        fixtures = [f for f in pool['fixtures'] if f['fixture_id'] != TARGET]
        assert len(variants) == len(selected['versions']) <= 5
    bindings = dict(pool_sha256=sha(HERE / 'pool.json'), plan_sha256=pool['plan_sha256'], helper_sha256=sha(__file__))
    return [(v, f, seat, bindings) for v in variants for f in fixtures for seat in (0, 1)]


def validate(row, job):
    variant, fixture, seat, bindings = job
    assert key(row) == (variant['version'], fixture['fixture_id'], seat)
    assert row['candidate_sha256'] == variant['candidate_sha256'] and all(row[k] == v for k, v in bindings.items())
    assert row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
    assert not row['candidate_errors'] and not row.get('opponent_errors')
    telemetry = row['candidate_telemetry']
    if variant['version'] == 'control-source':
        assert telemetry['guard_route_pair144'].split('|')[0] == 'BRUNCH_SPOT'
    elif not variant['version'].startswith('control-'):
        assert telemetry['early_brunch_shop72'] == 'BRUNCH_SPOT'
        assert telemetry['early_brunch_route'] == variant['route'] and telemetry['early_brunch_turns'] == 647
    if variant['version'] == 'control-main' and seat == fixture['source_candidate_seat']:
        assert row['candidate_reward'] == fixture['source_candidate_reward'] and row['opponent_reward'] == fixture['source_opponent_reward']


def run_game(job):
    variant, fixture, seat, bindings = job
    row = play(fixture, variant['candidate'], variant['candidate_sha256'], seat)
    row.update(version=variant['version'], team=fixture['team'], seed=fixture['seed'], **bindings)
    return row


def run(phase, workers):
    pool = context(); destination = HERE / (phase + '.json'); assert not destination.exists()
    if phase != 'controls':
        gate = read(HERE / 'controls.json')
        assert gate['complete'] and gate['clean'] and gate['game_count'] == 24 and gate['pool_sha256'] == sha(HERE / 'pool.json')
        expected_controls = {(v['version'], f['fixture_id'], s): (v, f, s, b) for v, f, s, b in jobs_for(pool, 'controls')}
        for row in gate['games']:
            validate(row, expected_controls[key(row)])
    jobs = jobs_for(pool, phase); expected = {(v['version'], f['fixture_id'], s): (v, f, s, b) for v, f, s, b in jobs}
    assert len(expected) == len(jobs)
    checkpoint = HERE / (phase + '.jsonl')
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    done = {key(r) for r in rows}; assert len(done) == len(rows)
    for row in rows:
        validate(row, expected[key(row)])
    pending = [j for j in jobs if (j[0]['version'], j[1]['fixture_id'], j[2]) not in done]
    print(phase, len(rows), '/', len(jobs), flush=True)
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(run_game, job) for job in pending[start:start+16]]):
                    row = future.result(); assert key(row) not in done
                    output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush()
                    validate(row, expected[key(row)]); done.add(key(row)); rows.append(row)
                    if len(rows) % 4 == 0:
                        print(phase, len(rows), '/', len(jobs), row['version'], row['team'], row['result'], row['margin'], flush=True)
    result = dict(complete=len(rows) == len(jobs), clean=True, game_count=len(rows), pool_sha256=sha(HERE / 'pool.json'),
                  helper_sha256=sha(__file__), completed_at_utc=now(), games=sorted(rows, key=key))
    write(destination, result)
    print(json.dumps({k:v for k,v in result.items() if k != 'games'}, indent=2), flush=True)


def shortlist():
    pool = context(); target = read(HERE / 'target.json')
    assert target['complete'] and target['clean'] and target['game_count'] == 182 and target['pool_sha256'] == sha(HERE / 'pool.json')
    eligible = []
    for variant in pool['variants']:
        rows = [r for r in target['games'] if r['version'] == variant['version']]
        assert len(rows) == 2
        if all(r['result'] == 'win' for r in rows):
            eligible.append(dict(version=variant['version'], margin_sum=sum(r['margin'] for r in rows)))
    eligible.sort(key=lambda r: (-r['margin_sum'], int(r['version'])))
    result = dict(complete=True, passed=bool(eligible), versions=[r['version'] for r in eligible[:5]],
                  ranked_winners=eligible, target_sha256=sha(HERE / 'target.json'), pool_sha256=sha(HERE / 'pool.json'), completed_at_utc=now())
    write(HERE / 'shortlist.json', result); print(json.dumps(result, indent=2), flush=True)


def select():
    pool = context(); finalists = read(HERE / 'shortlist.json'); retained = read(HERE / 'retention.json')
    assert finalists['passed'] and retained['complete'] and retained['clean'] and retained['pool_sha256'] == sha(HERE / 'pool.json')
    source = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games']}
    original = {(f['fixture_id'], r['seat']): r for f in pool['fixtures'] for r in f.get('baseline_frozen_tape_both_seat_outcomes', [])}
    for row in read(HERE / 'controls.json')['games']:
        (source if row['version'] == 'control-source' else original)[(row['fixture_id'], row['candidate_seat'])] = row
    all_rows = read(HERE / 'target.json')['games'] + retained['games']; summaries = []
    for version in finalists['versions']:
        rows = [r for r in all_rows if r['version'] == version]; assert len(rows) == 32
        pairs = {f['fixture_id']: [r for r in rows if r['fixture_id'] == f['fixture_id']] for f in pool['fixtures']}
        assert all(len(rs) == 2 for rs in pairs.values())
        regressions = [dict(fixture_id=r['fixture_id'], seat=r['candidate_seat']) for r in rows if r['result'] != 'win'
                       and any(c[(r['fixture_id'], r['candidate_seat'])]['result'] == 'win' for c in (source, original))]
        targets = [r for r in rows if not r['fixture_id'].startswith('public-win-')]
        summaries.append(dict(version=version, eligible=not regressions, regressions=regressions,
            target_sweeps=sum(all(r['result'] == 'win' for r in rs) for fid, rs in pairs.items() if not fid.startswith('public-win-')),
            target_points=sum(map(points, targets)), all_sweeps=sum(all(r['result'] == 'win' for r in rs) for rs in pairs.values()),
            all_points=sum(map(points, rows)), target_margin_delta=sum(r['margin']-source[(r['fixture_id'],r['candidate_seat'])]['margin'] for r in targets)))
    eligible = [r for r in summaries if r['eligible']]
    result = dict(complete=True, passed=bool(eligible), summaries=summaries, pool_sha256=sha(HERE / 'pool.json'),
                  target_sha256=sha(HERE / 'target.json'), retention_sha256=sha(HERE / 'retention.json'),
                  source_sha256=SOURCE_SHA, completed_at_utc=now())
    if eligible:
        best = min(eligible, key=lambda r: (-r['target_sweeps'], -r['target_points'], -r['all_sweeps'], -r['all_points'],
                                            -r['target_margin_delta'], int(r['version'])))
        variant = next(v for v in pool['variants'] if v['version'] == best['version'])
        path = HERE / 'candidate_selected.py'; backup = ROOT / ('main_candidate_early_brunch_20260928_' + variant['candidate_sha256'][:8] + '.py')
        for target in (path, backup):
            with target.open('xb') as output:
                output.write(Path(variant['candidate']).read_bytes())
            assert sha(target) == variant['candidate_sha256']
        result.update(selected=best, candidate=str(path), candidate_sha256=variant['candidate_sha256'], backup=str(backup))
    write(HERE / 'selection.json', result); print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('prepare', 'controls', 'target', 'shortlist', 'retention', 'select'))
    parser.add_argument('--workers', type=int, default=2); args = parser.parse_args()
    with exclusive_run(HERE / 'search.lock'):
        if args.phase in ('prepare', 'shortlist', 'select'):
            {'prepare': prepare, 'shortlist': shortlist, 'select': select}[args.phase]()
        else:
            run(args.phase, args.workers)
