"""Finite offline route/planting development with immutable checkpoints."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import gzip
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play, sha
from diagnostics.local_target_20260928.run_lock import exclusive_run

SOURCE = ROOT / 'main_candidate_partial_planting_20260928_06803086.py'
SOURCE_SHA = '068030868689db5eb1e9a4a4427bededa8fbc13cae14e1003eb6be5440a6da42'
MAIN_SHA = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
TARGETS = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
TARGETS_SHA = '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
WINS = ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json'
WINS_SHA = 'f1cd25bbe3e058fec3bea3bb0cc470cd135780d2bb098e701908daf4053555de'
FULL = ROOT / 'diagnostics/partial_planting_20260928/native_full.json'
FULL_SHA = '98e4c7530830bf557123a42723ec95b157e3a95fa666c5dae655d2b2e902718f'
GROUPS = {'A': ('BRUNCH_SPOT|BRUNCH_SPOT', '113371344', 10),
          'C': ('SMOOTHIE_SHOP|ICE_CREAM_SHOP', '113441389', 12)}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as output:
        json.dump(value, output, indent=2, ensure_ascii=False)


def now():
    return datetime.now(timezone.utc).isoformat()


def write_candidate(replacements, target):
    assert sha(SOURCE) == SOURCE_SHA
    source = SOURCE.read_bytes()
    assert b'_AC_ROUTE_REPLACEMENTS' not in source
    layer = (HERE / 'layer.py').read_text(encoding='utf-8').replace('REPLACEMENTS_VALUE', repr(replacements))
    blob = source + b'\n' + layer.encode('utf-8')
    compile(blob, str(target), 'exec')
    with target.open('xb') as output:
        output.write(blob)
    return sha(target)


def prepare():
    assert not (HERE / 'pool.json').exists()
    for path, digest in ((SOURCE, SOURCE_SHA), (ROOT / 'main.py', MAIN_SHA), (TARGETS, TARGETS_SHA),
                         (WINS, WINS_SHA), (FULL, FULL_SHA)):
        assert sha(path) == digest
    manifest, public = read(TARGETS), read(WINS)
    fixtures = manifest['live_losses'] + manifest['current_top20'] + public['fixtures']
    assert len(fixtures) == 104
    receipt = read(HERE / 'coverage.json')
    assert receipt['complete'] and receipt['passed'] and receipt['source_sha256'] == SOURCE_SHA
    assert receipt['correction_sha256'] == sha(HERE / 'COVERAGE_CORRECTION.md')
    assert receipt['helper_sha256'] == sha(HERE / 'coverage.py')
    prefixes = {(r['fixture_id'], r['candidate_seat']): r for r in receipt['prefixes']}
    assert len(prefixes) == 208
    coverage = []
    grouped = {group: [] for group in GROUPS}
    for fixture in fixtures:
        records = [prefixes[(fixture['fixture_id'], seat)] for seat in (0, 1)]
        assert all(r['source_replay_sha256'] == fixture['source_replay_sha256'] for r in records)
        pairs = {'|'.join(r['shops144']) for r in records}
        coverage.append(dict(fixture_id=fixture['fixture_id'], team=fixture['team'], pairs=sorted(pairs),
                             recorded_pair=records[0]['recorded_shops144']))
        for group, (wanted, _, _) in GROUPS.items():
            if wanted in pairs:
                assert pairs == {wanted}, 'Affected fixtures require both-seat coverage; document any mixed grouping before outcomes.'
                grouped[group].append(fixture)
    expected_a = {f['fixture_id'] for f in fixtures if f['fixture_id'] == 'live-114289228'
                  or (f['fixture_id'].startswith('top20-') and f['team'] == 'DECEM')}
    expected_c = {f['fixture_id'] for f in fixtures if f['fixture_id'] in ('public-win-114188105', 'public-win-114248439')
                  or (f['fixture_id'].startswith('top20-') and f['team'] in ('Vadim Vasilenko', 'Yizhou'))}
    assert len(expected_a) == 2 and len(expected_c) == 4
    assert {f['fixture_id'] for f in grouped['A']} == expected_a
    assert {f['fixture_id'] for f in grouped['C']} == expected_c
    old_folder = ROOT / 'diagnostics/compatible_route_pool_20260928'
    assert sha(old_folder / 'corrected_screen.json') == '28ca6b2c42b71e51ba664da34b49d4d380297acb7f6f05ae0dae093a46fe9dd7'
    old_screen, old_pool = read(old_folder / 'corrected_screen.json'), read(old_folder / 'pool.json')
    assert old_screen['pool_sha256'] == sha(old_folder / 'pool.json')
    spec = importlib.util.spec_from_file_location('guarded_route_source', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    folder = HERE / 'candidates'
    folder.mkdir(exist_ok=True)
    variants = []
    for group, (pair, original, count) in GROUPS.items():
        previous = sorted((v for v in old_pool['variants'] if v['group'] == group), key=lambda v: v['route'])
        assert len(previous) == count
        digests = set()
        for variant in previous:
            route = variant['route']
            actions = module._DATA['routes'][route]
            assert len(actions) == 719 and actions[:144] == module._DATA['routes'][original][:144]
            action_sha = hashlib.sha256(json.dumps(actions, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            assert action_sha == variant['route_sha256'] and action_sha not in digests
            digests.add(action_sha)
            path = folder / (group + '_' + route + '.py')
            digest = write_candidate({pair: int(route)}, path)
            variants.append(dict(version=group + '_' + route, group=group, route=route, pair=pair,
                                 candidate=str(path), candidate_sha256=digest, route_sha256=action_sha))
    del module
    result = dict(created_at_utc=now(), source=str(SOURCE), source_sha256=SOURCE_SHA, main_sha256=MAIN_SHA,
                  target_manifest_sha256=TARGETS_SHA, public_win_manifest_sha256=WINS_SHA, source_full_sha256=FULL_SHA,
                  old_pool_sha256=sha(old_folder / 'pool.json'), plan_sha256=sha(HERE / 'PLAN.md'),
                  native_plan_sha256=sha(HERE / 'NATIVE_PLAN.md'), layer_sha256=sha(HERE / 'layer.py'),
                  coverage_correction_sha256=sha(HERE / 'COVERAGE_CORRECTION.md'), coverage_sha256=sha(HERE / 'coverage.json'),
                  qualification_scope_sha256=sha(HERE / 'QUALIFICATION_SCOPE.md'),
                  fast_helper_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                  fixtures=grouped, variants=variants, coverage=coverage)
    write(HERE / 'pool.json', result)
    print(json.dumps(dict(variants=len(variants), pool_sha256=sha(HERE / 'pool.json'),
                          coverage={k: [(f['fixture_id'], f['team']) for f in v] for k, v in grouped.items()}), indent=2), flush=True)


def context():
    pool = read(HERE / 'pool.json')
    assert pool['plan_sha256'] == sha(HERE / 'PLAN.md') and pool['native_plan_sha256'] == sha(HERE / 'NATIVE_PLAN.md')
    assert pool['layer_sha256'] == sha(HERE / 'layer.py')
    assert pool['coverage_correction_sha256'] == sha(HERE / 'COVERAGE_CORRECTION.md') and pool['coverage_sha256'] == sha(HERE / 'coverage.json')
    assert pool['qualification_scope_sha256'] == sha(HERE / 'QUALIFICATION_SCOPE.md')
    assert sha(SOURCE) == SOURCE_SHA and sha(ROOT / 'main.py') == MAIN_SHA
    assert sha(TARGETS) == TARGETS_SHA and sha(WINS) == WINS_SHA and sha(FULL) == FULL_SHA
    assert pool['fast_helper_sha256'] == sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py')
    assert all(sha(v['candidate']) == v['candidate_sha256'] for v in pool['variants'])
    return pool


def key(row):
    return row['version'], row['fixture_id'], row['candidate_seat']


def jobs_for(pool):
    jobs = []
    controls = [dict(version='control-main', candidate=str(ROOT / 'main.py'), candidate_sha256=MAIN_SHA),
                dict(version='control-source', candidate=str(SOURCE), candidate_sha256=SOURCE_SHA)]
    for group, fixtures in pool['fixtures'].items():
        for fixture in fixtures:
            if fixture['fixture_id'].startswith('public-win-'):
                for control in controls:
                    for seat in (0, 1):
                        jobs.append((dict(control, group=group), fixture, seat, pool['plan_sha256'], sha(HERE / 'pool.json')))
    for variant in pool['variants']:
        for fixture in pool['fixtures'][variant['group']]:
            for seat in (0, 1):
                jobs.append((variant, fixture, seat, pool['plan_sha256'], sha(HERE / 'pool.json')))
    assert len(jobs) == 144
    return jobs


def run_game(job):
    variant, fixture, seat, plan_sha, pool_sha = job
    row = play(fixture, variant['candidate'], variant['candidate_sha256'], seat)
    row.update(version=variant['version'], group=variant['group'], team=fixture['team'], seed=fixture['seed'],
               plan_sha256=plan_sha, pool_sha256=pool_sha)
    if not variant['version'].startswith('control-'):
        telemetry = row['candidate_telemetry']
        assert telemetry['guard_route_pair144'] == variant['pair']
        assert telemetry['guard_route_selected'] == variant['route'] and telemetry['guard_route_turns'] > 0
    if variant['version'] == 'control-main' and seat == fixture['source_candidate_seat']:
        assert row['candidate_reward'] == fixture['source_candidate_reward']
        assert row['opponent_reward'] == fixture['source_opponent_reward']
        row['original_public_cash_parity'] = True
    return row


def run(workers):
    pool = context()
    jobs = jobs_for(pool)
    checkpoint = HERE / 'screen.jsonl'
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    expected = {(v['version'], f['fixture_id'], seat): (v, plan_sha, pool_sha) for v, f, seat, plan_sha, pool_sha in jobs}
    done = {key(r) for r in rows}
    assert len(done) == len(rows)
    for row in rows:
        variant, plan_sha, pool_sha = expected[key(row)]
        assert row['candidate_sha256'] == variant['candidate_sha256'] and row['plan_sha256'] == plan_sha and row['pool_sha256'] == pool_sha
    pending = [job for job in jobs if (job[0]['version'], job[1]['fixture_id'], job[2]) not in done]
    print(f'Screen {len(rows)}/144; workers={workers}', flush=True)
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(run_game, job) for job in pending[start:start+16]]):
                    row = future.result()
                    assert key(row) not in done
                    done.add(key(row)); rows.append(row)
                    output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush()
                    if len(rows) % 2 == 0:
                        print(f'{len(rows)}/144 {row["version"]} {row["team"]} seat{row["candidate_seat"]}: '
                              f'{row["result"]} {row["margin"]:+.0f}; guard {row["candidate_telemetry"].get("partial_plant_turns", 0)}', flush=True)
    clean = all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE' and not r['candidate_errors'] for r in rows)
    result = dict(complete=len(rows) == len(jobs), clean=clean, game_count=len(rows),
                  pool_sha256=sha(HERE / 'pool.json'), plan_sha256=pool['plan_sha256'], completed_at_utc=now(), games=sorted(rows, key=key))
    write(HERE / 'screen.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'games'}, indent=2), flush=True)


def points(row):
    return 1 if row['result'] == 'win' else .5 if row['result'] == 'draw' else 0


def select():
    pool = context()
    screen, full = read(HERE / 'screen.json'), read(FULL)
    assert screen['complete'] and screen['clean'] and screen['game_count'] == 144
    assert screen['pool_sha256'] == sha(HERE / 'pool.json') and full['complete'] and full['passed']
    source = {(r['rival'], r['candidate_seat']): r for r in full['games']}
    original = {(f['fixture_id'], r['seat']): r for fixtures in pool['fixtures'].values() for f in fixtures
                for r in f.get('baseline_frozen_tape_both_seat_outcomes', [])}
    for row in screen['games']:
        if row['version'] == 'control-source':
            source[(row['fixture_id'], row['candidate_seat'])] = row
        elif row['version'] == 'control-main':
            original[(row['fixture_id'], row['candidate_seat'])] = row
    summaries, replacements, chosen = [], {}, []
    for group, fixtures in pool['fixtures'].items():
        baseline = [source[(f['fixture_id'], seat)] for f in fixtures for seat in (0, 1)]
        base_sweeps = sum(all(source[(f['fixture_id'], seat)]['result'] == 'win' for seat in (0, 1)) for f in fixtures)
        base_points = sum(map(points, baseline))
        eligible = []
        for variant in (v for v in pool['variants'] if v['group'] == group):
            rows = [r for r in screen['games'] if r['version'] == variant['version']]
            assert len(rows) == len(fixtures) * 2
            pairs = {f['fixture_id']: [r for r in rows if r['fixture_id'] == f['fixture_id']] for f in fixtures}
            regressions = [dict(fixture_id=r['fixture_id'], seat=r['candidate_seat']) for r in rows if r['result'] != 'win'
                           and any(control[(r['fixture_id'], r['candidate_seat'])]['result'] == 'win' for control in (source, original))]
            sweeps = sum(all(r['result'] == 'win' for r in pair) for pair in pairs.values())
            score = sum(map(points, rows))
            delta = sum(r['margin'] - source[(r['fixture_id'], r['candidate_seat'])]['margin'] for r in rows)
            item = dict(version=variant['version'], group=group, route=variant['route'], pair=variant['pair'],
                        sweeps=sweeps, win_points=score, regressions=regressions, margin_delta_vs_source=delta,
                        eligible=not regressions and (sweeps, score) > (base_sweeps, base_points),
                        fixtures=[dict(fixture_id=k, team=rs[0]['team'], margins=[r['margin'] for r in rs],
                                       both_seat_win=all(r['result'] == 'win' for r in rs),
                                       guard_turns=[r['candidate_telemetry']['partial_plant_turns'] for r in rs]) for k, rs in pairs.items()])
            summaries.append(item)
            if item['eligible']:
                eligible.append(item)
        if eligible:
            best = sorted(eligible, key=lambda r: (-r['sweeps'], -r['win_points'], -r['margin_delta_vs_source'], r['route']))[0]
            replacements[best['pair']] = int(best['route']); chosen.append(best)
    rescues = [f['team'] for choice in chosen for f in choice['fixtures'] if f['team'] in ('DECEM', 'Vadim Vasilenko') and f['both_seat_win']]
    result = dict(complete=True, passed=bool(rescues), rescued_top20=rescues, selected_replacements=replacements,
                  source_sha256=SOURCE_SHA, pool_sha256=sha(HERE / 'pool.json'), screen_sha256=sha(HERE / 'screen.json'),
                  plan_sha256=pool['plan_sha256'], completed_at_utc=now(), selected_groups=chosen, summaries=summaries)
    if result['passed']:
        target = HERE / 'candidate_selected.py'
        result['candidate'] = str(target)
        result['candidate_sha256'] = write_candidate(replacements, target)
        backup = ROOT / ('main_candidate_guarded_routes_20260928_' + result['candidate_sha256'][:8] + '.py')
        with backup.open('xb') as output:
            output.write(target.read_bytes())
        assert sha(backup) == result['candidate_sha256']
        result['backup'] = str(backup)
    write(HERE / 'selection.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'summaries'}, indent=2, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'select'))
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    with exclusive_run(HERE / 'search.lock'):
        {'prepare': prepare, 'run': lambda: run(args.workers), 'select': select}[args.phase]()
