# Exact cash ledgers for 34 fresh paired-route losses — 2026-09-26

`analyze_loss_ledgers.py` reran current `main.py` SHA-256 `489fe8e4...`
against each of the 34 lost routes from the refreshed top-100 panel on its
source seed, in seat 0 with native shops. Every run reproduced **both terminal
cash values exactly** from `main_100routes.json`; both agents ended `DONE`.
The join uses action hash, seed, and source seat because some teams shared
one public episode. `all34_loss_ledgers_s0.json` contains the item-level
executed cash reconstruction and individual checkpoint records are in
`loss_ledgers_s0/`. These 34 routes have negative *paired* margins; seat 0
itself won the dodsters route by 655 coins.

| Item | Our net cash minus fixed rival, summed over 34 seat-0 games | Routes below rival |
| --- | ---: | ---: |
| Tomato | −175,114 | 30 |
| Wool | −143,782 | 23 |
| Carrot | −71,426 | 22 |
| Egg | −58,139 | 19 |
| Wheat | −40,676 | 19 |
| Strawberry | −27,290 | 22 |
| Fertilizer | +49,400 | 7 |
| Milk | +68,742 | 5 |
| Melon | +75,106 | 5 |

The tomato gap comprises 194,714 fewer gross sale coins, partly offset by
19,600 less tomato seed spending; we sold 2,691 fewer tomato units. Wool has
a 143,782 sale-receipt gap and 252 fewer units sold. Across these selected
losses we spent 21,741 less on hires and 8,000 less on land than the fixed
rivals, so simply adding animal/crop sites also needs a funded labor plan.
The all-item and atomic cash differences reconcile to −261,538 total seat-0
margin, with zero unexplained remainder per route.

This loss-only sample is **diagnostic**. Aggregate tomato and wool gaps do
not prove that buying more tomato seeds or sheep would improve live win rate:
shop unlocks, market prices, worker competition, and rival behavior react to
our actions. Earlier late-tomato eligibility, day-11 sheep expansion, and
route-12 pilot regressions demonstrate that risk. The fresh route panel still
has 66/100 positive paired routes. **Decision:** prioritize a complete,
funded tomato or wool production schedule with explicit work and selling
coverage, tested on winning controls and fresh reactive seeds; do not promote
a partial crop swap or change/upload `main.py` from these ledgers alone.
