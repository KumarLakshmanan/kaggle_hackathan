"""Build and verify the frozen a44 pasture-guard study without games.

This file's build and verify-static phases only read frozen inputs, import the
candidate to inspect its static tables, and write study artifacts in HERE.
Native-prefix and full-game execution remain separate future phases.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import ast
import gzip
import hashlib
import importlib.util
import json
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

SOURCE = ROOT / 'diagnostics/upload_adaptive_donor_20260928_a44c8c2c/main.py'
TARGET_POOL = ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full_pool.json'
TARGET_RESULTS = ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full_results.json'
TARGET_HELPER = ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full.py'
PUBLIC_POOL = ROOT / 'diagnostics/adaptive_third_pair_repair_20260928/pool.json'
PUBLIC_DISCOVERY = ROOT / 'diagnostics/adaptive_third_pair_repair_20260928/discovery.json'
PUBLIC_HELPER = ROOT / 'diagnostics/adaptive_third_pair_repair_20260928/study.py'
PUBLIC_OPENING_AUDIT = ROOT / 'diagnostics/adaptive_third_pair_repair_20260928/STEP1_OPENING_AUDIT.json'
COMPONENT_DIR = ROOT / 'diagnostics/production_leaf_selector_20260928'
COMPONENT_CANDIDATE = COMPONENT_DIR / 'candidates/production_goose_95e5bd8f5d_113332529.py'
COMPONENT_RECEIPT = COMPONENT_DIR / 'conditional.json'
COMPONENT_LAYER = COMPONENT_DIR / 'layer.py'
SOURCE32 = ROOT / 'main_candidate_animal_liquidity_20260928_32e299fe.py'
FAST_GAME = ROOT / 'diagnostics/stream_replay_io_20260928/fast_game_cached.py'
CACHED_INPUT = ROOT / 'diagnostics/stream_replay_io_20260928/cached_input.py'
INITIAL_CACHE = ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json'
NATIVE_CORE = ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py'
NATIVE_CHECK = ROOT / 'diagnostics/physical_route_rollout_20260928/check.py'
RUN_LOCK = ROOT / 'diagnostics/local_target_20260928/run_lock.py'

CANDIDATE = HERE / 'candidate_pasture_guard_source_leaf.py'
FEATURES = HERE / 'feature_rows.json'
POOL = HERE / 'pool.json'
STATIC_RECEIPT = HERE / 'static_preflight.json'
DONOR_IDS = (
    'live-114232208',
    'live-114235177',
    'live-114279308',
    'top20-03-Boey-114266440',
    'top20-06-Majkel1337-114263239',
)
THIRD_ID = 'live-114274897'
CHRIS_ID = 'public-win-114193811'
LEAF_KEY = 'BRUNCH_SPOT|M8+|C>S|G+'
LEAF_ROUTE = 113332529
A44_SHA = 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
SOURCE32_SHA = '32e299fe047a79290d5025b4e2be455ae13d948020beae2d77cb44a7c17dc31e'
COMPONENT_SHA = '0eb77448c82e08b114749076c7589755522fdb890537dc974e8f5c248505106d'
COMPONENT_RECEIPT_SHA = '63bc163b401ec5704f264b200d578aa24dd0bd5b93d8bd005081b4f0ab2a54f3'
COMPONENT_LAYER_SHA = '76805b94493a482d3be1bd8906335a1dc4927e840b4cb00544738afdb8f8d289'
TARGET_POOL_SHA = '4d0a74d3c897891d182d80948a1d8b79d761855147098ad4a6b7d763e068af5d'
TARGET_RESULTS_SHA = 'ea74d2be3b852acf83885a35ce55296b391eff8b33b1bd5f556fa6242fa1d732'
PUBLIC_POOL_SHA = '41ead4cd5c6f9718b508e59262f8b8874771d13aa1084366acfb98b1c4e276ba'
PUBLIC_DISCOVERY_SHA = '3995f982e12686c3bcf35e31e352cfe36637e2e2c263fb6b9c6b9095bbbac6cb'
PUBLIC_HELPER_SHA = '954d15e27d25df9d1a18e63f3a5120fa2faf235464c8d4692daf22f75c37eecf'
PUBLIC_OPENING_AUDIT_SHA = '541837f2ab96aaa7517c9cd297ed00c80db2c3945df5d35d1c34ae83da359a40'
FAST_GAME_SHA = 'a57d12659af613512a61ac02aaa43d4c5ae4f4d8f2c5c02d3ed4ac6eafa2a38e'
CACHED_INPUT_SHA = 'e2aaefda623775c9c7d56304271c827ecd6e56cc109e5c6d8b35aeb458268aa1'
INITIAL_CACHE_SHA = 'f544b134e2ad51160e4d6ad7719b9f41ad6cc850a1a51162249ede1cba279968'
NATIVE_CORE_SHA = '5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795'
NATIVE_CHECK_SHA = 'f51b49dd2c627337136365603e4d0923c9f3e77f28bc8c77d08f608cba48e4a6'

OLD_STEP1 = (
    b"        hands = len(observation['farms'][1-player]['hands'])\n"
    b"        branch = 'shared151' if hands>=5 else ('shared150' if _BRIDGE_VARIANT=='five_or_zero' and hands==0 else 'source')\n"
    b"        _BRIDGE_STATS.update(bridge_requested=branch,bridge_rival_hands=hands)"
)
NEW_STEP1 = (
    b"        hands = len(observation['farms'][1-player]['hands'])\n"
    b"        rival_pastures = _guard_rival_pastures(observation)\n"
    b"        branch = 'shared151' if hands>=5 and rival_pastures == 0 else ('shared150' if _BRIDGE_VARIANT=='five_or_zero' and hands==0 else 'source')\n"
    b"        _BRIDGE_STATS.update(bridge_requested=branch,bridge_rival_hands=hands,bridge_rival_pastures=rival_pastures)"
)


def sha(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path: Path | str):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def abs_key(path: Path | str) -> str:
    return str(Path(path).resolve())


def expect_hash(path: Path, digest: str) -> None:
    actual = sha(path)
    if actual != digest:
        raise AssertionError(f'hash mismatch for {path}: {actual} != {digest}')


def write_new(path: Path, payload) -> None:
    raw = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(raw)


def write_bytes_new(path: Path, raw: bytes) -> None:
    with path.open('xb') as stream:
        stream.write(raw)


def verify_upstream_bindings(bindings: dict[str, str]) -> None:
    for path, digest in bindings.items():
        expect_hash(Path(path), digest)


def expected_static_hashes() -> dict[Path, str]:
    return {
        SOURCE: A44_SHA,
        TARGET_POOL: TARGET_POOL_SHA,
        TARGET_RESULTS: TARGET_RESULTS_SHA,
        PUBLIC_POOL: PUBLIC_POOL_SHA,
        PUBLIC_DISCOVERY: PUBLIC_DISCOVERY_SHA,
        PUBLIC_HELPER: PUBLIC_HELPER_SHA,
        PUBLIC_OPENING_AUDIT: PUBLIC_OPENING_AUDIT_SHA,
        COMPONENT_CANDIDATE: COMPONENT_SHA,
        COMPONENT_RECEIPT: COMPONENT_RECEIPT_SHA,
        COMPONENT_LAYER: COMPONENT_LAYER_SHA,
        FAST_GAME: FAST_GAME_SHA,
        CACHED_INPUT: CACHED_INPUT_SHA,
        INITIAL_CACHE: INITIAL_CACHE_SHA,
        NATIVE_CORE: NATIVE_CORE_SHA,
        NATIVE_CHECK: NATIVE_CHECK_SHA,
        SOURCE32: SOURCE32_SHA,
    }


def construct_candidate() -> bytes:
    source = SOURCE.read_bytes()
    if source.count(OLD_STEP1) != 1:
        raise AssertionError('expected exactly one frozen donor selector block')
    patched = source.replace(OLD_STEP1, NEW_STEP1, 1)
    layer = (HERE / 'layer.py').read_bytes()
    if not layer.startswith(b'"""Source-only previously frozen Brunch goose leaf'):
        raise AssertionError('unexpected layer.py content')
    candidate = patched + b'\n' + layer
    if candidate.count(NEW_STEP1) != 1 or candidate.count(OLD_STEP1) != 0:
        raise AssertionError('selector patch did not land exactly once')
    # Reversing the one source edit and removing the exact appended layer must
    # recover the original a44 bytes byte-for-byte.
    base = candidate[:-len(layer)]
    if not base.endswith(b'\n'):
        raise AssertionError('candidate/layer separator is missing')
    base = base[:-1]
    if base.count(NEW_STEP1) != 1 or base.replace(NEW_STEP1, OLD_STEP1, 1) != source:
        raise AssertionError('candidate contains an unplanned source edit')
    return candidate


