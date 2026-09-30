# Dynamic production bundle feasibility — 2026-09-28

## Decision

**Reject at feasibility; do not build or test a policy candidate from this
audit.** The local evidence does not identify a repeatable, executable
melon/milk intervention narrow enough to freeze. The conspicuous melon price
gap is mostly a production-start timing gap, while the observable
sell-before-the-next-day opportunity is nearly absent for melons and usually
has the wrong price direction for milk. Closing the output gap would require
a new, state-aware production scheduler with a complete funding, work, and
market model. That is a larger architecture project, not a safe local rule.

This is a feasibility decision, not evidence that a future physical scheduler
cannot work. No candidate outcomes were collected and no promotion claim is
made.

## Scope and frozen target

I read `AGENTS.md`, `agent.md`,
`diagnostics/search_agent_20260926/RESULTS.md`, and the unified frozen target
at `diagnostics/local_target_20260928/PLAN.md`. I used only the saved local
loss and top-20 traces and the native engine. No Kaggle access, download,
upload, `main.py` edit, or `agent.md` edit occurred.

The frozen target has 30 recorded-loss replies and 20 top-team entries (48
unique episodes). The incumbent source hash is
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Its saved baseline loses all 60 seats against the 30 loss tapes and sweeps
17/20 top teams (34/40 seats). Fixed replies diagnose mechanics but do not
react to a candidate, so they cannot establish live strength.

## Evidence against a narrow production or sale trigger

The 30 live-loss product ledgers show a mixed production picture. Own MELON
sales exceed the rival's in 15 games, tie in 2, and trail in 13; own MILK
sales exceed in 16, tie in 1, and trail in 13. Despite that mix, own MELON
cash is lower in 26/30 games and own MILK cash is lower in 25/30. Among the
34 trace pairs where both sides sold the product (30 losses plus four saved
top-20 diagnostics), own average MELON sale price is about 92 coins lower
per unit and own average sale day is 13.3 days later. For MILK, the average
price gap is about 8.5 coins per unit and own average sale day is 0.9 days
later; own sales happen later in 27/34 pairs.

The MELON timing gap does not look like stock sitting unsold. In the same
34 paired traces, own first sale occurs on essentially the first day
sellable stock is observed in the shed (mean lag −0.09 days). Sample losses
show the pattern directly: Yaroslav's first own melon is sold on day 17 after
planting on days 6–13, versus the rival's first sale on day 10; chocolat's
first own sale is day 20 versus day 10; and Vadim's is day 21 versus day 10
after own planting began on day 10. Those traces point to late production
and collection rather than a missed liquidation of already available
MELON.

Same-turn market queue position is also too small to explain the price gap.
Opposing MELON sell orders share a turn only six times across the 34 pairs;
the observed own-versus-rival price difference on those turns averages
about −2 coins. MILK shares a turn 211 times, with an average same-turn
difference of about −1.8 coins. These are much smaller than the overall
average price gaps and do not suggest a general queue-priority correction.

I checked the concrete day-boundary rule: existing shed stock, no own SELL
already queued for that product, room under the 10-order limit, no own sale
that day, and a later actual own sale in the trace. This finds one MELON
window in 34 pairs: six units at a current quote of 221, followed by an
actual next-day sale at 223. It offers no early-sale price gain. It finds
nine MILK windows across seven pairs; only one next-day realized price is
below the current quote, while the mean next-day realized price is 23.67
coins higher. This is a descriptive replay comparison, not a causal market
simulation, but it does not justify freezing an earlier-sale trigger.

The saved top-20 controls reinforce the need for a full route choice rather
than a universal volume rule: DECEM has fewer own MELON/MILK sales, Boey has
equal MELON and fewer MILK sales, while the losing Vadim case and winning
Majkel control sell more of both. The other two top-20 losses are DECEM and
Boey; these cases do not share a single product-volume deficit.

## Why the full bundle is not a bounded patch

The previous search-agent result is direct counterevidence to building a
forecast-first portfolio chooser. Its bundle-search v2 lost all four fresh
paired seeds (eight seats) to reacting `main.py`, with mean seat margin
−88,281; deeper search variants also lost. The recorded gap was execution:
investment pace, funding order, travel, feed, and fertilizer collection.
The 2026-09-27 hire audit found that paid extra hands had no assignments in
the clearest day window, and rival work vectors could not be copied because
the two sides' tile and worker states diverged. The same-day land-order
bundle failed its frozen current-main and public-market gates. Those results
rule out repeating hire-only, same-turn land, or deeper beam-search changes.

A credible MELON/MILK scheduler would need to model and execute all of these
linked commitments from the live observation:

- cash and the order queue, including order cap, fill timing, and planned
  purchases that fund later actions;
- owned land, seed availability, planting sequence, crop age and watering
  state, maturity, harvest capacity, and worker travel/action limits;
- carrying harvested output from field to a tile or shed and the exact turn
  it becomes marketable;
- animal feed/care and milk collection, so new crop work does not starve or
  strand existing animals;
- sale timing and quantity against the changing shop and the reacting
  opponent's market orders.

The trace evidence does not currently establish spare cash, worker turns,
travel capacity, and market headroom for a single common earlier-MELON plan
that would preserve the incumbent's already successful production and
funding. Implementing and validating those coupled mechanics is a
substantial new scheduler effort, likely multi-week in scope, rather than a
small overlay. There is no basis here to invent a weak candidate just to
fill the saved panel.

## Future engineering milestone (not a candidate claim)

If this line is revisited, first build a deterministic **single-day
executable task planner** for one existing, near-mature MELON plot. Select a
saved native state with that plot and an available worker; from the exact
observation, plan worker travel, harvest, carrying/delivery, shed arrival,
and a valid market order while respecting current cash, queue capacity, and
the other committed tasks. Run the plan through the native engine and
require every predicted state transition to match the actual result: the
crop is harvested, product reaches the shed, the order is accepted, and no
unplanned crop or feed obligation fails. This isolates physical execution
without repeating the failed whole-game beam search.

Only after that milestone passes should a receding daily scheduler plan
backward from an earlier melon sale, adding the seed/funding, land, planting,
watering, maturation, and travel schedule. Freeze a separate candidate and
its reference hashes and gates before any outcomes. Use the 50-entry plan
for fixed-tape mechanism/regression checks, then fresh local native games
with both seats and at least two reacting references for any strength claim.

## Artifacts and decision record

- Unified local target and gates: `diagnostics/local_target_20260928/PLAN.md`
- Search-agent failure analysis: `diagnostics/search_agent_20260926/RESULTS.md`
- Prior physical execution audit: `diagnostics/physical_gap_20260927/RESULTS.md`
- Prior hire feasibility audit: `diagnostics/market_portfolio_20260927/HIRE_FEASIBILITY.md`
- Prior funded land-order result: `diagnostics/production_bundle_20260927/RESULTS.md`
- Prior sale predictor/action-rule result: `diagnostics/physical_sale_predictor_20260927/RESULTS.md`

**Decision:** reject the proposed dynamic production bundle at feasibility.
No candidate file, candidate-specific plan, fixed-panel test, or native
reacting test was created or run. Keep the incumbent and the frozen 50-entry
target unchanged.
