"""Finite, hash-bound development across all remaining public-loss branches."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import hashlib
import importlib.util
import json
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / 'diagnostics/guarded_route_pool_20260928'
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play, sha
from diagnostics.local_target_20260928.run_lock import exclusive_run

SOURCE = ROOT / 'main_candidate_guarded_routes_20260928_2dd39764.py'
SOURCE_SHA = '2dd397645df739ee41e73a0d91f9e749863068b18bf31319ab338c980094ba34'
MAIN_SHA = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
FULL = PRIOR / 'native_full.json'
FULL_SHA = 'a9f4f04a36d583520c1e0c1bfe7427d464ac037db823730d968beca90f5fb2ad'
INVENTORY = PRIOR / 'remaining_route_inventory.json'
INVENTORY_SHA = '91b3f1c8b55c98391fcf690c8ba4b15cefca00f07ccc22825c8d66d9bfa8bec6'
COVERAGE = PRIOR / 'coverage.json'
COVERAGE_SHA = '7eca6f807e770839037de68744feeb3e4fe17e40e7c5205020aac19279f94b50'
TARGETS = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
TARGETS_SHA = '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
WINS = ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json'
WINS_SHA = 'f1cd25bbe3e058fec3bea3bb0cc470cd135780d2bb098e701908daf4053555de'
EXCLUDED = {'BRUNCH_SPOT|BRUNCH_SPOT', 'SMOOTHIE_SHOP|ICE_CREAM_SHOP'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)


def now():
    return datetime.now(timezone.utc).isoformat()


def action_hash(actions):
    return hashlib.sha256(json.dumps(actions, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def assert_sources():
    for path, digest in ((SOURCE, SOURCE_SHA), (ROOT / 'main.py', MAIN_SHA), (FULL, FULL_SHA),
                         (INVENTORY, INVENTORY_SHA), (COVERAGE, COVERAGE_SHA),
                         (TARGETS, TARGETS_SHA), (WINS, WINS_SHA)):
        assert sha(path) == digest, str(path)


def freeze_seeds():
    rng = random.Random(2949099)
    panels = dict(pilot=sorted(rng.sample(range(2940000, 2944096), 32)),
                  confirmation=sorted(rng.sample(range(2945000, 2949096), 64)))
    path = HERE / 'native_seeds.json'
    if path.exists():
        receipt = read(path)
        assert receipt['panels'] == panels and receipt['native_plan_sha256'] == sha(HERE / 'NATIVE_PLAN.md')
    else:
        write(path, dict(created_at_utc=now(), rng=2949099, panels=panels,
                         native_plan_sha256=sha(HERE / 'NATIVE_PLAN.md'),
                         range_audit='Prior rg search of research markdown returned no 294xxxx matches before these plans were written.',
                         outcome_or_prefix_inspection=False))
    return sha(path)


def write_candidate(replacements, target):
    assert sha(SOURCE) == SOURCE_SHA
    source = SOURCE.read_bytes()
    assert b'_LOSS_POOL_PARENT' not in source
    layer = (HERE / 'layer.py').read_text(encoding='utf-8').replace('REPLACEMENTS_VALUE', repr(replacements))
    blob = source + b'\n' + layer.encode('utf-8')
    compile(blob, str(target), 'exec')
    with target.open('xb') as stream:
        stream.write(blob)
    return sha(target)


def prepare():
    assert not (HERE / 'pool.json').exists()
    assert_sources()
    seed_sha = freeze_seeds()
    manifest, public, full, coverage = read(TARGETS), read(WINS), read(FULL), read(COVERAGE)
    assert full['complete'] and full['passed'] and coverage['complete'] and coverage['passed']
    fixtures = manifest['live_losses'] + manifest['current_top20'] + public['fixtures']
    by_id = {f['fixture_id']: f for f in fixtures}; assert len(by_id) == 104
    source = {(r['rival'], r['candidate_seat']): r for r in full['games']}; assert len(source) == 100
    prefixes = {(r['fixture_id'], r['candidate_seat']): r for r in coverage['prefixes']}; assert len(prefixes) == 208
    current_pairs = {}
    for fixture in fixtures:
        fid = fixture['fixture_id']
        if fid.startswith('public-win-'):
            pairs = {'|'.join(prefixes[(fid, seat)]['shops144']) for seat in (0, 1)}
        else:
            pairs = {source[(fid, seat)]['candidate_telemetry']['guard_route_pair144'] for seat in (0, 1)}
        assert len(pairs) == 1, 'Mixed-seat memberships require a documented correction before outcomes.'
        current_pairs[fid] = next(iter(pairs))
    groups = [g for g in read(INVENTORY)['groups'] if g['pair'] not in EXCLUDED]
    assert len(groups) == 21
    spec = importlib.util.spec_from_file_location('public_loss_pool_source', SOURCE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    variants, grouped, descriptions, loss_ids = [], {}, {}, set()
    folder = HERE / 'candidates'; folder.mkdir(exist_ok=True)
    for number, group in enumerate(groups, 1):
        label, pair = f'G{number:02}', group['pair']
        lookup = pair if pair in module._DATA['route_map'] else pair.split('|')[0]
        route = str(module._DATA['route_map'][lookup])
        assert lookup == group['actual_lookup'] and route == group['source_route']
        members = sorted(fid for fid, actual in current_pairs.items() if actual == pair)
        assert members == sorted(f['fixture_id'] for f in group['affected_fixtures'])
        assert all(sorted(f['seats']) == [0, 1] for f in group['affected_fixtures'])
        grouped[label] = [by_id[fid] for fid in members]
        losses = [fid for fid in members if fid.startswith('live-') and
                  any(source[(fid, seat)]['result'] != 'win' for seat in (0, 1))]
        assert losses and set(losses) == {f['fixture_id'] for f in group['unresolved_targets']}
        loss_ids.update(losses)
        descriptions[label] = dict(pair=pair, source_route=route, source_lookup=lookup, target_loss_ids=losses)
        hashes = set()
        for replacement in group['compatible_routes']:
            actions = module._DATA['routes'][replacement]
            assert len(actions) == 719 and actions[:144] == module._DATA['routes'][route][:144]
            digest = action_hash(actions); assert digest not in hashes; hashes.add(digest)
            name = label + '_' + replacement
            path = folder / (name + '.py')
            candidate_sha = write_candidate({pair: int(replacement)}, path)
            variants.append(dict(version=name, group=label, pair=pair, route=replacement,
                                 candidate=str(path), candidate_sha256=candidate_sha, route_sha256=digest))
        assert len(hashes) == group['compatible_route_count']
    del module; gc.collect()
    assert len(loss_ids) == 29 and len(variants) == 222
    assert sum(2 * len(grouped[v['group']]) for v in variants) == 1026
    assert sum(f['fixture_id'].startswith('public-win-') for fs in grouped.values() for f in fs) == 13
    result = dict(created_at_utc=now(), source=str(SOURCE), source_sha256=SOURCE_SHA, main_sha256=MAIN_SHA,
                  target_manifest_sha256=TARGETS_SHA, public_win_manifest_sha256=WINS_SHA,
                  source_full_sha256=FULL_SHA, inventory_sha256=INVENTORY_SHA, coverage_sha256=COVERAGE_SHA,
                  plan_sha256=sha(HERE / 'PLAN.md'), native_plan_sha256=sha(HERE / 'NATIVE_PLAN.md'),
                  native_seed_manifest_sha256=seed_sha, helper_sha256=sha(__file__),
                  implementation_note_sha256=sha(HERE / 'IMPLEMENTATION_NOTE.md'), layer_sha256=sha(HERE / 'layer.py'),
                  fast_helper_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                  core_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py'),
                  fixtures=grouped, groups=descriptions, variants=variants, target_loss_ids=sorted(loss_ids))
    write(HERE / 'pool.json', result)
    print(json.dumps(dict(groups=len(groups), variants=len(variants), variant_games=1026, controls=52,
                          pool_sha256=sha(HERE / 'pool.json'), seed_manifest_sha256=seed_sha), indent=2), flush=True)


def context():
    assert_sources()
    pool = read(HERE / 'pool.json')
    for field, path in (('plan_sha256', HERE / 'PLAN.md'), ('native_plan_sha256', HERE / 'NATIVE_PLAN.md'),
                        ('native_seed_manifest_sha256', HERE / 'native_seeds.json'), ('helper_sha256', Path(__file__)),
                        ('layer_sha256', HERE / 'layer.py'), ('implementation_note_sha256', HERE / 'IMPLEMENTATION_NOTE.md'),
                        ('fast_helper_sha256', ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                        ('core_sha256', ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py')):
        assert pool[field] == sha(path), field
    assert all(sha(v['candidate']) == v['candidate_sha256'] for v in pool['variants'])
    return pool


def key(row):
    return row['version'], row['fixture_id'], row['candidate_seat']


def jobs_for(pool, phase):
    jobs = []
    if phase == 'controls':
        controls = [dict(version='control-main', candidate=str(ROOT / 'main.py'), candidate_sha256=MAIN_SHA),
                    dict(version='control-source', candidate=str(SOURCE), candidate_sha256=SOURCE_SHA)]
        for group, fixtures in pool['fixtures'].items():
            for fixture in fixtures:
                if fixture['fixture_id'].startswith('public-win-'):
                    for control in controls:
                        for seat in (0, 1):
                            jobs.append((dict(control, group=group, pair=pool['groups'][group]['pair']), fixture, seat))
    else:
        for variant in pool['variants']:
            for fixture in pool['fixtures'][variant['group']]:
                for seat in (0, 1):
                    jobs.append((variant, fixture, seat))
    bindings = dict(plan_sha256=pool['plan_sha256'], pool_sha256=sha(HERE / 'pool.json'), helper_sha256=sha(__file__))
    assert len(jobs) == (52 if phase == 'controls' else 1026)
    return [(variant, fixture, seat, bindings) for variant, fixture, seat in jobs]


def validate(row, job):
    variant, fixture, seat, bindings = job
    assert key(row) == (variant['version'], fixture['fixture_id'], seat)
    assert row['candidate_sha256'] == variant['candidate_sha256']
    assert all(row[k] == v for k, v in bindings.items())
    assert row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
    assert not row['candidate_errors'] and not row.get('opponent_errors')
    telemetry = row['candidate_telemetry']
    if variant['version'] == 'control-source':
        assert telemetry['guard_route_pair144'] == variant['pair'], 'Fresh source coverage differs; stop before variants.'
    elif not variant['version'].startswith('control-'):
        assert telemetry['loss_pool_pair144'] == variant['pair']
        assert telemetry['loss_pool_route'] == variant['route'] and telemetry['loss_pool_turns'] > 0
    if variant['version'] == 'control-main' and seat == fixture['source_candidate_seat']:
        assert row['candidate_reward'] == fixture['source_candidate_reward']
        assert row['opponent_reward'] == fixture['source_opponent_reward']


def run_game(job):
    variant, fixture, seat, bindings = job
    row = play(fixture, variant['candidate'], variant['candidate_sha256'], seat)
    row.update(version=variant['version'], group=variant['group'], team=fixture['team'], seed=fixture['seed'], **bindings)
    return row


def run(phase, workers):
    pool = context()
    destination = HERE / (phase + '.json'); assert not destination.exists(), 'Completed stage exists.'
    if phase == 'screen':
        controls = read(HERE / 'controls.json')
        assert controls['complete'] and controls['clean'] and controls['game_count'] == 52
        assert controls['pool_sha256'] == sha(HERE / 'pool.json')
        expected_controls = {(v['version'], f['fixture_id'], s): (v, f, s, b) for v, f, s, b in jobs_for(pool, 'controls')}
        assert len(controls['games']) == len(expected_controls)
        for row in controls['games']:
            validate(row, expected_controls[key(row)])
    jobs = jobs_for(pool, phase)
    expected = {(v['version'], f['fixture_id'], s): (v, f, s, b) for v, f, s, b in jobs}
    assert len(expected) == len(jobs)
    checkpoint = HERE / (phase + '.jsonl')
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    done = {key(r) for r in rows}; assert len(done) == len(rows)
    for row in rows:
        validate(row, expected[key(row)])
    pending = [job for job in jobs if (job[0]['version'], job[1]['fixture_id'], job[2]) not in done]
    print(f'{phase} {len(rows)}/{len(jobs)}; workers={workers}', flush=True)
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(run_game, job) for job in pending[start:start+16]]):
                    row = future.result(); assert key(row) not in done
                    output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush()
                    validate(row, expected[key(row)])
                    done.add(key(row)); rows.append(row)
                    if len(rows) % 4 == 0:
                        print(f'{phase} {len(rows)}/{len(jobs)} {row["version"]} {row["team"]} '
                              f'seat{row["candidate_seat"]}: {row["result"]} {row["margin"]:+.0f}', flush=True)
    result = dict(complete=len(rows) == len(jobs), clean=True, game_count=len(rows),
                  pool_sha256=sha(HERE / 'pool.json'), plan_sha256=pool['plan_sha256'], helper_sha256=sha(__file__),
                  completed_at_utc=now(), games=sorted(rows, key=key))
    if phase == 'screen':
        result['controls_sha256'] = sha(HERE / 'controls.json')
    write(destination, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'games'}, indent=2), flush=True)


def points(row):
    return 1.0 if row['result'] == 'win' else .5 if row['result'] == 'draw' else 0.0


def control_maps(pool):
    source = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games']}
    original = {(f['fixture_id'], r['seat']): r for fs in pool['fixtures'].values() for f in fs
                for r in f.get('baseline_frozen_tape_both_seat_outcomes', [])}
    for row in read(HERE / 'controls.json')['games']:
        control = source if row['version'] == 'control-source' else original
        control[(row['fixture_id'], row['candidate_seat'])] = row
    return source, original


def metrics(rows, target_ids):
    pairs = {}
    for row in rows:
        pairs.setdefault(row.get('fixture_id', row.get('rival')), []).append(row)
    assert all(len(rs) == 2 for rs in pairs.values())
    return dict(target_sweeps=sum(all(r['result'] == 'win' for r in rs) for fid, rs in pairs.items() if fid in target_ids),
                target_points=sum(points(r) for fid, rs in pairs.items() if fid in target_ids for r in rs),
                all_sweeps=sum(all(r['result'] == 'win' for r in rs) for rs in pairs.values()),
                all_points=sum(map(points, rows)))


def select():
    pool = context(); screen = read(HERE / 'screen.json')
    assert screen['complete'] and screen['clean'] and screen['game_count'] == 1026
    assert screen['pool_sha256'] == sha(HERE / 'pool.json') and screen['controls_sha256'] == sha(HERE / 'controls.json')
    source, original = control_maps(pool)
    summaries, chosen, unchanged, replacements, rescues = [], [], [], {}, []
    for group, fixtures in pool['fixtures'].items():
        targets = set(pool['groups'][group]['target_loss_ids'])
        baseline = [source[(f['fixture_id'], seat)] for f in fixtures for seat in (0, 1)]
        base = metrics(baseline, targets)
        unchanged.append(dict(group=group, **pool['groups'][group], **base))
        eligible = []
        for variant in (v for v in pool['variants'] if v['group'] == group):
            rows = [r for r in screen['games'] if r['version'] == variant['version']]
            assert len(rows) == len(fixtures) * 2
            scores = metrics(rows, targets)
            regressions = [dict(fixture_id=r['fixture_id'], seat=r['candidate_seat']) for r in rows
                           if r['result'] != 'win' and any(c[(r['fixture_id'], r['candidate_seat'])]['result'] == 'win'
                                                        for c in (source, original))]
            delta = sum(r['margin'] - source[(r['fixture_id'], r['candidate_seat'])]['margin']
                        for r in rows if r['fixture_id'] in targets)
            pairs = {f['fixture_id']: sorted([r for r in rows if r['fixture_id'] == f['fixture_id']], key=lambda r: r['candidate_seat'])
                     for f in fixtures}
            item = dict(version=variant['version'], group=group, route=variant['route'], pair=variant['pair'], **scores,
                        regressions=regressions, target_margin_delta_vs_source=delta,
                        eligible=not regressions and (scores['target_sweeps'] > base['target_sweeps'] or
                                                     scores['target_points'] > base['target_points']),
                        fixtures=[dict(fixture_id=fid, team=rs[0]['team'], margins=[r['margin'] for r in rs],
                                       both_seat_win=all(r['result'] == 'win' for r in rs)) for fid, rs in pairs.items()])
            summaries.append(item)
            if item['eligible']:
                eligible.append(item)
        if eligible:
            best = min(eligible, key=lambda r: (-r['target_sweeps'], -r['target_points'], -r['all_sweeps'],
                                               -r['all_points'], -r['target_margin_delta_vs_source'], int(r['route'])))
            chosen.append(best); replacements[best['pair']] = int(best['route'])
            rescues.extend(f for f in best['fixtures'] if f['fixture_id'] in targets and f['both_seat_win'])
    result = dict(complete=True, passed=bool(rescues), rescued_public_losses=rescues, selected_replacements=replacements,
                  source_sha256=SOURCE_SHA, pool_sha256=sha(HERE / 'pool.json'), screen_sha256=sha(HERE / 'screen.json'),
                  controls_sha256=sha(HERE / 'controls.json'), plan_sha256=pool['plan_sha256'], helper_sha256=sha(__file__),
                  completed_at_utc=now(), selected_groups=chosen, unchanged_options=unchanged, summaries=summaries)
    if result['passed']:
        path = HERE / 'candidate_selected.py'; digest = write_candidate(replacements, path)
        backup = ROOT / ('main_candidate_public_loss_routes_20260928_' + digest[:8] + '.py')
        with backup.open('xb') as output:
            output.write(path.read_bytes())
        assert sha(backup) == digest
        result.update(candidate=str(path), candidate_sha256=digest, backup=str(backup))
    write(HERE / 'selection.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('summaries', 'unchanged_options', 'selected_groups')},
                     indent=2, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('prepare', 'controls', 'screen', 'select'))
    parser.add_argument('--workers', type=int, default=2); args = parser.parse_args()
    with exclusive_run(HERE / 'search.lock'):
        {'prepare': prepare, 'controls': lambda: run('controls', args.workers),
         'screen': lambda: run('screen', args.workers), 'select': select}[args.phase]()