def import_bytes(name: str, path: Path, raw: bytes):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def import_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def route_hire_signature(route: list) -> dict:
    hires = []
    all_market_commands = 0
    for step, record in enumerate(route):
        commands = record.get('market', [])
        all_market_commands += len(commands)
        if any(command and command[0] == 'HIRE' for command in commands):
            hires.append(step)
    return {'steps': len(route), 'market_commands': all_market_commands,
            'hire_turns': hires, 'hire_turn_count': len(hires)}


def donor_namespace_snapshot(namespace: dict) -> dict:
    # repr digests retain the object graph shape/content without deepcopying
    # imported modules embedded in the isolated namespace.
    return {
        key: {
            'object_id': id(value),
            'type': type(value).__name__,
            'repr_sha256': hashlib.sha256(repr(value).encode('utf-8')).hexdigest(),
        }
        for key, value in namespace.items() if key != '__builtins__'
    }


def check_static_candidate(candidate_module, candidate_source: str) -> dict:
    # The runtime selectors may read only public rival hands/tiles and the
    # first unlocked shop. These exact helper definitions are the sole
    # appended selector functions; fixture IDs remain harness provenance.
    source = candidate_source
    tree = ast.parse(source)
    funcs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    required = {'_guard_rival_pastures', '_guard_leaf_key', '_guard_leaf_reset',
                '_guard_leaf_commit', '_guard_source_agent'}
    if not required.issubset(funcs):
        raise AssertionError(f'missing wrapper functions: {sorted(required - funcs.keys())}')
    selector_text = '\n'.join(ast.get_source_segment(source, funcs[n]) for n in
                               ('_guard_rival_pastures', '_guard_leaf_key'))
    forbidden = ('fixture_id', 'episode_id', 'seed', 'money', 'cash', 'private',
                 'submission_id', 'team', 'coordinate', 'farm_id')
    if any(token in selector_text.lower() for token in forbidden):
        raise AssertionError('runtime feature selector includes an identity/private/cash/seed field')
    if "hands>=5 and rival_pastures == 0" not in source:
        raise AssertionError('guard predicate not present in candidate source')

    original_map = deepcopy(candidate_module._DATA['route_map'])
    donor_namespace = candidate_module._BRIDGE_DONORS['shared151']
    donor_before = donor_namespace_snapshot(donor_namespace)
    base_map = deepcopy(candidate_module._GUARD_LEAF_BASE_MAP)
    if original_map != base_map:
        raise AssertionError('source route map base was not captured exactly')
    candidate_module._guard_leaf_commit()
    brunch_keys = [key for key in original_map if key.split('|')[0] == 'BRUNCH_SPOT']
    if not brunch_keys:
        raise AssertionError('source route map has no Brunch descendants')
    if any(candidate_module._DATA['route_map'][key] != LEAF_ROUTE for key in brunch_keys):
        raise AssertionError('Brunch route-map descendants are not committed to the frozen leaf')
    if any(candidate_module._DATA['route_map'][key] != original_map[key]
           for key in original_map if key.split('|')[0] != 'BRUNCH_SPOT'):
        raise AssertionError('leaf commit changed a non-Brunch route-map branch')
    if donor_namespace_snapshot(candidate_module._BRIDGE_DONORS['shared151']) != donor_before:
        raise AssertionError('leaf commit changed the isolated shared151 donor namespace')

    component = import_file('pasture_component_goose', COMPONENT_CANDIDATE)
    candidate_route = candidate_module._DATA['routes'].get(str(LEAF_ROUTE))
    component_route = component._DATA['routes'].get(str(LEAF_ROUTE))
    if candidate_route is None or candidate_route != component_route:
        raise AssertionError('frozen source route does not match the component schedule')
    signature = route_hire_signature(candidate_route)
    if signature['steps'] != 719 or signature['hire_turn_count'] == 0:
        raise AssertionError('leaf route schedule or hire schedule is incomplete')

    candidate_module._GUARD_LEAF_STATS.update(guard_leaf_key72='sample',
                                               guard_leaf_route=str(LEAF_ROUTE),
                                               guard_leaf_turns=55)
    candidate_module._BRIDGE_STATS['bridge_rival_pastures'] = 9
    candidate_module._guard_leaf_reset()
    if candidate_module._DATA['route_map'] != original_map:
        raise AssertionError('step-0 reset did not restore the complete base route map')
    if candidate_module._GUARD_LEAF_STATS != {
            'guard_leaf_key72': '', 'guard_leaf_route': '', 'guard_leaf_turns': 0}:
        raise AssertionError('step-0 reset did not clear leaf telemetry')
    if candidate_module._BRIDGE_STATS.get('bridge_rival_pastures') != 0:
        raise AssertionError('step-0 reset did not clear public pasture telemetry')
    if donor_namespace_snapshot(candidate_module._BRIDGE_DONORS['shared151']) != donor_before:
        raise AssertionError('reset changed the isolated shared151 donor namespace')

    fake = {
        'player': 0,
        'farms': [
            {'hands': [], 'tiles': [[None, None], [None, None]]},
            {'hands': [None] * 5,
             'tiles': [[{'kind': 'PASTURE'}, None], [None, {'kind': 'PASTURE'}]]},
        ],
    }
    if candidate_module._guard_rival_pastures(fake) != 2:
        raise AssertionError('pasture counter failed across public rival tiles')
    fake['player'] = 1
    if candidate_module._guard_rival_pastures(fake) != 0:
        raise AssertionError('pasture counter did not follow the relative player seat')
    return {
        'passed': True,
        'patch_occurrences': 1,
        'route_map_keys': len(original_map),
        'brunch_route_map_descendants': len(brunch_keys),
        'leaf_route_id': LEAF_ROUTE,
        'route_hire_signature': signature,
        'donor_namespace_unchanged': True,
        'route_map_reset_exact': True,
        'pasture_counter_public_relative': True,
        'selector_identity_private_seed_cash_free': True,
    }


