"""Build the full saved loss30 panel for the frozen Ghost + Kwa candidate."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
COMBO = ROOT / 'diagnostics/a44_ghost_kwa_combo_20260929'
COMBO_RUN = COMBO / 'outcome_run_20260929'
BASE6 = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
GHOST = ROOT / 'diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929'
KWA = ROOT / 'diagnostics/a44_kwa_wheat_zero_20260929'
CACHE = ROOT / 'diagnostics/stream_replay_io_20260928'
CANDIDATE = COMBO / 'candidate_v4.py'
CANDIDATE_SHA = '7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2'
COMBO_PANEL = COMBO / 'panel_v4.json'
COMBO_PANEL_SHA = '8f9eec84d361de731d95de88d76c5e78bf2c6bab58012a376daa5bdf466d15bd'
COMBO_MANIFEST = COMBO_RUN / 'frozen_manifest.json'
COMBO_MANIFEST_SHA = '277931bcc49350690a160e465ba8d96a0a4feb7c5be2af8de039bf60808723c9'
TOP20_RECEIPT = COMBO_RUN / 'outcome_receipt.json'
TOP20_RECEIPT_SHA = 'c576c106f4e40b009fba58cc2642d73c70571880bd940f75ca3b128a85cc51c9'
TOP20_LEDGER = COMBO_RUN / 'outcomes.jsonl'
TOP20_LEDGER_SHA = 'c31cd08a2aa8f8090a30fc3dd94d8ccd9b725a326326a91a5ffa478b31f8b2d3'
TOP20_RUN_MANIFEST = COMBO_RUN / 'run_manifest.json'
TOP20_RUN_MANIFEST_SHA = '957bc167e820c5265bd181a1c38a6707fdfc1a32ab8f3589fd7733566ae6957d'
TOP20_PREFLIGHT = COMBO_RUN / 'static_preflight.json'
TOP20_PREFLIGHT_SHA = '6c880aa593bafbb72a5d1beb9cd459fe76c2eca943bd2e7379c7f51bb31e0834'
BASE6_RESULTS_SHA = '5463a0efa37aebad2c11559cbcd2c39bf2a9a63ec5b2279f409d6360c61ff40d'
BASE6_PANEL_SHA = '7407b5f610457d2c00837a3c82e51ae2deaa225b20f2145e01dfaa92dba1db51'
BASE6_CANDIDATE_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
BASE6_FEATURES_SHA = 'bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795'
ACTION_CACHE_SHA = 'f544b134e2ad51160e4d6ad7719b9f41ad6cc850a1a51162249ede1cba279968'
PANEL_PATH = HERE / 'panel.json'
GHOST_TARGETS = {'live-114288168'}
KWA_TARGETS = {'live-114227779'}
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
            observation = item.get('observation') or {}
            require(int(observation.get('step', -1)) == 72,
                    f'step-72 trace malformed: {trace_path}')
            player = int(observation.get('player', -1))
            require(player == int(seat), f'trace seat mismatch: {trace_path}')
            rival = observation['farms'][1 - player]
            plots = sum(1 for row in rival['tiles'] for tile in row
                        if isinstance(tile, dict) and tile.get('crop') == 'WHEAT')
            stock = int(observation['market']['inventory']['WHEAT'])
            return plots, stock
    raise AssertionError(f'step-72 state missing: {trace_path}')


def verify_action_tape(path, expected):
    doc = json.loads(gzip.decompress(Path(path).read_bytes()))
    actions = doc.get('actions')
    require(isinstance(actions, list) and len(actions) == 719,
            f'opponent tape length changed: {path}')
    digests = {
        hashlib.sha256(json.dumps(actions, sort_keys=sort_keys,
                                 separators=(',', ':')).encode('utf-8')).hexdigest()
        for sort_keys in (False, True)
    }
    require(expected in digests, f'opponent tape changed: {path}')


def valid_baseline_provenance(row):
    if row.get('candidate_sha256') == '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9':
        return row.get('decision_equivalence_reuse') is not True
    return (row.get('candidate_sha256') == 'c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632'
            and row.get('decision_equivalence_reuse') is True
            and row.get('reused_parent_candidate_sha256') == 'c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632')


def main():
    if PANEL_PATH.exists():
        raise FileExistsError(f'panel builder never overwrites outputs: {PANEL_PATH}')
    require(sha(CANDIDATE) == CANDIDATE_SHA, 'combined candidate hash changed')
    require(sha(COMBO_PANEL) == COMBO_PANEL_SHA, 'top20 composition panel changed')
    require(sha(COMBO_MANIFEST) == COMBO_MANIFEST_SHA, 'top20 freeze manifest changed')
    require(sha(TOP20_RECEIPT) == TOP20_RECEIPT_SHA, 'top20 outcome receipt changed')
    require(sha(TOP20_LEDGER) == TOP20_LEDGER_SHA, 'top20 outcome ledger changed')
    require(sha(TOP20_RUN_MANIFEST) == TOP20_RUN_MANIFEST_SHA,
            'top20 run manifest changed')
    require(sha(TOP20_PREFLIGHT) == TOP20_PREFLIGHT_SHA,
            'top20 static preflight receipt changed')

    combo_manifest = load(COMBO_MANIFEST)
    for path_text, expected in combo_manifest['bindings'].items():
        path = Path(path_text)
        require(path.is_file() and sha(path) == expected,
                f'upstream composition binding changed: {path}')

    top20_receipt = load(TOP20_RECEIPT)
    top20_panel = load(COMBO_PANEL)
    require(top20_receipt.get('complete') is True
            and top20_receipt.get('passed') is True
            and top20_receipt.get('candidate_sha256') == CANDIDATE_SHA
            and top20_receipt.get('panel_sha256') == COMBO_PANEL_SHA
            and top20_receipt.get('top20_fixture_count') == 20
            and top20_receipt.get('top20_winning_sweeps') == 19
            and top20_receipt.get('top20_at_least_90_percent') is True,
            'completed top20 result is incomplete or failed')

    parent_panel = load(BASE6 / 'parent_panel.json')
    combined = load(BASE6 / 'combined_results.json')
    features_doc = load(BASE6 / 'feature_rows.json')
    ghost_preflight = load(GHOST / 'preflight.json')
    kwa_preflight = load(KWA / 'preflight.json')
    cache_doc = load(CACHE / 'initial_states.json')
    require(sha(BASE6 / 'combined_results.json') == BASE6_RESULTS_SHA
            and sha(BASE6 / 'parent_panel.json') == BASE6_PANEL_SHA
            and sha(BASE6 / 'candidate.py') == BASE6_CANDIDATE_SHA
            and sha(BASE6 / 'feature_rows.json') == BASE6_FEATURES_SHA
            and sha(CACHE / 'initial_states.json') == ACTION_CACHE_SHA,
            '6d panel, result, feature, or cache input changed')
    require(combined.get('complete') is True
            and combined.get('fixed_tape_only') is True
            and combined.get('candidate_sha256') == BASE6_CANDIDATE_SHA
            and len(combined.get('games', [])) == 208,
            '6d baseline is incomplete or changed')
    require(cache_doc.get('complete') is True and cache_doc.get('fixture_count') == 104,
            'replay cache is incomplete')

    fixture_rows = {row['fixture_id']: row for row in parent_panel['fixtures']}
    loss_order = [row['fixture_id'] for row in parent_panel['fixtures']
                  if row['panel'] == 'loss30']
    top20_order = [row['fixture_id'] for row in parent_panel['fixtures']
                   if row['panel'] == 'top20']
    require(len(loss_order) == 30 and len(set(loss_order)) == 30,
            'frozen loss30 set is not exactly 30 fixtures')
    require(len(top20_order) == 20 and len(set(top20_order)) == 20,
            'frozen top20 set is not exactly 20 fixtures')
    require(not set(loss_order) & set(top20_order), 'top20 and loss30 sets overlap')

    baseline = {(row['fixture_id'], int(row['candidate_seat'])): row
                for row in combined['games']}
    features = {(row['fixture_id'], int(row['seat'])): row
                for row in features_doc['rows']}
    ghost_rows = {(row['fixture_id'], int(row['seat'])): row
                  for row in ghost_preflight['feature_census']['all_feature_decisions']}
    kwa_targets = {(row['fixture_id'], int(row['seat']))
                   for row in kwa_preflight['trigger_rows']}
    ghost_targets = {(fid, seat) for (fid, seat), row in ghost_rows.items()
                     if row.get('triggered')}
    require(len(baseline) == 208 and len(features) == 208 and len(ghost_rows) == 208,
            'full 104-fixture source census is incomplete')
    require(kwa_targets == {(fid, seat) for fid in KWA_TARGETS for seat in (0, 1)},
            'Kwa full-corpus trigger census changed')
    require(ghost_targets == {(fid, seat) for fid in GHOST_TARGETS for seat in (0, 1)},
            'Ghost full-corpus trigger census changed')
    require(not kwa_targets & ghost_targets, 'route activation sets overlap')
    require(kwa_preflight.get('panel_counts') == {
                'loss30': 60, 'public-win': 108, 'top20': 40}
            and kwa_preflight.get('top20_trigger_count') == 0
            and kwa_preflight.get('public_win_trigger_count') == 0,
            'Kwa census coverage changed')

    cache_rows = {row['source_replay_path']: row for row in cache_doc['replays']}
    games = []
    for fixture_id in loss_order:
        fixture = fixture_rows[fixture_id]
        for seat in (0, 1):
            key = (fixture_id, seat)
            feature = features[key]
            ghost = ghost_rows[key]
            base = baseline[key]
            expected_kwa = key in kwa_targets
            expected_ghost = key in ghost_targets
            require(not (expected_kwa and expected_ghost),
                    f'route layers overlap at {key}')
            require(bool(ghost.get('triggered')) == expected_ghost
                    and feature['bridge_branch'] == ghost['bridge_branch'],
                    f'full-corpus feature census mismatch at {key}')
            require(expected_kwa == (fixture_id in KWA_TARGETS)
                    and expected_ghost == (fixture_id in GHOST_TARGETS),
                    f'target identity differs from trigger at {key}')
            require(valid_baseline_provenance(base),
                    f'6d baseline provenance changed at {key}')
            trace_path = Path(feature['trace_path'])
            require(trace_path.is_file() and sha(trace_path) == feature['trace_sha256'],
                    f'step-72 trace missing or changed at {key}')
            wheat_plots, wheat_stock = read_step72(trace_path, seat)
            require(int(ghost['step72_public_wheat']) == wheat_stock,
                    f'Ghost step-72 stock changed at {key}')
            fixture_cache = cache_rows.get(fixture['source_replay_path'])
            require(fixture_cache is not None
                    and fixture_cache['source_replay_sha256'] == fixture['source_replay_sha256']
                    and sha(fixture['source_replay_path']) == fixture_cache['compressed_sha256'],
                    f'replay cache identity changed at {key}')
            verify_action_tape(fixture['source_action_tape_path'],
                               fixture['source_opponent_action_sha256'])
            games.append({
                'fixture_id': fixture_id,
                'candidate_seat': seat,
                'panel': 'loss30',
                'expected_kwa_trigger': expected_kwa,
                'expected_ghost_trigger': expected_ghost,
                'expected_branch': feature['bridge_branch'],
                'expected_key': feature['rule_key'],
                'expected_parent_route': ghost['parent_selected_route'],
                'expected_ghost_wheat': wheat_stock,
                'expected_kwa_wheat_plots': wheat_plots,
                'expected_ghost_wheat_telemetry': (
                    wheat_stock if feature['bridge_branch'] == 'source' else None),
                'expected_kwa_wheat_plots_telemetry': (
                    wheat_plots if feature['bridge_branch'] == 'source' else None),
                'baseline_6d': {field: base[field] for field in CONTROL_FIELDS},
                'baseline_candidate_sha256': base['candidate_sha256'],
                'feature_trace_path': str(trace_path),
                'feature_trace_sha256': feature['trace_sha256'],
                'source_fixture': fixture,
            })

    loss_games = [row for row in games if row['panel'] == 'loss30']
    loss_baseline = {}
    for row in loss_games:
        loss_baseline.setdefault(row['fixture_id'], []).append(row['baseline_6d']['result'])
    loss_sweeps = sum(len(values) == 2 and all(value == 'win' for value in values)
                      for values in loss_baseline.values())
    require(len(games) == 60 and len(loss_baseline) == 30
            and sum(row['expected_kwa_trigger'] for row in games) == 2
            and sum(row['expected_ghost_trigger'] for row in games) == 2,
            'full loss30 panel does not contain 60 games and four activations')
    require(loss_sweeps == 22, f'6d loss30 baseline changed: {loss_sweeps}/30')

    panel = {
        'schema': 'a44-ghost-kwa-full-goal-panel-v1',
        'builder_sha256': sha(__file__),
        'candidate_path': str(CANDIDATE.resolve()),
        'candidate_sha256': CANDIDATE_SHA,
        'parent_6d_candidate_sha256': BASE6_CANDIDATE_SHA,
        'top20_reference_panel_path': str(COMBO_PANEL.resolve()),
        'top20_reference_panel_sha256': COMBO_PANEL_SHA,
        'top20_reference_receipt_path': str(TOP20_RECEIPT.resolve()),
        'top20_reference_receipt_sha256': TOP20_RECEIPT_SHA,
        'top20_reference_preflight_sha256': TOP20_PREFLIGHT_SHA,
        'top20_fixture_count': 20,
        'top20_goal_metric': 'both-seat fixture sweep',
        'top20_min_winning_sweeps': 18,
        'top20_measured_winning_sweeps': 19,
        'loss30_fixture_count': 30,
        'loss30_game_count': 60,
        'loss30_goal_metric': 'both-seat fixture sweep',
        'loss30_min_winning_sweeps': 27,
        'loss30_parent_6d_winning_sweeps': loss_sweeps,
        'fixture_order': loss_order,
        'game_count': len(games),
        'expected_kwa_trigger_seats': 2,
        'expected_ghost_trigger_seats': 2,
        'expected_control_seats': 56,
        'games': games,
    }
    with PANEL_PATH.open('x', encoding='utf-8', newline='\n') as out:
        out.write(json.dumps(panel, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({
        'panel_sha256': sha(PANEL_PATH),
        'candidate_sha256': CANDIDATE_SHA,
        'loss30_fixtures': len(loss_order),
        'loss30_games': len(games),
        'parent_6d_loss30_sweeps': loss_sweeps,
        'top20_reference_sweeps': 19,
        'kwa_trigger_seats': 2,
        'ghost_trigger_seats': 2,
        'controls': 56,
    }, indent=2))


if __name__ == '__main__':
    main()
