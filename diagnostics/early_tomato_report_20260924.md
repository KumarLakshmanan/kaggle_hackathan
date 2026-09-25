# Early tomato two-plot pilot — 2026-09-24

Local fixed-replay experiment, not a Kaggle submission. The candidate imports
`main.py` SHA-256 `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1` and does not modify it. Opponent tapes are
fixed historical actions; native shops can change when occupancy changes. Fixed-shop
runs force each original parent/native shop sequence and are counterfactual, not native scores.

The policy substitutes one two-seed strawberry order on days 6–9, only after
a same-day plant→water, later harvest, prospective day-end delivery, raw-tape
market SELL-slot, cash, and projected portfolio-receipts certificate. Future
shed capacity and parent-wrapper order slots are **not guaranteed** by that
certificate; modeled receipts are an optimistic screen, not realized profit.
It uses only the observed shops,
prices/inventory, own physical state, and own committed tape. No opponent/episode/seed
lookup or future-shop information enters the policy. The parent day-18 tomato
gate remains active when all its conditions hold; only these confirmed early
tomato tiles are excluded from its unrelated pre-existing-tomato check.

| Role | Team / episode | Parent native pair | Candidate native pair | Native Δ pair | Parent fixed pair | Candidate fixed pair | Fixed Δ pair |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| loss | Excluding / 112933084 | -78,392 | -75,044 | +3,348 | -78,392 | -72,782 | +5,610 |
| loss | ActiveMusyoku / 112941285 | -32,066 | -32,066 | +0 | -32,066 | -32,066 | +0 |
| loss | ActiveMusyoku / 112937075 | -16,466 | -16,466 | +0 | -16,466 | -16,466 | +0 |
| loss | Boey / 112939032 | -53,424 | -53,424 | +0 | -53,424 | -53,424 | +0 |
| control | KawattaTaido / 112928864 | +30,884 | +30,884 | +0 | +30,884 | +30,884 | +0 |
| control | Gatswei / 112940393 | +12,700 | -1,910 | -14,610 | +12,700 | +7,314 | -5,386 |

## Execution and economics

Values below are executed market commits, not attempted tape quantities.

### Excluding / 112933084 (loss)

Frozen panel pair margin: -78,392.

- Seat 0: fixed own/rival 116,023/155,219 → 115,874/152,265; native 116,023/155,219 → 109,844/147,366. Executed early plants 2, same-day WATER 2, early-plot tomato HARVEST 8 units; tomato sold 80/16,362 → 88/16,282; strawberry sold 244/40,445 → 229/40,222; modeled gain 215.0.
- Seat 1: fixed own/rival 116,023/155,219 → 115,874/152,265; native 116,023/155,219 → 109,844/147,366. Executed early plants 2, same-day WATER 2, early-plot tomato HARVEST 8 units; tomato sold 80/16,362 → 88/16,282; strawberry sold 244/40,445 → 229/40,222; modeled gain 215.0.

The trace confirms two successful early TOMATO seed buys, two plants, two
planting-day WATER actions, 8 harvested units, an 8-unit midnight shed deposit
at step 407, and a successful 8-unit TOMATO sale request at step 409. The
fixed-shop early action diff is exactly step 156 (the seed order) and steps
157/159 (the two plants); the existing WATER commands execute unchanged. The
parent's separate day-18 tomato project still qualified and its ten-seed order
executed. The added 8 sold units did **not** raise total tomato receipts:
16,362 → 16,282 as price impact reached all tomato sales. Own cash fell by
149 per seat fixed-shop and 6,179 per seat native. Rival cash fell by 2,954
fixed-shop and 7,853 native, accounting for the paired-margin gain.

### ActiveMusyoku / 112941285 (loss)

Frozen panel pair margin: -32,066.

- Seat 0: fixed own/rival 60,243/76,276 → 60,243/76,276; native 60,243/76,276 → 60,243/76,276. Executed early plants 0, same-day WATER 0, early-plot tomato HARVEST 0 units; tomato sold 0/0 → 0/0; strawberry sold 247/2,648 → 247/2,648; modeled gain abstained.
- Seat 1: fixed own/rival 60,243/76,276 → 60,243/76,276; native 60,243/76,276 → 60,243/76,276. Executed early plants 0, same-day WATER 0, early-plot tomato HARVEST 0 units; tomato sold 0/0 → 0/0; strawberry sold 247/2,648 → 247/2,648; modeled gain abstained.

### ActiveMusyoku / 112937075 (loss)

Frozen panel pair margin: -16,466.

