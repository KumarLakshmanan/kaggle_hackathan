"""Finite complete-schedule expansion; verified cached initial states."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.public_90_research_20260928 import research as prior
from diagnostics.stream_replay_io_20260928.fast_game_cached import play
from diagnostics.local_target_20260928.run_lock import exclusive_run

TARGET_IDS = ('live-114232208', 'live-114218866', 'live-114223292', 'live-114270587', 'live-114288168')
PRIOR_SHA = 'a588a300e8354b59f7edebbbdf74aee937efb3e7bd3c23736f11e1ec4317a7bb'


def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(row): return row['version'], row['fixture_id'], row['candidate_seat']
def now(): return datetime.now(timezone.utc).isoformat()
def write(p, data):
    with Path(p).open('x', encoding='utf-8') as out:
        json.dump(data, out, ensure_ascii=False, indent=2)


def prepare():
    prior.sources()
    old = prior.context()
    old_path = prior.HERE / 'target.json'
    assert sha(old_path) == PRIOR_SHA
    outcome = read(old_path)
    assert outcome['complete'] and outcome['clean'] and outcome['game_count'] == 320
    assert outcome['pool_sha256'] == sha(prior.HERE / 'pool.json')
    cached = ROOT / 'diagnostics/stream_replay_io_20260928'
    check = read(cached / 'cached_helper_parity.json')
    cm = read(cached / 'cached_helper_manifest.json')
    assert check['passed'] and check['manifest_sha256'] == sha(cached / 'cached_helper_manifest.json')
    assert all(sha(p) == v for p, v in cm['bindings'].items())
    spec = importlib.util.spec_from_file_location('residual_pool_source', prior.SOURCE)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    unique = {}
    for rid, actions in sorted(mod._DATA['routes'].items(), key=lambda x: int(x[0])):
        assert actions[:72] == mod._DATA['opening'][:72]
        unique.setdefault(prior.action_hash(actions), rid)
    assert len(unique) == 91
    chosen = []
    for shop, fixtures in old['fixtures'].items():
        for fixture in fixtures:
            if fixture['fixture_id'] in TARGET_IDS:
                chosen.append((shop, fixture))
    assert len(chosen) == 5 and len({s for s, _ in chosen}) == 5
    variants = []
    (HERE / 'candidates').mkdir(exist_ok=True)
    for shop, fixture in chosen:
        for rid in sorted(unique.values(), key=int):
            version = shop + '_' + rid
            path = HERE / 'candidates' / (version + '.py')
            digest = prior.candidate({shop: int(rid)}, path)
            variants.append(dict(version=version, shop=shop, route=rid, candidate=str(path),
                                 candidate_sha256=digest, fixture=fixture,
                                 action_sha256=prior.action_hash(mod._DATA['routes'][rid])))
    paths = [Path(__file__), HERE / 'PLAN.md', prior.SOURCE, prior.FULL, prior.TARGETS,
             prior.HERE / 'pool.json', prior.HERE / 'target.json', prior.HERE / 'research.py', prior.HERE / 'layer.py',
             cached / 'cached_input.py', cached / 'fast_game_cached.py', cached / 'initial_states.json',
             cached / 'cached_helper_parity.json', ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py']
    write(HERE / 'pool.json', dict(created_at_utc=now(), variants=variants,
          bindings={str(p): sha(p) for p in paths}, planned_games=910, prior_games=100, new_games=810))
    print('Frozen455 candidates,910 total games (100 prior,810 new).', flush=True)


def validate(row, variant):
    assert row['candidate_sha256'] == variant['candidate_sha256']
    assert row['fixture_id'] == variant['fixture']['fixture_id']
    assert row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
    assert not row['candidate_errors']
    telemetry = row['candidate_telemetry']
    assert telemetry['early_public_turns'] == 647
    assert telemetry['early_public_shop72'] == variant['shop'] and telemetry['early_public_route'] == variant['route']


def one(job):
    variant, seat = job
    result = play(variant['fixture'], variant['candidate'], variant['candidate_sha256'], seat)
    result.update(version=variant['version'], route=variant['route'], shop=variant['shop'],
                  team=variant['fixture']['team'], pool_sha256=sha(HERE / 'pool.json'), engineering_cached_input=True)
    validate(result, variant)
    return result


def run(workers):
    assert 1 <= workers <= 2
    pool = read(HERE / 'pool.json')
    assert all(sha(p) == v for p, v in pool['bindings'].items())
    assert all(sha(v['candidate']) == v['candidate_sha256'] for v in pool['variants'])
    indexed = {v['version']: v for v in pool['variants']}
    old = read(prior.HERE / 'target.json')
    rows = []
    for row in old['games']:
        if row['version'] not in indexed or row['fixture_id'] not in TARGET_IDS:
            continue
        variant = indexed[row['version']]
        validate(row, variant)
        assert row['pool_sha256'] == old['pool_sha256'] and row['helper_sha256'] == sha(prior.HERE / 'research.py')
        rows.append(dict(row, reused_from=str(prior.HERE / 'target.json'), reused_receipt_sha256=PRIOR_SHA))
    assert len(rows) == 100
    ledger = HERE / 'new_games.jsonl'
    if ledger.exists():
        for line in ledger.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            validate(row, indexed[row['version']])
            assert row['pool_sha256'] == sha(HERE / 'pool.json')
            rows.append(row)
    done = {key(r) for r in rows}
    assert len(done) == len(rows)
    pending = [(v, seat) for v in pool['variants'] for seat in (0, 1)
               if (v['version'], v['fixture']['fixture_id'], seat) not in done]
    assert len(rows) + len(pending) == 910
    print('Complete-route screen', len(rows), '/910; workers', workers, flush=True)
    with ledger.open('a', encoding='utf-8') as output:
        with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as executor:
            futures = {executor.submit(one, job): job for job in pending}
            for future in as_completed(futures):
                row = future.result()
                assert key(row) not in done
                done.add(key(row)); rows.append(row)
                output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush()
                if len(rows) % 10 == 0:
                    print('Complete-route screen', len(rows), '/910', row['version'], row['result'], row['margin'], flush=True)
    summaries, finalists = [], []
    for variant in pool['variants']:
        pair = [r for r in rows if r['version'] == variant['version']]
        assert len(pair) == 2
        summaries.append(dict(version=variant['version'], shop=variant['shop'], route=variant['route'],
             fixture_id=variant['fixture']['fixture_id'], sweep=all(r['result'] == 'win' for r in pair),
             points=sum({'win': 1, 'draw': .5, 'loss': 0}[r['result']] for r in pair),
             worst_margin=min(r['margin'] for r in pair), summed_margin=sum(r['margin'] for r in pair)))
    for shop in sorted({v['shop'] for v in pool['variants']}):
        good = [r for r in summaries if r['shop'] == shop and r['sweep']]
        good.sort(key=lambda r: (-r['points'], -r['worst_margin'], -r['summed_margin'], int(r['route'])))
        finalists.extend(r['version'] for r in good[:3])
    write(HERE / 'screen.json', dict(complete=True, clean=True, game_count=len(rows),
          prior_games=100, new_games=810, games=sorted(rows, key=key), summaries=summaries,
          finalists=finalists, pool_sha256=sha(HERE / 'pool.json'), completed_at_utc=now()))
    print('Completed910; finalist routes', finalists, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('phase', choices=('prepare', 'run'))
    p.add_argument('--workers', type=int, default=2); args = p.parse_args()
    if args.phase == 'prepare': prepare()
    else:
        with exclusive_run(HERE / 'screen.lock'): run(args.workers)
