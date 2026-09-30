# Public physical-state sale predictor and milk action pilot — 2026-09-26

## Correction — 2026-09-26 20:48 UTC (supersedes the model and parity claims below)

Kaggle replay frame `t` contains the observation for turn `t` but the action
that produced that observation on turn `t-1`. The first extractor paired that
observation with the prior action; the deployed wrapper paired it with the
current action. Consequently the original 11,478/2,051 opportunity counts,
0.835 holdout AUC, 2.889 lift, and claimed five-episode offline/deployment
feature parity do **not** validate the deployed model. The original native
pilot's terminal cash, DONE statuses, and 3/16 activation result remain valid
for its exact candidate bytes, but its model interpretation is withdrawn.

`corrected_extract.py` pairs observation frame `t` with action frame `t+1`
and labels only subsequent rival actions. It found 5,997 opportunities/708
positives in 100 development episodes and 1,108/112 in 17 later episodes
(16 episodes with positives). A refit with the same feature list and logistic
family reached development AUC 0.747 and holdout AUC **0.844**; holdout
top-quartile precision was **0.300**, or **2.964×** its 0.101 prevalence.
This is a correction on the **same reused holdout**, not independent model
confirmation. `check_feature_parity_corrected.py` matched all numeric features
on five distinct development episodes, and `file_parity_corrected.py` passed
Kaggle file-loader/direct parity in both seats with a final callable.

The corrected isolated candidate
`exp_physical_milk_sale_corrected_20260927.py` (SHA-256
`9d415fb73274fc9b6fe86ecf943b3c32961f4c158e06346e5d557d3e32d70960`)
kept the original action gate and thresholds. Against reacting unchanged
`main.py` on fresh seeds 2624000–2624015 in both seats with original shops,
all 64 control/candidate games ended DONE/DONE with zero branch errors, but
**0/16 paired seeds activated** and no actions changed. The predeclared
four-activation gate failed. **Reject the corrected action rule and both
versions of the model as evidence for promotion. No `main.py` edit or Kaggle
upload.** Exact corrected artifacts are `physical_opportunities_corrected.json`,
`model_result_corrected.json`, `file_parity_corrected_seed0.json`, and
`reactive_corrected_dev16.json`.

## Historical original pilot (model interpretation superseded above)

## Fresh replay cohort

A read-only Kaggle episode listing found 17 public games of current
submission 56572390 with IDs newer than the maximum in the prior 100-game
audit. The exact IDs were frozen before replay labels were read; three older
backfilled games were excluded. All 17 replays downloaded and completed:
seven wins, ten losses. `selection.json` records source audit hash and IDs;
`audit_new.json` and exact public replay files preserve observations and
outcomes. This is a chronological sample, not a causal policy comparison.

## Predictive result

The new features use only current public rival harvest readiness and worker
positions, appended to the prior public/history features. Under the frozen
one-per-stock-batch opportunity definition, 100 development games yielded
11,478 rows/887 positive rival-before-own sale events. The **17 untouched
later games** yielded 2,051 rows/137 positives across 16 episodes, passing
the frozen sample-size gate. The single prespecified L2 logistic fit reached
development AUC 0.769. On the temporal holdout it reached **AUC 0.835** and
top-quartile precision **0.193** versus prevalence **0.0668**, or **2.889×**
lift. Both predictive gates passed. This is a forecast of a limited
conditional event, not evidence that any action improves terminal cash.

## Frozen action pilot

Development-only diagnostics pointed to MILK as the product with material
price impact at high modeled risk. The isolated single-file candidate
`exp_physical_milk_sale_20260927.py` (SHA-256
`d65173e46e531068b85d78ad24ac779ce1cc7b56864dfb361a9eaffae87944a2`)
advanced at most eight already-shed milk units when its score was ≥0.30,
the rival had at least three publicly ready milk units, a same-day own tape
sale already existed, and the projected post-rival sale receipt drop was
at least 16 coins. It changed no route, worker, purchase or other product.
Deployment feature values exactly matched offline extraction on five
distinct development episodes. Kaggle's file loader selected the final
`kaggle_main_entrypoint`; file-path and direct-call seed-0 games matched
both seats and ended DONE/DONE.

On fresh native seeds 2623000–2623015, control and candidate each played
reacting unchanged `main.py` in both seats with original shops: **all 64
games DONE/DONE**, zero action-branch errors. The candidate triggered six
sales/32 units on only **3/16 paired seeds**, below the predeclared four-seed
activation minimum. Those three seeds had positive paired-margin deltas
+28, +16 and +150, sum **+194**. Aggregate own cash rose 80 while rival
cash fell 114. The maximum candidate call in this six-worker local run was
298 ms. These small positive deltas do not overcome the insufficient
activation or establish a leaderboard improvement.

**Decision: reject the action rule for `main.py`; keep the predictive model
as research evidence.** No independent native confirmation, full saved-route
regression, main-file edit or Kaggle upload follows after the failed frozen
development gate. The current submission source remains SHA-256 `489fe8e4...`.

Reproduce:

```powershell
python -X utf8 diagnostics\physical_sale_predictor_20260927\collect_new.py
python -X utf8 diagnostics\physical_sale_predictor_20260927\extract_features.py
python -X utf8 diagnostics\physical_sale_predictor_20260927\fit_model.py
python diagnostics\physical_sale_predictor_20260927\build_candidate.py
python -X utf8 diagnostics\physical_sale_predictor_20260927\check_feature_parity.py
python -X utf8 diagnostics\physical_sale_predictor_20260927\file_parity.py
python -X utf8 diagnostics\physical_sale_predictor_20260927\reactive_dev16.py
```

`physical_opportunities.json`, `model_result.json`,
`holdout_predictions.json`, `file_parity_seed0.json`, and
`reactive_dev16.json` contain exact source, label, score, loader and
terminal-cash evidence.
