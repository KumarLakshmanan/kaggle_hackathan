# Visible-worker repair compared with `main.py`

The new self-contained candidate is
`exp_shunki_visible_repair_20260927.py`, SHA-256
`1f22192297821ab5205b8cdcbd22bd1fab30d546860f3c61e8096a2a4355446b`.
It retains the later-shop selector's 145 recorded routes and shop map, and
adds observation-based weed repairs. Python compilation passed. Kaggle's
file loader selected `kaggle_shunki_visible_repair_entrypoint`; file-path and
direct runs matched terminal cash in both seats on parity seed 2630399.
A controlled weed observation changed an idle PASS to DIG, confirming the
repair code is functional.

On **fresh native seeds 2630400–2630415**, the candidate, unmodified Shunki
selector and unchanged `main.py` each faced reacting `main.py` in both seats,
with original shops. All 96 games ended DONE/DONE; the candidate and main
had matching first-two shops in all 32 seat comparisons. There were zero
repair errors, but also **zero weed-repair activations in all 32 candidate
games**. Consequently, candidate cash and paired margins matched the
unmodified Shunki selector exactly on every seed and seat.

Relative to main-vs-main controls, the candidate improved paired margin on
15/16 seeds, gained 246,330 own coins and 169,030 paired-margin coins in
aggregate. The weakest seed, **2630408**, lost **171,270 paired-margin
coins** (85,515 and 85,755 by seat) and 62,660 own coins. Its first shops
were ICE_CREAM_SHOP/BRUNCH_SPOT and its third shop was BAKERY, a three-shop
prefix absent from the 203 source replays. The selector had no specific
source route for that prefix and kept its two-shop route. This observation
identifies a coverage gap; it does not prove that the missing route alone
caused the entire loss.

**Decision: reject this candidate.** It failed the predeclared minimum
activation and worst-regression gates. It supplies no measured gain over the
existing Shunki candidate. Keep `main.py` unchanged and make no Kaggle upload.
The full comparisons and telemetry are in `reactive_dev16.json`; entrypoint
evidence is in `candidate_parity.json`. Reproduce with:

```powershell
python -X utf8 diagnostics/shunki_visible_repair_20260927/build_candidate.py
python -X utf8 diagnostics/shunki_visible_repair_20260927/verify_candidate.py
python -X utf8 diagnostics/shunki_visible_repair_20260927/reactive_dev16.py
```
