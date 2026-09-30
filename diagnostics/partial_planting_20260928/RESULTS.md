# Runtime partial planting — development pass, 2026-09-28

All 20 fast diagnostic games finish DONE/DONE/720 with zero recorded
errors. The incumbent-plus-guard arm 57f41f1e rescues no target and is
rejected at its frozen development gate. The complete-route-plus-guard
arm **06803086** rescues current Boey in both seats, with **+4,935**
margin each (route-only -1,577; main -20,873). Its guard activates three
turns in each Boey game. Yaroslav remains -324 and DECEM -62,163.

Both winning controls remain wins: Kaggledew +4,877 and Majkel +13,889
per seat. Majkel activates one guard turn and declines from main's
+17,814; this is reported without adding an unplanned cash-only veto.

**Select 06803086 for original native parity, then the full saved panel.**
These are selected development cases; no reacting strength qualification
or promotion has occurred. Main is unchanged. See `PLAN.md`, `pool.json`,
`fast_screen.json/jsonl`. The selected standalone file is backed up in
the workspace root before proceeding.

## Native parity — 2026-09-28 03:23 UTC

All ten selected-arm games finish DONE/DONE/720 with zero recorded policy
errors in the original native framework. Rewards and complete telemetry
match the fast results exactly, including both Boey wins. **Pass native
parity; advance to the complete 50-fixture saved panel.** The ten verified
games are reused in that 100-game ledger without duplicate counting.
Evidence: `native_parity.json/jsonl`.

The repeated Boey mechanism trace confirms successful WHEAT plants at
steps 187, 251 and 261. Four excess PLANT commands become PASS; every
retained target command consumes an already owned seed and creates the
expected plant. The resulting future shop path first differs from the
route-only control at observation 288. Thus the +6,512 relative-cash
change cannot be attributed solely to three crops' direct receipts.
Evidence: `boey_mechanism.json` and its hash-checked trace.

## Full saved-panel result — 2026-09-28 03:31 UTC

All 100 original-framework games complete DONE/DONE/720 with zero errors.
The ten development games retain exact fast/native cash and telemetry
parity. All 34 incumbent winning seats remain wins. The new result is
**18/20** top-team sweeps (36W/0D/4L) and **0/30** public-loss sweeps
(0W/0D/60L), **18/50** combined. Only Boey is rescued; DECEM and Vadim
remain the top-team losses. **Pass the saved-panel gate, not promotion.**

The separately frozen `NATIVE_PLAN.md` now controls fresh reacting
qualification. It compares the new file to both current main and its
route-only component, in two prospectively selected activation strata,
against both main and the market reference. Prefix selection is local and
does not inspect terminal outcomes. Main remains unchanged; no Kaggle.
Evidence: `native_full.json/jsonl`.

## Explicit experimental upload — 2026-09-28 03:54 UTC

The user explicitly selected backed-up 06803086 for Kaggle submissions.
Four local direct/file-loader games first passed: both seats reproduce all
719 action pairs and final cash exactly against saved Boey, including the
active partial-planting repair. All finish DONE/DONE/720, with no recorded
direct policy errors and 60 seconds of overage remaining.

Kaggle accepted the exact candidate as **56628152**, dated **03:54:13 UTC
(09:24:13 IST)**. Its status was **PENDING** at 03:54:18 UTC, without a
score. **Accept packaging; experimental upload completed at the user's
request. Independent strength qualification remains incomplete.** The
saved-panel win counts are unchanged and no leaderboard/replays were
refreshed. Root main remains exact 4ee and the local pilot scan continues.

Evidence: `../upload_partial_planting_20260928_06803086/loader_parity.json`
and `../upload_partial_planting_20260928_06803086/upload_receipt.json`.

## Bounded reacting coverage — 2026-09-28 04:42 UTC

The frozen scan completed **2,606 prefix games**, exhausting its allowed
range where coverage remained missing. The selected pairs are 4ee route
2920103/2920161, 4ee other-guard 2920340/2920545, and market route
2920049/2920091. It finds **zero** market other-guard pairs through 2922047.

**Do not advance under this plan: required activation coverage failed.**
No terminal reacting strength games were run, so this is insufficient
coverage, not an observed win-rate rejection. Do not enlarge the range or
silently remove the missing stratum. The exact source remains an uploaded
experimental candidate; local main stays 4ee. Evidence:
`pilot_eligibility.json`, SHA-256
`3cc3323a437659aaccfc78a1d15baa96196225e1dd8b53b741472a7889ff3d23`.
