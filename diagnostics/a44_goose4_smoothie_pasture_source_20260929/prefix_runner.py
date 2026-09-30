"""Static freeze and four-job, 72-transition 6d source-branch proof runner.

`freeze` and `verify` are read-only with respect to simulator state. `run`
executes exactly four bounded prefixes with one worker and never completes a
full game.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
import argparse
import gc
import gzip
import hashlib
import importlib.util
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SIXD_DIR = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
PASTURE_DIR = ROOT / 'diagnostics/pasture_guard_source_leaf_20260928'
SOURCE = SIXD_DIR / 'candidate.py'
CANDIDATE = HERE / 'candidate.py'
LAYER = HERE / 'layer.py'
BUILDER = HERE / 'build_preflight.py'
PLAN = HERE / 'PLAN.md'
PREFIX_PLAN = HERE / 'PREFIX_PLAN.md'
RUNNER = HERE / 'prefix_runner.py'
STATIC_PATH = HERE / 'static_preflight.json'
PAIR_ROWS = SIXD_DIR / 'pair_rows.json'
SIXD_FEATURES = SIXD_DIR / 'feature_rows.json'
PARENT_PANEL = SIXD_DIR / 'parent_panel.json'
PASTURE_FEATURES = PASTURE_DIR / 'feature_rows.json'
SIXD_MANIFEST = SIXD_DIR / 'frozen_manifest.json'
SIXD_PREFLIGHT = SIXD_DIR / 'preflight.json'
PASTURE_POOL = PASTURE_DIR / 'pool.json'
A44_SOURCE = ROOT / 'diagnostics/upload_adaptive_donor_20260928_a44c8c2c/main.py'
CACHE_HELPER = ROOT / 'diagnostics/stream_replay_io_20260928/cached_input.py'
INITIAL_CACHE = ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json'
NATIVE_CORE = ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py'
NATIVE_CHECK = ROOT / 'diagnostics/physical_route_rollout_20260928/check.py'
RUN_LOCK_HELPER = ROOT / 'diagnostics/local_target_20260928/run_lock.py'
MANIFEST_PATH = HERE / 'prefix_manifest.json'
FREEZE_RECEIPT_PATH = HERE / 'prefix_freeze_receipt.json'
PROGRESS_PATH = HERE / 'prefix_progress.jsonl'
RESULTS_PATH = HERE / 'prefix_results.json'
LOCK_PATH = HERE / 'prefix.lock'

SOURCE_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
A44_SHA = 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
THIRD_ID = 'live-114274897'
CHRIS_ID = 'public-win-114193811'
LEAF_KEY = 'BRUNCH_SPOT|M8+|C>S|G+'
LEAF_ROUTE = 113332529
OLD_SELECTOR = (
    b"        branch = 'shared151' if hands>=5 else "
    b"('shared150' if _BRIDGE_VARIANT=='five_or_zero' and hands==0 else 'source')"
)
FORCED_SOURCE_SELECTOR = b"        branch = 'source'"
EXPECTED_JOB_IDS = {
    f'{fixture_id}-seat{seat}'
    for fixture_id in (THIRD_ID, CHRIS_ID) for seat in (0, 1)
}


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path | str) -> str:
    return sha_bytes(Path(path).read_bytes())


def digest_object(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path | str):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_new(path: Path, payload) -> None:
    raw = (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8')
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


def forced_source_bytes(source: bytes | None = None) -> bytes:
    raw = SOURCE.read_bytes() if source is None else source
    if sha_bytes(raw) != SOURCE_SHA or raw.count(OLD_SELECTOR) != 1:
        raise AssertionError('forced-source reference is not based on exact 6d selector bytes')
    offset = raw.index(OLD_SELECTOR)
    forced = raw[:offset] + FORCED_SOURCE_SELECTOR + raw[offset+len(OLD_SELECTOR):]
    restored = forced[:offset] + OLD_SELECTOR + forced[offset+len(FORCED_SOURCE_SELECTOR):]
    if restored != raw:
        raise AssertionError('forced-source comparator edit cannot be reversed exactly')
    return forced


def canonical_action_tape(fixture: dict, bindings: dict[str, str]) -> list:
    path = Path(fixture['source_action_tape_path']).resolve()
    expected_file = bindings.get(str(path))
    if not expected_file or sha(path) != expected_file:
        raise AssertionError(f'action tape is not bound to the frozen manifest: {path}')
    tape = json.loads(gzip.decompress(path.read_bytes()))['actions']
    payload_hashes = [sha_bytes(json.dumps(tape, sort_keys=sort_keys,
                               separators=(',', ':')).encode('utf-8'))
                      for sort_keys in (False, True)]
    if len(tape) != 719 or fixture['source_opponent_action_sha256'] not in payload_hashes:
        raise AssertionError(f'action tape payload does not match fixture {fixture["fixture_id"]}')
    return tape


def current_static() -> dict:
    spec = importlib.util.spec_from_file_location('_pasture_6d_build_preflight', BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError('cannot load the static derivative builder')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.verify()
    return read_json(STATIC_PATH)


def make_jobs(static: dict) -> list[dict]:
    panel = read_json(PARENT_PANEL)
    fixtures = {row['fixture_id']: row for row in panel['fixtures']}
    census_by_key = {(row['fixture_id'], int(row['seat'])): row
                     for row in static['census']['rows']}
    jobs = []
    for fixture_id in (THIRD_ID, CHRIS_ID):
        if fixture_id not in fixtures:
            raise AssertionError(f'planned fixture is missing from exact 6d panel: {fixture_id}')
        for seat in (0, 1):
            row = census_by_key[(fixture_id, seat)]
            if (row['old_branch'] != 'shared151' or row['guarded_branch'] != 'source'
                    or int(row['rival_hands_step1']) < 5
                    or int(row['rival_pasture_count_step1']) != 1):
                raise AssertionError(f'planned source prefix no longer matches trigger row {fixture_id}/{seat}')
            jobs.append({
                'job_id': f'{fixture_id}-seat{seat}',
                'fixture_id': fixture_id,
                'candidate_seat': seat,
                'comparison': 'candidate_vs_forced_source_6d',
                'seed': int(fixtures[fixture_id]['seed']),
                'candidate_path': str(CANDIDATE.resolve()),
                'candidate_sha256': sha(CANDIDATE),
                'reference_path': str(SOURCE.resolve()),
                'reference_sha256': SOURCE_SHA,
                'reference_mode': 'exact_6d_bytes_with_one_in_memory_step1_forced_source_expression',
                'reference_effective_source_sha256': sha_bytes(forced_source_bytes()),
                'reference_selector_replacement': {
                    'old': OLD_SELECTOR.decode('ascii'),
                    'new': FORCED_SOURCE_SELECTOR.decode('ascii'),
                    'source_file_written': False,
                },
                'fixture': deepcopy(fixtures[fixture_id]),
                'expected_step1_public': {
                    'rival_hands': int(row['rival_hands_step1']),
                    'rival_pastures': int(row['rival_pasture_count_step1']),
                    'requested_branch': 'source',
                    'selected_branch': 'source',
                },
                'parent_step72_key_provenance_only': row['parent_branch_step72_key_provenance_only'],
                'runtime_step72_key_requirement': (
                    LEAF_KEY if fixture_id == THIRD_ID else 'must_not_equal:' + LEAF_KEY),
                'source_trace_provenance': {
                    'path': row['trace_path'], 'sha256': row['trace_sha256'],
                    'usage': 'hash-bound context provenance; never a source-branch observation or action comparator',
                },
                'fixture_file_bindings': {
                    'source_replay_path': row['source_replay_path'],
                    'source_replay_sha256': row['source_replay_sha256'],
                    'source_action_tape_path': row['action_tape_path'],
                    'source_opponent_action_sha256': row['source_opponent_action_sha256'],
                },
            })
    if {job['job_id'] for job in jobs} != EXPECTED_JOB_IDS:
        raise AssertionError('prefix matrix must contain exactly the four planned fixture-seat jobs')
    return jobs


def collect_bindings(jobs: list[dict], engine_path: Path) -> dict[str, str]:
    direct = [SOURCE, CANDIDATE, LAYER, BUILDER, PLAN, PREFIX_PLAN, RUNNER, STATIC_PATH,
              PAIR_ROWS, SIXD_FEATURES, PARENT_PANEL, PASTURE_FEATURES,
              SIXD_MANIFEST, SIXD_PREFLIGHT, PASTURE_POOL, A44_SOURCE,
              CACHE_HELPER, INITIAL_CACHE, NATIVE_CORE, NATIVE_CHECK,
              RUN_LOCK_HELPER, engine_path]
    paths = {str(path.resolve()) for path in direct}
    for job in jobs:
        paths.add(str(Path(job['source_trace_provenance']['path']).resolve()))
        paths.add(str(Path(job['fixture_file_bindings']['source_replay_path']).resolve()))
        paths.add(str(Path(job['fixture_file_bindings']['source_action_tape_path']).resolve()))
    bindings = {}
    for raw in sorted(paths):
        path = Path(raw)
        if not path.is_file():
            raise FileNotFoundError(f'prefix input is missing: {path}')
        bindings[str(path.resolve())] = sha(path)
    return bindings


def verify_fixtures_and_traces(jobs: list[dict], bindings: dict[str, str]) -> None:
    if sha(A44_SOURCE) != A44_SHA:
        raise AssertionError('local exact a44 lineage source hash changed')
    for job in jobs:
        fixture = job['fixture']
        replay = Path(fixture['source_replay_path']).resolve()
        tape = Path(fixture['source_action_tape_path']).resolve()
        trace = Path(job['source_trace_provenance']['path']).resolve()
        if sha(replay) != bindings[str(replay)]:
            raise AssertionError(f'source replay bytes are not bound: {replay}')
        try:
            replay_payload_sha = sha_bytes(gzip.decompress(replay.read_bytes()))
        except OSError as exc:
            raise AssertionError(f'source replay is not a valid gzip input: {replay}') from exc
        if replay_payload_sha != fixture['source_replay_sha256']:
            raise AssertionError(f'source replay payload hash mismatch: {replay}')
        if sha(tape) != bindings[str(tape)]:
            raise AssertionError(f'action tape file hash is not bound: {tape}')
        if sha(trace) != job['source_trace_provenance']['sha256']:
            raise AssertionError(f'saved source trace hash mismatch: {trace}')
        canonical_action_tape(fixture, bindings)


def freeze() -> None:
    if any(path.exists() for path in (MANIFEST_PATH, FREEZE_RECEIPT_PATH,
                                       PROGRESS_PATH, RESULTS_PATH, LOCK_PATH)):
        raise FileExistsError('prefix freeze or run artifacts already exist; refusing overwrite')
    static = current_static()
    engine_path = verified_engine_source()
    if sha(SOURCE) != SOURCE_SHA or sha(CANDIDATE) != static['candidate_sha256']:
        raise AssertionError('exact parent or derived candidate hash changed')
    jobs = make_jobs(static)
    bindings = collect_bindings(jobs, engine_path)
    verify_fixtures_and_traces(jobs, bindings)
    manifest = {
        'schema': 'a44-goose4-smoothie-pasture-source-prefix-manifest-v1',
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'static_only': True,
        'simulator_jobs_run_at_freeze': 0,
        'native_transitions_at_freeze': 0,
        'full_game_outcomes_run': False,
        'parent_candidate': {'path': str(SOURCE.resolve()), 'sha256': SOURCE_SHA},
        'candidate': {'path': str(CANDIDATE.resolve()), 'sha256': static['candidate_sha256']},
        'candidate_build': {
            'builder_path': str(BUILDER.resolve()), 'builder_sha256': sha(BUILDER),
            'layer_path': str(LAYER.resolve()), 'layer_sha256': sha(LAYER),
            'static_preflight_path': str(STATIC_PATH.resolve()), 'static_preflight_sha256': sha(STATIC_PATH),
            'selector_patch_count': 1,
            'parent_bytes_reconstructed_exactly_after_reversing_patch_and_layer_removal': True,
        },
        'runner': {'path': str(RUNNER.resolve()), 'sha256': sha(RUNNER)},
        'reference': {
            'path': str(SOURCE.resolve()), 'source_sha256': SOURCE_SHA,
            'mode': 'same exact 6d Goose4+Smoothie source bytes, forced to source at observation 1 in memory',
            'selector_replacement': {
                'old': OLD_SELECTOR.decode('ascii'),
                'new': FORCED_SOURCE_SELECTOR.decode('ascii'),
                'effective_source_sha256': sha_bytes(forced_source_bytes()),
                'source_file_written': False,
            },
        },
        'plans': {
            'study_plan': {'path': str(PLAN.resolve()), 'sha256': sha(PLAN)},
            'prefix_plan': {'path': str(PREFIX_PLAN.resolve()), 'sha256': sha(PREFIX_PLAN)},
        },
        'inputs': {
            'static_preflight': static,
            'pair_rows': {'path': str(PAIR_ROWS.resolve()), 'sha256': sha(PAIR_ROWS), 'rows': 208},
            '6d_features': {'path': str(SIXD_FEATURES.resolve()), 'sha256': sha(SIXD_FEATURES), 'rows': 208},
            'pasture_public_features': {'path': str(PASTURE_FEATURES.resolve()), 'sha256': sha(PASTURE_FEATURES), 'rows': 208},
            'parent_panel': {'path': str(PARENT_PANEL.resolve()), 'sha256': sha(PARENT_PANEL), 'fixtures': 104},
            '6d_manifest': {'path': str(SIXD_MANIFEST.resolve()), 'sha256': sha(SIXD_MANIFEST)},
            '6d_preflight': {'path': str(SIXD_PREFLIGHT.resolve()), 'sha256': sha(SIXD_PREFLIGHT)},
            'pasture_pool': {'path': str(PASTURE_POOL.resolve()), 'sha256': sha(PASTURE_POOL)},
        },
        'runtime_binding': {
            'cache_reader_path': str(CACHE_HELPER.resolve()), 'cache_reader_sha256': sha(CACHE_HELPER),
            'initial_state_cache_path': str(INITIAL_CACHE.resolve()), 'initial_state_cache_sha256': sha(INITIAL_CACHE),
            'native_core_path': str(NATIVE_CORE.resolve()), 'native_core_sha256': sha(NATIVE_CORE),
            'state_helper_path': str(NATIVE_CHECK.resolve()), 'state_helper_sha256': sha(NATIVE_CHECK),
            'run_lock_helper_path': str(RUN_LOCK_HELPER.resolve()), 'run_lock_helper_sha256': sha(RUN_LOCK_HELPER),
            'installed_engine_source_path': str(engine_path), 'installed_engine_source_sha256': sha(engine_path),
        },
        'jobs': jobs,
        'job_matrix_sha256': digest_object(jobs),
        'job_count': 4,
        'observation_range': [0, 72],
        'native_transitions_per_side': 72,
        'required_workers': 1,
        'max_jobs_per_worker_process': 4,
        'pass_gates': {
            'observations': 'full candidate/reference observation equality at every step 0..72',
            'actions': 'actions equal at steps 0..71; THIRD may differ only at step 72; ChrisTu equal through step 72',
            'guard': 'runtime hands/pastures equal frozen observation-1 values; candidate requested and selected branch are source in every job',
            'runtime_key': 'compute from the actual step-72 source-branch observation; THIRD must equal the Brunch goose key, ChrisTu must not equal it',
            'leaf': 'commit only Brunch route 113332529 once in THIRD; no ChrisTu commit',
            'route_map': 'step-0 reset equals exact 6d base map; only Brunch descendants plus base key change on THIRD; no map change on ChrisTu',
            'opening_procurement': 'common step-0 and source step-1 actions match reference; source guard, expected physical/private procurement, and error counters pass',
            'errors': 'zero policy, collision, procurement, bridge, leaf-commit, or native transition errors; both sides ACTIVE at observation 72',
            'state': 'own physical/private state equal through observation 72; shared market and cash are recorded',
        },
        'output_paths': {
            'progress': str(PROGRESS_PATH.resolve()), 'results': str(RESULTS_PATH.resolve()),
            'exclusive_run_lock': str(LOCK_PATH.resolve()),
            'static_freeze_receipt': str(FREEZE_RECEIPT_PATH.resolve()),
        },
        'file_bindings': dict(sorted(bindings.items())),
    }
    manifest['file_binding_count'] = len(bindings)
    write_new(MANIFEST_PATH, manifest)
    receipt = {
        'schema': 'a44-goose4-smoothie-pasture-source-prefix-static-freeze-v1',
        'static_freeze_passed': True,
        'manifest_path': str(MANIFEST_PATH.resolve()),
        'manifest_sha256': sha(MANIFEST_PATH),
        'runner_path': str(Path(__file__).resolve()),
        'runner_sha256': sha(Path(__file__)),
        'parent_candidate_sha256': SOURCE_SHA,
        'candidate_sha256': static['candidate_sha256'],
        'reference_effective_source_sha256': sha_bytes(forced_source_bytes()),
        'job_matrix_sha256': manifest['job_matrix_sha256'],
        'job_count': 4,
        'job_ids': [job['job_id'] for job in jobs],
        'changed_selector_rows': static['census']['changed_rows'],
        'runtime_key_requirement': {
            'THIRD': LEAF_KEY,
            'ChrisTu': 'actual source-branch key must not equal ' + LEAF_KEY,
        },
        'input_file_binding_count': len(bindings),
        'simulator_jobs_run': 0,
        'native_transitions': 0,
        'full_game_outcomes_run': False,
    }
    write_new(FREEZE_RECEIPT_PATH, receipt)
    print(json.dumps({'frozen': True, 'manifest_path': str(MANIFEST_PATH.resolve()),
                      'manifest_sha256': sha(MANIFEST_PATH),
                      'freeze_receipt_path': str(FREEZE_RECEIPT_PATH.resolve()),
                      'freeze_receipt_sha256': sha(FREEZE_RECEIPT_PATH),
                      'candidate_sha256': static['candidate_sha256'],
                      'reference_effective_source_sha256': sha_bytes(forced_source_bytes()),
                      'jobs': [job['job_id'] for job in jobs],
                      'input_file_binding_count': len(bindings),
                      'simulator_jobs_run': 0}, indent=2))


def verify_manifest() -> dict:
    manifest = read_json(MANIFEST_PATH)
    if manifest.get('schema') != 'a44-goose4-smoothie-pasture-source-prefix-manifest-v1':
        raise AssertionError('prefix manifest schema mismatch')
    for path, digest in manifest['file_bindings'].items():
        if sha(path) != digest:
            raise AssertionError(f'prefix input binding changed: {path}')
    static = current_static()
    jobs = make_jobs(static)
    if manifest['jobs'] != jobs or digest_object(jobs) != manifest['job_matrix_sha256']:
        raise AssertionError('four-job matrix no longer reproduces from bound inputs')
    if manifest.get('job_count') != 4 or manifest.get('required_workers') != 1:
        raise AssertionError('prefix run scope or worker count changed')
    if manifest.get('simulator_jobs_run_at_freeze') != 0 or manifest.get('native_transitions_at_freeze') != 0:
        raise AssertionError('freeze claims simulator activity')
    if manifest['parent_candidate']['sha256'] != SOURCE_SHA or sha(SOURCE) != SOURCE_SHA:
        raise AssertionError('exact 6d parent binding changed')
    if manifest['candidate']['sha256'] != sha(CANDIDATE):
        raise AssertionError('derivative binding changed')
    if manifest.get('runner') != {'path': str(RUNNER.resolve()), 'sha256': sha(RUNNER)}:
        raise AssertionError('prefix runner source hash changed')
    forced_sha = sha_bytes(forced_source_bytes())
    if manifest['reference']['selector_replacement']['effective_source_sha256'] != forced_sha:
        raise AssertionError('forced-source 6d comparator hash changed')
    if manifest['reference']['selector_replacement']['source_file_written'] is not False:
        raise AssertionError('forced-source comparator unexpectedly writes parent source')
    expected_outputs = {
        'progress': str(PROGRESS_PATH.resolve()), 'results': str(RESULTS_PATH.resolve()),
        'exclusive_run_lock': str(LOCK_PATH.resolve()),
        'static_freeze_receipt': str(FREEZE_RECEIPT_PATH.resolve()),
    }
    if manifest.get('output_paths') != expected_outputs:
        raise AssertionError('prefix output paths changed')
    verify_fixtures_and_traces(jobs, manifest['file_bindings'])
    receipt = read_json(FREEZE_RECEIPT_PATH)
    if (receipt.get('schema') != 'a44-goose4-smoothie-pasture-source-prefix-static-freeze-v1'
            or receipt.get('manifest_sha256') != sha(MANIFEST_PATH)
            or receipt.get('runner_sha256') != sha(Path(__file__))
            or receipt.get('candidate_sha256') != sha(CANDIDATE)
            or receipt.get('parent_candidate_sha256') != SOURCE_SHA
            or receipt.get('reference_effective_source_sha256') != forced_sha
            or receipt.get('job_matrix_sha256') != manifest['job_matrix_sha256']
            or receipt.get('job_count') != 4
            or receipt.get('input_file_binding_count') != len(manifest['file_bindings'])
            or receipt.get('simulator_jobs_run') != 0
            or receipt.get('native_transitions') != 0
            or receipt.get('full_game_outcomes_run') is not False):
        raise AssertionError('static freeze receipt is incomplete, stale or claims simulation activity')
    return manifest


def load_policy(path: str, digest: str, module_name: str, force_source: bool = False):
    source = Path(path).read_bytes()
    if sha_bytes(source) != digest:
        raise AssertionError(f'policy hash changed before import: {path}')
    if force_source:
        if Path(path).resolve() != SOURCE.resolve():
            raise AssertionError('forced-source patch is allowed only on exact parent candidate')
        source = forced_source_bytes(source)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None:
        raise RuntimeError(f'cannot construct policy module spec for {path}')
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    return module


def policy_observation(state, seat: int) -> dict:
    return deepcopy(dict(state[seat].observation, remainingOverageTime=60.0))


def own_physical_private(obs: dict, seat: int) -> dict:
    farm = deepcopy(obs['farms'][seat])
    farm.pop('money', None)
    return {'farm_without_cash': farm, 'private': deepcopy(obs['private'])}


def public_features(obs: dict) -> dict:
    rival = obs['farms'][1 - int(obs['player'])]
    pasture_count = sum(isinstance(tile, dict) and tile.get('kind') == 'PASTURE'
                        for row in rival['tiles'] for tile in row)
    melon = cow = sheep = goose = 0
    for row in rival['tiles']:
        for tile in row:
            if isinstance(tile, dict):
                melon += tile.get('crop') == 'MELON'
                cow += tile.get('animal') == 'COW'
                sheep += tile.get('animal') == 'SHEEP'
                goose += tile.get('animal') == 'GOOSE'
    cmp = 'C<S' if cow < sheep else 'C>S' if cow > sheep else 'C=S'
    shops = obs.get('town', {}).get('unlocked_shops') or []
    first_shop = shops[0] if shops else None
    key = (None if first_shop is None else
           first_shop + '|' + ('M8+' if melon >= 8 else 'M<8') + '|' + cmp
           + ('|G+' if goose > 0 else '|G0'))
    return {'rival_hands': len(rival['hands']), 'rival_pastures': pasture_count,
            'rival_melon': melon, 'rival_cows': cow, 'rival_sheep': sheep,
            'rival_geese': goose, 'first_unlocked_shop': first_shop, 'leaf_key': key}


def digest_route_map(value: dict) -> str:
    return digest_object(value)


def route_delta(base: dict, current: dict) -> dict:
    keys = sorted(key for key in set(base) | set(current) if base.get(key) != current.get(key))
    return {'changed_keys': keys,
            'before': {key: base.get(key) for key in keys},
            'after': {key: current.get(key) for key in keys}}


def error_counters(telemetry: dict) -> dict:
    tokens = ('error', 'collision', 'failed', 'refusal', 'procurement',
              'unfilled', 'abort', 'invalid', 'missing_buy')
    return {key: value for key, value in telemetry.items()
            if isinstance(value, (int, float)) and value != 0
            and any(token in key.lower() for token in tokens)}


def transition_run(job: dict, candidate_side: bool) -> dict:
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
    tape = canonical_action_tape(fixture, job['_file_bindings'])
    if candidate_side:
        module = load_policy(job['candidate_path'], job['candidate_sha256'],
                             f'prefix_candidate_{job["job_id"]}')
    else:
        module = load_policy(job['reference_path'], job['reference_sha256'],
                             f'prefix_forced_source_{job["job_id"]}', force_source=True)
    policy_fn = module.agent
    observations, actions, trace_hashes = [], [], []
    telemetry_at_step1 = {}
    map_reset_matches = False
    policy_errors, bridge_errors, native_errors = {}, {}, []
    source_procurement_state = None
    started = time.perf_counter()
    try:
        for step in range(73):
            obs = policy_observation(state, int(job['candidate_seat']))
            if int(obs['step']) != step:
                raise AssertionError(f'nonconsecutive native state: expected {step}, got {obs["step"]}')
            action = policy_fn(obs, cfg)
            action_copy = deepcopy(action)
            route_map = deepcopy(module._DATA['route_map'])
            observations.append({
                'step': step,
                'observation_sha256': digest_object(obs),
                'own_physical_private_sha256': digest_object(
                    own_physical_private(obs, int(job['candidate_seat']))),
                'shared_market_sha256': digest_object(deepcopy(obs.get('market', {}))),
                'cash': {'own': obs['farms'][int(job['candidate_seat'])].get('money'),
                         'rival': obs['farms'][1-int(job['candidate_seat'])].get('money')},
                'public_features': public_features(obs) if step in (1, 72) else None,
                'route_map_sha256': digest_route_map(route_map) if step in (0, 1, 72) else None,
                'route_map': route_map if step == 72 else None,
            })
            actions.append(action_copy)
            trace_hashes.append(digest_object({'step': step, 'observation': obs,
                                               'action': action_copy}))
            telemetry = deepcopy(dict(getattr(module.agent, 'telemetry', {}) or {}))
            if step == 0:
                map_reset_matches = (route_map == module._A44_GOOSE4_BASE_ROUTE_MAP)
            if step == 1:
                telemetry_at_step1 = telemetry
            for key, value in error_counters(telemetry).items():
                policy_errors[key] = max(value, policy_errors.get(key, 0))
            bridge_now = dict(getattr(module, '_BRIDGE_STATS', {}) or {})
            for key in ('bridge_common_failed', 'bridge_guard_refusals',
                        'bridge_source_guard_failed', 'bridge_errors'):
                value = bridge_now.get(key, 0)
                if value:
                    bridge_errors[key] = max(value, bridge_errors.get(key, 0))
            if step < 72:
                state[int(job['candidate_seat'])].action = deepcopy(action_copy)
                state[1-int(job['candidate_seat'])].action = deepcopy(tape[step])
                try:
                    native_core.interpreter(state, env)
                except Exception as exc:
                    native_errors.append({'step': step, 'type': type(exc).__name__, 'message': str(exc)})
                    raise
                for item in state:
                    item.observation.step = step + 1
                if step == 1:
                    obs2 = policy_observation(state, int(job['candidate_seat']))
                    own_seat = int(job['candidate_seat'])
                    farm = deepcopy(obs2['farms'][own_seat])
                    private = deepcopy(obs2['private'])
                    expected = module._bridge_expected('source', cfg)
                    actual = module._bridge_physical(farm, private)
                    source_procurement_state = {
                        'expected_physical_private_sha256': digest_object(expected),
                        'actual_physical_private_sha256': digest_object(actual),
                        'matches_expected_source_branch_state': actual == expected,
                    }
        telemetry_final = deepcopy(dict(getattr(module.agent, 'telemetry', {}) or {}))
        bridge_stats = deepcopy(dict(getattr(module, '_BRIDGE_STATS', {}) or {}))
        pasture_stats = deepcopy(dict(getattr(module, '_A44_PASTURE_BRUNCH_STATS', {}) or {}))
        return {
            'observations': observations, 'actions': actions, 'trace_hashes': trace_hashes,
            'step1_telemetry': telemetry_at_step1, 'final_telemetry': telemetry_final,
            'bridge_stats': bridge_stats, 'pasture_stats': pasture_stats,
            'route_map_reset_matches': map_reset_matches,
            'base_route_map': deepcopy(module._A44_GOOSE4_BASE_ROUTE_MAP),
            'source_procurement_state': source_procurement_state,
            'policy_error_counters': policy_errors, 'bridge_error_counters': bridge_errors,
            'native_transition_errors': native_errors,
            'wall_seconds': time.perf_counter() - started,
            'status_at_observation72': [getattr(item, 'status', None) for item in state],
        }
    finally:
        del module, state, tape
        gc.collect()


def compare_job(job: dict) -> dict:
    reference = transition_run(job, candidate_side=False)
    candidate = transition_run(job, candidate_side=True)
    seat = int(job['candidate_seat'])
    fixture_id = job['fixture_id']
    obs_rows, action_rows = [], []
    for step, (ref_row, cand_row) in enumerate(zip(reference['observations'], candidate['observations'])):
        obs_rows.append({
            'step': step,
            'full_observation_equal': ref_row['observation_sha256'] == cand_row['observation_sha256'],
            'own_physical_private_equal': ref_row['own_physical_private_sha256'] == cand_row['own_physical_private_sha256'],
            'shared_market_equal': ref_row['shared_market_sha256'] == cand_row['shared_market_sha256'],
            'candidate_cash': cand_row['cash'], 'reference_cash': ref_row['cash'],
        })
        action_rows.append({'step': step, 'equal': candidate['actions'][step] == reference['actions'][step],
                            'candidate': candidate['actions'][step],
                            'reference': reference['actions'][step]})
    diff_steps = [row['step'] for row in action_rows if not row['equal']]
    candidate_step1 = candidate['step1_telemetry']
    reference_step1 = reference['step1_telemetry']
    candidate_obs1 = candidate['observations'][1]['public_features']
    reference_obs1 = reference['observations'][1]['public_features']
    candidate_obs72 = candidate['observations'][72]['public_features']
    reference_obs72 = reference['observations'][72]['public_features']
    pasture_stats = candidate['pasture_stats']
    candidate_map72 = candidate['observations'][72]['route_map']
    reference_map72 = reference['observations'][72]['route_map']
    base_map = candidate['base_route_map']
    if base_map != reference['base_route_map']:
        raise AssertionError('candidate and forced-source base route maps differ')
    expected_brunch_keys = sorted({
        key for key in base_map if key == 'BRUNCH_SPOT' or key.startswith('BRUNCH_SPOT|')
    } | {'BRUNCH_SPOT'})
    candidate_delta = route_delta(base_map, candidate_map72)
    reference_delta = route_delta(base_map, reference_map72)
    ref_base_hash = reference['observations'][0]['route_map_sha256']
    cand_base_hash = candidate['observations'][0]['route_map_sha256']
    source_selection_gate = (
        candidate_step1.get('bridge_requested') == 'source'
        and candidate_step1.get('bridge_selected') == 'source'
        and reference_step1.get('bridge_requested') == 'source'
        and reference_step1.get('bridge_selected') == 'source'
        and pasture_stats.get('pasture_guard_requested_step1') == 'source'
        and pasture_stats.get('pasture_guard_selected_step1') == 'source'
        and pasture_stats.get('pasture_guard_rival_hands_step1') == job['expected_step1_public']['rival_hands']
        and pasture_stats.get('pasture_guard_rival_pastures_step1') == job['expected_step1_public']['rival_pastures']
        and candidate_obs1['rival_hands'] == job['expected_step1_public']['rival_hands']
        and candidate_obs1['rival_pastures'] == job['expected_step1_public']['rival_pastures']
        and reference_obs1['rival_hands'] == candidate_obs1['rival_hands']
        and reference_obs1['rival_pastures'] == candidate_obs1['rival_pastures'])
    observations_gate = all(row['full_observation_equal'] for row in obs_rows)
    state_gate = all(row['own_physical_private_equal'] for row in obs_rows if 2 <= row['step'] <= 72)
    action_equal_through71 = all(action_rows[step]['equal'] for step in range(72))
    opening_gate = action_rows[0]['equal'] and action_rows[1]['equal']
    reset_gate = (candidate['route_map_reset_matches'] and reference['route_map_reset_matches']
                  and cand_base_hash == ref_base_hash)
    error_gate = (not candidate['policy_error_counters'] and not reference['policy_error_counters']
                  and not candidate['bridge_error_counters'] and not reference['bridge_error_counters']
                  and not candidate['native_transition_errors'] and not reference['native_transition_errors']
                  and all(candidate['bridge_stats'].get(key, 0) == 0 for key in (
                      'bridge_common_failed', 'bridge_guard_refusals',
                      'bridge_source_guard_failed', 'bridge_errors'))
                   and int(pasture_stats.get('pasture_brunch_errors', 0)) == 0)
    procurement_gate = (
        candidate['source_procurement_state'] is not None
        and reference['source_procurement_state'] is not None
        and candidate['source_procurement_state']['matches_expected_source_branch_state']
        and reference['source_procurement_state']['matches_expected_source_branch_state'])
    candidate_route = str(pasture_stats.get('pasture_brunch_route72', ''))
    candidate_turns = int(pasture_stats.get('pasture_brunch_turns', 0))
    candidate_key_reported = pasture_stats.get('pasture_brunch_key72')
    candidate_key_actual = candidate_obs72['leaf_key']
    key_gate = candidate_key_reported == candidate_key_actual
    if fixture_id == THIRD_ID:
        runtime_leaf_gate = (candidate_key_actual == LEAF_KEY and candidate_route == str(LEAF_ROUTE)
                             and candidate_turns == 1)
        route_map_gate = (
            candidate_delta['changed_keys'] == expected_brunch_keys
            and all(candidate_delta['after'].get(key) == LEAF_ROUTE for key in expected_brunch_keys)
            and not reference_delta['changed_keys'])
        action72_gate = set(diff_steps).issubset({72})
        action72_detail = {'difference_allowed': True,
                           'difference_present': not action_rows[72]['equal'],
                           'candidate': action_rows[72]['candidate'],
                           'reference': action_rows[72]['reference']}
    else:
        runtime_leaf_gate = (candidate_key_actual != LEAF_KEY and not candidate_route
                             and candidate_turns == 0)
        route_map_gate = not candidate_delta['changed_keys'] and not reference_delta['changed_keys']
        action72_gate = diff_steps == [] and action_rows[72]['equal']
        action72_detail = {'difference_allowed': False,
                           'difference_present': not action_rows[72]['equal'],
                           'candidate': action_rows[72]['candidate'],
                           'reference': action_rows[72]['reference']}
    status_gate = (candidate['status_at_observation72'] == ['ACTIVE', 'ACTIVE']
                   and reference['status_at_observation72'] == ['ACTIVE', 'ACTIVE'])
    expected_route_loaded = True
    # The static preflight already resolved route 113332529 to a 719-action
    # source schedule. Record the check alongside the runtime route-map gate.
    static_route = read_json(STATIC_PATH)['route_map_static_check']
    expected_route_loaded = (static_route['route_id'] == LEAF_ROUTE
                             and static_route['route_action_count'] == 719)
    checks = {
        'full_observation_equality_steps0_72': observations_gate,
        'own_physical_private_equality_observations2_72': state_gate,
        'actions_equal_steps0_71': action_equal_through71,
        'common_step0_and_source_step1_actions_equal': opening_gate,
        'source_branch_and_public_selector_values': source_selection_gate,
        'route_map_step0_reset': reset_gate,
        'step72_key_matches_actual_source_observation': key_gate,
        'fixture_leaf_activation': runtime_leaf_gate,
        'only_intended_brunch_route_map_change': route_map_gate,
        'source_step1_procurement_matches_expected_physical_private_state': procurement_gate,
        'step72_action_allowance': action72_gate,
        'zero_policy_bridge_leaf_procurement_native_errors': error_gate,
        'both_policies_active_at_observation72': status_gate,
        'route113332529_is_719_action_schedule': expected_route_loaded,
    }
    return {
        'job_id': job['job_id'], 'fixture_id': fixture_id,
        'candidate_seat': seat, 'comparison': job['comparison'],
        'seed': job['seed'], 'candidate_sha256': job['candidate_sha256'],
        'reference_source_sha256': job['reference_sha256'],
        'reference_effective_source_sha256': job['reference_effective_source_sha256'],
        'candidate_requested_branch': candidate_step1.get('bridge_requested'),
        'candidate_selected_branch': candidate_step1.get('bridge_selected'),
        'candidate_step1_public_features': candidate_obs1,
        'reference_step1_public_features': reference_obs1,
        'candidate_runtime_step72_public_features': candidate_obs72,
        'reference_runtime_step72_public_features': reference_obs72,
        'candidate_reported_step72_key': candidate_key_reported,
        'candidate_reported_step72_route': candidate_route,
        'candidate_reported_leaf_turns': candidate_turns,
        'expected_brunch_route_map_keys': expected_brunch_keys,
        'candidate_route_map_delta': candidate_delta,
        'reference_route_map_delta': reference_delta,
        'step72_action': action72_detail,
        'action_difference_steps': diff_steps,
        'observation_comparisons': obs_rows,
        'action_comparisons': action_rows,
        'candidate_step1_telemetry': candidate_step1,
        'reference_step1_telemetry': reference_step1,
        'candidate_final_telemetry': candidate['final_telemetry'],
        'candidate_bridge_stats': candidate['bridge_stats'],
        'candidate_pasture_stats': pasture_stats,
        'candidate_source_procurement_state': candidate['source_procurement_state'],
        'reference_source_procurement_state': reference['source_procurement_state'],
        'candidate_policy_error_counters': candidate['policy_error_counters'],
        'reference_policy_error_counters': reference['policy_error_counters'],
        'candidate_bridge_error_counters': candidate['bridge_error_counters'],
        'reference_bridge_error_counters': reference['bridge_error_counters'],
        'candidate_native_transition_errors': candidate['native_transition_errors'],
        'reference_native_transition_errors': reference['native_transition_errors'],
        'candidate_status_at_observation72': candidate['status_at_observation72'],
        'reference_status_at_observation72': reference['status_at_observation72'],
        'candidate_prefix_seconds': candidate['wall_seconds'],
        'reference_prefix_seconds': reference['wall_seconds'],
        'native_transitions_per_side': 72,
        'checks': checks,
        'passed': all(checks.values()),
    }


def run_prefix(workers: int) -> None:
    if workers != 1:
        raise ValueError('the frozen 6d prefix plan requires exactly one worker')
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    with exclusive_run(LOCK_PATH):
        _run_prefix_locked()


def _run_prefix_locked() -> None:
    manifest = verify_manifest()
    if RESULTS_PATH.exists():
        raise FileExistsError('prefix_results.json exists; refusing to overwrite it')
    expected_ids = {job['job_id'] for job in manifest['jobs']}
    rows = []
    if PROGRESS_PATH.exists():
        rows = [json.loads(line) for line in PROGRESS_PATH.read_text(encoding='utf-8').splitlines()
                if line.strip()]
    done = {row['job_id'] for row in rows}
    if len(done) != len(rows) or not done.issubset(expected_ids):
        raise AssertionError('prefix checkpoint has duplicate or unexpected jobs')
    if any(row.get('manifest_sha256') != sha(MANIFEST_PATH) for row in rows):
        raise AssertionError('prefix checkpoint belongs to a different manifest')
    pending = [job for job in manifest['jobs'] if job['job_id'] not in done]
    mode = 'a' if PROGRESS_PATH.exists() else 'x'
    with PROGRESS_PATH.open(mode, encoding='utf-8') as stream:
        if pending:
            with ProcessPoolExecutor(max_workers=1, max_tasks_per_child=4) as executor:
                for job in pending:
                    job['_file_bindings'] = manifest['file_bindings']
                    result = executor.submit(compare_job, job).result()
                    result['manifest_sha256'] = sha(MANIFEST_PATH)
                    rows.append(result)
                    stream.write(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({'completed': len(rows), 'total': 4,
                                      'job_id': result['job_id'], 'passed': result['passed']},
                                     ensure_ascii=False), flush=True)
    by_id = {row['job_id']: row for row in rows}
    if set(by_id) != expected_ids:
        raise AssertionError('four source-prefix rows are incomplete')
    ordered = [by_id[job['job_id']] for job in manifest['jobs']]
    third = [row for row in ordered if row['fixture_id'] == THIRD_ID]
    chris = [row for row in ordered if row['fixture_id'] == CHRIS_ID]
    third_actions = all(set(row['action_difference_steps']).issubset({72})
                        and row['checks']['actions_equal_steps0_71'] for row in third)
    chris_actions = all(row['action_difference_steps'] == []
                         and row['checks']['actions_equal_steps0_71'] for row in chris)
    passed = (len(ordered) == 4 and all(row['passed'] for row in ordered)
              and len(third) == len(chris) == 2 and third_actions and chris_actions)
    receipt = {
        'schema': 'a44-goose4-smoothie-pasture-source-prefix-result-v1',
        'complete': len(ordered) == 4, 'passed': passed,
        'manifest_path': str(MANIFEST_PATH.resolve()), 'manifest_sha256': sha(MANIFEST_PATH),
        'candidate_sha256': manifest['candidate']['sha256'],
        'parent_candidate_sha256': manifest['parent_candidate']['sha256'],
        'reference_effective_source_sha256': manifest['reference']['selector_replacement']['effective_source_sha256'],
        'job_count': 4, 'third_step72_only_action_difference_gate': third_actions,
        'christu_actions_equal_through72_gate': chris_actions,
        'native_transitions_per_side': 72, 'full_game_outcomes_run': False,
        'jobs': ordered, 'completed_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    write_new(RESULTS_PATH, receipt)
    print(json.dumps({key: value for key, value in receipt.items() if key != 'jobs'}, indent=2))


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
                          'candidate_sha256': manifest['candidate']['sha256'],
                          'job_count': manifest['job_count'],
                          'simulator_jobs_run': 0}, indent=2))
    else:
        run_prefix(args.workers)


if __name__ == '__main__':
    main()
