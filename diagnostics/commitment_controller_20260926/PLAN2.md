# Day-6 whole-route commitment experiment — predeclared 2026-09-26

## Causal question and frozen state

The exact active `main.py` SHA-256 is
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
The rejected day-11 sheep overlay failed to represent opportunity cost against
route 9's own sheep, land and worker schedule. On one seed, forcing identical
future shops reversed the effect, so native future-shop uncertainty must be
reported separately. This second and last challenger mechanism chooses a
**whole existing continuation** at the earlier route commitment. It changes
the representation and comparison of investments, worker/land reservations,
physical output and sale timing together; it does not inject a new purchase
into a route that keeps following the old schedule.

Route 0 and route 9 have identical first 144 tape actions. From steps
144–647, route 0 schedules 203 HIRE orders, 3 cows, 3 sheep, 2 geese and
more milk/fertilizer sales; route 9 schedules 219 HIRE orders, 2 cows and
6 sheep with more wool sale and worker/placement commitments. Both schedule
two land buys; both switch to existing route 2 at step 648. This gives a
bounded, complete counterfactual, with no reservation transplantation.

The observation-legal trigger is **step 144**, when the native router
would choose route 9 and exactly one of the first two unlocked shops is a
YARN_STORE. It excludes the existing rare route-128 rival-response control.
The first 144 turns and all other route families are unaffected.

A: native route 9 via unchanged `main.py`. B: compare the incumbent route 9
and alternate route 0 using their full time-indexed plans and the step-144
legal observation. The deterministic model prices planned capital, seed/feed
purchases, escalating daily hires, land, predicted crop/livestock output,
scheduled deliveries and sale slots. It caps sales at projected available
stock, checks money, land, feed and worker demand, and updates public market
inventory and a predicted rival sale stream. It evaluates three hypothetical
future Yarn unlock paths: none, one on day 15, two on days 15 and 21.
Select route 0 only when its estimated terminal **paired margin** is better
in every scenario and its obligations are feasible; model error or ties
fall back to route 9. The forecasts use neither actual future shops nor
the seed, opponent identity, replay name or hidden state. C always uses
route 0 at the same trigger; this is the simple full-route control. In all
arms the inherited native execution, safety, market and terminal layers
continue normally, including response to the changed state.

The approximate gross effect is on the order of thousands to tens of
thousands of coins: a 200-coin WOOL quote makes a 100-unit change worth
about 20,000 before market impact, whereas 16 additional HIRE orders and
different land, animal/feed and delivery schedules consume some of that.
The exact ledger of the first sheep test showed a 27,375-coin wool receipt
change on one seat, demonstrating scale but not a guaranteed route gain.

## Unit, evaluation order, and immutable gates

Engine is installed `kaggle-environments==1.32.7`, 720 turns, standard
two-seat native seeded configuration. The seed is the independent shop/RNG
block; the two seat outcomes are paired within it. Model and simple control
are frozen **before** the following native development block:
seeds 2613000–2613015, both seats, each A/B/C against the trusted reacting
`main.py`. The mechanism-OFF wrapper must first match direct `main.py` on
seeds 2613000 and 2613001 in both seats. Primary measure is positive
summed paired margin per seed. Also report seat wins, rescued draws/losses,
reversed wins, own and rival terminal cash, worst per-seed and per-seat
regression, failed/no-op action evidence, source/runtime and status errors.

Acceptance gate: B must increase paired wins over A and C on this development
block, with all seats DONE, no incumbent winning-control reversal, and no
material downside. If it passes, freeze the exact challenger and evaluate
both previously frozen top-100 saved-action panels and an untouched native
block 2613100–2613115 in both seats. The panels are fixed-action
regression controls, not reactive validation. Promotion additionally
requires better paired wins on the broad panel and independent/reactive
confirmation on the untouched block; cash gain alone does not pass. A failed
development gate rejects B without threshold tuning or access to the
untouched block. If B never switches a route, reject as ineffective.

Do not run unfamiliar downloaded opponent Python in the local unsandboxed
runner. The reacting opponent for this native test is the trusted local
`main.py`. Future shop matching, if performed, is labeled as a diagnostic
intervention, never as an independent native result. No Kaggle upload,
`main.py` edit, commit or push is authorized by this experiment.
