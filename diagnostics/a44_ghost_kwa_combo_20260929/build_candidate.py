"""Assemble the hash-bound Ghost + Kwa overlay and its 58-game panel."""
from pathlib import Path
import gzip
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GHOST_PATH = ROOT / 'diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/candidate.py'
KWA_LAYER_PATH = ROOT / 'diagnostics/a44_kwa_wheat_zero_20260929/wheat_zero_layer.py'
GHOST_SHA = '228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767'
KWA_LAYER_SHA = '5f137649d797d95305854fcb2fc9bff2febdbde0e2522029f6797e5b68ff83d5'
BASE6 = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
CACHE_PATH = ROOT / 'diagnostics/stream_replay_io_20260928/initial_states.json'
ACTION_CACHE_SHA = 'f544b134e2ad51160e4d6ad7719b9f41ad6cc850a1a51162249ede1cba279968'
GHOST_PREFLIGHT_PATH = ROOT / 'diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/preflight.json'
KWA_PREFLIGHT_PATH = ROOT / 'diagnostics/a44_kwa_wheat_zero_20260929/preflight.json'
EXPECTED_FILES = {
    BASE6 / 'combined_results.json': '5463a0efa37aebad2c11559cbcd2c39bf2a9a63ec5b2279f409d6360c61ff40d',
    BASE6 / 'parent_panel.json': '7407b5f610457d2c00837a3c82e51ae2deaa225b20f2145e01dfaa92dba1db51',
    BASE6 / 'feature_rows.json': 'bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795',
    BASE6 / 'frozen_manifest.json': 'bb4e44f5d0038ce5fd24c2a9b935e7f341538abe484fef7aa819f38b6c6d900a',
    BASE6 / 'a44_controls.json': '91155aea3fa6ef6dc3cdc4ab97e5eaaab889909cb3acfaedc9377c593953cc55',
    CACHE_PATH: ACTION_CACHE_SHA,
    GHOST_PREFLIGHT_PATH: 'aefa68e3126e9eb6554cdfe426d023953e90524a72f8da49c4986240c6f801fc',
    ROOT / 'diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/frozen_manifest.json': '3a3cd881a7d2972e93c57dbc747ff16ca0c335b773b3ebafaa7f63eb440aa4d2',
    ROOT / 'diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/panel.json': '545c038fb0ab95530a53e58847e23233ddc3a0202fc36dae72f500ef185cbbf6',
    KWA_PREFLIGHT_PATH: 'dd44f46bb135f2ffb0b0fb894a001d737dce92c1f703d55fa14d3c57f5b1d89a',
    ROOT / 'diagnostics/a44_kwa_wheat_zero_20260929/manifest.json': '329176df031f017ad5ba6ac45edd3401b4891910d840c128ae3f731a48a07e3f',
}
GHOST_TARGETS = {'live-114288168'}
KWA_TARGETS = {'live-114227779'}
UNION_FIXTURE_ORDER = (
    'live-114227779', 'live-114236633', 'live-114255779',
    'live-114257327', 'live-114258293', 'live-114288168',
    'public-win-114209881', 'public-win-114221853', 'public-win-114245470',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_file(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def count_rival_wheat_plots(trace_path, expected_seat):
    with gzip.open(trace_path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            item = json.loads(line)
            if int(item.get('step', -1)) != 72:
                continue
            observation = item.get('observation') or {}
            if int(observation.get('step', -1)) != 72:
                raise ValueError(f'step-72 trace observation malformed: {trace_path}')
            player = int(observation.get('player', -1))
            if player != int(expected_seat):
                raise ValueError(f'step-72 trace seat differs: {trace_path}')
            rival = observation['farms'][1 - player]
            return sum(1 for row in rival['tiles'] for tile in row
                       if isinstance(tile, dict) and tile.get('crop') == 'WHEAT')
    raise ValueError(f'step-72 observation absent: {trace_path}')


def verify_action_tape(path, expected_digest):
    tape_doc = json.loads(gzip.decompress(Path(path).read_bytes()))
    tape = tape_doc.get('actions')
    if not isinstance(tape, list) or len(tape) != 719:
        raise ValueError(f'opponent action tape must contain 719 actions: {path}')
    digests = {
        hashlib.sha256(json.dumps(tape, sort_keys=sort_keys,
                                 separators=(',', ':')).encode('utf-8')).hexdigest()
        for sort_keys in (False, True)
    }
    if expected_digest not in digests:
        raise ValueError(f'opponent action digest changed: {path}')


def verify_cached_replay(cache_rows, fixture):
    path = fixture['source_replay_path']
    cached = cache_rows.get(path)
    if cached is None or cached.get('source_replay_sha256') != fixture['source_replay_sha256']:
        raise ValueError(f'fixture replay does not match the verified input cache: {path}')
    if sha(path) != cached.get('compressed_sha256'):
        raise ValueError(f'compressed replay changed after cache audit: {path}')


def main():
    candidate_path = HERE / 'candidate_v4.py'
    panel_path = HERE / 'panel_v4.json'
    if candidate_path.exists() or panel_path.exists():
        raise FileExistsError('candidate builder never overwrites outputs')
    if sha(GHOST_PATH) != GHOST_SHA or sha(KWA_LAYER_PATH) != KWA_LAYER_SHA:
        raise ValueError('standalone candidate/layer hash changed')
    for path, expected in EXPECTED_FILES.items():
        if sha(path) != expected:
            raise ValueError(f'fixed input hash changed: {path}')

    ghost_bytes = GHOST_PATH.read_bytes()
    kwa_bytes = KWA_LAYER_PATH.read_bytes()
    separator = b'' if ghost_bytes.endswith(b'\n') else b'\n'
    candidate_bytes = ghost_bytes + separator + b'\n' + kwa_bytes
    source = candidate_bytes.decode('utf-8')
    compile(source, str(candidate_path), 'exec')
    tree = ast.parse(source)
    rules = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == '_A44_GOOSE4_RULES'
                for target in node.targets):
            rules = ast.literal_eval(node.value)
            break
    if rules is None or any(key.startswith('BRUNCH_SPOT|') for key in rules):
        raise ValueError('Ghost Goose4 route selector could overwrite the outer Kwa BRUNCH commit')
    candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()

    parent_panel = json_file(BASE6 / 'parent_panel.json')
    combined = json_file(BASE6 / 'combined_results.json')
    feature_doc = json_file(BASE6 / 'feature_rows.json')
    cache_doc = json_file(CACHE_PATH)
    if not cache_doc.get('complete') or cache_doc.get('fixture_count') != 104:
        raise ValueError('verified replay cache is incomplete')
    cache_rows = {row['source_replay_path']: row for row in cache_doc['replays']}
    ghost_preflight = json_file(GHOST_PREFLIGHT_PATH)
    kwa_preflight = json_file(KWA_PREFLIGHT_PATH)
    fixture_rows = {row['fixture_id']: row for row in parent_panel['fixtures']}
    baseline_rows = {(row['fixture_id'], int(row['candidate_seat'])): row
                     for row in combined['games']}
    features = {(row['fixture_id'], int(row['seat'])): row for row in feature_doc['rows']}
    ghost_rows = {(row['fixture_id'], int(row['seat'])): row
                  for row in ghost_preflight['feature_census']['all_feature_decisions']}
    if (len(fixture_rows) != 104 or len(baseline_rows) != 208
            or len(features) != 208 or len(ghost_rows) != 208):
        raise ValueError('full 104-fixture/208-seat parent census is malformed')
    top20_order = tuple(row['fixture_id'] for row in parent_panel['fixtures']
                        if row['panel'] == 'top20')
    if len(top20_order) != 20 or len(set(top20_order)) != 20:
        raise ValueError('frozen top20 fixture census is not exactly 20 rows')
    if set(top20_order) & set(UNION_FIXTURE_ORDER):
        raise ValueError('top20 fixtures unexpectedly overlap the union loss panel')
    fixture_order = top20_order + UNION_FIXTURE_ORDER
    if len(fixture_order) != 29 or len(set(fixture_order)) != 29:
        raise ValueError('combined panel fixture membership is malformed')

    kwa_triggers = {(row['fixture_id'], int(row['seat'])) for row in kwa_preflight['trigger_rows']}
    kwa_controls = {(row['fixture_id'], int(row['seat'])): row
                    for row in kwa_preflight['same_leaf_winning_control_rows']}
    ghost_triggers = {(row['fixture_id'], seat) for row in ghost_rows.values()
                      if row['triggered'] for seat in (0,)}
    # The Ghost receipt records seats directly; rebuild the full key set below.
    ghost_triggers = {(row['fixture_id'], int(row['seat'])) for row in ghost_rows.values()
                      if row['triggered']}
    if kwa_triggers != {(fid, seat) for fid in KWA_TARGETS for seat in (0, 1)}:
        raise ValueError('Kwa activation census changed')
    if ghost_triggers != {(fid, seat) for fid in GHOST_TARGETS for seat in (0, 1)}:
        raise ValueError('Ghost activation census changed')
    if kwa_triggers & ghost_triggers:
        raise ValueError('Kwa and Ghost activation predicates overlap')
    brunch_rows = {key for key, row in features.items()
                   if row['bridge_branch'] == 'source'
                   and row['rule_key'] == 'BRUNCH_SPOT|M8+|C<S|G0'}
    if brunch_rows != kwa_triggers | set(kwa_controls):
        raise ValueError('Kwa trigger/control rows do not cover every matching BRUNCH census row')
    if any(row['triggered'] and row['panel'] == 'top20' for row in ghost_rows.values()):
        raise ValueError('Ghost trigger entered the frozen top20 panel')
    if any(row['panel'] == 'top20' for row in kwa_preflight['trigger_rows']):
        raise ValueError('Kwa trigger entered the frozen top20 panel')

    games = []
    for fixture_id in fixture_order:
        fixture = fixture_rows[fixture_id]
        for seat in (0, 1):
            key = (fixture_id, seat)
            feature = features[key]
            ghost = ghost_rows[key]
            baseline = baseline_rows[key]
            expected_kwa = key in kwa_triggers
            expected_ghost = key in ghost_triggers
            if feature['bridge_branch'] != ghost['bridge_branch']:
                raise ValueError(f'feature and Ghost branch census differ at {key}')
            if expected_kwa and not (feature['bridge_branch'] == 'source'
                                     and feature['rule_key'] == 'BRUNCH_SPOT|M8+|C<S|G0'):
                raise ValueError(f'Kwa trigger/key mismatch at {key}')
            if expected_ghost != bool(ghost['triggered']):
                raise ValueError(f'Ghost trigger mismatch at {key}')
            if fixture['panel'] not in ('top20', 'loss30', 'public-win'):
                raise ValueError(f'unexpected panel class for {key}: {fixture["panel"]}')
            if fixture['panel'] == 'top20' and (expected_kwa or expected_ghost):
                raise ValueError(f'route trigger entered the frozen top20 panel: {key}')
            if baseline['candidate_sha256'] != 'c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632':
                raise ValueError(f'6d combined row has an unexpected reused candidate at {key}')
            controls = {name: baseline[name] for name in (
                'result', 'candidate_reward', 'opponent_reward', 'margin',
                'candidate_status', 'opponent_status', 'frames', 'candidate_errors')}
            known_kwa = kwa_controls.get(key)
            expected_kwa_plots = (0 if expected_kwa else
                                  int(known_kwa['rival_wheat_plots']) if known_kwa else None)
            trace_path = Path(feature['trace_path'])
            if not trace_path.is_file() or sha(trace_path) != feature['trace_sha256']:
                raise ValueError(f'feature trace is missing or changed at {key}')
            computed_kwa_plots = count_rival_wheat_plots(trace_path, seat)
            if expected_kwa_plots is not None and expected_kwa_plots != computed_kwa_plots:
                raise ValueError(f'Kwa plot count differs from upstream census at {key}')
            expected_kwa_plots = computed_kwa_plots
            fixture_metadata = fixture
            for path_field, hash_field in (
                    ('source_replay_path', 'source_replay_sha256'),
                    ('source_action_tape_path', 'source_opponent_action_sha256')):
                source_path = Path(fixture_metadata[path_field])
                if not source_path.is_file():
                    raise ValueError(f'fixture input is missing or changed: {source_path}')
                if path_field == 'source_replay_path':
                    verify_cached_replay(cache_rows, fixture_metadata)
                else:
                    verify_action_tape(source_path, fixture_metadata[hash_field])
            games.append({
                'fixture_id': fixture_id,
                'candidate_seat': seat,
                'panel': fixture['panel'],
                'expected_kwa_trigger': expected_kwa,
                'expected_ghost_trigger': expected_ghost,
                'expected_branch': feature['bridge_branch'],
                'expected_key': feature['rule_key'],
                'expected_parent_route': ghost['parent_selected_route'],
                'expected_ghost_wheat': int(ghost['step72_public_wheat']),
                'expected_kwa_wheat_plots': expected_kwa_plots,
                'expected_ghost_wheat_telemetry': (
                    int(ghost['step72_public_wheat'])
                    if feature['bridge_branch'] == 'source' else None),
                'expected_kwa_wheat_plots_telemetry': (
                    expected_kwa_plots if feature['bridge_branch'] == 'source' else None),
                'baseline_6d': controls,
                'baseline_reused_candidate_sha256': baseline['candidate_sha256'],
                'feature_trace_path': feature['trace_path'],
                'feature_trace_sha256': feature['trace_sha256'],
                'source_fixture': fixture,
            })

    if len(games) != 58 or sum(row['expected_kwa_trigger'] for row in games) != 2 \
            or sum(row['expected_ghost_trigger'] for row in games) != 2:
        raise ValueError('combined outcome panel must have 58 seats and four activations')
    top20_games = [row for row in games if row['panel'] == 'top20']
    top20_baseline = {}
    for row in top20_games:
        top20_baseline.setdefault(row['fixture_id'], []).append(row['baseline_6d']['result'])
    top20_wins = sum(len(results) == 2 and all(value == 'win' for value in results)
                     for results in top20_baseline.values())
    if len(top20_games) != 40 or len(top20_baseline) != 20 or top20_wins < 18:
        raise ValueError('6d baseline does not meet the frozen top20 90% threshold')
    panel = {
        'schema': 'a44-ghost-kwa-combined-fixed-panel-v2',
        'builder_sha256': sha(__file__),
        'candidate_sha256': candidate_sha,
        'ghost_candidate_sha256': GHOST_SHA,
        'kwa_layer_sha256': KWA_LAYER_SHA,
        'parent_6d_candidate_sha256': '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9',
        'parent_6d_combined_results_sha256': sha(BASE6 / 'combined_results.json'),
        'full_fixture_count': 104,
        'full_seat_count': 208,
        'fixture_count': len(fixture_order),
        'game_count': len(games),
        'fixture_order': list(fixture_order),
        'top20_fixture_count': 20,
        'top20_game_count': 40,
        'top20_baseline_winning_sweeps': top20_wins,
        'top20_goal_metric': 'both-seat fixture sweep',
        'top20_min_winning_sweeps': 18,
        'expected_kwa_trigger_seats': 2,
        'expected_ghost_trigger_seats': 2,
        'expected_control_seats': 54,
        'games': games,
    }
    # Write only after every source, panel, fixture, and trace check has passed.
    with candidate_path.open('xb') as out:
        out.write(candidate_bytes)
    with panel_path.open('x', encoding='utf-8', newline='\n') as out:
        out.write(json.dumps(panel, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'candidate_sha256': candidate_sha,
                      'candidate_bytes': len(candidate_bytes),
                      'ghost_triggers': sorted(ghost_triggers),
                      'kwa_triggers': sorted(kwa_triggers),
                      'overlap': sorted(kwa_triggers & ghost_triggers),
                      'game_count': len(games),
                      'top20_fixture_count': len(top20_baseline),
                      'top20_baseline_winning_sweeps': top20_wins,
                      'panel_sha256': sha(panel_path)}, indent=2))


if __name__ == '__main__':
    main()
