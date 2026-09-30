"""Check material qualification errors with synthetic outcomes only."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.public_loss_route_pool_20260928.native import impossible_bounds, summaries, bootstrap, key, activated_seeds
from diagnostics.public_loss_route_pool_20260928.search import write, sha


def toy(ref, seed, outcomes, active=True):
    return [dict(version=arm, rival=ref, seed=seed, candidate_seat=seat, result=outcomes[arm],
                 candidate_telemetry={'loss_pool_turns': int(active) if arm == 'new' else 0})
            for arm in ('main', 'source', 'new') for seat in (0, 1)]


def main():
    jobs = []
    for seed in (1, 2):
        jobs += toy('4ee', seed, dict(main='draw', source='draw', new='win'))
    jobs += toy('market', 1, dict(main='draw', source='draw', new='loss'))
    deferred = next(r for r in jobs if r['rival'] == 'market' and r['version'] == 'new' and r['candidate_seat'] == 1)
    before = [r for r in jobs if key(r) != key(deferred)]
    assert not impossible_bounds(before, jobs, 1), 'A final win could still tie the reference.'
    failures = impossible_bounds(jobs, jobs, 1)
    assert any(f['subset'] == 'reference:market' for f in failures)
    assert not any(f['subset'] == 'pooled' for f in failures), 'Pooled gains must not hide a reference regression.'

    tied = toy('4ee', 3, dict(main='loss', source='win', new='win'))
    assert any(f['subset'] == 'pooled' and f['control'] == 'source' for f in impossible_bounds(tied, tied, 1))
    inactive = toy('4ee', 4, dict(main='loss', source='loss', new='win'), active=False)
    pending = [r for r in inactive if not (r['version'] == 'new' and r['candidate_seat'] == 1)]
    assert not any(f['subset'] == 'activation' for f in impossible_bounds(pending, inactive, 1))
    assert any(f['subset'] == 'activation' for f in impossible_bounds(inactive, inactive, 1))
    assert activated_seeds(jobs) == {1, 2}, 'Count a seed only once across seats and references.'

    paired = []
    for ref in ('4ee', 'market'):
        for seed, outcome in ((21, 'win'), (22, 'loss')):
            paired += toy(ref, seed, dict(main='draw', source='draw', new=outcome))
    intervals = bootstrap(paired)
    assert all(v['distinct_seeds'] == 2 and v['lower'] == -.5 and v['upper'] == .5 for v in intervals.values())
    report = dict(passed=True, native_helper_sha256=sha(HERE / 'native.py'),
                  checks=['No premature stop when reference tie remains possible',
                          'Pooled wins cannot hide a reference regression',
                          'Strict pooled gain must beat both controls',
                          'Activation upper bound includes every unfinished new-arm seed',
                          'Activation counts distinct seeds across seats and references',
                          'Bootstrap resamples both seats and references together'],
                  bootstrap_toy_intervals=intervals, scope='Synthetic checks only; no strategy strength evidence.')
    write(HERE / 'native_gate_checks.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
