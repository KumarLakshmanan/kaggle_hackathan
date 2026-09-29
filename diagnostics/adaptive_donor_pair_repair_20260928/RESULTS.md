# Donor151 observed-pair repair — 28 September 2026

## Development decision: advance exact a44c8c2c to a separately bound full panel

The bounded repair and exact combined pilot pass their frozen gates.
The original bridge48 study remains rejected; this is a new candidate
with two tested observed-shop mappings, not a reassessment of that receipt.

At publicly observed turn144, under the already selected donor151 branch,
map both `BAKERY|FARMERS_MARKET` and `PET_CAFE|ICE_CREAM_SHOP` to existing
donor route2. No opening, quantity, guard, helper, source fallback or
runtime identity/seed logic changed.

Combined candidate SHA-256:
`a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`.
An identical backup is saved in this directory as
`main_candidate_donor_pair_repair_a44c8c2c.py`.

## Engineering evidence

Static audit verified all three existing bridged donor151 routes equal
through raw actions0..150 and that every raw action, queue and hire-recovery
reference consults the same selected schedule/map. All route arrays remain
exactly unchanged. Eight pre-outcome native prefixes each matched 144
actions and 145 observations against exact ceed697f traces, including
the state at observation144. No prefix mismatch occurred.

## Exhaustive bounded route choice

Both actual pairs affect exactly one fixture each, in both seats, within
the completed twelve-fixture pilot. Route0 controls are reused with exact
source candidate, receipt and trace provenance; all eight route1/2 games
were newly executed. Every game was clean.

| Actual observed pair / opponent | route0 | route1 | route2 selected |
| --- | ---: | ---: | ---: |
| BAKERY / FARMERS_MARKET — Boey | -1,943 both | -48,282 both | +10,714 both |
| PET_CAFE / ICE_CREAM_SHOP — booming114279308 | -23,186 both | -39,962 / -42,037 | +3,298 / +2,542 |

Margins are own cash minus rival cash; paired values are seats0/1.
Route2 alone repairs Boey and wins the second pair under the frozen
rescue/points/paired-margin/route-key ordering. Exact32e's Boey margin
was +4,935, so the repair also improves its prior winning margin.

Boey route2 gains 20,489 own cash and 7,832 rival cash relative to ceed,
for a paired-margin gain of 12,657 in each seat. Terminal cash is
101,949 versus 91,235. On booming114279308, own changes are +26,025/+25,647
and rival changes -459/-81, for paired gains +26,484/+25,728.

## Fresh exact combined pilot

All 24 planned seats were rerun with exact a44c8c2c. Result: **20 wins,
0 draws, 4 losses**, or **10/12 both-seat fixtures**. This compares with
7/12 for exact32e and 8/12 for rejected ceed on this same development panel.

- Public subset: 7/8 both-seat wins (14W/0D/2L).
- Top-team subset: 3/4 both-seat wins (6W/0D/2L).
- All exact32e prior winning seats retained.
- All ceed winning seats retained, including booming114232208 and mhw114235177.
- Boey repaired in both seats; booming114279308 newly won in both seats.
- Remaining losses on this pilot: Ghost114288168 and DECEM114267880.
- All 24 rows exactly match expected per-pair/source rewards, statuses,
  frame count and full policy telemetry. No regression or mismatch.

Session37470 exited0 at 2026-09-28T17:40:32.666709+00:00. All frozen inputs
were rechecked unchanged. This result does not establish the complete
top20/public30 counts, and it is not independent reacting validation.
Full50 is not started. Original-native parity, reacting qualification,
public-win regressions and file-loader gates remain before promotion.

## Reproduction and receipts

The frozen sequence is `study.py prepare`, `study.py prefix`, `study.py
screen`, then `study.py combined`; run in a clean evidence copy. Completed
receipts and candidates have overwrite guards. At most one cached worker
ran, recycled after eight games. Source main, existing studies and Kaggle
remain unchanged.

| Artifact | SHA-256 |
| --- | --- |
| combined_results.json | 82953029de1373927b43ffb766dbdaf02b18990d71e534a4a78705c78af517a3 |
| screen.json | 9d8c4649ae5c5932ea994dd74cd7437bd051d93a8ce19ab0d5a04b8c8585098c |
| prefix_results.json | d07387a6b5aad7292d7e0a9d8a334353c99846706c75858200851eaec67d7cf2 |
| pool.json | 8dbb99617d72585b75ee9f2b19d6254f51e30d59bdedc4ea75612919595bdaf2 |
| study.py | 6cc8c077d4781ad8b2820a6153314599962e7b0a8c4236fc79440b145aab8533 |

`screen_binding.json` records the prefix receipt binding before any
full-game outcomes. Every native observation/action trace has its own hash
in the corresponding receipt.
