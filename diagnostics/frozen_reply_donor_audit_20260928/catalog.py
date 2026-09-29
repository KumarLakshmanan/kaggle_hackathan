"""Human-readable donor catalog built exclusively from the frozen audit inputs."""
from collections import Counter, defaultdict
from pathlib import Path
import gzip
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit import sha, digest
from semantic_audit import normalized_physical


def main():
    strict = json.loads((HERE / 'inventory.json').read_text(encoding='utf-8'))
    semantic = json.loads((HERE / 'semantic_physical_inventory.json').read_text(encoding='utf-8'))
    normalized = {r['fixture_id']:r for r in semantic['fixtures']}
    groups = defaultdict(list)
    for row in strict['fixtures']:
        assert sha(row['tape_path']) == row['tape_file_sha256']
        actions = json.loads(gzip.decompress(Path(row['tape_path']).read_bytes()))['actions']
        groups[digest(normalized_physical(actions[:72]))].append(row)
    catalog = []
    for fingerprint, rows in sorted(groups.items(), key=lambda pair:(-len(pair[1]),pair[0])):
        catalog.append(dict(opening72_normalized_physical_sha256=fingerprint, fixture_count=len(rows),
                            fixtures=[r['fixture_id'] for r in rows],
                            historical_first_shop_counts=dict(Counter('|'.join(r['recorded_shops']['72']) for r in rows)),
                            compatible_with_source_opening=False,
                            admissible_as_source72_or144_replacement=False,
                            reason='Physical commands differ from source at turn0 or1, including after PASS/default-argument normalization. Whole opening and funding need separate study.'))
    output = dict(read_only_audit=True, outcome_games_run=0, strict_inventory_sha256=sha(HERE/'inventory.json'),
                  semantic_inventory_sha256=sha(HERE/'semantic_physical_inventory.json'), helper_sha256=sha(__file__),
                  physically_distinct_donor_openings72=len(groups), source_library_physical_opening72_count=len({r['physical_prefix72_sha256'] for r in strict['library'].values()}),
                  opening_families=catalog)
    (HERE/'opening_family_catalog.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    lines=['# Frozen opponent donor schedules — read-only inventory', '',
           'All 50 tapes are novel complete action and physical-command schedules relative to the source library. None matches the source or any library route through 72 turns, including the explicit semantic normalization. Consequently the list of admissible source-compatible replacement donors is empty.', '',
           'Recorded first shops below are archive provenance. They are not claims of counterfactual coverage and cannot select a conflicting opening before those shops become visible.', '',
           '| Fixture | Team | Recorded first shop | First differing normalized physical turn |',
           '| --- | --- | --- | ---: |']
    for row in strict['fixtures']:
        extra=normalized[row['fixture_id']]
        lines.append('| '+row['fixture_id']+' | '+row['team'].replace('|','\\|')+' | '+','.join(row['recorded_shops']['72'])+' | '+str(extra['source_opening_common_prefix'])+' |')
    lines += ['', 'Complete action hashes, both 72/144 prefix hashes, valid type checks, source/shop family matches, and all 7,250 library comparisons are retained in the JSON receipts. Opening clusters are in opening_family_catalog.json. No strategy artifacts or outcome games were created.']
    (HERE/'DONORS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Opening clusters',len(groups),'library physical opening72 count',output['source_library_physical_opening72_count'])
    for group in catalog:
        print(group['fixture_count'],group['historical_first_shop_counts'],group['fixtures'])


if __name__=='__main__':main()
