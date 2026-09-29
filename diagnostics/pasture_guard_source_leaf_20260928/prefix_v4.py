"""Frozen v4 pre-outcome native-prefix proof runner for the pasture study.

`freeze` and `verify` are static only. `run` reuses ten already passing v3
donor controls and runs only four affected exact-a44 prefixes through step 72.
It never runs a complete game.
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
PLAN_PATH = HERE / 'PREFIX_PLAN_V4.md'
MANIFEST_PATH = HERE / 'prefix_manifest_v4.json'
PROGRESS_PATH = HERE / 'prefix_v4_progress.jsonl'
RESULTS_PATH = HERE / 'prefix_v4_results.json'
LOCK_PATH = HERE / 'prefix_v4.lock'
FREEZE_RECEIPT_PATH = HERE / 'prefix_v4_freeze_receipt.json'
BASE_PREFIX_PATH = HERE / 'prefix.py'
BASE_MANIFEST_PATH = HERE / 'prefix_manifest.json'
BASE_PLAN_PATH = HERE / 'PREFIX_PLAN.md'
BASE_PROGRESS_PATH = HERE / 'prefix_progress.jsonl'
PREVIOUS_PREFIX_PATH = HERE / 'prefix_v2.py'
PREVIOUS_MANIFEST_PATH = HERE / 'prefix_manifest_v2.json'
PREVIOUS_PLAN_PATH = HERE / 'PREFIX_PLAN_V2.md'
V3_PREFIX_PATH = HERE / 'prefix_v3.py'
V3_MANIFEST_PATH = HERE / 'prefix_manifest_v3.json'
V3_PLAN_PATH = HERE / 'PREFIX_PLAN_V3.md'
V3_PROGRESS_PATH = HERE / 'prefix_v3_progress.jsonl'
V3_RESULTS_PATH = HERE / 'prefix_v3_results.json'
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
            source_control = feature['source_control']
            if (source_control.get('a44_observed_branch') != 'shared151'
                    or source_control.get('guarded_branch_from_public_features') != 'source'
                    or source_control.get('branch_changes') is not True):
                raise AssertionError(f'affected fixture no longer requires an a44 source-fallback comparison: {fixture_id}/{seat}')
            fixture = fixtures[fixture_id]
            fixture_file_bindings = {
                str(Path(fixture[field]).resolve()): pool['bindings'][str(Path(fixture[field]).resolve())]
                for field in ('source_replay_path', 'source_action_tape_path')}
            jobs.append({
                'job_id': f'source-fallback-{fixture_id}-seat{seat}',
                'fixture_id': fixture_id, 'candidate_seat': seat,
                'comparison': 'candidate_vs_exact_a44_source_fallback',
                'candidate_path': pool['candidate']['path'],
                'candidate_sha256': pool['candidate']['sha256'],
                'reference_path': str(SOURCE_A44.resolve()),
                'reference_sha256': EXPECTED_A44,
                'reference_entrypoint': '_BRIDGE_SOURCE_AGENT',
                'fixture': fixture,
                'fixture_file_bindings': fixture_file_bindings,
                'expected_a44_control': controls.get((fixture_id, seat)),
                'saved_a44_trace_path': feature['provenance']['trace_path'],
                'saved_a44_trace_sha256': feature['provenance']['trace_sha256'],
                'frozen_feature_row': feature,
            })
    if len(jobs) != 14 or len({job['job_id'] for job in jobs}) != 14:
        raise AssertionError('v4 prefix matrix must be exactly fourteen unique comparisons')
    return jobs


def validate_v3_donor_reuse(pool: dict, jobs: list[dict]) -> tuple[dict, list[dict]]:
    """Prove v3's ten donor rows apply unchanged to the v4 donor jobs."""
    old_manifest = read_json(V3_MANIFEST_PATH)
    old_receipt = read_json(V3_RESULTS_PATH)
    for path, digest in old_manifest['file_bindings'].items():
        if sha(path) != digest:
            raise AssertionError(f'v3 frozen input changed before donor-row reuse: {path}')
    if old_manifest['file_bindings'].get(str(V3_PREFIX_PATH.resolve())) != sha(V3_PREFIX_PATH):
        raise AssertionError('v3 runner does not match its frozen v3 input binding')
    if old_receipt.get('manifest_sha256') != sha(V3_MANIFEST_PATH):
        raise AssertionError('v3 result receipt is not bound to the preserved v3 manifest')
    if (not old_receipt.get('complete') or old_receipt.get('job_count') != 14
            or old_receipt.get('candidate_sha256') != pool['candidate']['sha256']
            or old_receipt.get('pool_sha256') != sha(POOL_PATH)
            or old_receipt.get('feature_rows_sha256') != sha(FEATURES_PATH)
            or old_receipt.get('engine_sha256') != old_manifest['runtime_binding']['installed_engine_source_sha256']
            or old_receipt.get('native_core_sha256') != old_manifest['runtime_binding']['native_core_sha256']):
        raise AssertionError('v3 receipt candidate or runtime bindings do not match v4 inputs')
    if old_manifest.get('candidate', {}).get('sha256') != pool['candidate']['sha256']:
        raise AssertionError('v3 and v4 candidates differ')
    if old_manifest.get('source_comparators', {}).get('exact_a44', {}).get('sha256') != EXPECTED_A44:
        raise AssertionError('v3 donor comparator was not exact a44')

    old_donor_jobs = [job for job in old_manifest['jobs']
                      if job['comparison'] == 'candidate_vs_exact_a44']
    new_donor_jobs = [job for job in jobs if job['comparison'] == 'candidate_vs_exact_a44']
    if len(old_donor_jobs) != 10 or old_donor_jobs != new_donor_jobs:
        raise AssertionError('v3 donor job definitions are not identical to the v4 donor controls')
    if digest_object(old_manifest['jobs']) != old_manifest.get('job_matrix_sha256'):
        raise AssertionError('v3 frozen job matrix digest is invalid')
    result_by_id = {row['job_id']: row for row in old_receipt.get('jobs', [])}
    if len(result_by_id) != 14:
        raise AssertionError('v3 receipt does not contain fourteen unique result rows')
    required_checks = (
        'observation_gate', 'action_gate', 'opening_turn0_turn1_and_procurement_gate',
        'own_physical_private_observation2_72_gate', 'source_selection_gate',
        'step72_leaf_gate', 'runtime_public_obs1_feature_binding_gate',
        'runtime_public_obs72_feature_binding_gate', 'saved_a44_trace_reproduction_gate',
        'telemetry_gate', 'bounded_active_prefix_gate',
        'zero_policy_guard_procurement_errors_gate',
    )
    reusable = []
    for job in new_donor_jobs:
        row = result_by_id.get(job['job_id'])
        if (row is None or row.get('comparison') != 'candidate_vs_exact_a44'
                or row.get('candidate_sha256') != pool['candidate']['sha256']
                or row.get('reference_sha256') != EXPECTED_A44
                or row.get('passed') is not True
                or row.get('action_difference_steps') != []
                or row.get('saved_a44_trace_prefix_mismatch_steps') != []
                or any(row.get('checks', {}).get(key) is not True for key in required_checks)
                or any(not item.get('full_observation_equal')
                       for item in row.get('observation_comparisons', []))
                or any(not item.get('equal') for item in row.get('action_comparisons', []))
                or row.get('candidate_status_at_observation72') != ['ACTIVE', 'ACTIVE']
                or row.get('reference_status_at_observation72') != ['ACTIVE', 'ACTIVE']
                or row.get('candidate_leaf_stats_after_step72', {}).get('guard_leaf_route')
                or int(row.get('candidate_leaf_stats_after_step72', {}).get('guard_leaf_turns', 0)) != 0):
            raise AssertionError(f'v3 donor result is not reusable: {job["job_id"]}')
        reusable.append(row)
    if len(reusable) != 10:
        raise AssertionError('v4 must reuse exactly ten passing v3 donor rows')
    row_by_id = {row['job_id']: row for row in reusable}
    binding = {
        'source_runner': {'path': str(V3_PREFIX_PATH.resolve()), 'sha256': sha(V3_PREFIX_PATH)},
        'source_plan': {'path': str(V3_PLAN_PATH.resolve()), 'sha256': sha(V3_PLAN_PATH)},
        'source_manifest': {'path': str(V3_MANIFEST_PATH.resolve()), 'sha256': sha(V3_MANIFEST_PATH)},
        'source_progress': {'path': str(V3_PROGRESS_PATH.resolve()), 'sha256': sha(V3_PROGRESS_PATH)},
        'source_result_receipt': {'path': str(V3_RESULTS_PATH.resolve()), 'sha256': sha(V3_RESULTS_PATH)},
        'source_receipt_manifest_sha256': old_receipt['manifest_sha256'],
        'candidate_sha256': pool['candidate']['sha256'],
        'exact_a44_sha256': EXPECTED_A44,
        'reused_rows': [
            {'job_id': job['job_id'],
             'job_definition_sha256': digest_object(job),
             'result_row_sha256': digest_object(row_by_id[job['job_id']]),
             'comparison': row_by_id[job['job_id']]['comparison'],
             'passed': row_by_id[job['job_id']]['passed']}
            for job in new_donor_jobs],
    }
    return binding, reusable


