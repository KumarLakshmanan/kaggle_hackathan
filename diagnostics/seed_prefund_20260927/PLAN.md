# Guarded same-turn seed prefunding — frozen before candidate outcomes

2026-09-27. Base source is the uploaded 4eeac9c3 byte-for-byte backup. Make
one isolated candidate by appending a final wrapper after the incumbent
purchase and two-pass queue logic. Do not edit `main.py` or upload.

## Mechanism and narrow rule

In fresh 16:35 UTC top-20 saved-action games, Boey at turn 187 has 9 coins,
attempts `BUY_SEED WHEAT 2` at 10 coins/unit, then sells 10 WHEAT for 309
coins. Vadim at turn 180 has 3 coins, attempts `BUY_SEED WHEAT 1`, then sells
8 WHEAT for 256 coins. Both seed orders fail before a same-turn sale. Older
current-100 Boey/DECEM/Majkel traces also show failed seed purchases before
sales. These observations motivate an experiment; they do not establish
terminal benefit or acting-opponent strength.

Only when the final incumbent market queue begins with adjacent
`BUY_SEED <crop> n`, `SELL WHEAT q`, and current cash is below one seed unit
price, try swapping those two existing orders. Do not add orders or change
quantities or any worker actions. Require simulator forecasts with an idle
rival and a hypothetical mirror rival to show that the existing sale fills,
at least one extra seed is purchased, no other own purchase/holding/worker/
land signature worsens, and the hypothetical rival's resource signature is
unchanged. Bound immediate market price externality by 20 coins after
accounting for the newly purchased seeds. The guard reads only current
public market/farm state and our private shed/seeds; no opponent identity,
episode ID, configured seed, future shop, or rival-private data.

The prior broad planned-funding composition 7673 was rejected despite
passing broad games: its separate 1,280-prefix reacting coverage audit found
zero eligible cases against the required 16. This narrow seed rule is a new
component with a new activation gate, and whole-policy gains from other
components cannot qualify it.

## Development gates (recorded action routes, not independent validation)

1. Verify base SHA, candidate SHA, route hashes, and a small native trace
   showing the intended extra seed while all orders/worker commands retain
   their original multiset. Check both seats of fresh top-20 Boey and Vadim.
2. Run the full fresh 16:35 top-20 panel, both seats (40 games), original
   shops and seeds. Require at least one of Boey or Vadim to flip to a
   **both-seat win**, no previously winning seat to be lost, candidate
   activation in both seats of the rescued opponent, all DONE/720 and zero
   telemetry/errors. Stop and reject if this first outcome gate fails.
3. Conditional on gate 2, run the 11:37 current-100 and original-50 panels,
   both seats (300 games). Require no incumbent winning seat lost, at least
   73/99 current-100 external sweeps, 36/50 current-50 sweeps and 44/50
   original-50 sweeps, all DONE/720 and zero telemetry/errors. Keep the own
   current-100 self-control separate. Saved tapes are regression only.

## Independent native confirmation, conditional on development

Freeze untouched seeds 2717000–2717031. Compare old uploaded 4ee and new
candidate against reacting 4ee, c68 and 3bd references, both seats, native
shops, masking configured seed from agent observations (384 complete games).
Require at least eight paired seeds where the new rule activates in both
seats across the reference block, including two paired seeds versus each of
two references. Require positive pooled paired win-point gain with a positive
lower 95% percentile bootstrap bound (10,000 whole-seed resamples, RNG
2717099), and no per-reference win-point regression. Report paired margin,
own cash and rival cash as mechanism diagnostics. Require DONE/DONE/720,
zero errors and valid native runtime budgets. If the activation threshold
fails, reject this component as 7673 was rejected.

Only after all gates pass, check direct and Kaggle file-loader all-action
and both-cash parity in both seats of an activated native seed. Promotion
would need a separate review and a fresh explicit user upload request; this
experiment makes no upload or change to `main.py`.
