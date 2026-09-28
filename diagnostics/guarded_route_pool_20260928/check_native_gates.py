"""Check qualification failure modes without running strategy outcomes."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.guarded_route_pool_20260928.native import impossible_bounds, summaries, bootstrap, gkey
from diagnostics.guarded_route_pool_20260928.search import write, sha


def toy(ref, pair, seed, outcomes):
    return [dict(version=version, rival=ref, shop_pair=pair, seed=seed, candidate_seat=seat,
                 result=outcomes[version], margin=0.)
            for version in ('main', 'source', 'new') for seat in (0, 1)]


def main():
    jobs = []
    for ref in ('4ee', 'market'):
        for pair, seed in (('A', 1), ('A', 2), ('C', 3)):
            jobs.extend(toy(ref, pair, seed, {'main': 'draw', 'source': 'draw', 'new': 'win' if pair == 'A' else 'loss'}))
    deferred = next(row for row in jobs if row['rival'] == '4ee' and row['shop_pair'] == 'C'
                    and row['version'] == 'new' and row['candidate_seat'] == 1)
    before = [row for row in jobs if not (row['rival'] == 'market' and row['shop_pair'] == 'C' and row['version'] == 'new')
              and gkey(row) != gkey(deferred)]
    assert not impossible_bounds(before, jobs), 'One remaining win can still satisfy the branch tie.'
    after = before + [deferred]
    failures = impossible_bounds(after, jobs)
    assert any(row['subset'] == '4ee:C' for row in failures)
    assert not any(row['subset'] == 'pooled' for row in failures), 'Branch loss must not be hidden by larger gains elsewhere.'
    summary = summaries(jobs, jobs)
    pooled = summary[0]['arms']
    assert pooled['new']['win_points'] > pooled['main']['win_points']
    assert any(row['arms']['new']['win_points'] < row['arms']['source']['win_points'] for row in summary if row['subset'] != 'pooled')

    controls = toy('4ee', 'A', 7, {'main': 'loss', 'source': 'win', 'new': 'win'})
    assert any(row['subset'] == 'pooled' and row['control'] == 'source' for row in impossible_bounds(controls, controls))

    paired = []
    for ref in ('4ee', 'market'):
        for seed, outcome in ((21, 'win'), (22, 'loss')):
            paired.extend(toy(ref, 'A', seed, {'main': 'draw', 'source': 'draw', 'new': outcome}))
    intervals = bootstrap(paired)
    assert all(value['distinct_seeds'] == 2 and value['lower'] == -.5 and value['upper'] == .5 for value in intervals.values())
    report = dict(passed=True, native_helper_sha256=sha(HERE / 'native.py'),
                  checks=['No premature stop when a branch tie is still possible',
                          'Per-branch regression cannot be hidden by pooled gains',
                          'Strict improvement must beat both controls',
                          'Bootstrap keeps both seats and both references together by seed'],
                  bootstrap_toy_intervals=intervals,
                  scope='Synthetic qualification-logic checks; no candidate strength evidence.')
    write(HERE / 'native_gate_checks.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
