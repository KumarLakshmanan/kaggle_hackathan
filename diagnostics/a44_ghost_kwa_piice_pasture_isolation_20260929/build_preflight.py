from __future__ import annotations
import copy
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
COMPOSED = ROOT / 'diagnostics/a44_ghost_kwa_piice_combo_20260929'
V4 = ROOT / 'diagnostics/a44_ghost_kwa_combo_20260929'
BASE6 = ROOT / 'diagnostics/a44_goose4_smoothie_source_20260929'
PASTURE = ROOT / 'diagnostics/pasture_guard_source_leaf_20260928'
PASTURE_EXACT = ROOT / 'diagnostics/a44_goose4_smoothie_pasture_source_20260929'
FEATURES = PASTURE / 'feature_rows.json'
BASE6_FEATURES = BASE6 / 'feature_rows.json'
PARENT_SOURCE = COMPOSED / 'candidate.py'
V4_SOURCE = V4 / 'candidate_v4.py'
OLD_PASTURE_CANDIDATE = PASTURE_EXACT / 'candidate.py'
OLD_PREFIX_RESULTS = PASTURE_EXACT / 'prefix_results.json'
OLD_PREFIX_MANIFEST = PASTURE_EXACT / 'prefix_manifest.json'
PARENT_SHA = '8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62'
V4_SHA = '7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2'
BASE6_SHA = '6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9'
OLD_PASTURE_SHA = '5b4ef52d19cb8ffb310b2bb067c725810241668667a0b5b468ac09b6b9215506'
TARGET = 'live-114274897'
CHRIS = 'public-win-114193811'
TARGET_LEAF = 'BRUNCH_SPOT|M8+|C>S|G+'
TARGET_ROUTE = 113332529
OVERRIDE_HANDS = 5
OVERRIDE_PASTURES = 1
BRANCH_NEEDLE = "        branch = 'shared151' if hands>=5 else ('shared150' if _BRIDGE_VARIANT=='five_or_zero' and hands==0 else 'source')"
BRANCH_REPLACEMENT = """        rival_pastures = _iso_pasture_public_count(observation)
        _ISO_PASTURE_TRIGGERED = (hands == 5 and rival_pastures == 1)
        branch = ('source' if _ISO_PASTURE_TRIGGERED else
                  ('shared151' if hands>=5 else ('shared150' if _BRIDGE_VARIANT=='five_or_zero' and hands==0 else 'source')))"""
GLOBAL_NEEDLE = '    global _BRIDGE_SELECTED, _BRIDGE_INITIAL'
GLOBAL_REPLACEMENT = '    global _BRIDGE_SELECTED, _BRIDGE_INITIAL, _ISO_PASTURE_TRIGGERED'

