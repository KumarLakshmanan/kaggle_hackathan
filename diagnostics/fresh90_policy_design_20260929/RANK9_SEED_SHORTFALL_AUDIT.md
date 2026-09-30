# Rank 9 strawberry seed shortfall audit — 2026-09-29

## Decision

The step-166 failure is a real, scheduled crop loss. Its first causal event is
the step-160 WHEAT product purchase, which uses $28 needed for the next
strawberry seed commitment. Withholding that purchase in this trace would have
left enough cash for the scheduled step-165 seed purchase and step-166 plant.
Record this as an untested lead only: do not build or tune a liquidity guard
from this audit. The six potential strawberry units do not demonstrate a win
rescue against the episode's $9,792 loss, and the shared-market effect of the
different wheat and strawberry volumes is not measured here.

## Trace evidence

Source is `main_candidate_minimal_repair_20260929_cb76fbc4.py` at SHA-256
`cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74`.
Both rank-9 seat traces for public episode `115320793` show the same actions
and state progression; they are paired seats, not independent episodes.

| Step | Cash and seed state before action | Market order | Outcome |
|---|---|---|---|
| 151 | $394, 0 strawberry seeds | Buy 2 strawberry seeds | Succeeds; step 152 has $194 and 2 seeds |
| 152 | $194, 2 seeds | None | Two scheduled strawberry plants consume both seeds |
| 160 | $194, 0 seeds, 12 wheat in shed | Buy 1 wheat product for $28 | Succeeds; shed wheat becomes 13, cash $166 |
| 162 | $166, 0 seeds, 13 wheat in shed | Sell 1 wheat, then buy 1 strawberry seed | Both succeed; sale restores $28, seed costs $100; step 163 has $94 and 1 seed |
| 163 | $94, 1 seed | None | Scheduled plant consumes the seed |
| 165 | $94, 0 seeds | Buy 1 strawberry seed for $100 | Fails as unaffordable; this is the only market order |
| 166 | $94, 0 seeds | None | Hand 3 attempts `PLANT STRAWBERRY` on vacant tile `[1,0]`; no crop is created |

The causal budget counterfactual is straightforward on the recorded actions:
skip the step-160 wheat purchase. The step-162 wheat sale and seed buy then
leave $122 rather than $94, so the step-165 seed buy succeeds and the step-166
plant has its seed. The step-160 purchase and the step-162 sale are a one-unit
wheat round trip in this trace; the shed starts at 12, and the later plan also
buys wheat. This makes that purchase a plausible liquidity tradeoff, though
its wider market effect still needs a reacting-game test.

## Lost production evidence

After step 166, the scheduled worker plan continues treating `[1,0]` as a
strawberry crop: water actions reach it at steps 167, 205, 255, 303, 351,
383, 428, 479 and 521; fertilize actions at 382 and 478; harvest actions at
406, 452, 496 and 546. The tile remains empty in the trace through these
actions and is later planted with wheat at step 548.

Using the native crop rule (`first_yield_day=10`, interval 2, max yield 4)
from `diagnostics/physical_route_rollout_20260928/native_core.py:9,676-710`,
a strawberry planted on step 166 (day 6) and watered/fertilized as scheduled
would produce 2 units at day 16, 1 at day 18, 2 at day 20, and 1 at day 22:
six units in total. Those yields align with the four recorded harvest
attempts. This is a counterfactual production count, not observed revenue.
The trace's strawberry prices at steps 406, 452, 496 and 546 were $164,
$112, $95 and $114. Actual future sale timing, own receipts and the rival's
response to added strawberry supply are not isolated, so these prices should
not be multiplied into a claimed margin gain.

## Generalizable candidate scope and counterevidence

A possible future rule could project available cash through the next few
scheduled market turns and committed plant actions. If current seed inventory
plus already-scheduled seed purchases cannot cover an imminent crop planting,
and a scheduled sale would fund the seed, suppress a lower-priority
`BUY_PRODUCT` that would make the later seed unaffordable. This would have
suppressed the step-160 wheat buy in this fixed action sequence. It has not
been implemented or tested, must preserve feed and other physical needs, and
would need reacting-opponent evaluation because changing product purchases
alters shared prices and supply. Prior broad wheat-reserve transplants failed;
that is relevant caution, not a test of this narrower mechanism.

In the 20 seat-0 fixture traces (15 distinct public episodes), I found three
strawberry `PLANT` actions with zero seeds: rank 8 at step 180, rank 9 at step
166, and rank 19 at step 190. That is 3 of 568 strawberry plant requests in
this correlated diagnostic panel. Rank 8 and rank 19 also have competing
orders ahead of seed purchases, while rank 9 is specifically an upstream cash
reservation miss. This recurrence shows the mechanism appears in more than
one episode, but the low trigger rate limits expected aggregate impact. Do not
infer that it flips rank 9's -$9,792 loss by itself.

## Promotion record

- **Candidate:** route-aware seed liquidity guard for already-committed,
  imminent crop planting.
- **Evidence:** one failed strawberry crop with six scheduled native yields;
  three strawberry seedless plants across 20 fixture rows / 15 episodes.
- **Status:** untested lead only; no guard should be built or tuned from this
  audit. No candidate code was changed and no games were run.
