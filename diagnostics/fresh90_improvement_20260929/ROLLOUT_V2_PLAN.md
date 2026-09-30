# Whole-schedule rollout V2 — frozen before V2 outcomes

The V1 reacting pilot produced no switches or changed rewards. Its original
source remains preserved. Code review identified a forecast mismatch: raw
PLANT actions could trigger atomic rejection in the simulated game, while
real cb76 retains executable planting requests. Do not escalate V1 further.

V2 retains the exact V1 compatible schedule pool, physical simulator and four
explicit unknown-future/rival forecasts, with two changes:

1. Apply the existing partial-planting repair to each forecast action, for
   both own policy and the router rival. Snapshot and restore its telemetry
   so hypothetical actions never contaminate actual execution statistics.
2. Use weak Pareto improvement across scenarios: require minimum predicted
   paired margin gain >=0, average gain >1000 coins, and no scenario own-cash
   decrease. Maximize average paired gain, then worst gain. V1's strictly
   positive1500 floor rejects options that tie when a future event does not
   activate; a tied scenario is compatible with non-inferiority. This is a
   prospective development criterion, not a guarantee about unmodeled rivals.

The queue optimizer remains omitted equally from all forecasts, and rival
inventory/actions remain explicit forecasts. Exact physical execution does
not remove these sources of prediction error.

Freeze a new candidate hash before outcomes. Run fresh newest top20, both
seats versus exact cb76 on the same cases. Pilot gate: clean, activation,
positive total win-points and no lost baseline win. Run all8 predeclared
development reacting seeds if saved pilot passes; require PLAN.md's paired
reacting gates. If the saved pilot fails, preserve results and reject V2;
do not launch conditional confirmation. Newest top100 baseline remains useful
regardless. The 32 independent confirmation seeds remain unused until a
candidate passes all prerequisite gates.

The two initial reacting seed results are development data for V2. No claim
of independent improvement may be made from reusing them. Neither this plan
nor a saved win percentage authorizes a Kaggle upload.