LAYER = r'''
# Isolated public step-1 pasture trigger and Brunch goose leaf.
_ISO_PASTURE_TRIGGERED = False
_ISO_PASTURE_PARENT_AGENT = agent
_ISO_PASTURE_KEY72 = 'BRUNCH_SPOT|M8+|C>S|G+'
_ISO_PASTURE_ROUTE72 = 113332529
_ISO_PASTURE_STATS = {
    'iso_pasture_rival_hands_step1': -1,
    'iso_pasture_rival_pastures_step1': -1,
    'iso_pasture_triggered_step1': False,
    'iso_pasture_branch_step1': '',
    'iso_pasture_reset_route_map_matches': False,
    'iso_pasture_leaf_key72': '',
    'iso_pasture_leaf_route72': '',
    'iso_pasture_leaf_turns': 0,
    'iso_pasture_leaf_errors': 0,
}

def _iso_pasture_public_count(observation):
    rival = observation['farms'][1 - int(observation['player'])]
    return sum(
        isinstance(tile, dict) and tile.get('kind') == 'PASTURE'
        for row in rival.get('tiles', [])
        for tile in row
    )

def _iso_pasture_reset():
    global _ISO_PASTURE_TRIGGERED
    _ISO_PASTURE_TRIGGERED = False
    _ISO_PASTURE_STATS.update(
        iso_pasture_rival_hands_step1=-1,
        iso_pasture_rival_pastures_step1=-1,
        iso_pasture_triggered_step1=False,
        iso_pasture_branch_step1='',
        iso_pasture_reset_route_map_matches=False,
        iso_pasture_leaf_key72='',
        iso_pasture_leaf_route72='',
        iso_pasture_leaf_turns=0,
        iso_pasture_leaf_errors=0,
    )

def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _iso_pasture_reset()

    if step == 72:
        branch = _BRIDGE_SELECTED
        key = _a44_goose4_key(observation) if branch == 'source' else ''
        _ISO_PASTURE_STATS['iso_pasture_leaf_key72'] = key
        if (_ISO_PASTURE_TRIGGERED and branch == 'source'
                and key == _ISO_PASTURE_KEY72):
            try:
                _a44_goose4_commit(_ISO_PASTURE_KEY72, _ISO_PASTURE_ROUTE72)
                _ISO_PASTURE_STATS['iso_pasture_leaf_route72'] = str(
                    _ISO_PASTURE_ROUTE72)
            except Exception:
                _ISO_PASTURE_STATS['iso_pasture_leaf_errors'] += 1

    result = _ISO_PASTURE_PARENT_AGENT(observation, configuration)

    if step == 0:
        _ISO_PASTURE_STATS['iso_pasture_reset_route_map_matches'] = (
            _DATA['route_map'] == _PIICE_BASE_ROUTE_MAP)
    elif step == 1:
        rival_hands = len(observation['farms'][1 - int(observation['player'])]['hands'])
        rival_pastures = _iso_pasture_public_count(observation)
        _ISO_PASTURE_STATS.update(
            iso_pasture_rival_hands_step1=rival_hands,
            iso_pasture_rival_pastures_step1=rival_pastures,
            iso_pasture_triggered_step1=bool(_ISO_PASTURE_TRIGGERED),
            iso_pasture_branch_step1=str(_BRIDGE_SELECTED),
        )
    elif step >= 72 and _ISO_PASTURE_STATS['iso_pasture_leaf_route72']:
        _ISO_PASTURE_STATS['iso_pasture_leaf_turns'] += 1

    agent.telemetry.update(getattr(_ISO_PASTURE_PARENT_AGENT, 'telemetry', {}))
    agent.telemetry.update(_ISO_PASTURE_STATS)
    return result

agent.telemetry = {}

def kaggle_a44_isolated_pasture_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''.lstrip()

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def read(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def dump(path: Path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n',
                          encoding='utf-8', newline='\n')

def import_candidate(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def obs_through(path: Path, last_step=72):
    result = {}
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            step = int(row.get('step', -1))
            if 0 <= step <= last_step:
                result[step] = row['observation']
            if step == last_step:
                break
    assert set(result) == set(range(last_step + 1)), (str(path), sorted(result))
    return result

def public_leaf_key(observation):
    shops = observation.get('town', {}).get('unlocked_shops', []) or []
    if not shops:
        return None
    rival = observation['farms'][1 - int(observation['player'])]
    melon = cow = sheep = goose = 0
    for row in rival.get('tiles', []):
        for tile in row:
            if isinstance(tile, dict):
                melon += tile.get('crop') == 'MELON'
                cow += tile.get('animal') == 'COW'
                sheep += tile.get('animal') == 'SHEEP'
                goose += tile.get('animal') == 'GOOSE'
    comparison = 'C<S' if cow < sheep else 'C>S' if cow > sheep else 'C=S'
    return shops[0] + '|' + ('M8+' if melon >= 8 else 'M<8') + '|' + comparison + ('|G+' if goose > 0 else '|G0')

def public_obs_features(observation):
    rival = observation['farms'][1 - int(observation['player'])]
    return {
        'rival_hands': len(rival.get('hands', [])),
        'rival_pasture_count': _pasture_count_from_tiles(rival.get('tiles', [])),
    }

def _pasture_count_from_tiles(tiles):
    return sum(isinstance(tile, dict) and tile.get('kind') == 'PASTURE'
               for row in tiles for tile in row)

def public_branch(hands):
    return 'shared151' if hands >= 5 else 'source'

def build_candidate():
    parent_bytes = PARENT_SOURCE.read_bytes()
    assert sha_bytes(parent_bytes) == PARENT_SHA
    text = parent_bytes.decode('utf-8')
    assert text.count(BRANCH_NEEDLE) == 1, text.count(BRANCH_NEEDLE)
    assert text.count(GLOBAL_NEEDLE) == 1, text.count(GLOBAL_NEEDLE)
    text = text.replace(GLOBAL_NEEDLE, GLOBAL_REPLACEMENT, 1)
    text = text.replace(BRANCH_NEEDLE, BRANCH_REPLACEMENT, 1)
    candidate_bytes = text.encode('utf-8') + b'\n\n' + LAYER.encode('utf-8')
    compile(candidate_bytes, str(HERE / 'candidate.py'), 'exec')
    (HERE / 'candidate_parent.py').write_bytes(parent_bytes)
    (HERE / 'layer.py').write_text(LAYER, encoding='utf-8', newline='\n')
    (HERE / 'candidate.py').write_bytes(candidate_bytes)
    assert sha(HERE / 'candidate_parent.py') == PARENT_SHA
    return sha(HERE / 'candidate.py')

def build_census():
    source = read(FEATURES)
    assert source['row_count'] == 208 and len(source['rows']) == 208
    census_rows = []
    for row in source['rows']:
        prov = row['provenance']
        path = Path(prov['trace_path'])
        actual_sha = sha(path)
        assert actual_sha == prov['trace_sha256'], (str(path), actual_sha, prov['trace_sha256'])
        observations = obs_through(path, 72)
        step1 = public_obs_features(observations[1])
        leaf72 = public_leaf_key(observations[72])
        frozen = row['selector_features']
        assert step1['rival_hands'] == frozen['obs1_rival_hands'], (prov['fixture_id'], prov['candidate_seat'])
        assert step1['rival_pasture_count'] == frozen['obs1_rival_pasture_count'], (prov['fixture_id'], prov['candidate_seat'])
        assert leaf72 == frozen['obs72_leaf_key'], (prov['fixture_id'], prov['candidate_seat'], leaf72, frozen['obs72_leaf_key'])
        baseline = public_branch(step1['rival_hands'])
        trigger = (step1['rival_hands'] == OVERRIDE_HANDS
                   and step1['rival_pasture_count'] == OVERRIDE_PASTURES)
        patched = 'source' if trigger else baseline
        source_key_match_without_latch = baseline == 'source' and leaf72 == TARGET_LEAF
        new_leaf_eligible = trigger and patched == 'source' and leaf72 == TARGET_LEAF
        census_rows.append({
            'fixture_id': prov['fixture_id'],
            'panel': prov['panel'],
            'seat': int(prov['candidate_seat']),
            'trace_path': str(path),
            'trace_sha256': actual_sha,
            'obs1_public_rival_hands': step1['rival_hands'],
            'obs1_public_rival_pasture_count': step1['rival_pasture_count'],
            'baseline_6d_branch': baseline,
            'isolated_branch': patched,
            'isolated_override_trigger': trigger,
            'branch_changed': patched != baseline,
            'obs72_public_leaf_key': leaf72,
            'baseline_source_and_leaf_collision': source_key_match_without_latch,
            'isolated_leaf_eligible': new_leaf_eligible,
        })
    trigger_rows = [r for r in census_rows if r['isolated_override_trigger']]
    leaf_rows = [r for r in census_rows if r['isolated_leaf_eligible']]
    changed_rows = [r for r in census_rows if r['branch_changed']]
    expected = {(TARGET, 0), (TARGET, 1)}
    assert {(r['fixture_id'], r['seat']) for r in trigger_rows} == expected
    assert {(r['fixture_id'], r['seat']) for r in changed_rows} == expected
    assert {(r['fixture_id'], r['seat']) for r in leaf_rows} == expected
    controls = [r for r in census_rows if r['panel'] == 'public54']
    assert len(controls) == 108 and not any(r['isolated_override_trigger'] for r in controls)
    top20 = [r for r in census_rows if r['fixture_id'].startswith('top20-')]
    public_wins = [r for r in census_rows if r['fixture_id'].startswith('public-win-')]
    assert top20 and public_wins
    assert not any(r['isolated_override_trigger'] for r in top20 + public_wins)
    assert len([r for r in census_rows if r['fixture_id'] == CHRIS]) == 2
    assert all((r['obs1_public_rival_hands'], r['obs1_public_rival_pasture_count']) == (6, 1)
               and not r['branch_changed'] for r in census_rows if r['fixture_id'] == CHRIS)
    assert all(r['obs72_public_leaf_key'] == TARGET_LEAF for r in leaf_rows)
    return {
        'complete': True,
        'source_feature_rows_sha256': sha(FEATURES),
        'source_6d_feature_rows_sha256': sha(BASE6_FEATURES),
        'row_count': len(census_rows),
        'panel_counts': dict(sorted(Counter(r['panel'] for r in census_rows).items())),
        'control_type_counts': {
            'public54_rows': len(controls),
            'top20_rows': len(top20),
            'public_win_rows': len(public_wins),
            'top20_and_public_win_overlap': sum(r in top20 for r in public_wins),
        },
        'selector': {
            'features': ['obs1 rival public hand count', 'obs1 rival public pasture tile count'],
            'predicate': 'rival_hands == 5 and rival_pasture_count == 1',
            'uses_fixture_id_seed_or_private_data': False,
            'target_seat_count': len(trigger_rows),
            'target_seats': sorted([{'fixture_id': r['fixture_id'], 'seat': r['seat']} for r in trigger_rows],
                                   key=lambda r: (r['fixture_id'], r['seat'])),
            'public54_trigger_count': sum(r['isolated_override_trigger'] for r in controls),
            'top20_trigger_count': sum(r['isolated_override_trigger'] for r in top20),
            'public_win_trigger_count': sum(r['isolated_override_trigger'] for r in public_wins),
            'branch_changed_count': len(changed_rows),
            'baseline_source_target_key_collision_count_without_latch': sum(
                r['baseline_source_and_leaf_collision'] for r in census_rows),
            'isolated_step72_leaf_count': len(leaf_rows),
        },
        'rows': census_rows,
    }

def static_action_checks():
    # This calls policy entrypoints over saved observations only. It runs no engine.
    focus = []
    candidate_path = HERE / 'candidate.py'
    for fixture_id in (TARGET, CHRIS):
        matching = [r for r in read(FEATURES)['rows']
                    if r['provenance']['fixture_id'] == fixture_id]
        assert len(matching) == 2
        for feature_row in matching:
            prov = feature_row['provenance']
            obs = obs_through(Path(prov['trace_path']), 72)
            parent = import_candidate(PARENT_SOURCE, f'iso_parent_{fixture_id}_{prov["candidate_seat"]}')
            candidate = import_candidate(candidate_path, f'iso_candidate_{fixture_id}_{prov["candidate_seat"]}')
            previous = None
            if fixture_id == TARGET:
                previous = import_candidate(OLD_PASTURE_CANDIDATE,
                                             f'iso_6d_pasture_{fixture_id}_{prov["candidate_seat"]}')
            parent_equal_steps = []
            previous_equal_steps = []
            candidate_parent_diff_steps = []
            route_delta = []
            for step in range(73):
                parent_action = parent.agent(copy.deepcopy(obs[step]))
                candidate_action = candidate.agent(copy.deepcopy(obs[step]))
                if candidate_action == parent_action:
                    parent_equal_steps.append(step)
                else:
                    candidate_parent_diff_steps.append(step)
                if previous is not None:
                    previous_action = previous.agent(copy.deepcopy(obs[step]))
                    if candidate_action == previous_action:
                        previous_equal_steps.append(step)
            telemetry = dict(candidate.agent.telemetry)
            branch = candidate._BRIDGE_SELECTED
            if fixture_id == TARGET:
                assert candidate._ISO_PASTURE_TRIGGERED is True
                assert branch == 'source'
                assert previous_equal_steps == list(range(73))
                assert telemetry.get('iso_pasture_leaf_key72') == TARGET_LEAF
                assert telemetry.get('iso_pasture_leaf_route72') == str(TARGET_ROUTE)
                assert telemetry.get('iso_pasture_leaf_errors') == 0
                assert telemetry.get('a44_ghost_wheat_active72') is False
                assert telemetry.get('a44_kwa_wheat_zero_active72') is False
                assert telemetry.get('a44_goose4_key72') == TARGET_LEAF
                expected_delta = {key for key in candidate._PIICE_BASE_ROUTE_MAP
                                  if key == 'BRUNCH_SPOT' or key.startswith('BRUNCH_SPOT|')}
                route_delta = sorted(key for key in set(candidate._PIICE_BASE_ROUTE_MAP) | set(candidate._DATA['route_map'])
                                     if candidate._PIICE_BASE_ROUTE_MAP.get(key) != candidate._DATA['route_map'].get(key))
                assert set(route_delta) == expected_delta, sorted(set(route_delta) ^ expected_delta)
                assert all(candidate._DATA['route_map'][key] == TARGET_ROUTE for key in expected_delta)
                assert not candidate_parent_diff_steps or candidate_parent_diff_steps[0] >= 1
            else:
                assert candidate._ISO_PASTURE_TRIGGERED is False
                assert branch == 'shared151'
                assert parent_equal_steps == list(range(73))
                assert not candidate_parent_diff_steps
                assert telemetry.get('iso_pasture_leaf_route72') == ''
                assert telemetry.get('iso_pasture_leaf_errors') == 0
                assert telemetry.get('a44_ghost_wheat_active72') is False
                assert telemetry.get('a44_kwa_wheat_zero_active72') is False
                assert telemetry.get('iso_pasture_reset_route_map_matches') is True
            focus.append({
                'fixture_id': fixture_id,
                'seat': int(prov['candidate_seat']),
                'trace_sha256': prov['trace_sha256'],
                'candidate_vs_parent_equal_steps': parent_equal_steps,
                'candidate_vs_parent_diff_steps': candidate_parent_diff_steps,
                'candidate_vs_previous_6d_pasture_equal_steps': previous_equal_steps,
                'candidate_selected_branch': branch,
                'candidate_trigger_latch': bool(candidate._ISO_PASTURE_TRIGGERED),
                'step72_leaf_key': telemetry.get('iso_pasture_leaf_key72'),
                'step72_leaf_route': telemetry.get('iso_pasture_leaf_route72'),
                'step72_leaf_turns': telemetry.get('iso_pasture_leaf_turns'),
                'ghost_inactive': telemetry.get('a44_ghost_wheat_active72') is False,
                'kwa_inactive': telemetry.get('a44_kwa_wheat_zero_active72') is False,
                'piice_inactive_through72': telemetry.get('piice_active144') is False,
                'route_map_delta_keys': route_delta,
            })
    assert all(r['candidate_vs_parent_equal_steps'] == list(range(73)) for r in focus
               if r['fixture_id'] == CHRIS)
    assert all(r['candidate_vs_previous_6d_pasture_equal_steps'] == list(range(73)) for r in focus
               if r['fixture_id'] == TARGET)
    return focus

def main():
    assert sha(PARENT_SOURCE) == PARENT_SHA
    assert sha(V4_SOURCE) == V4_SHA
    assert sha(BASE6 / 'candidate.py') == BASE6_SHA
    assert sha(OLD_PASTURE_CANDIDATE) == OLD_PASTURE_SHA
    assert sha(OLD_PREFIX_RESULTS) == 'e966821dbcac8d95a18e6f6c3e827bdae04a8753ea23ed53534e3f8ae5641406'
    assert sha(OLD_PREFIX_MANIFEST) == '98a379d182082928e8aea2fc172d215d48bc1caefd7870a3eb480bcf20189bb8'
    parent_manifest = read(COMPOSED / 'frozen_manifest.json')
    assert parent_manifest.get('complete') is True
    assert parent_manifest.get('candidate_sha256') == PARENT_SHA
    parent_receipt = read(COMPOSED / 'outcome_receipt.json')
    assert parent_receipt.get('complete') is True and parent_receipt.get('candidate_sha256') == PARENT_SHA
    v4_receipt = read(V4 / 'outcome_run_20260929' / 'outcome_receipt.json')
    assert v4_receipt.get('candidate_sha256') == V4_SHA
    candidate_sha = build_candidate()
    census = build_census()
    dump(HERE / 'feature_census.json', census)
    action_checks = static_action_checks()
    parent_module = import_candidate(PARENT_SOURCE, 'iso_parent_constants')
    composition = {
        'parent_candidate_sha256': PARENT_SHA,
        'v4_parent_candidate_sha256': V4_SHA,
        'ghost_key72': getattr(parent_module, '_A44_GHOST_WHEAT_KEY72'),
        'ghost_key_disjoint_from_target': getattr(parent_module, '_A44_GHOST_WHEAT_KEY72') != TARGET_LEAF,
        'kwa_key72': getattr(parent_module, '_A44_KWA_WHEAT_ZERO_KEY'),
        'kwa_key_disjoint_from_target': getattr(parent_module, '_A44_KWA_WHEAT_ZERO_KEY') != TARGET_LEAF,
        'goose4_rule_keys': sorted(parent_module._A44_GOOSE4_RULES),
        'goose4_rules_disjoint_from_target': TARGET_LEAF not in parent_module._A44_GOOSE4_RULES,
        'piice_key72': getattr(parent_module, '_PIICE_KEY72'),
        'piice_pair': getattr(parent_module, '_PIICE_PAIR'),
        'piice_key_disjoint_from_target': getattr(parent_module, '_PIICE_KEY72') != TARGET_LEAF,
        'piice_pair_disjoint_from_target_first_shop': getattr(parent_module, '_PIICE_PAIR').split('|')[0] != 'BRUNCH_SPOT',
        'policy_action_comparison_scope': '4 target/control seat traces, observations 0..72; actions only, no transitions',
    }
    assert composition['ghost_key_disjoint_from_target']
    assert composition['kwa_key_disjoint_from_target']
    assert composition['goose4_rules_disjoint_from_target']
    assert composition['piice_key_disjoint_from_target']
    assert composition['piice_pair_disjoint_from_target_first_shop']
    static = {
        'complete': True,
        'static_only': True,
        'engine_or_native_transitions': 0,
        'candidate_sha256': candidate_sha,
        'parent_candidate_sha256': PARENT_SHA,
        'v4_parent_candidate_sha256': V4_SHA,
        'feature_census_sha256': sha(HERE / 'feature_census.json'),
        'feature_census_row_count': 208,
        'selector_target_seats': census['selector']['target_seats'],
        'selector_trigger_count': census['selector']['target_seat_count'],
        'public54_trigger_count': census['selector']['public54_trigger_count'],
        'top20_trigger_count': census['selector']['top20_trigger_count'],
        'public_win_trigger_count': census['selector']['public_win_trigger_count'],
        'isolated_leaf_count': census['selector']['isolated_step72_leaf_count'],
        'composition': composition,
        'focus_action_checks': action_checks,
        'all_static_gates_passed': True,
    }
    dump(HERE / 'static_preflight.json', static)
    external_paths = [
        PARENT_SOURCE, V4_SOURCE, COMPOSED / 'frozen_manifest.json',
        COMPOSED / 'outcome_receipt.json', COMPOSED / 'prefix_probe.json',
        COMPOSED / 'layer.py', V4 / 'panel_v4.json',
        V4 / 'outcome_run_20260929' / 'outcome_receipt.json',
        V4 / 'outcome_run_20260929' / 'frozen_manifest.json',
        BASE6 / 'candidate.py', BASE6_FEATURES, BASE6 / 'combined_results.json',
        BASE6 / 'parent_panel.json', FEATURES,
        PASTURE / 'candidate_pasture_guard_source_leaf.py',
        PASTURE / 'pool.json', OLD_PASTURE_CANDIDATE,
        OLD_PREFIX_RESULTS, OLD_PREFIX_MANIFEST,
    ]
    external = {str(p.resolve()): sha(p) for p in external_paths}
    trace_bindings = {r['trace_path']: r['trace_sha256'] for r in census['rows']}
    internal_names = ['PLAN.md', 'build_preflight.py', 'candidate_parent.py',
                      'candidate.py', 'layer.py', 'feature_census.json',
                      'static_preflight.json']
    manifest = {
        'schema': 'a44-v4-piice-isolated-pasture-static-freeze-v1',
        'complete': True,
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'parent_candidate_sha256': PARENT_SHA,
        'v4_parent_candidate_sha256': V4_SHA,
        'candidate_sha256': candidate_sha,
        'selector': 'obs1 public rival hands == 5 and rival public pasture tile count == 1',
        'leaf': {'requires_step1_latch': True, 'source_branch_only': True,
                 'step72_key': TARGET_LEAF, 'route': TARGET_ROUTE},
        'files': {name: sha(HERE / name) for name in internal_names},
        'external_inputs': external,
        'trace_sha256_bindings': trace_bindings,
        'required_workers': 1,
        'simulation_jobs_run': 0,
        'engine_transitions_run': 0,
        'outcome_runner_included': False,
    }
    dump(HERE / 'frozen_manifest.json', manifest)
    manifest_sha = sha(HERE / 'frozen_manifest.json')
    receipt = {
        'complete': True,
        'static_only': True,
        'candidate_sha256': candidate_sha,
        'parent_candidate_sha256': PARENT_SHA,
        'feature_census_sha256': sha(HERE / 'feature_census.json'),
        'static_preflight_sha256': sha(HERE / 'static_preflight.json'),
        'manifest_path': str((HERE / 'frozen_manifest.json').resolve()),
        'manifest_sha256': manifest_sha,
        'simulation_jobs_run': 0,
        'engine_transitions_run': 0,
    }
    dump(HERE / 'freeze_receipt.json', receipt)
    verify()
    print(json.dumps({
        'candidate_sha256': candidate_sha,
        'parent_candidate_sha256': PARENT_SHA,
        'manifest_sha256': manifest_sha,
        'feature_census_sha256': sha(HERE / 'feature_census.json'),
        'static_preflight_sha256': sha(HERE / 'static_preflight.json'),
        'trigger_seats': census['selector']['target_seats'],
        'public54_trigger_count': census['selector']['public54_trigger_count'],
        'top20_trigger_count': census['selector']['top20_trigger_count'],
        'public_win_trigger_count': census['selector']['public_win_trigger_count'],
        'static_gates_passed': True,
    }, indent=2))

def verify():
    manifest = read(HERE / 'frozen_manifest.json')
    assert manifest['complete'] is True
    assert manifest['candidate_sha256'] == sha(HERE / 'candidate.py')
    assert manifest['parent_candidate_sha256'] == sha(HERE / 'candidate_parent.py') == PARENT_SHA
    assert manifest['files']['PLAN.md'] == sha(HERE / 'PLAN.md')
    assert manifest['files']['build_preflight.py'] == sha(HERE / 'build_preflight.py')
    assert manifest['files']['candidate.py'] == sha(HERE / 'candidate.py')
    assert manifest['files']['candidate_parent.py'] == sha(HERE / 'candidate_parent.py')
    assert manifest['files']['layer.py'] == sha(HERE / 'layer.py')
    assert manifest['files']['feature_census.json'] == sha(HERE / 'feature_census.json')
    assert manifest['files']['static_preflight.json'] == sha(HERE / 'static_preflight.json')
    for path, digest in manifest['external_inputs'].items():
        assert sha(Path(path)) == digest, path
    for path, digest in manifest['trace_sha256_bindings'].items():
        assert sha(Path(path)) == digest, path
    receipt = read(HERE / 'freeze_receipt.json')
    assert receipt['manifest_sha256'] == sha(HERE / 'frozen_manifest.json')
    assert receipt['candidate_sha256'] == sha(HERE / 'candidate.py')
    static = read(HERE / 'static_preflight.json')
    assert static['all_static_gates_passed'] is True and static['engine_or_native_transitions'] == 0

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify()
        print('static freeze verified')
    else:
        main()
