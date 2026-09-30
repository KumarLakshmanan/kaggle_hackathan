# Visible-production schedule pilot — 27 September 2026

Frozen f66be305 recovers DECEM in both seats: +13510 and +46307, versus
a2's -82105 in each seat. Both games DONE/DONE, zero overlay/queue errors;
the alternative complete physical schedule activates for 575 turns.

The commit happens only at turn 144, after a byte-identical a2 prefix.
All other 49 saved matchups have different first-two-shop histories in
both seats. Their behavior is therefore unchanged, and their 98 a2 results
are reused with a recorded exclusion proof instead of rerun.

Aggregate development result: **44/50 sweeps, 88/100 seats**, no old sweep
lost. Two newly measured games plus 98 provably unaffected prior games.
This remains a fixed replay development result.

Decision: pass development; start the separately frozen outcome-blind
selection and 128-game native confirmation in NATIVE_PLAN.md. No promotion
or upload. Main remains a2, and the pending upload question explicitly
names a2; this candidate cannot be substituted for those approved bytes.
