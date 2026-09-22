import json
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as K


def noop_audit(agents, seed=9001):
    """Count engine actions that changed nothing.

    Wraps _apply_unit_action, snapshots the mutable farm + private state either
    side of the call, and compares. PASS is tracked separately: a deliberate pass
    is a legitimate choice, not waste, and it would otherwise dominate the count.
    """
    original = K._apply_unit_action
    stats = {}

    def hooked(farm, private, idx, action, *args, **kwargs):
        before = (json.dumps(farm, sort_keys=True), json.dumps(private, sort_keys=True))
        result = original(farm, private, idx, action, *args, **kwargs)
        after = (json.dumps(farm, sort_keys=True), json.dumps(private, sort_keys=True))
        name = action[0] if isinstance(action, (list, tuple)) and action else str(action)
        row = stats.setdefault(name, [0, 0])
        row[0] += 1
        row[1] += (before == after)
        return result

    K._apply_unit_action = hooked
    try:
        make("kaggriculture", configuration={"seed": seed}, debug=False).run(agents)
    finally:
        K._apply_unit_action = original          # always restore, even on failure
    return stats


def report(label, stats):
    real = {k: v for k, v in stats.items() if k != "PASS"}
    total = sum(v[0] for v in real.values())
    wasted = sum(v[1] for v in real.values())
    print(f"{label:10s} {total:5d} real actions   {wasted:5d} wasted   "
          f"{100 * wasted / max(1, total):5.1f}%")
    for name, (n, bad) in sorted(real.items(), key=lambda kv: -kv[1][1])[:5]:
        if bad:
            print(f"    {name:10s} {n:5d} issued  {bad:5d} no-op  {100 * bad / n:5.1f}%")


for name in ["starter", "random"]:
    report(name, noop_audit([name, name]))

import math
from statistics import mean
from kaggle_environments import make


def duel(agent_a, agent_b, seeds, verbose=True):
    """Paired comparison over common seeds, both seats. Returns (wins, t)."""
    diffs = []
    for seed in seeds:
        for swap in (False, True):
            pair = [agent_b, agent_a] if swap else [agent_a, agent_b]
            env = make("kaggriculture", configuration={"seed": seed}, debug=False)
            env.run(pair)
            r = [s["reward"] or 0 for s in env.steps[-1]]
            a, b = (r[1], r[0]) if swap else (r[0], r[1])
            diffs.append(a - b)

    n = len(diffs)
    m = mean(diffs)
    sd = (sum((d - m) ** 2 for d in diffs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    t = m / se if se else 0.0
    wins = sum(d > 0 for d in diffs)
    if verbose:
        print(f"{n} games ({len(seeds)} seeds x 2 seats)")
        print(f"  wins   {wins}/{n}  ({100 * wins / n:.0f}%)")
        print(f"  margin ${m:,.0f}/game   stderr ${se:,.0f}   t = {t:+.2f}")
        print(f"  verdict: {'SHIP' if t > 2 else 'not proven — do not spend a submission'}")
    return wins, t


duel("starter", "random", seeds=range(9001, 9007))