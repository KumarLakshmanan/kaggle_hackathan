# 6a step-1 hire-only ablation

Date: 2026-09-29

## Hypothesis

The rejected 23-turn Roman bridge discarded the entire 6a step-1 action. This
ablation preserves the exact 6a action and appends only one `HIRE` market order
on the exact target trigger. It tests whether one additional early worker can
help the remaining `live-114270587` loss without changing the opening resource
collection, route, or market orders.

The wrapper calls the exact 6a parent once on every observation. It does not
use a donor, skip parent calls, replace farmer/hand orders, or alter any other
market command. Controls must match 6a in all 719 observations and actions.

## Fixed panel

Run both seats of `live-114270587` against the saved opponent action tape, plus
both seats of `public-win-114251368` and both seats of the top-20
`Kaggledew Valley` fixture. First rerun the six direct 6a baselines and require
them to match the hash-bound v8 baseline receipt exactly.

## Gates fixed before execution

1. The manifest, panel, parent, candidate, runner, engine, replay, tape, and
   helper hashes must match before and after execution; source-only module
   loading is required.
2. Before full games, run a native four-action prefix in both target seats
   against the exact saved opponent tape. Match the direct-parent step-0 and
   step-1 observations/actions to the existing 6a prefix; prove the candidate
   has one extra hand and `hires_today=5` at step 2, paid exactly $5, with the
   rival and market unchanged, and every other step-2 observation field equal
   after normalizing only money, hire count, the appended hand, and its empty
   inventory. Require the parent to return five hand commands at steps 2 and 3
   after the hire.
3. All six 6a baselines must finish `DONE/DONE` at 720 frames and match the
   existing v8 baseline rewards, margins, outcomes, statuses, and telemetry.
4. The candidate must add exactly one trailing `HIRE` to the complete parent
   step-1 action in both target seats. The pre-step-1 observation must match
   the direct-parent trace. The six parent market orders must remain first in
   order; the candidate action must contain seven market orders, below the
   configured ten-order cap. The wrapper also checks the configured fifth-hire
   price and starting cash; the native step-2 gate must prove the hire actually
   executed for $5 after the preserved queue. No other target-turn intervention
   is allowed.
5. Both controls must match their direct 6a baseline observations and actions
   at all 719 turns, as well as exact outcomes, rewards, margins, statuses,
   frames, and telemetry.
6. Both target seats must change from the 6a loss to a positive-margin win.
   Otherwise reject this intervention. Report paired margin and reward deltas
   even if the win gate fails.
7. All candidate games must finish `DONE/DONE` at 720 frames without policy
   errors. This is a fixed-tape diagnostic only; it is not independent,
   reactive, leaderboard, or promotion evidence.

Root `main.py` and Kaggle are out of scope.

The native runner uses the hash-bound extracted transition core. It does not
exercise Kaggle's framework schema, timeout, or file-loader checks.
