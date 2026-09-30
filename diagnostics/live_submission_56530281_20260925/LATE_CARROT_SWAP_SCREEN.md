# Predeclared late wheat-to-carrot planting screen

Date: 2026-09-25. Frozen `main.py` SHA-256:
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.

Three of the 11 actual live losses first diverged from a near-mirror rival's
carrot plantings at replay action rows 647–657. On 113151063 and 113160599,
we requested five WHEAT plants in action rows 657–659 while the rival requested five CARROT
plants in those same slots; 113161648 also diverged late. Their lower CARROT
units were an observed quantity deficit, not merely sale-order pricing.

Hypothesis: on the standard late route-2 skeleton, buying five CARROT seeds
before action row 657 and replacing the five planned WHEAT plant requests in
rows 657–659 with CARROT might improve endgame net cash. The competitor's actions
are motivation only, never runtime input. More carrots could instead miss the
harvest/sale window or saturate price.

Standalone treatment `exp_late_carrot_20260925.py` modifies **only** the
standard observed skeleton: at policy step 652 (replay action row 653) change
its WHEAT-seed ×2 order to CARROT-seed ×3; at policy steps 653 and 654 change
WHEAT-seed ×1 to CARROT-seed ×1; at policy steps 656–658 change existing
PLANT WHEAT unit requests to PLANT CARROT; at policy step 657 remove the
now-unneeded WHEAT-seed ×2 order. It leaves later original
CARROT-seed orders and all other farm/market actions intact. It activates
only if the policy-step-652 skeleton is present, cash is sufficient and standard
configuration is in use; subsequent missed skeletons are logged. It uses no
seed, episode ID, rival current action, future shop, or private opponent data.

Primary development screen: the same 24 live opponent tapes, original seeds,
both seats, including the three target losses and all 13 existing winning
routes as controls. Frozen baseline: 13/24 route wins, 26/48 seat wins,
all `DONE`. To justify **further** testing, require at least 15/24 routes and
30/48 seats, no baseline winning route reversal or timeout, and positive own
cash in every rescued loss. If it fails, stop; do not tune by individual
episode or shop pair. If it passes, inspect successful plant/harvest/sale
counts and run the full historical 100-route panel and fresh reactive games
before any `main.py` promotion. No Kaggle upload is authorized here.

## Harness correction before treatment results

The first 48-game run accidentally used replay action-row numbers as policy
step numbers. Its candidate telemetry recorded **zero activations and zero
changed orders/plants** in all 48 games; its byte-for-byte baseline outcomes
are therefore a no-treatment harness check, not a result for the hypothesis.
That output is retained as `late_carrot_24routes_both_seats.json`. The code
above now uses the corresponding policy steps (row minus one) and will be
rerun to a distinct output file with the same predeclared gate.

## Corrected treatment result — rejected

A two-seat smoke test confirmed one activation, three seed-order changes and
five plant-command changes per game on target 113151063. The corrected full
48-game screen then completed with both agents `DONE` throughout and a
maximum measured candidate call of about 370 ms. The outcome remained
**13/24 route-pair wins and 26/48 seat wins**; no lost route was rescued.
The three originally motivating losses improved by only +22, +40 and +32
margin coins per seat, while another loss worsened by 232 and a baseline
+140 winning margin narrowed to +6. Two cases activated at turn 652 but
later missed the planned skeleton, so the unguarded early seed replacement
was wasteful there. The predeclared promotion gate failed and the treatment
is not in `main.py`. Full data: `late_carrot_corrected_24routes_both_seats.json`.

The exact same-seed/seat event traces for target 113151063 explain the small
gain. The candidate successfully changed five WHEAT plants to CARROT, sold
**10 more CARROT** units for +251 sale coins, sold **10 fewer WHEAT** units
for −210 sale coins, and spent 40 additional coins on seeds. Its own terminal
cash improved by only **one** coin; the paired margin improved by 22 because
the frozen rival's cash fell 21. Shops were identical in both native traces.
The trace files and `analyze_late_carrot_trace.py` reproduce these figures.
This is not a general solution to the recurring carrot-volume gap: product
mix must be judged on net profit, including seed cost and reduced wheat sale,
not only the rival's extra carrot units.
