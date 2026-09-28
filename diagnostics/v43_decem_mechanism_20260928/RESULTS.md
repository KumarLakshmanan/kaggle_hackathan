# V43 versus 4ee on DECEM — mechanism diagnosis (2026-09-28)

## Decision

**Reject a V43 branch or suffix transplant for a new candidate.** V43 raises
the saved DECEM tape margin by 47,419 coins, from −62,163 to −14,744, in both
seats, but still loses. It starts from a different investment bundle at step
0, and its farm, private inventory, shop sequence, and market state are
already incompatible with 4ee at the first proposed switch (day 3). The
frozen five-fixture screen also found no V43 target-seat win: it still loses
to DECEM, Boey, and Vadim in all six seats, and loses both Majkel control
seats where 4ee wins. The V43 screen retained its two DSM control wins.

The trace does expose a physical execution difference: V43 records fewer
failed worker commands and more changed harvest commands. That is entangled
with its day-zero spending, crop/animal portfolio, extra land, and shared
market effects; it does not isolate a safe component to transplant. A
first-shop selector would be observed only after these opening choices have
already changed the state. No candidate was frozen or tested here.

## Scope and integrity

This report summarizes four repeats of existing local native fixed-tape
results: unchanged 4ee and unchanged decoded V43, each in both seats, against
the same DECEM 719-action route. The fixture is episode 114267880, seed
1390733823, engine 1.32.7. All four runs finished `DONE` and reproduced the
already-scored margins exactly. Route action hash:
`a326e4f9e779ce21762e8cac5a0058884a1676271f296bf4c2291180b0175226`.
Raw replay hash: `1d6a1d7ce66a2e07bd1576528e930ac5f13777fdb88f673eea3aa0a4c34c8072`.
The `main.py` and `main_v43_current.py` hashes match the frozen plan before
and after tracing. These are diagnostic fixed actions, not reacting-policy
validation.

## Where execution first diverges

The step-0 observations are identical within each seat, but the policies
choose different market bundles immediately. 4ee queues 28 WHEAT, sells 24
WHEAT, buys 2 more WHEAT, buys 2 COW and 3 SHEEP, buys 1 STRAWBERRY seed, and
requests four hires. V43 queues 4 WHEAT, two hires, 7 MELON and 5 WHEAT seeds,
and 4 SHEEP. Both farmers PASS. By step 1, cash, hired-hand state, private
inventory/seeds, and shared market inventory differ. This is a policy choice
from the initial state, not a response to a DECEM-only observed trigger.

At the proposed switch snapshots, state compatibility is poor in both seats:

| Day / step | Shops unlocked (4ee / V43) | Candidate cash (4ee / V43) | Candidate land (4ee / V43) | Candidate crop counts (4ee / V43) | Candidate animals (4ee / V43) | Exact matching tile records |
|---|---|---:|---|---|---|---:|
| 3 / 72 | BRUNCH_SPOT / SMOOTHIE_SHOP | 402 / 308 | NW / NW | wheat 18, strawberry 2 / wheat 10, strawberry 2, melon 7 | cow 2, sheep 3 / sheep 4 | 1 of 23 overlapping tiles |
| 6 / 144 | BRUNCH_SPOT×2 / SMOOTHIE_SHOP×2 | 860 / 153 | NW / NW | wheat 7, strawberry 10 / wheat 6, strawberry 6, melon 7 | cow 4, sheep 4 / cow 1, sheep 4 | 5 of 24 |
| 10 / 240 | BRUNCH_SPOT×2, FARMERS_MARKET / SMOOTHIE_SHOP×2, FARMERS_MARKET | 1,380 / 778 | NW+NE / NW+NE | wheat 1, strawberry 33, melon 1 / wheat 8, strawberry 21, melon 7 | cow 4, sheep 5 / cow 8, sheep 4 | 7 of 48 |
| 18 / 432 | BRUNCH_SPOT, BRUNCH_SPOT, FARMERS_MARKET, BAKERY, YARN_STORE, BRUNCH_SPOT / SMOOTHIE_SHOP, SMOOTHIE_SHOP, FARMERS_MARKET, SMOOTHIE_SHOP, PET_CAFE, PIZZA_SHOP | 19,256 / 31,421 | NW+NE / NW+NE+SW | wheat 1, tomato 1, strawberry 32, melon 1 / wheat 15, strawberry 35 | cow 2, sheep 2 / cow 10, sheep 4 | 5 of 48 |

The full candidate observation, candidate farm, private shed, and shop list
differ at all four checkpoints. Candidate shed inventories also diverge
early: at day 3, 4ee has 21 WHEAT and 5 FERTILIZER versus V43's 9 WHEAT; at
day 6, V43 has 25 WHEAT versus 4ee's 7; by day 18, 4ee holds 45 STRAWBERRY
versus V43's 8. The day-18 land difference is two quadrants versus three.

