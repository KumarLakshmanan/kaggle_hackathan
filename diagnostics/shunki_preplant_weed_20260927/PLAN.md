# Clear weeds in an otherwise wasted action before planting

The original top-50 ymg_aq trace has PLANT commands on weeds at turns
269, 352 and 438. Its route schedules PASS immediately before the first,
and HARVEST before the other two. These preceding commands cannot change
a weed tile. Replacing them with DIG can restore the already scheduled
planting and watering without moving a worker or delaying the crop.

Use submitted `3cc0f69f...` as the immutable source. If a worker stands on
a visible weed, its current command is a tile operation that is a no-op
on weeds, and its next recorded command is PLANT/BUILD at the same spot,
replace only the current command with DIG. Skip day boundaries and the
last turn. Do not replace valid shed operations or moves. No prices,
opponent identity, hidden state, or seed conditions are used.

Development: eight known top-50 losses, both seats. Require DONE, zero
exceptions, actual repairs, and at least one new two-seat win before the
full top-50 regression panel. Full-panel gate: more than 42 sweeps with
no more than one existing sweep lost. Record cash only as diagnosis.

If passed, use fresh native seeds 2634200–2634231 in both seats, old and
new against frozen prior main 489fe8e4 and new versus reacting submitted
3cc. Require all DONE, no aggregate win-point regression against the
prior main, at least 20/32 paired win points against 3cc, and at least
four activated seed pairs. Sparse activation does not establish benefit;
it requires a separate prospective outcome-blind conditional panel.
Verify both-seat file loading before any promotion. No upload authorized.
