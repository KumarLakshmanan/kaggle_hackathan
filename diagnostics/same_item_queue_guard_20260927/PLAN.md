# Same-item queue guard — prospective test, 2026-09-27

The incumbent is the exact uploaded `main.py` SHA-256
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Keep it unchanged. The candidate is a copy with one narrow guard: if the
purchase-queue output for a turn contains both `BUY_PRODUCT` and `SELL` for
the same item, skip the final iterated reordering pass and retain the
purchase-queue result. All physical actions, quantities, other queue passes,
and routes remain intact. This guard uses only our visible action and is
implemented in a separate `candidate.py`.

Motivation is the fresh Yizhou top-20 tape diagnosis: 30 of 75 changed queue
turns have same-item buy/sell, and a tiny early order change fed a rival land
affordability threshold. This is hypothesis generation, not validation.
The prior one-turn step-170 override was rejected; this is a broader rule.

## Frozen development gate

Use the official 2026-09-27 16:35 top-20 route manifest with verified action
hashes. First run the five targeted source tapes in both seats: four current
losses (DECEM, Boey, Vadim Vasilenko, Majkel1337) and the current Yizhou win.
Native engine 1.32.7, original endogenous shops, DONE/DONE/720. Require at
least one of the four losses to become a win in **both** seats, while
preserving the Yizhou win in both seats, to justify a full top-20 screen.
Cash margins are diagnostics only. If this gate fails, reject this candidate
for the user's top-20 objective without using fixed tapes as evidence of
general strength.

If it passes, run all 20 tapes in both seats; require at least 17/20 both-seat
sweeps and no lost incumbent winning seat. These tapes are regression data,
not independent reacting-policy evidence.

## Conditional independent native gate

If both tape gates pass, compare the unchanged incumbent and candidate on
fresh seeds 2717000–2717015, both seats, original endogenous shops, seed
masked from both agents, against reacting 4ee, c68, 3bd and historical 1f
policies (256 games). All must be DONE/DONE/720 with zero agent errors and
sub-second max candidate call. Require candidate win points to exceed
incumbent pooled points, no per-reference point regression, and a positive
lower bound of a 95% paired whole-seed bootstrap interval (10,000 resamples,
RNG seed 2717099). Preserve both seats and all references in each block.
Report cash and rival changes separately. Passing this gate warrants
consideration for local promotion and both-seat Kaggle loader verification,
not a claim that it beats all top teams.

Never upload without a fresh explicit user request for that new upload.
