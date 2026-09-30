# Offline perfect-information market diagnostic — 2026-09-27

All four selected games passed all 719 turn reconstructions: both players'
cash, sheds, seeds, worker counts and unlocked land match the passive
trace. Day-boundary parity includes the native inventory deposit and
worker retirement; see `IMPLEMENTATION_NOTE.md` for the corrected first
attempt. No policy was changed or full game rerun.

The search used the **actual recorded opposing queue and private stock**,
which a deployed agent cannot observe. It considered two passes of
reordering existing SELL and BUY_PRODUCT orders while preserving both
players' resources and avoiding an immediate own-cash loss.

| Opponent | Factual margin | Turns with a found improvement | Sum of local relative-cash gains |
|---|---:|---:|---:|
| Driz Lo | +9,617 | 17 | +530 |
| liminhai | -38,375 | 17 | +2,423 |
| istinetz | +5,269 | 26 | +561 |
| Joseph Adamski | +3,010 | 96 | +4,197 |

These sums evaluate separate factual states. They are **not** a full-game
counterfactual, a mathematical upper bound, a globally optimal market
search, or achievable forecast performance. Future money, decisions and
shop generation could change after an intervention.

**Accept the diagnostic. Do not promote or deploy an oracle.** For the
largest loss, the opportunities found by this search are small relative
to the reconciled tomato/melon production deficit. The two-pass3bd
candidate also failed to add a current top-50 win. Further work should
therefore investigate an executable physical production addition or a
new independently validated complete schedule, while keeping whole
existing commitments, worker costs and shared-market effects in view.

Evidence: `PLAN.md`, `audit_v2.json`, source/engine/trace hashes. The
incomplete first `audit.json` remains as a diagnostic failure receipt.
