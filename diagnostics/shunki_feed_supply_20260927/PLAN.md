# Fund tomorrow's recorded wheat pickups — 2026-09-27

Fresh top-50 diagnosis found 24 FEED commands without carried wheat in the
DECEM loss, followed by 13 livestock escapes. The first failures occur
around turns 300–305; two workers are away from the shed with no wheat even
while the shed holds 50 units from a later market purchase. No active work
was lost because of missing hired workers. Current score in both seats:
-82,192 against DECEM, FARMERS_MARKET/ICE_CREAM_SHOP/SMOOTHIE_SHOP.

Create a separate candidate based on `3cc0f69f...` that, after turn 240,
checks next turn's recorded PICKUP WHEAT requests. Project current unit
transfers and market stock changes. If those pickups would lack stock, add
a funded wheat purchase at the end of this turn's orders. Require current
cash of at least 2,000, reserve 500 plus conservative current purchase/hire
costs, respect ten orders and shed capacity, and skip shop/day boundaries.
Do not change movement, production tasks, seed choices or sale quantities.
Record activation counts and quantities. This is a testable supply-timing
hypothesis, not a claim that more wheat always helps.

Development: both seats against the fresh DECEM replay, with exact source
and original-seed controls already recorded. Require all DONE, actual
activation, positive own-cash and outcome/margin improvement before further
testing. Freeze the artifact before development. If passed, run all 50
fresh routes in both seats and compare to the existing 42/50, 84/100 source.
Treat this panel as development/regression data once inspected.

If the full panel increases sweep count without losing more than one
existing sweep, test new native seeds 2633200–2633215, both seats: original
and new candidate versus reacting frozen incumbent, and new versus reacting
original candidate. Require DONE throughout, no lower aggregate win points
against incumbent, at least ten of sixteen seed-block win points head to
head with original, and at least four activated seed pairs. If activation
is sparse, do not infer general validation; design a separately frozen
outcome-blind conditional panel. Verify both-seat Kaggle loading before
any promotion. Keep current main and every prior candidate unchanged.
