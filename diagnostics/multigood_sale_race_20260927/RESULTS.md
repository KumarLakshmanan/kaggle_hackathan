# Multi-product rival sale-race predictor — 2026-09-26

## Data gate

The read-only extractor processed 100 completed current-submission replays,
with the prior 39 development episode IDs and 61 disjoint holdout episodes.
It found 11,478 qualifying one-per-stock-batch sale opportunities. There
were 319 positives in development and **568 positives in holdout**, spread
across **55 holdout episodes**. Six holdout products had at least five
positives. The predeclared data gate passed.

## Frozen predictive gate

The single prespecified L2 logistic model used only current/past observation,
own stock/action, and public money/producer counts. Development AUC was
0.799. On the untouched holdout, AUC was **0.654**, below the required
**0.70**. Holdout top-quartile precision was 0.1516 versus prevalence
0.0803, a 1.887-fold lift above the separate 1.4-fold threshold. Both
thresholds were required, so the predictive gate failed.

**Decision: reject this predictor.** Do not tune it against this holdout,
turn it into an action rule, edit `main.py`, or upload to Kaggle based on this
experiment. The data gate establishes that multi-product opportunities are
numerous enough to study, but this public-feature model did not generalize
well enough to support a sale timing intervention. The target itself is
conditional on a future own sale within 24 turns, which a deployed policy
would still have to forecast.

Reproduction:

```powershell
python diagnostics\multigood_sale_race_20260927\extract_dataset.py
python diagnostics\multigood_sale_race_20260927\fit_model.py
```

Evidence: `opportunities.json` (audit/development source hashes, all rows),
`model_result.json` (frozen coefficients and metrics), and
`holdout_predictions.json` (episode/step/item/label/probability).