def freeze() -> None:
    if (MANIFEST_PATH.exists() or RESULTS_PATH.exists() or PROGRESS_PATH.exists()
            or LOCK_PATH.exists() or FREEZE_RECEIPT_PATH.exists()):
        raise FileExistsError('v4 freeze/run outputs already exist; use verify or inspect them')
    pool, features, _ = validate_static()
    jobs = make_jobs(pool, features)
    donor_reuse, _ = validate_v3_donor_reuse(pool, jobs)
    engine_path = verified_engine_source()
    bindings = dict(pool['bindings'])
    direct = [POOL_PATH, FEATURES_PATH, STATIC_PATH, PLAN_PATH, Path(__file__),
              BASE_PREFIX_PATH, BASE_MANIFEST_PATH, BASE_PLAN_PATH, BASE_PROGRESS_PATH,
              PREVIOUS_PREFIX_PATH, PREVIOUS_MANIFEST_PATH, PREVIOUS_PLAN_PATH,
              V3_PREFIX_PATH, V3_MANIFEST_PATH, V3_PLAN_PATH, V3_PROGRESS_PATH, V3_RESULTS_PATH,
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
                raise AssertionError(f'v4 prefix input is absent from frozen file bindings: {path}')
        canonical_action_tape(fixture, bindings)
    selected_fixtures = {job['fixture_id']: job['fixture'] for job in jobs}
    seeds = {fid: int(row['seed']) for fid, row in selected_fixtures.items()}
    if len(seeds) != 7:
        raise AssertionError('v4 manifest must bind the seven frozen fixture seeds')
    reused_controls = [job['expected_a44_control'] for job in jobs
                       if job['comparison'] == 'candidate_vs_exact_a44']
    if len(reused_controls) != 10 or any(row['candidate_sha256'] != EXPECTED_A44 for row in reused_controls):
        raise AssertionError('ten exact-a44 donor controls are not bound')
    manifest = {
        'schema': 'pasture-guard-native-prefix-manifest-v4',
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'exact-a44 source-fallback compatibility proof before outcome games; no complete games',
        'version_lineage': {
            'supersedes_runner_path': str(V3_PREFIX_PATH.resolve()),
            'supersedes_runner_sha256': sha(V3_PREFIX_PATH),
            'supersedes_manifest_path': str(V3_MANIFEST_PATH.resolve()),
            'supersedes_manifest_sha256': sha(V3_MANIFEST_PATH),
            'supersedes_result_path': str(V3_RESULTS_PATH.resolve()),
            'supersedes_result_sha256': sha(V3_RESULTS_PATH),
            'v1_runner_sha256': sha(BASE_PREFIX_PATH),
            'v1_manifest_sha256': sha(BASE_MANIFEST_PATH),
            'v1_progress_sha256': sha(BASE_PROGRESS_PATH),
            'v2_runner_sha256': sha(PREVIOUS_PREFIX_PATH),
            'v2_manifest_sha256': sha(PREVIOUS_MANIFEST_PATH),
            'correction': 'all four source-fallback prefixes compare against the candidate base exact a44; observations must match at steps 0..72, actions at 0..71, with only the THIRD step-72 leaf action permitted to differ; ten identical donor controls are reused from passing v3 result rows',
        },
        'candidate': {'path': pool['candidate']['path'], 'sha256': pool['candidate']['sha256']},
        'pool': {'path': str(POOL_PATH.resolve()), 'sha256': sha(POOL_PATH)},
        'feature_rows': {'path': str(FEATURES_PATH.resolve()), 'sha256': sha(FEATURES_PATH), 'rows': 208},
        'static_receipt': {'path': str(STATIC_PATH.resolve()), 'sha256': sha(STATIC_PATH)},
        'source_comparators': {
            'active_exact_a44': {'path': str(SOURCE_A44.resolve()), 'sha256': EXPECTED_A44},
            'affected_reference_entrypoint': '_BRIDGE_SOURCE_AGENT from the exact-a44 file',
            'preserved_historical_v3_wrong_comparator': {
                'path': str(SOURCE32.resolve()), 'sha256': EXPECTED_32E,
                'active_in_v4_job_matrix': False},
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
            'v3_reused_donor_prefix_rows': donor_reuse,
            'affected_context_a44_outer_dispatcher_trace_provenance_only': [
                {'fixture_id': job['fixture_id'], 'candidate_seat': job['candidate_seat'],
                 'trace_path': job['saved_a44_trace_path'],
                 'trace_sha256': job['saved_a44_trace_sha256'],
                 'usage': 'provenance only; trace records the outer shared151 dispatcher, not the forced source entrypoint'}
                for job in jobs if job['comparison'] == 'candidate_vs_exact_a44_source_fallback'],
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
        'job_count': len(jobs), 'reused_v3_donor_job_count': 10,
        'fresh_affected_job_count': 4, 'observation_limit': 72,
        'required_workers': 1, 'max_jobs_per_worker_process': 4,
        'pass_gates': {
            'donor_reuse': 'reuse only the ten individually passing v3 donor rows with byte-identical job definitions, candidate SHA, exact-a44 SHA, and all recorded row checks true',
            'affected_observations': 'candidate source fallback and exact-a44 _BRIDGE_SOURCE_AGENT full observations equal at every step 0..72',
            'affected_actions': 'candidate and exact a44 actions equal at steps 0..71; ChrisTu also equal at step 72; THIRD may differ only at step 72 and the exact candidate/reference action is recorded',
            'affected_state': 'own physical/private state exact at observations 2..72; shared market and cash are also ledgered',
            'source_selection': 'candidate bridge_requested=source and bridge_selected=source for both seats of THIRD and ChrisTu, bound to observed rival hands and pasture count; reference invokes exact-a44 _BRIDGE_SOURCE_AGENT directly because the original dispatcher records shared151 in these fixtures',
            'telemetry': 'shared source-policy telemetry matches exact a44 at observation 1; candidate-only bridge selector fields equal the bound source decision and have zero errors; the three guard_leaf fields are inactive at observation 1 and match the intended step-72 leaf result',
            'leaf': '113332529 active once at step 72 on both THIRD seats only; inactive on both ChrisTu seats and all five donor fixtures',
            'saved_controls': 'the ten reused donor rows reproduce their bound saved a44 traces; affected-row a44 dispatcher traces are bound as provenance only because they use shared151 rather than the forced source entrypoint',
            'errors': 'zero policy, bridge guard, bridge source, collision, procurement, or engine errors; both policies remain ACTIVE at observation 72',
        },
        'output_paths': {
            'progress': str(PROGRESS_PATH.resolve()),
            'receipt': str(RESULTS_PATH.resolve()),
            'exclusive_run_lock': str(LOCK_PATH.resolve()),
            'static_freeze_receipt': str(FREEZE_RECEIPT_PATH.resolve()),
        },
        'file_bindings': dict(sorted(bindings.items())),
    }
    manifest['control_bindings_sha256'] = digest_object(manifest['control_bindings'])
    write_new(MANIFEST_PATH, manifest)
    freeze_receipt = {
        'schema': 'pasture-guard-native-prefix-static-freeze-receipt-v4',
        'static_freeze_passed': True,
        'manifest_path': str(MANIFEST_PATH.resolve()),
        'manifest_sha256': sha(MANIFEST_PATH),
        'runner_path': str(Path(__file__).resolve()),
        'runner_sha256': sha(Path(__file__)),
        'candidate_sha256': pool['candidate']['sha256'],
        'pool_sha256': sha(POOL_PATH),
        'feature_rows_sha256': sha(FEATURES_PATH),
        'exact_a44_sha256': EXPECTED_A44,
        'engine_sha256': sha(engine_path),
        'native_core_sha256': sha(NATIVE_CORE),
        'job_matrix_sha256': manifest['job_matrix_sha256'],
        'job_count': len(jobs),
        'reused_v3_donor_job_count': 10,
        'fresh_exact_a44_source_fallback_job_ids': [
            job['job_id'] for job in jobs
            if job['comparison'] == 'candidate_vs_exact_a44_source_fallback'],
        'v3_reused_donor_prefix_rows': donor_reuse,
        'input_file_binding_count': len(bindings),
        'future_result_path': str(RESULTS_PATH.resolve()),
        'simulator_jobs_run': 0,
        'full_game_outcomes_run': False,
    }
    write_new(FREEZE_RECEIPT_PATH, freeze_receipt)
    print(json.dumps({
        'frozen': True, 'manifest': str(MANIFEST_PATH.resolve()),
        'manifest_sha256': sha(MANIFEST_PATH), 'job_count': len(jobs),
        'reused_v3_donor_rows': 10, 'fresh_exact_a44_source_fallback_jobs': 4,
        'fixture_seed_bindings': len(seeds), 'engine_sha256': sha(engine_path),
        'runner_sha256': sha(Path(__file__)),
        'freeze_receipt': str(FREEZE_RECEIPT_PATH.resolve()),
        'freeze_receipt_sha256': sha(FREEZE_RECEIPT_PATH), 'simulations_run': 0,
    }, indent=2), flush=True)


def verify_manifest() -> dict:
    manifest = read_json(MANIFEST_PATH)
    for path, digest in manifest['file_bindings'].items():
        if sha(path) != digest:
            raise AssertionError(f'v4 prefix manifest binding changed: {path}')
    pool, features, static = validate_static()
    if manifest['pool']['sha256'] != sha(POOL_PATH):
        raise AssertionError('v4 manifest pool hash is stale')
    if manifest['feature_rows']['sha256'] != sha(FEATURES_PATH):
        raise AssertionError('v4 manifest feature hash is stale')
    if manifest['candidate']['sha256'] != pool['candidate']['sha256']:
        raise AssertionError('v4 manifest candidate hash is stale')
    lineage = manifest['version_lineage']
    if (lineage['supersedes_runner_sha256'] != sha(V3_PREFIX_PATH)
            or lineage['supersedes_manifest_sha256'] != sha(V3_MANIFEST_PATH)
            or lineage['supersedes_result_sha256'] != sha(V3_RESULTS_PATH)
            or lineage['v1_runner_sha256'] != sha(BASE_PREFIX_PATH)
            or lineage['v1_manifest_sha256'] != sha(BASE_MANIFEST_PATH)
            or lineage['v1_progress_sha256'] != sha(BASE_PROGRESS_PATH)
            or lineage['v2_runner_sha256'] != sha(PREVIOUS_PREFIX_PATH)
            or lineage['v2_manifest_sha256'] != sha(PREVIOUS_MANIFEST_PATH)):
        raise AssertionError('v4 lineage no longer matches the preserved v1-v3 artifacts')
    if manifest['static_receipt']['sha256'] != sha(STATIC_PATH) or not static['passed']:
        raise AssertionError('v4 static receipt is stale or failed')
    jobs = make_jobs(pool, features)
    if (jobs != manifest['jobs'] or len(jobs) != manifest['job_count'] or len(jobs) != 14
            or digest_object(jobs) != manifest['job_matrix_sha256']):
        raise AssertionError('v4 job matrix changed since freeze')
    if any(job['reference_sha256'] != EXPECTED_A44 for job in jobs):
        raise AssertionError('v4 contains a non-a44 active prefix comparator')
    if digest_object(manifest['control_bindings']) != manifest['control_bindings_sha256']:
        raise AssertionError('v4 control-binding receipt hash is inconsistent')
    if manifest['control_bindings']['reused_exact_a44_control_rows'] != pool['reused_exact_a44_controls']:
        raise AssertionError('v4 reused-a44 control rows differ from the frozen pool')
    if manifest['control_bindings']['fresh_exact_a44_christu_controls_staged'] != pool['fresh_exact_a44_control_jobs']:
        raise AssertionError('v4 fresh exact-a44 ChrisTu jobs differ from the frozen pool')
    donor_reuse, _ = validate_v3_donor_reuse(pool, jobs)
    if manifest['control_bindings']['v3_reused_donor_prefix_rows'] != donor_reuse:
        raise AssertionError('v4 v3-donor reuse binding changed')
    fixture_by_id = {job['fixture_id']: job['fixture'] for job in jobs}
    expected_fixture_bindings = [
        {'fixture_id': fid, 'seed': int(fixture_by_id[fid]['seed']),
         'source_replay_path': fixture_by_id[fid]['source_replay_path'],
         'source_replay_sha256': fixture_by_id[fid]['source_replay_sha256'],
         'action_tape_path': fixture_by_id[fid]['source_action_tape_path'],
         'source_opponent_action_sha256': fixture_by_id[fid]['source_opponent_action_sha256']}
        for fid in sorted(fixture_by_id)]
    if expected_fixture_bindings != manifest['fixtures_and_seeds']:
        raise AssertionError('v4 fixture, seed, replay, or action-tape binding changed')
    engine_path = verified_engine_source()
    if str(engine_path) != manifest['runtime_binding']['installed_engine_source_path']:
        raise AssertionError('installed Kaggriculture engine path changed')
    for job in jobs:
        canonical_action_tape(job['fixture'], manifest['file_bindings'])
    if manifest['output_paths']['static_freeze_receipt'] != str(FREEZE_RECEIPT_PATH.resolve()):
        raise AssertionError('v4 static freeze receipt output path changed')
    freeze_receipt = read_json(FREEZE_RECEIPT_PATH)
    if (freeze_receipt.get('schema') != 'pasture-guard-native-prefix-static-freeze-receipt-v4'
            or freeze_receipt.get('static_freeze_passed') is not True
            or freeze_receipt.get('manifest_sha256') != sha(MANIFEST_PATH)
            or freeze_receipt.get('runner_sha256') != sha(Path(__file__))
            or freeze_receipt.get('candidate_sha256') != pool['candidate']['sha256']
            or freeze_receipt.get('pool_sha256') != sha(POOL_PATH)
            or freeze_receipt.get('feature_rows_sha256') != sha(FEATURES_PATH)
            or freeze_receipt.get('exact_a44_sha256') != EXPECTED_A44
            or freeze_receipt.get('engine_sha256') != manifest['runtime_binding']['installed_engine_source_sha256']
            or freeze_receipt.get('native_core_sha256') != manifest['runtime_binding']['native_core_sha256']
            or freeze_receipt.get('job_matrix_sha256') != manifest['job_matrix_sha256']
            or freeze_receipt.get('v3_reused_donor_prefix_rows')
                != manifest['control_bindings']['v3_reused_donor_prefix_rows']
            or freeze_receipt.get('input_file_binding_count') != len(manifest['file_bindings'])
            or freeze_receipt.get('job_count') != 14
            or freeze_receipt.get('reused_v3_donor_job_count') != 10
            or freeze_receipt.get('simulator_jobs_run') != 0
            or freeze_receipt.get('full_game_outcomes_run') is not False
            or freeze_receipt.get('fresh_exact_a44_source_fallback_job_ids') != [
                job['job_id'] for job in jobs
                if job['comparison'] == 'candidate_vs_exact_a44_source_fallback']):
        raise AssertionError('v4 static freeze receipt is missing, stale, or reports simulation activity')
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
    if candidate_side or job['comparison'] == 'candidate_vs_exact_a44':
        policy_fn = module.agent
    else:
        if job.get('reference_entrypoint') != '_BRIDGE_SOURCE_AGENT':
            raise AssertionError('affected exact-a44 prefix must pin the source fallback entrypoint')
        policy_fn = getattr(module, job['reference_entrypoint'])
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
            action = policy_fn(obs, cfg)
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
                step1_stats = deepcopy(dict(getattr(policy_fn, 'telemetry', {}) or {}))
            telemetry_now = dict(getattr(policy_fn, 'telemetry', {}) or {})
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
        telemetry = deepcopy(dict(getattr(policy_fn, 'telemetry', {}) or {}))
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
    # Step 72 is observed before its action is applied; this is the leaf's
    # source state, so observations must remain identical to exact a44.
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
    affected_case = job['comparison'] == 'candidate_vs_exact_a44_source_fallback'
    if not (donor_case or affected_case):
        raise AssertionError(f'unrecognized v4 comparator: {job["comparison"]}')
    entrypoint_gate = (not affected_case
                       or job.get('reference_entrypoint') == '_BRIDGE_SOURCE_AGENT')
    saved_mismatches = (verify_saved_control_prefix(
        job['saved_a44_trace_path'], job['saved_a44_trace_sha256'], reference['record_hashes'])
        if donor_case else None)
    action_differences = [row for row in actions if not row['equal']]
    difference_steps = [row['step'] for row in action_differences]
    obs_gate = all(row['full_observation_equal'] for row in observations)
    state_gate = all(row['own_physical_private_equal']
                     for row in observations if 2 <= row['observation_step'] <= 72)
    branch_gate = (candidate_branch == ('shared151' if donor_case else 'source')
                   and candidate_requested == ('shared151' if donor_case else 'source')
                   and candidate_pastures == (0 if donor_case else feature['obs1_rival_pasture_count'])
                   and candidate_step1.get('bridge_rival_hands') == feature['obs1_rival_hands'])
    opening_gate = all(
        observations[step]['full_observation_equal'] and actions[step]['equal']
        for step in (0, 1))
    if donor_case:
        telemetry_comparable = dict(candidate['telemetry'])
        telemetry_reference = dict(reference['telemetry'])
        telemetry_comparable.pop('bridge_rival_pastures', None)
        telemetry_reference.pop('bridge_rival_pastures', None)
        telemetry_equal = telemetry_comparable == telemetry_reference
        action_gate = all(row['equal'] for row in actions)
        leaf_gate = (runtime_obs72_features['leaf_key72'] != LEAF_KEY
                     and not leaf.get('guard_leaf_route')
                     and int(leaf.get('guard_leaf_turns', 0)) == 0)
        saved_control_gate = not saved_mismatches
        telemetry_detail_gate = telemetry_equal
    else:
        telemetry_equal = None
        core_step1_candidate = {key: value for key, value in candidate_step1.items()
                                if key not in {'bridge_rival_pastures', 'guard_leaf_key72',
                                               'guard_leaf_route', 'guard_leaf_turns'}}
        core_step1_reference = {key: value for key, value in reference['step1_telemetry'].items()
                                if key not in {'bridge_rival_pastures', 'guard_leaf_key72',
                                               'guard_leaf_route', 'guard_leaf_turns'}}
        candidate_step1_extras = set(candidate_step1) - set(reference['step1_telemetry'])
        expected_step1_extras = {
            'bridge_selected', 'bridge_requested', 'bridge_rival_hands',
            'bridge_common_failed', 'bridge_guard_refusals',
            'bridge_source_guard_failed', 'bridge_errors', 'bridge_rival_pastures',
            'guard_leaf_key72', 'guard_leaf_route', 'guard_leaf_turns'}
        shared_step1_telemetry_equal = (core_step1_candidate == core_step1_reference
                                        and candidate_step1_extras == expected_step1_extras)
        step1_leaf_inactive = (
            candidate_step1.get('guard_leaf_key72') == ''
            and candidate_step1.get('guard_leaf_route') == ''
            and int(candidate_step1.get('guard_leaf_turns', 0)) == 0)
        bridge_selector_telemetry_gate = (
            candidate_step1.get('bridge_selected') == 'source'
            and candidate_step1.get('bridge_requested') == 'source'
            and candidate_step1.get('bridge_rival_hands') == feature['obs1_rival_hands']
            and candidate_step1.get('bridge_rival_pastures') == feature['obs1_rival_pasture_count']
            and all(candidate_step1.get(key) == 0 for key in (
                'bridge_common_failed', 'bridge_guard_refusals',
                'bridge_source_guard_failed', 'bridge_errors')))
        leaf_gate = (leaf_key_matches_observation and ((fixture_id == THIRD_ID
                      and runtime_obs72_features['leaf_key72'] == LEAF_KEY
                      and leaf.get('guard_leaf_route') == LEAF_ROUTE
                      and int(leaf.get('guard_leaf_turns', 0)) == 1)
                     or (fixture_id == CHRIS_ID and runtime_obs72_features['leaf_key72'] != LEAF_KEY
                         and not leaf.get('guard_leaf_route')
                         and int(leaf.get('guard_leaf_turns', 0)) == 0)))
        if fixture_id == THIRD_ID:
            action_allowance_gate = set(difference_steps).issubset({72})
            step72_action_record = {
                'allowed_difference': True,
                'difference_present': not actions[72]['equal'],
                'candidate_action': actions[72]['candidate'],
                'reference_action': actions[72]['reference'],
            }
        else:
            action_allowance_gate = difference_steps == []
            step72_action_record = {
                'allowed_difference': False,
                'difference_present': not actions[72]['equal'],
                'candidate_action': actions[72]['candidate'],
                'reference_action': actions[72]['reference'],
            }
        actions_equal_through71 = all(actions[step]['equal'] for step in range(72))
        action_gate = actions_equal_through71 and action_allowance_gate
        saved_control_gate = not saved_mismatches
        telemetry_detail_gate = (shared_step1_telemetry_equal and step1_leaf_inactive
                                 and bridge_selector_telemetry_gate)
        telemetry_difference_ledger = {
            'step1_candidate_only_keys': sorted(candidate_step1_extras),
            'expected_step1_candidate_only_keys': sorted(expected_step1_extras),
            'step1_shared_base_telemetry_equal': shared_step1_telemetry_equal,
            'step1_bridge_selector_telemetry_gate': bridge_selector_telemetry_gate,
            'step1_leaf_inactive': step1_leaf_inactive,
            'final_candidate_telemetry': candidate['telemetry'],
            'final_reference_telemetry': reference['telemetry'],
            'leaf_stats_at_step72': leaf,
        }
    market_diff_steps = [row['observation_step'] for row in observations if not row['shared_market_equal']]
    cash_ledger = [row for row in observations if row['cash_delta']['own'] or row['cash_delta']['rival']]

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
    procurement_gate = opening_gate and action_gate and state_gate
    passed = all((obs_gate, action_gate, opening_gate, state_gate, branch_gate,
                  runtime_obs1_gate, runtime_obs72_gate,
                  leaf_gate, saved_control_gate, telemetry_equal is not False, status_gate,
                  zero_errors, procurement_gate, telemetry_detail_gate, entrypoint_gate))
    result = {
        'job_id': job['job_id'], 'fixture_id': fixture_id, 'candidate_seat': seat,
        'comparison': job['comparison'], 'seed': int(job['fixture']['seed']),
        'candidate_sha256': job['candidate_sha256'],
        'reference_sha256': job['reference_sha256'],
        'reference_entrypoint': job.get('reference_entrypoint', 'agent'),
        'reference_original_a44_dispatch_branch': source_obs1,
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
        'action_difference_steps': difference_steps,
        'third_step72_leaf_action': (step72_action_record if affected_case and fixture_id == THIRD_ID else None),
        'shared_market_difference_steps': market_diff_steps,
        'cash_difference_ledger': cash_ledger,
        'saved_a44_trace_prefix_mismatch_steps': saved_mismatches,
        'checks': {
            'full_exact_a44_observation_equality_steps0_72_gate': obs_gate,
            'action_gate': action_gate,
            'action_equality_steps0_71_gate': (all(actions[step]['equal'] for step in range(72))
                                               if affected_case else action_gate),
            'step72_action_allowance_gate': (action_allowance_gate if affected_case else True),
            'opening_turn0_turn1_and_procurement_gate': procurement_gate,
            'own_physical_private_observation2_72_gate': state_gate,
            'source_selection_gate': branch_gate, 'step72_leaf_gate': leaf_gate,
            'runtime_public_obs1_feature_binding_gate': runtime_obs1_gate,
            'runtime_public_obs72_feature_binding_gate': runtime_obs72_gate,
            'saved_a44_trace_reproduction_gate': (saved_control_gate if donor_case else None),
            'exact_a44_source_entrypoint_gate': (
                entrypoint_gate),
            'telemetry_gate': telemetry_equal is not False,
            'intended_bridge_and_leaf_telemetry_only_gate': telemetry_detail_gate,
            'bounded_active_prefix_gate': status_gate,
            'zero_policy_guard_procurement_errors_gate': zero_errors,
        },
        'passed': passed,
        'candidate_prefix_seconds': candidate['wall_seconds'],
        'reference_prefix_seconds': reference['wall_seconds'],
        'frames_observed': 73,
        'native_transitions': 72,
    }
    if affected_case:
        result['telemetry_difference_ledger'] = telemetry_difference_ledger
    return result


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
        raise ValueError('the frozen v4 prefix plan requires exactly one worker')
    if RESULTS_PATH.exists():
        raise FileExistsError('prefix_v4_results.json already exists; refusing to overwrite the frozen receipt')
    rows = []
    if PROGRESS_PATH.exists():
        rows = [json.loads(line) for line in PROGRESS_PATH.read_text(encoding='utf-8').splitlines() if line.strip()]
    done = {row['job_id'] for row in rows}
    fresh_jobs = [job for job in manifest['jobs']
                  if job['comparison'] == 'candidate_vs_exact_a44_source_fallback']
    fresh_job_ids = {job['job_id'] for job in fresh_jobs}
    if len(done) != len(rows) or not done.issubset(fresh_job_ids):
        raise AssertionError('v4 checkpoint contains duplicate or non-affected jobs')
    if any(row.get('manifest_sha256') != sha(MANIFEST_PATH) for row in rows):
        raise AssertionError('v4 checkpoint belongs to a different manifest')
    jobs = [job for job in fresh_jobs if job['job_id'] not in done]
    mode = 'a' if PROGRESS_PATH.exists() else 'x'
    with PROGRESS_PATH.open(mode, encoding='utf-8') as stream:
        if jobs:
            with ProcessPoolExecutor(max_workers=1, max_tasks_per_child=4) as executor:
                for job in jobs:
                    # Submit one fresh prefix only. If it fails, no later job
                    # is queued or run without a durable result row.
                    result = executor.submit(compare_run, job).result()
                    result['manifest_sha256'] = sha(MANIFEST_PATH)
                    rows.append(result)
                    stream.write(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({'fresh_completed': len(rows), 'fresh_total': 4,
                                      'job_id': result['job_id'], 'passed': result['passed']},
                                     ensure_ascii=False), flush=True)
    by_id = {row['job_id']: row for row in rows}
    if set(by_id) != fresh_job_ids:
        raise AssertionError('v4 fresh affected prefix set is incomplete')
    _, reused_donor_rows = validate_v3_donor_reuse(
        read_json(POOL_PATH), manifest['jobs'])
    by_id.update({row['job_id']: row for row in reused_donor_rows})
    rows = [by_id[job['job_id']] for job in manifest['jobs']]
    donor_rows = [row for row in rows if row['comparison'] == 'candidate_vs_exact_a44']
    third_rows = [row for row in rows if row['fixture_id'] == THIRD_ID]
    chris_rows = [row for row in rows if row['fixture_id'] == CHRIS_ID]
    third_action_gate = all(
        set(row.get('action_difference_steps', [])).issubset({72})
        and row.get('checks', {}).get('action_equality_steps0_71_gate') is True
        for row in third_rows)
    chris_action_gate = all(
        row.get('action_difference_steps', []) == []
        and row.get('checks', {}).get('action_equality_steps0_71_gate') is True
        and row.get('action_comparisons', [])[72].get('equal') is True
        for row in chris_rows)
    passed = (len(rows) == 14 and all(row['passed'] for row in rows)
              and len(donor_rows) == 10 and len(third_rows) == 2 and len(chris_rows) == 2
              and third_action_gate and chris_action_gate
              and all(row.get('checks', {}).get('full_exact_a44_observation_equality_steps0_72_gate') is True
                      for row in third_rows + chris_rows)
              and all(row['candidate_leaf_stats_after_step72'].get('guard_leaf_route') == LEAF_ROUTE
                      for row in third_rows)
              and all(not row['candidate_leaf_stats_after_step72'].get('guard_leaf_route')
                      for row in chris_rows + donor_rows))
    receipt = {
        'schema': 'pasture-guard-native-prefix-receipt-v4',
        'complete': len(rows) == 14, 'passed': passed,
        'manifest_path': str(MANIFEST_PATH.resolve()), 'manifest_sha256': sha(MANIFEST_PATH),
        'candidate_sha256': manifest['candidate']['sha256'],
        'pool_sha256': manifest['pool']['sha256'],
        'feature_rows_sha256': manifest['feature_rows']['sha256'],
        'engine_sha256': manifest['runtime_binding']['installed_engine_source_sha256'],
        'native_core_sha256': manifest['runtime_binding']['native_core_sha256'],
        'job_count': len(rows), 'reused_v3_donor_jobs': len(donor_rows),
        'fresh_exact_a44_source_fallback_jobs': len(third_rows) + len(chris_rows),
        'v3_donor_reuse_binding': manifest['control_bindings']['v3_reused_donor_prefix_rows'],
        'third_step72_difference_gate': third_action_gate,
        'christu_all_actions_equal_gate': chris_action_gate,
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
