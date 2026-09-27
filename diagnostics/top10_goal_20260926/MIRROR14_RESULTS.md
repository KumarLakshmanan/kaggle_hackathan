# Mirror-gated 14-turn sale lookahead — 2026-09-26

The isolated `exp_sale_mirror14_20260926.py` candidate (SHA-256
`27ff9808b58b1823f0ab604aa0a694fbf95db018f72f663b922968cfcc83f56d`)
changes only `_ADV_LOOK = 12 if matched else 4` to 14, from submitted
`main.py` SHA-256 `08aa268a...`. The four-turn non-mirror behavior and all
production routes remain identical. `build_sale_mirror14.py` reproduces it.

On 16 predeclared new native seeds 2611200–2611215, both seats, against
reacting current `main.py`, the candidate won **32/32 seat-games**, +17,290
aggregate margin, all `DONE`, with 32 activated games and zero reported
advance errors. This is direct near-mirror evidence, with the two seats of
each seed correlated. Raw results: `reactive_mirror14_fresh.json`.

The previous 16-turn variant reversed the saved `len8487` win. A targeted
regression check reran that risk route and `xi luo` in both seats, on their
original native seeds and action tapes. The 14-turn variant lost `len8487`
by 18 coins **in each seat**, exactly the same result as 16 turns, versus
the submitted 12-turn baseline's +457 per seat. It also narrowed `xi luo`
from +847 to +729 per seat. All four games ended `DONE`. Raw results:
`mirror14_risk_routes.json`; the prior baseline and 16-turn results are in
`diagnostics/top100_refresh_2026-09-26/main_local_100routes.json` and
`mirror16_100routes.json`.

**Reject 14 turns for promotion.** Its direct mirror gain came with a
verified win-to-loss reversal on a previously used fixed-action regression
route, so a wider route screen was not necessary. The saved route is not
independent live validation, but the reversal is a concrete compatibility
risk for the current 12-turn policy. No `main.py` edit or Kaggle upload.

Follow-up seat-0 traces reproduced +457 for 12 turns and −18 for 14 turns.
The first changed sale advanced three milk units from step 313 to 308;
the public milk quote was 105 at step 308 and 116 at the baseline sale.
Later early sales likewise often moved milk, wool or strawberry into lower
current quotes. Candidate final cash fell 363 coins and the fixed rival's
cash rose 112, explaining the 475-coin margin reversal. The trace files are
`mirror12_len8487_s0_trace.json.gz` and
`mirror14_len8487_s0_trace.json.gz`. This supports the rejection without
claiming that the same price path would occur against a reacting opponent.
