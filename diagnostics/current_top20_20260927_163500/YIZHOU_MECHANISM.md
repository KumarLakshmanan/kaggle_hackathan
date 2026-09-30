# Yizhou same-tape margin regression — 27 September 2026

The fresh rank-15 Yizhou tape is episode 114255901, seed 383655650. Both
policies win both seats. Relative to c68, uploaded 4ee changes final cash:

| Seat | Our cash Δ | Rival cash Δ | Margin Δ |
|---:|---:|---:|---:|
| 0 | −13,787 | +17,868 | −31,655 |
| 1 | −13,011 | +17,637 | −30,648 |

Full native seat-0 traces were rerun from the two hash-verified policy files,
using the same source seed, original shops and static opponent actions. The
cash totals match the paired assessment. Across all 719 turns, both policies
submit exactly the same farmer and hand actions and the same **multiset** of
market orders on every turn. They reorder the queue on 75 turns. The first
action difference is step 1, but it leaves the resulting state unchanged.
The first cash difference appears after step 170 (day 7, hour 2): 4ee's
WHEAT sell/buy order gives us 15 fewer coins and the rival 15 more. The
first market-state difference is pre-step 243; the first shop difference is
pre-step 288.

At step 251 (day 10, hour 11), the rival begins with 2,511 coins under 4ee
versus 2,505 under c68 and submits the same melon sale, wheat-seed purchase
and `BUY_LAND` orders. Under 4ee it buys the 4,000-coin SE quadrant and
ends with 1 coin; under c68 it cannot buy the land and ends with 3,995
coins. This is a concrete threshold that amplifies small prior cash/order
differences into different production and shared-market conditions. By day
18, 4ee has 957 fewer own coins and the rival 161 fewer; by day 24 the gap
is 6,599 fewer own and 9,591 more rival. Final losses are shown above.

One causal probe replaced **only** 4ee's step-170 market order with c68's
order while retaining 4ee on all other turns. The rival still acquired SE
land by step 252 and the final margin was +66,072, versus +66,082 for
unmodified 4ee and +97,737 for c68. Thus the first impactful reorder is
not sufficient to explain or repair the terminal regression on its own.

A narrow candidate worth predeclaring is to retain incumbent c68 ordering
when the queue has both `BUY_PRODUCT` and `SELL` for the same item. This
criterion covers 30 of the 75 changed Yizhou turns, including the first
cash-changing step. It is only a hypothesis: other changed turns and
future-shop feedback may still dominate. If tested, build it separately,
require both seats and original native shops on this tape as a mechanism
check, then a fresh reactive panel with wins as the promotion objective.
Do not promote on this fixed replay or on one favorable margin.

**Decision:** Accept the order/affordability mechanism as a diagnosis;
reject a step-170-only fix and defer the broader guard pending independent
tests. `main.py` and Kaggle status remain unchanged.

Evidence: `yizhou_current_seat0_trace.json.gz`,
`yizhou_prior_seat0_trace.json.gz`, `yizhou_mechanism.json`,
`yizhou_turn170_probe.json`, `assessment.json`, and
`assessment_prior_c68.json`.
