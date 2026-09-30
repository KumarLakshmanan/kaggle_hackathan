"""Static preflight and freeze builder for the six-fixture Ghost outcome run.
This module reads frozen artifacts and game inputs; it never imports the game engine.
"""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GHOST = ROOT / 'diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929'
BASE6 = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
CACHE = ROOT / 'diagnostics/stream_replay_io_20260928'
SHARED_PANEL = ROOT / 'diagnostics/physical_route_rollout_20260928'
RUN_LOCK_HELPER = ROOT / 'diagnostics/local_target_20260928/run_lock.py'
CANDIDATE_SHA = '228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767'
PARENT_CANDIDATE_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
GOOSE4_SHA = 'c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632'
A44_SHA = 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
GHOST_PREFLIGHT_SHA = 'aefa68e3126e9eb6554cdfe426d023953e90524a72f8da49c4986240c6f801fc'
GHOST_MANIFEST_SHA = '3a3cd881a7d2972e93c57dbc747ff16ca0c335b773b3ebafaa7f63eb440aa4d2'
GHOST_PANEL_SHA = '545c038fb0ab95530a53e58847e23233ddc3a0202fc36dae72f500ef185cbbf6'
BASE6_RESULTS_SHA = '5463a0efa37aebad2c11559cbcd2c39bf2a9a63ec5b2279f409d6360c61ff40d'
BASE6_PARENT_PANEL_SHA = '7407b5f610457d2c00837a3c82e51ae2deaa225b20f2145e01dfaa92dba1db51'
BASE6_PANEL_SHA = '223294a93418ec110e2f53414b0592a478046e99877755fd42fee71f30471b7c'
BASE6_MANIFEST_SHA = 'bb4e44f5d0038ce5fd24c2a9b935e7f341538abe484fef7aa819f38b6c6d900a'
A44_CONTROLS_SHA = '91155aea3fa6ef6dc3cdc4ab97e5eaaab889909cb3acfaedc9377c593953cc55'
FEATURE_ROWS_SHA = 'bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795'
CACHE_SHA = 'f544b134e2ad51160e4d6ad7719b9f41ad6cc850a1a51162249ede1cba279968'
FIXTURES = (
    'live-114255779', 'live-114258293', 'live-114288168',
    'public-win-114209881', 'public-win-114221853', 'public-win-114245470',
)
ICE_KEY = 'ICE_CREAM_SHOP|M8+|C>S|G0'

FIXED_FILES = (
    (GHOST / 'candidate.py', CANDIDATE_SHA, 'ghost candidate'),
    (GHOST / 'preflight.json', GHOST_PREFLIGHT_SHA, 'ghost static preflight receipt'),
    (GHOST / 'frozen_manifest.json', GHOST_MANIFEST_SHA, 'ghost frozen manifest'),
    (GHOST / 'panel.json', GHOST_PANEL_SHA, 'ghost six-fixture panel'),
    (BASE6 / 'candidate.py', PARENT_CANDIDATE_SHA, 'exact accepted 6d parent candidate'),
    (BASE6 / 'combined_results.json', BASE6_RESULTS_SHA, 'exact 6d combined baseline'),
    (BASE6 / 'parent_panel.json', BASE6_PARENT_PANEL_SHA, '104-fixture parent panel'),
    (BASE6 / 'panel.json', BASE6_PANEL_SHA, '6d selected panel'),
    (BASE6 / 'frozen_manifest.json', BASE6_MANIFEST_SHA, '6d frozen manifest'),
    (BASE6 / 'a44_controls.json', A44_CONTROLS_SHA, 'a44 controls'),
    (BASE6 / 'feature_rows.json', FEATURE_ROWS_SHA, 'bound 104-fixture features'),
    (CACHE / 'fast_game_cached.py', 'a57d12659af613512a61ac02aaa43d4c5ae4f4d8f2c5c02d3ed4ac6eafa2a38e', 'native-game runner helper'),
    (CACHE / 'cached_input.py', 'e2aaefda623775c9c7d56304271c827ecd6e56cc109e5c6d8b35aeb458268aa1', 'cached input helper'),
    (CACHE / 'initial_states.json', CACHE_SHA, 'verified replay cache'),
    (CACHE / 'cached_helper_manifest.json', '24c526c44382bf9bd24139bbb20d3c4e75aaf3ee24f73609cf703c1839ad4173', 'cached helper manifest'),
    (CACHE / 'cached_helper_parity.json', 'd4971428f0141301c7f3ebe6c2ee42b66c3a5f9faef202e7e22a0fb041958fa7', 'cached helper parity receipt'),
    (SHARED_PANEL / 'native_core.py', '5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795', 'frozen native transitions'),
    (SHARED_PANEL / 'check.py', 'f51b49dd2c627337136365603e4d0923c9f3e77f28bc8c77d08f608cba48e4a6', 'native state helper'),
    (SHARED_PANEL / 'parity.json', '26ebd915525fbb4285387364deb13c3e28da7509708dfc9b7f419978cc40e273', 'native parity receipt'),
    (SHARED_PANEL / 'RESULTS.md', 'abea40c0701877b8942509b5ec7567905990825f63f1001e8041501cec871b0f', 'native parity report'),
    (RUN_LOCK_HELPER, '6ae76386c4bfda83a5efff6c0772ad22a4480155126ac9f0ed5616ec68c0d219', 'exclusive run lock helper'),
)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def resolved(path):
    return str(Path(path).resolve())