def public_features(obs1: dict, obs72: dict) -> dict:
    player = int(obs1['player'])
    rival = obs1['farms'][1 - player]
    hands = len(rival['hands'])
    pastures = sum(isinstance(tile, dict) and tile.get('kind') == 'PASTURE'
                   for row in rival['tiles'] for tile in row)
    rival72 = obs72['farms'][1 - int(obs72['player'])]
    melon = cow = sheep = goose = 0
    for row in rival72['tiles']:
        for tile in row:
            if isinstance(tile, dict):
                melon += tile.get('crop') == 'MELON'
                cow += tile.get('animal') == 'COW'
                sheep += tile.get('animal') == 'SHEEP'
                goose += tile.get('animal') == 'GOOSE'
    shops = obs72['town']['unlocked_shops']
    if not shops:
        raise AssertionError('observation72 has no revealed shop for the frozen leaf key')
    first_shop = shops[0]
    comparison = 'C<S' if cow < sheep else 'C>S' if cow > sheep else 'C=S'
    key = (first_shop + '|' + ('M8+' if melon >= 8 else 'M<8') + '|' + comparison
           + ('|G+' if goose > 0 else '|G0'))
    requested = 'shared151' if hands >= 5 else 'source'
    guarded = 'shared151' if hands >= 5 and pastures == 0 else 'source'
    return {
        'selector_features': {
            'obs1_rival_hands': hands,
            'obs1_rival_pasture_count': pastures,
            'obs72_first_revealed_shop': first_shop,
            'obs72_rival_melon_plots': melon,
            'obs72_rival_cows': cow,
            'obs72_rival_sheep': sheep,
            'obs72_rival_geese': goose,
            'obs72_leaf_key': key,
            'obs72_leaf_matches': key == LEAF_KEY,
        },
        'source_control': {
            'a44_requested_branch_from_hands': requested,
            'a44_observed_branch': None,
            'guarded_branch_from_public_features': guarded,
            'branch_changes': guarded != requested,
            'leaf_eligible_after_guard': guarded == 'source' and key == LEAF_KEY,
        },
    }