- Seat 0: fixed own/rival 79,685/87,918 → 79,685/87,918; native 79,685/87,918 → 79,685/87,918. Executed early plants 0, same-day WATER 0, early-plot tomato HARVEST 0 units; tomato sold 0/0 → 0/0; strawberry sold 249/3,461 → 249/3,461; modeled gain abstained.
- Seat 1: fixed own/rival 79,685/87,918 → 79,685/87,918; native 79,685/87,918 → 79,685/87,918. Executed early plants 0, same-day WATER 0, early-plot tomato HARVEST 0 units; tomato sold 0/0 → 0/0; strawberry sold 249/3,461 → 249/3,461; modeled gain abstained.

### Boey / 112939032 (loss)

Frozen panel pair margin: -53,424.

- Seat 0: fixed own/rival 103,125/129,837 → 103,125/129,837; native 103,125/129,837 → 103,125/129,837. Executed early plants 0, same-day WATER 0, early-plot tomato HARVEST 0 units; tomato sold 0/0 → 0/0; strawberry sold 251/45,028 → 251/45,028; modeled gain abstained.
- Seat 1: fixed own/rival 103,125/129,837 → 103,125/129,837; native 103,125/129,837 → 103,125/129,837. Executed early plants 0, same-day WATER 0, early-plot tomato HARVEST 0 units; tomato sold 0/0 → 0/0; strawberry sold 251/45,028 → 251/45,028; modeled gain abstained.

### KawattaTaido / 112928864 (control)

Frozen panel pair margin: +30,884.

- Seat 0: fixed own/rival 78,231/62,789 → 78,231/62,789; native 78,231/62,789 → 78,231/62,789. Executed early plants 0, same-day WATER 0, early-plot tomato HARVEST 0 units; tomato sold 0/0 → 0/0; strawberry sold 246/4,007 → 246/4,007; modeled gain abstained.
- Seat 1: fixed own/rival 78,231/62,789 → 78,231/62,789; native 78,231/62,789 → 78,231/62,789. Executed early plants 0, same-day WATER 0, early-plot tomato HARVEST 0 units; tomato sold 0/0 → 0/0; strawberry sold 246/4,007 → 246/4,007; modeled gain abstained.

### Gatswei / 112940393 (control)

Frozen panel pair margin: +12,700.

- Seat 0: fixed own/rival 107,780/101,430 → 106,123/102,466; native 107,780/101,430 → 104,168/105,123. Executed early plants 2, same-day WATER 2, early-plot tomato HARVEST 8 units; tomato sold 0/0 → 8/640; strawberry sold 249/50,653 → 234/48,551; modeled gain 354.0.
- Seat 1: fixed own/rival 107,780/101,430 → 106,123/102,466; native 107,780/101,430 → 104,168/105,123. Executed early plants 2, same-day WATER 2, early-plot tomato HARVEST 8 units; tomato sold 0/0 → 8/640; strawberry sold 249/50,653 → 234/48,551; modeled gain 354.0.

The trace confirms two successful TOMATO seed buys, two plants, two same-day
WATER actions, 8 harvested units, an 8-unit midnight shed deposit at step 407,
and successful sale of 8 TOMATO units for 640. Displaced STRAWBERRY receipts
fell by 2,102; own cash fell by 1,657 per seat fixed-shop and 3,612 native.
The fixed-shop pair remains a win but loses 5,386 of margin. The native pair
**reverses from a +12,700 win to a −1,910 loss**.

## Decision

Predeclared promotion screen: ≥20% of the original paired deficit on each of
four losses spanning three teams, no exposed winning-control reversal, then
a top-20 test and finally ≥72/100 routes plus ≥143/200 seats on the full panel.

Observed fixed-shop deficit recoveries: 112933084: +5,610/78,392 (+7.2%); 112941285: +0/32,066 (+0.0%); 112937075: +0/16,466 (+0.0%); 112939032: +0/53,424 (+0.0%).

The model forecast only 8 displaced STRAWBERRY units and 6 sold TOMATO units
per committed seat, whereas the fixed-shop trace records 15 fewer STRAWBERRY
sales and 8 extra TOMATO sales. Its +215 Excluding and +354 Gatswei modeled
gains contrast with realized **own-cash losses** of 149 and 1,657 per seat.
Consequently the modeled price impact and delivery timing are not reliable
enough for promotion; successful deposits and receipts above come from the
execution trace, not the forecast. Both committed routes stayed within the
ten-order market cap; all 48 games finished `DONE`, and the maximum candidate
action runtime across the 24 candidate games was 234.6 ms (<1 second).

**Fail.** Fixed-shop loss recovery was only 7.2% on Excluding and 0% on the
other three losses, below the predeclared 20% target. Gatswei is an exposed
**native winning-control reversal**, and its fixed-shop margin also declines.
KawattaTaido was exposed to the gate (two order considerations) but safely
abstained. No top-20 or 100-route/200-seat run was performed. The experiment
is rejected; `main.py` stays frozen and nothing was submitted or uploaded.
