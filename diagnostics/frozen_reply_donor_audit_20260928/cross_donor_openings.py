"""Inventory exact shared openings among novel donors, without outcome games."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit import sha, prefix_length


def main():
    audit = json.loads((HERE/'inventory.json').read_text(encoding='utf-8'))
    groups = defaultdict(list)
    for row in audit['fixtures']:
        groups[row['exact_prefix72_sha256']].append(row)
    repeated=[]
    for fingerprint, rows in sorted(groups.items(),key=lambda pair:(-len(pair[1]),pair[0])):
        if len(rows)<2:
            continue
        actions={}
        for row in rows:
            assert sha(row['tape_path'])==row['tape_file_sha256']
            actions[row['fixture_id']]=json.loads(gzip.decompress(Path(row['tape_path']).read_bytes()))['actions']
        comparisons=[]
        for i,left in enumerate(rows):
            for right in rows[i+1:]:
                comparisons.append(dict(left=left['fixture_id'],right=right['fixture_id'],
                                        exact_common_prefix=prefix_length(actions[left['fixture_id']],actions[right['fixture_id']]),
                                        left_shops144=left['recorded_shops']['144'],right_shops144=right['recorded_shops']['144']))
        repeated.append(dict(exact_prefix72_sha256=fingerprint,fixtures=[dict(fixture_id=r['fixture_id'],team=r['team'],
                             canonical_action_sha256=r['canonical_action_sha256'],tape_path=r['tape_path'],
                             recorded_shops=r['recorded_shops']) for r in rows], pairwise= comparisons,
                             shared_with_current_source=False,
                             possible_research='A separate policy may adopt this whole shared opening from turn0, then condition later complete schedules on publicly observed shop prefixes, after state/funding and original-native validation.'))
    result=dict(read_only_audit=True,outcome_games_run=0,strict_inventory_sha256=sha(HERE/'inventory.json'),helper_sha256=sha(__file__),
                distinct_donor_exact_openings72=len(groups),repeated_groups=repeated,
                limitation='These shared openings are between donors only. None can be spliced after the current source opening. Recorded shop paths are provenance, not guaranteed counterfactual coverage.')
    (HERE/'cross_donor_openings.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