def load_features(target_pool: dict, target_results: dict,
                  public_pool: dict, public_discovery: dict) -> dict:
    if not target_results['complete'] or not target_results['clean'] or not target_results['passed']:
        raise AssertionError('a44 target50 controls are not a clean complete receipt')
    if not public_discovery['complete'] or not public_discovery['passed']:
        raise AssertionError('a44 public54 discovery is not a clean complete receipt')
    target_fixtures = {row['fixture_id']: row for row in target_pool['fixtures']}
    public_fixtures = {row['fixture_id']: row for row in public_pool['public_fixtures']}
    if len(target_fixtures) != 50 or len(public_fixtures) != 54:
        raise AssertionError('expected frozen target50 and public54 fixtures')
    if set(target_fixtures) & set(public_fixtures):
        raise AssertionError('target50 and public54 fixture IDs unexpectedly overlap')

    rows = []
    for panel, source_rows, fixture_map in (
            ('target50', target_results['games'], target_fixtures),
            ('public54', public_discovery['rows'], public_fixtures)):
        for row in source_rows:
            if row.get('candidate_sha256') != A44_SHA:
                raise AssertionError(f'{panel} row is not exact a44: {row.get("fixture_id")}')
            fixture = fixture_map[row['fixture_id']]
            trace = Path(row['trace_path'])
            if sha(trace) != row['trace_sha256']:
                raise AssertionError(f'trace hash changed: {trace}')
            selected = {}
            with gzip.open(trace, 'rt', encoding='utf-8') as stream:
                for line in stream:
                    record = json.loads(line)
                    step = int(record['observation']['step'])
                    if step in (1, 72):
                        selected[step] = record['observation']
            if set(selected) != {1, 72}:
                raise AssertionError(f'trace missing observation1/72: {trace}')
            features = public_features(selected[1], selected[72])
            if panel == 'target50':
                branch = row['candidate_telemetry']['bridge_selected']
                requested = row['candidate_telemetry']['bridge_requested']
            else:
                branch = row['branch']
                requested = branch
            if features['source_control']['a44_requested_branch_from_hands'] != requested:
                raise AssertionError(f'hands control branch mismatch for {row["fixture_id"]}/{row["candidate_seat"]}')
            if branch != features['source_control']['a44_requested_branch_from_hands']:
                raise AssertionError(f'baseline branch does not match a44 hands rule: {row["fixture_id"]}')
            features['source_control']['a44_observed_branch'] = branch
            rows.append({
                'provenance': {
                    'panel': panel,
                    'fixture_id': row['fixture_id'],
                    'team': fixture.get('team'),
                    'episode_id': fixture.get('episode_id'),
                    'candidate_seat': int(row['candidate_seat']),
                    'trace_path': str(trace.resolve()),
                    'trace_sha256': row['trace_sha256'],
                },
                **features,
            })
    if len(rows) != 208 or len({(r['provenance']['fixture_id'], r['provenance']['candidate_seat'])
                               for r in rows}) != 208:
        raise AssertionError('feature receipt is not 208 unique fixture/seat rows')
    return {'schema': 'pasture-guard-public-features-v1', 'row_count': 208, 'rows': rows}


