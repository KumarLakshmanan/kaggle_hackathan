# Executable search engine — measured results

Candidate `bbffbe65`. Qualified: **True**. Promoted to root main.py: **True**.

The online agent generates market programs by reordering, splitting and merging orders with exact native transitions; it retains the existing complete worker schedule. The separate offline physical planner generates movement, transfers, coordinated work and funded investments. Its focused probes pass, but that broader planner is experimental and has not earned competition promotion.

| Panel | Baseline W/D/L | Candidate W/D/L | Point gain | Candidate mean coin margin | Paired mean margin gain |
|---|---:|---:|---:|---:|---:|
| pilot | 0/16/0 | 16/0/0 | +8.0 | 2,213.5 | +2,213.5 |
| top20 | 32/0/8 | 32/0/8 | +0.0 | 42,770.9 | +568.3 |
| top100 | 132/0/68 | 136/0/64 | +4.0 | 30,409.2 | +765.6 |
| confirm | 67/54/7 | 121/0/7 | +27.0 | 13,313.9 | +2,308.7 |

Confirmation point-rate difference: 0.2109; whole-seed95% bootstrap interval: [0.1640625, 0.25].

## Every reacting reference

| Policy | Baseline W/D/L | Candidate W/D/L | Point gain | Paired mean margin gain |
|---|---:|---:|---:|---:|
| 4ee | 2/28/2 | 30/0/2 | +14.0 | +6,864.1 |
| c95 | 32/0/0 | 32/0/0 | +0.0 | -17.2 |
| cb76 | 1/26/5 | 27/0/5 | +13.0 | +2,414.4 |
| v35 | 32/0/0 | 32/0/0 | +0.0 | -26.6 |

Native confirmation measured peak candidate call: 3.850668s under the six-worker local run. All-case CSV uses nested native timing fields; the generic native receipt field `max_seconds` is zero because that coordinator reads the fast-runner field only. Clean completion is the frozen runtime gate.

Native framework/file-loader parity in both seats: **True**. Same actions/rewards as direct execution; minimum overage: 42.380399s.

Saved top20/top100 are from the2026-09-29 22:34:23IST snapshot. They repeat recorded opponent actions, cannot react, and are correlated; they do not establish a live win rate. Top20 rows are reused in top100; do not add their counts as independent games.

Every case, coins, runtime, action-search counts and exact source hashes: [ALL_CASES.csv](ALL_CASES.csv). All100 saved opponents and every paired seat: [TOP100_PAIRED.md](TOP100_PAIRED.md) and [TOP100_PAIRED.csv](TOP100_PAIRED.csv). Per-phase receipts bind the result ledgers. The original pilot runner is archived under `revisions/run_experiment_pilot.py` after adding the predeclared top100 extension to the coordinator.

Offline planner execution scope: [PLANNER_SCOPE.md](PLANNER_SCOPE.md), [planner_verification.json](planner_verification.json), and the hash-bound four-turn CLI example [planner_cli_receipt.json](planner_cli_receipt.json). Those checks validate generated action execution, not competitive strength or final-season forecasts.

After qualification, the builder was guarded against wrapping an already-built engine. A rebuild from the preserved4ee executor produces the exact tested candidate bytes; recursive wrapping is rejected before creating a file: [build_safety_receipt.json](build_safety_receipt.json). The original generation builder is preserved under `revisions/build_agent_v1.py` with its manifest-bound hash.

No Kaggle submission occurred. Promotion, if any, changes the local artifact only. Beating every opponent or reaching top10 is not established.
