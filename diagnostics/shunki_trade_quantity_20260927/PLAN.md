# Resource-preserving trade quantities

Frozen 2026-09-27 02:41 UTC before any full candidate games. Parent is
market-queue a2d2869c. A passive offline probe on three existing development
traces found 36–58 feasible quantity changes per game; its forecasts are
not observed profits or independent evidence.

Retain all farm commands, market operation slots, and planned net supplies.
For the first BUY_PRODUCT and SELL pair of WHEAT or FERTILIZER, propose
equal quantity changes of +4, +12, +24, -4, -12, -24, keeping each quantity
in 1..100. Do not add orders or change other goods. Forecast using the
embedded 1.32.7 market against a passive rival, the parent's market queue,
and the original schedule queue if different. The rival forecasts use
explicit hypothetical stock, never unavailable private state.

Every forecast must preserve both players' physical resources and keep our
cash no lower. Require nonnegative relative-cash change under every active
forecast and a positive sum. Prefer the largest worst-case relative gain,
then summed gain. Candidate is deterministic and uses only current observations.

First evaluate native seeds 2674000–2674007, both seats, against reacting
a2: 16 games. Require all DONE, no quantity/queue errors, at least 12 seat
win points, and activation in at least six paired seeds. Otherwise reject.

If it passes, run the entire fixed top-50 panel in both seats. Require at
least 43 sweeps and no previous sweep lost. The panel remains development
and regression only. An additional fresh native old/new comparison against
1f, 489 and C95 will be frozen before seeing its outcomes if both initial
stages pass. No promotion or upload follows from the pilot alone.

Preserve a root backup and source hash. The 50/50 and live top-10 objectives
remain separate; no prediction of an exact rating is justified.
