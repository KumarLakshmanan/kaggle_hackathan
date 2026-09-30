# Strawberry-only physical-mirror sale horizon — 2026-09-26

## Candidate and scope

`build_mirror_straw24.py` generated the isolated candidate
`exp_mirror_straw24_20260926.py` (SHA-256
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`)
from the submitted `main.py` hash `08aa268a...`. When both publicly visible
farms' tiles and worker positions match, strawberry sales alone may look up
to 24 turns ahead. Other products retain the existing 12-turn mirror horizon;
non-mirror behavior stays at four turns. The first-future-sale protection and
all farm, shop-routing, and other market rules remain unchanged. No opponent
identity, episode ID, seed, or future shops are deployment inputs.

## Development replays and risk route

Six then-available public live losses from corrected submission 56569042 were
captured as action routes and tested in both seats on their original seeds.
The baseline reproduced the exact public terminal cash in each original
seat. The candidate rescued K.Piro (-65 to +1,142) and wei chang (-690 to
+54), each in both seats. It did not rescue the other four losses. Across all
12 games, own cash gained 1,256, fixed rivals' cash fell 2,870, and total
margin gained 4,126. This is a development panel with fixed rival actions,
not independent adaptive validation. Raw paired results:
`mirror_straw24_baseline_live_losses6.json` and
`mirror_straw24_live_losses6.json`.

The previously known `len8487` regression route stayed a +457 win per seat,
exactly matching the submitted baseline; the 14-/16-turn all-product variants
had reversed that route. See `mirror_straw24_len8487_risk.json`.

## Fresh reactive games

The frozen candidate played reacting current `main.py` on two separately
predeclared new 16-seed native blocks, with seats swapped for every seed.
All 64 games ended `DONE`; no advance or gate errors were reported.

| Block | Paired seeds positive / negative / tied | Seat wins / losses / draws | Total candidate margin |
| --- | ---: | ---: | ---: |
| 2611700–2611715 | 12 / 1 / 3 | 25 / 3 / 4 | +11,334 |
| 2611800–2611815 | 10 / 0 / 6 | 20 / 0 / 12 | +7,458 |

The seats of a given seed are correlated, so 64 seat-games are not 64
independent shop draws. The one activated negative seed in the first block
was 2611713 (-121 per seat). On seed 2611715 the candidate did not activate;
the +1,134/-1,134 seat results cancel as a paired tie. Raw evidence:
`reactive_mirror_straw24_fresh.json` and
`reactive_mirror_straw24_fresh2.json`.

## Saved-route regressions and public controls

The full September 25 and September 26 saved top-100 panels already record
where the physical-mirror gate ever opens. Selecting all such routes is an
exact regression screen for this isolated change: on other routes the new
24-turn branch cannot execute before any action divergence. `select_straw24_regression_routes.py`
selected 35/100 older and 25/100 newer routes; every selected route was
tested in both seats, and all runs ended `DONE`.

| Panel | Changed routes | Rescues | Reversals | Own cash delta | Rival cash delta | Margin delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| September 25 | 3 | 0 | 0 | -346 | -10 | -336 |
| September 26 | 8 | 0 | 0 | +326 | -102 | +428 |

The full-panel positive paired-route counts therefore remain 59/100 and
69/100 respectively; this change does not solve the high-strawberry farm
losses. Raw results and exact joins are in the two
`mirror_straw24_sep*_eligible_results.json` files and
`mirror_straw24_panel_comparison.json`.

Matched reactive tests against saved public H6 and Haide implementations
retained all 8/8 control wins for each, with identical cash and zero outcome
reversals over four fresh seeds and both seats. The candidate did not make a
terminal difference in those controls. See
`reactive_mirror_straw24_public.json`.

## Later live-route check and loader parity

After the candidate was frozen, seven newer public games from submission
56569042 were extracted and tested as saved opponent actions. All five
control wins and both control losses retained their outcomes in both seats;
total margin increased 1,110 over 14 games. The two new losses were not
rescued. This is a later fixed-action check, not a reacting-opponent test.
See `mirror_straw24_recent7_baseline.json` and
`mirror_straw24_recent7_candidate.json`.

Kaggle's file-path loader selected the final `kaggle_main_entrypoint` for the
candidate. On activated seed 2611700, both file-path and direct-call games
produced the same +690 margin in both seats, with both agents `DONE`.
`mirror_straw24_file_parity.json` records the source hashes and results.

## Decision

**Promoted the exact candidate to local `main.py`.** The resulting SHA-256 is
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
The preceding uploaded local source is backed up byte-for-byte as
`main_before_mirror_straw24_20260926_08aa268a.py` (SHA-256 `08aa268a...`).
The promoted file's Kaggle file-path loader selected
`kaggle_main_entrypoint`; on activated native seed 2611700, file-path and
direct-call results matched at +690 coins in both seats, with both agents
`DONE`. Evidence: `mirror_straw24_promoted_parity.json`.

Two independent reactive
blocks favor it overall; the saved top-100 screens show no outcome reversal;
the later public routes preserve all control wins; and Kaggle loader parity
passes on an activated seed. The negative reactive seed, small older-panel
cash regression, and unchanged 69/100 saved-route count limit the claim to
an incremental near-mirror improvement. This does not establish top-10 rank
or success against all 100 saved routes. The existing Kaggle submission
56569042 still contains the older `08aa268a...` source. The user subsequently
gave a fresh explicit upload approval, and the promoted file was submitted
separately as **56572390** at 07:01 UTC. Its first Kaggle status was
`PENDING`. See `UPLOAD_56572390.md` for the exact bytes and command.
