"""Static hash binding and freeze for the combined 18-seat outcome test."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
COMBO = HERE.parent
BASE6 = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
GHOST = ROOT / 'diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929'
KWA = ROOT / 'diagnostics/a44_kwa_wheat_zero_20260929'
CACHE = ROOT / 'diagnostics/stream_replay_io_20260928'
NATIVE = ROOT / 'diagnostics/physical_route_rollout_20260928'
LOCK_HELPER = ROOT / 'diagnostics/local_target_20260928/run_lock.py'
CANDIDATE = COMBO / 'candidate_v4.py'
PANEL_PATH = COMBO / 'panel_v4.json'
MANIFEST_PATH = HERE / 'frozen_manifest.json'
PREFLIGHT_PATH = HERE / 'static_preflight.json'
RESULTS_PATH = HERE / 'outcomes.jsonl'
RECEIPT_PATH = HERE / 'outcome_receipt.json'
RUN_MANIFEST_PATH = HERE / 'run_manifest.json'
OWN_LOCK_PATH = HERE / 'run.lock'
CANDIDATE_SHA = '7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2'
PANEL_SHA = '8f9eec84d361de731d95de88d76c5e78bf2c6bab58012a376daa5bdf466d15bd'
PARENT_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
REUSED_SHA = 'c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632'
BASE6_RESULTS_SHA = '5463a0efa37aebad2c11559cbcd2c39bf2a9a63ec5b2279f409d6360c61ff40d'
BASE6_PANEL_SHA = '7407b5f610457d2c00837a3c82e51ae2deaa225b20f2145e01dfaa92dba1db51'
GHOST_CANDIDATE_SHA = '228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767'
GHOST_PREFLIGHT_SHA = 'aefa68e3126e9eb6554cdfe426d023953e90524a72f8da49c4986240c6f801fc'
GHOST_MANIFEST_SHA = '3a3cd881a7d2972e93c57dbc747ff16ca0c335b773b3ebafaa7f63eb440aa4d2'
GHOST_PANEL_SHA = '545c038fb0ab95530a53e58847e23233ddc3a0202fc36dae72f500ef185cbbf6'
GHOST_RUN_RECEIPT_SHA = '510339d20aace4317f7dfc4330b7a8f4e59d1edcc5fd458f474fddefb3c702f8'
GHOST_LEDGER_SHA = 'a060e1441ee0ac37e8e83c3e81203797fecc78ad0d306e27ca98a21cbcf6831c'
KWA_CANDIDATE_SHA = '36f1a351c4b85b62d7c5fb07489927821d98823c57d0e7131e19eb186951a54e'
KWA_LAYER_SHA = '5f137649d797d95305854fcb2fc9bff2febdbde0e2522029f6797e5b68ff83d5'
KWA_PREFLIGHT_SHA = 'dd44f46bb135f2ffb0b0fb894a001d737dce92c1f703d55fa14d3c57f5b1d89a'
KWA_MANIFEST_SHA = '329176df031f017ad5ba6ac45edd3401b4891910d840c128ae3f731a48a07e3f'
KWA_RUN_RECEIPT_SHA = '940a16e49362dd6a7b1f07a14602eb41c3949d74b8e1ccdd975137c88a4baee3'
KWA_LEDGER_SHA = 'b384008eee6a94522b85216d066468f3335b5c1ad950ed731ba7fc9f94cdf2cc'
FEATURE_ROWS_SHA = 'bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795'
ACTION_CACHE_SHA = 'f544b134e2ad51160e4d6ad7719b9f41ad6cc850a1a51162249ede1cba279968'
REUSED_GOOSE4_SHA = 'c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632'
UNION_ORDER = (
    'live-114227779', 'live-114236633', 'live-114255779',
    'live-114257327', 'live-114258293', 'live-114288168',
    'public-win-114209881', 'public-win-114221853', 'public-win-114245470',
)
TOP20_COUNT = 20
CONTROL_FIELDS = (
    'result', 'candidate_reward', 'opponent_reward', 'margin',
    'candidate_status', 'opponent_status', 'frames',
)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def key(path):
    return str(Path(path).resolve())


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_step72(trace_path, expected_seat):
    with gzip.open(trace_path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            item = json.loads(line)
            if int(item.get('step', -1)) != 72:
                continue
            observation = item.get('observation') or {}
            require(int(observation.get('step', -1)) == 72,
                    f'step-72 observation malformed: {trace_path}')
            player = int(observation.get('player', -1))
            require(player == int(expected_seat), f'trace seat mismatch: {trace_path}')
            rival = observation['farms'][1 - player]
            wheat_plots = sum(1 for row in rival['tiles'] for tile in row
                              if isinstance(tile, dict) and tile.get('crop') == 'WHEAT')
            wheat_stock = int(observation['market']['inventory']['WHEAT'])
            return wheat_plots, wheat_stock
    raise AssertionError(f'step-72 observation missing: {trace_path}')


def verify_action_tape(path, expected_digest):
    doc = json.loads(gzip.decompress(Path(path).read_bytes()))
    tape = doc.get('actions')
    require(isinstance(tape, list) and len(tape) == 719,
            f'opponent action tape length changed: {path}')
    digests = {
        hashlib.sha256(json.dumps(tape, sort_keys=sort_keys,
                                 separators=(',', ':')).encode('utf-8')).hexdigest()
        for sort_keys in (False, True)
    }
    require(expected_digest in digests, f'opponent action tape content changed: {path}')


def add_binding(bindings, path, expected=None):
    path = Path(path).resolve()
    require(path.is_file(), f'missing frozen input: {path}')
    actual = sha(path)
    if expected is not None:
        require(actual == expected, f'hash mismatch for {path}: {actual} != {expected}')
    prior = bindings.setdefault(str(path), actual)
    require(prior == actual, f'conflicting binding for {path}')


def verify_inputs():
    require(sha(CANDIDATE) == CANDIDATE_SHA, 'combined candidate hash changed')
    require(sha(PANEL_PATH) == PANEL_SHA, 'combined panel hash changed')
    candidate = CANDIDATE.read_text(encoding='utf-8')
    compile(candidate, str(CANDIDATE), 'exec')
    panel = load(PANEL_PATH)
    require(panel.get('schema') == 'a44-ghost-kwa-combined-fixed-panel-v2'
            and panel.get('candidate_sha256') == CANDIDATE_SHA
            and panel.get('parent_6d_candidate_sha256') == PARENT_SHA,
            'panel lineage mismatch')
    require(panel.get('builder_sha256') == sha(COMBO / 'build_candidate.py')
            and panel.get('top20_goal_metric') == 'both-seat fixture sweep'
            and panel.get('top20_min_winning_sweeps') == 18,
            'panel builder binding or top20 objective changed')
    require(panel.get('game_count') == 58 and panel.get('fixture_count') == 29
            and panel.get('top20_fixture_count') == 20
            and panel.get('top20_game_count') == 40
            and panel.get('expected_control_seats') == 54,
            'panel fixture order or size changed')
    parent_panel = load(BASE6 / 'parent_panel.json')
    top20_order = [row['fixture_id'] for row in parent_panel['fixtures']
                   if row['panel'] == 'top20']
    require(len(top20_order) == TOP20_COUNT and len(set(top20_order)) == TOP20_COUNT,
            'parent panel does not contain exactly 20 top-team fixtures')
    fixture_order = top20_order + list(UNION_ORDER)
    require(panel.get('fixture_order') == fixture_order,
            'panel fixture membership or order changed')
    expected_rows = [(fixture_id, seat) for fixture_id in fixture_order for seat in (0, 1)]
    actual_rows = [(row['fixture_id'], int(row['candidate_seat'])) for row in panel['games']]
    require(actual_rows == expected_rows, 'panel seat order changed')
    require(sum(bool(row['expected_kwa_trigger']) for row in panel['games']) == 2
            and sum(bool(row['expected_ghost_trigger']) for row in panel['games']) == 2
            and sum(not row['expected_kwa_trigger'] and not row['expected_ghost_trigger']
                    for row in panel['games']) == 54,
            'trigger/control counts changed')
    require(all(not (row['expected_kwa_trigger'] and row['expected_ghost_trigger'])
                for row in panel['games']), 'trigger layers overlap')

    combined = load(BASE6 / 'combined_results.json')
    require(combined.get('complete') is True and combined.get('fixed_tape_only') is True
            and combined.get('candidate_sha256') == PARENT_SHA
            and combined.get('panel_sha256') == BASE6_PANEL_SHA
            and len(combined.get('games', [])) == 208,
            'exact 6d baseline is incomplete or changed')
    require(parent_panel.get('fixture_count') == 104
            and len(parent_panel.get('fixtures', [])) == 104,
            '104-fixture panel changed')
    baseline = {(row['fixture_id'], int(row['candidate_seat'])): row
                for row in combined['games']}
    require(len(baseline) == 208, '6d baseline has duplicate seats')
    parent_fixtures = {row['fixture_id']: row for row in parent_panel['fixtures']}
    require(len(parent_fixtures) == 104, '6d fixture table has duplicate ids')
    cache_doc = load(CACHE / 'initial_states.json')
    require(sha(CACHE / 'initial_states.json') == ACTION_CACHE_SHA
            and cache_doc.get('complete') is True and cache_doc.get('fixture_count') == 104,
            'verified replay cache is incomplete or changed')
    replay_cache = {entry['source_replay_path']: entry for entry in cache_doc['replays']}
    for row in panel['games']:
        seat_key = (row['fixture_id'], int(row['candidate_seat']))
        base = baseline.get(seat_key)
        require(base is not None, f'6d row missing: {seat_key}')
        require(base.get('decision_equivalence_reuse') is True
                and base.get('candidate_sha256') == REUSED_GOOSE4_SHA,
                f'control baseline provenance changed: {seat_key}')
        require({field: row['baseline_6d'].get(field) for field in CONTROL_FIELDS}
                == {field: base.get(field) for field in CONTROL_FIELDS},
                f'panel baseline fields changed: {seat_key}')
        fixture = parent_fixtures.get(row['fixture_id'])
        require(fixture is not None, f'fixture absent from 6d panel: {row["fixture_id"]}')
        require(fixture == row['source_fixture'], f'source fixture metadata changed: {seat_key}')
        cached = replay_cache.get(fixture['source_replay_path'])
        require(cached is not None
                and cached['source_replay_sha256'] == fixture['source_replay_sha256']
                and sha(fixture['source_replay_path']) == cached['compressed_sha256'],
                f'compressed replay differs from audited cache: {seat_key}')
        verify_action_tape(fixture['source_action_tape_path'],
                           fixture['source_opponent_action_sha256'])
        trace = Path(row['feature_trace_path'])
        require(trace.is_file() and sha(trace) == row['feature_trace_sha256'],
                f'feature trace changed: {seat_key}')
        wheat_plots, wheat_stock = read_step72(trace, int(row['candidate_seat']))
        require(row.get('expected_kwa_wheat_plots') == wheat_plots
                and row.get('expected_ghost_wheat') == wheat_stock,
                f'step-72 public-state census changed: {seat_key}')
        source_branch = row['expected_branch'] == 'source'
        require(row.get('expected_kwa_wheat_plots_telemetry') == (wheat_plots if source_branch else None)
                and row.get('expected_ghost_wheat_telemetry') == (wheat_stock if source_branch else None),
                f'source-only telemetry expectation changed: {seat_key}')

    top20_rows = [row for row in panel['games'] if row['panel'] == 'top20']
    top20_results = {}
    for row in top20_rows:
        top20_results.setdefault(row['fixture_id'], []).append(row['baseline_6d']['result'])
    top20_wins = sum(len(results) == 2 and all(result == 'win' for result in results)
                     for results in top20_results.values())
    require(len(top20_rows) == 40 and len(top20_results) == 20 and top20_wins >= 18
            and panel.get('top20_baseline_winning_sweeps') == top20_wins,
            'frozen 6d parent does not preserve the 90% top20 goal')

    ghost_static = load(GHOST / 'preflight.json')
    ghost_receipt = load(GHOST / 'outcome_run_v2_20260929/run_receipt.json')
    kwa_static = load(KWA / 'preflight.json')
    kwa_receipt = load(KWA / 'runs/six_game_run_001/outcome_receipt.json')
    require(ghost_static.get('passed') is True and ghost_static.get('engine_transitions') == 0
            and ghost_receipt.get('gate_passed') is True and ghost_receipt.get('game_count') == 12
            and ghost_receipt.get('candidate_sha256') == GHOST_CANDIDATE_SHA,
            'upstream Ghost fixed-panel result did not pass')
    require(kwa_static.get('complete') is True and kwa_static.get('game_transitions') == 0
            and kwa_receipt.get('all_outcome_gates_passed') is True
            and kwa_receipt.get('candidate_sha256') == KWA_CANDIDATE_SHA,
            'upstream Kwa fixed-panel result did not pass')
    require(ghost_static.get('candidate_sha256') == GHOST_CANDIDATE_SHA
            and kwa_static.get('candidate_sha256') == KWA_CANDIDATE_SHA,
            'upstream candidate lineage changed')
    ghost_rows = {(row['fixture_id'], int(row['seat'])): row
                  for row in ghost_static['feature_census']['all_feature_decisions']}
    kwa_targets = {(row['fixture_id'], int(row['seat']))
                   for row in load(KWA / 'preflight.json')['trigger_rows']}
    ghost_targets = {(key, seat) for key, seat in ghost_rows
                     if ghost_rows[(key, seat)].get('triggered')}
    require(kwa_targets == {('live-114227779', 0), ('live-114227779', 1)}
            and ghost_targets == {('live-114288168', 0), ('live-114288168', 1)},
            'upstream activation census changed')
    for row in panel['games']:
        k = (row['fixture_id'], int(row['candidate_seat']))
        g = ghost_rows[k]
        require(bool(row['expected_ghost_trigger']) == bool(g['triggered'])
                and row['expected_branch'] == g['bridge_branch']
                and row['expected_key'] == g['step72_public_key']
                and int(row['expected_ghost_wheat']) == int(g['step72_public_wheat'])
                and row['expected_parent_route'] == g['parent_selected_route'],
                f'Ghost feature census differs at {k}')
        require(bool(row['expected_kwa_trigger']) == (k in kwa_targets),
                f'Kwa feature census differs at {k}')
    return panel, parent_fixtures, baseline


def collect_bindings(panel):
    bindings = {}
    cache = load(CACHE / 'initial_states.json')
    replay_cache = {entry['source_replay_path']: entry for entry in cache['replays']}
    fixed = [
        (CANDIDATE, CANDIDATE_SHA), (PANEL_PATH, PANEL_SHA),
        (COMBO / 'build_candidate.py', None),
        (BASE6 / 'candidate.py', PARENT_SHA),
        (BASE6 / 'combined_results.json', BASE6_RESULTS_SHA),
        (BASE6 / 'parent_panel.json', BASE6_PANEL_SHA),
        (BASE6 / 'frozen_manifest.json', 'bb4e44f5d0038ce5fd24c2a9b935e7f341538abe484fef7aa819f38b6c6d900a'),
        (BASE6 / 'feature_rows.json', FEATURE_ROWS_SHA),
        (BASE6 / 'a44_controls.json', '91155aea3fa6ef6dc3cdc4ab97e5eaaab889909cb3acfaedc9377c593953cc55'),
        (GHOST / 'candidate.py', GHOST_CANDIDATE_SHA),
        (GHOST / 'preflight.json', GHOST_PREFLIGHT_SHA),
        (GHOST / 'frozen_manifest.json', GHOST_MANIFEST_SHA),
        (GHOST / 'panel.json', GHOST_PANEL_SHA),
        (GHOST / 'outcome_run_v2_20260929/run_receipt.json', GHOST_RUN_RECEIPT_SHA),
        (GHOST / 'outcome_run_v2_20260929/candidate.jsonl', GHOST_LEDGER_SHA),
        (KWA / 'candidate.py', KWA_CANDIDATE_SHA),
        (KWA / 'wheat_zero_layer.py', KWA_LAYER_SHA),
        (KWA / 'preflight.json', KWA_PREFLIGHT_SHA),
        (KWA / 'manifest.json', KWA_MANIFEST_SHA),
        (KWA / 'runs/six_game_run_001/outcome_receipt.json', KWA_RUN_RECEIPT_SHA),
        (KWA / 'runs/six_game_run_001/outcomes.jsonl', KWA_LEDGER_SHA),
        (CACHE / 'fast_game_cached.py', 'a57d12659af613512a61ac02aaa43d4c5ae4f4d8f2c5c02d3ed4ac6eafa2a38e'),
        (CACHE / 'cached_input.py', 'e2aaefda623775c9c7d56304271c827ecd6e56cc109e5c6d8b35aeb458268aa1'),
        (CACHE / 'initial_states.json', ACTION_CACHE_SHA),
        (CACHE / 'cached_helper_manifest.json', '24c526c44382bf9bd24139bbb20d3c4e75aaf3ee24f73609cf703c1839ad4173'),
        (CACHE / 'cached_helper_parity.json', 'd4971428f0141301c7f3ebe6c2ee42b66c3a5f9faef202e7e22a0fb041958fa7'),
        (NATIVE / 'native_core.py', '5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795'),
        (NATIVE / 'check.py', 'f51b49dd2c627337136365603e4d0923c9f3e77f28bc8c77d08f608cba48e4a6'),
        (NATIVE / 'parity.json', '26ebd915525fbb4285387364deb13c3e28da7509708dfc9b7f419978cc40e273'),
        (LOCK_HELPER, '6ae76386c4bfda83a5efff6c0772ad22a4480155126ac9f0ed5616ec68c0d219'),
        (HERE / 'PLAN.md', None),
        (HERE / 'run.py', None),
        (HERE / 'preflight.py', None),
    ]
    for path, expected in fixed:
        add_binding(bindings, path, expected)
    cache = load(CACHE / 'initial_states.json')
    replay_cache = {row['source_replay_path']: row for row in cache['replays']}
    for row in panel['games']:
        add_binding(bindings, row['feature_trace_path'], row['feature_trace_sha256'])
        fixture = row['source_fixture']
        cached = replay_cache.get(fixture['source_replay_path'])
        require(cached is not None
                and cached['source_replay_sha256'] == fixture['source_replay_sha256'],
                f'replay metadata differs from input cache: {fixture["fixture_id"]}')
        add_binding(bindings, fixture['source_replay_path'], cached['compressed_sha256'])
        verify_action_tape(fixture['source_action_tape_path'],
                           fixture['source_opponent_action_sha256'])
        add_binding(bindings, fixture['source_action_tape_path'])
    return bindings


def frozen_package():
    panel, fixtures, baseline = verify_inputs()
    bindings = collect_bindings(panel)
    manifest = {
        'schema': 'a44-ghost-kwa-combo-frozen-manifest-v1',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'complete': True,
        'diagnostic_only': True,
        'fixed_tape_only': True,
        'reactive_validation': False,
        'promotion': False,
        'candidate_sha256': CANDIDATE_SHA,
        'panel_sha256': PANEL_SHA,
        'parent_6d_candidate_sha256': PARENT_SHA,
        'parent_6d_results_sha256': BASE6_RESULTS_SHA,
        'ghost_candidate_sha256': GHOST_CANDIDATE_SHA,
        'kwa_candidate_sha256': KWA_CANDIDATE_SHA,
        'binding_count': len(bindings),
        'bindings': bindings,
        'runner_sha256': sha(HERE / 'run.py'),
        'preflight_builder_sha256': sha(HERE / 'preflight.py'),
        'plan_sha256': sha(HERE / 'PLAN.md'),
        'game_count': len(panel['games']),
        'fixture_count': len(panel['fixture_order']),
        'expected_kwa_activations': 2,
        'expected_ghost_activations': 2,
        'expected_controls': 54,
        'resume_allowed': False,
    }
    manifest_path = MANIFEST_PATH
    preflight_path = PREFLIGHT_PATH
    require(not manifest_path.exists() and not preflight_path.exists(),
            'freeze outputs already exist; never overwrites')
    require(not any(path.exists() for path in (RESULTS_PATH, RECEIPT_PATH,
                                               RUN_MANIFEST_PATH, OWN_LOCK_PATH)),
            'game-run output already exists; freeze refuses to overwrite')
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    with manifest_path.open('xb') as out:
        out.write(manifest_bytes)
    preflight = {
        'schema': 'a44-ghost-kwa-combo-static-preflight-v1',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'passed': True,
        'static_only': True,
        'engine_transitions': 0,
        'policy_action_calls': 0,
        'outcome_games_run': 0,
        'candidate_sha256': CANDIDATE_SHA,
        'panel_sha256': PANEL_SHA,
        'manifest_sha256': sha(manifest_path),
        'runner_sha256': sha(HERE / 'run.py'),
        'binding_count': len(bindings),
        'trigger_rows': [
            {'fixture_id': row['fixture_id'], 'seat': row['candidate_seat'],
             'kwa': row['expected_kwa_trigger'], 'ghost': row['expected_ghost_trigger']}
            for row in panel['games'] if row['expected_kwa_trigger'] or row['expected_ghost_trigger']
        ],
        'control_count': 54,
        'evidence_limit': 'Static only. No engine import, agent call, or game transition.',
    }
    with preflight_path.open('xb') as out:
        out.write((json.dumps(preflight, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
    return manifest, preflight


def verify_frozen():
    manifest = load(MANIFEST_PATH)
    preflight = load(PREFLIGHT_PATH)
    require(manifest.get('complete') is True and manifest.get('diagnostic_only') is True
            and manifest.get('fixed_tape_only') is True and manifest.get('promotion') is False
            and manifest.get('candidate_sha256') == CANDIDATE_SHA
            and manifest.get('panel_sha256') == PANEL_SHA,
            'frozen manifest fields differ')
    require(isinstance(manifest.get('bindings'), dict)
            and manifest.get('binding_count') == len(manifest['bindings']),
            'frozen manifest bindings invalid')
    mismatches = []
    for path_text, expected in manifest['bindings'].items():
        path = Path(path_text)
        actual = sha(path) if path.is_file() else 'MISSING'
        if actual != expected:
            mismatches.append((path_text, actual, expected))
    require(not mismatches, f'frozen file mismatch: {mismatches[:6]}')
    require(preflight.get('passed') is True and preflight.get('static_only') is True
            and preflight.get('engine_transitions') == 0
            and preflight.get('policy_action_calls') == 0
            and preflight.get('manifest_sha256') == sha(MANIFEST_PATH)
            and preflight.get('runner_sha256') == sha(HERE / 'run.py'),
            'static preflight receipt invalid')
    require(not any(path.exists() for path in (RESULTS_PATH, RECEIPT_PATH,
                                               RUN_MANIFEST_PATH, OWN_LOCK_PATH)),
            'outcome outputs already exist; static verification is pre-run only')
    sys.path.insert(0, str(ROOT))
    import runpy
    namespace = runpy.run_path(str(HERE / 'run.py'))
    checks = namespace['telemetry_checks']
    synthetic = {
        'candidate_telemetry': {
            'bridge_selected': 'source', 'bridge_errors': 0,
            'a44_kwa_wheat_zero_branch72': 'source',
            'a44_kwa_wheat_zero_key72': 'BRUNCH_SPOT|M8+|C<S|G0',
            'a44_kwa_wheat_zero_active72': True,
            'a44_kwa_wheat_zero_route72': '113535489',
            'a44_kwa_wheat_zero_turns': 647, 'a44_kwa_wheat_zero_errors': 0,
            'a44_kwa_wheat_zero_rival_wheat_plots72': 0,
            'a44_ghost_wheat_branch72': 'source',
            'a44_ghost_wheat_key72': 'BRUNCH_SPOT|M8+|C<S|G0',
            'a44_ghost_wheat_checked72': True,
            'a44_ghost_wheat_stock72': 9976,
            'a44_ghost_wheat_active72': False,
            'a44_ghost_wheat_route72': '',
            'a44_goose4_branch72': 'source', 'a44_goose4_key72': 'BRUNCH_SPOT|M8+|C<S|G0',
            'a44_goose4_route': '', 'a44_goose4_turns': 0, 'a44_goose4_errors': 0,
        }
    }
    row = {'expected_kwa_trigger': True, 'expected_ghost_trigger': False,
           'expected_branch': 'source',
           'expected_key': 'BRUNCH_SPOT|M8+|C<S|G0', 'expected_ghost_wheat': 9976,
           'expected_ghost_wheat_telemetry': 9976,
           'expected_parent_route': None, 'expected_kwa_wheat_plots': 0,
           'expected_kwa_wheat_plots_telemetry': 0}
    require(all(checks(synthetic, row).values()), 'synthetic positive telemetry check failed')
    require(not all(checks({}, row).values()), 'synthetic missing telemetry was accepted')
    return manifest, preflight


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('freeze', 'verify'):
        raise SystemExit('Usage: preflight.py freeze|verify')
    if sys.argv[1] == 'freeze':
        manifest, preflight = frozen_package()
        print(json.dumps({'frozen': True, 'candidate_sha256': CANDIDATE_SHA,
                          'binding_count': manifest['binding_count'],
                          'manifest_sha256': sha(MANIFEST_PATH),
                          'preflight_sha256': sha(PREFLIGHT_PATH)}, indent=2))
    else:
        manifest, preflight = verify_frozen()
        print(json.dumps({'verified': True, 'passed': preflight['passed'],
                          'candidate_sha256': CANDIDATE_SHA,
                          'binding_count': manifest['binding_count'],
                          'engine_transitions': preflight['engine_transitions']}, indent=2))


if __name__ == '__main__':
    main()
