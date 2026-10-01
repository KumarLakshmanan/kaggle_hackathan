# Kaggriculture executable search engine

This engine generates new action sequences and simulates their effects on
coins, resources, workers and the shared market. It has two interfaces:

- `plan` generates movement, shed transfers, coordinated work and funded investment programs over several
  turns, and writes a recommendation with separate scenario coin outcomes.
- `build` packages the strongest retained physical executor with an online
  market-program search into one standalone Kaggle-compatible Python file.

The online agent synthesizes new order sequences by moving, splitting and
merging transactions. It does not select a previously tested strategy file.
It keeps the established physical production schedule while requiring its
generated market plan to preserve both players' modeled noncash state and
avoid a cash-margin decline in every scenario. This first implementation is
a tactical engine. Whole-season autonomous farm planning remains research.

## Run

From `H:\hackathan` using the installed Python:

```powershell
python -m kaggriculture_engine plan --input diagnostics/executable_engine_20260930/example_observation.json --output my_plan.json --horizon 12 --nodes 1000 --seconds 30
python -m kaggriculture_engine build --output my_search_agent.py --baseline diagnostics/executable_engine_20260930/baseline_4eeac9c3.py --nodes 48 --depth 3
```

The offline planner implementation is `planner.py`; it is separate from the frozen tactical candidate and is not competitively qualified. Focused native probes and their scope are documented in `diagnostics/executable_engine_20260930/PLANNER_SCOPE.md`.

The input JSON contains `observation` and `configuration`, as supplied to an
agent. Only the observation's public fields and own private inventory are
read. The real episode seed is ignored. Output files must not already exist.
The planning continuation requires this workspace's retained executor format.

## What the numbers mean

`scenario_results` gives our cash, rival cash and their difference after the
reported `completed_depth`. These values are exact transitions *conditional
on the modeled actions, inventory and future-event assumptions*. They are
not guaranteed final-season coins or win probabilities. The report states
whether the simulated season has actually ended.

Opponent actions are modeled as idle, mirrored market orders, or frontloaded
orders with additional hypothetical inventory. Opponent worker actions are
PASS. Real rivals can choose other actions; testing against reacting policies
is required. Future shop/weed events use independent hypothetical seeds, not
the live episode seed. The leaf evaluation discounts held inventory and seeds
and does not credit unexecuted future harvests. Consequently short searches
can undervalue long-term farm expansion.

The offline plan is a common action sequence across scenarios; the continuation
comes from the first scenario's observed state. Replan when an actual new
observation arrives. A generated recommendation is not automatically compiled
into a whole-season agent.

## Budgets and reproducibility

The online search is limited to 48 evaluated programs, beam width3, depth3 by
default. Depth is a maximum: the node budget can be exhausted at the first level for a large order queue. Fixed node budgets make decisions reproducible across machine loads;
runtime is measured in benchmarks. It falls back to the executor if search
raises an exception, and counts that failure in telemetry. A nonzero error
counter fails qualification.

Every built candidate has a manifest binding the exact baseline, engine,
simulator, builder and candidate hashes. Simulation source is the frozen
native Kaggriculture1.32.7 code; verify parity before using another version.

## Qualification

`diagnostics/executable_engine_20260930/PLAN.md` declares paired reacting and
saved-replay gates. `engineering_checks.json` verifies native transition parity,
physical-state preservation, seed independence and offline plan execution.
These engineering checks alone do not establish a stronger agent.

Pass an unwrapped physical executor to `build` (for this experiment, `--baseline diagnostics/executable_engine_20260930/baseline_4eeac9c3.py`). An already-built search agent must not be wrapped a second time. Original candidates and root-main backups are preserved. Kaggle submission
requires a fresh explicit user request under AGENTS.md.
