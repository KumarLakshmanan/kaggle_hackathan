from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ROMAN = HERE.parent
V5_PACKAGE = ROOT / 'diagnostics/a44_ghost_kwa_piice_goalpanel_20260929'
V5_CANDIDATE = V5_PACKAGE / 'candidate.py'
V5_PANEL = V5_PACKAGE / 'panel.json'
V5_RECEIPT = V5_PACKAGE / 'outcome_receipt.json'
V5_MANIFEST = V5_PACKAGE / 'frozen_manifest.json'
FEATURE_ROWS = ROOT / 'diagnostics/a44_source_bridge_goose_4leaf_20260929/feature_rows.json'
DONOR = ROOT / 'diagnostics/donor_opening_agents_20260928/candidate_shared166.py'
ADAPTER = ROMAN / 'adapter_layer.py'
CACHE_HELPER = ROOT / 'diagnostics/stream_replay_io_20260928/cached_input.py'
INITIAL_CACHE = ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json'
NATIVE_HELPER = ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py'
NATIVE_CHECK = ROOT / 'diagnostics/physical_route_rollout_20260928/check.py'
RUN_LOCK_HELPER = ROOT / 'diagnostics/local_target_20260928/run_lock.py'
ENGINE = None
MANIFEST = HERE / 'freeze_manifest.json'
RUN_MANIFEST = HERE / 'run_manifest.json'
PROGRESS = HERE / 'prefix_progress.jsonl'
SNAPSHOTS = HERE / 'expected_step2_public_snapshots.json'
RECEIPT = HERE / 'prefix_receipt.json'
OWN_LOCK = HERE / 'run.lock'
SHARED_LOCK = ROOT / 'diagnostics/.shared_game_run.lock'

TARGET_ID = 'live-114270587'
TARGET_REPLAY_SHA = 'f583a9acbd01eb997b74f5ea3d8b533ae55cf79a6712ae2a50f5c20b18ab8774'
TAPE_FILE_SHA = '18ba3ec92eec0ec7bab95498119eebae88e7ce0ca4571eba42ffbaeb9ddda4b1'
TAPE_PAYLOAD_SHA = '4fa1c7ac2d31990c78ef1b73bc995d7cbf12e4813b6646611537274469553455'
TAPE_ACTION1_SHA = '48e7b680c2f75b6a1d838749d1289420710bd6fb05c27275c9f2c38ac26769ff'
V5_SHA = '8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62'
DONOR_SHA = 'fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849'
OUTPUTS = (RUN_MANIFEST, PROGRESS, SNAPSHOTS, RECEIPT, OWN_LOCK)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def digest_json(value) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                ensure_ascii=True).encode('utf-8'))


