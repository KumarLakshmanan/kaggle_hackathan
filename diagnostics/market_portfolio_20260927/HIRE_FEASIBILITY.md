# Early hire bundle feasibility — 2026-09-27

## Decision

Reject a hire-only patch for promotion. A third-to-fifth hire is affordable on the target day boundaries and often fits in the market queue, but the incumbent does not issue any hand commands on the clearest missed day and sizes later hand command lists to exactly the hires it already made. Adding hires alone therefore buys idle workers. A usable change would need a new task allocator plus a compatible feed, crop, harvest, and delivery schedule; the current route data does not provide a safe drop-in bundle.

No candidate was built and no native seeds were run. This is a feasibility audit of the hash-verified fresh DECEM and Majkel loss traces. Fixed public action tapes remain diagnostic only.

## Evidence source

- Incumbent: exact uploaded 4eeac9c3, frozen at `diagnostics/current_top20_20260927_163500/candidate_frozen.py`.
- Native original-shop traces: `decem_current_seat0_events.json.gz` and `majkel_current_seat0_events.json.gz` in the same directory. These replay the fresh public DECEM and Majkel tapes against reacting 4ee on each source seed; both end DONE/DONE/720 and reproduce the frozen matchup margins.
- Hire cost is read from successful `market_atomic/HIRE` events. Queue length and worker commands are read from each step's actual emitted action. Step boundaries below are each 24-turn day boundary.

## Candidate cash, queue slots, and next-day task assignments

`queue` is the incumbent's market-order count at that boundary. The hires/cost columns aggregate successful hires and their cost during the next 24 turns, steps `[s, s+24)`. `next-day commands` counts hand-command slots emitted during the next 23 turns, steps `s+1` through `s+23`, followed by state-changing hand actions from the trace. This distinction matters at step 0: DECEM places five hires at step 1, after its step-1 action, so there are no hand commands until step 2; those five hands account for 110 commands over steps 2–23.

| Trace | Step | 4ee cash | 4ee queue | 4ee hires / cost | 4ee next-day hand commands / changes | Rival hires / cost | Rival next-day commands / changes |
|---|---:|---:|---:|---:|---:|---:|---:|
| DECEM | 0 | 3,000 | 10 | 4 / 7 | 92 / 89 | 5 / 12 | 110 / 90 |
| DECEM | 24 | 98 | 1 | 0 / 0 | **0 / 0** | 3 / 4 | 69 / 43 |
| DECEM | 48 | 155 | 10 | 4 / 7 | 92 / 92 | 5 / 12 | 115 / 98 |
| DECEM | 72 | 402 | 6 | 3 / 4 | 69 / 54 | 5 / 12 | 115 / 91 |
| DECEM | 96 | 66 | 7 | 4 / 7 | 92 / 85 | 6 / 20 | 138 / 109 |
| DECEM | 120 | 466 | 5 | 2 / 2 | 46 / 44 | 5 / 12 | 115 / 85 |
| Majkel | 0 | 3,000 | 10 | 4 / 7 | 92 / 89 | 5 / 12 | 115 / 96 |
| Majkel | 24 | 96 | 1 | 0 / 0 | **0 / 0** | 4 / 7 | 92 / 78 |
| Majkel | 48 | 152 | 10 | 4 / 7 | 92 / 92 | 4 / 7 | 92 / 87 |
| Majkel | 72 | 399 | 7 | 3 / 4 | 69 / 54 | 4 / 7 | 114 / 102 |
| Majkel | 96 | 93 | 9 | 4 / 7 | 92 / 84 | 4 / 7 | 114 / 105 |
| Majkel | 120 | 402 | 3 | 3 / 4 | 69 / 53 | 4 / 7 | 114 / 100 |

The source trace confirms hire expenses are small relative to cash on hand. At step 24, 4ee has 96–98 coins and spends nothing on hires; the rival hires three or four hands for 4–7 coins. The incumbent queue contains one market order, so adding those hire orders would fit under the 10-order per-turn cap without displacing a market order. Cash and market slots do not block this purchase.

The missing work bundle does. At steps 25–47, 4ee emits an empty `hands` list on every turn in both traces. Its farmer has 22 non-PASS actions out of 23 turns, but no job schedule exists for hired hands. The rival uses 69 or 92 hand-command slots and records 43 or 78 state-changing actions during that window. A hire-only change would leave the new workers without assignments.

At steps 72 and 120, 4ee's queues have room for two additional hire orders in both traces; its cash can cover them, but the next-day hand lists contain exactly three or two-to-three workers' commands. Step 96 has room for at most one additional order in the Majkel trace (queue 9 of 10), while the current list is again sized to four hires. Steps 0 and 48 already have full ten-order queues and four hires; a fifth hire there would require removing an existing order. At step 0 the displaced item would have to come from the incumbent's WHEAT buy/sell sequence, COW/SHEEP purchase, or STRAWBERRY seed order. At step 48 it would come from fertilizer/wheat/seed orders. Neither is a free funding source.

## Schedule compatibility

The source workers' action lists cannot be copied as the missing assignments. At step 24, the exact candidate and rival tile states match on only 12 of 25 occupied sites for DECEM and 10 of 25 for Majkel (matching tile kind, crop/animal, age, and yield). Both sides have the farmer at `[4, 4]` and no hired hands at that boundary, but the crop portfolios differ: DECEM has 19 WHEAT and 1 STRAWBERRY for 4ee versus 12 WHEAT and 6 MELON for the rival; Majkel has 19 WHEAT and 1 STRAWBERRY versus 9 WHEAT and 5 MELON. The rival's hand work is tied to its own tile maturity, shed stock, and positions.

By step 72 the exact-site overlap falls to 5/25 (DECEM) and 6/25 (Majkel). The incumbent therefore needs a new state-aware scheduler; inserting extra HIRE orders or copying the rival's hand vectors does not produce an executable portfolio.

## Conclusion and future gate

The trace supports a genuine early labor-day gap, especially at step 24, but it does not support an isolated hire patch. A future candidate must include the worker tasks that use the labor and must preserve the funding, feed, crop, and sale chain. If such a concrete candidate is built, keep the reserved native block 2720000–2720031 untouched until its artifact and gate are frozen; run both seats with original shop generation against 4ee and at least two reacting references, count wins/draws/losses as primary, and do not promote from fixed replay tapes.
