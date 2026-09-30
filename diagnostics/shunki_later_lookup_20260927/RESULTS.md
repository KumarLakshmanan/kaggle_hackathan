# Exact-prefix later-shop selector — 2026-09-26 22:09 UTC

The isolated 1,815,505-byte candidate
`exp_shunki_later_lookup_20260927.py` (SHA-256
`68aad0908c38884aba856373088f1a6ba4a0423df2ee00edbec4c796f8e45fac`)
contains 145 distinct recorded routes and 1,241 visible-shop-prefix
entries. It switches at a later shop only where the selected route's
earlier actions match exactly. Kaggle's final callable and direct/file
terminal cash parity passed in both seats.

On the **previously examined** seed 2630130, the selector used the
ICE_CREAM_SHOP/BRUNCH_SPOT/YARN_STORE route at turn 216. One-seat cash
changed from 67,150 versus 162,795 under the old two-shop lookup to
133,173 versus 133,750 here, reducing margin loss from 95,645 to 577.
This is a mechanism check on a known failure, not independent validation.

On fresh native seeds 2630200–2630215 versus reacting unchanged `main.py`,
both seats and original shops, all 64 games finished DONE/DONE and all
32 seat comparisons retained matching first-two shops. Thirteen of 16
paired seeds and 26/32 seats improved margin; total own cash changed
**+664,749**, rival cash **+387,976**, and paired margin **+276,773**.
The weakest seed was 2630211 with BRUNCH_SPOT/PIZZA_SHOP, down
**15,838 paired margin**, exceeding the predeclared −10,000 floor.

**Decision: reject this exact later-shop artifact at the fresh
development gate. No untouched confirmation block, top-100 escalation,
`main.py` edit, or Kaggle upload.** The later-shop rule did fix its
specific old failure, but a new negative tail remains. Further work
must be a separate candidate with new fresh tests; fixed public action
tapes alone cannot validate it.

Evidence: `PLAN.md`, `build_manifest.json`, `candidate_parity.json`,
`reactive_dev16.json`. Reproduce with:

```powershell
python -X utf8 diagnostics\shunki_later_lookup_20260927\build_candidate.py
python -X utf8 diagnostics\shunki_later_lookup_20260927\verify_candidate.py
python -X utf8 diagnostics\shunki_later_lookup_20260927\reactive_dev16.py
```

## Exact event diagnosis of the weakest new seed

Read-only native event traces reproduced seed 2630211 cash exactly:
main self-play 96,306/96,306, later-shop selector versus main
104,535/112,454. The selector increased its own cash **8,229** but
increased the reacting main opponent's cash **16,148**. Relative to its
main-self-play control, the rival collected **+9,371** net MILK and
**+7,289** net STRAWBERRY cash, partly offset by **−9,027** TOMATO.
The selector itself gained **+3,478** MILK and **+3,374** STRAWBERRY net
cash but lost **6,072** CARROT cash. No failed market orders were found
for the selector in this game. These deltas show a market interaction
and schedule tradeoff; they do not isolate a causal one-step fix.
**Diagnostic decision: no new policy promotion from this trace.**
Evidence: `loss_2630211_ledger.json`, `diagnose_2630211.py`.
