"""Finite compatible-suffix screen on frozen public production leaves."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import gc
import gzip
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LEAVES = ROOT / 'diagnostics/production_leaf_selector_20260928'
EARLY = ROOT / 'diagnostics/public_90_research_20260928'
CACHE = ROOT / 'diagnostics/stream_replay_io_20260928'
sys.path.insert(0, str(ROOT))
from diagnostics.production_leaf_selector_20260928 import study as previous
from diagnostics.stream_replay_io_20260928.fast_game_cached import play
from diagnostics.stream_replay_io_20260928.cached_input import load_fixture
from diagnostics.physical_route_rollout_20260928 import native_core as core
from diagnostics.physical_route_rollout_20260928.check import Box, state_from_frames
from diagnostics.local_target_20260928.run_lock import exclusive_run

SPECS = [('PET_CAFE|M8+|C>S', '113517834', 'live-114260122', 10, 8),
         ('PIZZA_SHOP|M8+|C>S', '113332529', 'live-114238112', 13, 4)]


def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def write(p, value):
    with Path(p).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
def key(row): return row['version'], row['fixture_id'], row['candidate_seat']
def point(row): return {'win': 1, 'draw': .5, 'loss': 0}[row['result']]


def load(p):
    spec = importlib.util.spec_from_file_location('pair_policy', p)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def build(parent, leaf, default, rules, path):
    layer = (HERE / 'layer.py').read_text(encoding='utf-8').replace('LEAF_VALUE', repr(leaf)).replace('DEFAULT_VALUE', repr(default)).replace('RULES_VALUE', repr(rules))
    blob = Path(parent).read_bytes() + b'\n' + layer.encode('utf-8')
    compile(blob, str(path), 'exec')
    if not path.exists():
        with path.open('xb') as stream: stream.write(blob)
    assert path.read_bytes() == blob
    return sha(path)


def prepare():
    old = previous.context(); controls = previous.source_controls()
    control_path = LEAVES / 'controls.json'
    assert sha(control_path) == '2ca9a8c946c7cab1f331bea3f8eea5c253226a5ca5a62427df374ea6f122a293'
    families = []; variants = []
    (HERE / 'candidates').mkdir(exist_ok=True)
    fixtures = {f['fixture_id']: f for f in old['fixtures']}
    for index, (leaf, medoid, target, expected_members, expected_fixtures) in enumerate(SPECS):
        parent = next(c for c in old['candidates'] if c['arm'] == 'production' and c['leaf'] == leaf and c['route'] == medoid)
        module = load(parent['candidate'])
        unique = {}
        for route, actions in sorted(module._DATA['routes'].items(), key=lambda x: int(x[0])):
            if actions[:144] == module._DATA['routes'][medoid][:144]:
                token = hashlib.sha256(json.dumps(actions, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                unique.setdefault(token, route)
        routes = sorted(unique.values(), key=int)
        assert len(routes) == expected_members and len(parent['affected_fixture_ids']) == expected_fixtures
        fids = parent['affected_fixture_ids']
        assert all((fid, seat) in controls for fid in fids for seat in (0, 1))
        families.append(dict(index=index, leaf=leaf, medoid=medoid, target=target, parent=parent,
                             routes=routes, fixtures=[fixtures[fid] for fid in fids],
                             controls=[dict(controls[(fid, s)], fixture_id=fid) for fid in fids for s in (0, 1)]))
        for route in routes:
            version = 'family' + str(index) + '_' + route
            path = HERE / 'candidates' / (version + '.py')
            digest = build(parent['candidate'], leaf, route, {}, path)
            candidate = load(path)
            assert candidate._DATA['routes'][route][:144] == module._DATA['routes'][medoid][:144]
            assert candidate._PRODUCTION_LEAF_RULES == module._PRODUCTION_LEAF_RULES
            candidate._production_leaf_commit(leaf, route)
            fake = dict(step=144, town={'unlocked_shops': [leaf.split('|')[0], 'BAKERY']})
            assert candidate._hire_recovery_schedule(fake) == candidate._DATA['routes'][route]
            candidate._production_leaf_reset()
            assert candidate._DATA['route_map'] == candidate._PRODUCTION_LEAF_BASE_MAP
            variants.append(dict(version=version, family=index, route=route, candidate=str(path), candidate_sha256=digest))
            del candidate; gc.collect()
        del module; gc.collect()
    assert len(variants) == 23
    paths = [Path(__file__), HERE / 'PLAN.md', HERE / 'layer.py', LEAVES / 'pool.json',
             LEAVES / 'study.py', LEAVES / 'layer.py', LEAVES / 'controls.json', previous.FULL,
             CACHE / 'fast_game_cached.py', CACHE / 'cached_input.py', CACHE / 'initial_states.json',
             CACHE / 'cached_helper_parity.json', ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py']
    paths += [Path(f['parent']['candidate']) for f in families]
    write(HERE / 'pool.json', dict(frozen_at_utc=now(), families=families, variants=variants,
          bindings={str(p): sha(p) for p in paths}, planned_games=264, new_games=264))
    print('Frozen23 candidates /264 games.', flush=True)


def context():
    pool = read(HERE / 'pool.json')
    assert all(sha(p) == h for p, h in pool['bindings'].items())
    assert all(sha(v['candidate']) == v['candidate_sha256'] for v in pool['variants'])
    return pool


def prefix(path, fixture, seat):
    replay = load_fixture(fixture)
    state = state_from_frames(replay['steps'][0]); cfg = dict(replay['configuration']); cfg['seed'] = None
    env = Box(configuration=Box(**cfg), info={'seed': int(fixture['seed'])}, done=False)
    tape = read_tape(fixture)
    module = load(path); digest = hashlib.sha256()
    for step in range(144):
        obs = copy.deepcopy(dict(state[seat].observation, remainingOverageTime=60.0))
        action = module.agent(obs, cfg)
        digest.update(json.dumps([obs, action], sort_keys=True, separators=(',', ':')).encode())
        state[seat].action = action; state[1-seat].action = copy.deepcopy(tape[step])
        core.interpreter(state, env)
        for item in state: item.observation.step = step + 1
    digest.update(json.dumps(dict(state[seat].observation), sort_keys=True, separators=(',', ':')).encode())
    del module; gc.collect()
    return digest.hexdigest()


def read_tape(fixture):
    tape = json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    hashes = [hashlib.sha256(json.dumps(tape, sort_keys=s, separators=(',', ':')).encode()).hexdigest() for s in (False, True)]
    assert fixture['source_opponent_action_sha256'] in hashes and len(tape) == 719
    return tape


def preflight():
    pool = context(); checks = []
    for family in pool['families']:
        fixture = next(f for f in family['fixtures'] if f['fixture_id'] == family['target'])
        for seat in (0, 1):
            expected = prefix(family['parent']['candidate'], fixture, seat)
            for route in (family['routes'][0], family['routes'][-1]):
                variant = next(v for v in pool['variants'] if v['family'] == family['index'] and v['route'] == route)
                actual = prefix(variant['candidate'], fixture, seat)
                assert actual == expected
                checks.append(dict(version=variant['version'], fixture_id=fixture['fixture_id'], seat=seat, trajectory_sha256=actual, passed=True))
    assert len(checks) == 8
    write(HERE / 'preflight.json', dict(passed=True, checks=checks, pool_sha256=sha(HERE / 'pool.json'), completed_at_utc=now()))
    print('Eight144-action/145-observation prefix pairs match.', flush=True)


def valid(row, variant):
    assert row['candidate_sha256'] == variant['candidate_sha256']
    assert row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
    assert not row['candidate_errors']
    tel = row['candidate_telemetry']
    assert tel['production_leaf_turns'] == 647 and tel['production_pair_turns'] == 575
    assert tel['production_leaf_route'] == tel['production_pair_route'] == variant['route']


def one(job):
    variant, fixture, seat = job
    row = play(fixture, variant['candidate'], variant['candidate_sha256'], seat)
    row.update(version=variant['version'], family=variant['family'], route=variant['route'], team=fixture['team'], pool_sha256=sha(HERE / 'pool.json'))
    valid(row, variant)
    return row


def run(workers):
    assert 1 <= workers <= 2
    pool = context(); preflight = read(HERE / 'preflight.json')
    assert preflight['passed'] and preflight['pool_sha256'] == sha(HERE / 'pool.json')
    expected = {(v['version'], f['fixture_id'], s): (v, f, s)
                for v in pool['variants'] for f in pool['families'][v['family']]['fixtures'] for s in (0, 1)}
    assert len(expected) == 264
    ledger = HERE / 'screen.jsonl'
    rows = [json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    done = {key(r) for r in rows}; assert len(done) == len(rows)
    for row in rows:
        valid(row, expected[key(row)][0]); assert row['pool_sha256'] == sha(HERE / 'pool.json')
    print('Compatible continuation', len(rows), '/264', flush=True)
    with ledger.open('a', encoding='utf-8') as stream:
        with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as executor:
            futures = {executor.submit(one, job): k for k, job in expected.items() if k not in done}
            for future in as_completed(futures):
                row = future.result(); assert key(row) not in done
                done.add(key(row)); rows.append(row)
                stream.write(json.dumps(row, ensure_ascii=False) + '\n'); stream.flush()
                if len(rows) % 8 == 0: print('Compatible continuation', len(rows), '/264', row['version'], row['margin'], flush=True)
    write(HERE / 'screen.json', dict(complete=True, clean=True, games=rows, game_count=264,
          pool_sha256=sha(HERE / 'pool.json'), completed_at_utc=now()))
    select(pool, rows)


def select(pool, rows):
    selected = []; decisions = []
    for family in pool['families']:
        controls = {(r['fixture_id'], r['candidate_seat']): r for r in family['controls']}
        relevant = [r for r in rows if r['family'] == family['index']]
        contexts = {}
        for key0 in controls:
            values = {r['candidate_telemetry']['production_pair144'] for r in relevant if (r['fixture_id'], r['candidate_seat']) == key0}
            assert len(values) == 1
            contexts[key0] = values.pop()
        assert all(contexts[(fid, 0)] == contexts[(fid, 1)] for fid, _ in contexts)
        rules = {}; choices = []
        for pair in sorted(set(contexts.values())):
            options = []
            for route in family['routes']:
                rr = [r for r in relevant if r['route'] == route and contexts[(r['fixture_id'], r['candidate_seat'])] == pair]
                regressions = [key(r) for r in rr if controls[(r['fixture_id'], r['candidate_seat'])]['result'] == 'win' and r['result'] != 'win']
                ids = {r['fixture_id'] for r in rr}
                sweeps = sum(all(r['result'] == 'win' for r in rr if r['fixture_id'] == fid) for fid in ids)
                options.append(dict(route=route, regressions=regressions, sweeps=sweeps,
                                    points=sum(map(point, rr)), delta_margin=sum(r['margin'] - controls[(r['fixture_id'], r['candidate_seat'])]['margin'] for r in rr)))
            eligible = [o for o in options if not o['regressions']]
            eligible.sort(key=lambda o: (-o['sweeps'], -o['points'], -o['delta_margin'], int(o['route'])))
            choice = eligible[0] if eligible else None
            if choice: rules[pair] = choice['route']
            choices.append(dict(pair=pair, options=options, selected=choice))
        covered = len(rules) == len(set(contexts.values()))
        target_rows = [r for r in relevant if r['fixture_id'] == family['target'] and r['route'] == rules.get(contexts[(r['fixture_id'], r['candidate_seat'])])]
        rescued = len(target_rows) == 2 and all(r['result'] == 'win' for r in target_rows)
        passed = covered and rescued
        decisions.append(dict(family=family['index'], leaf=family['leaf'], covered=covered, target_rescued=rescued, passed=passed, choices=choices))
        if passed:
            path = HERE / ('candidate_selected_family' + str(family['index']) + '.py')
            digest = build(family['parent']['candidate'], family['leaf'], family['medoid'], rules, path)
            selected.append(dict(family=family['index'], rules=rules, candidate=str(path), candidate_sha256=digest))
    write(HERE / 'selection.json', dict(complete=True, selected=selected, decisions=decisions,
          screen_sha256=sha(HERE / 'screen.json'), pool_sha256=sha(HERE / 'pool.json'), completed_at_utc=now()))
    print('Selected families', [s['family'] for s in selected], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('phase', choices=('prepare', 'preflight', 'run'))
    p.add_argument('--workers', type=int, default=2); args = p.parse_args()
    if args.phase == 'prepare': prepare()
    elif args.phase == 'preflight': preflight()
    else:
        with exclusive_run(HERE / 'screen.lock'): run(args.workers)
