# Day-26 complete-route transition experiment (2026-09-27)

## Hypothesis

The incumbent switches every shop-specific native route to route 2 at step
648 (day 27). Switching one day earlier might improve late wheat/carrot
production and market execution by using the complete route-2 schedule for
day 26, including its workers, seeds, feed and sales. This is a coherent route
transition rather than a single extra product or action.

## Frozen candidate and gates

Create `exp_early_route2_20260927.py` as an exact `main.py` snapshot with each
short source-line standalone step-648 threshold changed to 624. Do not touch
compressed route data. This includes the router, forward-look overlays and
seed-float start threshold. Inspect the resulting diff and verify path-loader
entrypoint selection.

First compare candidate against the snapshot `main.py` on native seeds
2617000–2617003, both seats, endogenous shops and a reacting opponent.
Require all games `DONE`, positive aggregate candidate own cash and margin,
and at least three of four paired seeds with positive margins to expose a
larger confirmation panel. Reject immediately otherwise. Fixed public routes
may be used afterward only to diagnose a passed native candidate, never as
independent validation.

No Kaggle upload is authorized by this experiment.
