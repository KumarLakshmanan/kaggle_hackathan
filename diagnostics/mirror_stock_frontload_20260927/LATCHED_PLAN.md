# Persistent visible mirror, current-stock sale — frozen 2026-09-26 18:49 UTC

The first exact-current-mirror gate missed its motivating sale. A read-only
scan of the frozen 39 public replays shows that episode 113642505 had 145
consecutive exact physical matches earlier, then diverged in tiles while
worker positions and hand counts stayed equal. At step 686 our current shed
held 20 strawberries at visible quote 82, with no strawberry order; the
rival sold at step 690 and our incumbent sold at step 693 after glut.

Build one isolated candidate from exact current `main.py` bytes. Starting at
step 144, latch a public mirror flag only after 24 consecutive observations
with equal farm tiles, farmer positions and hands. From step 480 to 717,
act only when this flag is latched, the farms are no longer exactly equal,
and farmer positions and hands still match. If the current observed shed has
at least four strawberries, visible price is above $1, and the incumbent
has no strawberry SELL, no BUY_PRODUCT, no strawberry PICKUP and fewer than
ten market orders, prepend a SELL for all currently observed stock. No
episode ID, seed, opponent identity, private rival state or future action
can enter the policy. The 24-turn streak is a conservative lineage filter;
the four-unit floor is one regular strawberry harvest. The policy does not
change the existing exact-mirror sale lookahead.

Mechanism smoke: replay the documented episode in both seats. It must fire
at the documented original-seat sale opportunity with no errors and both
games `DONE` before the full development screen. A smoke improvement is
only a mechanism check, not validation. The read-only opportunities scan
found potential activation in 24 of 29 loss cases and nine of ten close-win
controls; this is deliberately a hard screen for regressions.

Development screen: the same frozen 29 current live losses and ten closest
wins, original seeds in both seats with endogenous shops. Reuse the exact
`489fe8e4...` baseline that reproduced all 39 original-seat Kaggle cash
pairs. Require all candidate games `DONE`, zero candidate errors, at least
**five original-seat loss rescues**, at most **one original-seat control-win
reversal**, positive total own-cash change and positive paired-margin change
across 39 original seats. Fail any: reject before fresh reactive and top-100
testing. Saved rival actions are diagnostics, not independent validation.

If development passes, use fresh reactive seeds 2614300–2614315 in both
seats against reacting `main.py`, requiring a positive paired-seed majority,
positive total margin, all `DONE` and bounded call time. Then test the
previously sensitive len8487 route and saved top-100 mirror-eligible subset
in both seats, with no control-win reversal. Back up current source and
verify Kaggle file-path loading before any local promotion. A Kaggle upload
requires a fresh explicit user request and is not authorized here.
