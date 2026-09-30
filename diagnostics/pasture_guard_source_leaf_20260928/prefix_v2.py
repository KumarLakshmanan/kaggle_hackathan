"""Frozen pre-outcome native-prefix proof runner for the pasture study.

`freeze` and `verify` are static only. `run` performs fourteen bounded
observation-72 engineering comparisons and never runs a complete game.
"""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import argparse
import copy
import gc
import gzip
import hashlib
import importlib.util
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
POOL_PATH = HERE / 'pool.json'
FEATURES_PATH = HERE / 'feature_rows.json'
STATIC_PATH = HERE / 'static_preflight.json'
PLAN_PATH = HERE / 'PREFIX_PLAN_V2.md'
MANIFEST_PATH = HERE / 'prefix_manifest_v2.json'
PROGRESS_PATH = HERE / 'prefix_v2_progress.jsonl'
RESULTS_PATH = HERE / 'prefix_v2_results.json'
LOCK_PATH = HERE / 'prefix_v2.lock'
BASE_PREFIX_PATH = HERE / 'prefix.py'
BASE_MANIFEST_PATH = HERE / 'prefix_manifest.json'
BASE_PLAN_PATH = HERE / 'PREFIX_PLAN.md'
BASE_PROGRESS_PATH = HERE / 'prefix_progress.jsonl'
SOURCE_A44 = ROOT / 'diagnostics/upload_adaptive_donor_20260928_a44c8c2c/main.py'
SOURCE32 = ROOT / 'main_candidate_animal_liquidity_20260928_32e299fe.py'
CACHE_HELPER = ROOT / 'diagnostics/stream_replay_io_20260928/cached_input.py'
INITIAL_CACHE = ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json'
NATIVE_CORE = ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py'
NATIVE_CHECK = ROOT / 'diagnostics/physical_route_rollout_20260928/check.py'
RUN_LOCK = ROOT / 'diagnostics/local_target_20260928/run_lock.py'
DONOR_IDS = (
    'live-114232208', 'live-114235177', 'live-114279308',
    'top20-03-Boey-114266440', 'top20-06-Majkel1337-114263239',
)
THIRD_ID = 'live-114274897'
CHRIS_ID = 'public-win-114193811'
LEAF_KEY = 'BRUNCH_SPOT|M8+|C>S|G+'
LEAF_ROUTE = '113332529'
EXPECTED_A44 = 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
EXPECTED_32E = '32e299fe047a79290d5025b4e2be455ae13d948020beae2d77cb44a7c17dc31e'


