# Rival-aware research planner (2026-09-25)

This is a new experimental policy layer over the prior independently tested
worker executor, not an edit to `main.py` and not a Kaggle submission file.
It chooses farm investments from current public market/farm observations.
No replay identity, seed, future shop draw or rival private inventory is used.

## Different hypothesis

The previous planner ranked assets by projected **own cash** and lost badly.
This planner estimates the incremental terminal **paired margin** caused by
one new asset: its own product/input cashflow plus the effect of its market
stock changes on visible rival production. The engine's known price curve is
used; future shop arrivals and exact sale timing are explicit approximations.

The same runnable `agent.py` exposes three modes via `MODE`:

- `control`: exact prior v1 investment scoring, to verify wrapper parity.
- `terminal_margin`: season-to-end marginal margin with two demand/rival
  scenarios. This tests opponent-aware investment ranking.
- `short_cycle`: 12-day conservative margin, requiring projects to start
  returning cash sooner. This tests a different rolling-horizon method.

The worker scheduler, unit-action validation, buying, selling and hiring are
unchanged from the frozen v1 executor. The only treatment is investment
valuation. Thus a loss identifies the high-level model, not an altered
execution protocol.

## Predeclared screen

1. Prove `MODE=control` reproduces frozen v1 actions/results in both seats.
2. Unit-test market-price and rival-externality sign, horizon and schemas.
3. Run both new modes reactively versus `main.py` on seeds 0 and 42, both
   seats. Record wins, own/rival cash, status and latency.
4. Run matched exogenous-shop checks for any apparently promising mode;
   no promotion from native-seed luck or a fixed-action tape.
5. Only if a mode beats the v1 control materially *and* challenges `main.py`
   on independent reactive checks, expand to the complete top-50 panel and
   fresh holdouts before considering `main.py` promotion.

The model is not a trained rollout selector. It is an intentionally smaller
alternative strategic hypothesis to test before paying for a large terminal
rollout dataset.