def compact_control(row: dict) -> dict:
    fields = ('fixture_id', 'candidate_seat', 'candidate_sha256', 'candidate_reward',
              'opponent_reward', 'margin', 'result', 'candidate_status',
              'opponent_status', 'frames', 'trace_path', 'trace_sha256',
              'candidate_telemetry', 'candidate_errors', 'clean')
    return {key: row.get(key) for key in fields}


def fixture_inputs(target_pool: dict, public_pool: dict) -> dict[str, dict]:
    fixtures = {}
    for panel, source in (('target50', target_pool['fixtures']),
                          ('public54', public_pool['public_fixtures'])):
        for row in source:
            fixture = deepcopy(row)
            fixture['panel'] = panel
            for name in ('source_replay_path', 'source_replay_sha256',
                         'source_action_tape_path', 'source_opponent_action_sha256'):
                if not fixture.get(name):
                    raise AssertionError(f'{row["fixture_id"]} missing {name}')
            fixtures[row['fixture_id']] = fixture
    return fixtures


def build_pool(target_pool: dict, target_results: dict, public_pool: dict,
               public_discovery: dict, feature_payload: dict, candidate_digest: str,
               study_digest: str) -> dict:
    fixture_map = fixture_inputs(target_pool, public_pool)
    pilot_ids = list(DONOR_IDS) + [THIRD_ID, CHRIS_ID]
    if any(fid not in fixture_map for fid in pilot_ids):
        raise AssertionError('fixed seven-fixture pilot is not present in frozen inputs')
    target_control_by_key = {(r['fixture_id'], r['candidate_seat']): r
                             for r in target_results['games']}
    reused = []
    for fid in list(DONOR_IDS) + [THIRD_ID]:
        for seat in (0, 1):
            row = target_control_by_key[(fid, seat)]
            if row['candidate_sha256'] != A44_SHA or not row['clean']:
                raise AssertionError(f'non-a44/unclean reused control {fid}/{seat}')
            reused.append(compact_control(row))
    if len(reused) != 12 or len({(r['fixture_id'], r['candidate_seat']) for r in reused}) != 12:
        raise AssertionError('expected twelve unique reused exact-a44 full controls')
    if any(r['result'] != 'win' for r in reused if r['fixture_id'] in DONOR_IDS):
        raise AssertionError('one of the five frozen successful donor controls is not a win')

    candidate_jobs = [
        {'fixture_id': fid, 'candidate_seat': seat,
         'fixture': fixture_map[fid], 'candidate_path': str(CANDIDATE.resolve()),
         'candidate_sha256': candidate_digest,
         'output_trace_path': str((HERE / f'candidate_{fid}_seat{seat}.jsonl.gz').resolve())}
        for fid in pilot_ids for seat in (0, 1)
    ]
    fresh_controls = [
        {'fixture_id': CHRIS_ID, 'candidate_seat': seat,
         'fixture': fixture_map[CHRIS_ID], 'candidate_path': str(SOURCE.resolve()),
         'candidate_sha256': A44_SHA,
         'output_trace_path': str((HERE / f'fresh_a44_chris_seat{seat}.jsonl.gz').resolve()),
         'status': 'PENDING_FRESH_EXACT_A44_CONTROL'}
        for seat in (0, 1)
    ]
    prefix_jobs = [
        {'fixture_id': fid, 'candidate_seat': seat,
         'candidate_path': str(CANDIDATE.resolve()), 'candidate_sha256': candidate_digest,
         'source32_path': str(SOURCE32.resolve()), 'source32_sha256': SOURCE32_SHA}
        for fid in (THIRD_ID, CHRIS_ID) for seat in (0, 1)
    ]

    bindings: dict[str, str] = {}
    for upstream in (target_pool, public_pool):
        verify_upstream_bindings(upstream['bindings'])
        bindings.update(upstream['bindings'])
    # Bind every primary receipt itself; upstream pool bindings alone do not
    # include their own bytes or every post-discovery feature trace.
    direct = [SOURCE, TARGET_POOL, TARGET_RESULTS, TARGET_HELPER, PUBLIC_POOL,
              PUBLIC_DISCOVERY, PUBLIC_HELPER, PUBLIC_OPENING_AUDIT,
              COMPONENT_CANDIDATE, COMPONENT_RECEIPT, COMPONENT_LAYER,
              SOURCE32, FAST_GAME, CACHED_INPUT, INITIAL_CACHE,
              NATIVE_CORE, NATIVE_CHECK, RUN_LOCK,
              HERE / 'PLAN.md', HERE / 'REVIEW.md', HERE / 'STATIC_AUDIT.md',
              HERE / 'layer.py', Path(__file__)]
    for path in direct:
        bindings[abs_key(path)] = sha(path)
    bindings[abs_key(CANDIDATE)] = candidate_digest
    for row in feature_payload['rows']:
        bindings[row['provenance']['trace_path']] = row['provenance']['trace_sha256']
    # The replay manifest in the frozen compact cache carries compressed-file
    # hashes; fixture replay/action digests are decoded-payload hashes.
    cache = read_json(INITIAL_CACHE)
    cached_replays = {row['source_replay_path']: row for row in cache['replays']}
    for fixture in fixture_map.values():
        replay = cached_replays.get(fixture['source_replay_path'])
        if not replay or replay['source_replay_sha256'] != fixture['source_replay_sha256']:
            raise AssertionError(f'raw replay is not in the verified compact cache: {fixture["fixture_id"]}')
        replay_path = Path(fixture['source_replay_path']).resolve()
        if sha(replay_path) != replay['compressed_sha256']:
            raise AssertionError(f'compressed replay hash changed: {replay_path}')
        bindings[str(replay_path)] = replay['compressed_sha256']
        action_path = Path(fixture['source_action_tape_path']).resolve()
        raw_tape = gzip.decompress(action_path.read_bytes())
        tape = json.loads(raw_tape)['actions']
        action_hashes = [hashlib.sha256(json.dumps(tape, sort_keys=sort_keys,
                                  separators=(',', ':')).encode()).hexdigest()
                          for sort_keys in (False, True)]
        if fixture['source_opponent_action_sha256'] not in action_hashes:
            raise AssertionError(f'action tape content hash changed: {action_path}')
        bindings[str(action_path)] = sha(action_path)

    return {
        'schema': 'pasture-guard-source-leaf-pool-v1',
        'source': {'path': str(SOURCE.resolve()), 'sha256': A44_SHA},
        'candidate': {'path': str(CANDIDATE.resolve()), 'sha256': candidate_digest,
                      'build': 'exact one-block selector patch plus exact local layer.py'},
        'source32_prefix_comparator': {'path': str(SOURCE32.resolve()), 'sha256': SOURCE32_SHA},
        'selector_definition': {
            'step1': "shared151 iff public rival hands >= 5 and public rival PASTURE tile count == 0; otherwise source",
            'step72_source_only': LEAF_KEY + f' -> {LEAF_ROUTE}',
            'runtime_features': ['public rival hand count', 'public rival PASTURE tile count',
                                 'first revealed shop', 'public rival MELON/COW/SHEEP/GOOSE tile counts'],
            'runtime_exclusions': ['fixture/team/episode identity', 'private state', 'seed', 'cash', 'coordinates'],
        },
        'scope': {
            'target_fixtures': 50, 'public_fixtures': 54, 'bound_fixture_seat_rows': 208,
            'affected_fixture_ids': [THIRD_ID, CHRIS_ID],
            'donor_control_fixture_ids': list(DONOR_IDS),
            'candidate_fixture_ids': pilot_ids, 'candidate_games': 14,
            'fresh_exact_a44_control_games': 2,
            'identity_use': 'fixture IDs are harness provenance only; no identity enters selector_features',
        },
        'feature_rows': {'path': str(FEATURES.resolve()), 'sha256': sha_json(feature_payload),
                         'row_count': feature_payload['row_count']},
        'fixtures': [fixture_map[fid] for fid in sorted(fixture_map)],
        'candidate_jobs': candidate_jobs,
        'reused_exact_a44_controls': reused,
        'fresh_exact_a44_control_jobs': fresh_controls,
        'prefix_jobs': prefix_jobs,
        'source_receipts': {
            'a44_full_target_pool': {'path': str(TARGET_POOL.resolve()), 'sha256': TARGET_POOL_SHA},
            'a44_full_target_results': {'path': str(TARGET_RESULTS.resolve()), 'sha256': TARGET_RESULTS_SHA},
            'a44_public54_pool': {'path': str(PUBLIC_POOL.resolve()), 'sha256': PUBLIC_POOL_SHA},
            'a44_public54_discovery': {'path': str(PUBLIC_DISCOVERY.resolve()), 'sha256': PUBLIC_DISCOVERY_SHA},
            'goose_component_candidate': {'path': str(COMPONENT_CANDIDATE.resolve()), 'sha256': COMPONENT_SHA},
            'goose_component_receipt': {'path': str(COMPONENT_RECEIPT.resolve()), 'sha256': COMPONENT_RECEIPT_SHA},
        },
        'reused_control_count': len(reused),
        'bindings': dict(sorted(bindings.items())),
        'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
    }


