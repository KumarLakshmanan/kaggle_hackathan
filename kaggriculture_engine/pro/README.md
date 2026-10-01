# Scenario-aware executable engine v2

This is a separate research engine and two generated competition candidates.
The validated root `main.py` is preserved until a candidate passes the frozen
qualification plan. There is no guaranteed-win mode.

## Implemented components

| Component | What it does | Limits |
|---|---|---|
| `beliefs.py` | Tracks visible rival crops/animals, production capacity, stock intervals and uncertain residual market flows. | Public market changes cannot uniquely reveal rival trades or private stock. |
| `scheduler.py` | Assigns workers in native execution order; maintains existing assets and funds bounded seed, animal, land and worker commitments. Includes travel, pickup/drop, planting, watering, maturity, harvest, feed, care and fertilizer. | A greedy executable scheduler, not an optimal farm planner. |
| `scenarios.py` | Samples three synthetic future seeds with low/mid/high stock and reacting seller/producer policies. Retains the former three market safety anchors. | Scenario weights are heuristic. The real hidden episode seed and future shops are never read. |
| `value.py` / `train.py` | Fits final relative-coin residuals and win-point estimates from legal seat observations and saved final rewards. Fixed episode-group holdout and uncertainty/extrapolation guard. | Saved episodes are correlated; estimates are not calibrated live win probabilities. |
| `simulation.py` / `optimizer.py` | Native exact transitions, plain observations, bounded isolated caches, deduplication and sale-prioritized queue generation. | Local benchmarks do not prove a Kaggle timeout guarantee. |
| `planner.py` | Compares incumbent itinerary with whole-portfolio maintenance and funded crop/animal/land increments through twelve native days. Reports coins for both players and paired relative gains. | Baseline future continuation is the immutable itinerary, not an exact clone of every incumbent repair. Partial forecasts cannot activate a plan. |
| `season.py` | Offline forecasts through actual native terminal cash, using a compatible portfolio-maintenance control. Reports harvested units, terminal stock, peak assets and whether proposed commitments were established and reached maturity. | Rival policy, stock and future shops remain hypothetical. This is not an independently qualified competitive agent. |
| `runtime.py` | Uses the validated incumbent, adds bounded market edits, optionally evaluates physical commitments on turns144/216 and continues any selected physical plan. | Physical planning needs observed activation and independent qualification before it earns competition use. |
| `build.py` | Embeds stdlib runtime, simulator and model into a self-contained candidate, with source hashes and a final Kaggle callable. | Does not submit or change root `main.py`. |

## Budgets and safety checks

Market search tests at most12 distinct programs every fourth hour, under six
hypotheses. Every accepted edit preserves both farms' noncash state and private
inventories and does not lower our cash or relative cash in any hypothesis.
These are model-conditional safeguards, not a proof against unknown opponents.

Online physical search has a4096-transition budget and three reacting scenarios.
It completes2592 native transitions to compare the itinerary, maintenance and one
crop expansion over288 turns (shortened only at actual season end). A complete
paired comparison, nonnegative relative cash in every scenario, predicted gain
above max(2000, holdout RMSE/3), and supported model features are required.
Remaining season production is estimated with an explicit fitted tail error;
it is not falsely reported as simulated final coins. Offline search also offers
animal/land bundles and reports any incomplete alternatives.

The offline suggestion interface also blocks a selected bundle if its itinerary
control is outside the fitted model's support. A foreign saved farm portfolio
can be incompatible with that itinerary: a collapsing control does not establish
a strong new strategy. `review.py` reports this explicitly. The source-frozen
physical runtime candidates are experimental; do not infer their qualification
from offline bundle forecasts or market-only match gains.

Offline `plan` defaults to a state-compatible `--control maintenance` baseline.
Use `--control itinerary` only for an observation compatible with that executor's
portfolio. The maintenance comparison ranks new investments against maintaining
everything already owned; it does not claim to exactly reproduce uploaded main.
The frozen online physical controller still uses its declared itinerary control
and remains experimental. Tool refinements do not alter the frozen agents.

The cache includes all public/private state, configuration, hypothetical seed,
statuses and both actions. Cached values are copied on return, so modifying one
branch cannot corrupt another. It is bounded per search.

## Reproduce

From `H:\hackathan`, using the project's Python environment:

```powershell
python -m kaggriculture_engine.pro.train --manifest diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json --output new_value_model.json

python -m kaggriculture_engine.pro build --baseline diagnostics/professional_engine_20260930/baseline_main_bbffbe65.py --model diagnostics/professional_engine_20260930/value_model.json --output new_candidate.py --physical

python -m kaggriculture_engine.pro plan --baseline diagnostics/professional_engine_20260930/baseline_main_bbffbe65.py --model diagnostics/professional_engine_20260930/value_model.json --input diagnostics/professional_engine_20260930/example_input.json --output suggested_strategy.json --transitions 12000

python -m kaggriculture_engine.pro plan --input diagnostics/professional_engine_20261001/example_input.json --output full_season_suggestion.json --transitions 12000 --season

python diagnostics/professional_engine_20260930/verify_engine.py
python diagnostics/professional_engine_20260930/run_experiment.py screen --workers 6
```

Use new output paths: builders/plan suggestions refuse to overwrite prior
artifacts. Retraining changes the model identity; do not overwrite a frozen
model while resuming its games. The offline trainer requires NumPy; generated
agents require only Python's standard library.

Qualification is source-bound and resumable under the shared game lock.
`diagnostics/professional_engine_20260930/PLAN.md` fixes development seeds and
reserved confirmation seeds before outcomes. Both seats remain paired;
native framework/file-loader checks and uncertainty across whole seed blocks
are required. Saved action tapes are diagnostic controls, never independent
validation of an adaptive policy.

The initial September30 builds were rejected after an empty-order scenario
sort crashed. The operational repair and additional adversarial probe are
preserved in `diagnostics/professional_engine_20261001`. That experiment uses
fresh34010001–4 development and34010101–16 confirmation seeds. See its own
PLAN/results/decision; do not resume the rejected build under the repaired hash.
Cache timing depends on workload: the repaired probe was slower with caching
(0.02059s versus0.01008s for40 simple transitions). Caching preserves branch
integrity and can reuse expensive settlement, but a general speedup is not claimed.

`--season` needs no executor or fitted model. It simulates to the native final
cash in each hypothesis instead of estimating the remaining season. Hypothetical
win points are precise for those simulated worlds, not live win probabilities.
Only complete paired forecasts with nonnegative scenario points/relative coins,
mean relative gain at least2000 coins and established/matured new commitments
can recommend an expansion. Remaining stock receives no terminal cash credit.
The tested foreign farm observation completed18 scenario seasons /10350 native
transitions; every expansion was rejected. An adversarial two-worker harvest
correctly counts four wheat units once, and an insufficient budget selects no
strategy. See `season_verification.json` and `offline_full_season_verified.json`.

## Evidence

`engineering_checks.json` records216 native/cache parity cases and physical,
information-boundary and complete-horizon probes. The model fit has1314 training
samples and198 holdout samples, with episode groups disjoint. Holdout relative
coin RMSE is5053.28 versus5938.84 for current cash; Brier score is0.16387 versus
0.23978 for the declared cash-only heuristic. These older samples establish
model error only. Match receipts and final promotion decisions are recorded
separately in the diagnostics directory and `agent.md`.
