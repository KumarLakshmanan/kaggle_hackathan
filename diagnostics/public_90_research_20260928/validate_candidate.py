"""Frozen original-framework parity and bounded saved-public-win regression."""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import importlib.metadata
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.public_90_research_20260928.research import read, write, sha, now, SOURCE, SOURCE_SHA, FULL
from diagnostics.local_target_20260928.run_lock import exclusive_run

CANDIDATE_SHA = '8ccb862a215da429097f9c2f895defe9b8aa90eaae019964e1d831c5d889b638'
MAIN_SHA = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
WINS = ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json'
CACHE = ROOT / 'diagnostics/stream_replay_io_20260928'
LEAF = ROOT / 'diagnostics/production_leaf_selector_20260928'
OLD = ROOT / 'diagnostics/public_loss_route_pool_20260928'
FIELDS = ('candidate_reward', 'opponent_reward', 'result', 'frames', 'candidate_status', 'opponent_status', 'candidate_telemetry')
INPUT_FIELDS = ('fixture_id', 'seed', 'source_replay_path', 'source_replay_sha256', 'source_action_tape_path', 'source_opponent_action_sha256')


def key(row):
    return row['fixture_id'], row['candidate_seat']


def clean(row):
    return row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE' and not row['candidate_errors'] and not row.get('opponent_errors')


def summarize(rows):
    pairs = {}
    for row in rows: pairs.setdefault(row['fixture_id'], []).append(row)
    assert all(len(pair) == 2 for pair in pairs.values())
    return dict(fixtures=len(pairs), games=len(rows), both_seat_wins=sum(all(r['result'] == 'win' for r in pair) for pair in pairs.values()),
                WDL=[sum(r['result'] == value for r in rows) for value in ('win', 'draw', 'loss')])