def sha_json(payload) -> str:
    raw = (json.dumps(payload, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def static_preflight(candidate_bytes: bytes, candidate_digest: str,
                     features: dict, pool: dict) -> dict:
    candidate_module = import_bytes('pasture_guard_static_candidate', CANDIDATE, candidate_bytes)
    candidate_checks = check_static_candidate(candidate_module, candidate_bytes.decode('utf-8'))
    rows = features['rows']
    changed = [r for r in rows if r['source_control']['branch_changes']]
    affected = sorted({r['provenance']['fixture_id'] for r in changed})
    if len(affected) != 2 or set(affected) != {THIRD_ID, CHRIS_ID} or len(changed) != 4:
        raise AssertionError(f'pasture guard scope drifted: {affected}; {len(changed)} contexts')
    donor_rows = [r for r in rows if r['provenance']['fixture_id'] in DONOR_IDS]
    if len(donor_rows) != 10 or any(
            r['selector_features']['obs1_rival_hands'] < 5 or
            r['selector_features']['obs1_rival_pasture_count'] != 0 or
            r['source_control']['guarded_branch_from_public_features'] != 'shared151' or
            r['selector_features']['obs72_leaf_matches'] for r in donor_rows):
        raise AssertionError('five frozen donor controls do not remain zero-pasture/no-leaf contexts')
    third_rows = [r for r in rows if r['provenance']['fixture_id'] == THIRD_ID]
    if len(third_rows) != 2 or any(not r['selector_features']['obs72_leaf_matches'] for r in third_rows):
        raise AssertionError('both saved THIRD observations at72 must match the frozen Brunch leaf')
    if any(r['source_control']['leaf_eligible_after_guard'] for r in donor_rows):
        raise AssertionError('a donor-selected context would activate the source-only leaf')
    if len(pool['reused_exact_a44_controls']) != 12 or len(pool['candidate_jobs']) != 14:
        raise AssertionError('pilot jobs/control reuse counts are incomplete')
    if len(pool['fresh_exact_a44_control_jobs']) != 2:
        raise AssertionError('two fresh exact-a44 ChrisTu controls are not staged')
    if any(job['candidate_sha256'] != A44_SHA for job in pool['fresh_exact_a44_control_jobs']):
        raise AssertionError('fresh controls are not bound to exact a44')
    return {
        'schema': 'pasture-guard-static-preflight-v1',
        'complete': True,
        'passed': True,
        'candidate_sha256': candidate_digest,
        'pool_sha256': sha_json(pool),
        'feature_rows_sha256': sha_json(features),
        'bound_feature_rows': len(rows),
        'fixture_count': len({r['provenance']['fixture_id'] for r in rows}),
        'source_branch_counts': dict(Counter(r['source_control']['a44_observed_branch'] for r in rows)),
        'guard_branch_counts': dict(Counter(r['source_control']['guarded_branch_from_public_features'] for r in rows)),
        'guard_changed_contexts': [
            {'fixture_id': r['provenance']['fixture_id'],
             'candidate_seat': r['provenance']['candidate_seat'],
             'hands': r['selector_features']['obs1_rival_hands'],
             'rival_pastures': r['selector_features']['obs1_rival_pasture_count']}
            for r in changed],
        'donor_control_contexts': 10,
        'donor_controls_all_zero_pasture_and_leaf_inactive': True,
        'third_observation72_leaf_feature_matches': 2,
        'candidate_static_checks': candidate_checks,
        'native_prefix': 'PENDING_FRESH_CIM_EXIT_CHECK',
        'outcome_games_started': False,
        'outcome_gate': 'BLOCKED until native prefix passes and parent confirms worker slot',
        'fresh_chris_a44_controls_staged': 2,
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
    }


def load_all_inputs():
    for path, digest in expected_static_hashes().items():
        expect_hash(path, digest)
    if sha(TARGET_HELPER) != '09773df031d0ceb310e8ba17e89036050c5cc8d35b2fa12d8662f9f9b76ccc47':
        raise AssertionError('a44 full-control builder hash changed')
    for path, digest in ((HERE / 'PLAN.md', None), (HERE / 'REVIEW.md', None),
                         (HERE / 'STATIC_AUDIT.md', None), (HERE / 'layer.py', None)):
        if not path.exists():
            raise AssertionError(f'missing study input {path}')
    target_pool = read_json(TARGET_POOL)
    target_results = read_json(TARGET_RESULTS)
    public_pool = read_json(PUBLIC_POOL)
    public_discovery = read_json(PUBLIC_DISCOVERY)
    return target_pool, target_results, public_pool, public_discovery


def build() -> None:
    if any(path.exists() for path in (CANDIDATE, FEATURES, POOL, STATIC_RECEIPT)):
        raise FileExistsError('frozen output exists; run verify-static instead of rebuilding')
    target_pool, target_results, public_pool, public_discovery = load_all_inputs()
    candidate_bytes = construct_candidate()
    candidate_digest = hashlib.sha256(candidate_bytes).hexdigest()
    features = load_features(target_pool, target_results, public_pool, public_discovery)
    pool = build_pool(target_pool, target_results, public_pool, public_discovery,
                      features, candidate_digest, sha(Path(__file__)))
    preflight = static_preflight(candidate_bytes, candidate_digest, features, pool)
    write_bytes_new(CANDIDATE, candidate_bytes)
    write_new(FEATURES, features)
    write_new(POOL, pool)
    # Recompute after writing so the receipt covers the actual frozen bytes.
    preflight['pool_sha256'] = sha(POOL)
    preflight['feature_rows_sha256'] = sha(FEATURES)
    write_new(STATIC_RECEIPT, preflight)
    print(json.dumps({
        'complete': True,
        'passed': preflight['passed'],
        'candidate': str(CANDIDATE.resolve()),
        'candidate_sha256': sha(CANDIDATE),
        'pool': str(POOL.resolve()),
        'pool_sha256': sha(POOL),
        'feature_rows': str(FEATURES.resolve()),
        'feature_rows_sha256': sha(FEATURES),
        'feature_rows_count': features['row_count'],
        'static_preflight': str(STATIC_RECEIPT.resolve()),
        'static_preflight_sha256': sha(STATIC_RECEIPT),
        'native_prefix': preflight['native_prefix'],
        'outcome_games_started': False,
    }, indent=2), flush=True)


def verify_static() -> None:
    target_pool, target_results, public_pool, public_discovery = load_all_inputs()
    pool = read_json(POOL)
    features = read_json(FEATURES)
    receipt = read_json(STATIC_RECEIPT)
    candidate_digest = sha(CANDIDATE)
    candidate_bytes = CANDIDATE.read_bytes()
    if pool['candidate']['sha256'] != candidate_digest:
        raise AssertionError('candidate hash differs from frozen pool')
    verify_upstream_bindings(pool['bindings'])
    if sha(FEATURES) != pool['feature_rows']['sha256']:
        raise AssertionError('feature rows differ from frozen pool')
    if sha_json(features) != pool['feature_rows']['sha256']:
        raise AssertionError('feature row canonical hash mismatch')
    regenerated = load_features(target_pool, target_results, public_pool, public_discovery)
    if sha_json(regenerated) != sha(FEATURES):
        raise AssertionError('208 public feature rows no longer reproduce from bound source traces')
    expected = static_preflight(candidate_bytes, candidate_digest, features, pool)
    for key in ('complete', 'passed', 'candidate_sha256', 'pool_sha256',
                'feature_rows_sha256', 'bound_feature_rows', 'fixture_count',
                'source_branch_counts', 'guard_branch_counts', 'guard_changed_contexts',
                'donor_control_contexts', 'donor_controls_all_zero_pasture_and_leaf_inactive',
                'third_observation72_leaf_feature_matches', 'candidate_static_checks',
                'fresh_chris_a44_controls_staged'):
        if expected[key] != receipt[key]:
            raise AssertionError(f'static preflight drift: {key}')
    if receipt['pool_sha256'] != sha(POOL) or receipt['feature_rows_sha256'] != sha(FEATURES):
        raise AssertionError('static receipt does not bind frozen pool/features')
    print(json.dumps({
        'verified': True, 'passed': receipt['passed'],
        'candidate_sha256': candidate_digest, 'pool_sha256': sha(POOL),
        'feature_rows_sha256': sha(FEATURES), 'feature_rows_count': features['row_count'],
        'native_prefix': receipt['native_prefix'], 'outcome_games_started': False,
    }, indent=2), flush=True)


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {'build', 'verify-static'}:
        raise SystemExit(f'usage: py -3 {Path(__file__).as_posix()} build|verify-static')
    if sys.argv[1] == 'build':
        build()
    else:
        verify_static()


if __name__ == '__main__':
    main()
