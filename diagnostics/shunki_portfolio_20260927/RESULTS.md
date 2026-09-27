# Public Shunki route portfolio feasibility — 2026-09-26 21:45 UTC

All 203 completed public episodes for ShunkiKyoya submission 56553856
were fetched and reduced to verified, compressed 719-action routes. The
routes cover all eight first shops and 61 of 64 first-two-shop pairs.
Every route has the same first 72 actions. The exact-action branching
criteria in `PLAN.md` failed: four first-shop groups diverge before turn
144 (FARMERS_MARKET at 92, PIZZA_SHOP at 79, SMOOTHIE_SHOP at 100,
YARN_STORE at 132). Forty-five same-pair groups have more than one
complete action hash.

The differences are often small but state-dependent. In a repeated
PIZZA_SHOP/PET_CAFE pair, the turn-79 action buys and sells 16 wheat
versus 15; the visible wheat quotes were 30 versus 28 and own money
522 versus 480. The farm tiles and workers matched. In a repeated
YARN_STORE/BAKERY pair, turn 132 was farmer PASS versus DIG; the DIG
farm had a visible weed under the farmer, while the other did not.
At the earliest divergence of the 45 conflicting shop-pair groups,
33 were market-only and 12 involved farmer and/or hands. These are
sampled counterexamples to exact route lookup, not a measured model of
the full opposing policy.

**Decision: reject direct exact-action portfolio assembly under the
frozen feasibility plan. No `main.py` edit or Kaggle upload.** A separate
shop-aware recorded-route probe may quantify whether a coarse lookup
still helps, but it must pass fresh reacting both-seat tests before any
promotion. Its fixed public source histories are training evidence only.

Evidence: `route_manifest.json`, `prefix_analysis.json`,
`component_analysis.json`, 203 compressed route files under `routes/`,
and scripts `collect_routes.py`, `analyze_prefixes.py`, and
`analyze_action_components.py`. The two specific observation checks used
Kaggle public replay IDs 113833606 / 113488962 and 113821826 / 113581559.
