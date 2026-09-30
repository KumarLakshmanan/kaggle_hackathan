"""Build three frozen top-rank single-tape controls and static receipts."""
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import importlib.util
import inspect
import json
import runpy
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_DIR = ROOT / 'diagnostics' / 'fresh90_refresh_20260929'
SUMMARY = SOURCE_DIR / 'routes' / 'development_latest' / 'summary.json'
OLD_CANDIDATE_DIR = ROOT / 'diagnostics' / 'fresh90_current_opening_20260929'
EXPECTED_SUMMARY_SHA = '9dc48578eb5e828d8038ff39821c8e27ddb12b1a7a4812a87622003c2db63e9c'
EXPECTED_PLAN_SHA = (HERE / 'PLAN_SHA256.txt').read_text(encoding='utf-8').splitlines()[0].split()[0].lower()
ENGINE_VERSION = '1.32.7'
TARGET_RANKS = (1, 2, 3)
INVESTMENT_TYPES = {'HIRE', 'BUY_LAND', 'BUY_ANIMAL', 'BUY_SEED', 'BUY_SEEDS'}
ALLOWED_IMPORTS = {'base64', 'copy', 'json', 'zlib'}

CANDIDATE_TEMPLATE = '''"""Frozen single-tape control; generated from a public development route."""
import base64
import copy
import json
import zlib

_PACKED = "__PACKED__"
_ACTIONS = json.loads(zlib.decompress(base64.b85decode(_PACKED.encode("ascii"))).decode("utf-8"))
_CALLS = 0

def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)

def agent(observation, configuration=None):
    del configuration
    global _CALLS
    raw_step = _get(observation, "step", None)
    try:
        step = int(raw_step) if raw_step is not None else _CALLS
    except (TypeError, ValueError):
        step = _CALLS
    _CALLS += 1
    step = max(0, min(step, 718))
    return copy.deepcopy(_ACTIONS[step])

def kaggle_fresh_opening_router_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def decode_replay(raw: bytes) -> dict:
    value = json.loads(raw.decode('utf-8'))
    while isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError('decoded replay is not a JSON object')
    return value


def verify_source(row: dict) -> tuple[list, dict]:
    key = (int(row['rank']), int(row['episode_id']))
    if not row.get('runner_eligible') or int(row.get('frames', -1)) != 720:
        raise RuntimeError(f'route is not runner-eligible: {key}')
    if row.get('engine_version') != ENGINE_VERSION or row.get('source_statuses') != ['DONE', 'DONE']:
        raise RuntimeError(f'engine/status mismatch: {key}')

    route_path = Path(row['path'])
    route_payload = json.loads(gzip.decompress(route_path.read_bytes()))
    actions = route_payload['actions']
    action_sha = sha(canonical(actions))
    if len(actions) != 719 or action_sha != row['action_sha256']:
        raise RuntimeError(f'action tape hash/length mismatch: {key}')

    replay_path = Path(row['replay_path'])
    replay_archive = replay_path.read_bytes()
    replay_raw = gzip.decompress(replay_archive)
    replay = decode_replay(replay_raw)
    replay_archive_sha = sha(replay_archive)
    replay_sha = sha(replay_raw)
    if replay_archive_sha != row['replay_archive_sha256'] or replay_sha != row['replay_sha256']:
        raise RuntimeError(f'replay archive/raw hash mismatch: {key}')
    if replay.get('statuses') != ['DONE', 'DONE'] or replay.get('module_version') != ENGINE_VERSION:
        raise RuntimeError(f'replay completion/engine mismatch: {key}')
    if len(replay.get('steps') or []) != 720:
        raise RuntimeError(f'replay frame count mismatch: {key}')
    seat = int(row['source_seat'])
    team_names = (replay.get('info') or {}).get('TeamNames') or []
    if len(team_names) != 2 or team_names[seat] != row['team']:
        raise RuntimeError(f'replay seat/team mapping mismatch: {key}')

    index_path = Path(row['public_state_index_path'])
    index_archive = index_path.read_bytes()
    if sha(index_archive) != row['public_state_index_sha256']:
        raise RuntimeError(f'public index archive hash mismatch: {key}')
    index = json.loads(gzip.decompress(index_archive))
    if index['action_sha256_by_seat'][str(seat)] != action_sha:
        raise RuntimeError(f'public index action hash mismatch: {key}')

    state_path = Path(row['public_state_path'])
    state_archive = state_path.read_bytes()
    state_raw = gzip.decompress(state_archive)
    state_sha = sha(state_raw)
    if state_sha != row['public_state_sha256']:
        raise RuntimeError(f'public state content hash mismatch: {key}')
    timeline = json.loads(state_raw)
    if len(timeline) != 720:
        raise RuntimeError(f'public sidecar frame count mismatch: {key}')

    provenance = {
        'rank': int(row['rank']), 'team': row['team'], 'team_id': row.get('team_id'),
        'submission_id': row.get('submission_id'), 'episode_id': int(row['episode_id']),
        'source_seat': seat, 'engine_version': ENGINE_VERSION, 'frames': 720,
        'action_sha256': action_sha, 'replay_archive_sha256': replay_archive_sha,
        'replay_sha256': replay_sha, 'public_state_index_archive_sha256': sha(index_archive),
        'public_state_index_action_seat_sha256': index['action_sha256_by_seat'][str(seat)],
        'public_state_archive_sha256': sha(state_archive), 'public_state_content_sha256': state_sha,
        'route_path': str(route_path.resolve()), 'replay_path': str(replay_path.resolve()),
        'public_state_index_path': str(index_path.resolve()), 'public_state_path': str(state_path.resolve()),
    }
    return actions, provenance


def order_stats(actions: list) -> dict:
    market_counts: dict[str, int] = {}
    type_item_counts: dict[str, int] = {}
    investment_counts: dict[str, int] = {}
    investment_units: dict[str, int] = {}
    seed_counts: dict[str, int] = {}
    seed_units: dict[str, int] = {}
    plant_counts: dict[str, int] = {}
    first_offsets: dict[str, int] = {}
    for offset, action in enumerate(actions[:24]):
        for order in action.get('market', []) or []:
            if not isinstance(order, list) or not order:
                continue
            kind = str(order[0])
            item = str(order[1]) if len(order) > 1 else '(none)'
            market_counts[kind] = market_counts.get(kind, 0) + 1
            key = f'{kind}:{item}'
            type_item_counts[key] = type_item_counts.get(key, 0) + 1
            first_offsets.setdefault(key, offset)
            if kind in INVESTMENT_TYPES:
                investment_counts[kind] = investment_counts.get(kind, 0) + 1
                if len(order) > 2 and isinstance(order[2], (int, float)):
                    investment_units[key] = investment_units.get(key, 0) + int(order[2])
            if kind in {'BUY_SEED', 'BUY_SEEDS'}:
                seed_counts[item] = seed_counts.get(item, 0) + 1
                if len(order) > 2 and isinstance(order[2], (int, float)):
                    seed_units[item] = seed_units.get(item, 0) + int(order[2])
        worker_actions = [action.get('farmer', [])] + (action.get('hands', []) or [])
        for worker in worker_actions:
            if isinstance(worker, list) and len(worker) >= 2 and worker[0] == 'PLANT':
                crop = str(worker[1])
                plant_counts[crop] = plant_counts.get(crop, 0) + 1
                first_offsets.setdefault(f'PLANT:{crop}', offset)
    return {
        'turn_offsets': '0..23 (day0; zero-based)',
        'market_order_counts_by_type': dict(sorted(market_counts.items())),
        'market_order_counts_by_type_and_item': dict(sorted(type_item_counts.items())),
        'investment_order_counts_by_type': dict(sorted(investment_counts.items())),
        'investment_numeric_units_by_type_and_item': dict(sorted(investment_units.items())),
        'seed_purchase_order_counts_by_crop': dict(sorted(seed_counts.items())),
        'seed_purchase_numeric_units_by_crop': dict(sorted(seed_units.items())),
        'plant_command_counts_by_crop': dict(sorted(plant_counts.items())),
        'first_order_offsets_by_type_and_item': dict(sorted(first_offsets.items())),
        'scope_caveat': 'Recorded order/worker commands only; this does not establish successful execution or outcome.',
    }


def load_rejected_family_routes() -> list[dict]:
    module_files = [
        OLD_CANDIDATE_DIR / 'candidate_01_family01_rank65.py',
        OLD_CANDIDATE_DIR / 'candidate_02_family02_rank16.py',
        OLD_CANDIDATE_DIR / 'candidate_03_family03_rank30.py',
    ]
    rows = []
    for path in module_files:
        module = runpy.run_path(str(path))
        for rank, tape in sorted(module['_TAPES'].items()):
            rows.append({
                'rank': int(rank), 'source_candidate_file': str(path.resolve()),
                'candidate_file_sha256': sha(path.read_bytes()), 'actions': tape['actions'],
            })
    return rows


def main() -> None:
    if sha((HERE / 'PLAN.md').read_bytes()) != EXPECTED_PLAN_SHA:
        raise RuntimeError('frozen plan hash mismatch')
    summary_raw = SUMMARY.read_bytes()
    summary_sha = sha(summary_raw)
    if summary_sha != EXPECTED_SUMMARY_SHA:
        raise RuntimeError('source summary hash mismatch')
    rows = json.loads(summary_raw.decode('utf-8'))
    by_rank = {int(row['rank']): row for row in rows}
    if len(rows) != 100 or any(rank not in by_rank for rank in TARGET_RANKS):
        raise RuntimeError('unexpected source size or missing top ranks')

    generated = []
    action_by_rank = {}
    source_provenance = {}
    for rank in TARGET_RANKS:
        row = by_rank[rank]
        actions, provenance = verify_source(row)
        action_by_rank[rank] = actions
        source_provenance[rank] = provenance
        packed = base64.b85encode(zlib.compress(canonical(actions), level=9)).decode('ascii')
        source = CANDIDATE_TEMPLATE.replace('__PACKED__', packed)
        candidate_path = HERE / f'candidate_top_rank_{rank}.py'
        candidate_path.write_text(source, encoding='utf-8')
        candidate_raw = candidate_path.read_bytes()
        generated.append({
            'rank': rank, 'path': str(candidate_path.resolve()),
            'candidate_sha256': sha(candidate_raw), 'candidate_bytes': len(candidate_raw),
            'source': provenance,
        })

    # Static action-only first-day summary for top-three versus the six tapes
    # retained in the earlier, already-rejected opening experiment.
    rejected = load_rejected_family_routes()
    all_static = []
    for rank in TARGET_RANKS:
        all_static.append({
            'group': 'top3_single_tape_controls', 'rank': rank,
            'team': by_rank[rank]['team'], 'episode_id': int(by_rank[rank]['episode_id']),
            'action_sha256': source_provenance[rank]['action_sha256'],
            'day0': order_stats(action_by_rank[rank]),
        })
    for item in rejected:
        all_static.append({
            'group': 'previously_rejected_physical_prefix_families', 'rank': item['rank'],
            'source_candidate_file': item['source_candidate_file'],
            'candidate_file_sha256': item['candidate_file_sha256'],
            'action_sha256': sha(canonical(item['actions'])),
            'day0': order_stats(item['actions']),
        })
    static_report = {
        'created_at_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'source_summary_sha256': summary_sha,
        'method': 'Read only first 24 recorded actions per complete route; count market commands and PLANT commands.',
        'records': all_static,
        'game_runs': 0, 'outcome_fields_used': False, 'reserved_tapes_read': False,
        'network_calls': 0,
    }
    static_path = HERE / 'static_day0_comparison.json'
    static_path.write_text(json.dumps(static_report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    validated = []
    for item in generated:
        path = Path(item['path'])
        raw = path.read_bytes()
        tree = ast.parse(raw.decode('utf-8'), filename=path.name)
        compile(tree, str(path), 'exec')
        imports = set()
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.FunctionDef):
                functions[node.name] = node
        if not imports <= ALLOWED_IMPORTS:
            raise RuntimeError(f'unexpected import in {path.name}: {imports - ALLOWED_IMPORTS}')
        if not {'agent', 'kaggle_fresh_opening_router_entrypoint'} <= set(functions):
            raise RuntimeError(f'missing final callable in {path.name}')
        spec = importlib.util.spec_from_file_location(f'top_rank_{item["rank"]}_control', path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f'cannot load {path.name}')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actions = action_by_rank[item['rank']]
        if len(module._ACTIONS) != 719 or sha(canonical(module._ACTIONS)) != item['source']['action_sha256']:
            raise RuntimeError(f'embedded tape mismatch in {path.name}')
        sig_entry = str(inspect.signature(module.kaggle_fresh_opening_router_entrypoint))
        sig_agent = str(inspect.signature(module.agent))
        if sig_entry != '(observation, configuration=None)' or sig_agent != '(observation, configuration=None)':
            raise RuntimeError(f'call signature mismatch in {path.name}')
        validated.append({
            'rank': item['rank'], 'path': item['path'], 'candidate_sha256': item['candidate_sha256'],
            'source_action_sha256': item['source']['action_sha256'],
            'embedded_action_sha256': sha(canonical(module._ACTIONS)),
            'actions': len(module._ACTIONS), 'ast_parse': True, 'compile': True, 'module_load': True,
            'agent_callable': callable(module.agent),
            'final_callable': 'kaggle_fresh_opening_router_entrypoint',
            'final_callable_loads': callable(module.kaggle_fresh_opening_router_entrypoint),
            'agent_signature': sig_agent, 'final_callable_signature': sig_entry,
            'policy_action_calls': 0,
        })

    manifest = {
        'created_at_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'scope': 'Three complete top-rank single-tape controls. Static source validation only; no game, simulator, or policy calls.',
        'selection': {
            'source_summary_path': str(SUMMARY.resolve()), 'source_summary_sha256': summary_sha,
            'leaderboard_snapshot_utc': '2026-09-29T17:04:23Z', 'source_summary_receipt_utc': '2026-09-29T17:04:25.099949Z',
            'engine_version': ENGINE_VERSION, 'source_rows': len(rows), 'selected_ranks': list(TARGET_RANKS),
            'criterion': 'ascending frozen leaderboard rank; no outcomes, seed, opponent, or reserved data',
        },
        'frozen_plan_path': str((HERE / 'PLAN.md').resolve()),
        'frozen_plan_sha256': EXPECTED_PLAN_SHA,
        'candidates': generated,
        'static_day0_comparison': {
            'path': str(static_path.resolve()), 'sha256': sha(static_path.read_bytes()),
            'routes_counted': len(all_static), 'top3_routes': 3, 'rejected_family_routes': 6,
        },
        'validation': {
            'source_route_replay_and_public_sidecar_provenance_verified': len(generated),
            'candidate_results': validated,
            'network_calls': 0, 'reserved_tapes_read': False, 'outcome_fields_used': False,
            'simulator_imported': False, 'games_run': 0, 'policy_action_calls': 0,
        },
    }
    manifest_path = HERE / 'candidate_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    hashes = [
        ('PLAN.md', HERE / 'PLAN.md'),
        ('source_summary', SUMMARY),
        ('candidate_top_rank_1.py', HERE / 'candidate_top_rank_1.py'),
        ('candidate_top_rank_2.py', HERE / 'candidate_top_rank_2.py'),
        ('candidate_top_rank_3.py', HERE / 'candidate_top_rank_3.py'),
        ('static_day0_comparison.json', static_path),
        ('candidate_manifest.json', manifest_path),
    ]
    (HERE / 'SHA256SUMS.txt').write_text('\n'.join(f'{sha(path.read_bytes())}  {label}' for label, path in hashes) + '\n', encoding='utf-8')
    print(json.dumps({
        'candidates': [{'rank': row['rank'], 'path': Path(row['path']).name,
                        'sha256': row['candidate_sha256']} for row in generated],
        'source_action_sha256': {str(rank): source_provenance[rank]['action_sha256'] for rank in TARGET_RANKS},
        'manifest_sha256': sha(manifest_path.read_bytes()),
        'plan_sha256': EXPECTED_PLAN_SHA,
        'static_day0_report': str(static_path.resolve()),
    }, indent=2))

if __name__ == '__main__':
    main()