def sha(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest_object(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path | str):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_new(path: Path, payload) -> None:
    raw = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(raw)


def verified_engine_source() -> Path:
    spec = importlib.util.find_spec('kaggle_environments')
    if spec is None or not spec.origin:
        raise RuntimeError('installed kaggle-environments engine source is unavailable')
    path = Path(spec.origin).parent / 'envs' / 'kaggriculture' / 'kaggriculture.py'
    if not path.is_file():
        raise RuntimeError(f'installed Kaggriculture engine source is missing: {path}')
    return path.resolve()


def canonical_action_tape(fixture: dict, bindings: dict[str, str]) -> list:
    path = Path(fixture['source_action_tape_path']).resolve()
    expected_file = bindings.get(str(path))
    if not expected_file or sha(path) != expected_file:
        raise AssertionError(f'action-tape file is not frozen in the pool: {path}')
    tape = json.loads(gzip.decompress(path.read_bytes()))['actions']
    hashes = [hashlib.sha256(json.dumps(tape, sort_keys=sort_keys,
                            separators=(',', ':')).encode()).hexdigest()
              for sort_keys in (False, True)]
    if len(tape) != 719 or fixture['source_opponent_action_sha256'] not in hashes:
        raise AssertionError(f'action-tape payload does not match fixture: {fixture["fixture_id"]}')
    return tape


def validate_static() -> tuple[dict, dict, dict]:
    pool = read_json(POOL_PATH)
    features = read_json(FEATURES_PATH)
    static = read_json(STATIC_PATH)
    if not static['complete'] or not static['passed']:
        raise AssertionError('the a44-bound static preflight did not pass')
    if pool['candidate']['sha256'] != sha(pool['candidate']['path']):
        raise AssertionError('candidate no longer matches the static pool')
    if pool['feature_rows']['sha256'] != sha(FEATURES_PATH):
        raise AssertionError('feature rows no longer match the static pool')
    if static['pool_sha256'] != sha(POOL_PATH) or static['feature_rows_sha256'] != sha(FEATURES_PATH):
        raise AssertionError('static receipt no longer matches the static pool/features')
    for path, digest in pool['bindings'].items():
        if sha(path) != digest:
            raise AssertionError(f'frozen pool binding changed: {path}')
    if pool['source']['sha256'] != EXPECTED_A44 or sha(SOURCE_A44) != EXPECTED_A44:
        raise AssertionError('exact a44 comparison source changed')
    if pool['source32_prefix_comparator']['sha256'] != EXPECTED_32E or sha(SOURCE32) != EXPECTED_32E:
        raise AssertionError('exact32e source comparator changed')
    if features['row_count'] != 208 or len(features['rows']) != 208:
        raise AssertionError('the frozen 208-row feature receipt is incomplete')
    return pool, features, static


def pool_feature_index(features: dict) -> dict:
    return {(row['provenance']['fixture_id'], row['provenance']['candidate_seat']): row
            for row in features['rows']}


def make_jobs(pool: dict, features: dict) -> list[dict]:
    fixtures = {row['fixture_id']: row['fixture'] for row in pool['candidate_jobs']}
    controls = {(row['fixture_id'], row['candidate_seat']): row
                for row in pool['reused_exact_a44_controls']}
    feature_index = pool_feature_index(features)
    jobs = []
    for fixture_id in DONOR_IDS:
        for seat in (0, 1):
            control = controls[(fixture_id, seat)]
            feature = feature_index[(fixture_id, seat)]
            selector = feature['selector_features']
            if not selector.get('obs72_first_revealed_shop') or selector.get('obs72_leaf_key') == LEAF_KEY:
                raise AssertionError(f'donor prefix has an invalid observation-72 leaf binding: {fixture_id}/{seat}')
            fixture = fixtures[fixture_id]
            fixture_file_bindings = {
                str(Path(fixture[field]).resolve()): pool['bindings'][str(Path(fixture[field]).resolve())]
                for field in ('source_replay_path', 'source_action_tape_path')}
            jobs.append({
                'job_id': f'donor-a44-{fixture_id}-seat{seat}',
                'fixture_id': fixture_id, 'candidate_seat': seat,
                'comparison': 'candidate_vs_exact_a44',
                'candidate_path': pool['candidate']['path'],
                'candidate_sha256': pool['candidate']['sha256'],
                'reference_path': str(SOURCE_A44.resolve()),
                'reference_sha256': EXPECTED_A44,
                'fixture': fixture,
                'fixture_file_bindings': fixture_file_bindings,
                'expected_a44_control': control,
                'saved_a44_trace_path': control['trace_path'],
                'saved_a44_trace_sha256': control['trace_sha256'],
                'frozen_feature_row': feature,
            })
    for fixture_id in (THIRD_ID, CHRIS_ID):
        for seat in (0, 1):
            feature = feature_index[(fixture_id, seat)]
            selector = feature['selector_features']
            if not selector.get('obs72_first_revealed_shop'):
                raise AssertionError(f'affected prefix has no revealed shop at observation 72: {fixture_id}/{seat}')
            if fixture_id == THIRD_ID and selector.get('obs72_leaf_key') != LEAF_KEY:
                raise AssertionError(f'THIRD frozen leaf key changed: {fixture_id}/{seat}')
            if fixture_id == CHRIS_ID and selector.get('obs72_leaf_key') == LEAF_KEY:
                raise AssertionError(f'ChrisTu frozen context unexpectedly matches the source leaf: {fixture_id}/{seat}')
            fixture = fixtures[fixture_id]
            fixture_file_bindings = {
                str(Path(fixture[field]).resolve()): pool['bindings'][str(Path(fixture[field]).resolve())]
                for field in ('source_replay_path', 'source_action_tape_path')}
            jobs.append({
                'job_id': f'source-fallback-{fixture_id}-seat{seat}',
                'fixture_id': fixture_id, 'candidate_seat': seat,
                'comparison': 'candidate_vs_exact32e_source',
                'candidate_path': pool['candidate']['path'],
                'candidate_sha256': pool['candidate']['sha256'],
                'reference_path': str(SOURCE32.resolve()),
                'reference_sha256': EXPECTED_32E,
                'fixture': fixture,
                'fixture_file_bindings': fixture_file_bindings,
                'expected_a44_control': controls.get((fixture_id, seat)),
                'saved_a44_trace_path': feature['provenance']['trace_path'],
                'saved_a44_trace_sha256': feature['provenance']['trace_sha256'],
                'frozen_feature_row': feature,
            })
    if len(jobs) != 14 or len({job['job_id'] for job in jobs}) != 14:
        raise AssertionError('prefix job matrix must be exactly fourteen unique comparisons')
    return jobs


def freeze() -> None:
    if MANIFEST_PATH.exists() or RESULTS_PATH.exists() or PROGRESS_PATH.exists() or LOCK_PATH.exists():
        raise FileExistsError('prefix freeze/run outputs already exist; use verify or inspect them')
    pool, features, _ = validate_static()
    jobs = make_jobs(pool, features)
    engine_path = verified_engine_source()
    bindings = dict(pool['bindings'])
    direct = [POOL_PATH, FEATURES_PATH, STATIC_PATH, PLAN_PATH, Path(__file__),
              BASE_PREFIX_PATH, BASE_MANIFEST_PATH, BASE_PLAN_PATH, BASE_PROGRESS_PATH,
              SOURCE_A44, SOURCE32, CACHE_HELPER, INITIAL_CACHE, NATIVE_CORE, NATIVE_CHECK, RUN_LOCK,
              Path(pool['source_receipts']['a44_full_target_results']['path']),
              Path(pool['source_receipts']['a44_public54_discovery']['path']), engine_path]
    for path in direct:
        bindings[str(path.resolve())] = sha(path)
    for job in jobs:
        fixture = job['fixture']
        for field in ('source_replay_path', 'source_action_tape_path'):
            path = Path(fixture[field]).resolve()
            if str(path) not in bindings:
                raise AssertionError(f'prefix input is absent from frozen file bindings: {path}')
        canonical_action_tape(fixture, bindings)
    selected_fixtures = {job['fixture_id']: job['fixture'] for job in jobs}
    seeds = {fid: int(row['seed']) for fid, row in selected_fixtures.items()}
    if len(seeds) != 7:
        raise AssertionError('prefix manifest must bind the seven frozen fixture seeds')
    reused_controls = [job['expected_a44_control'] for job in jobs
                       if job['comparison'] == 'candidate_vs_exact_a44']
    if len(reused_controls) != 10 or any(row['candidate_sha256'] != EXPECTED_A44 for row in reused_controls):
        raise AssertionError('ten exact-a44 donor control rows are not bound')
    manifest = {
        'schema': 'pasture-guard-native-prefix-manifest-v1',
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'engineering pre-outcome prefix proof; no complete outcome games',
        'version_lineage': {
            'supersedes_runner_path': str(BASE_PREFIX_PATH.resolve()),
            'supersedes_runner_sha256': sha(BASE_PREFIX_PATH),
            'supersedes_manifest_path': str(BASE_MANIFEST_PATH.resolve()),
            'supersedes_manifest_sha256': sha(BASE_MANIFEST_PATH),
            'original_progress_path': str(BASE_PROGRESS_PATH.resolve()),
            'original_progress_sha256': sha(BASE_PROGRESS_PATH),
            'correction': 'observation-1 instrumentation records an empty unlocked-shops list as pre-shop state; a leaf key is required only at observation 72',
        },
        'candidate': {'path': pool['candidate']['path'], 'sha256': pool['candidate']['sha256']},
        'pool': {'path': str(POOL_PATH.resolve()), 'sha256': sha(POOL_PATH)},
        'feature_rows': {'path': str(FEATURES_PATH.resolve()), 'sha256': sha(FEATURES_PATH), 'rows': 208},
        'static_receipt': {'path': str(STATIC_PATH.resolve()), 'sha256': sha(STATIC_PATH)},
        'source_comparators': {
            'exact_a44': {'path': str(SOURCE_A44.resolve()), 'sha256': EXPECTED_A44},
            'exact32e_source': {'path': str(SOURCE32.resolve()), 'sha256': EXPECTED_32E},
        },
        'fixtures_and_seeds': [
            {'fixture_id': fid, 'seed': seed,
             'source_replay_path': selected_fixtures[fid]['source_replay_path'],
             'source_replay_sha256': selected_fixtures[fid]['source_replay_sha256'],
             'action_tape_path': selected_fixtures[fid]['source_action_tape_path'],
             'source_opponent_action_sha256': selected_fixtures[fid]['source_opponent_action_sha256']}
            for fid, seed in sorted(seeds.items())],
        'control_bindings': {
            'reused_exact_a44_control_rows': pool['reused_exact_a44_controls'],
            'reused_exact_a44_donor_controls': [
                {key: row.get(key) for key in (
                    'fixture_id', 'candidate_seat', 'candidate_sha256', 'result',
                    'candidate_reward', 'opponent_reward', 'trace_path', 'trace_sha256')}
                for row in reused_controls],
            'affected_context_a44_trace_provenance': [
                {'fixture_id': job['fixture_id'], 'candidate_seat': job['candidate_seat'],
                 'trace_path': job['saved_a44_trace_path'],
                 'trace_sha256': job['saved_a44_trace_sha256']}
                for job in jobs if job['comparison'] == 'candidate_vs_exact32e_source'],
            'fresh_exact_a44_christu_controls_staged': pool['fresh_exact_a44_control_jobs'],
            'a44_full_results_receipt': pool['source_receipts']['a44_full_target_results'],
            'a44_public54_discovery_receipt': pool['source_receipts']['a44_public54_discovery'],
        },
        'runtime_binding': {
            'native_core_path': str(NATIVE_CORE.resolve()), 'native_core_sha256': sha(NATIVE_CORE),
            'state_helper_path': str(NATIVE_CHECK.resolve()), 'state_helper_sha256': sha(NATIVE_CHECK),
            'run_lock_path': str(RUN_LOCK.resolve()), 'run_lock_sha256': sha(RUN_LOCK),
            'cache_reader_path': str(CACHE_HELPER.resolve()), 'cache_reader_sha256': sha(CACHE_HELPER),
            'initial_state_cache_path': str(INITIAL_CACHE.resolve()), 'initial_state_cache_sha256': sha(INITIAL_CACHE),
            'installed_engine_source_path': str(engine_path), 'installed_engine_source_sha256': sha(engine_path),
            'policy_configuration_seed': None,
            'native_environment_info_seed': 'fixture seed bound above',
        },
        'jobs': jobs,
        'job_matrix_sha256': digest_object(jobs),
        'job_count': len(jobs), 'observation_limit': 72, 'required_workers': 1,
        'max_jobs_per_worker_process': 4,
        'pass_gates': {
            'donor_comparisons': 'candidate and exact a44 actions/observations equal at observations 0..72; saved a44 trace prefix reproduces',
            'affected_opening': 'candidate matches exact32e turn-0 common and turn-1 source actions and own physical/private state after both turns',
            'affected_state': 'own physical/private state exact at observations 2..72; cash, shared market and actions ledgered separately',
            'source_selection': 'candidate bridge_requested=source and bridge_selected=source for both seats of THIRD and ChrisTu',
            'leaf': '113332529 active on both THIRD seats only; inactive on ChrisTu and all five donor fixtures',
            'errors': 'zero policy, bridge guard, bridge source, collision, procurement, or engine errors',
        },
        'output_paths': {
            'progress': str(PROGRESS_PATH.resolve()),
            'receipt': str(RESULTS_PATH.resolve()),
            'exclusive_run_lock': str(LOCK_PATH.resolve()),
        },
        'file_bindings': dict(sorted(bindings.items())),
    }
    manifest['control_bindings_sha256'] = digest_object(manifest['control_bindings'])
    write_new(MANIFEST_PATH, manifest)
    print(json.dumps({
        'frozen': True, 'manifest': str(MANIFEST_PATH.resolve()),
        'manifest_sha256': sha(MANIFEST_PATH), 'job_count': len(jobs),
        'donor_a44_jobs': sum(j['comparison'] == 'candidate_vs_exact_a44' for j in jobs),
        'affected_32e_jobs': sum(j['comparison'] == 'candidate_vs_exact32e_source' for j in jobs),
        'fixture_seed_bindings': len(seeds), 'engine_sha256': sha(engine_path),
        'runner_sha256': sha(Path(__file__)), 'simulations_run': 0,
    }, indent=2), flush=True)


def verify_manifest() -> dict:
    manifest = read_json(MANIFEST_PATH)
    for path, digest in manifest['file_bindings'].items():
        if sha(path) != digest:
            raise AssertionError(f'prefix manifest binding changed: {path}')
    pool, features, static = validate_static()
    if manifest['pool']['sha256'] != sha(POOL_PATH):
        raise AssertionError('prefix manifest pool hash is stale')
    if manifest['feature_rows']['sha256'] != sha(FEATURES_PATH):
        raise AssertionError('prefix manifest feature hash is stale')
    if manifest['candidate']['sha256'] != pool['candidate']['sha256']:
        raise AssertionError('prefix manifest candidate hash is stale')
    if (manifest['version_lineage']['supersedes_runner_sha256'] != sha(BASE_PREFIX_PATH)
            or manifest['version_lineage']['supersedes_manifest_sha256'] != sha(BASE_MANIFEST_PATH)
            or manifest['version_lineage']['original_progress_sha256'] != sha(BASE_PROGRESS_PATH)):
        raise AssertionError('v2 lineage no longer matches the preserved original freeze')
    if manifest['static_receipt']['sha256'] != sha(STATIC_PATH) or not static['passed']:
        raise AssertionError('prefix manifest static receipt is stale or failed')
    jobs = make_jobs(pool, features)
    if (jobs != manifest['jobs'] or len(jobs) != manifest['job_count'] or len(jobs) != 14
            or digest_object(jobs) != manifest['job_matrix_sha256']):
        raise AssertionError('prefix job matrix changed since freeze')
    if digest_object(manifest['control_bindings']) != manifest['control_bindings_sha256']:
        raise AssertionError('prefix control-binding receipt hash is inconsistent')
    if manifest['control_bindings']['reused_exact_a44_control_rows'] != pool['reused_exact_a44_controls']:
        raise AssertionError('prefix reused-a44 control rows differ from the frozen pool')
    if manifest['control_bindings']['fresh_exact_a44_christu_controls_staged'] != pool['fresh_exact_a44_control_jobs']:
        raise AssertionError('prefix fresh exact-a44 ChrisTu jobs differ from the frozen pool')
    fixture_by_id = {job['fixture_id']: job['fixture'] for job in jobs}
    expected_fixture_bindings = [
        {'fixture_id': fid, 'seed': int(fixture_by_id[fid]['seed']),
         'source_replay_path': fixture_by_id[fid]['source_replay_path'],
         'source_replay_sha256': fixture_by_id[fid]['source_replay_sha256'],
         'action_tape_path': fixture_by_id[fid]['source_action_tape_path'],
         'source_opponent_action_sha256': fixture_by_id[fid]['source_opponent_action_sha256']}
        for fid in sorted(fixture_by_id)]
    if expected_fixture_bindings != manifest['fixtures_and_seeds']:
        raise AssertionError('prefix fixture, seed, replay, or action-tape binding changed')
    engine_path = verified_engine_source()
    if str(engine_path) != manifest['runtime_binding']['installed_engine_source_path']:
        raise AssertionError('installed Kaggriculture engine path changed')
    for job in jobs:
        canonical_action_tape(job['fixture'], manifest['file_bindings'])
    return manifest


def load_policy(path: str, digest: str, module_name: str):
    if sha(path) != digest:
        raise AssertionError(f'policy hash changed before import: {path}')
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def policy_observation(state, seat: int) -> dict:
    return deepcopy(dict(state[seat].observation, remainingOverageTime=60.0))


def own_physical_private(obs: dict, seat: int) -> dict:
    farm = deepcopy(obs['farms'][seat])
    farm.pop('money', None)
    return {'farm_without_cash': farm, 'private': deepcopy(obs['private'])}


def public_selector_features(obs: dict) -> dict:
    """Return only public inputs read by the frozen selector and source leaf."""
    rival = obs['farms'][1 - int(obs['player'])]
    pasture_count = sum(
        isinstance(tile, dict) and tile.get('kind') == 'PASTURE'
        for row in rival['tiles'] for tile in row)
    melon = cow = sheep = goose = 0
    for row in rival['tiles']:
        for tile in row:
            if isinstance(tile, dict):
                melon += tile.get('crop') == 'MELON'
                cow += tile.get('animal') == 'COW'
                sheep += tile.get('animal') == 'SHEEP'
                goose += tile.get('animal') == 'GOOSE'
    comparison = 'C<S' if cow < sheep else 'C>S' if cow > sheep else 'C=S'
    unlocked_shops = obs.get('town', {}).get('unlocked_shops') or []
    first_unlocked_shop = unlocked_shops[0] if unlocked_shops else None
    leaf_key = (None if first_unlocked_shop is None else
                first_unlocked_shop + '|' + ('M8+' if melon >= 8 else 'M<8')
                + '|' + comparison + ('|G+' if goose > 0 else '|G0'))
    return {'rival_hands': len(rival['hands']), 'rival_pasture_count': pasture_count,
            'rival_melon_tiles': melon, 'rival_cow_tiles': cow,
            'rival_sheep_tiles': sheep, 'rival_goose_tiles': goose,
            'first_unlocked_shop': first_unlocked_shop, 'leaf_key72': leaf_key}


def market_snapshot(obs: dict) -> dict:
    return deepcopy(obs.get('market', {}))


def cash_snapshot(obs: dict, seat: int) -> dict:
    return {
        'own': obs['farms'][seat].get('money'),
        'rival': obs['farms'][1 - seat].get('money'),
    }


def policy_error_counters(stats: dict) -> dict:
    terms = ('error', 'collision', 'failed', 'refusal', 'procurement', 'unfilled', 'abort')
    return {key: value for key, value in stats.items()
            if isinstance(value, (int, float)) and value != 0
            and any(term in key.lower() for term in terms)}


def transition_run(job: dict, candidate_side: bool) -> dict:
    """Run one policy for turns 0..71 and request its action at observation72."""
    sys.path.insert(0, str(ROOT))
    from diagnostics.stream_replay_io_20260928.cached_input import load_fixture
    from diagnostics.physical_route_rollout_20260928 import native_core
    from diagnostics.physical_route_rollout_20260928.check import Box, state_from_frames

    fixture = job['fixture']
    cached = load_fixture(fixture)
    state = state_from_frames(cached['steps'][0])
    cfg = dict(cached['configuration'])
    cfg['seed'] = None
    env = Box(configuration=Box(**cfg), info={'seed': int(fixture['seed'])}, done=False)
    del cached
    tape = canonical_action_tape(fixture, job['fixture_file_bindings'])
    if candidate_side:
        path, digest, name = job['candidate_path'], job['candidate_sha256'], 'prefix_candidate'
    else:
        path, digest, name = job['reference_path'], job['reference_sha256'], 'prefix_reference'
    module = load_policy(path, digest, name)
    observations = []
    actions = []
    record_hashes = []
    step1_stats = {}
    seen_policy_errors = {}
    seen_bridge_errors = {}
    started = time.perf_counter()
    try:
        for step in range(73):
            obs = policy_observation(state, job['candidate_seat'])
            if int(obs['step']) != step:
                raise AssertionError(f'nonconsecutive state step: expected {step}, got {obs["step"]}')
            action = module.agent(obs, cfg)
            action_copy = deepcopy(action)
            observations.append({
                'step': step,
                'full_observation_sha256': digest_object(obs),
                'own_physical_private_sha256': digest_object(own_physical_private(obs, job['candidate_seat'])),
                'shared_market_sha256': digest_object(market_snapshot(obs)),
                'cash': cash_snapshot(obs, job['candidate_seat']),
                'public_features': (public_selector_features(obs) if step in (1, 72) else None),
            })
            actions.append(action_copy)
            record_hashes.append(digest_object({'step': step, 'observation': obs, 'action': action_copy}))
            if step == 1:
                step1_stats = deepcopy(dict(getattr(module.agent, 'telemetry', {}) or {}))
            telemetry_now = dict(getattr(module.agent, 'telemetry', {}) or {})
            for key, value in policy_error_counters(telemetry_now).items():
                seen_policy_errors[key] = max(value, seen_policy_errors.get(key, 0))
            bridge_now = dict(getattr(module, '_BRIDGE_STATS', {}) or {})
            for key in ('bridge_common_failed', 'bridge_guard_refusals',
                        'bridge_source_guard_failed', 'bridge_errors'):
                value = bridge_now.get(key, 0)
                if value:
                    seen_bridge_errors[key] = max(value, seen_bridge_errors.get(key, 0))
            if step < 72:
                state[job['candidate_seat']].action = deepcopy(action_copy)
                state[1 - job['candidate_seat']].action = deepcopy(tape[step])
                native_core.interpreter(state, env)
                for item in state:
                    item.observation.step = step + 1
        telemetry = deepcopy(dict(getattr(module.agent, 'telemetry', {}) or {}))
        leaf_stats = deepcopy(dict(getattr(module, '_GUARD_LEAF_STATS', {}) or {}))
        guard_stats = deepcopy(dict(getattr(module, '_BRIDGE_STATS', {}) or {}))
        return {
            'observations': observations,
            'actions': actions,
            'record_hashes': record_hashes,
            'step1_telemetry': step1_stats,
            'telemetry': telemetry,
            'leaf_stats': leaf_stats,
            'bridge_stats': guard_stats,
            'policy_error_counters': seen_policy_errors,
            'bridge_error_counters': seen_bridge_errors,
            'wall_seconds': time.perf_counter() - started,
            'status_at_observation72': [getattr(item, 'status', None) for item in state],
        }
    finally:
        del module, state, tape
        gc.collect()


def verify_saved_control_prefix(path: str, digest: str, record_hashes: list) -> list[int]:
    trace = Path(path)
    if sha(trace) != digest:
        raise AssertionError(f'saved a44 control trace hash changed: {trace}')
    mismatches = []
    with gzip.open(trace, 'rt', encoding='utf-8') as stream:
        for expected_step in range(73):
            line = stream.readline()
            if not line:
                mismatches.append(expected_step)
                break
            row = json.loads(line)
            actual_step = int(row['step'])
            if actual_step != expected_step or digest_object(row) != record_hashes[expected_step]:
                mismatches.append(expected_step)
    return mismatches


def compare_run(job: dict) -> dict:
    reference = transition_run(job, candidate_side=False)
    candidate = transition_run(job, candidate_side=True)
    feature = job['frozen_feature_row']['selector_features']
    fixture_id = job['fixture_id']
    seat = int(job['candidate_seat'])
    observations = []
    actions = []
    for ref_row, cand_row in zip(reference['observations'], candidate['observations']):
        step = ref_row['step']
        observations.append({
            'observation_step': step,
            'full_observation_equal': ref_row['full_observation_sha256'] == cand_row['full_observation_sha256'],
            'own_physical_private_equal': ref_row['own_physical_private_sha256'] == cand_row['own_physical_private_sha256'],
            'shared_market_equal': ref_row['shared_market_sha256'] == cand_row['shared_market_sha256'],
            'candidate_cash': cand_row['cash'],
            'reference_cash': ref_row['cash'],
            'cash_delta': {
                key: (cand_row['cash'][key] - ref_row['cash'][key]
                      if isinstance(cand_row['cash'][key], (int, float))
                      and isinstance(ref_row['cash'][key], (int, float)) else None)
                for key in ('own', 'rival')},
        })
        cand_action = candidate['actions'][step]
        ref_action = reference['actions'][step]
        actions.append({'step': step, 'equal': cand_action == ref_action,
                        'candidate': cand_action, 'reference': ref_action})

    candidate_step1 = candidate['step1_telemetry']
    candidate_branch = candidate_step1.get('bridge_selected')
    candidate_requested = candidate_step1.get('bridge_requested')
    candidate_pastures = candidate_step1.get('bridge_rival_pastures')
    leaf = candidate['leaf_stats']
    # The last stored observation is the state visible when the step-72 policy
    # call occurred; public leaf features are recomputed from that actual state.
    candidate_obs72 = candidate['observations'][72]
    runtime_obs1_features = candidate['observations'][1]['public_features']
    runtime_obs72_features = candidate_obs72['public_features']
    runtime_obs1_gate = (
        runtime_obs1_features['rival_hands'] == feature['obs1_rival_hands']
        and runtime_obs1_features['rival_pasture_count'] == feature['obs1_rival_pasture_count'])
    runtime_obs72_gate = (
        runtime_obs72_features['first_unlocked_shop'] == feature['obs72_first_revealed_shop']
        and runtime_obs72_features['rival_melon_tiles'] == feature['obs72_rival_melon_plots']
        and runtime_obs72_features['rival_cow_tiles'] == feature['obs72_rival_cows']
        and runtime_obs72_features['rival_sheep_tiles'] == feature['obs72_rival_sheep']
        and runtime_obs72_features['rival_goose_tiles'] == feature['obs72_rival_geese']
        and runtime_obs72_features['leaf_key72'] == feature['obs72_leaf_key'])
    leaf_key_matches_observation = (leaf.get('guard_leaf_key72')
                                    == runtime_obs72_features['leaf_key72'])
    frozen_obs1 = feature['obs1_rival_hands'], feature['obs1_rival_pasture_count']
    source_obs1 = job['frozen_feature_row']['source_control']['a44_observed_branch']
    donor_case = job['comparison'] == 'candidate_vs_exact_a44'
    if donor_case:
        telemetry_comparable = dict(candidate['telemetry'])
        telemetry_reference = dict(reference['telemetry'])
        telemetry_comparable.pop('bridge_rival_pastures', None)
        telemetry_reference.pop('bridge_rival_pastures', None)
        telemetry_equal = telemetry_comparable == telemetry_reference
        saved_mismatches = verify_saved_control_prefix(
            job['saved_a44_trace_path'], job['saved_a44_trace_sha256'], reference['record_hashes'])
        obs_gate = all(row['full_observation_equal'] for row in observations)
        action_gate = all(row['equal'] for row in actions)
        leaf_gate = (runtime_obs72_features['leaf_key72'] != LEAF_KEY
                     and not leaf.get('guard_leaf_route')
                     and int(leaf.get('guard_leaf_turns', 0)) == 0)
        branch_gate = (candidate_branch == 'shared151' and candidate_requested == 'shared151'
                       and candidate_pastures == 0
                       and candidate_step1.get('bridge_rival_hands') == feature['obs1_rival_hands'])
        opening_gate = all(row['full_observation_equal'] and actions[row['observation_step']]['equal']
                           for row in observations if row['observation_step'] in (0, 1))
        state_gate = True
        market_diff_steps = [row['observation_step'] for row in observations if not row['shared_market_equal']]
        cash_ledger = [row for row in observations if row['cash_delta']['own'] or row['cash_delta']['rival']]
        action_differences = [row for row in actions if not row['equal']]
        saved_control_gate = not saved_mismatches
    else:
        telemetry_equal = None
        saved_mismatches = []
        branch_gate = (candidate_branch == 'source' and candidate_requested == 'source'
                       and candidate_pastures == feature['obs1_rival_pasture_count']
                       and candidate_step1.get('bridge_rival_hands') == feature['obs1_rival_hands'])
        action_gate = all(actions[step]['equal'] for step in (0, 1))
        opening_gate = action_gate and all(
            observations[step]['own_physical_private_equal'] for step in (1, 2))
        state_gate = all(row['own_physical_private_equal']
                         for row in observations if 2 <= row['observation_step'] <= 72)
        obs_gate = state_gate
        market_diff_steps = [row['observation_step'] for row in observations if not row['shared_market_equal']]
        cash_ledger = [row for row in observations
                       if row['cash_delta']['own'] or row['cash_delta']['rival']]
        action_differences = [row for row in actions if not row['equal']]
        leaf_gate = (leaf_key_matches_observation and ((fixture_id == THIRD_ID
                      and runtime_obs72_features['leaf_key72'] == LEAF_KEY
                      and leaf.get('guard_leaf_route') == LEAF_ROUTE
                      and int(leaf.get('guard_leaf_turns', 0)) == 1)
                     or (fixture_id == CHRIS_ID and runtime_obs72_features['leaf_key72'] != LEAF_KEY
                         and not leaf.get('guard_leaf_route')
                         and int(leaf.get('guard_leaf_turns', 0)) == 0)))
        saved_control_gate = True

    errors = {
        'candidate': candidate['policy_error_counters'],
        'reference': reference['policy_error_counters'],
        'candidate_bridge': candidate['bridge_error_counters'],
        'reference_bridge': reference['bridge_error_counters'],
    }
    zero_errors = (not errors['candidate'] and not errors['reference']
                   and all(not value for group in (errors['candidate_bridge'], errors['reference_bridge'])
                           for value in group.values()))
    status_gate = (candidate['status_at_observation72'] == ['ACTIVE', 'ACTIVE']
                   and reference['status_at_observation72'] == ['ACTIVE', 'ACTIVE'])
    if donor_case:
        procurement_gate = opening_gate and action_gate and state_gate
    else:
        procurement_gate = opening_gate and state_gate
    passed = all((obs_gate, action_gate, opening_gate, state_gate, branch_gate,
                  runtime_obs1_gate, runtime_obs72_gate,
                  leaf_gate, saved_control_gate, telemetry_equal is not False, status_gate,
                  zero_errors, procurement_gate))
    return {
        'job_id': job['job_id'], 'fixture_id': fixture_id, 'candidate_seat': seat,
        'comparison': job['comparison'], 'seed': int(job['fixture']['seed']),
        'candidate_sha256': job['candidate_sha256'],
        'reference_sha256': job['reference_sha256'],
        'candidate_requested_branch_at_step1': candidate_requested,
        'candidate_selected_branch_at_step1': candidate_branch,
        'candidate_rival_pasture_count_at_step1': candidate_pastures,
        'runtime_public_features_at_step1': runtime_obs1_features,
        'runtime_public_features_at_step72': runtime_obs72_features,
        'step72_leaf_key_matches_actual_observation': leaf_key_matches_observation,
        'runtime_obs72_features_match_frozen_row': runtime_obs72_gate,
        'frozen_obs1_public_features': frozen_obs1,
        'frozen_a44_observed_branch': source_obs1,
        'candidate_leaf_stats_after_step72': leaf,
        'candidate_status_at_observation72': candidate['status_at_observation72'],
        'reference_status_at_observation72': reference['status_at_observation72'],
        'candidate_telemetry': candidate['telemetry'],
        'reference_telemetry': reference['telemetry'],
        'error_and_guard_ledger': errors,
        'observation_comparisons': observations,
        'action_comparisons': actions,
        'action_difference_steps': [row['step'] for row in action_differences],
        'shared_market_difference_steps': market_diff_steps,
        'cash_difference_ledger': cash_ledger,
        'saved_a44_trace_prefix_mismatch_steps': saved_mismatches,
        'checks': {
            'observation_gate': obs_gate, 'action_gate': action_gate,
            'opening_turn0_turn1_and_procurement_gate': procurement_gate,
            'own_physical_private_observation2_72_gate': state_gate,
            'source_selection_gate': branch_gate, 'step72_leaf_gate': leaf_gate,
            'runtime_public_obs1_feature_binding_gate': runtime_obs1_gate,
            'runtime_public_obs72_feature_binding_gate': runtime_obs72_gate,
            'saved_a44_trace_reproduction_gate': saved_control_gate,
            'telemetry_gate': telemetry_equal is not False,
            'bounded_active_prefix_gate': status_gate,
            'zero_policy_guard_procurement_errors_gate': zero_errors,
        },
        'passed': passed,
        'candidate_prefix_seconds': candidate['wall_seconds'],
        'reference_prefix_seconds': reference['wall_seconds'],
        'frames_observed': 73,
        'native_transitions': 72,
    }


def run_prefix(workers: int) -> None:
    if workers != 1:
        raise ValueError('the frozen prefix plan requires exactly one worker')
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    with exclusive_run(LOCK_PATH):
        _run_prefix_locked()


def _run_prefix_locked() -> None:
    manifest = verify_manifest()
    if manifest['required_workers'] != 1:
        raise ValueError('the frozen prefix plan requires exactly one worker')
    if RESULTS_PATH.exists():
        raise FileExistsError('prefix_v2_results.json already exists; refusing to overwrite a frozen receipt')
    rows = []
    if PROGRESS_PATH.exists():
        rows = [json.loads(line) for line in PROGRESS_PATH.read_text(encoding='utf-8').splitlines() if line.strip()]
    done = {row['job_id'] for row in rows}
    if len(done) != len(rows) or not done.issubset({job['job_id'] for job in manifest['jobs']}):
        raise AssertionError('prefix checkpoint contains duplicate or out-of-pool jobs')
    if any(row.get('manifest_sha256') != sha(MANIFEST_PATH) for row in rows):
        raise AssertionError('prefix checkpoint belongs to a different manifest')
    jobs = [job for job in manifest['jobs'] if job['job_id'] not in done]
    mode = 'a' if PROGRESS_PATH.exists() else 'x'
    with PROGRESS_PATH.open(mode, encoding='utf-8') as stream:
        for start in range(0, len(jobs), 4):
            with ProcessPoolExecutor(max_workers=1, max_tasks_per_child=4) as executor:
                for result in executor.map(compare_run, jobs[start:start + 4]):
                    result['manifest_sha256'] = sha(MANIFEST_PATH)
                    rows.append(result)
                    stream.write(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({'completed': len(rows), 'total': 14,
                                      'job_id': result['job_id'], 'passed': result['passed']},
                                     ensure_ascii=False), flush=True)
    by_id = {row['job_id']: row for row in rows}
    rows = [by_id[job['job_id']] for job in manifest['jobs']]
    donor_rows = [row for row in rows if row['comparison'] == 'candidate_vs_exact_a44']
    third_rows = [row for row in rows if row['fixture_id'] == THIRD_ID]
    chris_rows = [row for row in rows if row['fixture_id'] == CHRIS_ID]
    passed = (len(rows) == 14 and all(row['passed'] for row in rows)
              and len(donor_rows) == 10 and len(third_rows) == 2 and len(chris_rows) == 2
              and all(row['candidate_leaf_stats_after_step72'].get('guard_leaf_route') == LEAF_ROUTE
                      for row in third_rows)
              and all(not row['candidate_leaf_stats_after_step72'].get('guard_leaf_route')
                      for row in chris_rows + donor_rows))
    receipt = {
        'schema': 'pasture-guard-native-prefix-receipt-v1',
        'complete': len(rows) == 14, 'passed': passed,
        'manifest_path': str(MANIFEST_PATH.resolve()), 'manifest_sha256': sha(MANIFEST_PATH),
        'candidate_sha256': manifest['candidate']['sha256'],
        'pool_sha256': manifest['pool']['sha256'],
        'feature_rows_sha256': manifest['feature_rows']['sha256'],
        'engine_sha256': manifest['runtime_binding']['installed_engine_source_sha256'],
        'native_core_sha256': manifest['runtime_binding']['native_core_sha256'],
        'job_count': len(rows), 'donor_a44_jobs': len(donor_rows),
        'affected_32e_jobs': len(third_rows) + len(chris_rows),
        'full_game_outcomes_run': False,
        'study_pilot_authorized_by_prefix': False,
        'jobs': rows,
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    write_new(RESULTS_PATH, receipt)
    print(json.dumps({key: value for key, value in receipt.items() if key != 'jobs'},
                     indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('freeze', 'verify', 'run'))
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    if args.phase == 'freeze':
        freeze()
    elif args.phase == 'verify':
        manifest = verify_manifest()
        print(json.dumps({'verified': True, 'manifest_sha256': sha(MANIFEST_PATH),
                          'job_count': manifest['job_count'], 'simulations_run': 0}, indent=2))
    else:
        run_prefix(args.workers)


if __name__ == '__main__':
    main()