def prepare():
    assert not (HERE / 'validation_pool.json').exists()
    assert sha(SOURCE) == SOURCE_SHA and sha(ROOT / 'main.py') == MAIN_SHA
    full, selected, pool = read(HERE / 'combined_full.json'), read(HERE / 'selection.json'), read(HERE / 'pool.json')
    assert full['complete'] and full['passed'] and full['clean']
    assert sha(HERE / 'combined_full.json') == '330ab7523ed226366838283a46cb6689c19aca85d9988855390b65297de7743a'
    assert full['candidate_sha256'] == selected['candidate_sha256'] == CANDIDATE_SHA
    assert sha(selected['candidate']) == sha(selected['backup']) == CANDIDATE_SHA
    changed = [f for shop, fs in sorted(pool['fixtures'].items()) if shop in selected['replacements'] for f in fs]
    assert len(changed) == 16
    wins = read(WINS)['fixtures']; assert len(wins) == 54
    by_id = {f['fixture_id']: f for f in wins}
    source_receipt, source_pool = read(LEAF / 'controls.json'), read(LEAF / 'pool.json')
    assert sha(LEAF / 'controls.json') == '2ca9a8c946c7cab1f331bea3f8eea5c253226a5ca5a62427df374ea6f122a293'
    assert source_receipt['complete'] and source_receipt['clean'] and source_receipt['pool_sha256'] == sha(LEAF / 'pool.json')
    assert source_receipt['helper_sha256'] == sha(LEAF / 'study.py')
    for path, digest in source_pool['bindings'].items(): assert sha(path) == digest, path
    prior_inputs = {f['fixture_id']: f for f in source_pool['fixtures']}
    reused_source = []
    for row in source_receipt['games']:
        fixture = by_id[row['fixture_id']]
        assert all(fixture[k] == prior_inputs[row['fixture_id']][k] for k in INPUT_FIELDS)
        assert row['candidate_sha256'] == SOURCE_SHA and clean(row)
        assert row['pool_sha256'] == source_receipt['pool_sha256'] and row['helper_sha256'] == source_receipt['helper_sha256']
        reused_source.append(dict(row, reused_from=str(LEAF / 'controls.json'), reused_receipt_sha256=sha(LEAF / 'controls.json')))
    assert len(reused_source) == len({key(r) for r in reused_source}) == 56
    old_receipt, old_pool = read(OLD / 'controls.json'), read(OLD / 'pool.json')
    assert sha(OLD / 'controls.json') == '706ee8d1420a1e8a6db71b3aea915ec57abaa2ccf2e6a6b87c8a0fea8f71edc4'
    assert old_receipt['complete'] and old_receipt['clean'] and old_receipt['pool_sha256'] == sha(OLD / 'pool.json')
    assert old_pool['fast_helper_sha256'] == sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py')
    assert old_pool['core_sha256'] == sha(ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py')
    old_inputs = {f['fixture_id']: f for fs in old_pool['fixtures'].values() for f in fs}
    reused_main = []
    for row in old_receipt['games']:
        if row['candidate_sha256'] != MAIN_SHA: continue
        fixture = by_id[row['fixture_id']]
        assert all(fixture[k] == old_inputs[row['fixture_id']][k] for k in INPUT_FIELDS)
        assert clean(row) and row['seed'] == fixture['seed']
        reused_main.append(dict(row, reused_from=str(OLD / 'controls.json'), reused_receipt_sha256=sha(OLD / 'controls.json')))
    assert len(reused_main) == len({key(r) for r in reused_main}) == 26
    assert len({r['fixture_id'] for r in reused_main}) == 13
    assert read(CACHE / 'cached_helper_parity.json')['passed']
    assert importlib.metadata.version('kaggle_environments') == '1.32.7'
    package = Path(importlib.util.find_spec('kaggle_environments').origin).parent
    files = [Path(__file__), HERE / 'VALIDATION_PLAN.md', HERE / 'combined_full.json', HERE / 'selection.json', HERE / 'pool.json',
             SOURCE, Path(selected['candidate']), Path(selected['backup']), ROOT / 'main.py', FULL, WINS,
             ROOT / 'diagnostics/opening_probe_v2_20260928/qualify.py', ROOT / 'paired_benchmark.py',
             ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py', ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py',
             CACHE / 'cached_helper_parity.json', CACHE / 'cached_helper_manifest.json', CACHE / 'cached_input.py', CACHE / 'fast_game_cached.py', CACHE / 'initial_states.json',
             LEAF / 'controls.json', LEAF / 'pool.json', LEAF / 'study.py', OLD / 'controls.json', OLD / 'pool.json', OLD / 'search.py',
             package / 'envs/kaggriculture/kaggriculture.py', package / 'envs/kaggriculture/kaggriculture.json', package / 'core.py', package / 'agent.py']
    bindings = {str(path): sha(path) for path in files}
    completed = {key(r) for r in reused_source}
    native_jobs = [dict(version='8ccb', fixture_id=f['fixture_id'], rival=f['fixture_id'], team=f['team'],
                        seed=int(f['seed']), candidate_seat=seat, path=selected['candidate'], candidate_sha256=CANDIDATE_SHA,
                        opponent='rawroute:' + f['source_action_tape_path'], opponent_action_sha256=f['source_opponent_action_sha256'],
                        source_replay_sha256=f['source_replay_sha256']) for f in changed for seat in (0, 1)]
    source_jobs = [dict(fixture_id=f['fixture_id'], candidate_seat=seat) for f in wins for seat in (0, 1) if (f['fixture_id'], seat) not in completed]
    candidate_jobs = [dict(fixture_id=f['fixture_id'], candidate_seat=seat) for f in wins for seat in (0, 1)]
    assert len(native_jobs) == 32 and len(source_jobs) == 52 and len(candidate_jobs) == 108
    result = dict(created_at_utc=now(), no_new_outcomes=True, bindings=bindings, candidate=selected['candidate'], backup=selected['backup'],
                  candidate_sha256=CANDIDATE_SHA, source_sha256=SOURCE_SHA, native_jobs=native_jobs, source_jobs=source_jobs,
                  candidate_jobs=candidate_jobs, fixtures=wins, changed_fixtures=changed, reused_source=reused_source, reused_main=reused_main)
    write(HERE / 'validation_pool.json', result)
    print(json.dumps(dict(pool_sha256=sha(HERE / 'validation_pool.json'), plan_sha256=sha(HERE / 'VALIDATION_PLAN.md'),
                         helper_sha256=sha(__file__), native_games=32, source_new=52, candidate_new=108, source_reused=56, main_reused=26), indent=2), flush=True)


def context():
    pool = read(HERE / 'validation_pool.json')
    for path, digest in pool['bindings'].items(): assert sha(path) == digest, path
    return pool


def native_worker(job):
    from diagnostics.opening_probe_v2_20260928.qualify import play
    from paired_benchmark import engine_version
    assert engine_version == '1.32.7'
    return play(job)


def run(phase):
    pool = context(); pool_sha = sha(HERE / 'validation_pool.json')
    destination = HERE / (phase + '.json'); checkpoint = HERE / (phase + '.jsonl')
    assert not destination.exists()
    if phase != 'native_parity':
        native = read(HERE / 'native_parity.json')
        assert native['complete'] and native['passed'] and native['validation_pool_sha256'] == pool_sha
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    if phase == 'public_source' and not rows:
        rows = [dict(r, validation_pool_sha256=pool_sha) for r in pool['reused_source']]
        checkpoint.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    expected = pool['native_jobs'] if phase == 'native_parity' else pool['candidate_jobs']
    wanted = {key(j): j for j in expected}; assert len(wanted) == len(expected)
    digest = SOURCE_SHA if phase == 'public_source' else CANDIDATE_SHA
    for row in rows:
        assert key(row) in wanted and row['candidate_sha256'] == digest and row['validation_pool_sha256'] == pool_sha
        assert clean(row), 'Checkpoint contains a technical failure requiring a separate diagnosis.'
        if phase == 'native_parity': assert all(row[k] == v for k, v in wanted[key(row)].items())
    done = {key(r) for r in rows}; assert len(done) == len(rows)
    pending = [job for job in expected if key(job) not in done]
    fast = {key(r): r for r in read(HERE / 'combined_full.json')['games']}
    source = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games'] if r['version'] == 'integrated'}
    fixtures = {f['fixture_id']: f for f in pool['fixtures']}
    if phase == 'public_candidate':
        public_source = read(HERE / 'public_source.json')
        assert public_source['complete'] and public_source['clean'] and public_source['validation_pool_sha256'] == pool_sha
        source = {key(r): r for r in public_source['games']}
    def retain(row, output):
        assert key(row) not in done and row['candidate_sha256'] == digest
        row['validation_pool_sha256'] = pool_sha
        done.add(key(row)); rows.append(row)
        output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush()
        print(f'{phase} {len(rows)}/{len(expected)} {row["team"]} seat{row["candidate_seat"]} {row["result"]} {row["margin"]:+.0f}', flush=True)
        assert clean(row), 'Technical execution failure retained; stop before another game.'
    with checkpoint.open('a', encoding='utf-8') as output:
        if phase == 'native_parity':
            for start in range(0, len(pending), 4):
                with ProcessPoolExecutor(max_workers=1) as executor:
                    for row in executor.map(native_worker, pending[start:start + 4]): retain(row, output)
        else:
            from diagnostics.stream_replay_io_20260928.fast_game_cached import play
            path = str(SOURCE) if phase == 'public_source' else pool['candidate']
            for job in pending:
                fixture = fixtures[job['fixture_id']]
                row = play(fixture, path, digest, job['candidate_seat'])
                row.update(team=fixture['team'], source_replay_sha256=fixture['source_replay_sha256'],
                           source_opponent_action_sha256=fixture['source_opponent_action_sha256'])
                retain(row, output)
    assert len(rows) == len(expected)
    mismatches, regressions = [], []
    if phase == 'native_parity':
        mismatches = [dict(key=key(r), fields=[f for f in FIELDS if r[f] != fast[key(r)][f]]) for r in rows if any(r[f] != fast[key(r)][f] for f in FIELDS)]
        regressions = [dict(key=key(r), control='source367') for r in rows if source[key(r)]['result'] == 'win' and r['result'] != 'win']
    if phase == 'public_candidate':
        tested = {key(r): r for r in rows}
        regressions = [dict(key=key(r), control='source367') for r in rows if source[key(r)]['result'] == 'win' and r['result'] != 'win']
        regressions += [dict(key=key(r), control='available_main4ee') for r in pool['reused_main'] if r['result'] == 'win' and tested[key(r)]['result'] != 'win']
        regressions += [dict(key=(f['fixture_id'], f['source_candidate_seat']), control='recorded_public_win') for f in pool['fixtures'] if tested[(f['fixture_id'], f['source_candidate_seat'])]['result'] != 'win']
        for row in rows:
            base = source[key(row)]
            row.update(source_result=base['result'], source_margin=base['margin'], delta_own=row['candidate_reward'] - base['candidate_reward'],
                       delta_rival=row['opponent_reward'] - base['opponent_reward'], delta_margin=row['margin'] - base['margin'])
    result = dict(complete=True, passed=all(clean(r) for r in rows) and not mismatches and not regressions, clean=all(clean(r) for r in rows),
                  phase=phase, framework='original Kaggle env.run' if phase == 'native_parity' else 'cached pure native transitions',
                  diagnostic_only=True, validation_pool_sha256=pool_sha, candidate_sha256=digest, helper_sha256=sha(__file__),
                  completed_at_utc=now(), mismatches=mismatches, regressions=regressions, summary=summarize(rows), games=rows)
    write(destination, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'games'}, indent=2, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('prepare', 'native_parity', 'public_source', 'public_candidate'))
    args = parser.parse_args()
    with exclusive_run(HERE / 'validation.lock'):
        prepare() if args.phase == 'prepare' else run(args.phase)
