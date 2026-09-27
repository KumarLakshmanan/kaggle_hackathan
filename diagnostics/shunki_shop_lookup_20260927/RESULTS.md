# Coarse public-route shop lookup development — 2026-09-26

The newest public episode per first shop and per first-two-shop pair was
packed into one isolated 763,862-byte candidate,
`exp_shunki_shop_lookup_20260927.py` (SHA-256
`371ab5db408e8d9dc3e6d733d3b7f59756b806c471bc9acbe43ee6f2c82f6fbe`).
It uses only shops already visible at turns 72 and 144. Kaggle's final
file callable and direct/file terminal cash parity passed in both seats.

Fresh native seeds 2630000–2630015 versus reacting unchanged `main.py`,
both seats and original shops, produced 64 DONE/DONE games and all 32
candidate/control seat comparisons had matching first-two shops.
Fourteen of sixteen paired seeds and 28/32 seats improved margin. Aggregate
own cash changed **+361,264**, rival cash **+97,600**, and paired margin
**+263,664**. However seed 2630001 with PET_CAFE/ICE_CREAM_SHOP lost
**17,906 paired margin**, exceeding the frozen −10,000 floor. Seed 2630014
lost 3,606 paired margin. The two seats had identical deltas on every
seed in this block, so the seed count is the useful independent count.

**Decision: reject this exact coarse lookup at its predeclared development
gate. No top-100 escalation, `main.py` edit, or Kaggle upload.** The broad
positive result warrants a separate untouched robustness study, but it
cannot repair the failed gate retroactively. The source routes remain
fixed public histories; fresh reactive games are the relevant evidence.

Evidence: `PLAN.md`, `build_manifest.json`, `candidate_parity.json`,
`reactive_dev16.json`. Reproduce with:

```powershell
python -X utf8 diagnostics\shunki_shop_lookup_20260927\build_candidate.py
python -X utf8 diagnostics\shunki_shop_lookup_20260927\verify_candidate.py
python -X utf8 diagnostics\shunki_shop_lookup_20260927\reactive_dev16.py
```

## Separate untouched robustness check — 2026-09-26 21:57 UTC

The candidate bytes were unchanged. On sequential seeds 2630100–2630131,
both seats and reacting main controls, all 128 games finished DONE/DONE.
Twenty-nine of 32 paired seeds improved margin, 58/64 seats improved,
aggregate own cash changed **+353,121**, rival cash **−36,841**, and paired
margin **+389,962**. The distribution has a severe tail: seed 2630130
with ICE_CREAM_SHOP/BRUNCH_SPOT lost **191,290 paired margin** (−95,645
per seat). The two candidate seats each ended at 67,150 own cash against
162,795 rival cash, versus 125,694 each in matched main self-play.

The first-two shops matched in 62/64 seat comparisons. Seed 2630100
changed the second shop from BAKERY to PET_CAFE despite the same seed;
the corresponding paired gain is therefore not a fixed-shop comparison.
The catastrophic seed 2630130 retained the same first two shops in both
arms. Its third shop was YARN_STORE. The three saved public routes for
that first-two-shop pair came from different third shops: FARMERS_MARKET
(selected by this candidate), PIZZA_SHOP, and YARN_STORE. Their actions
first diverge around turn 216, at the third-shop reveal. This supports a
specific later-shop mismatch hypothesis, but does not yet prove it caused
the loss.

**Decision: retain rejection of this exact two-shop candidate.** Broad
gains justify researching a third-shop-aware route selector, but its
state compatibility and fresh performance remain unverified. No main
edit or Kaggle upload. Evidence: `ROBUSTNESS_PLAN.md`,
`reactive_robust32.json`, and public replay IDs 113445495, 113383763,
113347600.
