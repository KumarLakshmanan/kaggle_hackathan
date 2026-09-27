# Six-turn physical-mirror sale advance — 2026-09-26

## Hypothesis and candidate

The local eight-turn sale gate exchanged three paired wins for three paired
losses on a new 40-route live-opponent tape panel. I tested whether reducing
its lookahead to six turns would preserve near-mirror preemption while avoiding
some harmful early sales. `exp_sale_mirror6_20260926.py` is the exact current
local `main.py` plus `mirror6_tail.py`. Only the gated lookahead changes from
eight to six; outside visible physical equality the original four-turn
lookahead remains. It uses only current public observations. Candidate SHA-256
is `375ea0203f078325c2e8562e2e52b74e09b9506b7fedba81bc96fb447d97afae`.

## Matched evidence

All games below finished with both players `DONE`; each saved route was played
in both seats. The local engine was 1.32.7.

| Test | Submitted backup | Local eight-turn gate | Six-turn candidate |
| --- | ---: | ---: | ---: |
| Fresh 40 live-opponent **fixed tapes**, paired wins / 40 | 11 | 11 | 12 |
| Same tapes, seat wins / 80 | 21 | 21 | 23 |
| Current top-100 **fixed tapes**, paired wins / 100 | 59 | 59 | 59 |
| Same top-100, seat wins / 200 | 118 | 118 | 118 |
| Fresh reactive near-clone, wins / 16 | 1 control | 16 | 16 |

On the 40-route development tapes, six turns rescued two backup losses and
reversed one backup win. Relative to the eight-turn gate it rescued two
reversals but gave back one rescue. Across 80 seats, six turns lowered own
cash by 2,746 versus the submitted backup and by 3,483 versus the local
eight-turn gate. These tapes were inspected before choosing the six-turn
candidate, so their extra paired win is development evidence only.

The separate top-100 saved panel showed **no outcome flips** against either
baseline. Relative to the submitted backup, the six-turn candidate lowered
own cash 1,418 and fixed-rival cash 544 across 200 seats. Relative to the
current eight-turn gate, it lowered own cash 580 and raised fixed-rival cash
550. The candidate activated in 36/200 seats for 158 extra advance turns.

Native reactive games used previously unused seeds 2610000–2610007, both
seats, with an unchanged uploaded-backup self-play control on the same
seed/seat combinations. Both gates activated in all 16 games and won 16/16
against the reacting backup. The eight-turn gate had +22,598 aggregate
margin; six turns had +16,194. Six turns yielded 1,678 less own cash and
4,726 more rival cash than eight turns. Maximum candidate call was 272.2 ms.
The check establishes a causal near-clone advantage for both lengths, but
does not establish performance against the leaderboard's diverse agents.

Exact evidence: `mirror6_live40_comparison.json`,
`mirror6_top100_comparison.json`, `reactive_mirror6_fresh.json`, and their
underlying per-game route JSONs. Reproduction scripts are `build_mirror6.py`,
`compare_mirror6.py`, and `reactive_mirror6_fresh.py`.

## Decision

**Reject the six-turn candidate.** It improves only the development 40-route
fixed-tape win count, leaves the broader 100-route results unchanged, and is
weaker than the current eight-turn gate on the fresh reactive control. Keep
local `main.py` at SHA-256
`6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076`.
No Kaggle upload was made.