def add_binding(bindings, roles, path, role, expected=None):
    path = Path(path).resolve()
    actual = sha(path)
    if expected is not None and actual != expected:
        raise ValueError(f'{role} SHA mismatch: {path}: {actual} != {expected}')
    key = str(path)
    if key in bindings and bindings[key] != actual:
        raise ValueError(f'conflicting binding: {path}')
    bindings[key] = actual
    roles.setdefault(key, []).append(role)
    return actual


def action_tape_sha(tape):
    candidates = set()
    for sort_keys in (False, True):
        packed = json.dumps(tape, sort_keys=sort_keys, separators=(',', ':')).encode('utf-8')
        candidates.add(hashlib.sha256(packed).hexdigest())
    return candidates


def verify_and_freeze():
    manifest_path = HERE / 'frozen_manifest.json'
    receipt_path = HERE / 'preflight.json'
    outputs = (HERE / 'candidate.jsonl', HERE / 'run_receipt.json', HERE / 'run.lock')
    runner_source = (HERE / 'run.py').read_text(encoding='utf-8')
    if ('checks = telemetry_checks(actual, panel_row, expected_trigger)' not in runner_source
            or 'checks = telemetry_checks(panel_row, expected_trigger)' in runner_source):
        raise ValueError('runner telemetry call site must pass the actual game result')
    import runpy
    runner_namespace = runpy.run_path(str(HERE / 'run.py'))
    telemetry_checks = runner_namespace['telemetry_checks']
    active_panel = {'step72_public_wheat': 9975, 'expected_derivative_route': 113360743}
    active_telemetry = {
        'a44_ghost_wheat_branch72': 'source',
        'a44_ghost_wheat_key72': ICE_KEY,
        'a44_ghost_wheat_checked72': True,
        'a44_ghost_wheat_stock72': 9975,
        'a44_ghost_wheat_active72': True,
        'a44_ghost_wheat_route72': '113360743',
        'a44_goose4_branch72': 'source',
        'a44_goose4_key72': ICE_KEY,
        'a44_goose4_route': '113360743',
        'a44_goose4_turns': 647,
        'a44_goose4_errors': 0,
        'bridge_errors': 0,
    }
    positive = telemetry_checks({'candidate_telemetry': active_telemetry}, active_panel, True)
    if not all(item['passed'] for item in positive.values()):
        raise ValueError('synthetic positive telemetry check failed')
    negative = telemetry_checks({}, active_panel, True)
    if any(item['passed'] for item in negative.values()):
        raise ValueError('synthetic missing-telemetry check failed to reject')

    if manifest_path.exists() or receipt_path.exists():
        raise FileExistsError('freeze outputs already exist; this preflight never overwrites')
    existing = [str(p) for p in outputs if p.exists()]
    if existing:
        raise FileExistsError(f'outcome or lock output already exists: {existing}')

    bindings, roles = {}, {}
    for path, expected, role in FIXED_FILES:
        add_binding(bindings, roles, path, role, expected)
    add_binding(bindings, roles, HERE / 'PLAN.md', 'frozen outcome plan')
    add_binding(bindings, roles, HERE / 'panel.json', 'copied Ghost six-fixture panel', GHOST_PANEL_SHA)
    add_binding(bindings, roles, HERE / 'run.py', 'one-shot outcome runner')
    add_binding(bindings, roles, HERE / 'preflight.py', 'static freeze builder')

    ghost_panel_path = GHOST / 'panel.json'
    panel = load(HERE / 'panel.json')
    ghost_panel = load(ghost_panel_path)
    ghost_receipt = load(GHOST / 'preflight.json')
    ghost_manifest = load(GHOST / 'frozen_manifest.json')
    if panel != ghost_panel:
        raise ValueError('copied six-fixture panel differs from the Ghost source panel')
    if not (ghost_receipt.get('passed') is True and ghost_receipt.get('static_only') is True
            and ghost_receipt.get('experiment_completed') is False
            and ghost_receipt.get('outcome_games_run') == 0
            and ghost_receipt.get('engine_transitions') == 0
            and ghost_receipt.get('policy_action_calls') == 0
            and ghost_receipt.get('candidate_sha256') == CANDIDATE_SHA
            and ghost_receipt.get('parent_candidate_sha256') == PARENT_CANDIDATE_SHA
            and ghost_receipt.get('source_a44_sha256') == A44_SHA):
        raise ValueError('Ghost static preflight receipt is not the expected no-game pass')
    if not (ghost_manifest.get('complete') is True and ghost_manifest.get('static_only') is True
            and ghost_manifest.get('experiment_completed') is False
            and ghost_manifest.get('outcome_games_run') == 0
            and ghost_manifest.get('candidate_sha256') == CANDIDATE_SHA
            and ghost_manifest.get('parent_candidate_sha256') == PARENT_CANDIDATE_SHA
            and ghost_manifest.get('source_a44_sha256') == A44_SHA
            and ghost_manifest.get('preflight_sha256') == GHOST_PREFLIGHT_SHA):
        raise ValueError('Ghost frozen manifest does not match the expected derivative')
    if ghost_manifest.get('input_binding_count') != 498:
        raise ValueError('Ghost parent input binding count changed')

    combined = load(BASE6 / 'combined_results.json')
    parent_panel = load(BASE6 / 'parent_panel.json')
    panel6 = load(BASE6 / 'panel.json')
    cache = load(CACHE / 'initial_states.json')
    if not (combined.get('complete') and combined.get('diagnostic_only')
            and combined.get('fixed_tape_only') and combined.get('promotion') is False
            and combined.get('candidate_sha256') == PARENT_CANDIDATE_SHA
            and combined.get('source_a44_sha256') == A44_SHA
            and combined.get('panel_sha256') == BASE6_PARENT_PANEL_SHA
            and combined.get('new_candidate_games') == 12
            and combined.get('equivalent_reused_parent_games') == 196
            and len(combined.get('games', [])) == 208):
        raise ValueError('6d combined result receipt changed or is incomplete')
    if not (parent_panel.get('fixture_count') == 104 and len(parent_panel.get('fixtures', [])) == 104
            and panel6.get('fixture_count') == 6 and panel6.get('candidate_games') == 12
            and cache.get('complete') is True and cache.get('fixture_count') == 104):
        raise ValueError('6d panel or replay cache census changed')

    games = panel.get('games', [])
    if panel.get('fixture_count') != 6 or panel.get('game_count') != 12 or len(games) != 12:
        raise ValueError('outcome panel must contain six fixtures and twelve seat rows')
    expected_pairs = [(fixture_id, seat) for fixture_id in FIXTURES for seat in (0, 1)]
    actual_pairs = [(row['fixture_id'], int(row['candidate_seat'])) for row in games]
    if actual_pairs != expected_pairs:
        raise ValueError('panel rows are not the fixed fixture/seat order')
    if panel.get('candidate_sha256') != CANDIDATE_SHA or panel.get('parent_candidate_sha256') != PARENT_CANDIDATE_SHA:
        raise ValueError('panel candidate lineage changed')
    if panel.get('source_a44_sha256') != A44_SHA or panel.get('accepted_combined_results_sha256') != BASE6_RESULTS_SHA:
        raise ValueError('panel baseline binding changed')
    if panel.get('full_panel_sha256') != BASE6_PARENT_PANEL_SHA:
        raise ValueError('panel does not cite exact 104-fixture parent panel')

    baseline = {(row['fixture_id'], int(row['candidate_seat'])): row for row in combined['games']}
    if len(baseline) != 208:
        raise ValueError('6d combined results are not unique by fixture and seat')
    parent_fixtures = {row['fixture_id']: row for row in parent_panel['fixtures']}
    cache_replays = {row['source_replay_path']: row for row in cache['replays']}
    cache_fixtures = {row['fixture_id']: row['source_replay_path'] for row in cache['fixtures']}
    if (len(parent_fixtures) != 104 or len(cache_fixtures) != 104
            or len(cache_replays) != cache.get('unique_replay_count')):
        raise ValueError('parent fixture keys or unique replay-cache keys are malformed')

    activated, controls, baseline_rows, fixture_blobs = [], [], [], []
    for fixture_id in FIXTURES:
        fixture = parent_fixtures.get(fixture_id)
        if fixture is None:
            raise ValueError(f'fixture absent from 104-row parent panel: {fixture_id}')
        replay_path = Path(fixture['source_replay_path']).resolve()
        if cache_fixtures.get(fixture_id) != str(replay_path):
            raise ValueError(f'fixture/replay cache mapping differs from parent panel: {fixture_id}')
        cached = cache_replays.get(str(replay_path))
        if cached is None or cached['source_replay_sha256'] != fixture['source_replay_sha256']:
            raise ValueError(f'fixture replay is not bound by initial-state cache: {fixture_id}')
        replay_sha = add_binding(bindings, roles, replay_path, f'{fixture_id} compressed replay')
        if replay_sha != cached['compressed_sha256']:
            raise ValueError(f'compressed replay hash differs from cache: {fixture_id}')
        tape_path = Path(fixture['source_action_tape_path']).resolve()
        tape_file_sha = add_binding(bindings, roles, tape_path, f'{fixture_id} fixed opponent action tape')
        tape = json.loads(gzip.decompress(tape_path.read_bytes()))['actions']
        tape_content_shas = action_tape_sha(tape)
        if len(tape) != 719 or fixture['source_opponent_action_sha256'] not in tape_content_shas:
            raise ValueError(f'action tape content hash/length mismatch: {fixture_id}')
        fixture_blobs.append(dict(fixture_id=fixture_id,
                                  source_replay_path=str(replay_path),
                                  source_replay_sha256=fixture['source_replay_sha256'],
                                  source_replay_compressed_sha256=replay_sha,
                                  source_action_tape_path=str(tape_path),
                                  source_action_tape_compressed_sha256=tape_file_sha,
                                  source_opponent_action_sha256=fixture['source_opponent_action_sha256'],
                                  action_count=len(tape)))

    for row in games:
        key = (row['fixture_id'], int(row['candidate_seat']))
        fixture_id, seat = key
        if row.get('step72_branch') != 'source' or row.get('step72_public_key') != ICE_KEY:
            raise ValueError(f'expected public source/ICE key mismatch: {key}')
        expected_route = 113360743 if row.get('expected_trigger') else 113470868
        if int(row.get('step72_public_wheat')) < 0 or row.get('expected_derivative_route') != expected_route:
            raise ValueError(f'expected route/wheat metadata mismatch: {key}')
        if bool(row.get('expected_trigger')) != (fixture_id == 'live-114288168'):
            raise ValueError(f'unexpected trigger fixture: {key}')
        if row.get('expected_trigger') and int(row['step72_public_wheat']) != 9975:
            raise ValueError(f'Ghost target threshold differs: {key}')
        if not row.get('expected_trigger') and int(row['step72_public_wheat']) <= 9975:
            raise ValueError(f'false-trigger control crosses threshold: {key}')
        if row.get('expected_parent_goose4_route') != 113470868:
            raise ValueError(f'parent Goose4 route mismatch: {key}')
        base = baseline.get(key)
        if base is None or not base.get('decision_equivalence_reuse'):
            raise ValueError(f'6d combined result row missing or not exact parent reuse: {key}')
        if base.get('candidate_sha256') != GOOSE4_SHA:
            raise ValueError(f'expected exact Goose4 source row for accepted 6d baseline: {key}')
        if (row.get('accepted_6d_result') != base.get('result')
                or float(row.get('accepted_6d_margin')) != float(base.get('margin'))
                or row.get('accepted_6d_result_row_candidate_sha256') != base.get('candidate_sha256')):
            raise ValueError(f'panel 6d baseline outcome differs from combined receipt: {key}')
        controls_fields = ('result', 'candidate_reward', 'opponent_reward', 'margin')
        baseline_rows.append(dict(fixture_id=fixture_id, candidate_seat=seat,
                                  expected_trigger=bool(row['expected_trigger']),
                                  baseline={name: base[name] for name in controls_fields},
                                  baseline_source_candidate_sha256=base['candidate_sha256']))
        if row['expected_trigger']:
            activated.append(key)
        else:
            controls.append(key)
        trace_path = Path(row['source_trace_path']).resolve()
        trace_sha = add_binding(bindings, roles, trace_path,
                                f'{fixture_id} seat {seat} step-72 feature trace', row['source_trace_sha256'])
        if trace_sha != row['source_trace_sha256']:
            raise ValueError(f'step-72 trace hash mismatch: {key}')

    if activated != [('live-114288168', 0), ('live-114288168', 1)] or len(controls) != 10:
        raise ValueError('expected exactly two Ghost target seats and ten false-trigger controls')
    if len(set(bindings)) != len(bindings):
        raise ValueError('duplicate frozen file path')

    # Keep the static receipt limited to byte/hash/data checks. It makes no policy call and imports no transition code.
    receipt = dict(
        schema='ghost-wheat-outcome-static-preflight/v1',
        passed=True,
        static_only=True,
        experiment_completed=False,
        outcome_games_run=0,
        engine_transitions=0,
        policy_action_calls=0,
        promotion=False,
        reactive_validation=False,
        fixed_tape_only=True,
        candidate_sha256=CANDIDATE_SHA,
        parent_candidate_sha256=PARENT_CANDIDATE_SHA,
        source_a44_sha256=A44_SHA,
        ghost_preflight_sha256=GHOST_PREFLIGHT_SHA,
        ghost_manifest_sha256=GHOST_MANIFEST_SHA,
        accepted_combined_results_sha256=BASE6_RESULTS_SHA,
        parent_panel_sha256=BASE6_PARENT_PANEL_SHA,
        panel_sha256=sha(HERE / 'panel.json'),
        fixture_count=6,
        game_count=12,
        activation_seats=[dict(fixture_id=f, seat=s) for f, s in activated],
        false_trigger_control_count=len(controls),
        expected_trigger_count=len(activated),
        exact_6d_baseline_rows=baseline_rows,
        fixture_blobs=fixture_blobs,
        binding_count=len(bindings),
        bindings=bindings,
        binding_roles=roles,
        no_resume=True,
        output_absence_checked=True,
    )
    receipt_path.open('x', encoding='utf-8', newline='\n').write(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    receipt_sha = sha(receipt_path)
    manifest_bindings = dict(bindings)
    manifest_bindings[str(receipt_path.resolve())] = receipt_sha
    manifest_roles = {path: list(roles.get(path, [])) for path in manifest_bindings}
    manifest_roles[str(receipt_path.resolve())] = ['outcome static preflight receipt']
    manifest = dict(
        schema='ghost-wheat-outcome-run-freeze/v1',
        complete=True,
        diagnostic_only=True,
        fixed_tape_only=True,
        promotion=False,
        reactive_validation=False,
        experiment_completed=False,
        outcome_games_run=0,
        candidate_sha256=CANDIDATE_SHA,
        parent_candidate_sha256=PARENT_CANDIDATE_SHA,
        goose4_candidate_sha256=GOOSE4_SHA,
        source_a44_sha256=A44_SHA,
        ghost_preflight_sha256=GHOST_PREFLIGHT_SHA,
        ghost_static_manifest_sha256=GHOST_MANIFEST_SHA,
        static_preflight_sha256=receipt_sha,
        accepted_combined_results_sha256=BASE6_RESULTS_SHA,
        parent_panel_sha256=BASE6_PARENT_PANEL_SHA,
        panel_sha256=sha(HERE / 'panel.json'),
        runner_sha256=sha(HERE / 'run.py'),
        plan_sha256=sha(HERE / 'PLAN.md'),
        preflight_builder_sha256=sha(HERE / 'preflight.py'),
        binding_count=len(manifest_bindings),
        bindings=manifest_bindings,
        binding_roles=manifest_roles,
        future_outputs=['candidate.jsonl', 'run_receipt.json'],
        lock_paths=[str((ROOT / 'diagnostics/.shared_game_run.lock').resolve()), str((HERE / 'run.lock').resolve())],
        gate=dict(clean_games=12, frames=720, candidate_and_opponent_done=True,
                  ghost_both_seats_win=True, false_trigger_controls_exactly_match_6d=10,
                  expected_telemetry=True),
        run_command='python -X utf8 diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/outcome_run_v2_20260929/run.py',
    )
    (HERE / 'frozen_manifest.json').open('x', encoding='utf-8', newline='\n').write(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return receipt, manifest


if __name__ == '__main__':
    receipt, manifest = verify_and_freeze()
    print(json.dumps(dict(passed=receipt['passed'], static_only=True,
                          outcome_games_run=0, engine_transitions=0,
                          binding_count=manifest['binding_count'],
                          static_preflight_sha256=manifest['static_preflight_sha256']), indent=2))