This agrees with the prior splice findings in `agent.md`: the 2026-09-27
shop-reveal audit found routes divergent from step 0 through step 143, low
tile agreement at steps 72/144, and zero hand-position overlap before the
second reveal; the route-library audit found no distinct continuation
matching the flagged losses' first 240 worker actions and investment. The
current trace likewise offers no compatible state at day 3, 6, 10, or 18.

## Cash, production, and worker execution

For both seats, terminal candidate/rival cash is 56,371 / 118,534 under 4ee
and 124,960 / 139,704 under V43. V43's own market operations net 121,960
coins versus 53,371 under 4ee (+68,589); the fixed-action rival's market
operations net 136,704 versus 115,534 (+21,170). The paired margin therefore
improves by 47,419 but remains negative.

V43 makes 100 successful BUY_PRODUCT unit fills costing 3,497 coins,
compared with 3,773 fills costing 157,460 under 4ee. V43's successful sale
receipts are lower (148,692 versus 231,720), while the fixed-action rival's
receipts rise (165,570 versus 144,246). 4ee's receipts are dominated by
WHEAT (149,894); V43 shifts its own receipts toward MILK (60,540) and
STRAWBERRY (52,500). The rival also sells more MILK and STRAWBERRY in V43's
market. The fixed route does not react, but its fixed actions still face the
market and prices produced by each candidate.

| Candidate-side activity | 4ee | V43 |
|---|---:|---:|
| Harvest commands that changed farm/private state | 293 / 453 (64.7%) | 384 / 420 (91.4%) |
| Actual hired-hand non-PASS commands | 5,339 | 6,006 |
| Actual hired-hand non-PASS commands with no state change | 1,149 (21.5%) | 199 (3.3%) |

Counts exclude action slots for hands not present in the pre-action farm
state. “Changed” means the instrumented action changed farm or private state;
harvest command counts are not a count of units produced.

### End-of-day cash by day

The four columns are candidate cash and fixed-action rival cash for each
policy. Seat 1 produced the same daily values and terminal margins as seat 0.

| Day | 4ee own | 4ee rival | V43 own | V43 rival |
|---:|---:|---:|---:|---:|
| 0 | 98 | 5 | 170 | 6 |
| 1 | 155 | 165 | 106 | 162 |
| 2 | 402 | 50 | 308 | 49 |
| 3 | 66 | 15 | 464 | 24 |
| 4 | 466 | 64 | 10 | 10 |
| 5 | 860 | 661 | 153 | 609 |
| 6 | 897 | 14 | 805 | 61 |
| 7 | 234 | 223 | 431 | 237 |
| 8 | 81 | 226 | 215 | 841 |
| 9 | 1,380 | 207 | 778 | 493 |
| 10 | 3,401 | 8,343 | 6,835 | 8,796 |
| 11 | 4,786 | 13,016 | 6,232 | 15,206 |
| 12 | 6,025 | 15,750 | 9,288 | 18,818 |
| 13 | 6,706 | 17,094 | 9,102 | 21,854 |
| 14 | 9,523 | 20,170 | 10,706 | 26,800 |
| 15 | 10,203 | 23,931 | 15,984 | 31,042 |
| 16 | 14,934 | 35,894 | 20,983 | 43,069 |
| 17 | 19,256 | 42,084 | 31,421 | 49,939 |
| 18 | 27,611 | 51,969 | 38,670 | 60,976 |
| 19 | 30,443 | 56,831 | 44,979 | 68,868 |
| 20 | 36,867 | 63,593 | 52,506 | 78,643 |
| 21 | 38,293 | 64,550 | 66,297 | 82,559 |
| 22 | 38,696 | 67,890 | 74,415 | 90,085 |
| 23 | 39,089 | 73,328 | 81,783 | 95,671 |
| 24 | 39,050 | 76,474 | 86,856 | 101,742 |
| 25 | 40,136 | 83,104 | 94,319 | 108,637 |
| 26 | 42,041 | 88,605 | 99,785 | 114,460 |
| 27 | 42,439 | 98,080 | 103,578 | 121,769 |
| 28 | 47,199 | 110,238 | 114,628 | 131,903 |
| 29 | 56,371 | 118,534 | 124,960 | 139,704 |

## Artifacts and reproduction

- `PLAN.md` — frozen diagnostic scope and decision rule.
- `run_traces.py` — hash-checked repeats of the four existing native fixtures.
- `analyze_traces.py` — read-only daily and checkpoint summaries.
- `trace_analysis.json` — daily cash, receipts, harvest/no-op counts, switch
  checkpoints, tile alignment, and market cash flow by operation for both
  seats.
- `4ee-seat0.json.gz`, `4ee-seat1.json.gz`, `V43-seat0.json.gz`,
  `V43-seat1.json.gz` — captured observations and native event traces.

Reproduce the trace capture and analysis locally with:

```powershell
python -X utf8 diagnostics/v43_decem_mechanism_20260928/run_traces.py
python -X utf8 diagnostics/v43_decem_mechanism_20260928/analyze_traces.py
```