def read(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_once(path: Path, value):
    raw = (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + '\n').encode('utf-8')
    with Path(path).open('xb') as stream:
        stream.write(raw)


def engine_path() -> Path:
    spec = importlib.util.find_spec('kaggle_environments')
    if spec is None or not spec.origin:
        raise RuntimeError('installed kaggle-environments engine is unavailable')
    if importlib.metadata.version('kaggle-environments') != '1.32.7':
        raise RuntimeError('expected Kaggriculture engine 1.32.7')
    path = Path(spec.origin).parent / 'envs' / 'kaggriculture' / 'kaggriculture.py'
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.resolve()


def fixture_rows():
    panel = read(V5_PANEL)
    receipt = read(V5_RECEIPT)
    assert panel.get('candidate_sha256') == V5_SHA
    assert receipt.get('candidate_sha256') == V5_SHA
    assert receipt.get('complete') is True and receipt.get('game_count') == 100
    assert receipt.get('loss30_winning_sweeps') == 25
    assert receipt.get('top20_winning_sweeps') == 19
    rows = [row for row in panel['games'] if row['fixture_id'] == TARGET_ID]
    assert len(rows) == 2 and {int(row['candidate_seat']) for row in rows} == {0, 1}
    assert all(row['source_fixture']['source_replay_sha256'] == TARGET_REPLAY_SHA
               for row in rows)
    assert all(row['source_fixture']['source_opponent_action_sha256'] == TAPE_PAYLOAD_SHA
               for row in rows)
    return rows


def make_manifest(check_empty=True):
    if check_empty and any(path.exists() for path in (MANIFEST, *OUTPUTS)):
        raise FileExistsError('probe is one-shot; freeze or output already exists')
    rows = fixture_rows()
    features = read(FEATURE_ROWS)
    feature_by_key = {(row['fixture_id'], int(row['seat'])): row
                      for row in features['rows']}
    jobs = []
    for row in rows:
        seat = int(row['candidate_seat'])
        fixture = deepcopy(row['source_fixture'])
        feature = feature_by_key[(TARGET_ID, seat)]
        tape_path = Path(fixture['source_action_tape_path']).resolve()
        replay_path = Path(fixture['source_replay_path']).resolve()
        trace_path = Path(feature['trace_path']).resolve()
        # `source_replay_sha256` identifies the decompressed replay payload;
        # the raw gzip bytes are separately frozen in `bindings` below.
        assert sha_bytes(gzip.decompress(replay_path.read_bytes())) == TARGET_REPLAY_SHA
        assert sha(tape_path) == TAPE_FILE_SHA
        assert sha(trace_path) == feature['trace_sha256']
        payload = json.loads(gzip.decompress(tape_path.read_bytes()))['actions']
        assert len(payload) == 719
        payload_hash = digest_json(payload)
        assert payload_hash == TAPE_PAYLOAD_SHA
        assert digest_json(payload[1]) == TAPE_ACTION1_SHA
        jobs.append({
            'fixture_id': TARGET_ID,
            'candidate_seat': seat,
            'fixture': fixture,
            'source_trace_path': str(trace_path),
            'source_trace_sha256': feature['trace_sha256'],
            'opponent_tape_file_sha256': TAPE_FILE_SHA,
            'opponent_tape_payload_sha256': payload_hash,
            'opponent_action1_sha256': digest_json(payload[1]),
        })

    engine = engine_path()
    paths = [HERE / 'PLAN.md', HERE / 'prefix_probe.py', V5_CANDIDATE,
             V5_PANEL, V5_RECEIPT, V5_MANIFEST, FEATURE_ROWS, DONOR,
             ADAPTER, CACHE_HELPER, INITIAL_CACHE, NATIVE_HELPER, NATIVE_CHECK,
             RUN_LOCK_HELPER, engine]
    for job in jobs:
        paths.extend((Path(job['fixture']['source_replay_path']),
                      Path(job['fixture']['source_action_tape_path']),
                      Path(job['source_trace_path'])))
    bindings = {str(path.resolve()): sha(path.resolve())
                for path in sorted(set(paths), key=lambda item: str(item).lower())}
    assert bindings[str(V5_CANDIDATE.resolve())] == V5_SHA
    assert bindings[str(DONOR.resolve())] == DONOR_SHA
    return {
        'schema': 'roman-shared166-exact-v5-two-seat-prefix-freeze-v1',
        'complete': True,
        'diagnostic_only': True,
        'fixed_opponent_tape': True,
        'full_games': 0,
        'engine_transitions_at_freeze': 0,
        'parent_candidate_sha256': V5_SHA,
        'donor_candidate_sha256': DONOR_SHA,
        'adapter_sha256': sha(ADAPTER),
        'job_count': len(jobs),
        'jobs': jobs,
        'binding_count': len(bindings),
        'bindings': bindings,
        'shared_lock_path': str(SHARED_LOCK),
        'worker_count': 1,
        'resume_allowed': False,
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
    }


def verify():
    manifest = read(MANIFEST)
    expected = make_manifest(check_empty=False)
    assert set(manifest) == set(expected), 'freeze manifest has unexpected or missing fields'
    for key, value in expected.items():
        if key != 'frozen_at_utc':
            assert manifest[key] == value, f'frozen manifest field changed: {key}'
    assert isinstance(manifest.get('frozen_at_utc'), str) and manifest['frozen_at_utc']
    assert manifest.get('complete') is True and manifest.get('diagnostic_only') is True
    assert manifest.get('fixed_opponent_tape') is True and manifest.get('full_games') == 0
    assert manifest.get('parent_candidate_sha256') == V5_SHA
    assert manifest.get('donor_candidate_sha256') == DONOR_SHA
    assert manifest.get('binding_count') == len(manifest.get('bindings', {}))
    assert len(manifest['jobs']) == 2
    assert {int(job['candidate_seat']) for job in manifest['jobs']} == {0, 1}
    return manifest


def freeze():
    manifest = make_manifest()
    write_once(MANIFEST, manifest)
    print(json.dumps({key: manifest[key] for key in
                      ('complete', 'parent_candidate_sha256', 'donor_candidate_sha256',
                       'adapter_sha256', 'job_count', 'binding_count')}, indent=2))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot load {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_inputs(job):
    sys.path.insert(0, str(ROOT))
    from diagnostics.physical_route_rollout_20260928.check import Box, state_from_frames
    from diagnostics.stream_replay_io_20260928.cached_input import load_fixture
    fixture = job['fixture']
    cached = load_fixture(fixture)
    state = state_from_frames(cached['steps'][0])
    cfg = dict(cached['configuration'])
    cfg['seed'] = None
    env = Box(configuration=Box(**cfg), info={'seed': int(fixture['seed'])}, done=False)
    tape = json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
    return state, cfg, env, tape


def obs_copy(state, player):
    return deepcopy(dict(state[player].observation, remainingOverageTime=60.0))


def apply_transition(state, env, player, action, opponent_action, step):
    state[player].action = deepcopy(action)
    state[1 - player].action = deepcopy(opponent_action)
    from diagnostics.physical_route_rollout_20260928 import native_core
    native_core.interpreter(state, env)
    for item in state:
        item.observation.step = step + 1


def source_trace(job):
    wanted = {}
    with gzip.open(job['source_trace_path'], 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            step = int(row['step'])
            if step <= 2:
                wanted[step] = row
            if len(wanted) == 3:
                break
    assert set(wanted) == {0, 1, 2}
    return wanted


def comparable_observation(observation):
    def plain(value):
        if isinstance(value, dict):
            return {key: plain(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [plain(item) for item in value]
        return value
    return {key: plain(value) for key, value in dict(observation).items()
            if key != 'remainingOverageTime'}


def expected_own_state_after_hire(observation1, seat):
    """Project the complete own farm/private state after the guarded HIRE."""
    own = deepcopy(observation1['farms'][seat])
    if len(own.get('hands', [])) != 4 or int(own.get('hires_today', -1)) != 4:
        raise ValueError('step-1 own state is not the guarded four-hand opening')
    expected_farm = deepcopy(own)
    expected_farm['farmer'] = [4, 3]
    expected_farm['hands'] = [[5, 4], [4, 5], [5, 5], [4, 4], [4, 4]]
    expected_farm['hires_today'] = 5
    expected_farm['money'] = float(own['money']) - 5.0

    expected_private = deepcopy(observation1['private'])
    inventories = expected_private.get('inventories')
    if not isinstance(inventories, list) or len(inventories) != 5:
        raise ValueError('step-1 private inventory does not match four hands plus farmer')
    expected_private['inventories'] = deepcopy(inventories) + [{}]
    return expected_farm, expected_private


def run_v5_prefix(job, suffix):
    seat = int(job['candidate_seat'])
    state, cfg, env, tape = load_inputs(job)
    parent = load_module(V5_CANDIDATE, f'roman_v5_{suffix}_seat{seat}')
    trace = source_trace(job)
    observed = {0: obs_copy(state, seat)}
    actions = {}
    for step in (0, 1):
        observation = obs_copy(state, seat)
        action = parent.agent(observation, cfg)
        actions[step] = deepcopy(action)
        apply_transition(state, env, seat, action, tape[step], step)
        observed[step + 1] = obs_copy(state, seat)
    source_checks = {
        'step0_observation_matches_source': comparable_observation(observed[0]) == comparable_observation(trace[0]['observation']),
        'step0_action_matches_source': actions[0] == trace[0]['action'],
        'step1_observation_matches_source': comparable_observation(observed[1]) == comparable_observation(trace[1]['observation']),
        'step1_action_matches_source': actions[1] == trace[1]['action'],
        'step2_observation_matches_source': comparable_observation(observed[2]) == comparable_observation(trace[2]['observation']),
    }
    return {
        'observations': observed,
        'actions': actions,
        'source_checks': source_checks,
        'opening_matches_source': all(source_checks.values()),
        'status': [item.status for item in state],
    }


def make_dummy_snapshot(layer, job):
    """Let the guarded bridge reach its HIRE only for this tagged probe.

    The public values are deliberately placeholders: discovery records the
    actual post-HIRE snapshot, then a second replay must match it before the
    adapter can call the donor. Provenance fields satisfy the adapter's
    fail-closed pre-HIRE contract and are checked independently by the runner.
    """
    return {
        'candidate_seat': int(job['candidate_seat']),
        'fixture_id': TARGET_ID,
        'source_replay_sha256': job['fixture']['source_replay_sha256'],
        'opponent_tape_file_sha256': job['opponent_tape_file_sha256'],
        'opponent_tape_payload_sha256': job['opponent_tape_payload_sha256'],
        'rival_farm': {key: None for key in layer._EXPECTED_RIVAL_FARM_KEYS},
        'market': {'inventory': {}, 'prices': {}},
        'opponent_action_tape_sha256': layer.MATCHED_OPP_ACTION_TAPE_SHA256,
        'opponent_action_index': 1,
        'opponent_action_sha256': layer.MATCHED_OPP_STEP1_ACTION_SHA256,
        'adapter_step': 1,
        'adapter_action_sha256': layer.ADAPTER_STEP1_ACTION_SHA256,
    }


def discover_adapter_snapshot(job, layer_source_sha, seat_baseline):
    seat = int(job['candidate_seat'])
    if sha(ADAPTER) != layer_source_sha:
        return {'candidate_seat': seat,
                'checks': {'adapter_source_hash_matches_freeze': False},
                'snapshot': None}
    if sha(V5_CANDIDATE) != V5_SHA or sha(DONOR) != DONOR_SHA:
        return {'candidate_seat': seat,
                'checks': {'parent_and_donor_source_hashes_match_freeze': False},
                'snapshot': None}
    state, cfg, env, tape = load_inputs(job)
    parent = load_module(V5_CANDIDATE, f'roman_discover_v5_seat{seat}')
    donor = load_module(DONOR, f'roman_discover_donor_seat{seat}')
    layer = load_module(ADAPTER, f'roman_discover_layer_seat{seat}')
    dummy = make_dummy_snapshot(layer, job)
    adapted = layer.make_agent(parent.agent, donor._donor_action, dummy)
    obs0 = obs_copy(state, seat)
    action0 = adapted(obs0, cfg)
    apply_transition(state, env, seat, action0, tape[0], 0)
    obs1 = obs_copy(state, seat)
    trigger = layer._public_trigger(obs1)
    own_opening = layer._expected_parent_opening_state(obs1)
    action1 = adapted(obs1, cfg)
    expected_hire = layer._fifth_hire_action(obs1)
    apply_transition(state, env, seat, action1, tape[1], 1)
    obs2 = obs_copy(state, seat)
    merge_state = layer._expected_step2_merge_state(obs2)
    expected_farm, expected_private = expected_own_state_after_hire(obs1, seat)
    snapshot = {
        'candidate_seat': seat,
        'fixture_id': TARGET_ID,
        'source_replay_sha256': job['fixture']['source_replay_sha256'],
        'opponent_tape_file_sha256': job['opponent_tape_file_sha256'],
        'opponent_tape_payload_sha256': job['opponent_tape_payload_sha256'],
        'opponent_action_tape_sha256': layer.MATCHED_OPP_ACTION_TAPE_SHA256,
        'opponent_action_index': 1,
        'opponent_action_sha256': job['opponent_action1_sha256'],
        'adapter_step': 1,
        'adapter_action_sha256': digest_json(action1),
        'rival_farm': deepcopy(obs2['farms'][1 - seat]),
        'market': deepcopy(obs2['market']),
        'own_farm': deepcopy(obs2['farms'][seat]),
        'own_private': deepcopy(obs2['private']),
        'observation2_sha256': digest_json(comparable_observation(obs2)),
    }
    checks = {
        'adapter_source_hash_matches_freeze': True,
        'parent_and_donor_source_hashes_match_freeze': True,
        'step0_action_matches_v5': action0 == seat_baseline['actions'][0],
        'step1_observation_matches_v5': comparable_observation(obs1) == comparable_observation(seat_baseline['observations'][1]),
        'public_trigger': bool(trigger),
        'own_step1_opening_guard': bool(own_opening),
        'fifth_hire_action': action1 == expected_hire,
        'adapter_action_hash_bound': snapshot['adapter_action_sha256'] == layer.ADAPTER_STEP1_ACTION_SHA256,
        'step2_own_merge_guard': bool(merge_state),
        'step2_complete_own_state_matches_prediction': (
            obs2['farms'][seat] == expected_farm and obs2['private'] == expected_private),
        'step2_hire_count_5': len(obs2['farms'][seat]['hands']) == 5 and obs2['farms'][seat]['hires_today'] == 5,
        'step2_cash_1083': float(obs2['farms'][seat]['money']) == 1083.0,
        'step2_expected_own_hands': obs2['farms'][seat]['hands'] == [[5, 4], [4, 5], [5, 5], [4, 4], [4, 4]],
        'snapshot_tape_provenance': (
            snapshot['candidate_seat'] == seat
            and snapshot['fixture_id'] == TARGET_ID
            and snapshot['source_replay_sha256'] == job['fixture']['source_replay_sha256']
            and snapshot['opponent_tape_file_sha256'] == job['opponent_tape_file_sha256']
            and snapshot['opponent_tape_payload_sha256'] == job['opponent_tape_payload_sha256']
            and snapshot['opponent_action_tape_sha256'] == layer.MATCHED_OPP_ACTION_TAPE_SHA256
            and snapshot['opponent_action_index'] == 1
            and snapshot['opponent_action_sha256'] == layer.MATCHED_OPP_STEP1_ACTION_SHA256
            and snapshot['adapter_step'] == 1
            and snapshot['adapter_action_sha256'] == layer.ADAPTER_STEP1_ACTION_SHA256
        ),
        'status_active': all(status == 'ACTIVE' for status in (state[0].status, state[1].status)),
    }
    return {'candidate_seat': seat, 'checks': checks, 'snapshot': snapshot,
            'v5_step0': seat_baseline['actions'][0],
            'v5_step1': seat_baseline['actions'][1],
            'adapted_step0': action0, 'adapted_step1': action1,
            'v5_observation2': comparable_observation(seat_baseline['observations'][2]),
            'adapter_observation1': comparable_observation(obs1),
            'adapter_observation2': comparable_observation(obs2)}


def validate_adapter_snapshot(job, snapshot, discovered, frozen_adapter_sha256):
    seat = int(job['candidate_seat'])
    if sha(ADAPTER) != frozen_adapter_sha256:
        return {'candidate_seat': seat,
                'checks': {'adapter_source_hash_matches_freeze': False},
                'refused_snapshot_injection': True}
    if sha(V5_CANDIDATE) != V5_SHA or sha(DONOR) != DONOR_SHA:
        return {'candidate_seat': seat,
                'checks': {'parent_and_donor_source_hashes_match_freeze': False},
                'refused_snapshot_injection': True}
    state, cfg, env, tape = load_inputs(job)
    parent = load_module(V5_CANDIDATE, f'roman_validate_v5_seat{seat}')
    donor = load_module(DONOR, f'roman_validate_donor_seat{seat}')
    layer = load_module(ADAPTER, f'roman_validate_layer_seat{seat}')
    provenance_checks = {
        'adapter_source_hash_matches_freeze': sha(ADAPTER) == frozen_adapter_sha256,
        'snapshot_seat_matches_job': snapshot.get('candidate_seat') == seat,
        'snapshot_fixture_matches_job': snapshot.get('fixture_id') == TARGET_ID,
        'snapshot_replay_hash_matches_job': snapshot.get('source_replay_sha256') == job['fixture']['source_replay_sha256'],
        'snapshot_tape_file_hash_matches_job': snapshot.get('opponent_tape_file_sha256') == job['opponent_tape_file_sha256'],
        'snapshot_tape_payload_hash_matches_job': snapshot.get('opponent_tape_payload_sha256') == job['opponent_tape_payload_sha256'],
        'snapshot_adapter_step_is_one': snapshot.get('adapter_step') == 1,
        'snapshot_adapter_action_hash_matches_contract': snapshot.get('adapter_action_sha256') == layer.ADAPTER_STEP1_ACTION_SHA256,
        'snapshot_opponent_action_tape_hash_matches_contract': snapshot.get('opponent_action_tape_sha256') == layer.MATCHED_OPP_ACTION_TAPE_SHA256,
        'snapshot_opponent_action_index_is_one': snapshot.get('opponent_action_index') == 1,
        'snapshot_opponent_action_hash_matches_contract': snapshot.get('opponent_action_sha256') == layer.MATCHED_OPP_STEP1_ACTION_SHA256,
    }
    if not all(provenance_checks.values()):
        return {'candidate_seat': seat, 'checks': provenance_checks,
                'refused_snapshot_injection': True}
    expected = deepcopy(snapshot)
    adapted = layer.make_agent(parent.agent, donor._donor_action, expected)

    obs0 = obs_copy(state, seat)
    action0 = adapted(obs0, cfg)
    apply_transition(state, env, seat, action0, tape[0], 0)
    obs1 = obs_copy(state, seat)
    action1 = adapted(obs1, cfg)
    apply_transition(state, env, seat, action1, tape[1], 1)
    obs2 = obs_copy(state, seat)

    raw_expected = donor._DONOR_ROUTES[donor._DONOR_DEFAULT][2]
    mapped_expected = layer.remap_donor_hands(raw_expected, len(obs2['farms'][seat]['hands']))
    public_guard = layer._expected_step2_public_state(obs2, expected)
    own_guard = layer._expected_step2_merge_state(obs2)
    predicted_farm, predicted_private = expected_own_state_after_hire(obs1, seat)
    own_matches_prediction = (
        obs2['farms'][seat] == predicted_farm
        and obs2['private'] == predicted_private
    )
    own_matches_discovery = (
        obs2['farms'][seat] == snapshot['own_farm']
        and obs2['private'] == snapshot['own_private']
    )
    rival_matches_snapshot = (
        obs2['farms'][1 - seat] == snapshot['rival_farm']
        and obs2['market'] == snapshot['market']
    )
    pre_action_checks = {
        **provenance_checks,
        'step0_action_matches_v5': action0 == discovered['v5_step0'],
        'step1_observation_matches_v5': comparable_observation(obs1) == discovered['adapter_observation1'],
        'step2_observation_hash_matches_discovery': digest_json(comparable_observation(obs2)) == snapshot.get('observation2_sha256'),
        'step1_hire_action': action1 == layer._fifth_hire_action(obs1),
        'step2_own_merge_guard': bool(own_guard),
        'step2_public_rival_market_guard': bool(public_guard),
        'step2_complete_own_state_matches_prediction': bool(own_matches_prediction),
        'step2_own_state_matches_discovery': bool(own_matches_discovery),
        'step2_rival_market_matches_snapshot': bool(rival_matches_snapshot),
        'donor_remap_shape_valid_before_call': mapped_expected is not None,
    }
    if not all(pre_action_checks.values()):
        checks = {
            **pre_action_checks,
            'donor_action_called': False,
            'worker_remap_matches_raw_donor_action': False,
            'action2_not_all_pass': False,
            'action2_transition_applied': False,
            'two_cow_pickups_successful': False,
            'both_states_active_after_action2': False,
        }
        return {
            'candidate_seat': seat,
            'checks': checks,
            'refused_donor_action': True,
            'observation2_own_farm': deepcopy(obs2['farms'][seat]),
            'observation2_own_private': deepcopy(obs2['private']),
            'observation2_rival_farm': deepcopy(obs2['farms'][1 - seat]),
            'observation2_market': deepcopy(obs2['market']),
            'statuses_at_step2': [item.status for item in state],
        }

    action2 = adapted(obs2, cfg)
    action2_matches = action2 == mapped_expected
    action2_not_pass = action2 != {'farmer': ['PASS'],
                                   'hands': [['PASS']] * len(obs2['farms'][seat]['hands']),
                                   'market': []}
    action2_applied = action2_matches and action2_not_pass
    if action2_applied:
        apply_transition(state, env, seat, action2, tape[2], 2)
        obs3 = obs_copy(state, seat)
        inventory_cows = [int(item.get('COW', 0)) for item in obs3['private']['inventories']]
        cow_units = sum(inventory_cows)
        cow_pickup_hands = [index - 1 for index, quantity in enumerate(inventory_cows)
                            if index > 0 and quantity > 0]
        cows_ok = cow_units == 2 and cow_pickup_hands == [3, 4]
        active_after = all(item.status == 'ACTIVE' for item in state)
    else:
        obs3 = None
        inventory_cows = []
        cow_pickup_hands = []
        cows_ok = False
        active_after = False
    checks = {
        **pre_action_checks,
        'donor_action_called': True,
        'worker_remap_matches_raw_donor_action': action2_matches,
        'action2_not_all_pass': action2_not_pass,
        'action2_transition_applied': action2_applied,
        'two_cow_pickups_successful': cows_ok,
        'both_states_active_after_action2': active_after,
    }
    return {
        'candidate_seat': seat,
        'checks': checks,
        'step2_action': action2,
        'raw_donor_action2': raw_expected,
        'expected_mapped_donor_action2': mapped_expected,
        'observation2_own_farm': deepcopy(obs2['farms'][seat]),
        'observation2_rival_farm': deepcopy(obs2['farms'][1 - seat]),
        'observation2_market': deepcopy(obs2['market']),
        'observation3_own_farm': deepcopy(obs3['farms'][seat]) if obs3 else None,
        'observation3_own_private': deepcopy(obs3['private']) if obs3 else None,
        'cow_inventory_by_private_slot': inventory_cows,
        'cow_pickup_hand_indices': cow_pickup_hands,
        'statuses_after_step2': [item.status for item in state],
    }


def run():
    if any(path.exists() for path in OUTPUTS):
        raise FileExistsError('one-shot probe refuses existing or partial outputs')
    sys.path.insert(0, str(ROOT))
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    with exclusive_run(SHARED_LOCK):
        with exclusive_run(OWN_LOCK):
            manifest = verify()
            frozen_adapter_sha256 = manifest['bindings'][str(ADAPTER.resolve())]
            started = datetime.now(timezone.utc).isoformat()
            write_once(RUN_MANIFEST, {
                'started_at_utc': started,
                'freeze_manifest_sha256': sha(MANIFEST),
                'parent_candidate_sha256': V5_SHA,
                'adapter_sha256': sha(ADAPTER),
                'full_games': 0,
                'resume_allowed': False,
                'shared_lock_path': str(SHARED_LOCK),
            })
            rows = []
            baselines = {}
            with PROGRESS.open('x', encoding='utf-8', newline='\n') as stream:
                for job in manifest['jobs']:
                    try:
                        baseline = run_v5_prefix(job, 'base')
                        baselines[int(job['candidate_seat'])] = baseline
                        baseline_passed = baseline['opening_matches_source'] and all(
                            status == 'ACTIVE' for status in baseline['status'])
                        baseline_row = {
                            'phase': 'baseline',
                            'fixture_id': TARGET_ID,
                            'candidate_seat': int(job['candidate_seat']),
                            'baseline_source_checks': baseline['source_checks'],
                            'baseline_step0_action': baseline['actions'][0],
                            'baseline_step1_action': baseline['actions'][1],
                            'baseline_observation1': comparable_observation(baseline['observations'][1]),
                            'baseline_observation2': comparable_observation(baseline['observations'][2]),
                            'status': baseline['status'],
                            'passed': baseline_passed,
                        }
                        stream.write(json.dumps(baseline_row, ensure_ascii=True, separators=(',', ':')) + '\n')
                        stream.flush()
                        print(json.dumps({'phase': 'baseline',
                                          'fixture_id': TARGET_ID,
                                          'candidate_seat': int(job['candidate_seat']),
                                          'passed': baseline_passed,
                                          'failed_checks': [key for key, value in baseline['source_checks'].items() if not value]},
                                         ensure_ascii=True), flush=True)
                    except Exception as exc:
                        baselines[int(job['candidate_seat'])] = None
                        baseline_row = {'phase': 'baseline',
                                        'fixture_id': TARGET_ID,
                                        'candidate_seat': int(job['candidate_seat']),
                                        'passed': False,
                                        'error': f'{type(exc).__name__}: {exc}'}
                        stream.write(json.dumps(baseline_row, ensure_ascii=True, separators=(',', ':')) + '\n')
                        stream.flush()
                        print(json.dumps(baseline_row, ensure_ascii=True), flush=True)

                baseline_gate = (
                    len(baselines) == 2
                    and all(baselines.get(seat) is not None for seat in (0, 1))
                    and all(baselines[seat]['opening_matches_source']
                            and all(status == 'ACTIVE' for status in baselines[seat]['status'])
                            for seat in (0, 1))
                )
                discoveries = {}
                if baseline_gate:
                    for job in manifest['jobs']:
                        seat = int(job['candidate_seat'])
                        try:
                            discovery = discover_adapter_snapshot(
                                job, frozen_adapter_sha256, baselines[seat])
                            discovery['checks']['both_v5_source_prefixes_match'] = True
                            discovery['checks']['historical_v5_baseline_status_active'] = all(
                                status == 'ACTIVE' for status in baselines[seat]['status'])
                            discoveries[seat] = discovery
                            event = {
                                'phase': 'discovery',
                                'fixture_id': TARGET_ID,
                                'candidate_seat': seat,
                                'passed': all(discovery['checks'].values()),
                                'failed_checks': [key for key, value in discovery['checks'].items()
                                                  if not value],
                            }
                        except Exception as exc:
                            discoveries[seat] = {
                                'error': f'{type(exc).__name__}: {exc}',
                                'checks': {},
                            }
                            event = {'phase': 'discovery',
                                     'fixture_id': TARGET_ID,
                                     'candidate_seat': seat,
                                     'passed': False,
                                     'error': discoveries[seat]['error']}
                        stream.write(json.dumps(event, ensure_ascii=True, separators=(',', ':')) + '\n')
                        stream.flush()
                        print(json.dumps(event, ensure_ascii=True), flush=True)

                discovery_gate = (
                    baseline_gate
                    and len(discoveries) == 2
                    and all(seat in discoveries
                            and 'error' not in discoveries[seat]
                            and all(discoveries[seat]['checks'].values())
                            and discoveries[seat].get('snapshot') is not None
                            for seat in (0, 1))
                )
                for job in manifest['jobs']:
                    seat = int(job['candidate_seat'])
                    baseline = baselines.get(seat)
                    discovery = discoveries.get(seat)
                    if not baseline_gate:
                        row = {
                            'phase': 'result',
                            'fixture_id': TARGET_ID,
                            'candidate_seat': seat,
                            'baseline_source_checks': baseline['source_checks'] if baseline else None,
                            'checks': {'both_v5_source_prefixes_match': False},
                            'adapter_discovery_skipped': True,
                            'skip_reason': 'at least one seat failed the exact historical V5 source-prefix gate',
                            'passed': False,
                        }
                    elif not discovery_gate:
                        row = {
                            'phase': 'result',
                            'fixture_id': TARGET_ID,
                            'candidate_seat': seat,
                            'baseline_source_checks': baseline['source_checks'],
                            'discovery_checks': discovery.get('checks') if discovery else None,
                            'snapshot': discovery.get('snapshot') if discovery else None,
                            'adapter_validation_skipped': True,
                            'checks': {'both_seat_discovery_gates_passed': False},
                            'skip_reason': 'at least one seat failed discovery; no donor validation ran',
                            'error': discovery.get('error') if discovery else None,
                            'passed': False,
                        }
                    else:
                        try:
                            validation = validate_adapter_snapshot(
                                job, discovery['snapshot'], discovery,
                                frozen_adapter_sha256)
                            checks = dict(discovery['checks'])
                            checks.update({'snapshot_' + key: value
                                           for key, value in validation['checks'].items()})
                            row = {
                                'phase': 'result',
                                'fixture_id': TARGET_ID,
                                'candidate_seat': seat,
                                'baseline_source_checks': baseline['source_checks'],
                                'baseline_step0_action': baseline['actions'][0],
                                'baseline_step1_action': baseline['actions'][1],
                                'baseline_observation1': comparable_observation(baseline['observations'][1]),
                                'baseline_observation2': comparable_observation(baseline['observations'][2]),
                                'discovery_checks': discovery['checks'],
                                'snapshot': discovery['snapshot'],
                                'validation': validation,
                                'checks': checks,
                                'passed': bool(discovery_gate and all(checks.values())),
                            }
                        except Exception as exc:
                            row = {'phase': 'result',
                                   'fixture_id': TARGET_ID,
                                   'candidate_seat': seat,
                                   'passed': False,
                                   'error': f'{type(exc).__name__}: {exc}'}
                    rows.append(row)
                    stream.write(json.dumps(row, ensure_ascii=True, separators=(',', ':')) + '\n')
                    stream.flush()
                    print(json.dumps({'phase': 'result',
                                      'fixture_id': TARGET_ID,
                                      'candidate_seat': seat,
                                      'passed': row['passed'],
                                      'failed_checks': [key for key, value in
                                          row.get('checks', {}).items() if not value],
                                      'adapter_discovery_skipped': row.get('adapter_discovery_skipped', False),
                                      'error': row.get('error')}, ensure_ascii=True), flush=True)
            snapshots = {
                'schema': 'roman-shared166-v5-seat-bound-step2-public-snapshots-v1',
                'complete': len(rows) == 2 and all(row.get('passed') for row in rows),
                'adapter_discovery_skipped': not baseline_gate,
                'two_seat_discovery_gate_passed': discovery_gate,
                'parent_candidate_sha256': V5_SHA,
                'adapter_sha256': sha(ADAPTER),
                'snapshots': [row['snapshot'] for row in rows if row.get('snapshot') is not None],
            }
            write_once(SNAPSHOTS, snapshots)
            receipt = {
                'schema': 'roman-shared166-v5-two-seat-prefix-outcome-v1',
                'complete': len(rows) == 2,
                'diagnostic_only': True,
                'fixed_opponent_tape': True,
                'full_games': 0,
                'reactive_validation': False,
                'promotion': False,
                'parent_candidate_sha256': V5_SHA,
                'adapter_sha256': sha(ADAPTER),
                'donor_candidate_sha256': DONOR_SHA,
                'freeze_manifest_sha256': sha(MANIFEST),
                'snapshot_file_sha256': sha(SNAPSHOTS),
                'seat_count': len(rows),
                'v5_source_prefix_gate_passed_both_seats': baseline_gate,
                'two_seat_discovery_gate_passed': discovery_gate,
                'adapter_discovery_skipped': not baseline_gate,
                'passed_seats': sum(bool(row['passed']) for row in rows),
                'rows': rows,
                'passed': len(rows) == 2 and all(row['passed'] for row in rows),
                'completed_at_utc': datetime.now(timezone.utc).isoformat(),
            }
            write_once(RECEIPT, receipt)
            print(json.dumps({key: value for key, value in receipt.items() if key != 'rows'},
                             ensure_ascii=True, indent=2), flush=True)
            return receipt


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    if command == 'freeze':
        freeze()
    elif command == 'verify':
        manifest = verify()
        print(json.dumps({'verified': True, 'binding_count': manifest['binding_count'],
                          'job_count': manifest['job_count'],
                          'parent_candidate_sha256': V5_SHA}, indent=2))
    elif command == 'run':
        result = run()
        if not result['passed']:
            raise SystemExit(1)
    else:
        raise SystemExit('usage: prefix_probe.py freeze|verify|run')


if __name__ == '__main__':
    main()
