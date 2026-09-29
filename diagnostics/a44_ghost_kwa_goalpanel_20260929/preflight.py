"""Static freeze and verification for the full frozen loss30 goal run."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
COMBO = ROOT / 'diagnostics/a44_ghost_kwa_combo_20260929'
COMBO_RUN = COMBO / 'outcome_run_20260929'
COMBO_PANEL = COMBO / 'panel_v4.json'
TOP20_RECEIPT = COMBO_RUN / 'outcome_receipt.json'
BASE6 = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
GHOST = ROOT / 'diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929'
KWA = ROOT / 'diagnostics/a44_kwa_wheat_zero_20260929'
CACHE = ROOT / 'diagnostics/stream_replay_io_20260928'
NATIVE = ROOT / 'diagnostics/physical_route_rollout_20260928'
LOCK_HELPER = ROOT / 'diagnostics/local_target_20260928/run_lock.py'
CANDIDATE = COMBO / 'candidate_v4.py'
PANEL_PATH = HERE / 'panel.json'
MANIFEST_PATH = HERE / 'frozen_manifest.json'
PREFLIGHT_PATH = HERE / 'static_preflight.json'
RESULTS_PATH = HERE / 'outcomes.jsonl'
RECEIPT_PATH = HERE / 'outcome_receipt.json'
RUN_MANIFEST_PATH = HERE / 'run_manifest.json'
OWN_LOCK_PATH = HERE / 'run.lock'
SHARED_LOCK_PATH = ROOT / 'diagnostics/.shared_game_run.lock'
CANDIDATE_SHA = '7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2'
PANEL_SHA = 'dd11014aa8b9423a43a5f8fd6bf1af592881b940845d032c406a8d86cc1e6ea7'
COMBO_PANEL_SHA = '8f9eec84d361de731d95de88d76c5e78bf2c6bab58012a376daa5bdf466d15bd'
COMBO_MANIFEST_SHA = '277931bcc49350690a160e465ba8d96a0a4feb7c5be2af8de039bf60808723c9'
TOP20_RECEIPT_SHA = 'c576c106f4e40b009fba58cc2642d73c70571880bd940f75ca3b128a85cc51c9'
TOP20_LEDGER_SHA = 'c31cd08a2aa8f8090a30fc3dd94d8ccd9b725a326326a91a5ffa478b31f8b2d3'
TOP20_RUN_MANIFEST_SHA = '957bc167e820c5265bd181a1c38a6707fdfc1a32ab8f3589fd7733566ae6957d'
TOP20_PREFLIGHT_SHA = '6c880aa593bafbb72a5d1beb9cd459fe76c2eca943bd2e7379c7f51bb31e0834'
BASE6_RESULTS_SHA = '5463a0efa37aebad2c11559cbcd2c39bf2a9a63ec5b2279f409d6360c61ff40d'
BASE6_PANEL_SHA = '7407b5f610457d2c00837a3c82e51ae2deaa225b20f2145e01dfaa92dba1db51'
BASE6_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
BASE6_FEATURES_SHA = 'bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795'
GHOST_CANDIDATE_SHA = '228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767'
GHOST_PREFLIGHT_SHA = 'aefa68e3126e9eb6554cdfe426d023953e90524a72f8da49c4986240c6f801fc'
GHOST_MANIFEST_SHA = '3a3cd881a7d2972e93c57dbc747ff16ca0c335b773b3ebafaa7f63eb440aa4d2'
GHOST_PANEL_SHA = '545c038fb0ab95530a53e58847e23233ddc3a0202fc36dae72f500ef185cbbf6'
GHOST_RECEIPT_SHA = '510339d20aace4317f7dfc4330b7a8f4e59d1edcc5fd458f474fddefb3c702f8'
GHOST_LEDGER_SHA = 'a060e1441ee0ac37e8e83c3e81203797fecc78ad0d306e27ca98a21cbcf6831c'
KWA_CANDIDATE_SHA = '36f1a351c4b85b62d7c5fb07489927821d98823c57d0e7131e19eb186951a54e'
KWA_LAYER_SHA = '5f137649d797d95305854fcb2fc9bff2febdbde0e2522029f6797e5b68ff83d5'
KWA_PREFLIGHT_SHA = 'dd44f46bb135f2ffb0b0fb894a001d737dce92c1f703d55fa14d3c57f5b1d89a'
KWA_MANIFEST_SHA = '329176df031f017ad5ba6ac45edd3401b4891910d840c128ae3f731a48a07e3f'
KWA_RECEIPT_SHA = '940a16e49362dd6a7b1f07a14602eb41c3949d74b8e1ccdd975137c88a4baee3'
KWA_LEDGER_SHA = 'b384008eee6a94522b85216d066468f3335b5c1ad950ed731ba7fc9f94cdf2cc'
ACTION_CACHE_SHA = 'f544b134e2ad51160e4d6ad7719b9f41ad6cc850a1a51162249ede1cba279968'
REUSED_SHA = 'c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632'
UNION_KWA = ('live-114227779', 0)
UNION_GHOST = ('live-114288168', 0)
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


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_step72(trace_path, seat):
    with gzip.open(trace_path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            item = json.loads(line)
            if int(item.get('step', -1)) != 72:
                continue
            obs = item.get('observation') or {}
            require(int(obs.get('step', -1)) == 72
                    and int(obs.get('player', -1)) == int(seat),
                    f'step-72 trace identity changed: {trace_path}')
            rival = obs['farms'][1 - int(seat)]
            plots = sum(1 for row in rival['tiles'] for tile in row
                        if isinstance(tile, dict) and tile.get('crop') == 'WHEAT')
            return plots, int(obs['market']['inventory']['WHEAT'])
    raise AssertionError(f'step-72 observation missing: {trace_path}')


def verify_action_tape(path, expected):
    doc = json.loads(gzip.decompress(Path(path).read_bytes()))
    actions = doc.get('actions')
    require(isinstance(actions, list) and len(actions) == 719,
            f'action tape length changed: {path}')
    digests = {hashlib.sha256(json.dumps(
        actions, sort_keys=sort_keys, separators=(',', ':')).encode('utf-8')).hexdigest()
        for sort_keys in (False, True)}
    require(expected in digests, f'action tape digest changed: {path}')


def valid_baseline_provenance(row):
    if row.get('candidate_sha256') == BASE6_SHA:
        return row.get('decision_equivalence_reuse') is not True
    return (row.get('candidate_sha256') == REUSED_SHA
            and row.get('decision_equivalence_reuse') is True
            and row.get('reused_parent_candidate_sha256') == REUSED_SHA)


def add_binding(bindings, path, expected=None):
    path = Path(path).resolve()
    require(path.is_file(), f'missing frozen input: {path}')
    actual = sha(path)
    if expected is not None:
        require(actual == expected, f'hash mismatch for {path}: {actual} != {expected}')
    prior = bindings.setdefault(str(path), actual)
    require(prior == actual, f'conflicting binding for {path}')


def prior_top20_summary(panel):
    receipt = load(TOP20_RECEIPT)
    combo_panel = load(COMBO / 'panel_v4.json')
    top_ids = {row['fixture_id'] for row in combo_panel['games']
               if row['panel'] == 'top20'}
    rows = [row for row in receipt['games'] if row['fixture_id'] in top_ids]
    by_fixture = {}
    for row in rows:
        by_fixture.setdefault(row['fixture_id'], []).append(row)
        require(row['candidate_sha256'] == CANDIDATE_SHA
                and row['clean_done_done_720'] is True
                and row['telemetry_passed'] is True
                and row['control_exact'] is True,
                f'top20 source game failed for {row["fixture_id"]}/{row["candidate_seat"]}')
    sweeps = sum(len(values) == 2
                 and {int(row['candidate_seat']) for row in values} == {0, 1}
                 and all(row['actual'].get('result') == 'win' for row in values)
                 for values in by_fixture.values())
    require(len(rows) == 40 and len(by_fixture) == 20 and sweeps == 19
            and sweeps >= int(panel['top20_min_winning_sweeps']),
            'top20 reference receipt does not meet the frozen goal')
    return receipt, rows, sweeps


def verify_inputs():
    require(sha(CANDIDATE) == CANDIDATE_SHA, 'combined candidate hash changed')
    require(sha(PANEL_PATH) == PANEL_SHA, 'loss30 panel hash changed')
    panel = load(PANEL_PATH)
    require(panel.get('schema') == 'a44-ghost-kwa-full-goal-panel-v1'
            and panel.get('candidate_sha256') == CANDIDATE_SHA
            and panel.get('builder_sha256') == sha(HERE / 'build_panel.py'),
            'candidate or builder lineage mismatch')
    require(panel.get('game_count') == 60 and panel.get('loss30_fixture_count') == 30
            and panel.get('loss30_game_count') == 60
            and panel.get('top20_fixture_count') == 20
            and panel.get('top20_min_winning_sweeps') == 18
            and panel.get('loss30_min_winning_sweeps') == 27
            and panel.get('expected_control_seats') == 56,
            'full goal thresholds or fixture counts changed')
    require(panel.get('top20_reference_panel_sha256') == COMBO_PANEL_SHA
            and panel.get('top20_reference_receipt_sha256') == TOP20_RECEIPT_SHA,
            'top20 result reference changed')
    require(panel.get('top20_reference_preflight_sha256') == TOP20_PREFLIGHT_SHA,
            'top20 static preflight reference changed')
    top20_receipt, _, top20_sweeps = prior_top20_summary(panel)
    require(top20_receipt.get('passed') is True, 'top20 run receipt did not pass')

    parent_panel = load(BASE6 / 'parent_panel.json')
    combined = load(BASE6 / 'combined_results.json')
    features_doc = load(BASE6 / 'feature_rows.json')
    cache_doc = load(CACHE / 'initial_states.json')
    ghost_preflight = load(GHOST / 'preflight.json')
    kwa_preflight = load(KWA / 'preflight.json')
    require(sha(BASE6 / 'combined_results.json') == BASE6_RESULTS_SHA
            and sha(BASE6 / 'parent_panel.json') == BASE6_PANEL_SHA
            and sha(BASE6 / 'candidate.py') == BASE6_SHA
            and sha(BASE6 / 'feature_rows.json') == BASE6_FEATURES_SHA
            and sha(CACHE / 'initial_states.json') == ACTION_CACHE_SHA,
            'exact 6d panel input changed')
    require(combined.get('complete') is True and combined.get('fixed_tape_only') is True
            and combined.get('candidate_sha256') == BASE6_SHA
            and len(combined.get('games', [])) == 208,
            '6d baseline is incomplete')
    fixtures = {row['fixture_id']: row for row in parent_panel['fixtures']}
    loss_order = [row['fixture_id'] for row in parent_panel['fixtures']
                  if row['panel'] == 'loss30']
    require(panel.get('fixture_order') == loss_order and len(loss_order) == 30,
            'loss30 membership or order changed')
    baseline = {(row['fixture_id'], int(row['candidate_seat'])): row
                for row in combined['games']}
    features = {(row['fixture_id'], int(row['seat'])): row for row in features_doc['rows']}
    ghost_rows = {(row['fixture_id'], int(row['seat'])): row
                  for row in ghost_preflight['feature_census']['all_feature_decisions']}
    kwa_targets = {(row['fixture_id'], int(row['seat']))
                   for row in kwa_preflight['trigger_rows']}
    ghost_targets = {(fid, seat) for (fid, seat), row in ghost_rows.items()
                     if row.get('triggered')}
    require(len(baseline) == 208 and len(features) == 208 and len(ghost_rows) == 208,
            'full 208-seat source census is incomplete')
    require(kwa_targets == {('live-114227779', 0), ('live-114227779', 1)}
            and ghost_targets == {('live-114288168', 0), ('live-114288168', 1)},
            'full-corpus activation census changed')
    require(kwa_preflight.get('panel_counts') == {
                'loss30': 60, 'public-win': 108, 'top20': 40}
            and kwa_preflight.get('top20_trigger_count') == 0
            and kwa_preflight.get('public_win_trigger_count') == 0,
            'Kwa full-corpus static census changed')
    cache = load(CACHE / 'initial_states.json')
    replay_cache = {row['source_replay_path']: row for row in cache['replays']}
    rows = panel['games']
    expected_order = [(fid, seat) for fid in loss_order for seat in (0, 1)]
    actual_order = [(row['fixture_id'], int(row['candidate_seat'])) for row in rows]
    require(actual_order == expected_order, '60-row loss panel ordering changed')
    require(sum(bool(row['expected_kwa_trigger']) for row in rows) == 2
            and sum(bool(row['expected_ghost_trigger']) for row in rows) == 2
            and sum(not row['expected_kwa_trigger'] and not row['expected_ghost_trigger']
                    for row in rows) == 56,
            'activation or control counts changed')
    baseline_sweeps = {}
    for row in rows:
        key = (row['fixture_id'], int(row['candidate_seat']))
        base = baseline.get(key)
        require(base is not None and valid_baseline_provenance(base),
                f'6d baseline provenance changed at {key}')
        require({name: row['baseline_6d'].get(name) for name in CONTROL_FIELDS}
                == {name: base.get(name) for name in CONTROL_FIELDS},
                f'panel baseline result changed at {key}')
        fixture = fixtures[row['fixture_id']]
        require(fixture == row['source_fixture'], f'fixture metadata changed at {key}')
        feature = features[key]
        ghost = ghost_rows[key]
        require(row['expected_branch'] == feature['bridge_branch']
                and row['expected_branch'] == ghost['bridge_branch']
                and row['expected_key'] == feature['rule_key']
                and row['expected_key'] == ghost['step72_public_key']
                and bool(row['expected_ghost_trigger']) == bool(ghost['triggered']),
                f'feature census changed at {key}')
        trace = Path(row['feature_trace_path'])
        require(trace.is_file() and sha(trace) == row['feature_trace_sha256'],
                f'trace missing or changed at {key}')
        plots, stock = read_step72(trace, int(row['candidate_seat']))
        require(plots == row['expected_kwa_wheat_plots']
                and stock == row['expected_ghost_wheat'],
                f'trace state changed at {key}')
        source_branch = row['expected_branch'] == 'source'
        require(row['expected_kwa_wheat_plots_telemetry'] == (plots if source_branch else None)
                and row['expected_ghost_wheat_telemetry'] == (stock if source_branch else None),
                f'telemetry expectation changed at {key}')
        replay = fixture['source_replay_path']
        cached = replay_cache.get(replay)
        require(cached is not None
                and cached['source_replay_sha256'] == fixture['source_replay_sha256']
                and sha(replay) == cached['compressed_sha256'],
                f'replay cache identity changed at {key}')
        verify_action_tape(fixture['source_action_tape_path'],
                           fixture['source_opponent_action_sha256'])
        if int(row['candidate_seat']) == 0:
            baseline_sweeps[row['fixture_id']] = base['result'] == 'win'
        else:
            baseline_sweeps[row['fixture_id']] = (
                baseline_sweeps[row['fixture_id']] and base['result'] == 'win')
    require(sum(baseline_sweeps.values()) == 22
            and panel.get('loss30_parent_6d_winning_sweeps') == 22,
            '6d loss30 baseline sweep count changed')

    combo_manifest = load(COMBO_RUN / 'frozen_manifest.json')
    require(sha(COMBO_RUN / 'frozen_manifest.json') == COMBO_MANIFEST_SHA
            and len(combo_manifest.get('bindings', {})) == 147,
            'prior composition freeze manifest changed')
    mismatches = []
    for path_text, expected in combo_manifest['bindings'].items():
        path = Path(path_text)
        actual = sha(path) if path.is_file() else 'MISSING'
        if actual != expected:
            mismatches.append((path_text, actual, expected))
    require(not mismatches, f'prior composition freeze no longer verifies: {mismatches[:5]}')

    # Re-run the frozen telemetry predicate on both previously completed target pairs.
    telemetry_checks = runpy.run_path(str(COMBO_RUN / 'run.py'))['telemetry_checks']
    previous_panel = load(COMBO / 'panel_v4.json')
    previous_by_key = {(row['fixture_id'], int(row['candidate_seat'])): row
                       for row in previous_panel['games']}
    previous_games = {(row['fixture_id'], int(row['candidate_seat'])): row
                      for row in top20_receipt['games']}
    for target in ({('live-114227779', seat) for seat in (0, 1)}
                   | {('live-114288168', seat) for seat in (0, 1)}):
        source_row = previous_by_key[target]
        result = previous_games[target]
        require(result['telemetry_passed'] is True
                and all(telemetry_checks(result['actual'], source_row).values()),
                f'previous target telemetry does not verify at {target}')
    return panel, top20_sweeps


def collect_bindings(panel):
    bindings = {}
    combo_manifest = load(COMBO_RUN / 'frozen_manifest.json')
    for path_text, expected in combo_manifest['bindings'].items():
        add_binding(bindings, path_text, expected)
    fixed = [
        (COMBO_RUN / 'frozen_manifest.json', COMBO_MANIFEST_SHA),
        (COMBO / 'candidate_v4.py', CANDIDATE_SHA),
        (COMBO / 'panel_v4.json', COMBO_PANEL_SHA),
        (COMBO_RUN / 'outcome_receipt.json', TOP20_RECEIPT_SHA),
        (COMBO_RUN / 'outcomes.jsonl', TOP20_LEDGER_SHA),
        (COMBO_RUN / 'run_manifest.json', TOP20_RUN_MANIFEST_SHA),
        (COMBO_RUN / 'static_preflight.json', TOP20_PREFLIGHT_SHA),
        (BASE6 / 'candidate.py', BASE6_SHA),
        (BASE6 / 'combined_results.json', BASE6_RESULTS_SHA),
        (BASE6 / 'parent_panel.json', BASE6_PANEL_SHA),
        (BASE6 / 'feature_rows.json', BASE6_FEATURES_SHA),
        (BASE6 / 'frozen_manifest.json', 'bb4e44f5d0038ce5fd24c2a9b935e7f341538abe484fef7aa819f38b6c6d900a'),
        (BASE6 / 'a44_controls.json', '91155aea3fa6ef6dc3cdc4ab97e5eaaab889909cb3acfaedc9377c593953cc55'),
        (GHOST / 'candidate.py', GHOST_CANDIDATE_SHA),
        (GHOST / 'preflight.json', GHOST_PREFLIGHT_SHA),
        (GHOST / 'frozen_manifest.json', GHOST_MANIFEST_SHA),
        (GHOST / 'panel.json', GHOST_PANEL_SHA),
        (GHOST / 'outcome_run_v2_20260929/run_receipt.json', GHOST_RECEIPT_SHA),
        (GHOST / 'outcome_run_v2_20260929/candidate.jsonl', GHOST_LEDGER_SHA),
        (KWA / 'candidate.py', KWA_CANDIDATE_SHA),
        (KWA / 'wheat_zero_layer.py', KWA_LAYER_SHA),
        (KWA / 'preflight.json', KWA_PREFLIGHT_SHA),
        (KWA / 'manifest.json', KWA_MANIFEST_SHA),
        (KWA / 'runs/six_game_run_001/outcome_receipt.json', KWA_RECEIPT_SHA),
        (KWA / 'runs/six_game_run_001/outcomes.jsonl', KWA_LEDGER_SHA),
        (CACHE / 'initial_states.json', ACTION_CACHE_SHA),
        (CACHE / 'fast_game_cached.py', 'a57d12659af613512a61ac02aaa43d4c5ae4f4d8f2c5c02d3ed4ac6eafa2a38e'),
        (CACHE / 'cached_input.py', 'e2aaefda623775c9c7d56304271c827ecd6e56cc109e5c6d8b35aeb458268aa1'),
        (CACHE / 'cached_helper_manifest.json', '24c526c44382bf9bd24139bbb20d3c4e75aaf3ee24f73609cf703c1839ad4173'),
        (CACHE / 'cached_helper_parity.json', 'd4971428f0141301c7f3ebe6c2ee42b66c3a5f9faef202e7e22a0fb041958fa7'),
        (NATIVE / 'native_core.py', '5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795'),
        (NATIVE / 'check.py', 'f51b49dd2c627337136365603e4d0923c9f3e77f28bc8c77d08f608cba48e4a6'),
        (NATIVE / 'parity.json', '26ebd915525fbb4285387364deb13c3e28da7509708dfc9b7f419978cc40e273'),
        (LOCK_HELPER, '6ae76386c4bfda83a5efff6c0772ad22a4480155126ac9f0ed5616ec68c0d219'),
        (HERE / 'build_panel.py', None),
        (HERE / 'PLAN.md', None),
        (HERE / 'preflight.py', None),
        (HERE / 'run.py', None),
        (PANEL_PATH, PANEL_SHA),
    ]
    for path, expected in fixed:
        add_binding(bindings, path, expected)
    cache = load(CACHE / 'initial_states.json')
    replay_cache = {row['source_replay_path']: row for row in cache['replays']}
    for row in panel['games']:
        add_binding(bindings, row['feature_trace_path'], row['feature_trace_sha256'])
        fixture = row['source_fixture']
        cached = replay_cache[fixture['source_replay_path']]
        add_binding(bindings, fixture['source_replay_path'], cached['compressed_sha256'])
        add_binding(bindings, fixture['source_action_tape_path'])
    return bindings


def frozen_package():
    panel, top20_sweeps = verify_inputs()
    bindings = collect_bindings(panel)
    require(not MANIFEST_PATH.exists() and not PREFLIGHT_PATH.exists(),
            'freeze outputs exist; preflight never overwrites')
    require(not any(path.exists() for path in (
        RESULTS_PATH, RECEIPT_PATH, RUN_MANIFEST_PATH, OWN_LOCK_PATH)),
        'run outputs already exist; refusing to freeze over an attempted run')
    manifest = {
        'schema': 'a44-ghost-kwa-full-goal-frozen-manifest-v1',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'complete': True,
        'diagnostic_only': True,
        'fixed_tape_only': True,
        'reactive_validation': False,
        'promotion': False,
        'candidate_sha256': CANDIDATE_SHA,
        'panel_sha256': PANEL_SHA,
        'parent_6d_candidate_sha256': BASE6_SHA,
        'top20_reference_receipt_sha256': TOP20_RECEIPT_SHA,
        'top20_reference_preflight_sha256': TOP20_PREFLIGHT_SHA,
        'top20_winning_sweeps': top20_sweeps,
        'loss30_goal_sweeps': 27,
        'loss30_baseline_sweeps': 22,
        'binding_count': len(bindings),
        'bindings': bindings,
        'builder_sha256': sha(HERE / 'build_panel.py'),
        'preflight_sha256': sha(HERE / 'preflight.py'),
        'runner_sha256': sha(HERE / 'run.py'),
        'plan_sha256': sha(HERE / 'PLAN.md'),
        'game_count': 60,
        'fixture_count': 30,
        'expected_kwa_activations': 2,
        'expected_ghost_activations': 2,
        'expected_controls': 56,
        'resume_allowed': False,
    }
    with MANIFEST_PATH.open('x', encoding='utf-8', newline='\n') as out:
        out.write(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    receipt = {
        'schema': 'a44-ghost-kwa-full-goal-static-preflight-v1',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'passed': True,
        'static_only': True,
        'engine_transitions': 0,
        'policy_action_calls': 0,
        'outcome_games_run': 0,
        'candidate_sha256': CANDIDATE_SHA,
        'panel_sha256': PANEL_SHA,
        'manifest_sha256': sha(MANIFEST_PATH),
        'runner_sha256': sha(HERE / 'run.py'),
        'binding_count': len(bindings),
        'top20_reference_sweeps': top20_sweeps,
        'loss30_fixture_count': 30,
        'loss30_games': 60,
        'kwa_trigger_seats': 2,
        'ghost_trigger_seats': 2,
        'control_seats': 56,
        'evidence_limit': 'Static verification only; no candidate game was run in this package.',
    }
    with PREFLIGHT_PATH.open('x', encoding='utf-8', newline='\n') as out:
        out.write(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
    return manifest, receipt


def verify_frozen():
    manifest = load(MANIFEST_PATH)
    receipt = load(PREFLIGHT_PATH)
    require(manifest.get('complete') is True and manifest.get('fixed_tape_only') is True
            and manifest.get('promotion') is False
            and manifest.get('candidate_sha256') == CANDIDATE_SHA
            and manifest.get('panel_sha256') == PANEL_SHA,
            'frozen manifest fields changed')
    require(len(manifest.get('bindings', {})) == manifest.get('binding_count'),
            'frozen bindings are malformed')
    mismatches = []
    for path_text, expected in manifest['bindings'].items():
        path = Path(path_text)
        actual = sha(path) if path.is_file() else 'MISSING'
        if actual != expected:
            mismatches.append((path_text, actual, expected))
    require(not mismatches, f'frozen input hash mismatch: {mismatches[:5]}')
    require(manifest.get('builder_sha256') == sha(HERE / 'build_panel.py')
            and manifest.get('preflight_sha256') == sha(HERE / 'preflight.py')
            and manifest.get('runner_sha256') == sha(HERE / 'run.py')
            and manifest.get('plan_sha256') == sha(HERE / 'PLAN.md'),
            'builder, preflight, runner, or plan changed')
    require(receipt.get('passed') is True and receipt.get('static_only') is True
            and receipt.get('engine_transitions') == 0
            and receipt.get('policy_action_calls') == 0
            and receipt.get('outcome_games_run') == 0
            and receipt.get('manifest_sha256') == sha(MANIFEST_PATH)
            and receipt.get('runner_sha256') == sha(HERE / 'run.py'),
            'static preflight receipt is incomplete')
    require(not any(path.exists() for path in (
        RESULTS_PATH, RECEIPT_PATH, RUN_MANIFEST_PATH, OWN_LOCK_PATH)),
        'full loss30 outputs already exist; no resume or overwrite is allowed')
    return manifest, receipt


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('freeze', 'verify'):
        raise SystemExit('Usage: preflight.py freeze|verify')
    if sys.argv[1] == 'freeze':
        manifest, receipt = frozen_package()
        print(json.dumps({'frozen': True, 'candidate_sha256': CANDIDATE_SHA,
                          'binding_count': manifest['binding_count'],
                          'manifest_sha256': sha(MANIFEST_PATH),
                          'preflight_sha256': sha(PREFLIGHT_PATH)}, indent=2))
    else:
        manifest, receipt = verify_frozen()
        panel, sweeps = verify_inputs()
        print(json.dumps({'verified': True, 'passed': receipt['passed'],
                          'candidate_sha256': CANDIDATE_SHA,
                          'binding_count': manifest['binding_count'],
                          'loss30_games': len(panel['games']),
                          'top20_reference_sweeps': sweeps,
                          'engine_transitions': receipt['engine_transitions']}, indent=2))


if __name__ == '__main__':
    main()
