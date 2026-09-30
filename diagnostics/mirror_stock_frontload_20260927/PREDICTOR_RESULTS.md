# Public-history sale-race predictor — rejected before fitting, 2026-09-26

The frozen extractor read 100 completed live public replays of current
submission 56572390. It applied the rejected half-base rule's legal visible
gate and kept only the first opportunity in each own strawberry-stock batch.
The prior 29-loss plus ten-close-win cohort served as the development split;
the remaining 61 episodes were reserved for diagnostic holdout. The 100
episode IDs are distinct and all source hashes are recorded in
`sale_race_dataset.json`.

Only **70** eligible batch opportunities existed: development had 45
(8 where the rival sold before our next sale within 24 turns, 37 other),
and the 61-episode holdout had 25 (5 positive, 20 other). The frozen plan
required at least **20 positive holdout opportunities** before fitting or
considering a predictor. This sample is too sparse for a defensible
held-out estimate of rival timing under the narrow gate.

**Decision: reject the predictor path at its data sufficiency gate.** No
classifier was fitted, no live-policy feature was added, and no reactive
promotion claim follows from these replays. The 39/61 split is a diagnostic
separation within public data, not independent policy validation. Shift work
to the larger repeatable production gaps in the refreshed top-100 losses.
`main.py` and Kaggle remain unchanged.

Reproduce: `python -B -X utf8
diagnostics/mirror_stock_frontload_20260927/extract_sale_race_dataset.py`.
