# Mirror-gated 16-turn sale lookahead — 2026-09-26

## Hypothesis and candidate

Extending only the physical-mirror sale lookahead from 12 to 16 turns might
front-run a similar opponent for more cash. `build_sale_mirror16.py` produced
`exp_sale_mirror16_20260926.py` (SHA-256
`9d7d237cf5a93a000b39cae74a2bfe6411d610342817b674c3cc0f014ff56993`)
from the then-current `main.py` (SHA-256 `0e2c30f4...`). The only source change
was `_ADV_LOOK = 12 if matched else 4` to `_ADV_LOOK = 16 if matched else 4`.
Original-shop behavior, the normal four-turn sale lookahead, all production
routes and every other source byte were held fixed.

## Native reactive evidence

`reactive_mirror16_fresh.py` tested 16 predeclared new engine seeds
2610600–2610615, both seats, against the 12-turn `main.py`. All 32 games ended
`DONE`, with 27 candidate wins, three losses and two draws. Total candidate
margin was +11,960 coins. The lookahead activated in 30/32 games with zero
reported errors; maximum candidate call was 509 ms. The two-seat outcomes
are correlated within a seed. Seed 2610604 drew both seats without activation;
seed 2610605 lost 288 per seat; seed 2610601 lost 52 in one seat and won 84 in
the other. Thus the direct mirror benefit was positive but less uniform than
the previous 12-versus-8 test.

`reactive_mirror16_public.py` then matched 12-turn control and 16-turn
treatment against two saved *reacting* public agents on four new seeds each,
both seats. All 32 control/treatment games ended `DONE`.

| Reacting opponent | 12-turn wins | 16-turn wins | Treatment margin change | Activation |
| --- | ---: | ---: | ---: | ---: |
| Public preempt H6 | 8/8 | 8/8 | 0 | 0/8 |
| Haide | 8/8 | 8/8 | -217 | 8/8 |

Against Haide, our treatment cash increased 760 coins across eight games,
while the reacting rival's cash increased 977. This is a measured small
margin loss, not a result flip.

## Complete saved-route regression screen

`route_panel_benchmark.py` tested the candidate on all 100 September 26
top-player public action hashes, each in both seats with its original shop
sequence; all 200 games ended `DONE`. `compare_mirror16_routes.py` compared
them against the **12-turn** baseline by action hash and seat. The panel was
already used to develop the 12-turn policy; it is a deterministic regression
screen, not independent validation or a live win-rate estimate.

| Measure | 12 turns | 16 turns |
| --- | ---: | ---: |
| Paired route wins | 69/100 | 68/100 |
| Seat-game wins | 137/200 | 135/200 |
| Aggregate paired-margin change | — | -1,824 coins |
| Changed routes | — | 16 |
| Win-to-loss route reversals | — | 1 |
| Loss-to-win rescues | — | 0 |

The reversed `len8487` route moved from +914 paired margin to -36, a
950-coin paired regression. The next largest regression was -678 on `xi luo`;
the best route improvement was +24. Our own terminal cash fell 1,820 across
the 200 games; rival cash rose four. The increased lookahead activated in 34
saved-route seat-games. The route runner reported a 5.75-second maximum call
while this panel shared the machine with the public-agent tests, so that
isolated latency is not a standalone runtime measurement.

## Decision

**Reject 16 turns for broad promotion.** It gained in direct near-mirror
matches, but it reversed a win and had no rescue in the full saved-route
screen, and it slightly worsened the reacting Haide margins. The evidence does
not justify replacing the locally promoted 12-turn policy. The verified local
`main.py` SHA-256 remains
`0e2c30f44ca7a6e0181e38a8d378af1f266ffacaaef33983a1673061797d647a`.
No Kaggle upload occurred.

Reproduction and raw evidence: `build_sale_mirror16.py`,
`reactive_mirror16_fresh.py` / `.json`,
`reactive_mirror16_public.py` / `.json`,
`diagnostics/top100_refresh_2026-09-26/mirror16_100routes.json`,
`diagnostics/top100_refresh_2026-09-26/mirror12_100routes.json`, and
`mirror16_vs12_top100_comparison.json`.
