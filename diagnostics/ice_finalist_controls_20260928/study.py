"""Frozen three-route Ice controls using existing public production features."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import gc
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.production_leaf_selector_20260928 import study as previous
from diagnostics.stream_replay_io_20260928.fast_game_cached import play
from diagnostics.local_target_20260928.run_lock import exclusive_run

LEAF = 'ICE_CREAM_SHOP|M8+|C>S'
ROUTES = ('113384557', '113360743', '113801171')
REQUIRED = ('live-114288168', 'live-114258293')


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p, value):
    with Path(p).open('x', encoding='utf-8') as stream: json.dump(value, stream, ensure_ascii=False, indent=2)
def now(): return datetime.now(timezone.utc).isoformat()
def key(row): return row['version'], row['fixture_id'], row['candidate_seat']


def prepare():
    old = previous.context(); controls = previous.source_controls()
    source_screen = ROOT / 'diagnostics/residual_91_routes_20260928/screen.json'
    assert sha(source_screen) == 'efab80fb79d112082ade79dea84acac0c872e383aaade2de0abdaa6a211b80b7'
    source = read(source_screen)
    assert set('ICE_CREAM_SHOP_' + r for r in ROUTES).issubset(source['finalists'])
    features = read(previous.PRIOR / 'matched_features72.json')['rows']
    fids = sorted({r['fixture_id'] for r in features if previous.feature_key(r, 'production') == LEAF})
    assert len(fids) == 7 and all((fid, s) in controls for fid in fids for s in (0, 1))
    assert set(REQUIRED).issubset(fids)
    fixtures = [f for f in old['fixtures'] if f['fixture_id'] in fids]
    variants = []
    for route in ROUTES:
        path = HERE / ('candidate_' + route + '.py')
        digest = previous.build('production', {LEAF: int(route)}, path)
        module = previous.load(path)
        assert module._DATA['routes'][route][:72] == module._DATA['opening'][:72]
        for row in features:
            assert module._production_leaf_key(previous.observation(row)) == previous.feature_key(row, 'production')
        module._production_leaf_commit(LEAF, route)
        assert module._hire_recovery_schedule(dict(step=144, town={'unlocked_shops': ['ICE_CREAM_SHOP', 'BAKERY']})) == module._DATA['routes'][route]
        module._production_leaf_reset(); assert module._DATA['route_map'] == module._PRODUCTION_LEAF_BASE_MAP
        del module; gc.collect()
        variants.append(dict(version=route, candidate=str(path), candidate_sha256=digest))
    paths = [Path(__file__), HERE / 'PLAN.md', previous.HERE / 'pool.json', previous.HERE / 'study.py',
             previous.HERE / 'layer.py', previous.HERE / 'controls.json', previous.FULL,
             previous.SOURCE, source_screen, previous.PRIOR / 'matched_features72.json',
             previous.CACHE / 'fast_game_cached.py', previous.CACHE / 'cached_input.py', previous.CACHE / 'initial_states.json']
    controls = [dict(controls[(fid, s)], fixture_id=fid) for fid in fids for s in (0, 1)]
    reference = [r for r in source['games'] if r['version'] in {'ICE_CREAM_SHOP_' + route for route in ROUTES}]
    assert len(reference) == 6
    write(HERE / 'pool.json', dict(frozen_at_utc=now(), variants=variants, fixtures=fixtures,
          controls=controls, ghost_reference=reference, planned_games=42,
          bindings={str(p): sha(p) for p in paths}))
    print('Frozen three Ice finalists;42 affected games.', flush=True)


def valid(row, variant):
    assert row['candidate_sha256'] == variant['candidate_sha256']
    assert row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
    assert not row['candidate_errors']
    tel = row['candidate_telemetry']
    assert tel['production_leaf_key72'] == LEAF and tel['production_leaf_route'] == variant['version'] and tel['production_leaf_turns'] == 647


def one(job):
    variant, fixture, seat = job
    row = play(fixture, variant['candidate'], variant['candidate_sha256'], seat)
    row.update(version=variant['version'], pool_sha256=sha(HERE / 'pool.json'))
    valid(row, variant)
    return row


def run(workers):
    assert 1 <= workers <= 2
    pool = read(HERE / 'pool.json')
    assert all(sha(p) == h for p, h in pool['bindings'].items())
    assert all(sha(v['candidate']) == v['candidate_sha256'] for v in pool['variants'])
    jobs = {(v['version'], f['fixture_id'], s): (v, f, s) for v in pool['variants'] for f in pool['fixtures'] for s in (0, 1)}
    assert len(jobs) == 42
    ledger = HERE / 'screen.jsonl'
    rows = [json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    done = {key(r) for r in rows}; assert len(rows) == len(done)
    for row in rows:
        valid(row, jobs[key(row)][0]); assert row['pool_sha256'] == sha(HERE / 'pool.json')
    with ledger.open('a', encoding='utf-8') as stream:
        with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as executor:
            futures = [executor.submit(one, job) for k, job in jobs.items() if k not in done]
            for future in as_completed(futures):
                row = future.result(); assert key(row) not in done
                done.add(key(row)); rows.append(row)
                stream.write(json.dumps(row, ensure_ascii=False) + '\n'); stream.flush()
                print('Ice controls', len(rows), '/42', row['version'], row['fixture_id'], row['margin'], flush=True)
    controls = {(r['fixture_id'], r['candidate_seat']): r for r in pool['controls']}
    summaries = []
    for variant in pool['variants']:
        rr = [r for r in rows if r['version'] == variant['version']]
        for row in rr:
            if row['fixture_id'] == REQUIRED[0]:
                expected = next(r for r in pool['ghost_reference'] if r['route'] == variant['version'] and r['candidate_seat'] == row['candidate_seat'])
                assert all(row[k] == expected[k] for k in ('candidate_reward', 'opponent_reward', 'result', 'frames', 'candidate_status', 'opponent_status'))
        losses = [key(r) for r in rr if controls[(r['fixture_id'], r['candidate_seat'])]['result'] == 'win' and r['result'] != 'win']
        required = all(r['result'] == 'win' for r in rr if r['fixture_id'] in REQUIRED)
        summaries.append(dict(version=variant['version'], regressions=losses, required_rescues=required,
             passed=not losses and required,
             sweeps=sum(all(r['result'] == 'win' for r in rr if r['fixture_id'] == f['fixture_id']) for f in pool['fixtures']),
             points=sum({'win': 1, 'draw': .5, 'loss': 0}[r['result']] for r in rr),
             delta_margin=sum(r['margin'] - controls[(r['fixture_id'], r['candidate_seat'])]['margin'] for r in rr)))
    eligible = sorted([s for s in summaries if s['passed']], key=lambda s: (-s['sweeps'], -s['points'], -s['delta_margin'], int(s['version'])))
    write(HERE / 'screen.json', dict(complete=True, clean=True, games=rows, game_count=42, summaries=summaries,
          selected=eligible[0] if eligible else None, pool_sha256=sha(HERE / 'pool.json'), completed_at_utc=now()))
    print('Ice finalist passes:', [s['version'] for s in eligible], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('phase', choices=('prepare', 'run')); p.add_argument('--workers', type=int, default=2); args = p.parse_args()
    if args.phase == 'prepare': prepare()
    else:
        with exclusive_run(HERE / 'screen.lock'): run(args.workers)
