# Late cash erosion in 29 live losses — 2026-09-26

`late_loss_ledgers.py` replayed each frozen loss against its original public
opponent actions on the original seed and our original seat, using the
installed 1.32.7 engine and current `main.py` SHA-256 `489fe8e4...`. All
29 replays reproduced **both** Kaggle terminal cash amounts exactly and ended
`DONE`/`DONE`. The transaction hook recorded only executed market units and
atomic purchases; every period's cash ledger reconciles to zero residual.
The opponent action tapes are diagnostic, not adaptive validation.

After the last action of day 19, our aggregate margin across these 29 games
was **+589 coins**, and we led in 19 games. From day 20 to the end, margin
fell **24,062 coins** to the observed −23,473 total; 28 of the 29 games lost
relative ground in that period. The late loss was entirely in market cash in
this accounting; other cash differences were zero.

| Product | Late net cash gap vs rival | Losses with negative gap | Executed sale-unit difference |
| --- | ---: | ---: | ---: |
| Strawberry | −9,640 | 23/29 | −4 |
| Milk | −9,519 | 19/29 | −29 |
| Wool | −9,268 | 23/29 | −6 |
| Carrot | −5,170 | 19/29 | −131 |
| Wheat | +7,039 | 5/29 | −2,089 |

The near-equal late strawberry and wool sale volumes, coupled with lower
receipts, indicate a price/timing gap in these observed matchups. Milk's
aggregate gap is concentrated: Tavuk Master accounts for −6,271 of it.
The wheat net advantage includes large offsetting purchases and sales, so
its sale-unit count alone is misleading. All 29 losses had zero shed and
worker-carried inventory after the final settled action (see
`terminal_inventory_losses.json`).

**Decision:** diagnose late market execution and test a narrowly isolated
quote-aware sale candidate. These ledgers do not justify editing `main.py`:
a changed action can move shared prices, future shops, and opponent actions.
Raw per-game and per-period numbers are in `late_loss_ledgers_29.json`.
