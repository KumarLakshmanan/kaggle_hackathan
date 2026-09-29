"""Supplement strict inventory with unit-command equivalences only."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import gzip
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit import ROOT, SOURCE, SOURCE_SHA, MANIFEST, MANIFEST_SHA, sha, digest, prefix_length


def normalized_command(command):
    if not command:
        return ['PASS']
    op = command[0]
    if op in ('PICKUP', 'PLACE'):
        return [op, command[1], command[2] if len(command) > 2 else 1]
    if op == 'PLANT':
        return command[:2]
    return command[:1]


def normalized_physical(actions):
    out = []
    for action in actions:
        hands = [normalized_command(c) for c in action.get('hands', [])]
        while hands and hands[-1] == ['PASS']:
            hands.pop()
        out.append(dict(farmer=normalized_command(action.get('farmer', ['PASS'])), hands=hands))
    return out


def main():
    assert sha(SOURCE) == SOURCE_SHA and sha(MANIFEST) == MANIFEST_SHA
    original = json.loads((HERE / 'inventory.json').read_text(encoding='utf-8'))
    assert original['complete'] and original['summary']['all_types_valid']
    spec = importlib.util.spec_from_file_location('semantic_audit_source367', SOURCE)
    source = importlib.util.module_from_spec(spec); spec.loader.exec_module(source)
    raw_routes = source._DATA['routes']; routes = {rid: normalized_physical(a) for rid,a in raw_routes.items()}
    opening = normalized_physical(source._DATA['opening'])
    families = sorted(k for k in source._DATA['route_map'] if '|' not in k)
    source_prefixes = {f: opening + routes[str(source._DATA['route_map'][f])][72:144] for f in families}
    rows = []; matrix = []
    for donor in original['fixtures']:
        assert sha(donor['tape_path']) == donor['tape_file_sha256']
        actions = json.loads(gzip.decompress(Path(donor['tape_path']).read_bytes()))['actions']
        acts = normalized_physical(actions)
        comparisons = [dict(fixture_id=donor['fixture_id'], route_id=rid, common_prefix=prefix_length(acts, route),
                            full_equal=acts == route) for rid, route in routes.items()]
        matrix.extend(comparisons)
        source_families = {f: prefix_length(acts,p) for f,p in source_prefixes.items()}
        row = dict(fixture_id=donor['fixture_id'], team=donor['team'], episode_id=donor['episode_id'], panel=donor['panel'],
                   normalized_physical_sha256=digest(acts), raw_canonical_action_sha256=donor['canonical_action_sha256'],
                   full_matching_library_routes=[r['route_id'] for r in comparisons if r['full_equal']],
                   library_prefix72_routes=[r['route_id'] for r in comparisons if r['common_prefix'] >= 72],
                   library_prefix144_routes=[r['route_id'] for r in comparisons if r['common_prefix'] >= 144],
                   max_library_common_prefix=max(r['common_prefix'] for r in comparisons),
                   source_opening_common_prefix=prefix_length(acts,opening),
                   source144_family_common_prefix=source_families,
                   source144_families=[f for f,n in source_families.items() if n == 144],
                   recorded_first_shop=donor['recorded_shops']['72'],
                   recorded_first_two_shops=donor['recorded_shops']['144'])
        first = row['source_opening_common_prefix']
        if first < 72:
            row['first_source_physical_mismatch'] = dict(step=first, source=opening[first], donor=acts[first])
        rows.append(row)
    summary = dict(fixtures=len(rows), novel_normalized_physical_fixture_count=sum(not r['full_matching_library_routes'] for r in rows),
                   source72_compatible_fixture_count=sum(r['source_opening_common_prefix'] >= 72 for r in rows),
                   source144_compatible_fixture_count=sum(bool(r['source144_families']) for r in rows),
                   any_library72_compatible_fixture_count=sum(bool(r['library_prefix72_routes']) for r in rows),
                   any_library144_compatible_fixture_count=sum(bool(r['library_prefix144_routes']) for r in rows),
                   source_opening_common_prefix_counts=dict(Counter(r['source_opening_common_prefix'] for r in rows)))
    result = dict(complete=True, read_only_audit=True, outcome_games_run=0, source_sha256=SOURCE_SHA,
                  target_manifest_sha256=MANIFEST_SHA, strict_inventory_sha256=sha(HERE / 'inventory.json'),
                  helper_sha256=sha(__file__),
                  normalization='Trim trailing PASS hand commands; empty command means PASS; PICKUP/PLACE missing quantity means1; PLANT ignores trailing arguments; other known unit commands use first opcode. Preserve worker ordering. Market commands are excluded and never normalized.',
                  limitation='Only syntactic unit-command equivalence. Matching physical commands cannot prove matching hires, positions, inventory, seed availability, money, land or market response.',
                  summary=summary, fixtures=rows, comparisons=matrix, completed_at_utc=datetime.now(timezone.utc).isoformat())
    output = HERE / 'semantic_physical_inventory.json'; assert not output.exists()
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    for row in rows:
        if row['source_opening_common_prefix'] >=72 or row['max_library_common_prefix'] >=72:
            print(row['team'],row['fixture_id'],row['source_opening_common_prefix'],row['source144_families'])


if __name__ == '__main__':
    main()
