"""Synthetic gate/stop accounting checks; no strategy games or strength evidence."""
from datetime import datetime, timezone
from pathlib import Path
import copy
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.observed_hire_recovery_20260928 import native as n

jobs = [dict(version=v, rival=ref, seed=seed, candidate_seat=seat)
        for seed in (1, 2) for ref in n.REFS for v in ('main', 'source', *n.CANDIDATES) for seat in (0, 1)]


def rows():
    return [dict(**job, result='win' if job['version'] in n.CANDIDATES else 'draw',
                 candidate_reward=110. if job['version'] in n.CANDIDATES else 100., opponent_reward=100.,
                 margin=10. if job['version'] in n.CANDIDATES else 0., frames=720,
                 candidate_status='DONE', opponent_status='DONE', candidate_errors={}, opponent_errors={},
                 candidate_telemetry={'hire_recovery_turns': int(job['version'] in n.CANDIDATES)}) for job in jobs]


checks = []
base = rows()
assert all(n.assess(base, jobs, c, 'pilot')['passed'] and not n.bounds(base, jobs, c, 2) for c in n.CANDIDATES)
checks.append('Complete two-reference candidate wins pass both required comparisons.')

equal = rows()
for r in equal:
    r['result'] = 'draw'
assert all(any(f['gate'] == 'pooled_strict_improvement' for f in n.bounds(equal, jobs, c, 2)) for c in n.CANDIDATES)
checks.append('Equality fails strict pooled improvement even when reference nonregression holds.')

regression = rows()
for r in regression:
    if r['version'] == 'repair_main' and r['rival'] == 'market':
        r['result'] = 'loss'
assert any(f['gate'] == 'reference_nonregression' for f in n.bounds(regression, jobs, 'repair_main', 2))
checks.append('Reference regression rejects a candidate.')

independent = rows()
for r in independent:
    if r['version'] == 'source':
        r['result'] = 'win'
    if r['version'] == 'repair_integrated':
        r['result'] = 'draw'
assert n.assess(independent, jobs, 'repair_main', 'pilot')['passed']
assert not n.assess(independent, jobs, 'repair_integrated', 'pilot')['passed']
assert n.bounds(independent, jobs, 'repair_integrated', 2)
checks.append('Integrated rejection does not veto the separate main-parent candidate.')

partial = [r for r in base if r['version'] not in n.CANDIDATES]
assert all(not n.bounds(partial, jobs, c, 2) and not n.assess(partial, jobs, c, 'pilot')['passed'] for c in n.CANDIDATES)
checks.append('Remaining candidate games prevent premature rejection, while incomplete arms cannot pass.')

inactive = rows()
for r in inactive:
    r['candidate_telemetry']['hire_recovery_turns'] = 0
assert all(any(f['gate'] == 'activation' for f in n.bounds(inactive, jobs, c, 2)) for c in n.CANDIDATES)
checks.append('Complete insufficient activation fails; repeated seats are not separate seeds.')

invalid = rows(); next(r for r in invalid if r['version'] == 'source')['candidate_errors'] = {'error': 1}
assert not n.bounds(invalid, jobs, 'repair_main', 2)
assert any(f['gate'] == 'execution' for f in n.bounds(invalid, jobs, 'repair_integrated', 2))
checks.append('A failed unique source control rejects only its dependent candidate.')

intervals = n.bootstrap(base, 'repair_integrated')
assert all(v['lower'] == v['upper'] == .5 and v['distinct_seeds'] == 2 and v['resamples'] == 20000 for v in intervals.values())
checks.append('Whole-seed bootstrap preserves all four games and exact constant effects.')

varying = rows()
for r in varying:
    if r['version'] == 'repair_main' and r['seed'] == 2:
        r['result'] = 'draw'
assert n.bootstrap(varying, 'repair_main')['main']['lower'] == 0
checks.append('Sparse clustered gain has a zero lower bound, not a spurious positive interval.')

assert n.needed_versions([]) == set()
assert n.needed_versions(['repair_main']) == {'main', 'repair_main'}
assert n.needed_versions(['repair_integrated']) == {'main', 'source', 'repair_integrated'}
checks.append('Canceled candidates remove only controls no surviving arm needs.')

n.write(HERE / 'native_gate_checks.json', dict(passed=True, synthetic_only=True, checks=checks,
    native_helper_sha256=n.sha(HERE / 'native.py'), check_helper_sha256=n.sha(__file__),
    completed_at_utc=datetime.now(timezone.utc).isoformat()))
print('Synthetic native gate checks:', len(checks), 'passed')
