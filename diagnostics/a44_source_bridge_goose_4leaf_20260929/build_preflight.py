"""Freeze and statically verify the a44 source-bridge four-leaf experiment."""
from collections import Counter
from pathlib import Path
import copy
import gzip
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

SOURCE = ROOT / 'diagnostics/upload_adaptive_donor_20260928_a44c8c2c/main.py'
GOOSE = ROOT / 'diagnostics/production_leaf_selector_20260928'
TARGET = ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928'
PUBLIC = ROOT / 'diagnostics/adaptive_third_pair_repair_20260928'
HELPERS = ROOT / 'diagnostics/stream_replay_io_20260928'
ROUTES = ROOT / 'diagnostics/physical_route_rollout_20260928'

RULES = {
    'FARMERS_MARKET|M<8|C>S|G0': 113535489,
    'ICE_CREAM_SHOP|M8+|C<S|G0': 113535489,
    'ICE_CREAM_SHOP|M8+|C>S|G0': 113470868,
    'PIZZA_SHOP|M8+|C<S|G0': 113470868,
}
GOOSE_RULES = {
    'BRUNCH_SPOT|M8+|C>S|G+': 113332529,
    **RULES,
}
EXPECTED_SOURCE_SHA = 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
EXPECTED_GOOSE_SHA = '5c97b54905274914a63a05d8eee5830754ea5f3bbb8e055db04ec6efa0d39ae3'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def resolve(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def canonical_tape_sha(actions):
    hashes = [hashlib.sha256(json.dumps(actions, sort_keys=sort_keys, separators=(',', ':')).encode()).hexdigest()
              for sort_keys in (False, True)]
    return hashes


def public_features(obs):
    shops = obs['town']['unlocked_shops']
    rival = obs['farms'][1 - int(obs['player'])]
    counts = {'MELON': 0, 'COW': 0, 'SHEEP': 0, 'GOOSE': 0}
    for row in rival['tiles']:
        for tile in row:
            if isinstance(tile, dict):
                counts['MELON'] += tile.get('crop') == 'MELON'
                for animal in ('COW', 'SHEEP', 'GOOSE'):
                    counts[animal] += tile.get('animal') == animal
    cmp = 'C<S' if counts['COW'] < counts['SHEEP'] else 'C>S' if counts['COW'] > counts['SHEEP'] else 'C=S'
    key = shops[0] + '|' + ('M8+' if counts['MELON'] >= 8 else 'M<8') + '|' + cmp
    key += '|G+' if counts['GOOSE'] else '|G0'
    return dict(shop=shops[0], melon_count=counts['MELON'], cow_count=counts['COW'],
                sheep_count=counts['SHEEP'], goose_count=counts['GOOSE'], key=key)


def iter_trace(path):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            yield json.loads(line)


def main():
    source_sha = sha(SOURCE)
    assert source_sha == EXPECTED_SOURCE_SHA
    production_pool_path = GOOSE / 'pool.json'
    production_pool_sha = sha(production_pool_path)
    goose_candidate_path = GOOSE / 'candidate_production_goose.py'
    goose_candidate_sha = sha(goose_candidate_path)
    assert goose_candidate_sha == EXPECTED_GOOSE_SHA

    selection = read(GOOSE / 'selection.json')
    selected_goose = next(r for r in selection['combined'] if r['arm'] == 'production_goose')
    assert selected_goose['rules'] == GOOSE_RULES
    assert selected_goose['candidate_sha256'] == EXPECTED_GOOSE_SHA
    assert selection['pool_sha256'] == production_pool_sha
    assert sha(GOOSE / 'conditional.json') == selection['conditional_sha256']
    assert sha(GOOSE / 'controls.json') == selection['controls_sha256']
    production_full = read(GOOSE / 'full.json')
    goose_outcomes = [r for r in production_full['games'] if r.get('version') == 'production_goose']
    assert len(goose_outcomes) == 100 and all(r['candidate_sha256'] == EXPECTED_GOOSE_SHA for r in goose_outcomes)
    assert production_full['complete'] and production_full['clean']
    goose_sweeps = {}
    pool_panel = {f['fixture_id']: ('loss30' if f.get('panel') == 'official_live_cohort_180951'
                                    else 'top20' if f.get('panel') == 'current_top20_20260927_172258'
                                    else 'public-win') for f in read(production_pool_path)['fixtures']}
    for r in goose_outcomes:
        goose_sweeps.setdefault(r['fixture_id'], []).append(r)
    assert sum(pool_panel[fid] == 'loss30' and all(x['result'] == 'win' for x in rows)
               for fid, rows in goose_sweeps.items()) == 18
    assert sum(pool_panel[fid] == 'top20' and all(x['result'] == 'win' for x in rows)
               for fid, rows in goose_sweeps.items()) == 19
    assert not any(r['parent_result'] == 'win' and r['result'] != 'win' for r in goose_outcomes)

    target_receipt = read(TARGET / 'full_results.json')
    target_pool = read(TARGET / 'full_pool.json')
    public_receipt = read(PUBLIC / 'discovery.json')
    target_rows = target_receipt['games']
    public_rows = public_receipt['rows']
    assert target_receipt['complete'] and target_receipt['clean']
    assert len(target_rows) == 100 and len({(r['fixture_id'], r['candidate_seat']) for r in target_rows}) == 100
    assert all(r['candidate_sha256'] == EXPECTED_SOURCE_SHA for r in target_rows)
    source_controls = {r['fixture_id']: r for r in read(GOOSE / 'controls.json')['games'] if r.get('version') == 'source'}
    conditional_goose = read(GOOSE / 'conditional.json')['games']
    public_route_controls = [r for r in conditional_goose
        if r.get('version') == 'production_goose_53a0614bd1_113470868'
        and r.get('candidate_telemetry', {}).get('production_leaf_route') == '113470868'
        and r['fixture_id'] in {'public-win-114209881', 'public-win-114221853', 'public-win-114245470'}]
    assert len(public_route_controls) == 6 and all(r['result'] == 'win' and r['parent_result'] == 'win'
                                                   for r in public_route_controls)
    assert public_receipt['complete'] and len(public_rows) == 108
    assert len({(r['fixture_id'], r['candidate_seat']) for r in public_rows}) == 108
    assert all(r['candidate_sha256'] == EXPECTED_SOURCE_SHA and r['passed'] for r in public_rows)
    assert target_receipt['pool_sha256'] == sha(TARGET / 'full_pool.json')
    assert public_receipt['pool_sha256'] == sha(PUBLIC / 'pool.json')

    pool = read(production_pool_path)
    fixtures_by_id = {r['fixture_id']: r for r in pool['fixtures']}
    assert len(fixtures_by_id) == 104
    assert set(fixtures_by_id) == ({r['fixture_id'] for r in target_rows} | {r['fixture_id'] for r in public_rows})
    assert len({r['fixture_id'] for r in target_rows}) == 50
    assert len({r['fixture_id'] for r in public_rows}) == 54

    # The saved outcome tape identifies only the two saved target panels; public
    # controls are explicitly re-evaluated against exact a44 source below.
    target_games = {(r['fixture_id'], r['candidate_seat']): r for r in target_rows}
    target_groups = {}
    for r in target_rows:
        target_groups.setdefault(r['fixture_id'], []).append(r)
    for fixture_id, rows in target_groups.items():
        assert len(rows) == 2 and {r['candidate_seat'] for r in rows} == {0, 1}
        assert all(r['clean'] and r['frames'] == 720 for r in rows)

    trace_records = {}
    for r in target_rows:
        trace_records[(r['fixture_id'], r['candidate_seat'])] = (r['trace_path'], r['trace_sha256'],
                                                                  r['candidate_telemetry']['bridge_selected'])
    for r in public_rows:
        key = (r['fixture_id'], r['candidate_seat'])
        assert key not in trace_records
        trace_records[key] = (r['trace_path'], r['trace_sha256'], r['branch'])
    assert len(trace_records) == 208

    feature_rows = []
    for fixture_id in sorted(fixtures_by_id):
        fixture = fixtures_by_id[fixture_id]
        panel_name = ('loss30' if fixture.get('panel') == 'official_live_cohort_180951'
                      else 'top20' if fixture.get('panel') == 'current_top20_20260927_172258'
                      else 'public-win')
        assert panel_name in {'loss30', 'top20', 'public-win'}
        for seat in (0, 1):
            path_string, trace_sha, branch = trace_records[(fixture_id, seat)]
            trace_path = resolve(path_string)
            assert trace_path.exists() and sha(trace_path) == trace_sha
            rows = list(iter_trace(trace_path))
            at72 = next((x for x in rows if x.get('step') == 72), None)
            assert at72 is not None and int(at72['observation']['step']) == 72
            obs = at72['observation']
            f = public_features(obs)
            if panel_name != 'public-win':
                assert branch == target_games[(fixture_id, seat)]['candidate_telemetry']['bridge_selected']
                assert branch in {'source', 'shared151', 'shared150'}
            else:
                assert branch == next(r['branch'] for r in public_rows
                                      if r['fixture_id'] == fixture_id and r['candidate_seat'] == seat)
            goose_route = GOOSE_RULES.get(f['key'])
            selected_route = goose_route if branch == 'source' and f['key'] in RULES else None
            row = dict(fixture_id=fixture_id, panel=panel_name, seat=seat, step=72,
                       bridge_branch=branch, shop=f['shop'], melon_count=f['melon_count'],
                       cow_count=f['cow_count'], sheep_count=f['sheep_count'],
                       goose_count=f['goose_count'], rule_key=f['key'],
                       production_goose_route=goose_route,
                       selected_route=selected_route,
                       trace_path=str(trace_path), trace_sha256=trace_sha)
            if panel_name != 'public-win':
                old = target_games[(fixture_id, seat)]
                row['a44_source_result'] = old['result']
                row['a44_source_margin'] = old['margin']
            feature_rows.append(row)
    assert len(feature_rows) == 208
    feature_keys = {(r['fixture_id'], r['seat']): r for r in feature_rows}
    assert len(feature_keys) == 208

    # Prove source controls, exact feature coverage, target baseline coverage,
    # and non-overlap with the unique a44 double-seat sweeps.
    goose_hits = [r for r in feature_rows if r['rule_key'] in GOOSE_RULES]
    four_hits = [r for r in feature_rows if r['rule_key'] in RULES]
    assert len(goose_hits) == 22 and len({r['fixture_id'] for r in goose_hits}) == 11
    assert len(four_hits) == 20 and len({r['fixture_id'] for r in four_hits}) == 10
    assert all(r['bridge_branch'] == 'source' for r in four_hits)
    assert all(r['panel'] != 'top20' for r in four_hits)
    assert sum(r['panel'] == 'loss30' for r in four_hits) == 14
    assert sum(r['panel'] == 'public-win' for r in four_hits) == 6
    target_sweeps = {}
    for fixture_id, rows in target_groups.items():
        target_sweeps[fixture_id] = all(r['result'] == 'win' for r in rows)
    a44_only = [fid for fid, won in target_sweeps.items() if won]
    expected_a44_only = {'live-114232208', 'live-114235177', 'live-114279308', 'live-114283577'}
    assert expected_a44_only <= set(a44_only)
    untouched = []
    for fixture_id in sorted(expected_a44_only):
        rows = [feature_keys[(fixture_id, seat)] for seat in (0, 1)]
        assert all(r['selected_route'] is None for r in rows)
        if all(r['bridge_branch'] != 'source' for r in rows):
            reason = 'source-bridge gate skips both seats'
        else:
            reason = 'step72 public key is outside the four rules'
        untouched.append(dict(fixture_id=fixture_id, a44_both_seat_win=True,
                              keys=[r['rule_key'] for r in rows],
                              branches=[r['bridge_branch'] for r in rows], reason=reason))

    goose = {r['rule_key'] for r in goose_hits}
    assert 'BRUNCH_SPOT|M8+|C>S|G+' in goose
    four_fixture_ids = sorted({r['fixture_id'] for r in four_hits})
    assert len(four_fixture_ids) == 10

    # Build the exact minimal replay panel required by the bound helper. Fixture
    # identity is only a corpus join key; no identity field enters the selector.
    panel_fixtures = []
    for fixture_id in sorted(fixtures_by_id):
        src = fixtures_by_id[fixture_id]
        panel_name = ('loss30' if src.get('panel') == 'official_live_cohort_180951'
                      else 'top20' if src.get('panel') == 'current_top20_20260927_172258'
                      else 'public-win')
        for key in ('source_replay_path', 'source_replay_sha256', 'source_action_tape_path',
                    'source_opponent_action_sha256', 'seed'):
            assert key in src
        panel_fixtures.append(dict(fixture_id=fixture_id, panel=panel_name, seed=src['seed'],
            source_replay_path=src['source_replay_path'], source_replay_sha256=src['source_replay_sha256'],
            source_action_tape_path=src['source_action_tape_path'],
            source_opponent_action_sha256=src['source_opponent_action_sha256']))
    target_baseline_games = []
    for r in target_rows:
        target_baseline_games.append({k: r[k] for k in ('fixture_id', 'candidate_seat', 'candidate_reward',
            'opponent_reward', 'margin', 'result', 'candidate_status', 'opponent_status', 'frames')})
    panel = dict(candidate='exact a44 source bridge + four Goose leaves', fixture_count=104,
        fixture_order='fixture_id sorted; seats 0 then 1', source_comparison='exact a44 target100 + new exact a44 public108',
        fixtures=panel_fixtures, target_baseline_games=target_baseline_games,
        target_baseline_receipt=str(TARGET / 'full_results.json'), target_baseline_sha256=sha(TARGET / 'full_results.json'))

    # Replay and tape byte hashes plus verified cached input manifest. Actual
    # execution remains staged in run_study.py and is not invoked here.
    fixture_file_bindings = {}
    cache = read(HELPERS / 'initial_states.json')
    cache_rows = {x['source_replay_path']: x for x in cache['replays']}
    for fixture in panel_fixtures:
        replay = resolve(fixture['source_replay_path'])
        tape = resolve(fixture['source_action_tape_path'])
        assert replay.exists() and tape.exists()
        # Match the replay's raw digest and compressed bytes through the audited cache.
        cache_row = cache_rows[fixture['source_replay_path']]
        assert cache_row['source_replay_sha256'] == fixture['source_replay_sha256']
        assert sha(replay) == cache_row['compressed_sha256']
        action_data = json.loads(gzip.decompress(tape.read_bytes()))
        actions = action_data['actions']
        assert len(actions) == 719 and fixture['source_opponent_action_sha256'] in canonical_tape_sha(actions)
        fixture_file_bindings[str(replay)] = sha(replay)
        fixture_file_bindings[str(tape)] = sha(tape)

    # Copy and compose candidate bytes only after verifying the exact a44 base.
    source_copy = HERE / 'source_a44.py'
    candidate_path = HERE / 'candidate.py'
    source_bytes = SOURCE.read_bytes()
    overlay_bytes = (HERE / 'overlay.py').read_bytes()
    source_copy.write_bytes(source_bytes)
    candidate_bytes = source_bytes.rstrip(b'\r\n') + b'\n\n' + overlay_bytes
    compile(candidate_bytes, str(candidate_path), 'exec')
    candidate_path.write_bytes(candidate_bytes)
    candidate_sha = sha(candidate_path)

    # Static import exercises module definitions only; it does not call the
    # game policy or any engine transition.
    spec = importlib.util.spec_from_file_location('a44_goose4_preflight_module', candidate_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base_routes = copy.deepcopy(module._DATA['route_map'])
    base_farmice = copy.deepcopy(module._FARMICE_TAPE)
    donor_state = {name: dict(donor_map=copy.deepcopy(ns['_DONOR_MAP']),
                              routes=copy.deepcopy(ns['_DONOR_ROUTES']))
                   for name, ns in module._BRIDGE_DONORS.items()}
    for route_id in set(RULES.values()):
        route = module._DATA['routes'][str(route_id)]
        assert len(route) == 719
    assert module._a44_goose4_active(72, 'source')
    assert not module._a44_goose4_active(72, 'shared151')
    assert not module._a44_goose4_active(72, 'shared150')
    assert not module._a44_goose4_active(71, 'source')
    assert not module._a44_goose4_active(73, 'source')
    route_checks = []
    assert len(module._DATA['opening']) == 72
    for leaf, route_id in RULES.items():
        shop = leaf.split('|', 1)[0]
        module._a44_goose4_commit(leaf, route_id)
        descendants = [key for key in base_routes if key.split('|', 1)[0] == shop]
        assert descendants
        assert all(module._DATA['route_map'][key] == route_id for key in descendants)
        assert module._DATA['route_map'][shop] == route_id
        if shop == 'FARMERS_MARKET':
            assert module._FARMICE_TAPE == module._DATA['routes'][str(route_id)]
        schedule = module._hire_recovery_schedule(dict(step=72, town=dict(unlocked_shops=[shop])))
        assert schedule == module._DATA['routes'][str(route_id)]
        assert {name: dict(donor_map=ns['_DONOR_MAP'], routes=ns['_DONOR_ROUTES'])
                for name, ns in module._BRIDGE_DONORS.items()} == donor_state
        route_checks.append(dict(rule_key=leaf, route=route_id, changed_shop=shop,
                                 descendants_updated=len(descendants), route_length=len(schedule),
                                 schedule_resolution_step=72))
        module._a44_goose4_reset()
        assert module._DATA['route_map'] == base_routes
        assert module._FARMICE_TAPE == base_farmice
    # Candidate key function must reproduce all 208 extracted keys exactly.
    for row in feature_rows:
        path, _, _ = trace_records[(row['fixture_id'], row['seat'])]
        trace72 = next(x for x in iter_trace(resolve(path)) if x.get('step') == 72)
        assert module._a44_goose4_key(trace72['observation']) == row['rule_key']

    fixture_file_bindings[str(HELPERS / 'initial_states.json')] = sha(HELPERS / 'initial_states.json')
    # Bind original public/target trace receipts and source data, the selected
    # Goose evidence, cached harness, and frozen native transition implementation.
    evidence_paths = [
        SOURCE,
        GOOSE / 'candidate_production_goose.py', GOOSE / 'layer.py', GOOSE / 'selection.json',
        GOOSE / 'pool.json', GOOSE / 'conditional.json', GOOSE / 'controls.json', GOOSE / 'full.json',
        GOOSE / 'preflight.json', GOOSE / 'RESULTS.md', GOOSE / 'RUN_STATE.md',
        TARGET / 'full.py', TARGET / 'study.py', TARGET / 'full_pool.json', TARGET / 'full_results.json',
        PUBLIC / 'study.py', PUBLIC / 'pool.json', PUBLIC / 'discovery.json',
        HELPERS / 'fast_game_cached.py', HELPERS / 'cached_input.py', HELPERS / 'cached_helper_manifest.json',
        HELPERS / 'cached_helper_parity.json', ROUTES / 'native_core.py', ROUTES / 'check.py',
        ROOT / 'diagnostics/local_target_20260928/run_lock.py',
        HERE / 'overlay.py', HERE / 'PLAN.md', HERE / 'run_study.py', HERE / 'build_preflight.py',
        HERE / 'source_a44.py', HERE / 'candidate.py',
    ]
    bindings = {str(path): sha(path) for path in evidence_paths}
    bindings.update(fixture_file_bindings)
    trace_bindings = {}
    for path, trace_sha, _ in trace_records.values():
        full = resolve(path)
        trace_bindings[str(full)] = trace_sha
    assert len(trace_bindings) == 208
    bindings.update(trace_bindings)

    write_json(HERE / 'feature_rows.json', dict(complete=True, source_a44_sha256=source_sha,
        production_pool_sha256=production_pool_sha,
        target_trace_receipt_sha256=sha(TARGET / 'full_results.json'),
        public_trace_receipt_sha256=sha(PUBLIC / 'discovery.json'),
        rows=feature_rows))
    write_json(HERE / 'panel.json', panel)

    # The note contains the previous completed Goose comparison and the new
    # static compatibility proof; it does not claim four-leaf outcomes.
    evidence = f'''# a44 source-bridge Goose four-leaf evidence\n\nThis frozen candidate starts from uploaded a44 source SHA-256 `{source_sha}` and exact production-Goose pool SHA-256 `{production_pool_sha}`. The 208 observation72 rows are bound to a44 target receipt `{sha(TARGET / 'full_results.json')}` (100 seats / 50 fixtures) and public-prefix receipt `{sha(PUBLIC / 'discovery.json')}` (108 seats / 54 fixtures); every exact compressed trace is bound in `frozen_manifest.json`. The four-key Goose coverage is {len(four_fixture_ids)}/104 fixtures and {len(four_hits)}/208 seats, all on the source bridge. Full production-Goose rule coverage is 11/104 fixtures and 22/208 seats; its extra Brunch/THIRD observation is on shared151 and excluded here.\n\nThe four a44 both-seat sweeps `{', '.join(sorted(expected_a44_only))}` do not match these rules. Three are already on shared151, so the source-bridge gate skips them; `live-114283577` is on source but has public key `{feature_keys[('live-114283577', 0)]['rule_key']}`, outside the four leaves. All 20 four-key triggers are outside top20. Rules: `{json.dumps(RULES, sort_keys=True)}`.\n\nThe completed production-Goose panel against source367 reports 18/30 loss30 sweeps and 19/20 top20 sweeps, with no source-winning seat regressions. Its known false positive pensukesan (`live-114218866`) remains a loss and changes from -8,665 to -53,956 margin per seat; Ghost Rule (`live-114288168`) splits seats; fasith (`live-114255779`) remains a both-seat win, with margin falling from +16,321 to +9,559 per seat. In the earlier route-113470868 Goose conditional screen, public controls `public-win-114209881`, `public-win-114221853`, and `public-win-114245470` each remain both-seat wins. These are prior source367-bound selector results, not outcomes for this a44-bound overlay. The new 54-fixture a44 source and 104-fixture candidate outcome phases remain staged.\n\nThis is static compatibility evidence plus saved fixed-tape context. It is not reactive validation and makes no promotion claim.\n'''
    (HERE / 'EVIDENCE.md').write_text(evidence, encoding='utf-8')
    bindings[str(HERE / 'feature_rows.json')] = sha(HERE / 'feature_rows.json')
    bindings[str(HERE / 'panel.json')] = sha(HERE / 'panel.json')
    bindings[str(HERE / 'EVIDENCE.md')] = sha(HERE / 'EVIDENCE.md')

    preflight = dict(passed=True, static_only=True, games_run=0, source_a44_sha256=source_sha,
        production_goose_sha256=EXPECTED_GOOSE_SHA, candidate_sha256=candidate_sha,
        production_pool_sha256=production_pool_sha,
        four_key_fixture_coverage=len(four_fixture_ids), four_key_seat_coverage=len(four_hits),
        five_key_fixture_coverage=len({r['fixture_id'] for r in goose_hits}),
        five_key_seat_coverage=len(goose_hits), feature_rows=208,
        target_baselines=100, public_source_controls_staged=108,
        candidate_games_staged=208, a44_only_double_seat_wins_untouched=untouched,
        route_checks=route_checks, all_four_key_hits_source_branch=True,
        all_top20_untouched=True, donor_maps_unchanged=True, reset_passed=True,
        exact_runtime_feature_keys_passed=True,
        trace_binding_count=len(trace_bindings), replay_tape_binding_count=len(fixture_file_bindings) - 1,
        candidate_path=str(candidate_path), staged_command='python -X utf8 diagnostics/a44_source_bridge_goose_4leaf_20260929/run_study.py full',
        completed_experiment=False, reactive_validation=False)
    write_json(HERE / 'preflight.json', preflight)
    bindings[str(HERE / 'preflight.json')] = sha(HERE / 'preflight.json')
    bindings[str(HERE / 'run_study.py')] = sha(HERE / 'run_study.py')
    bindings[str(HERE / 'build_preflight.py')] = sha(HERE / 'build_preflight.py')
    manifest = dict(complete=True, diagnostic_only=True, source_a44_sha256=source_sha,
        production_goose_sha256=EXPECTED_GOOSE_SHA, production_pool_sha256=production_pool_sha,
        panel_sha256=sha(HERE / 'panel.json'), feature_rows_sha256=sha(HERE / 'feature_rows.json'),
        candidate_sha256=candidate_sha, trace_binding_count=len(trace_bindings),
        replay_tape_binding_count=len(fixture_file_bindings) - 1, bindings=bindings)
    write_json(HERE / 'frozen_manifest.json', manifest)
    # Check that the staged runner verifies every bound byte before handing it off.
    for name, digest in bindings.items():
        assert resolve(name).exists() and sha(resolve(name)) == digest, f'Binding failed: {name}'
    assert sha(HERE / 'candidate.py') == candidate_sha
    print(json.dumps(dict(preflight=preflight, preflight_sha256=sha(HERE / 'preflight.json'),
                          manifest_sha256=sha(HERE / 'frozen_manifest.json'),
                          candidate_sha256=candidate_sha, panel_sha256=sha(HERE / 'panel.json'),
                          feature_rows_sha256=sha(HERE / 'feature_rows.json'),
                          bindings=len(bindings), trace_bindings=len(trace_bindings),
                          source_trigger_fixture_ids=four_fixture_ids), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
