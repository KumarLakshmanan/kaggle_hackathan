"""Read-only frozen-reply schedule inventory; no policy or outcome execution."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'main_candidate_hire_recovery_integrated_20260928_367d2e76.py'
SOURCE_SHA = '367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0'
MANIFEST = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
MANIFEST_SHA = '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(value):
    return sha_bytes(canonical(value))


def physical(actions):
    return [{'farmer': a.get('farmer', ['PASS']), 'hands': a.get('hands', [])} for a in actions]


def prefix_length(left, right):
    for i, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return i
    return min(len(left), len(right))


def valid_types(actions):
    errors = []; empty = Counter(); market_noops = Counter(); extra = Counter()
    for step, action in enumerate(actions):
        if not isinstance(action, dict):
            errors.append([step, 'action_not_object']); continue
        for key in set(action) - {'farmer', 'hands', 'market'}:
            extra[key] += 1
        for field in ('farmer', 'hands', 'market'):
            value = action.get(field)
            if not isinstance(value, list):
                errors.append([step, field, 'not_array']); continue
            commands = [value] if field == 'farmer' else value
            for index, command in enumerate(commands):
                if not isinstance(command, list):
                    errors.append([step, field, index, 'command_not_array']); continue
                if not command:
                    empty[field] += 1; continue
                if not isinstance(command[0], str) or any(type(v) not in (str, int) for v in command):
                    errors.append([step, field, index, 'non_string_or_integer_command'])
                if field == 'market' and command[0] in ('PASS', 'NOOP'):
                    market_noops[command[0]] += 1
    return dict(valid=not errors, errors=errors, empty_commands=dict(empty), market_noops=dict(market_noops), extra_keys=dict(extra))


def describe(actions):
    return dict(length=len(actions), canonical_action_sha256=digest(actions), physical_command_sha256=digest(physical(actions)),
                exact_prefix72_sha256=digest(actions[:72]), exact_prefix144_sha256=digest(actions[:144]),
                physical_prefix72_sha256=digest(physical(actions[:72])), physical_prefix144_sha256=digest(physical(actions[:144])),
                types=valid_types(actions))


def main():
    assert sha(SOURCE) == SOURCE_SHA and sha(MANIFEST) == MANIFEST_SHA
    assert not (HERE / 'inventory.json').exists()
    spec = importlib.util.spec_from_file_location('static_donor_source367', SOURCE)
    source = importlib.util.module_from_spec(spec); spec.loader.exec_module(source)
    routes = source._DATA['routes']; opening = source._DATA['opening']; route_map = source._DATA['route_map']
    assert len(routes) == 145 and len(opening) == 72
    library = {rid: describe(actions) for rid, actions in sorted(routes.items())}
    all_actions = defaultdict(list); all_physical = defaultdict(list)
    for rid, row in library.items():
        all_actions[row['canonical_action_sha256']].append(rid)
        all_physical[row['physical_command_sha256']].append(rid)
    families = sorted(k for k in route_map if '|' not in k)
    source_prefixes = {family: opening + routes[str(route_map[family])][72:144] for family in families}
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    fixtures = manifest['live_losses'] + manifest['current_top20']; assert len(fixtures) == 50
    rows = []; matrix = []; unique = {}
    for fixture in fixtures:
        tape_path = Path(fixture['source_action_tape_path']); raw_tape = gzip.decompress(tape_path.read_bytes())
        tape = json.loads(raw_tape)['actions']; meta = describe(tape)
        original_hashes = [sha_bytes(json.dumps(tape, sort_keys=s, separators=(',', ':')).encode()) for s in (False, True)]
        assert fixture['source_opponent_action_sha256'] in original_hashes
        raw_replay = gzip.decompress(Path(fixture['source_replay_path']).read_bytes())
        assert sha_bytes(raw_replay) == fixture['source_replay_sha256']
        replay = json.loads(raw_replay); del raw_replay
        seat = (1-int(fixture['source_candidate_seat'])) if fixture['fixture_id'].startswith('live-') else int(fixture['source_seat'])
        recorded_actions = [step[seat].get('action') for step in replay['steps'][1:720]]
        tape_replay_mismatches = [i for i, (left, right) in enumerate(zip(tape, recorded_actions)) if left != right]
        recorded_shops = {}
        for at in (72, 144, 216):
            recorded_shops[str(at)] = replay['steps'][at][seat]['observation']['town']['unlocked_shops']
        del replay
        exact_prefix = prefix_length(tape, opening)
        physical_prefix = prefix_length(physical(tape), physical(opening))
        comparisons = []
        for rid, route in sorted(routes.items()):
            record = dict(fixture_id=fixture['fixture_id'], route_id=rid,
                          exact_common_prefix=prefix_length(tape, route),
                          physical_common_prefix=prefix_length(physical(tape), physical(route)))
            comparisons.append(record); matrix.append(record)
        source_family_matches = {}
        for family, prefix in source_prefixes.items():
            source_family_matches[family] = dict(source_route_at72=str(route_map[family]),
                                                exact_prefix=prefix_length(tape, prefix),
                                                physical_prefix=prefix_length(physical(tape), physical(prefix)))
        row = dict(fixture_id=fixture['fixture_id'], team=fixture['team'], episode_id=fixture['episode_id'],
                   panel='loss30' if fixture['fixture_id'].startswith('live-') else 'top20',
                   tape_path=str(tape_path), tape_file_sha256=sha(tape_path),
                   manifest_action_sha256=fixture['source_opponent_action_sha256'], replay_action_seat=seat,
                   tape_replay_action_mismatch_count=len(tape_replay_mismatches), tape_replay_action_mismatch_examples=tape_replay_mismatches[:8],
                   recorded_shops=recorded_shops, **meta,
                   matching_full_library_routes=all_actions.get(meta['canonical_action_sha256'], []),
                   matching_physical_full_library_routes=all_physical.get(meta['physical_command_sha256'], []),
                   exact_source_opening72=exact_prefix == 72, physical_source_opening72=physical_prefix == 72,
                   source_opening_exact_common_prefix=exact_prefix, source_opening_physical_common_prefix=physical_prefix,
                   source_family_prefix144=source_family_matches,
                   exact_library_prefix72_routes=[r['route_id'] for r in comparisons if r['exact_common_prefix'] >= 72],
                   physical_library_prefix72_routes=[r['route_id'] for r in comparisons if r['physical_common_prefix'] >= 72],
                   exact_library_prefix144_routes=[r['route_id'] for r in comparisons if r['exact_common_prefix'] >= 144],
                   physical_library_prefix144_routes=[r['route_id'] for r in comparisons if r['physical_common_prefix'] >= 144],
                   max_exact_library_common_prefix=max(r['exact_common_prefix'] for r in comparisons),
                   max_physical_library_common_prefix=max(r['physical_common_prefix'] for r in comparisons))
        row['exact_source144_families'] = [f for f, r in source_family_matches.items() if r['exact_prefix'] == 144]
        row['physical_source144_families'] = [f for f, r in source_family_matches.items() if r['physical_prefix'] == 144]
        row['novel_full_actions'] = not row['matching_full_library_routes']
        row['novel_full_physical_commands'] = not row['matching_physical_full_library_routes']
        row['classification'] = ('existing_full_actions' if not row['novel_full_actions'] else
                                 'novel_actions_exact_opening' if row['exact_source_opening72'] else
                                 'novel_actions_physical_opening_only_unproven_funding' if row['physical_source_opening72'] else
                                 'different_physical_opening_requires_full_policy_research')
        rows.append(row)
        unique.setdefault(meta['canonical_action_sha256'], []).append(fixture['fixture_id'])
        print(len(rows), '/50', fixture['team'], row['classification'], 'prefix', row['source_opening_exact_common_prefix'], row['source_opening_physical_common_prefix'], flush=True)
    metadata = dict(source=str(SOURCE), source_sha256=SOURCE_SHA, target_manifest=str(MANIFEST), target_manifest_sha256=MANIFEST_SHA,
                    audit_helper_sha256=sha(__file__), read_only_audit=True, outcome_games_run=0,
                    canonicalization='JSON sorted object keys, compact separators, ensure_ascii=True; array order and empty commands retained',
                    physical_projection='farmer and hands only, retaining unit indices, argument values and array order',
                    empty_market_commands='Counted separately, accepted as typed no-op arrays; no game admissibility claim',
                    compatibility_limit='Exact raw schedule prefixes and physical prefixes are syntactic matches only; source wrappers and rival-dependent market funding require original-native state validation before schedule switching',
                    historical_shop_limit='Recorded shop families describe donor provenance, not source counterfactual shop coverage; no future shop values may enter runtime selection',
                    completed_at_utc=datetime.now(timezone.utc).isoformat())
    summary = dict(fixtures=50, distinct_episodes=len({f['episode_id'] for f in fixtures}), distinct_full_action_tapes=len(unique),
                   library_routes=145, library_distinct_full_actions=len(all_actions), library_distinct_physical_commands=len(all_physical),
                   all_lengths719=all(r['length'] == 719 for r in rows) and all(r['length'] == 719 for r in library.values()),
                   all_types_valid=all(r['types']['valid'] for r in rows) and all(r['types']['valid'] for r in library.values()),
                   all_tapes_match_recorded_actions=all(r['tape_replay_action_mismatch_count'] == 0 for r in rows),
                   classifications=dict(Counter(r['classification'] for r in rows)),
                   novel_physical_fixture_count=sum(r['novel_full_physical_commands'] for r in rows),
                   novel_action_exact_opening_fixture_count=sum(r['novel_full_actions'] and r['exact_source_opening72'] for r in rows),
                   novel_action_physical_opening_fixture_count=sum(r['novel_full_actions'] and r['physical_source_opening72'] for r in rows),
                   exact144_compatible_fixture_count=sum(bool(r['exact_source144_families']) for r in rows),
                   physical144_compatible_fixture_count=sum(bool(r['physical_source144_families']) for r in rows))
    result = dict(complete=True, summary=summary, fixtures=rows, duplicate_full_action_groups={k:v for k,v in unique.items() if len(v)>1},
                  library=library, source_first_shop_families=families, source_opening=describe(opening),
                  source_family_prefixes={f: describe(p) for f,p in source_prefixes.items()}, **metadata)
    (HERE / 'inventory.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    (HERE / 'all_route_comparisons.json').write_text(json.dumps(dict(comparisons=matrix, **metadata), indent=2), encoding='utf-8')
    shortlist = [r for r in rows if r['novel_full_actions'] and (r['exact_source_opening72'] or r['physical_source_opening72'])]
    (HERE / 'compatible_donor_inventory.json').write_text(json.dumps(dict(donors=shortlist, summary=summary, **metadata), indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    HERE.mkdir(parents=True, exist_ok=True)
    main()
