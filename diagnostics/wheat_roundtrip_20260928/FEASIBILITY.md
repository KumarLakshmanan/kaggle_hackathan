# WHEAT purchase / resale feasibility — 2026-09-28

## Decision

**No-go for a WHEAT purchase cap as a loss-avoidance change on the frozen corpus.** Total WHEAT product trade is cash-positive in all 30 saved live losses, and the identified same-step buy-then-resell pattern also appears in the current Majkel winning control. DECEM’s directly measurable same-step loss is only 6,858 coins against a 62,163-coin fixed-tape loss. This is diagnostic evidence, not a policy test; no game was run and no candidate was evaluated.

## Evidence and method

Read-only accounting of the 4ee event traces at `diagnostics/loss_class_20260927/traces/` (30 original-seat live losses) and `top20_traces/` (current DECEM, Boey, Vadim failures and one Majkel winning control). Source candidate hash is `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`. Counts include successful candidate-seat `BUY_PRODUCT WHEAT` and `SELL WHEAT` unit events only. FEED counts are successful changed actions; `simulation.py` confirms each consumes one WHEAT. Harvested WHEAT sums the pre-action crop `yield_units` on successful WHEAT harvests.

The “same-step resold” amount tags successful WHEAT buys during a market step, then counts them as resold only after WHEAT already in the shed at the first own WHEAT market event has been exhausted. It is a conservative, event-order measure of bought stock immediately sold in the same market step, not an independent replay counterfactual.

| Frozen set | Games | Bought: units / cost | Sold: units / receipts | Net WHEAT trade cash | FEED units | WHEAT harvested | Same-step bought then sold: units / cost → receipts (net) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 30 live losses | 30 | 90,882 / 3,315,483 | 97,981 / 3,577,635 | **+262,152** | 10,521 | 17,626 | 29,512 / 1,056,570 → 941,746 (**−114,824**) |
| Current top20 failures | 3 | 9,518 / 362,170 | 10,000 / 376,148 | **+13,978** | 900 | 1,384 | 4,063 / 159,077 → 144,018 (**−15,059**) |

All 30 live-loss traces have positive total WHEAT trade cash. Their 10,521 successful FEED actions used 10,521 WHEAT; the 17,626 WHEAT harvest units show that purchases are not all serving feed demand. The market stream has substantial same-step churn, but the whole WHEAT book remains profitable in these losses.

| Current top20 tape (candidate seat 0) | Tape margin | Bought: units / cost | Sold: units / receipts | Net trade cash | FEED / harvested | Same-step bought then sold: units / cost → receipts (net) |
|---|---:|---:|---:|---:|---:|---:|
| DECEM | −62,163 | 3,562 / 148,208 | 3,593 / 149,894 | +1,686 | 175 / 206 | 2,155 / 91,751 → 84,893 (−6,858) |
| Boey | −20,873 | 2,478 / 90,244 | 2,729 / 97,587 | +7,343 | 356 / 609 | 669 / 23,777 → 19,180 (−4,597) |
| Vadim Vasilenko | −400 | 3,478 / 123,718 | 3,678 / 128,667 | +4,949 | 369 / 569 | 1,239 / 43,549 → 39,945 (−3,604) |
| Majkel1337 (winning control) | +17,814 | 3,915 / 141,345 | 4,150 / 149,547 | +8,202 | 347 / 582 | 1,005 / 35,812 → 34,751 (−1,061) |

## Feasibility assessment

A broad volume cap would remove purchases that support feed and later sales, while the full WHEAT trade is positive in every saved live loss and each current top20 failure. A narrowly timed rule that suppresses only same-step purchases later sold after opening stock runs out could target a measured negative cash subset, but it is not success-neutral in the available evidence: the same signal occurs on Majkel, a winning tape. The 30-loss corpus has no winning controls, and only one current winning top20 event trace is available here, so harm-free behavior cannot be established. Rival market repricing also makes these fixed-tape cash deltas noncausal policy estimates.

**Recommendation:** do not implement or promote a cap from this screen. If revisited, freeze a concrete order-level rule and evaluate it in reacting native games against multiple references before using fixed-tape figures as anything beyond diagnosis.

## Scope note

The DECEM headline of 3,773 successful `BUY_PRODUCT` fills / 157,460 cost is the all-product total. It reconciles exactly as WHEAT 3,562 / 148,208 plus FERTILIZER 211 / 9,252. The 149,894 receipt figure is WHEAT sales, so the tables above compare WHEAT-only buys and sales. No Kaggle access, downloads, candidate outcomes, or edits to `main.py` / `agent.md` were made.
