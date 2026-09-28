"""Map the remaining frozen target losses to existing compatible schedules."""
from collections import defaultdict
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.guarded_route_pool_20260928.search import SOURCE, SOURCE_SHA, FULL, FULL_SHA, TARGETS, TARGETS_SHA, WINS, WINS_SHA, read, write, sha


def action_hash(actions):
    return hashlib.sha256(json.dumps(actions, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def main():
    for path, digest in ((SOURCE, SOURCE_SHA), (FULL, FULL_SHA), (TARGETS, TARGETS_SHA), (WINS, WINS_SHA)):
        assert sha(path) == digest
    coverage = read(HERE / 'coverage.json')
    assert coverage['complete'] and coverage['passed'] and coverage['source_sha256'] == SOURCE_SHA
    assert coverage['helper_sha256'] == sha(HERE / 'coverage.py')
    target = read(TARGETS)
    fixtures = target['live_losses'] + target['current_top20'] + read(WINS)['fixtures']
    by_id = {f['fixture_id']: f for f in fixtures}
    full = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games']}
    spec = importlib.util.spec_from_file_location('source_route_inventory', SOURCE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    prefixes = defaultdict(list)
    for route, actions in sorted(module._DATA['routes'].items()):
        prefixes[action_hash(actions[:144])].append((str(route), action_hash(actions)))
    groups = defaultdict(dict)
    for row in coverage['prefixes']:
        groups['|'.join(row['shops144'])].setdefault(row['fixture_id'], []).append(row['candidate_seat'])
    result = []
    for pair, members in sorted(groups.items()):
        lookup = pair if pair in module._DATA['route_map'] else pair.split('|')[0]
        route = str(module._DATA['route_map'][lookup])
        prefix_sha = action_hash(module._DATA['routes'][route][:144])
        seen, compatible = set(), []
        for other, digest in prefixes[prefix_sha]:
            if digest not in seen:
                seen.add(digest); compatible.append(other)
        failed = []
        for fixture_id, seats in members.items():
            if fixture_id.startswith('public-win-'):
                continue
            cases = [full[(fixture_id, seat)] for seat in sorted(seats)]
            if any(case['result'] != 'win' for case in cases):
                failed.append(dict(fixture_id=fixture_id, team=by_id[fixture_id]['team'], seats=sorted(seats),
                                   source_margins=[case['margin'] for case in cases]))
        if failed:
            result.append(dict(pair=pair, source_route=route, actual_lookup=lookup, compatible_routes=compatible,
                               compatible_route_count=len(compatible), unresolved_targets=failed,
                               affected_target_count=sum(not f.startswith('public-win-') for f in members),
                               affected_public_win_count=sum(f.startswith('public-win-') for f in members),
                               affected_fixtures=[dict(fixture_id=f, team=by_id[f]['team'], seats=sorted(seats)) for f, seats in sorted(members.items())]))
    output = dict(source_sha256=SOURCE_SHA, coverage_sha256=sha(HERE / 'coverage.json'), source_full_sha256=FULL_SHA,
                  scope='Static inventory for future research; no new strength outcomes or selection change.', groups=result)
    write(HERE / 'remaining_route_inventory.json', output)
    print(json.dumps([dict(pair=r['pair'], compatible_routes=r['compatible_route_count'],
                           unresolved_target_count=len(r['unresolved_targets']), affected_public_wins=r['affected_public_win_count']) for r in result], indent=2), flush=True)


if __name__ == '__main__':
    main()
