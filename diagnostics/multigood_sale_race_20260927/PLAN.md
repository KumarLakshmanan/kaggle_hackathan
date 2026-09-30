# Multi-product rival sale-race data gate — 2026-09-26

The prior observed-strawberry-stock predictor had only five positive holdout
opportunities under a narrow late physical-mirror gate and was rejected
before fitting. This new **read-only data gate** covers all farm products
and does not require physical mirroring. It uses the same 100 completed
current-submission public replays. The earlier 39 development episode IDs
remain development; the other 61 are an episode-disjoint diagnostic holdout.

An opportunity is one per item stock batch: own private shed stock ≥3,
current own action does not sell/buy/pick up that item, a free market slot,
and the next recorded own sale of that item is within 24 turns. The first
eligible step is kept until stock drops below 3 or an own sale resets the
batch. A positive label means a rival sale of the same item occurs **after**
the opportunity but before that next own sale, within 12 turns. Future
actions are used only for offline labels, never as deployable features.

Feature columns, if stored, may use only current and prior public
observation, own private shed, own action, and prior own-sale history: item,
step/hour, current quote and market inventory and their past changes, stock,
own/rival public producer counts, public money changes, and current physical
similarity. No rival private inventory, future action, replay ID, team name
or opponent policy is a feature.

Before fitting, require at least 20 positive opportunities in the 61-episode
holdout, positive examples in at least ten distinct holdout episodes, and at
least two product items with five or more holdout positives. If this data
gate fails, reject model fitting and policy tests. It passed with 568
holdout positives in 55 episodes. The one frozen model is L2-regularized
logistic regression: item one-hot columns plus all listed numerical features,
each standardized using development rows only and clipped to [-5, 5].
Use a bias term, unweighted cross-entropy, L2 coefficient 0.01 excluding the
bias, full-batch Adam for 1,000 steps with learning rate 0.05, and no
hyperparameter or feature selection based on holdout results. Require
episode-disjoint AUC≥0.70 and top-quartile precision≥1.4× prevalence, then
build an isolated action candidate for
native both-seat original-shop and fresh reactive testing. Passing a data
gate alone does not justify editing `main.py` or uploading to Kaggle.
