# Task-preserving hire consolidation: optimistic savings bound

GPT-6 Pro's [strategy consultation](https://chatgpt.com/c/6ab4f501-73e0-83ee-92a4-6283e49dd350)
suggested testing whether the **same completed work** can be scheduled with
one fewer hired worker, as distinct from the previously failed hire caps that
dropped work. This document makes only the first, optimistic scale check. It
does **not** establish a feasible replacement schedule or a policy improvement.

For each of the four previously frozen seat-0 near-tie loss traces, successful
`HIRE` events were grouped by `step // 24`. The final hire on a day is the
highest Fibonacci wage paid that day. `U` sums that last wage over all 30 days,
as though an omniscient scheduler could remove one hire every day while
preserving every productive action, market fill, and future state. That is an
upper bound on *pure wage savings* for this at-most-one-per-day pilot, not an
achievable cash gain. Traces and baseline cash are in
[the near-tie audit](NEAR_TIE_AUDIT_20260925.md).

| Seat-0 route | Baseline margin | Actual season hire spending | Optimistic `U` | Day-30 hires / last hire cost | Days where one last hire alone exceeds seat deficit |
| --- | ---: | ---: | ---: | ---: | ---: |
| marwar22 | −84 | 4,541 | 1,746 | 11 / 89 | 15 |
| Yannik Schiffner | −165 | 3,897 | 1,500 | 11 / 89 | 0 |
| feles99 | −173 | 7,324 | 2,809 | 13 / 233 | 7 |
| hiroshi murakami | −166 | 4,397 | 1,691 | 11 / 89 | 0 |

The bound is financially relevant on all four routes, but day-30 consolidation
alone could cross the seat deficit only for marwar22 or feles99. Yannik and
hiroshi would require savings on at least two days. The existing last-day
10/11-hire-cap screen rescued none, so these numbers justify a **feasibility
search**, not a blind hire deletion.

For example, marwar22's final hand travels to `(9,4)`, waters and harvests a
carrot, returns to the shed, then collects and deposits fertilizer. At the
carrot actions no other worker was within Manhattan distance two in the trace;
several co-located idle workers appeared only during its final deposit. Raw
`PASS` counts cannot prove that bundle is movable. A valid test must preserve
the harvest and sale timing, inventory, and next-day farm state before it may
claim to save the 89-coin final wage.
