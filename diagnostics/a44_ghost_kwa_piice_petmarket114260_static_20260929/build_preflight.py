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
PARENT_DIR = ROOT / 'diagnostics/a44_ghost_kwa_piice_combo_20260929'
PANEL_DIR = ROOT / 'diagnostics/a44_ghost_kwa_piice_goalpanel_20260929'
FEATURES = ROOT / 'diagnostics/pasture_guard_source_leaf_20260928/feature_rows.json'
ROUTE_SOURCE = ROOT / 'diagnostics/public_90_research_20260928/candidates/PET_CAFE_113517834.py'
TARGET = 'live-114260122'
CONTROL = 'public-win-114192390'
LEAF = 'PET_CAFE|M8+|C>S|G0'
ROUTE = 113517834
TARGET_PARENT_SHA = '8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62'

LAYER = r'''
# Isolated public Pet Cafe gate for route 113517834.
_A44_PET_MARKET_GATE_PARENT = agent
_A44_PET_MARKET_GATE_LEAF = 'PET_CAFE|M8+|C>S|G0'
_A44_PET_MARKET_GATE_ROUTE = 113517834
_A44_PET_MARKET_GATE_MELON = 12
_A44_PET_MARKET_GATE_WHEAT = 9975
_A44_PET_MARKET_GATE_ACTIVE = False
_A44_PET_MARKET_GATE_STATS = {
    'a44_pet_market_gate_key72': '',
    'a44_pet_market_gate_rival_melon72': -1,
    'a44_pet_market_gate_wheat_stock72': -1,
    'a44_pet_market_gate_active72': False,
    'a44_pet_market_gate_route72': '',
    'a44_pet_market_gate_turns': 0,
    'a44_pet_market_gate_errors': 0,
}

def _a44_pet_market_gate_melon_count(observation):
    rival = observation['farms'][1 - int(observation['player'])]
    return sum(
        isinstance(tile, dict) and tile.get('crop') == 'MELON'
        for row in rival.get('tiles', [])
        for tile in row
    )

def _a44_pet_market_gate_reset():
    global _A44_PET_MARKET_GATE_ACTIVE
    _A44_PET_MARKET_GATE_ACTIVE = False
    _A44_PET_MARKET_GATE_STATS.update(
        a44_pet_market_gate_key72='',
        a44_pet_market_gate_rival_melon72=-1,
        a44_pet_market_gate_wheat_stock72=-1,
        a44_pet_market_gate_active72=False,
        a44_pet_market_gate_route72='',
        a44_pet_market_gate_turns=0,
        a44_pet_market_gate_errors=0,
    )

def agent(observation, configuration=None):
    global _A44_PET_MARKET_GATE_ACTIVE
    step = int(observation['step'])
    if step == 0:
        _a44_pet_market_gate_reset()
    if step == 72:
        leaf = _a44_goose4_key(observation)
        rival_melon = _a44_pet_market_gate_melon_count(observation)
        wheat_stock = int(observation['market']['inventory']['WHEAT'])
        active = (leaf == _A44_PET_MARKET_GATE_LEAF
                  and rival_melon == _A44_PET_MARKET_GATE_MELON
                  and wheat_stock == _A44_PET_MARKET_GATE_WHEAT)
        _A44_PET_MARKET_GATE_STATS.update(
            a44_pet_market_gate_key72=leaf,
            a44_pet_market_gate_rival_melon72=rival_melon,
            a44_pet_market_gate_wheat_stock72=wheat_stock,
            a44_pet_market_gate_active72=bool(active),
        )
        if active:
            try:
                _a44_goose4_commit(_A44_PET_MARKET_GATE_LEAF,
                                   _A44_PET_MARKET_GATE_ROUTE)
                _A44_PET_MARKET_GATE_ACTIVE = True
                _A44_PET_MARKET_GATE_STATS[
                    'a44_pet_market_gate_route72'] = str(
                        _A44_PET_MARKET_GATE_ROUTE)
            except Exception:
                _A44_PET_MARKET_GATE_STATS[
                    'a44_pet_market_gate_errors'] += 1

    result = _A44_PET_MARKET_GATE_PARENT(observation, configuration)
    if step >= 72 and _A44_PET_MARKET_GATE_ACTIVE:
        _A44_PET_MARKET_GATE_STATS['a44_pet_market_gate_turns'] += 1
    agent.telemetry.update(getattr(_A44_PET_MARKET_GATE_PARENT,
                                   'telemetry', {}))
    agent.telemetry.update(_A44_PET_MARKET_GATE_STATS)
    return result

agent.telemetry = {}

def kaggle_a44_pet_market_gate_entrypoint(observation, configuration=None):
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


def canonical_sha(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=True).encode('utf-8')
    return sha_bytes(payload)


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


def observations(path: Path, last_step: int | None = None):
    result = {}
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            step = int(row.get('step', -1))
            if step < 0:
                continue
            result[step] = row['observation']
            if last_step is not None and step == last_step:
                break
    return result


def public_gate_features(observation, parent_module):
    rival = observation['farms'][1 - int(observation['player'])]
    melons = sum(
        isinstance(tile, dict) and tile.get('crop') == 'MELON'
        for row in rival.get('tiles', [])
        for tile in row
    )
    leaf = parent_module._a44_goose4_key(observation)
    wheat = int(observation['market']['inventory']['WHEAT'])
    return {
        'leaf72': leaf,
        'rival_visible_melon_count72': melons,
        'public_wheat_inventory72': wheat,
        'trigger': leaf == LEAF and melons == 12 and wheat == 9975,
    }


def build_candidate(parent_source: Path):
    parent_bytes = parent_source.read_bytes()
    assert sha_bytes(parent_bytes) == TARGET_PARENT_SHA
    route_parent = import_candidate(parent_source, 'pet_gate_route_parent')
    route_source = import_candidate(ROUTE_SOURCE, 'pet_gate_route_source')
    parent_route = route_parent._DATA['routes'][str(ROUTE)]
    source_route = route_source._DATA['routes'][str(ROUTE)]
    assert parent_route == source_route
    route_identity = {
        'route_id': ROUTE,
        'steps': len(parent_route),
        'parent_canonical_schedule_sha256': canonical_sha(parent_route),
        'source_canonical_schedule_sha256': canonical_sha(source_route),
        'schedule_equal': True,
    }

    candidate_bytes = parent_bytes + b'\n\n' + LAYER.encode('utf-8')
    compile(candidate_bytes, str(HERE / 'candidate.py'), 'exec')
    (HERE / 'candidate_parent.py').write_bytes(parent_bytes)
    (HERE / 'layer.py').write_text(LAYER, encoding='utf-8', newline='\n')
    (HERE / 'candidate.py').write_bytes(candidate_bytes)
    return route_identity, sha(HERE / 'candidate.py')


def trigger_census(feature_rows, parent_module):
    rows = []
    for feature in feature_rows['rows']:
        prov = feature['provenance']
        trace = Path(prov['trace_path'])
        trace_sha = sha(trace)
        assert trace_sha == prov['trace_sha256'], (str(trace), trace_sha)
        obs = observations(trace, 72)
        assert set(obs) == set(range(73)), (str(trace), sorted(obs))
        public = public_gate_features(obs[72], parent_module)
        assert public['leaf72'] == feature['selector_features']['obs72_leaf_key'], (
            prov['fixture_id'], prov['candidate_seat'], public['leaf72'],
            feature['selector_features']['obs72_leaf_key'])
        rows.append({
            'fixture_id': prov['fixture_id'],
            'panel': prov['panel'],
            'seat': int(prov['candidate_seat']),
            'trace_path': str(trace.resolve()),
            'trace_sha256': trace_sha,
            **public,
        })
    hits = [r for r in rows if r['trigger']]
    return rows, hits


def action_prefix_comparison(feature_rows, parent_module, candidate_module):
    rows = []
    call_count = 0
    for feature in feature_rows['rows']:
        prov = feature['provenance']
        trace = Path(prov['trace_path'])
        obs = observations(trace, 72)
        assert set(obs) == set(range(73))
        equal_steps = []
        differences = []
        for step in range(73):
            parent_action = parent_module.agent(copy.deepcopy(obs[step]))
            candidate_action = candidate_module.agent(copy.deepcopy(obs[step]))
            call_count += 2
            (equal_steps if parent_action == candidate_action else differences).append(step)
        telemetry = dict(candidate_module.agent.telemetry)
        rows.append({
            'fixture_id': prov['fixture_id'],
            'seat': int(prov['candidate_seat']),
            'steps_compared': 73,
            'equal_steps': equal_steps,
            'different_steps': differences,
            'gate_triggered': bool(telemetry.get('a44_pet_market_gate_active72')),
            'candidate_route': telemetry.get('a44_pet_market_gate_route72', ''),
            'gate_key': telemetry.get('a44_pet_market_gate_key72', ''),
            'rival_melons': telemetry.get('a44_pet_market_gate_rival_melon72', -1),
            'wheat_stock': telemetry.get('a44_pet_market_gate_wheat_stock72', -1),
            'route_map_delta_from_parent': sorted(
                key for key in set(candidate_module._DATA['route_map'])
                | set(parent_module._DATA['route_map'])
                if candidate_module._DATA['route_map'].get(key)
                != parent_module._DATA['route_map'].get(key)),
        })
    return rows, call_count


def full_focus_comparison(feature_rows, parent_source: Path, candidate_path: Path):
    focus = []
    total_calls = 0
    targets = [r for r in feature_rows['rows']
               if r['provenance']['fixture_id'] in (TARGET, CONTROL)]
    assert len(targets) == 4
    for feature in targets:
        prov = feature['provenance']
        trace = Path(prov['trace_path'])
        obs = observations(trace)
        assert 0 in obs and 72 in obs
        parent = import_candidate(parent_source,
                                  f'pet_gate_full_parent_{prov["fixture_id"]}_{prov["candidate_seat"]}')
        candidate = import_candidate(candidate_path,
                                     f'pet_gate_full_candidate_{prov["fixture_id"]}_{prov["candidate_seat"]}')
        equal = []
        different = []
        for step in sorted(obs):
            parent_action = parent.agent(copy.deepcopy(obs[step]))
            candidate_action = candidate.agent(copy.deepcopy(obs[step]))
            total_calls += 2
            (equal if parent_action == candidate_action else different).append(step)
        telemetry = dict(candidate.agent.telemetry)
        focus.append({
            'fixture_id': prov['fixture_id'],
            'seat': int(prov['candidate_seat']),
            'trace_sha256': prov['trace_sha256'],
            'observations_compared': len(obs),
            'first_step': min(obs),
            'last_step': max(obs),
            'different_step_count': len(different),
            'first_different_steps': different[:8],
            'last_different_steps': different[-4:],
            'gate_triggered': bool(telemetry.get('a44_pet_market_gate_active72')),
            'candidate_route': telemetry.get('a44_pet_market_gate_route72', ''),
        })
    return focus, total_calls


def input_bindings(census_rows):
    paths = [
        PARENT_DIR / 'candidate.py', PARENT_DIR / 'candidate_parent.py',
        PARENT_DIR / 'layer.py', PARENT_DIR / 'build_preflight.py',
        PARENT_DIR / 'frozen_manifest.json', PARENT_DIR / 'outcome_receipt.json',
        PARENT_DIR / 'prefix_probe.json',
        PANEL_DIR / 'candidate.py', PANEL_DIR / 'PLAN.md',
        PANEL_DIR / 'panel.json', PANEL_DIR / 'outcomes.jsonl',
        PANEL_DIR / 'frozen_manifest.json', PANEL_DIR / 'outcome_receipt.json',
        PANEL_DIR / 'static_preflight.json', PANEL_DIR / 'run.py',
        PANEL_DIR / 'build_panel.py',
        FEATURES, ROUTE_SOURCE,
        ROOT / 'diagnostics/public_90_research_20260928/RESULTS.md',
        ROOT / 'diagnostics/production_leaf_selector_20260928/RESULTS.md',
        ROOT / 'diagnostics/production_pair_continuations_20260928/RESULTS.md',
        ROOT / 'diagnostics/production_pair_continuations_20260928/screen.jsonl',
        ROOT / 'diagnostics/production_pair_continuations_20260928/selection.json',
    ]
    external = {str(p.resolve()): sha(p) for p in paths}
    traces = {r['trace_path']: r['trace_sha256'] for r in census_rows}
    return external, traces


def run_static():
    parent_source = PARENT_DIR / 'candidate.py'
    assert sha(parent_source) == TARGET_PARENT_SHA
    parent_manifest = read(PARENT_DIR / 'frozen_manifest.json')
    assert parent_manifest['complete'] is True
    assert parent_manifest['candidate_sha256'] == TARGET_PARENT_SHA
    panel_manifest = read(PANEL_DIR / 'frozen_manifest.json')
    panel_receipt = read(PANEL_DIR / 'outcome_receipt.json')
    assert panel_manifest['candidate_sha256'] == TARGET_PARENT_SHA
    assert panel_receipt['candidate_sha256'] == TARGET_PARENT_SHA
    assert read(PANEL_DIR / 'static_preflight.json')['engine_transitions'] == 0

    route_identity, candidate_sha = build_candidate(parent_source)
    feature_rows = read(FEATURES)
    assert feature_rows['row_count'] == 208 and len(feature_rows['rows']) == 208
    parent = import_candidate(parent_source, 'pet_gate_census_parent')
    candidate = import_candidate(HERE / 'candidate.py', 'pet_gate_census_candidate')
    census_rows, hits = trigger_census(feature_rows, parent)

    target_hits = sorted((r['fixture_id'], r['seat']) for r in hits
                         if r['fixture_id'] == TARGET)
    control_hits = sorted((r['fixture_id'], r['seat']) for r in hits
                          if r['fixture_id'] == CONTROL)
    unexpected_hits = sorted((r['fixture_id'], r['seat']) for r in hits
                             if r['fixture_id'] not in (TARGET, CONTROL))
    desired_hits = sorted([(TARGET, 0), (TARGET, 1)])
    exclusive_gate = (sorted((r['fixture_id'], r['seat']) for r in hits)
                      == desired_hits)

    prefix_rows, prefix_calls = action_prefix_comparison(
        feature_rows, parent, candidate)
    focus_rows, focus_calls = full_focus_comparison(
        feature_rows, parent_source, HERE / 'candidate.py')
    action_diffs_pre72 = [
        {'fixture_id': r['fixture_id'], 'seat': r['seat'], 'step': step}
        for r in prefix_rows for step in r['different_steps'] if step < 72
    ]
    control_diffs = [r for r in focus_rows if r['fixture_id'] == CONTROL
                     and r['different_step_count']]
    focus_by_id = {(r['fixture_id'], r['seat']): r for r in focus_rows}
    control_action_equal = all(
        focus_by_id[(CONTROL, seat)]['different_step_count'] == 0
        for seat in (0, 1))
    target_action_change_after72 = all(
        focus_by_id[(TARGET, seat)]['first_different_steps']
        and min(focus_by_id[(TARGET, seat)]['first_different_steps']) >= 72
        for seat in (0, 1))

    outcomes = []
    with (PANEL_DIR / 'outcomes.jsonl').open('r', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row.get('fixture_id') == TARGET:
                outcomes.append(row)
    assert len(outcomes) == 2
    target_panel_observation = [{
        'fixture_id': r['fixture_id'],
        'seat': r['candidate_seat'],
        'candidate_sha256': r['candidate_sha256'],
        'leaf72': r['actual']['candidate_telemetry'].get('a44_goose4_key72'),
        'wheat_stock72': r['actual']['candidate_telemetry'].get('a44_ghost_wheat_stock72'),
        'margin': r['actual']['margin'],
    } for r in outcomes]
    target_panel_matches = all(
        r['candidate_sha256'] == TARGET_PARENT_SHA
        and r['leaf72'] == LEAF and r['wheat_stock72'] == 9975
        for r in target_panel_observation)

    gates = {
        'exact_parent_candidate': sha(parent_source) == TARGET_PARENT_SHA,
        'route_schedule_matches_bound_source': route_identity['schedule_equal'],
        'all_208_trace_hashes_verified': len(census_rows) == 208,
        'target_exactly_both_seats_trigger': target_hits == desired_hits,
        'control_both_seats_inactive': control_hits == [],
        'no_unexpected_trigger_seats': unexpected_hits == [],
        'no_pre72_policy_action_differences': action_diffs_pre72 == [],
        'control_policy_actions_match_parent': control_action_equal,
        'target_actions_only_change_at_or_after_step72': target_action_change_after72,
        'exact_8f_panel_target_telemetry_matches_leaf_and_stock': target_panel_matches,
    }
    freeze_allowed = all(gates.values())
    static = {
        'schema': 'a44-v5-pet-market-114260-static-stage-v1',
        'complete': True,
        'static_only': True,
        'freeze_allowed': freeze_allowed,
        'engine_transitions': 0,
        'native_games': 0,
        'candidate_sha256': candidate_sha,
        'parent_candidate_sha256': TARGET_PARENT_SHA,
        'route_source_sha256': sha(ROUTE_SOURCE),
        'route_identity': route_identity,
        'feature_rows_sha256': sha(FEATURES),
        'census_row_count': len(census_rows),
        'gate': {
            'leaf': LEAF,
            'rival_visible_melon_count': 12,
            'public_wheat_inventory': 9975,
            'route': ROUTE,
        },
        'trigger_count': len(hits),
        'trigger_seats': sorted([
            {'fixture_id': r['fixture_id'], 'seat': r['seat']}
            for r in hits], key=lambda r: (r['fixture_id'], r['seat'])),
        'target_trigger_seats': target_hits,
        'control_trigger_seats': control_hits,
        'unexpected_trigger_seats': unexpected_hits,
        'action_policy_calls': prefix_calls + focus_calls,
        'pre72_action_differences': action_diffs_pre72,
        'focus_full_trace_action_comparisons': focus_rows,
        'target_8f_panel_telemetry': target_panel_observation,
        'gates': gates,
        'census': census_rows,
        'prefix_action_checks': prefix_rows,
    }
    dump(HERE / 'static_preflight.json', static)
    external, traces = input_bindings(census_rows)
    internal_names = ['PLAN.md', 'build_preflight.py', 'candidate_parent.py',
                      'candidate.py', 'layer.py', 'static_preflight.json']
    stage = {
        'schema': 'a44-v5-pet-market-114260-unfrozen-stage-v1',
        'complete': True,
        'frozen': False,
        'freeze_allowed': freeze_allowed,
        'staged_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'candidate_sha256': candidate_sha,
        'parent_candidate_sha256': TARGET_PARENT_SHA,
        'feature_rows_sha256': sha(FEATURES),
        'static_preflight_sha256': sha(HERE / 'static_preflight.json'),
        'internal_files': {name: sha(HERE / name) for name in internal_names},
        'external_inputs': external,
        'trace_sha256_bindings': traces,
        'target_seats_required': [{'fixture_id': TARGET, 'seat': 0},
                                  {'fixture_id': TARGET, 'seat': 1}],
        'control_seats_required_inactive_and_action_equal': [
            {'fixture_id': CONTROL, 'seat': 0},
            {'fixture_id': CONTROL, 'seat': 1}],
        'gate_failures': sorted(k for k, value in gates.items() if not value),
        'engine_transitions': 0,
        'native_games': 0,
    }
    dump(HERE / 'stage_manifest.json', stage)
    status_lines = [
        '# Candidate status: unfrozen',
        '',
        f"`freeze_allowed`: **{str(freeze_allowed).lower()}**.",
        '',
        'The exact target-only gate failed on the bound 208-seat trace census. '
        'The control `public-win-114192390` matches in both seats, so this '
        'package is staged for review only and has no frozen manifest or game runner.',
        '',
        f"Candidate SHA-256: `{candidate_sha}`.",
        f"8f parent SHA-256: `{TARGET_PARENT_SHA}`.",
        f"Static preflight SHA-256: `{sha(HERE / 'static_preflight.json')}`.",
        '',
        'No native transitions, simulator games, Kaggle access, `main.py` edits, '
        'or `agent.md` edits were performed.',
    ]
    (HERE / 'CANDIDATE_STATUS.md').write_text('\n'.join(status_lines) + '\n',
                                                   encoding='utf-8', newline='\n')
    stage = read(HERE / 'stage_manifest.json')
    stage['internal_files']['CANDIDATE_STATUS.md'] = sha(HERE / 'CANDIDATE_STATUS.md')
    stage['internal_files']['build_preflight.py'] = sha(HERE / 'build_preflight.py')
    dump(HERE / 'stage_manifest.json', stage)
    print(json.dumps({
        'candidate_sha256': candidate_sha,
        'parent_candidate_sha256': TARGET_PARENT_SHA,
        'route_schedule_sha256': route_identity['parent_canonical_schedule_sha256'],
        'trace_rows': len(census_rows),
        'trigger_count': len(hits),
        'trigger_seats': static['trigger_seats'],
        'control_action_equal': control_action_equal,
        'freeze_allowed': freeze_allowed,
        'failed_gates': stage['gate_failures'],
        'engine_transitions': 0,
        'native_games': 0,
    }, indent=2))


def verify_stage():
    stage = read(HERE / 'stage_manifest.json')
    assert stage['complete'] is True and stage['frozen'] is False
    assert stage['candidate_sha256'] == sha(HERE / 'candidate.py')
    assert stage['parent_candidate_sha256'] == sha(HERE / 'candidate_parent.py') == TARGET_PARENT_SHA
    assert stage['internal_files']['PLAN.md'] == sha(HERE / 'PLAN.md')
    assert stage['internal_files']['build_preflight.py'] == sha(HERE / 'build_preflight.py')
    assert stage['internal_files']['CANDIDATE_STATUS.md'] == sha(HERE / 'CANDIDATE_STATUS.md')
    assert stage['internal_files']['candidate.py'] == sha(HERE / 'candidate.py')
    assert stage['internal_files']['candidate_parent.py'] == sha(HERE / 'candidate_parent.py')
    assert stage['internal_files']['layer.py'] == sha(HERE / 'layer.py')
    assert stage['internal_files']['static_preflight.json'] == sha(HERE / 'static_preflight.json')
    assert stage['static_preflight_sha256'] == sha(HERE / 'static_preflight.json')
    for path, digest in stage['external_inputs'].items():
        assert sha(Path(path)) == digest, path
    for path, digest in stage['trace_sha256_bindings'].items():
        assert sha(Path(path)) == digest, path
    static = read(HERE / 'static_preflight.json')
    assert static['freeze_allowed'] is stage['freeze_allowed']
    return static


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        static = verify_stage()
        print(json.dumps({'stage_integrity_verified': True,
                          'frozen': False,
                          'freeze_allowed': static['freeze_allowed'],
                          'trigger_seats': static['trigger_seats']}, indent=2))
    else:
        run_static()
