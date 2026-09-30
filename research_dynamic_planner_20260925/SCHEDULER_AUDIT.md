# Scheduler mechanics audit

Scope: focused action-correctness checks for `candidate.py` against the
installed Kaggriculture engine. This is not an economic-tuning assessment, a
whole-game trace, or a control comparison.

## Engine and command

- Engine package: `kaggle_environments` 1.32.7; Kaggriculture implementation
  imported from that installed package.
- Command: `python -m unittest discover -s research_dynamic_planner_20260925 -p test_scheduler.py -v`
- Result on 2026-09-25: **5 tests passed**.

The tests exercise real `make("kaggriculture")` states and submit the
candidate's emitted actions through the installed engine. They pin scheduler
jobs in small states so the assertions do not depend on project ranking.

## Boundaries covered

1. **Seed timing and atomic PLANT:** when two jobs need WHEAT seed and none is
   held, the scheduler waits and requests two seeds. The engine makes those
   seeds available only after unit actions. On the following turn the candidate
   emits both PLANT actions, and the engine plants both. A direct engine check
   also confirms that two same-crop requests with only one seed are rejected as
   a group, not partially applied.
2. **Shared pickup reservation:** two workers need wheat while the shed holds
   one unit. The candidate emits one PICKUP and one PASS; the engine gives the
   unit to only the first worker. The market's later replenishment is checked
   separately from the workers' cargo.
3. **Last action of the episode:** at step 718 (day 29, hour 22 for a 720-step
   game), a worker at shed access emits DROP while the market queues SELL for
   the deposited carrots. The engine ends with empty cargo and shed stock and
   credits sale proceeds before marking the episode done.
4. **Harvest-age boundary:** a WHEAT plant at age 1 is watered but not
   harvested; at age 2 with a ripe yield, HARVEST succeeds and moves its units
   into worker cargo.
5. **Supply prerequisite:** an unfed goose with no wheat in cargo or shed is
   not fed. The worker routes toward the shed, and the engine market supplies
   wheat only after that unit action.

## Economics sidecar status

`economics.py` was absent during this run. The test loader uses a test-only
fallback for `investment_values` (empty project list) and delegates `price` to
the installed engine. Tests explicitly pin jobs and do not assert economic
ranking or tuning. When `economics.py` exists, the same test file loads it
automatically; rerun the command above to confirm the real-sidecar import path.

## Findings

No concrete scheduler/action defect reproduced in the covered boundaries.
This is limited evidence: it does not certify other scheduler paths, the
sidecar's economics, or full-game performance. The engine's ordering and
atomicity constraints above are documented because violating either would
produce silent no-ops or missed harvest/deposit actions.
