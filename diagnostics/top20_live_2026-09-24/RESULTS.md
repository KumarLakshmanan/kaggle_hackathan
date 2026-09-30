# Kaggriculture live-top-20 development check — 24 September 2026

This is a local, fixed-action-replay development panel, not a Kaggle rating or
a guarantee against reactive opponents. The live leaderboard's first 20 teams
were sampled at two recent public episodes each. Each of the 40 unique routes
was run with our agent in both seats using Kaggle Environments 1.32.7 and the
recorded seed. A *route win* below means positive sum of its two seat margins;
individual seat wins are reported separately. Do not group different routes by
seed: several public games reuse a seed.

| Agent/experiment | Route wins | Seat wins | Main conclusion |
| --- | ---: | ---: | --- |
| Current `main.py` | 37/40 | 74/80 | All games DONE; three route losses remain. |
| Day-11 narrow strawberry-to-tomato swap | 38/40 | 75/80 | Only one fresh route changed; gain depends heavily on later shop RNG. |

The three baseline route losses are against the current rank-8, rank-12 and
rank-20 teams. Baseline seat margins: rank 8 = −3,250/−7,604; rank 12 =
−3,990/−3,990; rank 20 = −3,066/−3,066. One route pair each was lost; the
other sampled route for each team was won. This is *not* a claim of 17/20 team
strength over the full distribution of their agents or seeds.

## Causal screen of the narrow tomato candidate

The rule substitutes 13 day-11 seed purchases and placements only with two
already-open tomato-buying shops, no strawberry-demand shop, and public tomato
scarcity. In the rank-8 loss it sold 51 tomato units and changed the pair's
native margins from −3,250/−7,604 to +3,111/−1,026. The alternate farm state
also changed a later shop unlock to Yarn Store, substantially increasing wool
receipts.

A separate 104-route/208-seat older best/failed/selected-top-20 screen retained
all wins but had **zero rule activations**, so it tests regression safety only
where the rule does nothing. On 324 older top-20/top-100 routes, the rule
activated on eight routes (16 seat games), changed eight route margins, gained
one route win, and created no new route loss. Seven margins improved; one
previously winning route regressed by 14,692 paired-margin units. Every seat
game finished, with no rule errors.

The diagnostic-only `--shop-sequence-from` option in
`trace_paired_game_events.py` forces the exact shop unlock types/times recorded
in an earlier native trace while leaving each policy's transactions and prices
to evolve. It is **not** the native Kaggle game and cannot be used as a score.
The unchanged main reproduced the rank-8 native baseline margin exactly under
its original shop sequence (−3,250 in seat 0), validating this comparison.

| Route/seat 0 | Original main | Tomato variant under main's original shops | Native tomato variant |
| --- | ---: | ---: | ---: |
| Fresh rank-8 loss | −3,250 | −3,342 | +3,111 |
| Older narrow loss | −266 | −885 | +1,073 |
| Older rank-12 loss | −4,384 | −1,759 | −29 |
| Older rank-12 comfortable win | +16,895 | +14,573 | +9,549 |

The variant did **not** rescue either of the first two losses under their
original demand path. In the fresh rank-8 crossover, main on the variant's
alternate shop path scored −72, while the variant scored +3,111. Thus the
investment is beneficial under that particular alternate demand schedule but
not under the original schedule. The native win is not a robust economic
correction to the observed loss, so the rule was **not promoted** to `main.py`.

## Other rejected experiments

- Universal second-opening-cow-to-sheep: native fixed-tape results flipped two
  hard losses but turned a prior near-win into a loss. Under original shops,
  rank-12 margin worsened −3,990 → −11,223 and rank-20 margin worsened
  −3,066 → −4,722 (seat 0). The native rescues depended on alternate shop
  outcomes. Not promoted.
- Earlier Yarn Store cow-to-sheep swap worsened the rank-12 and rank-8 losses;
  no robust rescue. Not promoted.
- Broadening the tomato rule to two Pet Cafes worsened the rank-20 loss from
  −3,066 to −10,011 per seat. Not promoted.
- Holding wool sales when late wool quotes were low worsened the rank-12 seat-0
  margin −3,990 → −10,975 even with shops held fixed. It raised opponent cash
  and displaced other receipts under shed/market pressure. Not promoted.
- Disabling clip rescue did not change the rank-12 loss and slightly worsened
  the rank-20 loss. Not promoted.

The loss-trace cash ledgers reconcile exactly. Shed stock is empty at the end
of all three fresh losses; the wool-receipts gap starts before the late price
collapse. In rank 12 our agent has two day-0 sheep versus the opponent's three,
then four versus six around day 7. Our greater eventual sheep/wool production
arrives after prices weaken. In rank 20 the opponent establishes more sheep and
geese while our milk and strawberry receipts are weak. These are observations
about output, timing and allocation—not proof that copying an opponent's farm
is feasible or profitable.

`main.py` was not changed by this check. Its SHA-256 remains
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.
No Kaggle submission was made.
