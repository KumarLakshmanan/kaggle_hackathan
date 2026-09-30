"""Synthetic gate accounting only; these are not strategy outcomes."""
from datetime import datetime, timezone
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.animal_liquidity_20260928 import native as n

jobs = [dict(version=v, rival=ref, seed=seed, candidate_seat=seat)
        for seed in (1,2) for ref in n.REFS for v in ('main','source','animal_cash') for seat in (0,1)]


def rows():
    return [dict(**j, result='win' if j['version']=='animal_cash' else 'draw',
                 candidate_reward=110. if j['version']=='animal_cash' else 100., opponent_reward=100.,
                 margin=10. if j['version']=='animal_cash' else 0., frames=720,
                 candidate_status='DONE', opponent_status='DONE', candidate_errors={}, opponent_errors={},
                 candidate_telemetry={'animal_cash_turns': int(j['version']=='animal_cash')}) for j in jobs]


checks=[]
base=rows()
assert n.assess(base,jobs,'animal_cash','pilot')['passed'] and not n.bounds(base,jobs,'animal_cash',2)
checks.append('Complete wins against both references pass both control comparisons.')

equal=rows()
for r in equal:r['result']='draw'
assert any(f['gate']=='pooled_strict_improvement' for f in n.bounds(equal,jobs,'animal_cash',2))
checks.append('Equality fails strict pooled improvement.')

regression=rows()
for r in regression:
    if r['version']=='animal_cash' and r['rival']=='market':r['result']='loss'
assert any(f['gate']=='reference_nonregression' for f in n.bounds(regression,jobs,'animal_cash',2))
checks.append('A reference regression cannot be hidden by another reference.')

parent=rows()
for r in parent:
    if r['version']=='source':r['result']='win'
assert not n.assess(parent,jobs,'animal_cash','pilot')['passed']
assert any(f.get('control')=='source' for f in n.bounds(parent,jobs,'animal_cash',2))
checks.append('Matching the source fails even when the candidate beats main.')

partial=[r for r in base if r['version']!='animal_cash']
assert not n.bounds(partial,jobs,'animal_cash',2) and not n.assess(partial,jobs,'animal_cash','pilot')['passed']
checks.append('Incomplete candidate rows cannot pass or be rejected before remaining possible gains are bounded.')

inactive=rows()
for r in inactive:r['candidate_telemetry']['animal_cash_turns']=0
assert any(f['gate']=='activation' for f in n.bounds(inactive,jobs,'animal_cash',2))
checks.append('Inactive complete panels fail.')

one_seed=rows()
for r in one_seed:
    if r['seed']==2:r['candidate_telemetry']['animal_cash_turns']=0
assert len(n.active_seeds(one_seed,'animal_cash'))==1
assert any(f['gate']=='activation' for f in n.bounds(one_seed,jobs,'animal_cash',2))
checks.append('Four seat/reference activations in one seed count once.')

invalid=rows();next(r for r in invalid if r['version']=='source')['candidate_errors']={'error':1}
assert any(f['gate']=='execution' for f in n.bounds(invalid,jobs,'animal_cash',2))
checks.append('Source execution errors reject the dependent comparison.')

intervals=n.bootstrap(base,'animal_cash')
assert all(v['lower']==v['upper']==.5 and v['resamples']==20000 and v['distinct_seeds']==2 for v in intervals.values())
checks.append('Whole-seed bootstrap keeps all four games and exact constant effects.')

varying=rows()
for r in varying:
    if r['version']=='animal_cash' and r['seed']==2:r['result']='draw'
assert all(v['lower']==0 for v in n.bootstrap(varying,'animal_cash').values())
checks.append('Sparse cluster-level gain has a zero lower bound.')

assert n.needed_versions([])==set() and n.needed_versions(['animal_cash'])=={'main','source','animal_cash'}
checks.append('Rejected candidate removes its pending controls too.')

n.write(HERE/'native_gate_checks.json',dict(passed=True,synthetic_only=True,checks=checks,
        native_helper_sha256=n.sha(HERE/'native.py'),check_helper_sha256=n.sha(__file__),
        completed_at_utc=datetime.now(timezone.utc).isoformat()))
print('Synthetic gate checks:',len(checks),'passed')
