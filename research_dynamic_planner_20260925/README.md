# Independent daily farm planner

This experiment is independent of `main.py`: no imported incumbent, embedded
action tapes, seed-dependent decisions, or replay identities. It uses a
rolling work horizon, explicit task prerequisites, and a marginal investment
model built from the current observation. The initial implementation is a
research candidate, not a promoted or submitted agent.

**Current outcome:** v1–v5 were rejected after reactive and matched-shop
tests. The currently edited source represents the rejected v5 experiment;
the frozen standalone files retain each tested version. See `RESULTS.md` for
scores and `PRO_STRATEGY.md` for the untested next architecture. Do not use
this directory as a Kaggle submission without new evidence.

The first concrete step toward that architecture is `terminal_rollout.py`:
it performs both-seat, full-game policy A/B comparisons with reactive rivals,
an optional matched exogenous shop schedule, and separate own/rival cash
attribution. It is an evaluation program, **not** an agent. Its same-agent
identity control and rejected-v5 demonstration are recorded in
`PRO_STRATEGY.md` and `rollout_*.json`.

## Hypothesis

Generating work from current assets and selecting new investments by marginal
revenue will respond to competing production and shop demand better than a
fixed action portfolio. The hypothesis is falsified if the complete agent
fails to increase wins in paired-seat comparisons. Runtime safety alone is
not sufficient evidence of strength.

## Ownership

- This task owns only `research_dynamic_planner_20260925/`.
- Main agent: scheduler, experiment harness, integration and reports.
- GPT-6 Luna/max economics sidecar: `economics.py`, `test_economics.py`,
  `ECONOMICS.md`.
- Existing hire consolidation, sale timing, and replay-wrapper experiments
  belong to the other ongoing task. Do not alter them.
- Do not upload this experiment or replace `main.py` without completed
  verification and, for uploading, an explicit user request.

## Architecture

1. Observe current tiles, workers, cash, supplies and public market.
2. Build finite jobs with movement, supplies, work and delivery prerequisites.
3. Allocate workers to feasible jobs, using urgency and expected net value.
4. Execute one action per worker and validate prerequisites against the next
   observation. Rebuild jobs when the farm changes.
5. Reprice new crop/animal investments using marginal revenue, visible
   production, current demand, and remaining season.

The scheduler explicitly reserves planting-day WATER, feed in worker cargo,
seed requests, and final-day delivery. It accounts for all workers sharing
the shed and for the engine processing unit actions before market purchases.

## Evidence and research

The installed Kaggriculture 1.32.7 engine is the mechanics authority. Source:
[Kaggle engine](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/kaggriculture.py).
The design uses the bounded replanning pattern described by Castaman et al.,
[Receding Horizon Task and Motion Planning in Changing Environments](https://arxiv.org/abs/2009.03139).
That paper motivates replanning feasible short action sequences; it supplies
no evidence that this farming policy wins games.

## Predeclared tests

- Compare mechanics and price calculations directly against the engine.
- Smoke test a complete 720-frame episode and inspect production, wasted
  work, delivery and runtime, not just `DONE` status.
- Paired reactive games versus frozen `main.py` on seeds 0, 1, 42, 20260925.
- Development replay screen: 12 evenly spaced routes from the frozen top-50
  panel, both seats. Diagnose failures before expensive full-panel runs.
- Before promotion: full 100-route panel, negative controls, and fresh
  reactive seeds. The repeatedly used saved panel is development data.

All native games retain the engine's actual future shop draws. If policy
changes alter weed RNG consumption and later shops, fixed-shop diagnostics
may explain the effect but must not replace native win/loss reporting.

## 2026-09-25 v5 throughput ablation (predeclared)

The v1 planner's day-1 investment score favored cows/sheep over melons and
its day-12 cash lag was 17,159 coins versus `main.py` in seed 0. V2–v4
inventory quotas and late staple bonuses did not fix the losses. The v5
ablation changes only the investment ranking objective to
`100 * projected net / (capital + 30 * expected actions * project days)`;
the late staple bonus is zero. It does not force a crop or hard-cap animals.
Test both seats under the v1 observed shop schedule and reactive native seeds
0 and 42. Improvement in one lucky native trajectory without matched-shop
own-cash improvement is not sufficient for promotion.
