# Visible-stock premium sale race — frozen 2026-09-26 18:41 UTC

Across the 29 live-loss replays, strawberry units were nearly equal but
−9,640 in late receipts came from unequal per-turn batches. A trace of one
loss showed 20 strawberries already in our shed for several turns while the
current route lookahead did not schedule them; the rival sold 20 at step 690
and our sale at step 692 received much less. This is a causal opportunity in
that saved action history, not evidence of a general strategy win.

Build one observation-only candidate from exact current `main.py` bytes. From
step 480 until termination, and only while public farm tiles and worker
positions physically match, inspect our **current observed shed**. If it has
at least four strawberries, the visible quote is above the engine's $1 floor,
the incumbent action has no strawberry SELL, no BUY_PRODUCT, no strawberry
PICKUP and fewer than ten market orders, prepend one SELL of the entire
observed strawberry stock. Keep every existing action/order otherwise. This
rule uses no episode ID, seed, opponent identity, saved future action, or
hidden rival state. Four units is one maximum regular strawberry harvest;
no price threshold or horizon is fitted to the replay cohort.

Development screen: the frozen 29 current live losses and ten closest wins,
each on its original seed and both seats with endogenous shops. Reuse the
`489fe8e4...` baseline that reproduced all 39 original-seat Kaggle cash
pairs. Require all candidate games `DONE`, zero candidate errors, at least
**five original-seat loss rescues**, at most **one original-seat control-win
reversal**, positive total own cash and positive paired margin across the
39 original seats. Fail any: reject before fresh reactive and top-100 tests.
Saved rival actions are diagnostic, not independent validation.

If this gate passes, test fresh native seeds 2614300–2614315 against reacting
current `main.py` in both seats, requiring a positive paired-seed majority,
positive total margin, all `DONE` and bounded call time. Then test the
previously sensitive len8487 route and the saved top-100 mirror-eligible
subset in both seats, with no control-win reversal. Back up current source
and verify Kaggle file-path loading before any local promotion. A Kaggle
upload needs a fresh explicit user request and is not authorized here.
